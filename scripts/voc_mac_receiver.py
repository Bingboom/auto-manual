#!/usr/bin/env python3
"""Run and manage the loopback-only product VOC receiver on macOS."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from integrations.product_voc.intake import BotWriter, Intake  # noqa: E402
from integrations.product_voc.server import LimitedServer, make_handler  # noqa: E402

DEFAULT_RUNTIME = Path.home() / "Library" / "Application Support" / "auto-manual" / "product-voc"


def private_runtime(path: Path) -> Path:
    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    return path


def read_pid(runtime: Path) -> int | None:
    try:
        value = json.loads((runtime / "receiver.pid").read_text(encoding="utf-8"))
        return int(value["pid"])
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def is_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def owns_process(pid: int) -> bool:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True, check=False
    )
    command = result.stdout.strip()
    return result.returncode == 0 and str(Path(__file__).resolve()) in command and " run " in f" {command} "


def validate_origins(origins: list[str]) -> None:
    for origin in origins:
        url = urlsplit(origin)
        loopback = url.scheme == "http" and url.hostname in ("127.0.0.1", "localhost")
        if (
            not url.hostname
            or url.username
            or url.password
            or url.path
            or url.query
            or url.fragment
            or not (url.scheme == "https" or loopback)
        ):
            raise ValueError("Origins must be bare HTTPS origins (HTTP loopback allowed for tests)")


def run_receiver(args: argparse.Namespace) -> int:
    validate_origins(args.origin)
    runtime = private_runtime(args.runtime_dir)
    lock_file = (runtime / "receiver.lock").open("a+")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        print("VOC receiver is already running", file=sys.stderr)
        return 2

    pid_path = runtime / "receiver.pid"
    intake = None
    server = None
    try:
        writer = BotWriter(base=args.base, table=args.table, profile=args.profile)
        writer.preflight()
        intake = Intake(runtime / "receipts.sqlite", writer)
        server = LimitedServer(
            ("127.0.0.1", args.port),
            make_handler(intake, set(args.origin), args.preview, args.cloudflare_tunnel),
        )
        pid_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
        os.chmod(pid_path, 0o600)

        def stop_server(_signum, _frame):
            threading.Thread(target=server.shutdown, daemon=True).start()

        signal.signal(signal.SIGTERM, stop_server)
        signal.signal(signal.SIGINT, stop_server)
        print(f"VOC receiver listening on 127.0.0.1:{args.port}; fixed table {args.table}", flush=True)
        server.serve_forever()
    finally:
        if server is not None:
            server.server_close()
        if intake is not None:
            intake.db.close()
        pid_path.unlink(missing_ok=True)
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()
    return 0


def child_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run",
        "--profile", args.profile,
        "--base", args.base,
        "--table", args.table,
        "--runtime-dir", str(args.runtime_dir.expanduser().resolve()),
        "--port", str(args.port),
    ]
    for origin in args.origin:
        command.extend(("--origin", origin))
    if args.preview:
        command.append("--preview")
    if args.cloudflare_tunnel:
        command.append("--cloudflare-tunnel")
    return command


def start_receiver(args: argparse.Namespace) -> int:
    runtime = private_runtime(args.runtime_dir)
    pid = read_pid(runtime)
    if is_running(pid):
        if owns_process(pid):
            print(f"VOC receiver is already running (pid {pid})")
            return 0
        print(f"Ignoring stale receiver pid file for reused pid {pid}", file=sys.stderr)
    (runtime / "receiver.pid").unlink(missing_ok=True)
    log_path = runtime / "receiver.log"
    log_handle = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.chmod(log_path, 0o600)
    try:
        process = subprocess.Popen(
            child_command(args),
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        os.close(log_handle)
    deadline = time.monotonic() + args.start_timeout
    health_url = f"http://127.0.0.1:{args.port}/healthz"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print(f"VOC receiver failed to start; inspect {log_path}", file=sys.stderr)
            return 1
        try:
            with urllib.request.urlopen(health_url, timeout=0.5) as response:
                if response.status == 200 and read_pid(runtime) == process.pid:
                    print(f"VOC receiver started on 127.0.0.1:{args.port} (pid {process.pid})")
                    return 0
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    process.terminate()
    print(f"VOC receiver did not become healthy; inspect {log_path}", file=sys.stderr)
    return 1


def stop_receiver(args: argparse.Namespace) -> int:
    runtime = args.runtime_dir.expanduser().resolve()
    pid = read_pid(runtime)
    if not is_running(pid):
        (runtime / "receiver.pid").unlink(missing_ok=True)
        print("VOC receiver is stopped")
        return 0
    if not owns_process(pid):
        print(f"Refusing to signal unrecognized pid {pid}", file=sys.stderr)
        return 2
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + args.stop_timeout
    while time.monotonic() < deadline:
        if not is_running(pid):
            (runtime / "receiver.pid").unlink(missing_ok=True)
            print("VOC receiver stopped")
            return 0
        time.sleep(0.1)
    print(f"VOC receiver pid {pid} did not stop", file=sys.stderr)
    return 1


def status_receiver(args: argparse.Namespace) -> int:
    pid = read_pid(args.runtime_dir.expanduser().resolve())
    if is_running(pid) and owns_process(pid):
        print(f"VOC receiver is running (pid {pid})")
        return 0
    print("VOC receiver is stopped")
    return 3


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    def runtime_options(command: argparse.ArgumentParser) -> None:
        command.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME)

    def receiver_options(command: argparse.ArgumentParser) -> None:
        runtime_options(command)
        command.add_argument("--profile", required=True, help="verified HT-Docs lark-cli profile")
        command.add_argument("--base", required=True)
        command.add_argument("--table", required=True)
        command.add_argument("--origin", action="append", required=True)
        command.add_argument("--port", type=int, default=9198)
        command.add_argument("--preview", action="store_true")
        command.add_argument("--cloudflare-tunnel", action="store_true")

    run = commands.add_parser("run", help="run in the foreground")
    receiver_options(run)
    run.set_defaults(action=run_receiver)
    start = commands.add_parser("start", help="start a detached process")
    receiver_options(start)
    start.add_argument("--start-timeout", type=float, default=10.0, help=argparse.SUPPRESS)
    start.set_defaults(action=start_receiver)
    stop = commands.add_parser("stop", help="stop the managed process")
    runtime_options(stop)
    stop.add_argument("--stop-timeout", type=float, default=10.0, help=argparse.SUPPRESS)
    stop.set_defaults(action=stop_receiver)
    status = commands.add_parser("status", help="report managed process state")
    runtime_options(status)
    status.set_defaults(action=status_receiver)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.action(args)


if __name__ == "__main__":
    raise SystemExit(main())
