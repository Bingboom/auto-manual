"""Per-target language scope: resolver behaviour and data-table invariants."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.config_loader import load_config_mapping  # noqa: E402
from tools.model_languages import (  # noqa: E402
    language_scope_label,
    load_model_languages,
    resolve_target_languages,
)
from tools.utils.targets import resolve_build_languages  # noqa: E402

EU_FAMILY = ["en", "fr", "es", "de", "it", "uk"]
US_FAMILY = ["en", "fr", "es"]


def _data_dir(rows: str) -> Path:
    td = Path(tempfile.mkdtemp())
    (td / "model_languages.csv").write_text(
        "Document_key,Project,languages,notes\n" + rows, encoding="utf-8")
    return td


class ResolveTargetLanguagesTests(unittest.TestCase):
    def test_row_narrows_family_preserving_family_order(self):
        data = _data_dir("JE-1000F_EU,HTE153,it;en;de;fr;es,note\n")
        scope = resolve_target_languages(
            EU_FAMILY, model="JE-1000F", region="EU", data_dir=data)
        # Family order wins; the table only ever subtracts.
        self.assertEqual(("en", "fr", "es", "de", "it"), scope.languages)
        self.assertEqual(("uk",), scope.dropped)
        self.assertTrue(scope.has_row)
        self.assertTrue(scope.is_trimmed)
        self.assertFalse(scope.unshipped)

    def test_missing_row_keeps_every_family_language(self):
        data = _data_dir("JE-9999X_EU,HTE999,en,note\n")
        scope = resolve_target_languages(
            EU_FAMILY, model="JE-1000F", region="EU", data_dir=data)
        self.assertEqual(tuple(EU_FAMILY), scope.languages)
        self.assertEqual((), scope.dropped)
        self.assertFalse(scope.has_row)
        self.assertFalse(scope.is_trimmed)

    def test_missing_table_keeps_every_family_language(self):
        scope = resolve_target_languages(
            EU_FAMILY, model="JE-1000F", region="EU",
            data_dir=Path(tempfile.mkdtemp()))
        self.assertEqual(tuple(EU_FAMILY), scope.languages)
        self.assertFalse(scope.has_row)

    def test_row_covering_family_is_a_no_op(self):
        data = _data_dir("JE-2000F_EU,HTE154,en;fr;es;de;it;uk,note\n")
        scope = resolve_target_languages(
            EU_FAMILY, model="JE-2000F", region="EU", data_dir=data)
        self.assertEqual(tuple(EU_FAMILY), scope.languages)
        self.assertEqual((), scope.dropped)
        self.assertFalse(scope.is_trimmed)

    def test_disjoint_row_is_unshipped_and_fails_open(self):
        # configs/config.eu-uk.yaml: a uk-only family pointed at a model that
        # ships no uk. The build must not change; check owns the failure.
        data = _data_dir("JE-1000F_EU,HTE153,en;fr;es;de;it,note\n")
        scope = resolve_target_languages(
            ["uk"], model="JE-1000F", region="EU", data_dir=data)
        self.assertEqual(("uk",), scope.languages)
        self.assertEqual((), scope.dropped)
        self.assertTrue(scope.unshipped)

    def test_single_language_derivative_inside_scope_is_untouched(self):
        data = _data_dir("JE-1000F_EU,HTE153,en;fr;es;de;it,note\n")
        scope = resolve_target_languages(
            ["de"], model="JE-1000F", region="EU", data_dir=data)
        self.assertEqual(("de",), scope.languages)
        self.assertFalse(scope.unshipped)

    def test_no_target_keeps_family(self):
        data = _data_dir("JE-1000F_EU,HTE153,en,note\n")
        scope = resolve_target_languages(
            EU_FAMILY, model=None, region=None, data_dir=data)
        self.assertEqual(tuple(EU_FAMILY), scope.languages)
        self.assertIsNone(scope.document_key)

    def test_historical_alias_in_family_matches_canonical_cell(self):
        data = _data_dir("JE-1000F_EU,HTE153,uk;en,note\n")
        scope = resolve_target_languages(
            ["en", "ukr", "fr"], model="JE-1000F", region="EU", data_dir=data)
        self.assertEqual(("en", "ukr"), scope.languages)
        self.assertEqual(("fr",), scope.dropped)

    def test_undeclared_row_language_is_reported(self):
        data = _data_dir("JE-1000F_EU,HTE153,en;fr;ko,note\n")
        scope = resolve_target_languages(
            ["en", "fr"], model="JE-1000F", region="EU", data_dir=data)
        self.assertEqual(("en", "fr"), scope.languages)
        self.assertEqual(("ko",), scope.undeclared)


class LoaderValidationTests(unittest.TestCase):
    def test_missing_column_fails_loudly(self):
        td = Path(tempfile.mkdtemp())
        (td / "model_languages.csv").write_text(
            "Document_key,notes\nJE-1000F_EU,x\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "missing required column"):
            load_model_languages(td)

    def test_duplicate_key_fails_loudly(self):
        data = _data_dir("JE-1000F_EU,H,en,a\nJE-1000F_EU,H,fr,b\n")
        with self.assertRaisesRegex(RuntimeError, "duplicate Document_key"):
            load_model_languages(data)

    def test_unregistered_language_fails_loudly(self):
        data = _data_dir("JE-1000F_EU,H,en;klingon,note\n")
        with self.assertRaisesRegex(RuntimeError, "unregistered language"):
            load_model_languages(data)

    def test_empty_languages_cell_fails_loudly(self):
        data = _data_dir("JE-1000F_EU,H,,note\n")
        with self.assertRaisesRegex(RuntimeError, "empty languages cell"):
            load_model_languages(data)


class LanguageScopeLabelTests(unittest.TestCase):
    def test_label_renders_registry_display_names(self):
        self.assertEqual(
            "English / French / Spanish / German / Italian",
            language_scope_label(("en", "fr", "es", "de", "it")),
        )

    def test_family_literals_match_the_derived_label(self):
        """MANUAL_LANGUAGE_SCOPE in each whole-book config is this rendering.

        The trimmed override replaces that literal, so the derivation has to
        reproduce it exactly for the untrimmed case or a trimmed book would
        silently change wording as well as content.
        """
        checked = 0
        for config_path in sorted((ROOT / "configs").glob("config*.yaml")):
            cfg = load_config_mapping(config_path)
            languages = resolve_build_languages(cfg)
            if len(languages) < 2:
                # Single-language derivatives deliberately advertise the
                # printed book's full scope, not their own one language.
                continue
            literal = (
                (cfg.get("build", {}).get("rst_substitutions") or {})
                .get("MANUAL_LANGUAGE_SCOPE")
            )
            if not literal:
                continue
            self.assertEqual(
                literal, language_scope_label(languages),
                f"{config_path.name} MANUAL_LANGUAGE_SCOPE drifted from its languages",
            )
            checked += 1
        self.assertGreaterEqual(checked, 2, "expected the us/eu merged families")


class TrackedTableTests(unittest.TestCase):
    """data/model_languages.csv must stay consistent with the configs."""

    def setUp(self):
        self.rows = load_model_languages(ROOT / "data")

    def test_table_parses_and_is_not_empty(self):
        self.assertTrue(self.rows)

    def test_every_row_is_a_subset_of_its_whole_book_family(self):
        # Derive region -> whole-book family from the configs themselves
        # rather than hardcoding a map, so a new family is covered for free.
        family_by_region: dict[str, tuple[str, ...]] = {}
        for config_path in sorted((ROOT / "configs").glob("config*.yaml")):
            cfg = load_config_mapping(config_path)
            languages = tuple(resolve_build_languages(cfg))
            if len(languages) < 2:
                continue
            for target in (cfg.get("build", {}).get("targets") or []):
                region = str((target or {}).get("region") or "").strip()
                if region:
                    family_by_region.setdefault(region, languages)
        self.assertTrue(family_by_region, "no whole-book family found")

        for key, languages in sorted(self.rows.items()):
            region = key.rsplit("_", 1)[-1]
            family = family_by_region.get(region)
            if family is None:
                continue
            extra = [lang for lang in languages if lang not in family]
            self.assertEqual(
                [], extra,
                f"{key} lists {extra} which region {region}'s family "
                f"{list(family)} does not declare",
            )

    def test_delivery_map_language_declarations_agree(self):
        """The DingTalk delivery map and the build scope must not disagree.

        The map declares what a published bundle covers; the scope decides
        what the build puts in it. A silent split between the two is exactly
        the defect this table exists to close.
        """
        from tools.dingtalk_delivery_map import load_delivery_map
        from tools.queue_query_languages import canonical_query_lang

        mapped = load_delivery_map(root=ROOT)
        self.assertTrue(mapped)
        compared = 0
        for target in mapped.values():
            key = f"{target.model}_{target.region}"
            shipped = self.rows.get(key)
            if shipped is None:
                continue
            declared = tuple(
                canonical_query_lang(name) for name in target.dingtalk_languages
            )
            self.assertEqual(
                sorted(shipped), sorted(declared),
                f"{key}: delivery map declares {list(declared)} but "
                f"model_languages.csv ships {list(shipped)}",
            )
            compared += 1
        self.assertGreater(compared, 0, "no delivery row overlapped the scope table")


if __name__ == "__main__":
    unittest.main()
