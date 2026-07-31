#!/usr/bin/env python3
"""Fail-closed ratchet for hand-written language literal tables.

The language registry is the source of truth for supported languages.  A few
renderer and integration boundaries still contain intentional literal tables,
so this check records the current residue instead of pretending it is already
zero.  Removing a finding is always allowed; adding or changing one requires
an explicit baseline diff in the same PR.

The scanner deliberately looks for AST containers containing at least two
registered language tokens.  It therefore catches language tables without
flagging ordinary prose or a single language comparison.  The baseline is a
reviewed text file, similar to the warning ratchet, and the standalone command
is strict by default::

    python tools/check_language_literal_ratchet.py check
    python tools/check_language_literal_ratchet.py update
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import lang_registry  # noqa: E402


DEFAULT_BASELINE = REPO_ROOT / "data" / "language_literal_baseline.txt"
_EXCLUDED_FILES = {"tools/lang_registry.py"}


@dataclass(frozen=True)
class LanguageLiteralFinding:
    path: str
    kind: str
    tokens: tuple[str, ...]
    fingerprint: str
    line: int

    @property
    def key(self) -> str:
        """Return a stable, line-independent baseline key."""

        return "\t".join((self.path, self.kind, ",".join(self.tokens), self.fingerprint))


@dataclass(frozen=True)
class RatchetResult:
    current: tuple[LanguageLiteralFinding, ...]
    new: tuple[str, ...]
    known: tuple[str, ...]
    stale: tuple[str, ...]
    baseline_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.baseline_missing:
            return 2
        return 1 if self.new else 0


def _source_paths(repo_root: Path) -> Iterable[Path]:
    build_entrypoint = repo_root / "build.py"
    if build_entrypoint.exists():
        yield build_entrypoint
    tools_root = repo_root / "tools"
    if tools_root.exists():
        yield from sorted(tools_root.rglob("*.py"))


def _direct_string_literals(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        items = node.elts
    elif isinstance(node, ast.Dict):
        items = [item for pair in zip(node.keys, node.values) for item in pair]
    else:
        return ()
    return tuple(
        item.value
        for item in items
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    )


def _fingerprint(node: ast.AST) -> str:
    dumped = ast.dump(node, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()[:16]


def collect_findings(repo_root: Path = REPO_ROOT) -> tuple[LanguageLiteralFinding, ...]:
    """Collect language-bearing literal containers from production Python."""

    language_tokens = set(lang_registry.LANGUAGE_BY_ALIAS)
    findings: list[LanguageLiteralFinding] = []
    for path in _source_paths(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        if relative in _EXCLUDED_FILES:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except SyntaxError as exc:
            raise RuntimeError(f"Cannot parse production Python file: {relative}") from exc
        for node in ast.walk(tree):
            raw_tokens = _direct_string_literals(node)
            tokens = tuple(
                sorted(
                    {token for token in raw_tokens if token.casefold() in language_tokens},
                    key=lambda token: (token.casefold(), token),
                )
            )
            if len(tokens) < 2:
                continue
            findings.append(
                LanguageLiteralFinding(
                    path=relative,
                    kind=type(node).__name__.lower(),
                    tokens=tokens,
                    fingerprint=_fingerprint(node),
                    line=getattr(node, "lineno", 0),
                )
            )
    return tuple(sorted(findings, key=lambda finding: finding.key))


def load_baseline(path: Path) -> set[str] | None:
    if not path.exists():
        return None
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def write_baseline(path: Path, findings: Iterable[LanguageLiteralFinding]) -> Path:
    entries = sorted({finding.key for finding in findings})
    header = (
        "# Language-literal table baseline.\n"
        "# A new entry fails the ratchet; stale entries are reported as debt\n"
        "# that can be removed. Regenerate intentionally with:\n"
        "#   python tools/check_language_literal_ratchet.py update\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n".join(entries) + "\n", encoding="utf-8")
    return path


def compare(
    findings: Iterable[LanguageLiteralFinding], baseline: set[str]
) -> RatchetResult:
    current = tuple(findings)
    current_keys = {finding.key for finding in current}
    return RatchetResult(
        current=current,
        new=tuple(sorted(current_keys - baseline)),
        known=tuple(sorted(current_keys & baseline)),
        stale=tuple(sorted(baseline - current_keys)),
    )


def check_repository(
    repo_root: Path = REPO_ROOT,
    *,
    baseline_path: Path | None = None,
    printer: Callable[[str], None] = print,
) -> RatchetResult:
    path = baseline_path or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    findings = collect_findings(repo_root)
    baseline = load_baseline(path)
    if baseline is None:
        result = RatchetResult(findings, (), (), (), baseline_missing=True)
        printer(f"[language-literal] ERROR missing baseline: {path}")
        return result

    result = compare(findings, baseline)
    for entry in result.new:
        printer(f"[language-literal] NEW {entry}")
    for entry in result.stale:
        printer(f"[language-literal] stale-baseline {entry}")
    printer(
        f"[language-literal] {len(result.new)} new, "
        f"{len(result.known)} known, {len(result.stale)} stale, "
        f"{len(result.current)} current"
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ratchet hand-written language literal tables against a reviewed baseline."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on language literal findings missing from the baseline"),
        ("update", "rewrite the baseline from the current findings"),
    ):
        subcommand = subcommands.add_parser(command, help=help_text)
        subcommand.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        subcommand.add_argument("--baseline", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    baseline = args.baseline or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    findings = collect_findings(repo_root)
    if args.command == "update":
        print(f"[language-literal] wrote {write_baseline(baseline, findings)} ({len(findings)} entries)")
        return 0
    return check_repository(repo_root, baseline_path=baseline).exit_code


if __name__ == "__main__":
    raise SystemExit(main())
