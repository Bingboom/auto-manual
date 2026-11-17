# -*- coding: utf-8 -*-
"""Sidecar manifests and link restoration for Feishu Bitable content backups."""

from __future__ import annotations

from tools.bitable_backup.sidecars import (
    ATTACHMENTS_MANIFEST,
    ATTACHMENTS_SCHEMA_VERSION,
    LINK_FIELD_TYPES,
    LINKS_MANIFEST,
    LINKS_SCHEMA_VERSION,
    TableExportData,
    apply_attachment_verification,
    build_attachments_manifest,
    build_links_manifest,
    build_record_key_index,
    load_attachment_expectations,
    normalize_attachments,
    normalize_link_record_ids,
    plan_and_restore_links,
    write_backup_sidecars,
)

__all__ = [
    "ATTACHMENTS_MANIFEST",
    "ATTACHMENTS_SCHEMA_VERSION",
    "LINK_FIELD_TYPES",
    "LINKS_MANIFEST",
    "LINKS_SCHEMA_VERSION",
    "TableExportData",
    "apply_attachment_verification",
    "build_attachments_manifest",
    "build_links_manifest",
    "build_record_key_index",
    "load_attachment_expectations",
    "normalize_attachments",
    "normalize_link_record_ids",
    "plan_and_restore_links",
    "write_backup_sidecars",
]
