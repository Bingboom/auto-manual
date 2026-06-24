#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live Feishu transports + table-binding parsing for cloud-doc backport.

Extracted from cloud_doc_backport.py (debt-paydown D2). Self-contained (lazy
imports of the lark-cli transports inside the functions; no Block/pipeline dep).
Re-exported by cloud_doc_backport.
"""
from __future__ import annotations

from typing import Any


def _parse_table_bindings(specs: list[str]) -> dict[str, tuple[str, str]]:
    """Parse ``--table-binding 'TABLE=BASE:TABLE_ID'`` specs into ``{table: (base, table_id)}``."""
    bindings: dict[str, tuple[str, str]] = {}
    for spec in specs:
        name, sep, rest = str(spec).partition("=")
        base, sep2, table_id = rest.partition(":")
        name, base, table_id = name.strip(), base.strip(), table_id.strip()
        if not (name and sep and sep2 and base and table_id):
            raise RuntimeError(f"--table-binding must look like TABLE=BASE:TABLE_ID, got: {spec!r}")
        bindings[name] = (base, table_id)
    return bindings

def _source_table_transport(bindings: dict[str, tuple[str, str]], *, lark_cli: str, identity: str) -> Any:
    """Build a live F6 transport whose ``binding_for`` resolves only the given tables.

    An unmapped table raises, which ``apply_change_requests`` isolates per-request
    (status ``error``) — so e.g. a derived ``Localized_Copy`` table is skipped safely.
    """
    from tools.feishu_record_transport import SourceTableLarkTransport
    from tools.sync_data import LarkCliSource

    def binding_for(table: str) -> tuple[str, str]:
        try:
            return bindings[table]
        except KeyError:
            raise RuntimeError(f"no writable --table-binding for table {table!r}") from None

    source = LarkCliSource(cli_bin=lark_cli, identity=identity)
    return SourceTableLarkTransport(source=source, binding_for=binding_for)

def _tm_transport(spec: str, *, lark_cli: str, identity: str) -> Any:
    """Build a live Translation_Memory transport from a ``BASE:TABLE_ID`` binding."""
    from tools.feishu_record_transport import TranslationMemoryLarkTransport
    from tools.sync_data import LarkCliSource

    base, sep, table_id = str(spec or "").partition(":")
    base, table_id = base.strip(), table_id.strip()
    if not (sep and base and table_id):
        raise RuntimeError(f"--tm-binding must look like BASE:TABLE_ID, got: {spec!r}")
    source = LarkCliSource(cli_bin=lark_cli, identity=identity)
    return TranslationMemoryLarkTransport(source=source, base_token=base, table_id=table_id)
