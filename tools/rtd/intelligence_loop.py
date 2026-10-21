"""Run the external intelligence loop by hand: sync the 外部情报 table, then push the digest.

    python -m tools.rtd.intelligence_loop sync --knowledge-dir DIR [--write [--push]]
    python -m tools.rtd.intelligence_loop push --knowledge-dir DIR [--dry-run]

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
import tempfile

from tools.rtd import intelligence_push as push
from tools.rtd import intelligence_sync as sync
from tools.rtd.decision_digest import decision_digest, safe_external_url
from tools.rtd.intelligence_events import CONTENT_DIR, EVENTS_FILE, encode_intake, events_snapshot
from tools.rtd.market_policy import market_context

ENV = {"base": "FEISHU_EXTERNAL_INTEL_BASE_TOKEN", "table": "FEISHU_EXTERNAL_INTEL_TABLE_ID",
       "chat": "FEISHU_EXTERNAL_INTEL_CHAT_ID", "record_url": "FEISHU_EXTERNAL_INTEL_RECORD_URL",
       "identity": "FEISHU_EXTERNAL_INTEL_IDENTITY", "site_url": "EXTERNAL_INTEL_SITE_URL"}
_TRANSPORT_HINT = "check the lark-cli profile, the bot's access and the configured ids"


def _iso_date(value: str) -> str:
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO date: {value!r}") from None


def _write(path: Path, payload: bytes) -> None:
    """Replace ``path`` with ``payload`` in one step, so a failed write keeps the last good file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


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
    if args.run is not None:
        return args.run
    from tools.rtd.system_workspace import lark_runner

    return lark_runner(args.cli_bin, args.identity)


def _deliver(args, intel: dict, report: dict | None, *, send: bool) -> int:
    """Send (or, when not ``send``, print) the digest message of ``intel``."""
    from tools.rtd.product_research import PAGE

    site = args.site_url.rstrip("/")
    digest = decision_digest(intel, page=PAGE, base_url=site)
    content = push.post_content(digest, today=args.today, record_url=args.record_url,
                                page_url=f"{site}/{PAGE}.html" if site else "", report=report)
    if content is None:
        print("push: nothing is pending and the sync reported nothing; no message")
        return 0
    key = push.idempotency_key(args.chat_id, content, args.today)
    if not send:
        print(f"push (dry run, idempotency key {key}):\n{push.preview(content)}")
        return 0
    try:
        receipt = push.send(_runner(args), chat_id=args.chat_id, content=content, key=key)
    except (RuntimeError, OSError, ValueError) as exc:
        # Transport errors carry the whole command line; never print or persist their text.
        print(f"ERROR   push failed ({type(exc).__name__}); {_TRANSPORT_HINT}; "
              "rerunning within the hour with the same content sends at most one message")
        return 1
    print(json.dumps({**receipt, "events_snapshot_id": intel["snapshot_id"]}, ensure_ascii=False))
    return 0


def _policy_ids(root: Path) -> set[str] | None:
    try:
        return {record["id"] for record in market_context(root)["records"]}
    except (OSError, ValueError, KeyError):
        print("WARNING market-policy records are unreadable; policy ids are not checked")
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
        # Transport errors carry the whole command line, base token included; print only their type.
        print(f"ERROR   table read failed ({type(exc).__name__}); {_TRANSPORT_HINT}")
        return 1
    try:
        document, report = sync.merge(previous, rows, today=args.today, policy_ids=_policy_ids(args.knowledge_dir))
    except ValueError as exc:
        print(f"ERROR   {path.name} cannot take this sync: {exc}")
        return 1
    payload = encode_intake(document)
    print("\n".join(_summary(report)))
    if payload == before:
        print(f"{path}: unchanged")
    elif args.write:
        _write(path, payload)
        print(f"{path}: written ({len(document['events'])} events)")
    else:
        print(f"{path}: would change (dry run; add --write to write it)")
    if not args.push:
        return 0
    try:
        intel = events_snapshot(payload, args.knowledge_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR   cannot build the digest: {exc}")
        return 1
    return _deliver(args, intel, report, send=args.write)


def run_push(args) -> int:
    path = args.knowledge_dir / CONTENT_DIR / EVENTS_FILE
    try:
        intel = events_snapshot(path.read_bytes() if path.is_file() else None, args.knowledge_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR   cannot read {path}: {exc}")
        return 1
    return _deliver(args, intel, None, send=not args.dry_run)


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
    return run_sync(args) if args.command == "sync" else run_push(args)


if __name__ == "__main__":
    sys.exit(main())
