#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import html
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class DiffRow:
    tracked_root: str
    model: str
    region: str
    artifact: str
    section: str
    page_key: str
    file_name: str
    relative_path: str
    change_type: str
    insertions: str
    deletions: str
    old_path: str
    new_path: str
    from_ref: str
    to_ref: str


def resolve_path_from_root(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def sanitize_token(value: str) -> str:
    out = []
    for ch in value.strip():
        if ch.isalnum() or ch in {"-", "_", "."}:
            out.append(ch)
        else:
            out.append("_")
    text = "".join(out).strip("._")
    return text or "value"


def run_git(args: list[str], *, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


def pathspec_from_root(repo_root: Path, tracked_root: Path) -> str:
    try:
        return tracked_root.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return tracked_root.as_posix()


def parse_name_status(output: str) -> dict[str, tuple[str, str, str]]:
    rows: dict[str, tuple[str, str, str]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0].strip()
        kind = status[:1]
        if kind in {"R", "C"} and len(parts) >= 3:
            old_path = parts[1].strip()
            new_path = parts[2].strip()
        elif len(parts) >= 2:
            old_path = ""
            new_path = parts[1].strip()
        else:
            continue
        rows[new_path or old_path] = (kind, old_path, new_path)
    return rows


def parse_numstat(output: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        insertions = parts[0].strip()
        deletions = parts[1].strip()
        path = parts[-1].strip()
        rows[path] = (insertions, deletions)
    return rows


def extract_bundle_fields(path_text: str) -> tuple[str, str, str, str, str, str]:
    pure = PurePosixPath(path_text)
    parts = pure.parts
    try:
        build_idx = parts.index("_build")
        model = parts[build_idx + 1]
        region = parts[build_idx + 2]
        artifact = parts[build_idx + 3]
        tail = parts[build_idx + 4 :]
    except (ValueError, IndexError):
        return "", "", "", "", pure.name, pure.stem

    section = tail[0] if tail else ""
    file_name = pure.name
    page_key = PurePosixPath(file_name).stem
    relative_path = "/".join(tail) if tail else file_name
    return model, region, artifact, section, relative_path, page_key


def collect_diff_rows(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
) -> list[DiffRow]:
    pathspec = pathspec_from_root(repo_root, tracked_root)
    name_status = parse_name_status(
        run_git(
            ["diff", "--name-status", "--find-renames", from_ref, to_ref, "--", pathspec],
            cwd=repo_root,
        )
    )
    numstat = parse_numstat(
        run_git(
            ["diff", "--numstat", "--find-renames", from_ref, to_ref, "--", pathspec],
            cwd=repo_root,
        )
    )

    rows: list[DiffRow] = []
    for key in sorted(name_status):
        change_type, old_path, new_path = name_status[key]
        stats = numstat.get(new_path) or numstat.get(old_path) or ("", "")
        chosen_path = new_path or old_path
        model, region, artifact, section, relative_path, page_key = extract_bundle_fields(chosen_path)
        rows.append(
            DiffRow(
                tracked_root=pathspec,
                model=model,
                region=region,
                artifact=artifact,
                section=section,
                page_key=page_key,
                file_name=PurePosixPath(chosen_path).name,
                relative_path=relative_path,
                change_type=change_type,
                insertions=stats[0],
                deletions=stats[1],
                old_path=old_path,
                new_path=new_path or old_path,
                from_ref=from_ref,
                to_ref=to_ref,
            )
        )
    return rows


def write_csv_report(rows: list[DiffRow], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "tracked_root",
                "model",
                "region",
                "artifact",
                "section",
                "page_key",
                "file_name",
                "relative_path",
                "change_type",
                "insertions",
                "deletions",
                "old_path",
                "new_path",
                "from_ref",
                "to_ref",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_html_report(rows: list[DiffRow], html_path: Path, *, from_ref: str, to_ref: str) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "tracked_root",
        "model",
        "region",
        "artifact",
        "section",
        "page_key",
        "file_name",
        "relative_path",
        "change_type",
        "insertions",
        "deletions",
        "old_path",
        "new_path",
        "from_ref",
        "to_ref",
    ]
    summary = {
        "files": len(rows),
        "added": sum(1 for row in rows if row.change_type == "A"),
        "modified": sum(1 for row in rows if row.change_type == "M"),
        "deleted": sum(1 for row in rows if row.change_type == "D"),
        "renamed": sum(1 for row in rows if row.change_type == "R"),
    }
    table_head = "".join(f"<th>{html.escape(col)}</th>" for col in headers)
    table_rows = []
    for row in rows:
        cols = "".join(f"<td>{html.escape(str(getattr(row, col)))}</td>" for col in headers)
        table_rows.append(f"<tr>{cols}</tr>")

    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            "  <title>Diff Report</title>",
            "  <style>",
            "    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; }",
            "    table { border-collapse: collapse; width: 100%; font-size: 13px; }",
            "    th, td { border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }",
            "    th { background: #f6f8fa; position: sticky; top: 0; }",
            "    .summary { display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }",
            "    .card { border: 1px solid #d0d7de; border-radius: 8px; padding: 10px 12px; min-width: 120px; }",
            "    .muted { color: #57606a; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>RST Diff Report</h1>",
            f"  <p class=\"muted\">{html.escape(from_ref)} -> {html.escape(to_ref)}</p>",
            "  <div class=\"summary\">",
            f"    <div class=\"card\"><strong>{summary['files']}</strong><div class=\"muted\">files</div></div>",
            f"    <div class=\"card\"><strong>{summary['added']}</strong><div class=\"muted\">added</div></div>",
            f"    <div class=\"card\"><strong>{summary['modified']}</strong><div class=\"muted\">modified</div></div>",
            f"    <div class=\"card\"><strong>{summary['deleted']}</strong><div class=\"muted\">deleted</div></div>",
            f"    <div class=\"card\"><strong>{summary['renamed']}</strong><div class=\"muted\">renamed</div></div>",
            "  </div>",
            "  <table>",
            f"    <thead><tr>{table_head}</tr></thead>",
            f"    <tbody>{''.join(table_rows)}</tbody>",
            "  </table>",
            "</body>",
            "</html>",
        ]
    )
    html_path.write_text(html_text, encoding="utf-8")


def generate_diff_report(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
    output_dir: Path,
) -> tuple[Path, Path]:
    rows = collect_diff_rows(
        repo_root=repo_root,
        tracked_root=tracked_root,
        from_ref=from_ref,
        to_ref=to_ref,
    )
    scope_name = tracked_root.name or "tracked_root"
    base_name = f"{sanitize_token(scope_name)}_{sanitize_token(from_ref)}_to_{sanitize_token(to_ref)}"
    csv_path = output_dir / f"{base_name}.csv"
    html_path = output_dir / f"{base_name}.html"
    write_csv_report(rows, csv_path)
    write_html_report(rows, html_path, from_ref=from_ref, to_ref=to_ref)
    return csv_path, html_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Export git diff under a tracked docs subtree to CSV/HTML.")
    ap.add_argument("--tracked-root", default="docs/_build/JE-1000F", help="Tracked subtree root")
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref")
    ap.add_argument(
        "--output-dir",
        default="reports/version_tracking/JE-1000F",
        help="Output directory for CSV/HTML reports",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tracked_root = resolve_path_from_root(args.tracked_root)
    output_dir = resolve_path_from_root(args.output_dir)
    try:
        csv_path, html_path = generate_diff_report(
            repo_root=ROOT,
            tracked_root=tracked_root,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
            output_dir=output_dir,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or str(exc), file=sys.stderr)
        return exc.returncode or 1

    print(f"[diff_report] CSV: {csv_path}")
    print(f"[diff_report] HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
