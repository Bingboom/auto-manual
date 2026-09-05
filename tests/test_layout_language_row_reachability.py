"""Layout-token ``lang_<code>_`` rows must be reachable at render time.

A measured override row is silently dead if its prefix is not the token the
IDML pipeline actually derives for that language.  ``normalize_lang`` maps the
canonical registry code ``ja`` onto the historical phase2 suffix ``jp``, so a
row keyed by the canonical code never matches and the component falls back to
the shared base value without any error.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from tools.idml.loaders import normalize_lang
from tools.lang_registry import LANGUAGE_REGISTRY
from tools.render_contract import load_layout_token_layers
from tools.utils.path_utils import repo_root

BASE_CSV = repo_root() / "data" / "layout_params.csv"
COMPACT_CSV = repo_root() / "data" / "layout_params.idml-compact.csv"


def _tokens() -> dict[str, object]:
    return load_layout_token_layers(BASE_CSV, (COMPACT_CSV,))


def _language_prefixes(keys) -> dict[str, list[str]]:
    """Group ``lang_<code>_<base>`` keys by their code, longest code first."""
    known = sorted(
        {normalize_lang(spec.code) for spec in LANGUAGE_REGISTRY}
        | {spec.code.casefold() for spec in LANGUAGE_REGISTRY},
        key=len,
        reverse=True,
    )
    grouped: dict[str, list[str]] = {}
    for key in keys:
        if not key.startswith("lang_"):
            continue
        for code in known:
            if key.startswith(f"lang_{code.casefold()}_"):
                grouped.setdefault(code, []).append(key)
                break
        else:
            grouped.setdefault("<unknown>", []).append(key)
    return grouped


class LanguageRowReachability(unittest.TestCase):
    def test_normalize_lang_maps_japanese_onto_the_phase2_suffix(self) -> None:
        """Pin the mapping the reachability of every JP row depends on."""
        self.assertEqual(normalize_lang("ja"), "jp")
        self.assertEqual(normalize_lang("jp"), "jp")

    def test_every_language_row_uses_a_registered_code(self) -> None:
        grouped = _language_prefixes(_tokens())
        self.assertNotIn(
            "<unknown>",
            grouped,
            f"layout rows use an unregistered language code: "
            f"{sorted(grouped.get('<unknown>', []))}",
        )

    def test_language_rows_are_keyed_by_the_pipeline_token(self) -> None:
        """A row keyed by a canonical code the pipeline rewrites is dead.

        ``normalize_lang`` is what turns a page's language into the prefix a
        component looks up, so a row may only use a code that survives it.
        """
        offenders: list[str] = []
        for code, keys in _language_prefixes(_tokens()).items():
            if code == "<unknown>":
                continue
            if normalize_lang(code) != code:
                offenders.extend(
                    f"{key} (pipeline emits lang_{normalize_lang(code)}_)"
                    for key in keys
                )
        self.assertEqual(
            [],
            sorted(offenders),
            "these layout rows can never be reached at render time",
        )

    def test_bp_jp_measured_overrides_resolve_for_the_target_language(self) -> None:
        """The BP@JP measured geometry must beat the shared base values."""
        config = yaml.safe_load(
            (repo_root() / "configs" / "config.bp-jp.yaml").read_text(
                encoding="utf-8"
            )
        )
        declared = config["build"]["languages"]
        self.assertEqual(["ja"], declared, "config language changed; retune below")
        code = normalize_lang(declared[0])

        tokens = _tokens()
        measured = {
            key
            for key in tokens
            if key.startswith("lang_") and "idml_inbox_compact_" in key
        } | {
            key
            for key in tokens
            if key.startswith("lang_") and "idml_warranty_" in key
        }
        japanese = sorted(k for k in measured if k.startswith(f"lang_{code}_"))
        self.assertTrue(
            japanese,
            f"no Japanese layout override is keyed lang_{code}_; the measured "
            f"reference geometry would silently fall back to the base values",
        )
        # A base row is optional: when the shared CSV carries none, the base
        # value is a code default, and the language row is the only source.
        pointless = [
            key
            for key in japanese
            if (base := tokens.get(key[len(f"lang_{code}_") :])) is not None
            and base.value == tokens[key].value
        ]
        self.assertEqual(
            [], pointless, "these language rows just restate their base value"
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
