#!/usr/bin/env python3
"""Fail-closed ratchet for ``tools/`` top-level modules and script bootstrap code (CQ-1.2).

Domain code is moving into real subpackages (``code_style_guide.md`` §2.16), so
two counts may only go down:

- ``tools/*.py`` top-level modules.  A module missing from the baseline fails the
  check; it can enter the baseline only through ``update --allow NAME=REASON``,
  which records the reason next to it.
- files under ``tools/`` that carry script bootstrap code (an import of
  ``script_bootstrap`` or a ``sys.path.insert(...)`` call), detected from the AST
  so comments and docstrings do not count.  A file that newly carries bootstrap
  code fails the check.

A module or bootstrap that disappeared must be written back in the same change
(``update``), so the gain cannot be silently spent later::

    python tools/check_top_level_module_ratchet.py check
    python tools/check_top_level_module_ratchet.py update [--allow new_tool.py="why it must be top-level"]
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "data" / "top_level_module_baseline.tsv"
_BOOTSTRAP_MODULE = "script_bootstrap"
MODULE = "module"
BOOTSTRAP = "bootstrap"


@dataclass(frozen=True)
class Baseline:
    """Recorded top-level modules (name -> reason, possibly empty) and bootstrap files."""

    modules: dict[str, str] = field(default_factory=dict)
    bootstraps: frozenset[str] = frozenset()


@dataclass(frozen=True)
class RatchetResult:
    modules: tuple[str, ...]
    bootstraps: tuple[str, ...]
    new_modules: tuple[str, ...] = ()
    new_bootstraps: tuple[str, ...] = ()
    removed_modules: tuple[str, ...] = ()
    removed_bootstraps: tuple[str, ...] = ()
    baseline_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.baseline_missing:
            return 2
        failed = (
            self.new_modules
            or self.new_bootstraps
            or self.removed_modules
            or self.removed_bootstraps
        )
        return 1 if failed else 0


def top_level_modules(repo_root: Path = REPO_ROOT) -> tuple[str, ...]:
    tools_root = repo_root / "tools"
    if not tools_root.exists():
        return ()
    return tuple(sorted(path.name for path in tools_root.glob("*.py")))


def _is_sys_path_insert(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "insert"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "path"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "sys"
    )


def _imports_bootstrap(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        return module.split(".")[-1] == _BOOTSTRAP_MODULE or any(
            alias.name == _BOOTSTRAP_MODULE for alias in node.names
        )
    if isinstance(node, ast.Import):
        return any(alias.name.split(".")[-1] == _BOOTSTRAP_MODULE for alias in node.names)
    return False


def uses_bootstrap(path: Path) -> bool:
    """True when ``path`` imports ``script_bootstrap`` or calls ``sys.path.insert``."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return False
    return any(_imports_bootstrap(node) or _is_sys_path_insert(node) for node in ast.walk(tree))


def bootstrap_files(repo_root: Path = REPO_ROOT) -> tuple[str, ...]:
    tools_root = repo_root / "tools"
    if not tools_root.exists():
        return ()
    found = []
    for path in sorted(tools_root.rglob("*.py")):
        if path.stem == _BOOTSTRAP_MODULE or "__pycache__" in path.parts:
            continue
        if uses_bootstrap(path):
            found.append(path.relative_to(repo_root).as_posix())
    return tuple(found)


def load_baseline(path: Path) -> Baseline | None:
    if not path.exists():
        return None
    modules: dict[str, str] = {}
    bootstraps: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        kind, name, *rest = line.split("\t")
        if kind == MODULE:
            modules[name] = rest[0] if rest else ""
        elif kind == BOOTSTRAP:
            bootstraps.add(name)
        else:
            raise ValueError(f"{path}: unknown baseline kind {kind!r}")
    return Baseline(modules, frozenset(bootstraps))


def write_baseline(
    path: Path,
    modules: Iterable[str],
    bootstraps: Iterable[str],
    reasons: dict[str, str],
) -> Path:
    header = (
        "# tools/ top-level modules and files carrying script bootstrap code (CQ-1.2).\n"
        "# Both lists may only shrink. A new top-level module enters only through\n"
        "#   python tools/check_top_level_module_ratchet.py update --allow NAME=REASON\n"
        "# which records the reason in the third column.\n"
    )
    module_rows = "".join(
        f"{MODULE}\t{name}" + (f"\t{reasons[name]}" if reasons.get(name) else "") + "\n"
        for name in sorted(modules)
    )
    bootstrap_rows = "".join(f"{BOOTSTRAP}\t{name}\n" for name in sorted(bootstraps))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + module_rows + bootstrap_rows, encoding="utf-8")
    return path


def compare(
    modules: Iterable[str],
    bootstraps: Iterable[str],
    baseline: Baseline,
) -> RatchetResult:
    current_modules = tuple(modules)
    current_bootstraps = tuple(bootstraps)
    module_set = set(current_modules)
    bootstrap_set = set(current_bootstraps)
    return RatchetResult(
        modules=current_modules,
        bootstraps=current_bootstraps,
        new_modules=tuple(name for name in current_modules if name not in baseline.modules),
        new_bootstraps=tuple(name for name in current_bootstraps if name not in baseline.bootstraps),
        removed_modules=tuple(sorted(name for name in baseline.modules if name not in module_set)),
        removed_bootstraps=tuple(sorted(name for name in baseline.bootstraps if name not in bootstrap_set)),
    )


def check_repository(
    repo_root: Path = REPO_ROOT,
    *,
    baseline_path: Path | None = None,
    printer: Callable[[str], None] = print,
) -> RatchetResult:
    path = baseline_path or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    modules = top_level_modules(repo_root)
    bootstraps = bootstrap_files(repo_root)
    baseline = load_baseline(path)
    if baseline is None:
        printer(f"[top-level] ERROR missing baseline: {path}")
        return RatchetResult(modules, bootstraps, baseline_missing=True)
    result = compare(modules, bootstraps, baseline)
    for name in result.new_modules:
        printer(
            f"[top-level] NEW tools/{name}: put new code in a subpackage, or record why it must be "
            f'top-level with `update --allow {name}="<reason>"`'
        )
    for name in result.new_bootstraps:
        printer(
            f"[top-level] NEW-BOOTSTRAP {name}: run it with `python -m tools.<module>` instead of "
            "adding script bootstrap code"
        )
    for name in result.removed_modules:
        printer(f"[top-level] REMOVED tools/{name}; lock it in with `python tools/check_top_level_module_ratchet.py update`")
    for name in result.removed_bootstraps:
        printer(f"[top-level] REMOVED-BOOTSTRAP {name}; lock it in with `python tools/check_top_level_module_ratchet.py update`")
    printer(
        f"[top-level] {len(modules)} top-level modules (baseline {len(baseline.modules)}), "
        f"{len(bootstraps)} bootstrap files (baseline {len(baseline.bootstraps)})"
    )
    return result


def _parse_allow(values: Iterable[str]) -> dict[str, str]:
    allowed: dict[str, str] = {}
    for value in values:
        name, sep, reason = value.partition("=")
        if not sep or not name.strip() or not reason.strip():
            raise SystemExit(f"--allow expects NAME=REASON, got {value!r}")
        allowed[name.strip()] = reason.strip()
    return allowed


def update_baseline(repo_root: Path, path: Path, allow: dict[str, str]) -> int:
    """Rewrite the baseline; refuse new top-level modules that carry no recorded reason."""
    previous = load_baseline(path)
    modules = top_level_modules(repo_root)
    reasons = dict(previous.modules) if previous is not None else {}
    reasons.update(allow)
    if previous is not None:
        missing = [name for name in modules if name not in previous.modules and name not in allow]
        if missing:
            for name in missing:
                print(f'[top-level] REFUSED tools/{name}: pass --allow {name}="<why it must be top-level>"')
            return 1
    write_baseline(path, modules, bootstrap_files(repo_root), reasons)
    print(f"[top-level] wrote {path}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ratchet tools/ top-level modules and script bootstrap code against a reviewed baseline."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on new modules or bootstrap code, or unrecorded removals"),
        ("update", "rewrite the baseline from the current tree"),
    ):
        subcommand = subcommands.add_parser(command, help=help_text)
        subcommand.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        subcommand.add_argument("--baseline", type=Path, default=None)
        if command == "update":
            subcommand.add_argument(
                "--allow",
                action="append",
                default=[],
                metavar="NAME=REASON",
                help="admit a new top-level module, recording why it must live at tools/ top level",
            )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    baseline = args.baseline or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    if args.command == "update":
        return update_baseline(repo_root, baseline, _parse_allow(args.allow))
    return check_repository(repo_root, baseline_path=baseline).exit_code


if __name__ == "__main__":
    sys.exit(main())
