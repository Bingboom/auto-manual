"""Read-only intake assistance. Run ``python -m tools.manual_intake_assist --help``.

Outputs are review work items, not renderer inputs, approvals or release evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.manual_intake_packet import check_packet, make_packet, native_copy_map
from tools.shared_art_review import apply_review_annotations, inventory, tracked_art, write_review


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    art = commands.add_parser("art-review")
    art.add_argument("--repo", type=Path, required=True)
    art.add_argument("--snapshots", type=Path, required=True)
    art.add_argument("--output", type=Path, required=True)
    art.add_argument("--selections", type=Path)
    art.add_argument("--identities", type=Path)
    for command in ("packet", "check-copy"):
        sub = commands.add_parser(command)
        for flag in ("reference-ir", "source", "output"):
            sub.add_argument("--" + flag, type=Path, required=True)
        for flag in ("model", "region", "language"):
            sub.add_argument("--" + flag, required=True)
        sub.add_argument("--pages", type=int, nargs="+", required=True)
        if command == "check-copy":
            sub.add_argument("--packet", type=Path, required=True)
            sub.add_argument("--copy-map", type=Path)
    args = parser.parse_args(argv)
    if args.command == "art-review":
        repo = args.repo.resolve()
        files = tracked_art(repo)
        downloads = args.snapshots / "downloads"
        files.extend(p for p in downloads.rglob("*") if p.is_file())
        result = inventory(repo, files, args.snapshots)
        apply_review_annotations(
            result,
            json.loads(args.selections.read_text(encoding="utf-8")) if args.selections else None,
            json.loads(args.identities.read_text(encoding="utf-8")) if args.identities else None,
        )
        write_review(result, args.output, repo)
        print(json.dumps({k: v for k, v in result.items() if k != "items"}, ensure_ascii=False))
        return 0
    expected = make_packet(args.reference_ir, args.source, model=args.model, region=args.region,
                           language=args.language, pages=args.pages)
    if args.command == "packet":
        _write(args.output, expected)
        print(f"{len(expected['items'])} pending copy items; candidate only")
        return 0
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    report = check_packet(packet, expected)
    _write(args.output, report)
    if not report["errors"] and args.copy_map:
        _write(args.copy_map, native_copy_map(packet, expected))
    print(f"{report['status']}: {len(report['errors'])} issues")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
