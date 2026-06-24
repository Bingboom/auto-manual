#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared constants + small scaffolding helpers for cloud-doc backport (D2-5).

Schema-version strings + counters / git-ref / timestamp / source-path resolution
used across the diff / apply / report / CLI layers. Imports only stdlib + the
model. Re-exported by cloud_doc_backport.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cloud_doc_backport_model import _read_text  # noqa: E402
from tools.utils.path_utils import get_paths  # noqa: E402


REPORT_SCHEMA_VERSION = "cloud-doc-backport-report/v1"

APPLY_SCHEMA_VERSION = "cloud-doc-backport-apply/v1"

VERIFY_SCHEMA_VERSION = "cloud-doc-backport-verify/v1"

RUN_SCHEMA_VERSION = "cloud-doc-backport-run/v1"

SOURCE_TABLE_SUGGESTIONS_SCHEMA_VERSION = "cloud-doc-backport-source-table-suggestions/v1"

TEMPLATE_SYNC_PROPOSAL_SCHEMA_VERSION = "cloud-doc-backport-template-sync-proposal/v1"

NORMALIZER_VERSION = "cloud-doc-normalizer/v4"

def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _git_ref() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=get_paths().root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    ref = completed.stdout.strip()
    return ref or None

def _counter_dict(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))

def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON file must contain an object: {path}")
    return payload

def _resolve_source_path(value: str | None, *, label: str) -> Path:
    if not value:
        raise RuntimeError(f"missing {label}")
    path = Path(value)
    if not path.is_absolute():
        path = get_paths().root / path
    if not path.exists():
        raise RuntimeError(f"{label} does not exist: {value}")
    if not path.is_file():
        raise RuntimeError(f"{label} must be a file: {value}")
    return path

def _validate_apply_source(path: Path, *, kind: str) -> None:
    if path.suffix != ".rst":
        raise RuntimeError(f"{kind} source must be an .rst file: {path}")
    if kind == "template":
        if "templates" not in path.parts:
            raise RuntimeError(f"template source must live under a templates directory: {path}")
        return
    if kind == "review":
        if "_review" not in path.parts:
            raise RuntimeError(f"review source must live under docs/_review: {path}")
        return
    raise RuntimeError(f"unsupported apply source kind: {kind}")

def _resolve_repo_file(root: Path, value: str | None, *, label: str) -> Path:
    if not value:
        raise RuntimeError(f"missing {label}")
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"{label} must live under repo root: {value}") from exc
    if not resolved.exists():
        raise RuntimeError(f"{label} does not exist: {value}")
    if not resolved.is_file():
        raise RuntimeError(f"{label} must be a file: {value}")
    return resolved
