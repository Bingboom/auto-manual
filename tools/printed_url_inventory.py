#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Printed-URL inventory (Milestone I4).

URLs and e-mail addresses that ship inside built manuals are unfixable after
print — a QR on a shipped back cover cannot be re-pointed. Nothing watched
their liveness: the repo's doc-link check covers maintainer markdown only.

This tool scans every text source that feeds built manuals (templates,
renderer components, family configs, the tracked phase2 CSV mirror) and
writes a tracked inventory ``data/printed_url_inventory.csv``. QR/image
targets are not text-scannable — register them by hand in
``data/printed_url_manual_entries.csv`` (they merge into the inventory).

Commands:

- ``scan``      rewrite the inventory from the current sources
- ``check``     regenerate in memory and fail (exit 1) if the committed
                inventory is stale — keeps the inventory honest in CI
- ``liveness``  HEAD-request every URL (network; the monthly ops pass,
                never CI)
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

INVENTORY_CSV = Path("data") / "printed_url_inventory.csv"
MANUAL_ENTRIES_CSV = Path("data") / "printed_url_manual_entries.csv"

SCAN_ROOTS = (
    "docs/templates",
    "docs/renderers",
    "docs/manifests",
    "configs",
    "data/phase2",
)
TEXT_SUFFIXES = {".rst", ".tex", ".sty", ".yaml", ".yml", ".csv", ".txt", ".json", ".md"}

_URL_RE = re.compile(r"https?://[^\s\"'<>\\)\]}|,，]+")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_MAX_SOURCES_LISTED = 3


def _strip_trailing_punct(target: str) -> str:
    return target.rstrip(".;:。；：、")


def scan_sources(repo_root: Path) -> dict[str, dict]:
    """target -> {kind, occurrences, sources} across the manual-feeding trees."""
    found: dict[str, dict] = {}

    def _record(target: str, kind: str, source: str) -> None:
        entry = found.setdefault(
            target, {"kind": kind, "occurrences": 0, "sources": set()}
        )
        entry["occurrences"] += 1
        entry["sources"].add(source)

    for root in SCAN_ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in files:
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(repo_root).as_posix()
            for match in _URL_RE.findall(text):
                _record(_strip_trailing_punct(match), "url", rel)
            for match in _EMAIL_RE.findall(text):
                _record(match, "email", rel)
    return found


def load_manual_entries(repo_root: Path) -> dict[str, dict]:
    path = repo_root / MANUAL_ENTRIES_CSV
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for row in csv.DictReader(path.open(encoding="utf-8")):
        target = (row.get("target") or "").strip()
        if not target:
            continue
        out[target] = {
            "kind": (row.get("kind") or "manual").strip() or "manual",
            "occurrences": 1,
            "sources": {(row.get("source_note") or "manual entry").strip()},
            "asset_key": (row.get("asset_key") or "").strip(),
        }
    return out


QR_CATEGORY = "二维码"


def crosscheck_qr_targets(records, *, repo_root: Path) -> tuple[tuple[str, str, str], ...]:
    """Every shippable QR asset must declare what it actually encodes.

    A QR is the one printed element whose payload cannot be read off the
    page during review, so the registry alone cannot say whether the right
    thing ships. Pairing each approved QR asset with a manual inventory
    entry makes the payload a tracked fact, and keeps a quarantined or
    stand-in candidate from being registered as a live printed target.

    Returns (code, asset_key, message) triples; empty means consistent.
    """
    entries = load_manual_entries(repo_root)
    registered: dict[str, str] = {}
    for target, entry in entries.items():
        asset_key = entry.get("asset_key")
        if asset_key:
            registered[asset_key] = target

    issues: list[tuple[str, str, str]] = []
    approved: set[str] = set()
    for record in records:
        if getattr(record, "category", "") != QR_CATEGORY:
            continue
        shippable = record.status == "✅成品"
        if shippable:
            approved.add(record.asset_key)
            if record.asset_key not in registered:
                issues.append((
                    "qr_target_unregistered",
                    record.asset_key,
                    "approved QR asset has no printed-target entry in "
                    f"{MANUAL_ENTRIES_CSV.as_posix()}; record what it encodes",
                ))
        elif record.asset_key in registered:
            issues.append((
                "qr_target_not_shippable",
                record.asset_key,
                f"{record.status} QR asset is registered as the printed target "
                f"{registered[record.asset_key]!r}",
            ))

    known = {record.asset_key for record in records}
    for asset_key, target in sorted(registered.items()):
        if asset_key not in known:
            issues.append((
                "qr_target_unknown_asset",
                asset_key,
                f"printed target {target!r} points at an unregistered asset",
            ))
    return tuple(issues)


def build_inventory_rows(repo_root: Path) -> list[dict[str, str]]:
    entries = scan_sources(repo_root)
    for target, manual in load_manual_entries(repo_root).items():
        if target in entries:
            entries[target]["sources"] |= manual["sources"]
        else:
            entries[target] = manual
    rows = []
    for target in sorted(entries):
        entry = entries[target]
        sources = sorted(entry["sources"])
        listed = ";".join(sources[:_MAX_SOURCES_LISTED])
        if len(sources) > _MAX_SOURCES_LISTED:
            listed += f";(+{len(sources) - _MAX_SOURCES_LISTED} more)"
        rows.append(
            {
                "target": target,
                "kind": entry["kind"],
                "occurrences": str(entry["occurrences"]),
                "sources": listed,
            }
        )
    return rows


def render_inventory_csv(rows: list[dict[str, str]]) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["target", "kind", "occurrences", "sources"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def check_liveness(rows: list[dict[str, str]], *, timeout: float = 10.0, printer=print) -> int:
    import urllib.error
    import urllib.request

    failures = 0
    for row in rows:
        if row["kind"] == "email" or not row["target"].startswith("http"):
            continue
        target = row["target"]
        request = urllib.request.Request(target, method="HEAD", headers={"User-Agent": "auto-manual-url-inventory"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                printer(f"[printed-urls] OK {response.status} {target}")
        except urllib.error.HTTPError as exc:
            level = "OK" if exc.code in (403, 405) else "DEAD"  # bot-blocked ≠ dead
            if level == "DEAD":
                failures += 1
            printer(f"[printed-urls] {level} {exc.code} {target}")
        except Exception as exc:
            failures += 1
            printer(f"[printed-urls] DEAD {target} ({exc})")
    printer(f"[printed-urls] liveness: {failures} failure(s)")
    return 1 if failures else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="printed_url_inventory",
        description="Inventory every URL/e-mail that ships inside built manuals.",
    )
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan", help="Rewrite data/printed_url_inventory.csv from sources.")
    sub.add_parser("check", help="Fail if the committed inventory is stale.")
    liveness = sub.add_parser("liveness", help="HEAD-request every URL (network; monthly ops).")
    liveness.add_argument("--timeout", type=float, default=10.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root
    rows = build_inventory_rows(repo_root)
    inventory_path = repo_root / INVENTORY_CSV
    if args.command == "scan":
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(render_inventory_csv(rows), encoding="utf-8")
        print(f"[printed-urls] wrote {inventory_path} ({len(rows)} target(s))")
        return 0
    if args.command == "check":
        current = render_inventory_csv(rows)
        committed = inventory_path.read_text(encoding="utf-8") if inventory_path.exists() else ""
        if current != committed:
            print(
                "[printed-urls] inventory is stale — run "
                "`python tools/printed_url_inventory.py scan` and commit the diff"
            )
            return 1
        print(f"[printed-urls] inventory current ({len(rows)} target(s))")
        return 0
    return check_liveness(rows, timeout=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
