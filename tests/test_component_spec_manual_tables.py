from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.component_specs.manual_table_adapters import (
    idml_manual_table_payload,
    latex_manual_table_projection,
    web_manual_table_projection,
    word_manual_table_projection,
)
from tools.component_specs.manual_table_html import (
    parse_lcd_icon_html,
    parse_symbol_tables_html,
    parse_troubleshooting_html,
)
from tools.component_specs.manual_tables import (
    LCD_ICON_COMPONENT_ID,
    SYMBOL_ICON_COMPONENT_ID,
    SYMBOL_SIGNAL_COMPONENT_ID,
    TROUBLESHOOTING_COMPONENT_ID,
)
from tools.component_specs.model import ComponentAsset, ComponentSpec
from tools.component_specs.registry import (
    load_component_registry,
    validate_component_registry,
    validate_component_spec,
)
from tools.manual_ir.whole_document_components import (
    ComponentClaim,
    _rebind_spec_assets,
    discover_registered_components,
)
from tools.utils.path_utils import Paths
from tools.web_document_ir import render_document_fragments
from tools.web_document_source import load_web_document
from tools.web_presentation import load_web_manual_contract
from tools.word_bundle_html import (
    _publish_rst_fragment_to_html,
    _rewrite_word_friendly_fragment,
)
from tools.word_bundle_html_only import _build_word_only_tags


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


def _lcd_html(*, rows: int = 2) -> str:
    values = []
    for index in range(1, rows + 1):
        values.append(
            "<tr><td>{0}</td><td><img src=\"{0}.png\" alt=\"Icon {0}\" "
            "width=\"42\"></td><td><strong>Name {0}</strong></td>"
            "<td><p>Meaning {0}</p></td></tr>".format(index)
        )
    return "<table><tbody>" + "".join(values) + "</tbody></table>"


def _troubleshooting_html() -> str:
    return (
        "<table><thead><tr><th>Error Code</th><th>Corrective Measures</th></tr>"
        "</thead><tbody><tr><td>F0</td><td><p>Restart <strong>once</strong>.</p>"
        "</td></tr><tr><td>F1</td><td>Contact support.</td></tr></tbody></table>"
    )


def _symbols_html(*, left: int, right: int) -> str:
    signal = (
        "<table><thead><tr><th>Symbol</th><th>Meaning</th></tr></thead><tbody>"
        '<tr><td><span class="hb-warning-lockup"><span aria-hidden="true">⚠</span>'
        "<span>WARNING</span></span></td><td>Serious hazard.</td></tr>"
        '<tr><td><span class="hb-warning-lockup"><span aria-hidden="true">⚠</span>'
        "<span>NOTE</span></span></td><td>Useful detail.</td></tr></tbody></table>"
    )
    rows = ["<tr><td><strong>Symbol</strong></td><td><strong>Meaning</strong></td>"
            "<td><strong>Symbol</strong></td><td><strong>Meaning</strong></td></tr>"]
    for index in range(max(left, right)):
        left_cells = (
            f'<td><img src="left-{index}.png" alt="Left {index}"></td>'
            f"<td>Left meaning {index}</td>"
            if index < left else "<td></td><td></td>"
        )
        right_cells = (
            f'<td><img src="right-{index}.png" alt="Right {index}"></td>'
            f"<td>Right meaning {index}</td>"
            if index < right else "<td></td><td></td>"
        )
        rows.append(f"<tr>{left_cells}{right_cells}</tr>")
    return signal + "<table><tbody>" + "".join(rows) + "</tbody></table>"


class ManualTableComponentSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_component_registry(PATHS.component_registry_contract)

    def test_registry_registers_four_components_and_repeatable_icon_roles(self) -> None:
        self.assertEqual([], validate_component_registry(self.registry))
        for component_id in (
            LCD_ICON_COMPONENT_ID,
            TROUBLESHOOTING_COMPONENT_ID,
            SYMBOL_SIGNAL_COMPONENT_ID,
            SYMBOL_ICON_COMPONENT_ID,
        ):
            with self.subTest(component_id=component_id):
                definition = self.registry["components"][component_id]
                self.assertEqual({"web", "latex", "idml", "word"}, set(definition["adapters"]))
        self.assertTrue(
            self.registry["components"][LCD_ICON_COMPONENT_ID]["asset_roles"]["icons"]["multiple"]
        )
        self.assertTrue(
            self.registry["components"][SYMBOL_ICON_COMPONENT_ID]["asset_roles"]["icons"]["multiple"]
        )

    def test_repeatable_asset_roles_are_ordered_and_single_roles_stay_unique(self) -> None:
        soup = BeautifulSoup(_lcd_html(), "html.parser")
        spec, boundary, images = parse_lcd_icon_html(
            soup,
            source_path=Path("renamed_display.rst"),
            declared_page=True,
            language="en",
        )
        self.assertEqual(["1.png", "2.png"], [asset.asset_ref for asset in spec.assets])
        packaged = {id(image): f"assets/ir/{index}.png" for index, image in enumerate(images)}
        rebound = _rebind_spec_assets(
            ComponentClaim(
                spec=spec,
                owned_nodes=(boundary,),
                asset_tags=tuple(("icons", image) for image in images),
            ),
            package_image=lambda image: packaged[id(image)],
            package_file=lambda path: str(path),
        )
        self.assertEqual(
            ["assets/ir/0.png", "assets/ir/1.png"],
            [asset.asset_ref for asset in rebound.assets],
        )
        invalid = ComponentSpec(
            component_id="HB-SPECIAL-OPERATION",
            variant="status-right",
            source_ref="demo",
            language="en",
            slots=(),
            assets=(
                ComponentAsset("artwork", "one.png", "shared"),
                ComponentAsset("artwork", "two.png", "shared"),
            ),
            token_roles=("component.special.operation",),
        )
        self.assertTrue(
            any("duplicate asset role 'artwork'" in issue for issue in validate_component_spec(invalid, self.registry))
        )

    def test_four_specs_preserve_rich_copy_assets_and_renderer_semantics(self) -> None:
        lcd, _, _ = parse_lcd_icon_html(
            BeautifulSoup(_lcd_html(), "html.parser"),
            source_path=Path("lcd.rst"),
            declared_page=True,
            language="en",
        )
        trouble, _, _ = parse_troubleshooting_html(
            BeautifulSoup(_troubleshooting_html(), "html.parser"),
            source_path=Path("trouble.rst"),
            declared_page=True,
            language="en",
        )
        signal, icons = parse_symbol_tables_html(
            BeautifulSoup(_symbols_html(left=3, right=1), "html.parser"),
            source_path=Path("symbols.rst"),
            expected_signal_rows=2,
            language="en",
        )
        specs = (lcd, trouble, signal[0], icons[0])
        self.assertEqual(
            [LCD_ICON_COMPONENT_ID, TROUBLESHOOTING_COMPONENT_ID,
             SYMBOL_SIGNAL_COMPONENT_ID, SYMBOL_ICON_COMPONENT_ID],
            [spec.component_id for spec in specs],
        )
        self.assertEqual([3, 1], [len(panel) for panel in icons[0].slot("panels").content])
        self.assertIn("<strong>Name 1</strong>", lcd.slot("rows").content[0]["name_html"])
        self.assertIn("<strong>once</strong>", trouble.slot("rows").content[0]["measures_html"])
        for spec in specs:
            with self.subTest(component_id=spec.component_id):
                self.assertEqual([], validate_component_spec(spec, self.registry))
                self.assertIn("component_class", web_manual_table_projection(spec))
                self.assertIn("environment", latex_manual_table_projection(spec))
                self.assertIn("kind", idml_manual_table_payload(spec))
                self.assertTrue(word_manual_table_projection(spec)["editable"])

    def test_variable_symbol_panels_are_supported_but_partial_pairs_fail_closed(self) -> None:
        for left, right in ((6, 5), (5, 2)):
            with self.subTest(left=left, right=right):
                _, icons = parse_symbol_tables_html(
                    BeautifulSoup(_symbols_html(left=left, right=right), "html.parser"),
                    source_path=Path("symbols.rst"),
                    expected_signal_rows=2,
                    language="ko" if right == 2 else "en",
                )
                self.assertEqual([left, right], [len(panel) for panel in icons[0].slot("panels").content])
        malformed = _symbols_html(left=2, right=1).replace(
            '<td><img src="right-0.png" alt="Right 0"></td><td>Right meaning 0</td>',
            '<td><img src="right-0.png" alt="Right 0"></td><td></td>',
        )
        with self.assertRaisesRegex(ValueError, "symbol pair"):
            parse_symbol_tables_html(
                BeautifulSoup(malformed, "html.parser"),
                source_path=Path("symbols.rst"),
                expected_signal_rows=2,
                language="en",
            )

    def test_real_us_and_kr_sources_keep_all_rows_and_variable_panels(self) -> None:
        contract = load_web_manual_contract()
        targets = (
            ("JE-1000F", "US", "en", ROOT / "docs/_review/JE-1000F/US/page", [6, 5]),
            ("JE-3000C", "KR", "ko", ROOT / "docs/_review/JE-3000C/KR/ko/page", [5, 2]),
        )
        for model, region, language, page_root, panel_counts in targets:
            with self.subTest(model=model, region=region, language=language):
                tags = _build_word_only_tags(model=model, region=region, lang=language)
                found = {}
                for stem, role in (
                    ("lcd_icons", "lcd_icons"),
                    ("troubleshooting", "troubleshooting"),
                    ("symbols", "symbols"),
                ):
                    path = page_root / f"{stem}_{language}.rst"
                    markup = _rewrite_word_friendly_fragment(
                        _publish_rst_fragment_to_html(
                            path.read_text(encoding="utf-8"), path, active_tags=tags
                        ),
                        lang=language,
                    )
                    claims = discover_registered_components(
                        BeautifulSoup(markup, "html.parser"),
                        source_path=path,
                        contract=contract,
                        model=model,
                        region=region,
                        language=language,
                        declared_role=role,
                    )
                    found.update({claim.spec.component_id: claim.spec for claim in claims})
                self.assertEqual(26, len(found[LCD_ICON_COMPONENT_ID].slot("rows").content))
                self.assertEqual(11, len(found[TROUBLESHOOTING_COMPONENT_ID].slot("rows").content))
                self.assertEqual(4, len(found[SYMBOL_SIGNAL_COMPONENT_ID].slot("rows").content))
                self.assertEqual(
                    panel_counts,
                    [len(panel) for panel in found[SYMBOL_ICON_COMPONENT_ID].slot("panels").content],
                )

    def test_declared_renamed_pages_discover_components_without_filename_heuristics(self) -> None:
        contract = deepcopy(load_web_manual_contract())
        lcd_claims = discover_registered_components(
            BeautifulSoup(_lcd_html(), "html.parser"),
            source_path=Path("renamed_display.rst"),
            contract=contract,
            model="OTHER",
            region="KR",
            language="ko",
            declared_role="lcd_icons",
        )
        trouble_claims = discover_registered_components(
            BeautifulSoup(_troubleshooting_html(), "html.parser"),
            source_path=Path("service_codes.rst"),
            contract=contract,
            model="OTHER",
            region="KR",
            language="ko",
            declared_role="troubleshooting",
        )
        self.assertEqual([LCD_ICON_COMPONENT_ID], [claim.spec.component_id for claim in lcd_claims])
        self.assertEqual([TROUBLESHOOTING_COMPONENT_ID], [claim.spec.component_id for claim in trouble_claims])

    def test_whole_document_cold_replay_dispatches_native_tables_without_legacy_projectors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            page = root / "display.rst"
            for index in (1, 2):
                (root / f"{index}.png").write_bytes(f"icon-{index}".encode())
            page.write_text(
                ".. raw:: html\n\n" + "\n".join(f"   {line}" for line in _lcd_html().splitlines()) + "\n",
                encoding="utf-8",
            )
            materialized = SimpleNamespace(
                model="OTHER",
                region="KR",
                lang="ko",
                languages=("ko",),
                bundle_dir=root,
                title="LCD",
            )
            package = root / "package"
            ir = load_web_document(
                materialized,
                page_paths=(page,),
                declarations={page: "lcd_icons"},
                page_languages={page.name: "ko"},
                active_tags={"not_latex"},
                output_dir=package,
                composite_manifest=None,
            )
            self.assertEqual(
                [LCD_ICON_COMPONENT_ID],
                [spec.component_id for spec in __import__(
                    "tools.component_specs.projection", fromlist=["project_manual_ir_components"]
                ).project_manual_ir_components(ir)],
            )
            page.unlink()
            with patch(
                "tools.web_presentation.transform_lcd_icon_tables",
                side_effect=AssertionError("legacy LCD projector called"),
            ):
                fragment = render_document_fragments(ir, package_root=package)[0]
            soup = BeautifulSoup(fragment, "html.parser")
            self.assertEqual(1, len(soup.select("figure.hb-lcd-table-composition")))
            self.assertEqual(2, len(soup.select("img.hb-lcd-icon-art")))
            self.assertIn("Name 1", soup.get_text(" ", strip=True))


if __name__ == "__main__":
    unittest.main()
