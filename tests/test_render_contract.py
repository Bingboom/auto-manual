from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.render_contract import (
    contract_sha256,
    effective_final_mile,
    load_layout_tokens,
    load_render_contract,
    resolve_layout_tokens,
    style_ids,
    validate_render_contract,
)
from tools.utils.path_utils import Paths, renderer_contracts_of


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


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

    def test_contract_matches_every_public_latex_style_id(self) -> None:
        registry = (PATHS.latex_renderer_dir / "STYLE_REGISTRY.md").read_text(encoding="utf-8")
        registry_ids = {
            value
            for value in re.findall(r"\| `([^`]+)` \|", registry)
            if value.startswith("HB-")
        }
        self.assertEqual(31, len(registry_ids))
        self.assertEqual(registry_ids, style_ids(self.contract))

    def test_contract_has_no_schema_or_token_errors(self) -> None:
        self.assertEqual([], validate_render_contract(self.contract, self.tokens))

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

    def test_strict_mode_exposes_remaining_renderer_debt(self) -> None:
        issues = validate_render_contract(self.contract, self.tokens, strict=True)
        self.assertTrue(issues)
        self.assertTrue(any("HB-TITLE-L1" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
