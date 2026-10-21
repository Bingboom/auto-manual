"""Run the external intelligence loop by hand: sync the 外部情报 table, then push the digest.

    python -m tools.intel sync --knowledge-dir DIR [--write [--push]]
    python -m tools.intel push --knowledge-dir DIR [--dry-run]

``sync`` reads the Feishu table (never writes it) and prints what would change in
``DIR/external-intel/events.json``; ``--write`` writes the file and ``--push`` then
sends the decision digest to the group. Without ``--write`` nothing is written or
sent, and ``--push`` prints the message instead. ``push`` sends the digest of the
file as it is. No workflow runs either command yet.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys

from . import delivery, push, sync
from .digest import decision_digest, safe_external_url
from .events import CONTENT_DIR, EVENTS_FILE, encode_intake, events_snapshot
from .feishu import LarkError, runner
from .files import write_atomic as _write
from .policies import read_policies

# Where the host renders the research page; digest links point at its event anchors.
PAGE = "research/product-intelligence"
ENV = {"base": "FEISHU_EXTERNAL_INTEL_BASE_TOKEN", "table": "FEISHU_EXTERNAL_INTEL_TABLE_ID",
       "chat": "FEISHU_EXTERNAL_INTEL_CHAT_ID", "record_url": "FEISHU_EXTERNAL_INTEL_RECORD_URL",
       "identity": "FEISHU_EXTERNAL_INTEL_IDENTITY", "site_url": "EXTERNAL_INTEL_SITE_URL"}
_TRANSPORT_HINT = "check the lark-cli profile, the bot's access and the configured ids"


def _iso_date(value: str) -> str:
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO date: {value!r}") from None


def _summary(report: dict) -> list[str]:
    counts = ", ".join(f"{key} {len(report[key])}" for key in sync.CHANGES)
    lines = [f"rows: {counts}, unchanged {report['unchanged']}; {len(report['problems'])} not used, "
             f"{len(report['notices'])} notices, {len(report['gone'])} events without a row"]
    for key in (*sync.CHANGES, "problems", "notices", "gone"):
        lines += [f"  {key:<10} {note['event_id']} {note['title']} {note['message']}".rstrip()
                  for note in report[key]]
    return lines


def _runner(args):
    """The injected ``run`` (tests), else lark-cli under the chosen identity."""
    return args.run if args.run is not None else runner(args.cli_bin, args.identity)


def _failure(exc: Exception) -> str:
    """What a failed call may print: a ``LarkError`` names no argument; any other transport only its type."""
    return str(exc) if isinstance(exc, LarkError) else type(exc).__name__


def _send_pending(args, job: dict) -> int:
    """Replay the original candidate and message, and clear it only after acknowledgment."""
    if job["destination_sha256"] != delivery.destination(args.chat_id, args.cli_bin, args.identity):
        print("ERROR   pending push belongs to another chat, profile or identity; restore the original configuration")
        return 1
    try:
        if delivery.apply_intake(args.knowledge_dir, job, _write):
            print(f"{args.knowledge_dir / CONTENT_DIR / EVENTS_FILE}: written from pending candidate")
        receipt = push.send(_runner(args), chat_id=args.chat_id, content=job["content"], key=job["idempotency_key"])
        if not receipt["message_id"]:
            raise RuntimeError("send returned no message acknowledgment")
        delivery.acknowledge(args.knowledge_dir, job)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR   push failed ({_failure(exc)}); pending candidate/message retained; "
              f"{_TRANSPORT_HINT}; retry the same command with the original configuration")
        return 1
    print(json.dumps({**receipt, "events_snapshot_id": job["events_snapshot_id"]}, ensure_ascii=False))
    return 0


def _store(args, payload: bytes | None, before: bytes | None) -> None:
    if payload is None:
        return
    path = args.knowledge_dir / CONTENT_DIR / EVENTS_FILE
    if payload == before:
        print(f"{path}: unchanged")
    elif args.write:
        _write(path, payload)
        print(f"{path}: written ({len(json.loads(payload)['events'])} events)")
    else:
        print(f"{path}: would change (dry run; add --write to write it)")


def _deliver(args, intel: dict, report: dict | None, *, send: bool,
             payload: bytes | None = None, before: bytes | None = None) -> int:
    """Send (or, when not ``send``, print) the digest message of ``intel``."""
    site = args.site_url.rstrip("/")
    digest = decision_digest(intel, page=PAGE, base_url=site)
    content = push.post_content(digest, today=args.today, record_url=args.record_url,
                                page_url=f"{site}/{PAGE}.html" if site else "", report=report)
    if content is None:
        _store(args, payload, before)
        print("push: nothing is pending and the sync reported nothing; no message")
        return 0
    job = delivery.message(content=content, today=args.today, snapshot=intel["snapshot_id"], chat=args.chat_id,
                           cli=args.cli_bin, identity=args.identity, intake=payload, before=before)
    if not send:
        _store(args, payload, before)
        print(f"push (dry run, idempotency key {job['idempotency_key']}):\n{push.preview(content)}")
        return 0
    delivery.save(args.knowledge_dir, job)
    return _send_pending(args, job)


def _policies(root: Path) -> list[dict] | None:
    """The policy records, or ``None`` with a warning when they cannot be read."""
    try:
        return read_policies(root)
    except (OSError, ValueError) as exc:
        print(f"WARNING market-policy records are unreadable ({exc}); policy ids are not checked")
        return None


def run_sync(args) -> int:
    path = args.knowledge_dir / CONTENT_DIR / EVENTS_FILE
    try:
        before = path.read_bytes() if path.is_file() else None
        previous = json.loads(before) if before is not None else None
    except (OSError, ValueError) as exc:
        print(f"ERROR   cannot read {path}: {exc}")
        return 1
    try:
        rows = sync.read_table(_runner(args), args.base_token, args.table_id)
    except sync.TableShapeError as exc:
        print(f"ERROR   {exc}; see the field list in the operator guide")
        return 1
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR   table read failed ({_failure(exc)}); {_TRANSPORT_HINT}")
        return 1
    policies = _policies(args.knowledge_dir)
    try:
        document, report = sync.merge(previous, rows, today=args.today,
                                      policy_ids=None if policies is None else {record["id"] for record in policies})
    except ValueError as exc:
        print(f"ERROR   {path.name} cannot take this sync: {exc}")
        return 1
    payload = encode_intake(document)
    print("\n".join(_summary(report)))
    if not args.push:
        _store(args, payload, before)
        return 0
    if policies is None:
        print("ERROR   cannot build the digest: policy events need readable market-policy records")
        return 1
    return _deliver(args, events_snapshot(payload, policies), report, send=args.write, payload=payload, before=before)


def run_push(args) -> int:
    path = args.knowledge_dir / CONTENT_DIR / EVENTS_FILE
    try:
        payload = path.read_bytes() if path.is_file() else None
        intel = events_snapshot(payload, read_policies(args.knowledge_dir) if payload is not None else [])
    except (OSError, ValueError) as exc:
        print(f"ERROR   cannot read {path}: {exc}")
        return 1
    return _deliver(args, intel, None, send=not args.dry_run, payload=payload, before=payload)


def _missing(args) -> list[str]:
    """Flags a run needs: the table for a sync, the chat only when a message is really sent."""
    syncing = args.command == "sync"
    needed = [("--base-token", "base_token"), ("--table-id", "table_id")] if syncing else []
    if (args.push and args.write) if syncing else not args.dry_run:
        needed.append(("--chat-id", "chat_id"))
    return [flag for flag, name in needed if not getattr(args, name)]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    commands = root.add_subparsers(dest="command", required=True)
    for name, text in (("sync", "read the 外部情报 table into events.json (dry run unless --write)"),
                       ("push", "send the decision digest of events.json to the group")):
        command = commands.add_parser(name, help=text)
        command.add_argument("--knowledge-dir", type=Path, required=True,
                             help="business knowledge directory, e.g. a Hello-Docs checkout's docs/knowledge")
        command.add_argument("--chat-id", default=os.environ.get(ENV["chat"], ""),
                             help=f"group chat id oc_... (default: ${ENV['chat']})")
        command.add_argument("--record-url", default=os.environ.get(ENV["record_url"], ""),
                             help=f"record link with {push.RECORD_PLACEHOLDER} (default: ${ENV['record_url']})")
        command.add_argument("--site-url", default=os.environ.get(ENV["site_url"], ""),
                             help=f"HTTPS site holding the research page (default: ${ENV['site_url']})")
        command.add_argument("--today", type=_iso_date, default=sync.business_today(),
                             help="revision and push date (default: today, China Standard Time)")
        command.add_argument("--cli-bin", default="lark-cli", help='lark-cli command, e.g. "lark-cli --profile prod"')
        command.add_argument("--as", dest="identity", default=os.environ.get(ENV["identity"], "bot"),
                             help=f"lark-cli identity (default: ${ENV['identity']} or bot)")
        if name == "sync":
            command.add_argument("--base-token", default=os.environ.get(ENV["base"], ""),
                                 help=f"base holding the 外部情报 table (default: ${ENV['base']})")
            command.add_argument("--table-id", default=os.environ.get(ENV["table"], ""),
                                 help=f"外部情报 table id (default: ${ENV['table']})")
            command.add_argument("--write", action="store_true", help="write events.json (and send with --push)")
            command.add_argument("--push", action="store_true", help="push the digest right after this sync")
        else:
            command.add_argument("--dry-run", action="store_true", help="print the message instead of sending it")
    return root


def main(argv: list[str] | None = None, *, run=None) -> int:
    """``run(args) -> payload`` stands in for lark-cli in tests."""
    args = parser().parse_args(argv)
    args.run = run
    if missing := _missing(args):
        print(f"ERROR   need {', '.join(missing)} (or the matching variables in --help)")
        return 1
    try:
        args.record_url = push.check_record_url(args.record_url)
    except ValueError as exc:
        print(f"ERROR   {exc}")
        return 1
    if args.site_url and not safe_external_url(args.site_url):
        print("ERROR   --site-url must be an HTTPS URL")
        return 1
    try:
        job = delivery.load(args.knowledge_dir)
        sending = args.write and args.push if args.command == "sync" else not args.dry_run
        if job is not None:
            if sending:
                print("push: resuming the saved message; run sync again afterwards for newer table changes")
                return _send_pending(args, job)
            if args.command == "sync" and args.write:
                print("ERROR   deliver the pending push before another written sync (add --push)")
                return 1
            if args.command == "push" or args.push:
                print(f"push (saved message, dry run):\n{push.preview(job['content'])}")
                return 0
        return run_sync(args) if args.command == "sync" else run_push(args)
    except (OSError, ValueError) as exc:
        print(f"ERROR   local intake/delivery state failed ({type(exc).__name__}); preserve the runtime state")
        return 1


if __name__ == "__main__":
    sys.exit(main())
