"""Registry of committed frozen source packages: admission count and shared-input drift.

A frozen source package is a directory under ``manual_sources/`` or
``data/manual_sources/`` that carries a ``source_manifest.json``. Packages are
immutable releases: a library fix alone does not update them
(``code-as-doc/dev/web_publish_pipeline/shared-component-admission.md``).
Before this registry nothing counted them, and a package's own tests skip when
the shared inputs it pinned (``repo_inputs``) drift, so a shared change could
leave packages behind without anyone seeing it.

``data/frozen_package_registry.json`` makes both visible, fail-closed (operator
decision 2026-10-19, 「失败 + 保持冻结」):

- every package is registered with an approval reference; an unregistered
  package, or a registered one that is gone, fails the check;
- every pinned shared input that no longer matches the checkout is recorded per
  package with its handling (``keep-frozen`` or ``rebuild-pending``) and a
  reason; unrecorded drift, and records whose drift has gone, fail the check;
- packages without pins are listed as "impact unknown", never as unaffected.

Each ``record`` call also appends a ``drift_log`` row (files, packages affected,
handling, optional operator minutes) for the roadmap's intervention KPI::

    python -m tools.web.frozen_package_registry check
    python -m tools.web.frozen_package_registry report [--changed PATH ...]
    python -m tools.web.frozen_package_registry register DIR ... --approval "MA-123"
    python -m tools.web.frozen_package_registry unregister DIR ...
    python -m tools.web.frozen_package_registry record --handling keep-frozen --reason "..." [--minutes N]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from tools.utils.path_utils import PathSegments

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "auto-manual-frozen-package-registry/v1"
# Kept here rather than in path_utils: about 20 frozen packages pin
# path_utils.py by hash, so editing it would drift every one of them.
SOURCE_MANIFEST_JSON = "source_manifest.json"
REGISTRY_JSON = "frozen_package_registry.json"
HANDLINGS = ("keep-frozen", "rebuild-pending")
PREFIX = "[frozen-packages]"


@dataclass(frozen=True)
class Package:
    """One frozen source package found in the checkout."""

    key: str
    pins: tuple[tuple[str, str], ...] | None
    error: str = ""


@dataclass(frozen=True)
class RegistryResult:
    packages: int = 0
    unpinned: tuple[str, ...] = ()
    known_drift: int = 0
    new_packages: tuple[str, ...] = ()
    removed_packages: tuple[str, ...] = ()
    new_drift: dict[str, tuple[str, ...]] = field(default_factory=dict)
    stale_drift: dict[str, tuple[str, ...]] = field(default_factory=dict)
    invalid: tuple[str, ...] = ()
    registry_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.registry_missing:
            return 2
        failed = (self.new_packages or self.removed_packages or self.new_drift
                  or self.stale_drift or self.invalid)
        return 1 if failed else 0


def frozen_source_roots_of(repo_root: Path) -> tuple[Path, Path]:
    return (repo_root / PathSegments.MANUAL_SOURCES,
            repo_root / PathSegments.DATA / PathSegments.MANUAL_SOURCES)


def frozen_package_registry_of(repo_root: Path) -> Path:
    return repo_root / PathSegments.DATA / REGISTRY_JSON


def _read_pins(manifest: Path) -> tuple[tuple[tuple[str, str], ...] | None, str]:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"unreadable source_manifest.json: {exc}"
    rows = data.get("repo_inputs") if isinstance(data, dict) else None
    if not rows:
        return None, ""
    pins = tuple((str(row["path"]), str(row["sha256"])) for row in rows
                 if isinstance(row, dict) and "path" in row and "sha256" in row)
    return pins, ""


def discover_packages(repo_root: Path) -> dict[str, Package]:
    found: dict[str, Package] = {}
    for root in frozen_source_roots_of(repo_root):
        if not root.is_dir():
            continue
        for manifest in sorted(root.rglob(SOURCE_MANIFEST_JSON)):
            key = manifest.parent.relative_to(repo_root).as_posix()
            pins, error = _read_pins(manifest)
            found[key] = Package(key, pins, error)
    return found


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def input_matches(path: Path, expected: str, cache: dict[Path, tuple[str, ...]]) -> bool:
    """True when ``path`` still has the pinned bytes.

    A Windows checkout may hold CRLF copies of text files that were pinned with
    LF, so the LF-normalized digest also counts as a match.
    """
    if path not in cache:
        if not path.is_file():
            cache[path] = ()
        else:
            data = path.read_bytes()
            digests = [_sha256(data)]
            if b"\r\n" in data:
                digests.append(_sha256(data.replace(b"\r\n", b"\n")))
            cache[path] = tuple(digests)
    return expected in cache[path]


def drifted_inputs(repo_root: Path, package: Package,
                   cache: dict[Path, tuple[str, ...]]) -> tuple[str, ...]:
    return tuple(sorted(rel for rel, sha in package.pins or ()
                        if not input_matches(repo_root / rel, sha, cache)))


def empty_registry() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "packages": {}, "drift_log": []}


def load_registry(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: schema_version must be {SCHEMA_VERSION}")
    data.setdefault("packages", {})
    data.setdefault("drift_log", [])
    return data


def write_registry(path: Path, registry: dict[str, Any]) -> None:
    registry["packages"] = {key: registry["packages"][key] for key in sorted(registry["packages"])}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _entry_problems(key: str, entry: Any) -> list[str]:
    if not isinstance(entry, dict) or not str(entry.get("approval") or "").strip():
        return [f"{key}: needs a non-empty approval reference"]
    problems = []
    for rel, record in (entry.get("known_drift") or {}).items():
        if not isinstance(record, dict) or record.get("handling") not in HANDLINGS:
            problems.append(f"{key}: {rel}: handling must be one of {', '.join(HANDLINGS)}")
        elif not str(record.get("reason") or "").strip():
            problems.append(f"{key}: {rel}: needs a reason")
    return problems


def compare(repo_root: Path, found: dict[str, Package], registry: dict[str, Any]) -> RegistryResult:
    entries: dict[str, Any] = registry["packages"]
    cache: dict[Path, tuple[str, ...]] = {}
    new_drift: dict[str, tuple[str, ...]] = {}
    stale_drift: dict[str, tuple[str, ...]] = {}
    invalid = [f"{pkg.key}: {pkg.error}" for pkg in found.values() if pkg.error]
    known = 0
    for key, entry in entries.items():
        invalid.extend(_entry_problems(key, entry))
        package = found.get(key)
        if package is None or not isinstance(entry, dict):
            continue
        recorded = set(entry.get("known_drift") or {})
        drifted = set(drifted_inputs(repo_root, package, cache))
        known += len(recorded & drifted)
        if drifted - recorded:
            new_drift[key] = tuple(sorted(drifted - recorded))
        if recorded - drifted:
            stale_drift[key] = tuple(sorted(recorded - drifted))
    return RegistryResult(
        packages=len(found),
        unpinned=tuple(key for key, pkg in found.items() if not pkg.pins and not pkg.error),
        known_drift=known,
        new_packages=tuple(key for key in found if key not in entries),
        removed_packages=tuple(sorted(key for key in entries if key not in found)),
        new_drift=new_drift,
        stale_drift=stale_drift,
        invalid=tuple(invalid),
    )


def _print_failures(result: RegistryResult, printer: Callable[[str], None]) -> None:
    for key in result.new_packages:
        printer(f"{PREFIX} NEW {key}: register it with its approval, "
                f'`python -m tools.web.frozen_package_registry register {key} --approval "MA-..."`')
    for key in result.removed_packages:
        printer(f"{PREFIX} GONE {key}: remove it with `python -m tools.web.frozen_package_registry unregister {key}`")
    for key, paths in result.new_drift.items():
        printer(f"{PREFIX} DRIFT {key}: {len(paths)} pinned shared input(s) changed: {', '.join(paths[:5])}"
                + (" ..." if len(paths) > 5 else ""))
    if result.new_drift:
        printer(f"{PREFIX} record how each drifted package is handled: `python -m tools.web.frozen_package_registry "
                'record --handling keep-frozen|rebuild-pending --reason "..." [--minutes N]`')
    for key, paths in result.stale_drift.items():
        printer(f"{PREFIX} STALE {key}: recorded drift no longer present ({', '.join(paths[:5])}); "
                "run `python -m tools.web.frozen_package_registry record` to drop it")
    for problem in result.invalid:
        printer(f"{PREFIX} INVALID {problem}")


def check_repository(repo_root: Path = REPO_ROOT, *, registry_path: Path | None = None,
                     printer: Callable[[str], None] = print) -> RegistryResult:
    path = registry_path or frozen_package_registry_of(repo_root)
    registry = load_registry(path)
    if registry is None:
        printer(f"{PREFIX} ERROR missing registry: {path}")
        return RegistryResult(registry_missing=True)
    result = compare(repo_root, discover_packages(repo_root), registry)
    _print_failures(result, printer)
    drifting = sum(1 for entry in registry["packages"].values()
                   if isinstance(entry, dict) and entry.get("known_drift"))
    printer(
        f"{PREFIX} {result.packages} packages ({result.packages - len(result.unpinned)} pin shared inputs, "
        f"{len(result.unpinned)} without pins: impact unknown); {result.known_drift} known drift in "
        f"{drifting} packages; {len(result.new_packages)} new, {len(result.removed_packages)} gone, "
        f"{sum(len(v) for v in result.new_drift.values())} new drift, "
        f"{sum(len(v) for v in result.stale_drift.values())} stale"
    )
    return result


def affected_packages(repo_root: Path, changed: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Packages that pin any of ``changed`` (repo-relative paths), with the matching pins."""
    wanted = {Path(item).as_posix() for item in changed}
    hits: dict[str, tuple[str, ...]] = {}
    for key, package in discover_packages(repo_root).items():
        pinned = sorted({rel for rel, _ in package.pins or ()} & wanted)
        if pinned:
            hits[key] = tuple(pinned)
    return hits


def _package_key(repo_root: Path, raw: str) -> str:
    path = Path(raw)
    path = path if path.is_absolute() else repo_root / path
    if path.name == SOURCE_MANIFEST_JSON:
        path = path.parent
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def register(repo_root: Path, registry: dict[str, Any], dirs: Iterable[str], approval: str,
             today: str) -> list[str]:
    if not approval.strip():
        raise ValueError("--approval must name the approval (for example an MA row)")
    found = discover_packages(repo_root)
    added = []
    for raw in dirs:
        key = _package_key(repo_root, raw)
        if key not in found:
            raise ValueError(f"{key}: no {SOURCE_MANIFEST_JSON} under a frozen source root")
        if key in registry["packages"]:
            raise ValueError(f"{key}: already registered")
        registry["packages"][key] = {"approval": approval.strip(), "registered": today, "known_drift": {}}
        added.append(key)
    return added


def unregister(repo_root: Path, registry: dict[str, Any], dirs: Iterable[str]) -> list[str]:
    found = discover_packages(repo_root)
    removed = []
    for raw in dirs:
        key = _package_key(repo_root, raw)
        if key in found:
            raise ValueError(f"{key}: still in the checkout; only a deleted package can be unregistered")
        if registry["packages"].pop(key, None) is not None:
            removed.append(key)
    return removed


def record(repo_root: Path, registry: dict[str, Any], *, handling: str | None, reason: str | None,
           today: str, minutes: int | None = None) -> RegistryResult:
    """Record every unrecorded drift with one handling, and drop stale records."""
    result = compare(repo_root, discover_packages(repo_root), registry)
    if result.new_drift and (handling not in HANDLINGS or not (reason or "").strip()):
        raise ValueError(f"new drift needs --handling ({'/'.join(HANDLINGS)}) and --reason")
    for key, paths in result.stale_drift.items():
        drift = registry["packages"][key]["known_drift"]
        for rel in paths:
            drift.pop(rel, None)
    for key, paths in result.new_drift.items():
        drift = registry["packages"][key].setdefault("known_drift", {})
        for rel in paths:
            drift[rel] = {"handling": handling, "reason": (reason or "").strip(), "since": today}
    if result.new_drift:
        row: dict[str, Any] = {
            "date": today,
            "files": sorted({rel for paths in result.new_drift.values() for rel in paths}),
            "packages": len(result.new_drift),
            "handling": handling,
            "reason": (reason or "").strip(),
        }
        if minutes is not None:
            row["minutes"] = minutes
        registry["drift_log"].append(row)
    return result


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="fail on unregistered packages, unrecorded drift or stale records")
    report = sub.add_parser("report", help="list packages that pin the given shared files")
    report.add_argument("--changed", nargs="*", default=[], help="repo-relative shared paths")
    reg = sub.add_parser("register", help="register new packages with their approval")
    reg.add_argument("dirs", nargs="+")
    reg.add_argument("--approval", required=True)
    unreg = sub.add_parser("unregister", help="drop packages that were deleted")
    unreg.add_argument("dirs", nargs="+")
    rec = sub.add_parser("record", help="record handling for new drift; drop stale records")
    rec.add_argument("--handling", choices=HANDLINGS)
    rec.add_argument("--reason")
    rec.add_argument("--minutes", type=int, help="operator minutes this shared change cost, if known")
    for command in (reg, rec):
        command.add_argument("--date", default=dt.date.today().isoformat())
    return parser.parse_args(argv)


def _report(repo_root: Path, changed: list[str]) -> int:
    found = discover_packages(repo_root)
    hits = affected_packages(repo_root, changed) if changed else {}
    for key, pins in hits.items():
        print(f"{PREFIX} AFFECTED {key}: {', '.join(pins)}")
    unpinned = [key for key, pkg in found.items() if not pkg.pins]
    print(f"{PREFIX} {len(hits)} of {len(found)} packages pin the given files; "
          f"{len(unpinned)} have no pins, so their impact is unknown")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command in (None, "check"):
        return check_repository(repo_root).exit_code
    if args.command == "report":
        return _report(repo_root, args.changed)
    path = frozen_package_registry_of(repo_root)
    registry = load_registry(path) or empty_registry()
    try:
        if args.command == "register":
            changed = register(repo_root, registry, args.dirs, args.approval, args.date)
        elif args.command == "unregister":
            changed = unregister(repo_root, registry, args.dirs)
        else:
            result = record(repo_root, registry, handling=args.handling, reason=args.reason,
                            today=args.date, minutes=args.minutes)
            changed = [*result.new_drift, *result.stale_drift]
    except ValueError as exc:
        print(f"{PREFIX} ERROR {exc}", file=sys.stderr)
        return 2
    write_registry(path, registry)
    print(f"{PREFIX} {args.command}: {len(changed)} package(s) updated in {path.relative_to(repo_root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
