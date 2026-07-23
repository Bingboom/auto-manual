from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.idml.components.base import RenderContext
from tools.idml.components.reference_figure import (
    _derived_crop,
    _download_copy,
    render_referencefigure,
)
from tools.idml.params import load_layout_params


ROOT = Path(__file__).resolve().parents[1]
APP_STYLE_TOKENS = (
    "idml_app_control_label_font_size",
    "idml_app_control_label_font_leading",
    "idml_app_control_label_min_height",
    "idml_app_connect_step_font_size",
    "idml_app_connect_step_font_leading",
    "idml_app_connect_note_font_size",
    "idml_app_connect_note_font_leading",
    "idml_app_connect_note_width",
    "idml_app_text_frame_safety",
)


class EditableReferenceFigureTests(unittest.TestCase):
    def _context(
        self,
        bundle: Path,
        stories: list[tuple[str, str]],
        *,
        params: dict[str, tuple[str, str]] | None = None,
        language: str | None = None,
        strict_component_assets: bool = False,
    ) -> RenderContext:
        def add_story(story_id: str, _title: str, parts: list[str]) -> str:
            stories.append((story_id, "".join(parts)))
            return story_id

        return RenderContext(
            params=(
                params
                if params is not None
                else load_layout_params(ROOT / "data" / "layout_params.csv")
                if strict_component_assets
                else {}
            ),
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=bundle,
            model="JE-1000F",
            region="US",
            language=language,
            strict_component_assets=strict_component_assets,
            add_story=add_story,
        )

    @staticmethod
    def _png(path: Path, size: tuple[int, int]) -> None:
        Image.new("RGB", size, "white").save(path)

    def test_download_copy_uses_last_sentence_for_the_right_column(self) -> None:
        self.assertEqual(
            ("Search in the store. Register and log in.", "Scan the QR code."),
            _download_copy(
                "Search in the store. Register and log in. Scan the QR code."
            ),
        )

    def test_download_group_has_fixed_bounds_despite_auto_height_copy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "download.png", (674, 141))

            xml, height = render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "app_download",
                    "image": "download.png",
                    "copy": "Left sentence. Right sentence.",
                },
                self._context(bundle, []),
                tid="download",
                terminal=False,
            )

            self.assertIn("referencefigure_download_bounds_download", xml)
            self.assertIn('Anchor="312.09 -82.153"', xml)
            self.assertAlmostEqual(84.153, height, places=3)
            self.assertIn("<Content></Content><Br/>", xml)

    def test_charging_car_copy_is_unlocked_and_above_the_art(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "car_charge.png", (1256, 462))
            stories: list[tuple[str, str]] = []

            xml, height = render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "charging_car",
                    "image": "car_charge.png",
                    "vehicle": "Vehicle",
                    "note": "*Cable sold separately.",
                },
                self._context(bundle, stories),
                tid="car",
                terminal=True,
            )

            self.assertGreater(height, 100.0)
            self.assertIn("grp_referencefigure_car", xml)
            self.assertIn("referencefigure_car_note_bg_car", xml)
            self.assertIn("tf_referencefigure_car_note_car", xml)
            self.assertIn("tf_referencefigure_car_vehicle_car", xml)
            self.assertLess(xml.index("carimg"), xml.index("tf_referencefigure_car_note_car"))
            self.assertIn('LockPosition="false" PinPosition="false"', xml)
            self.assertEqual(2, len(stories))
            self.assertIn("Vehicle", stories[1][1])

    def test_nonterminal_figure_ends_its_story_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "car_charge.png", (1256, 462))

            xml, _height = render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "charging_car",
                    "image": "car_charge.png",
                    "vehicle": "Vehicle",
                    "note": "Note",
                },
                self._context(bundle, []),
                tid="car_nonterminal",
                terminal=False,
            )

            self.assertIn("<Content></Content><Br/>", xml)

    def test_app_control_labels_and_step_numbers_are_top_layer_frames(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "add_device.png", (680, 601))
            (bundle / "front_controls.pdf").write_bytes(b"placeholder")
            stories: list[tuple[str, str]] = []

            xml, height = render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "app_add_device",
                    "image": "add_device.png",
                    "control_image": "front_controls.pdf",
                    "step_labels": ["2.1", "2.2"],
                    "labels_by_role": {
                        "main_power": "POWER Button",
                        "dc_usb": "DC / USB",
                        "ac": "AC Power Button",
                    },
                },
                self._context(bundle, stories),
                tid="app",
                terminal=True,
            )

            self.assertGreater(height, 200.0)
            self.assertIn("referencefigure_app_panel_bg_app", xml)
            self.assertIn("appcontrols", xml)
            self.assertEqual(5, xml.count("<TextFrame "))
            first_text = xml.index("<TextFrame ")
            self.assertLess(
                xml.index("referencefigure_app_rule_ac_extension_app"), first_text,
            )
            self.assertEqual(5, xml.count('LockPosition="false" PinPosition="false"'))
            self.assertEqual(5, len(stories))
            self.assertIn('Anchor="23.161 -47.5"', xml)
            self.assertIn('Anchor="75.097 -40.3"', xml)
            self.assertIn('Anchor="22.681 -30.099"', xml)
            self.assertIn('Anchor="100.5 -22.899"', xml)
            self.assertIn('Anchor="248.268 -29.001"', xml)
            self.assertIn('Anchor="310 -21.801"', xml)

    def test_app_control_roles_are_bound_to_visual_slots_not_source_order(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "add_device.png", (680, 601))
            (bundle / "front_controls.pdf").write_bytes(b"placeholder")
            stories: list[tuple[str, str]] = []

            render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "app_add_device",
                    "image": "add_device.png",
                    "control_image": "front_controls.pdf",
                    "step_labels": ["2.1", "2.2"],
                    "labels_by_role": {
                        # Deliberately not visual order. The role keys, not
                        # mapping insertion order or localized words, govern.
                        "ac": "Bouton d’alimentation CA",
                        "main_power": "Bouton POWER",
                        "dc_usb": "Bouton d’alimentation CC/USB",
                    },
                },
                self._context(bundle, stories, language="fr"),
                tid="app_roles",
                terminal=True,
            )

            story_map = dict(stories)
            self.assertIn(
                "Bouton POWER",
                story_map["st_anchor_referencefigure_app_label_0_app_roles"],
            )
            self.assertIn(
                "Bouton d’alimentation CC/USB",
                story_map["st_anchor_referencefigure_app_label_1_app_roles"],
            )
            self.assertIn(
                "Bouton d’alimentation CA",
                story_map["st_anchor_referencefigure_app_label_2_app_roles"],
            )

    def test_approved_app_requires_all_explicit_control_roles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "add_device.png", (680, 601))
            (bundle / "front_controls.pdf").write_bytes(b"placeholder")

            with self.assertRaisesRegex(
                ValueError,
                "approved app_add_device requires labels_by_role",
            ):
                render_referencefigure(
                    {
                        "kind": "referencefigure",
                        "layout": "app_add_device",
                        "image": "add_device.png",
                        "control_image": "front_controls.pdf",
                        "labels": ["POWER", "AC", "DC / USB"],
                    },
                    self._context(
                        bundle,
                        [],
                        language="fr",
                        strict_component_assets=True,
                    ),
                    tid="app_missing_roles",
                    terminal=True,
                )

    def test_approved_app_style_requires_every_numeric_token(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "add_device.png", (680, 601))
            (bundle / "front_controls.pdf").write_bytes(b"placeholder")
            spec = {
                "kind": "referencefigure",
                "layout": "app_add_device",
                "image": "add_device.png",
                "control_image": "front_controls.pdf",
                "labels_by_role": {
                    "main_power": "Main Power Button",
                    "dc_usb": "DC/USB Power Button",
                    "ac": "AC Power Button",
                },
            }
            for token in APP_STYLE_TOKENS:
                for mutation in ("missing", "invalid"):
                    with self.subTest(token=token, mutation=mutation):
                        params = load_layout_params(
                            ROOT / "data" / "layout_params.csv"
                        )
                        if mutation == "missing":
                            del params[token]
                            message = "missing required layout token"
                        else:
                            params[token] = ("not-a-number", "pt")
                            message = "non-numeric layout token"
                        with self.assertRaisesRegex(
                            ValueError,
                            rf"{message}: {token}",
                        ):
                            render_referencefigure(
                                spec,
                                self._context(
                                    bundle,
                                    [],
                                    params=params,
                                    strict_component_assets=True,
                                ),
                                tid=f"app_style_{mutation}",
                                terminal=True,
                            )

    def test_approved_reference_figure_missing_primary_image_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)

            with self.assertRaisesRegex(
                FileNotFoundError,
                "approved referencefigure image is unavailable",
            ):
                render_referencefigure(
                    {
                        "kind": "referencefigure",
                        "layout": "app_add_device",
                        "image": "missing-add-device.png",
                    },
                    self._context(
                        bundle,
                        [],
                        strict_component_assets=True,
                    ),
                    tid="app_missing_primary",
                    terminal=True,
                )

    def test_approved_app_missing_control_art_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "add_device.png", (680, 601))

            with self.assertRaisesRegex(
                FileNotFoundError,
                "approved app_add_device control_image is unavailable",
            ):
                render_referencefigure(
                    {
                        "kind": "referencefigure",
                        "layout": "app_add_device",
                        "image": "add_device.png",
                        "control_image": "missing-controls.pdf",
                        "labels_by_role": {
                            "main_power": "Main",
                            "dc_usb": "DC/USB",
                            "ac": "AC",
                        },
                    },
                    self._context(
                        bundle,
                        [],
                        strict_component_assets=True,
                    ),
                    tid="app_missing_controls",
                    terminal=True,
                )

    def test_app_figure_style_tokens_control_type_and_safe_frame_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "add_device.png", (680, 601))
            (bundle / "front_controls.pdf").write_bytes(b"placeholder")
            stories: list[tuple[str, str]] = []
            params = {
                "idml_app_control_label_font_size": ("4.7", "pt"),
                "idml_app_control_label_font_leading": ("5.6", "pt"),
                "idml_app_control_label_min_height": ("8.0", "pt"),
                "idml_app_connect_step_font_size": ("5.1", "pt"),
                "idml_app_connect_step_font_leading": ("5.9", "pt"),
                "idml_app_text_frame_safety": ("1.1", "pt"),
            }

            xml, _height = render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "app_add_device",
                    "image": "add_device.png",
                    "control_image": "front_controls.pdf",
                    "step_labels": ["2.1", "2.2"],
                    "labels_by_role": {
                        "main_power": "A deliberately long main power label",
                        "dc_usb": "DC / USB",
                        "ac": "AC",
                    },
                },
                self._context(bundle, stories, params=params),
                tid="app_tokens",
                terminal=True,
            )

            story_map = dict(stories)
            self.assertIn(
                'PointSize="4.7"',
                story_map["st_anchor_referencefigure_app_label_0_app_tokens"],
            )
            self.assertIn(
                '<Leading type="unit">5.6</Leading>',
                story_map["st_anchor_referencefigure_app_label_0_app_tokens"],
            )
            self.assertIn(
                'PointSize="5.1"',
                story_map["st_anchor_referencefigure_app_step_0_app_tokens"],
            )
            self.assertIn('AutoSizingType="HeightOnly"', xml)
            self.assertNotIn('Anchor="23.161 -47.5"', xml)

    def test_app_connect_note_uses_shared_width_and_type_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "connect_result.png", (1046, 651))
            stories: list[tuple[str, str]] = []
            params = {
                "idml_app_connect_note_font_size": ("5.4", "pt"),
                "idml_app_connect_note_font_leading": ("6.1", "pt"),
                "idml_app_connect_note_width": ("190", "pt"),
                "idml_app_text_frame_safety": ("1.0", "pt"),
            }

            xml, _height = render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "app_connect_result",
                    "image": "connect_result.png",
                    "step_labels": ["2.3", "2.4", "2.5"],
                    "reference_note": (
                        "Las capturas de pantalla anteriores sirven solo de referencia."
                    ),
                },
                self._context(bundle, stories, params=params, language="es"),
                tid="connect_tokens",
                terminal=True,
            )

            story_map = dict(stories)
            note = story_map[
                "st_anchor_referencefigure_connect_note_connect_tokens"
            ]
            self.assertIn('PointSize="5.4"', note)
            self.assertIn('<Leading type="unit">6.1</Leading>', note)
            self.assertIn('Anchor="215.934 0"', xml)
            self.assertIn('AutoSizingType="HeightOnly"', xml)

    def test_app_connect_result_is_cropped_and_captioned_with_top_frames(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            self._png(bundle / "connect_result.png", (1046, 651))
            stories: list[tuple[str, str]] = []

            xml, height = render_referencefigure(
                {
                    "kind": "referencefigure",
                    "layout": "app_connect_result",
                    "image": "connect_result.png",
                    "step_labels": ["2.3", "2.4", "2.5"],
                    "reference_note": "Reference only.",
                },
                self._context(bundle, stories),
                tid="connect",
                terminal=False,
            )

            crop = (
                bundle / "_generated" / "idml_reference_assets"
                / "connect_result_screens.png"
            )
            self.assertTrue(crop.is_file())
            with Image.open(crop) as image:
                self.assertEqual((1046, 587), image.size)
            self.assertAlmostEqual(178.0, height, places=3)
            self.assertIn('SpaceBefore="12"', xml)
            self.assertEqual(4, xml.count("<TextFrame "))
            self.assertEqual(4, xml.count('LockPosition="false" PinPosition="false"'))
            self.assertLess(xml.index("connectimg"), xml.index("<TextFrame "))
            self.assertIn("<Content></Content><Br/>", xml)
            self.assertEqual(4, len(stories))

    def test_derived_crop_rejects_symlinked_generated_parent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle"
            outside = root / "outside"
            bundle.mkdir()
            outside.mkdir()
            source = bundle / "connect_result.png"
            self._png(source, (1046, 651))
            (bundle / "_generated").symlink_to(
                outside,
                target_is_directory=True,
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "derived IDML crop destination must not use a symbolic link",
            ):
                _derived_crop(
                    self._context(bundle, []),
                    source,
                    name="screens",
                    box=(0, 0, 1046, 587),
                )

            self.assertEqual([], list(outside.iterdir()))

    def test_derived_crop_rejects_symlinked_target_without_touching_victim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle"
            bundle.mkdir()
            source = bundle / "connect_result.png"
            self._png(source, (1046, 651))
            target_dir = bundle / "_generated" / "idml_reference_assets"
            target_dir.mkdir(parents=True)
            victim = root / "victim.png"
            victim.write_bytes(b"outside-victim")
            target = target_dir / "connect_result_screens.png"
            target.symlink_to(victim)

            with self.assertRaisesRegex(
                RuntimeError,
                "derived IDML crop destination must not be a symbolic link",
            ):
                _derived_crop(
                    self._context(bundle, []),
                    source,
                    name="screens",
                    box=(0, 0, 1046, 587),
                )

            self.assertEqual(b"outside-victim", victim.read_bytes())
            self.assertTrue(target.is_symlink())


if __name__ == "__main__":
    unittest.main()
