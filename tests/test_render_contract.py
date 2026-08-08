from __future__ import annotations

from copy import deepcopy
import re
import unittest
from pathlib import Path

from tools.csv_to_tex_params import fmt_value
from tools.render_contract import (
    contract_sha256,
    effective_final_mile,
    load_layout_tokens,
    load_render_contract,
    resolve_layout_tokens,
    style_ids,
    validate_render_contract,
)
from tools.render_contract_schema import (
    WEB_COMPONENT_ADAPTERS,
    WORD_COMPONENT_ADAPTERS,
    actionable_debt,
)
from tools.utils.path_utils import Paths, renderer_contracts_of


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)

EXPECTED_STYLE_SEMANTICS = {
    "HB-CALLOUT-STRIP",
    "HB-PAGE-COVER",
    "HB-PAGE-NO-FOOTER",
    "HB-PAGE-STANDARD",
    "HB-SAFETY-DANGER",
    "HB-SAFETY-INSTRUCTION",
    "HB-SAFETY-LEAD",
    "HB-SAFETY-WARNING",
    "HB-SPECIAL-APP",
    "HB-SPECIAL-FCC",
    "HB-SPECIAL-INBOX",
    "HB-SPECIAL-OVERVIEW",
    "HB-TABLE-AUTO-RESUME",
    "HB-TABLE-KEY-COMBINATIONS",
    "HB-TABLE-LCD-ICON",
    "HB-TABLE-LCD-MODE",
    "HB-TABLE-SPEC",
    "HB-TABLE-SYMBOL-ICON",
    "HB-TABLE-SYMBOL-SIGNAL",
    "HB-TABLE-TROUBLESHOOTING",
    "HB-TITLE-L1",
    "HB-TITLE-L2",
    "HB-TITLE-L3",
    "HB-TYPE-BODY",
    "HB-TYPE-FOOTER",
    "HB-TYPE-LEAD",
    "HB-TYPE-LIST",
    "HB-TYPE-PAGE-NUMBER",
    "HB-WARRANTY-LEAD",
    "HB-WARRANTY-SECTION",
    "HB-WARRANTY-YEARS",
}


class RenderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_render_contract(PATHS.manual_style_contract)
        cls.tokens = load_layout_tokens(PATHS.layout_params_csv)

    def test_renderer_contract_path_uses_shared_path_helpers(self) -> None:
        self.assertEqual(PATHS.renderer_contracts_dir, renderer_contracts_of(PATHS.docs_dir))
        self.assertEqual(
            PATHS.manual_style_contract,
            ROOT / "docs" / "renderers" / "contracts" / "manual_style.yaml",
        )

    def test_contract_matches_every_documented_style_id(self) -> None:
        definition = (PATHS.renderer_contracts_dir / "STYLE_DEFINITION.md").read_text(
            encoding="utf-8"
        )
        documented_ids = {
            value
            for value in re.findall(r"\| `([^`]+)` \|", definition)
            if value.startswith("HB-")
        }
        self.assertEqual(EXPECTED_STYLE_SEMANTICS, documented_ids)
        self.assertEqual(documented_ids, style_ids(self.contract))

    def test_committed_contract_closes_all_actionable_style_debt(self) -> None:
        self.assertEqual(EXPECTED_STYLE_SEMANTICS, style_ids(self.contract))
        self.assertEqual([], validate_render_contract(self.contract, self.tokens, strict=True))
        self.assertEqual(
            {},
            {
                style_id: actionable_debt(self.contract, style)
                for style_id, style in self.contract["styles"].items()
                if actionable_debt(self.contract, style)
            },
        )

    def test_contract_has_no_schema_or_token_errors(self) -> None:
        self.assertEqual([], validate_render_contract(self.contract, self.tokens))

    def test_committed_contract_uses_schema_v2(self) -> None:
        self.assertEqual(2, self.contract["schema_version"])

    def test_v1_contract_remains_readable_during_compatibility_window(self) -> None:
        legacy = {
            "schema_version": 1,
            "defaults": {"final_mile": {"content_editable": False}},
            "styles": {
                "HB-DEMO": {
                    "semantic_source_kinds": ["paragraph"],
                    "token_refs": ["type_body_font_size"],
                    "latex": {"owner": "type_system.tex", "entrypoints": ["HBTypeBody"]},
                    "indesign": {"renderer": "paragraph", "paragraph_style": "Body"},
                    "status": "aligned",
                    "debt": [],
                }
            },
        }
        self.assertEqual([], validate_render_contract(legacy, self.tokens))

    def test_plural_indesign_paragraph_styles_are_validated(self) -> None:
        plural_only = deepcopy(self.contract)
        indesign = plural_only["styles"]["HB-TABLE-KEY-COMBINATIONS"]["indesign"]
        indesign.pop("object_style")
        self.assertFalse(any(
            "HB-TABLE-KEY-COMBINATIONS: at least one InDesign style binding"
            in issue
            for issue in validate_render_contract(plural_only, self.tokens)
        ))

        indesign["paragraph_styles"] = ["HB Data Header", ""]
        issues = validate_render_contract(plural_only, self.tokens)
        self.assertTrue(any(
            "HB-TABLE-KEY-COMBINATIONS.indesign.paragraph_styles must be a "
            "list of non-empty strings" in issue
            for issue in issues
        ))

    def test_v2_rejects_unknown_binding_keys(self) -> None:
        malformed = deepcopy(self.contract)
        style = malformed["styles"]["HB-TYPE-BODY"]
        style["web"]["css_patch"] = ".page p"
        style["word"]["style_id"] = "BodyText"
        issues = validate_render_contract(malformed, self.tokens)
        self.assertIn("styles.HB-TYPE-BODY.web: unsupported key 'css_patch'", issues)
        self.assertIn("styles.HB-TYPE-BODY.word: unsupported key 'style_id'", issues)

    def test_v2_rejects_malformed_boundary_records(self) -> None:
        malformed = deepcopy(self.contract)
        malformed["styles"]["HB-TYPE-BODY"]["constraints"] = [
            {"reason": "Web is responsive", "scope": ["web"], "evidence": []}
        ]
        issues = validate_render_contract(malformed, self.tokens)
        self.assertIn(
            "styles.HB-TYPE-BODY.constraints[0].owner must be a non-empty string",
            issues,
        )
        self.assertIn(
            "styles.HB-TYPE-BODY.constraints[0].evidence must be a non-empty list "
            "of non-empty strings",
            issues,
        )

    def test_not_applicable_web_binding_cannot_expose_selectors(self) -> None:
        malformed = deepcopy(self.contract)
        web = malformed["styles"]["HB-PAGE-STANDARD"]["web"]
        web["selectors"] = [".page"]
        issues = validate_render_contract(malformed, self.tokens)
        self.assertIn(
            "styles.HB-PAGE-STANDARD.web: not-applicable capability cannot "
            "declare selectors",
            issues,
        )

    def test_renderer_adapter_and_binding_registries_are_complete(self) -> None:
        css = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                PATHS.docs_dir / "_static" / "hb_manual.css",
                PATHS.renderer_contracts_dir / "web_manual.css",
                PATHS.renderer_contracts_dir / "web_fcc_components.css",
                PATHS.renderer_contracts_dir / "web_inbox_components.css",
                PATHS.renderer_contracts_dir / "web_app_components.css",
                PATHS.renderer_contracts_dir / "web_symbols_fcc_components.css",
            )
        )
        native_selectors = {"p", "ul", "ol", "h1", "h2", "h3"}
        word_style_source = (ROOT / "tools" / "word_bundle_docx_styles.py").read_text(
            encoding="utf-8"
        )
        for style_id, style in self.contract["styles"].items():
            with self.subTest(style_id=style_id):
                web = style["web"]
                self.assertIn(web["component_adapter"], WEB_COMPONENT_ADAPTERS)
                for selector in web["selectors"]:
                    if selector not in native_selectors:
                        self.assertIn(selector, css)
                word = style["word"]
                self.assertIn(word["component_adapter"], WORD_COMPONENT_ADAPTERS)
                for style_name in word["paragraph_styles"] + word["table_styles"]:
                    self.assertIn(f'"{style_name}"', word_style_source)

    def test_generated_latex_params_match_the_layout_token_source(self) -> None:
        prefix = r"\expandafter\def\csname HB"
        separator = r"\endcsname{"
        actual: dict[str, str] = {}
        for line in PATHS.params_tex.read_text(encoding="utf-8").splitlines():
            if not line.startswith(prefix) or separator not in line or not line.endswith("}"):
                continue
            key, value = line[len(prefix):].split(separator, 1)
            self.assertNotIn(key, actual)
            actual[key] = value[:-1]

        expected = {
            key: fmt_value(token.value, token.unit)
            for key, token in self.tokens.items()
        }
        self.assertEqual(expected, actual)

    def test_every_style_forbids_indesign_content_edits(self) -> None:
        for style_id, style in self.contract["styles"].items():
            with self.subTest(style_id=style_id):
                self.assertIs(False, effective_final_mile(self.contract, style)["content_editable"])

    def test_contract_digest_is_deterministic(self) -> None:
        first = contract_sha256(self.contract)
        second = contract_sha256(load_render_contract(PATHS.manual_style_contract))
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_language_overrides_resolve_onto_base_keys(self) -> None:
        base = resolve_layout_tokens(self.tokens)
        french = resolve_layout_tokens(self.tokens, "fr")
        spanish = resolve_layout_tokens(self.tokens, "es")
        self.assertEqual(self.tokens["lang_fr_comp_h1_pill_after"].value, french["comp_h1_pill_after"].value)
        self.assertEqual(self.tokens["lang_es_comp_h1_pill_after"].value, spanish["comp_h1_pill_after"].value)
        self.assertEqual(base["comp_h1_pill_after"].value, self.tokens["comp_h1_pill_after"].value)
        self.assertNotIn("lang_fr_comp_h1_pill_after", french)

    def test_strict_mode_reports_only_actionable_debt(self) -> None:
        issues = validate_render_contract(self.contract, self.tokens, strict=True)
        debt_styles = {
            match.group(1)
            for issue in issues
            if (match := re.search(r"styles\.(HB-[A-Z0-9-]+):", issue))
        }
        self.assertEqual(
            set(),
            debt_styles,
        )
        self.assertEqual(
            debt_styles,
            {
                style_id
                for style_id, style in self.contract["styles"].items()
                if actionable_debt(self.contract, style)
            },
        )

    def test_constraints_and_approved_variants_do_not_fail_strict_mode(self) -> None:
        bounded = deepcopy(self.contract)
        style = bounded["styles"]["HB-TYPE-BODY"]
        record = {
            "reason": "Reviewed projection difference",
            "owner": "renderer-contract-maintainers",
            "scope": ["web"],
            "evidence": ["tests.test_render_contract"],
        }
        style["constraints"] = [deepcopy(record)]
        style["approved_variants"] = [deepcopy(record)]
        issues = validate_render_contract(bounded, self.tokens, strict=True)
        self.assertFalse(any("styles.HB-TYPE-BODY:" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
