"""Logical names for the Feishu tables a sync-data run reads.

A failed ``lark-cli`` read used to surface only the API error ("you don't have
permission"), never which binding was refused, and sync-data reads tables from
more than one base. This module maps each resolved table id to the logical name
it is configured under, so the failure can say "translation_memory" or
"asset_definitions" without printing the id itself.

The map is built generically, so a new binding is labelled without touching
this file:

* every ``*table_id_env`` key under ``sync.phase2`` — the label is the config
  path without the env suffix (``tables.translation_memory`` →
  ``translation_memory``; ``spec_master_sources.spec_rows_source_table_id_env``
  → ``spec_master_sources.spec_rows_source``);
* every table in the frozen ``data/asset_base_bindings.json`` (asset and Web
  composite tables), labelled by its key there.

Config bindings win over the frozen file when both name the same table id.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from tools.utils.path_utils import PathSegments
from tools.utils.redaction import redact_identifiers

ASSET_BINDINGS_FILE_NAME = "asset_base_bindings.json"
UNLABELLED_TABLE = "unlabelled table"
_TABLE_ID_ENV_SUFFIX = "table_id_env"


def _label_from_path(path: tuple[str, ...], key: str) -> str:
    stem = key[: -len(_TABLE_ID_ENV_SUFFIX)].rstrip("_")
    parts = [*path, stem] if stem else list(path)
    if parts and parts[0] == "tables":
        parts = parts[1:]
    return ".".join(part for part in parts if part) or "phase2"


def _table_id_envs(node: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[str, str]]:
    if not isinstance(node, Mapping):
        return
    for key, value in node.items():
        key_text = str(key)
        if key_text.endswith(_TABLE_ID_ENV_SUFFIX) and isinstance(value, str) and value.strip():
            yield _label_from_path(path, key_text), value.strip()
        elif isinstance(value, Mapping):
            yield from _table_id_envs(value, (*path, key_text))


def _frozen_binding_labels(repo_root: Path) -> dict[str, str]:
    path = Path(repo_root) / PathSegments.DATA / ASSET_BINDINGS_FILE_NAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    tables = payload.get("tables") if isinstance(payload, dict) else None
    if not isinstance(tables, dict):
        return {}
    labels: dict[str, str] = {}
    for key, table in tables.items():
        table_id = str(table.get("table_id") or "").strip() if isinstance(table, dict) else ""
        if table_id:
            labels[table_id] = str(key)
    return labels


def table_labels_from_cfg(
    cfg: Mapping[str, Any],
    *,
    repo_root: Path,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Map every table id this config can read to its logical name."""
    env = os.environ if environ is None else environ
    labels = _frozen_binding_labels(repo_root)
    phase2_cfg = (cfg.get("sync") or {}).get("phase2") or {}
    for label, env_name in _table_id_envs(phase2_cfg):
        table_id = str(env.get(env_name) or "").strip()
        if table_id:
            labels[table_id] = label
    return labels


class LarkCliReadError(RuntimeError):
    """A failed ``lark-cli base`` call, labelled with its logical table and scrubbed of ids."""


_SECRET_FLAGS = ("--base-token", "--table-id", "--view-id", "--record-id")


def _flag_value(args: Sequence[str], flag: str) -> str:
    for index, arg in enumerate(args[:-1]):
        if arg == flag:
            return str(args[index + 1]).strip()
    return ""


def labelled_lark_failure(
    args: Sequence[str],
    message: str,
    table_labels: Mapping[str, str],
) -> str:
    """``[table: <logical name>] <message>`` with every id from ``args`` redacted."""
    table_id = _flag_value(args, "--table-id")
    label = table_labels.get(table_id, UNLABELLED_TABLE) if table_id else "no table"
    known = [_flag_value(args, flag) for flag in _SECRET_FLAGS]
    return f"[table: {label}] {redact_identifiers(message, known)}"


__all__ = (
    "LarkCliReadError",
    "UNLABELLED_TABLE",
    "labelled_lark_failure",
    "table_labels_from_cfg",
)
