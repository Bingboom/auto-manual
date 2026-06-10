#!/usr/bin/env python3
"""Verify that relative markdown links under code-as-doc/ and user-guide/ resolve.

Doc/code drift is a load-bearing risk in this repo: maintainer-facing docs in
code-as-doc/ are the architectural reference, but they reference files in
tools/, scripts/, docs/, and elsewhere by relative path. When code is renamed
or moved without updating the docs, links silently rot.

This script walks every .md file under the configured roots, extracts inline
markdown links, and verifies each relative target exists. External URLs and
pure in-page anchors are skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import unquote


DEFAULT_ROOTS = ("code-as-doc", "user-guide")

# Captures the target inside [label](target). Supports nested parens in label
# but not in target (rare in practice; flagged as broken if encountered).
LINK_PATTERN = re.compile(r"\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(([^()\s]+)\)")

EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "tel:")

# Repo-relative path prefixes that are generated, gitignored, or external. Links
# pointing here are valid references to where output lands but the target does
# not exist in a clean checkout. Match the .gitignore plus the publish/release
# output roots that build.py and the queue workers write under.
SKIP_REPO_RELATIVE_PREFIXES = (
    ".tmp/",
    "data/phase2/",
    "docs/_build/",
    "docs/_review/",
    "docs/generated/",
    "site/review-preview/dist/",
    "site/publish-latest/dist/",
    "reports/releases/",
    "../auto-manual-parity/",
)

# Archived/historical docs intentionally retain references to removed code
# (phase1 modules, prior parity sibling repos, etc.) as part of the record.
# Skip them rather than rewrite history.
SKIP_DOC_FILES = (
    "code-as-doc/code_optimization_log.md",
    "code-as-doc/maintainability_refactor_tracker.md",
    "code-as-doc/phase2_lark_setup_and_parity_plan.md",
)


@dataclass(frozen=True)
class BrokenLink:
    source_file: str
    line_number: int
    raw_target: str
    resolved_path: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check relative markdown link integrity under documentation roots."
    )
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root to inspect.",
    )
    parser.add_argument(
        "--root",
        dest="roots",
        action="append",
        help=(
            "Additional doc root to scan (relative to --repo-root). "
            f"Defaults: {', '.join(DEFAULT_ROOTS)}."
        ),
    )
    return parser.parse_args(argv)


def iter_markdown_files(repo_root: Path, roots: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw_root in roots:
        root_path = (repo_root / raw_root).resolve()
        if not root_path.exists():
            continue
        files.extend(sorted(root_path.rglob("*.md")))
    return files


def _is_external(target: str) -> bool:
    return target.startswith(EXTERNAL_PREFIXES)


def _strip_anchor(target: str) -> str:
    return target.split("#", 1)[0]


def extract_link_targets(md_text: str) -> list[tuple[int, str]]:
    """Return (line_number, raw_target) tuples for every markdown link."""
    results: list[tuple[int, str]] = []
    for match in LINK_PATTERN.finditer(md_text):
        target = match.group(1)
        line_number = md_text.count("\n", 0, match.start()) + 1
        results.append((line_number, target))
    return results


def _is_skipped_target(repo_root: Path, candidate: Path, decoded_target: str) -> bool:
    if decoded_target.startswith("../auto-manual-parity/"):
        return True
    try:
        rel = candidate.relative_to(repo_root)
    except ValueError:
        return False
    rel_text = str(rel).replace("\\", "/")
    rel_with_slash = rel_text + "/"
    for prefix in SKIP_REPO_RELATIVE_PREFIXES:
        if prefix.startswith("../"):
            continue
        if rel_text == prefix.rstrip("/") or rel_with_slash.startswith(prefix):
            return True
    return False


def check_file(repo_root: Path, md_file: Path) -> list[BrokenLink]:
    text = md_file.read_text(encoding="utf-8", errors="replace")
    failures: list[BrokenLink] = []
    for line_number, raw_target in extract_link_targets(text):
        if _is_external(raw_target):
            continue
        path_part = _strip_anchor(raw_target)
        if not path_part:
            continue  # pure anchor link like #section
        decoded = unquote(path_part)
        candidate = (md_file.parent / decoded).resolve()
        if candidate.exists():
            continue
        if _is_skipped_target(repo_root, candidate, decoded):
            continue
        failures.append(
            BrokenLink(
                source_file=str(md_file.relative_to(repo_root)).replace("\\", "/"),
                line_number=line_number,
                raw_target=raw_target,
                resolved_path=str(candidate).replace("\\", "/"),
            )
        )
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    roots = args.roots if args.roots else list(DEFAULT_ROOTS)

    md_files = iter_markdown_files(repo_root, roots)
    if not md_files:
        print(f"[doc-links] No markdown files found under {roots}.")
        return 0

    skipped_files: set[str] = {path for path in SKIP_DOC_FILES}
    checked_files: list[Path] = []
    skipped_count = 0
    total_links = 0
    all_failures: list[BrokenLink] = []
    for md_file in md_files:
        rel = str(md_file.relative_to(repo_root)).replace("\\", "/")
        if rel in skipped_files:
            skipped_count += 1
            continue
        checked_files.append(md_file)
        text = md_file.read_text(encoding="utf-8", errors="replace")
        total_links += sum(1 for _ in LINK_PATTERN.finditer(text))
        all_failures.extend(check_file(repo_root, md_file))

    if all_failures:
        print(
            f"[doc-links] {len(all_failures)} broken link(s) found "
            f"across {len(checked_files)} markdown file(s):"
        )
        for failure in all_failures:
            print(
                f"  {failure.source_file}:{failure.line_number} -> {failure.raw_target}"
            )
        return 1

    print(
        f"[doc-links] Checked {len(checked_files)} markdown file(s) "
        f"({skipped_count} archived skipped), {total_links} link(s), 0 broken."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
