#!/usr/bin/env python3
"""Read-only, dependency-free checks for mirror-owned content (never a deploy receipt)."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess


OWNED = {
    "Bingboom/Hello-Docs": ("docs/publish/", "docs/knowledge/"),
    "Bingboom/Hello-Docs-Review": ("docs/review-drafts/",),
}
ALL_OWNED = tuple(prefix for prefixes in OWNED.values() for prefix in prefixes)


def git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True,
    )
    return result.stdout.decode("utf-8").rstrip("\0").split("\0") if result.stdout else []


def safe_file(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if not relative or parts.is_absolute() or ".." in parts.parts or "\\" in relative:
        raise ValueError(f"unsafe relative path: {relative}")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError(f"file escapes content root or is a symlink: {relative}")
    if not path.is_file():
        raise ValueError(f"missing file: {relative}")
    return path


def validate_publish(root: Path) -> None:
    manifest_path = safe_file(root, "publish_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "auto-manual-web-publish-branch/v2":
        raise ValueError("unsupported publish manifest schema")
    if not isinstance(manifest.get("targets"), list) or not manifest["targets"]:
        raise ValueError("publish manifest needs nonempty targets")
    identities = set()
    for target in manifest["targets"]:
        identity = tuple(target[key] for key in ("model", "region", "lang"))
        if not all(isinstance(value, str) and value for value in identity) or identity in identities:
            raise ValueError("missing or duplicate publish target identity")
        identities.add(identity)
        safe_file(root, f"web/{target['route']}/{target['manual']}")
    if not isinstance(manifest.get("files"), list) or not manifest["files"]:
        raise ValueError("publish manifest needs a nonempty file inventory")
    recorded = set()
    for item in manifest["files"]:
        relative = item["path"]
        if relative in recorded or relative == "publish_manifest.json":
            raise ValueError(f"duplicate or recursive inventory entry: {relative}")
        recorded.add(relative)
        path = safe_file(root, relative)
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if path.stat().st_size != item["size"] or digest != item["sha256"]:
            raise ValueError(f"publish file size/hash mismatch: {relative}")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != recorded | {"publish_manifest.json"}:
        raise ValueError("publish manifest inventory does not match the file tree")


def check(root: Path, repository: str, *, base: str = "", base_ref: str = "", pr: bool = False) -> None:
    owned = OWNED[repository]
    tracked = set(git(root, "ls-files", "-z"))
    forbidden = tuple(prefix for prefix in ALL_OWNED if prefix not in owned)
    if any(path.startswith(forbidden) for path in tracked):
        raise ValueError("repository contains content owned by the other mirror")
    changed = git(root, "diff", "--name-only", "--no-renames", "-z", base, "HEAD") if base else sorted(tracked)
    allowed = owned + (("docs/_review/",) if repository == "Bingboom/Hello-Docs" and base_ref.startswith("review/") else ())
    if pr and (not base or any(not path.startswith(allowed) for path in changed)):
        raise ValueError("business PR must change only owned content (review backports: docs/_review)")
    selected = [path for path in changed if path in tracked and path.startswith(allowed)]
    for relative in selected:
        path = safe_file(root, relative)
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8-sig"))
        elif path.suffix == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for _row in csv.reader(handle, strict=True):
                    pass
    if repository == "Bingboom/Hello-Docs" and any(p.startswith("docs/publish/") for p in changed):
        # Deleting the entire publication tree must not silently pass.
        validate_publish(root / "docs" / "publish")
    print(f"Business content checks passed: {repository}; {len(selected)} changed/current content files")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", choices=OWNED, required=True)
    parser.add_argument("--base", default="", help="PR base SHA or previous push SHA, fetched locally")
    parser.add_argument("--base-ref", default="", help="PR base branch (review/* enables existing backports)")
    parser.add_argument("--pr", action="store_true")
    args = parser.parse_args()
    try:
        check(Path.cwd(), args.repository, base=args.base, base_ref=args.base_ref, pr=args.pr)
    except (ValueError, KeyError, TypeError, OSError, csv.Error, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Business content check failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
