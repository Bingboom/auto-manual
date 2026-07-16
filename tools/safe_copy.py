"""Fail-closed copy helpers for inputs that become part of a build bundle."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


_IGNORED_DIR_NAMES = frozenset({"__pycache__", ".mypy_cache", ".pytest_cache"})
_IGNORED_FILE_NAMES = frozenset({".DS_Store"})
_IGNORED_FILE_SUFFIXES = frozenset({".pyc", ".pyo", ".swp", ".swo", ".tmp"})


def _is_runtime_junk(path: Path) -> bool:
    if path.name in _IGNORED_FILE_NAMES:
        return True
    if path.name.endswith("~") or path.name.startswith(".#"):
        return True
    return path.suffix.casefold() in _IGNORED_FILE_SUFFIXES


def assert_source_tree_no_symlinks(root: Path, *, label: str) -> None:
    """Reject a source tree containing any symlink before bytes are copied."""

    if root.is_symlink():
        raise RuntimeError(f"{label} must not be a symbolic link: {root}")
    if not root.exists():
        return
    if not root.is_dir():
        raise RuntimeError(f"{label} is not a directory: {root}")
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"{label} must not contain symbolic links: {path}")


def _assert_source_file_no_symlinks(
    source: Path,
    *,
    source_root: Path,
    label: str,
) -> None:
    if source_root.is_symlink():
        raise RuntimeError(f"{label} root must not be a symbolic link: {source_root}")
    try:
        relative = source.relative_to(source_root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes its source root: {source}") from exc
    current = source_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"{label} must not use a symbolic link: {current}")
    if not source.is_file():
        raise RuntimeError(f"{label} is not a regular file: {source}")
    try:
        source.resolve(strict=True).relative_to(source_root.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes its source root: {source}") from exc


def _prepare_destination(
    destination: Path,
    *,
    destination_root: Path,
    label: str,
) -> Path:
    """Create a destination parent without traversing symlinks below its root."""

    root = Path(os.path.abspath(destination_root))
    target = Path(os.path.abspath(destination))
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} destination escapes its root: {destination}") from exc
    if not relative.parts or ".." in relative.parts:
        raise RuntimeError(f"{label} destination escapes its root: {destination}")
    if root.is_symlink():
        raise RuntimeError(f"{label} destination root must not be a symbolic link: {root}")
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"{label} destination root is not a safe directory: {root}")
    canonical_root = root.resolve(strict=True)

    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(
                f"{label} destination must not use a symbolic link: {current}"
            )
        if current.exists() and not current.is_dir():
            raise RuntimeError(f"{label} destination parent is not a directory: {current}")
        current.mkdir(exist_ok=True)
        if current.is_symlink():
            raise RuntimeError(
                f"{label} destination must not use a symbolic link: {current}"
            )
        try:
            current.resolve(strict=True).relative_to(canonical_root)
        except ValueError as exc:
            raise RuntimeError(f"{label} destination escapes its root: {current}") from exc

    target = current / relative.name
    if target.is_symlink():
        raise RuntimeError(f"{label} destination must not be a symbolic link: {target}")
    try:
        target.resolve(strict=False).relative_to(canonical_root)
    except ValueError as exc:
        raise RuntimeError(f"{label} destination escapes its root: {target}") from exc
    return target


def prepare_file_destination_no_symlinks(
    destination: Path,
    *,
    destination_root: Path,
    label: str,
) -> Path:
    """Return a lexical file target after rejecting symlinks in its path."""

    return _prepare_destination(
        destination,
        destination_root=destination_root,
        label=label,
    )


def copy_regular_file_no_symlinks(
    source: Path,
    destination: Path,
    *,
    source_root: Path,
    destination_root: Path | None = None,
    label: str,
) -> None:
    """Copy one regular file without following source or destination symlinks."""

    _assert_source_file_no_symlinks(source, source_root=source_root, label=label)
    target = _prepare_destination(
        destination,
        destination_root=destination_root or destination.parent,
        label=label,
    )
    if target.exists() and not target.is_file():
        raise RuntimeError(f"{label} destination is not a regular file: {target}")
    shutil.copy2(source, target, follow_symlinks=False)
    if target.is_symlink() or not target.is_file():
        raise RuntimeError(f"{label} did not copy to a regular file: {target}")
    _prepare_destination(
        target,
        destination_root=destination_root or destination.parent,
        label=label,
    )


def _ignore_runtime_junk(directory: str, names: list[str]) -> set[str]:
    root = Path(directory)
    ignored: set[str] = set()
    for name in names:
        path = root / name
        if name in _IGNORED_DIR_NAMES or (not path.is_dir() and _is_runtime_junk(path)):
            ignored.add(name)
    return ignored


def copytree_replace_no_symlinks(
    source: Path,
    destination: Path,
    *,
    destination_root: Path | None = None,
    label: str,
) -> None:
    """Replace a destination tree from deterministic, non-symlink source files."""

    assert_source_tree_no_symlinks(source, label=label)
    target = _prepare_destination(
        destination,
        destination_root=destination_root or destination.parent,
        label=label,
    )
    if target.exists():
        if not target.is_dir():
            raise RuntimeError(f"{label} destination is not a directory: {target}")
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        symlinks=True,
        ignore=_ignore_runtime_junk,
    )
    _prepare_destination(
        target,
        destination_root=destination_root or destination.parent,
        label=label,
    )
    assert_source_tree_no_symlinks(target, label=f"copied {label}")


__all__ = (
    "assert_source_tree_no_symlinks",
    "copy_regular_file_no_symlinks",
    "copytree_replace_no_symlinks",
    "prepare_file_destination_no_symlinks",
)
