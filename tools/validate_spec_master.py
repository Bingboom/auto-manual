#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.validate_spec_master_cli import main, parse_args
from tools.validate_spec_master_runtime import collect_spec_master_validation_issues
from tools.validate_spec_master_shared import (
    _accepted_document_keys,
    _build_langs,
    _collect_target_selectors,
    _effective_targets,
    _first_non_empty,
    _is_truthy,
    _LEGACY_FOOTNOTE_MARKER_RE,
    _LEGACY_SOURCE_HEADERS,
    _parse_ref_ids,
    _pick_document_key,
    _pick_line_number,
    _pick_value,
    _read_optional_rows,
    _repo_relative,
    _row_matches_target,
    _should_require_value_source,
    resolve_docs_dir,
    resolve_spec_master_csv_path,
    SpecMasterValidationIssue,
    SpecSelector,
)

__all__ = [
    "ROOT",
    "SpecMasterValidationIssue",
    "SpecSelector",
    "_accepted_document_keys",
    "_build_langs",
    "_collect_target_selectors",
    "_effective_targets",
    "_first_non_empty",
    "_is_truthy",
    "_LEGACY_FOOTNOTE_MARKER_RE",
    "_LEGACY_SOURCE_HEADERS",
    "_parse_ref_ids",
    "_pick_document_key",
    "_pick_line_number",
    "_pick_value",
    "_read_optional_rows",
    "_repo_relative",
    "_row_matches_target",
    "_should_require_value_source",
    "collect_spec_master_validation_issues",
    "main",
    "parse_args",
    "resolve_docs_dir",
    "resolve_spec_master_csv_path",
]


if __name__ == "__main__":
    raise SystemExit(main())
