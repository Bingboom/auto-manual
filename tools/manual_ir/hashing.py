"""Canonical hashing helpers shared by manual IR builders and validators."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def value_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ordered_files_sha256(files: Iterable[tuple[str, Path]]) -> str:
    digest = hashlib.sha256()
    for display_path, path in files:
        digest.update(display_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(file_sha256(path)))
        digest.update(b"\0")
    return digest.hexdigest()
