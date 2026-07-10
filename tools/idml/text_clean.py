"""Text sanitation shared by the IDML data loaders and prose extraction.

The phase2 source cells and review RST carry three things InDesign must
never see verbatim: ``{{VARIABLE}}`` placeholders (the RST renderers
substitute them via ``tools/utils/variable_resolver``; the IDML path did
not), RST inline roles such as ``V\\ :sub:`oc``` (render as plain text),
and line-block ``| `` prefixes used for forced breaks in cells.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

# export_idml.py runs as a direct script (also from the build queue) with
# tools/ itself on sys.path; the utils package imports with the tools.
# prefix, so make the repo root importable regardless of entry mode.
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.utils.spec_master_lookup import resolve_template_substitutions_from_spec_master
from tools.utils.variable_resolver import resolve_variable_value

_VAR = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
_RST_SUB = re.compile(r"\\?\s*:(?:sub|sup):`([^`]*)`")
_LINE_BLOCK_PIPE = re.compile(r"(?m)^\s*\|\s?")
# line-block pipes that survived upstream line-joining ("... | 2. Check ...")
_JOINED_STEP_PIPE = re.compile(r"(?<=\S)\s*\|\s+(?=\d+\.\s)")
_JOINER = "\\ "


def strip_rst_inline(text: str) -> str:
    """Drop RST inline-markup remnants: sub/sup roles and line-block pipes."""
    cleaned = _RST_SUB.sub(r"\1", text)
    cleaned = cleaned.replace(_JOINER, "")
    cleaned = _JOINED_STEP_PIPE.sub("\n", cleaned)
    return _LINE_BLOCK_PIPE.sub("", cleaned)


class VariableSubstituter:
    """Resolve ``{{KEY}}`` placeholders against the phase2 variable tables."""

    def __init__(self, data_root: Path, *, model: str, lang: str | None,
                 region: str | None = None) -> None:
        self._model = model
        self._lang = lang
        self._defaults = self._read(data_root / "Variable_Defaults.csv")
        self._overrides = self._read(data_root / "Variable_Lang_Overrides.csv")
        spec_csv = data_root / "Spec_Master.csv"
        # PRODUCT_NAME & friends live in Spec_Master, not the variable tables.
        self._spec_subs = (
            resolve_template_substitutions_from_spec_master(
                spec_csv, model=model, region=region, lang=lang or "en")
            if spec_csv.exists() else {}
        )

    @staticmethod
    def _read(path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def apply(self, text: str) -> str:
        def _sub(match: re.Match[str]) -> str:
            # Variable tables first (matches the RST renderers, e.g. the terse
            # "AC" button label); Spec_Master fills what they lack
            # (PRODUCT_NAME and friends).
            value = resolve_variable_value(
                self._defaults,
                self._overrides,
                match.group(1),
                model=self._model,
                lang=self._lang,
            )
            if value is None:
                value = self._spec_subs.get(match.group(1))
            return match.group(0) if value is None else str(value)

        return _VAR.sub(_sub, text)


def clean_cell(text: str, substituter: VariableSubstituter | None = None) -> str:
    """Full sanitation for one table cell."""
    cleaned = strip_rst_inline(text)
    if substituter is not None:
        cleaned = substituter.apply(cleaned)
    return cleaned
