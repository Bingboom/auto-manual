from __future__ import annotations

import hashlib
import inspect
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import pages, shared_page, symbols_page


ROOT = Path(__file__).resolve().parents[1]
BASE_PARAMS = ROOT / "data" / "layout_params.csv"
COMPACT_PARAMS = ROOT / "data" / "layout_params.idml-compact.csv"

COPY = {
    "en": {
        "h1": "IMPORTANT SAFETY INFORMATION",
        "instruction": "INSTRUCTIONS",
        "warning_label": "WARNING",
        "warning": "Always follow these precautions.",
        "subbar": "OPERATING INSTRUCTIONS",
        "lead": "SAVE THESE INSTRUCTIONS",
        "item": "Read all instructions.",
        "symbols": "MEANING OF SYMBOLS",
        "headers": ("Symbol", "Meaning"),
        "maintenance": "USER MAINTENANCE INSTRUCTIONS",
        "maintenance_body": "Keep the product clean.",
        "danger": "DANGER",
    },
    "fr": {
        "h1": "INFORMATIONS DE SÉCURITÉ IMPORTANTES",
        "instruction": "INSTRUCTIONS",
        "warning_label": "AVERTISSEMENT",
        "warning": "Respectez toujours ces précautions.",
        "subbar": "INSTRUCTIONS D’UTILISATION",
        "lead": "CONSERVEZ CES INSTRUCTIONS",
        "item": "Lisez toutes les instructions.",
        "symbols": "SIGNIFICATION DES SYMBOLES",
        "headers": ("Symbole", "Signification"),
        "maintenance": "INSTRUCTIONS D’ENTRETIEN",
        "maintenance_body": "Gardez le produit propre.",
        "danger": "DANGER",
    },
    "es": {
        "h1": "INFORMACIÓN DE SEGURIDAD IMPORTANTE",
        "instruction": "INSTRUCCIONES",
        "warning_label": "ADVERTENCIA",
        "warning": "Siga siempre estas precauciones.",
        "subbar": "INSTRUCCIONES DE FUNCIONAMIENTO",
        "lead": "CONSERVE ESTAS INSTRUCCIONES",
        "item": "Lea todas las instrucciones.",
        "symbols": "SIGNIFICADO DE LOS SÍMBOLOS",
        "headers": ("Símbolo", "Significado"),
        "maintenance": "INSTRUCCIONES DE MANTENIMIENTO",
        "maintenance_body": "Mantenga limpio el producto.",
        "danger": "PELIGRO",
    },
}

GOLDEN = {
    "en": {
        "standard": (
            "b05cdfc3dc0f3e76ff1db5c90320d29a0fdf26811d6e7fbe8199ca34e97bcbb7",
            "031f8f464a48c773145e19b8cee0cfed513ea33fa476c549620559798fbc550e",
        ),
        "compact": (
            "ff5a33cd0e41bd7307166c8e6cf19d51eba10c07f5e886f4b96291898c647852",
            "5ead970679e7f4996ed3c08da7a977bade911231b40ab81d2a9997e68befbfe0",
        ),
        "maintenance": (
            "3ec6fa6df6ae7d59f2c2daa8be07f9fe924775ce2565c32d63733c97c3ae31a3",
            "1c596928ba4d834fba6d42c253631cfbbf93b7b6a05419028467eb9905c2af5a",
        ),
    },
    "fr": {
        "standard": (
            "0d024f31507633de055897277b523d6bbb413304d5d745d1eca0ecfe3c735540",
            "69bf42d38d645da95ed2744a889903628999480017b7427d54c2f6479772e216",
        ),
        "compact": (
            "d03feba64928d93189f060ae479847ae6804cf59d3516b0813e54b85aca1ce7b",
            "75f5d3a48cb0894d2e7e74e9ec1181e8c8d901aefda0fa2210e793737efb0458",
        ),
        "maintenance": (
            "213357adf04fb79f6d6aac61db2b3ffcb7601be46b3bfcaa72d713bac1998fa4",
            "d4e40338e4069b2d72a03ebce765102b08f4604a4dd9e0b7d3f7a661dfe5663d",
        ),
    },
    "es": {
        "standard": (
            "fe9fbc6f6d61ddb1f16fa2c18df7c47db84fbc8257d3c0f92837dd1febc8a1e9",
            "736ac2da8cf14dc64774c6d40391d95ea1401e48b1e1d29fa0a264b4f14e5254",
        ),
        "compact": (
            "f9a812cb596412259b464594fc9975feaa4a573cb0720436b41af7af30f9b5fb",
            "c9c661fb090ac2b0425d68b5e1adc58f671c946b76681e21da676fd830d5469b",
        ),
        "maintenance": (
            "76aa126f07865dbec52b58f9537d19165872dad0684791ad18a17068bbba948f",
            "c2b3f1c69c3edc889b49ce6ae8cd7320056ff3a4a28a21dc218cb8a7ca3e1ed3",
        ),
    },
}


def _digest(value: str) -> str:
    normalized = value.replace(
        ROOT.resolve().as_uri(),
        "file://IDML-PANEL-ROOT",
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _result(writer: IdmlWriter, spread_id: str) -> tuple[str, str]:
    stories = "\n".join(
        f"{story_id}\0{xml}" for story_id, xml in writer.stories
    )
    return _digest(dict(writer.spreads)[spread_id]), _digest(stories)


def _signals(copy: dict[str, object]) -> list[dict[str, str]]:
    return [
        {
            "signal_key": "warning",
            "label": str(copy["warning_label"]),
            "text": str(copy["warning"]),
        },
        {
            "signal_key": "tips",
            "label": "TIP",
            "text": str(copy["item"]),
        },
    ]


def _snapshot(language: str, mode: str) -> tuple[str, str]:
    copy = COPY[language]
    overlays = (COMPACT_PARAMS,) if mode == "compact" else ()
    params = load_layout_params(BASE_PARAMS, overlays)
    writer = IdmlWriter(
        params,
        language=language,
        strict_component_assets=True,
    )
    if mode == "standard":
        sid = f"st_safety_contract_{language}"
        blocks = [
            ("h1", str(copy["h1"])),
            ("component", json.dumps({
                "kind": "safetyinstruction",
                "texts": [copy["instruction"]],
            }, ensure_ascii=False)),
            ("layout", "twocol_start"),
            ("component", json.dumps({
                "kind": "warninglead",
                "label": copy["warning_label"],
                "texts": [copy["warning"]],
            }, ensure_ascii=False)),
            *[("list", f"• {copy['item']} {index}") for index in range(1, 7)],
            ("layout", "twocol_end"),
            ("h2", str(copy["subbar"])),
            ("layout", "twocol_start"),
            ("safetylead", str(copy["lead"])),
            ("list", f"• {copy['item']}"),
            ("layout", "twocol_end"),
        ]
        writer.add_safety_page(sid, f"safety_{language}", blocks, ROOT, 1)
        return _result(writer, "sp_1")

    symbol_data = SimpleNamespace(
        title=copy["symbols"],
        signal_headers=copy["headers"],
        icon_headers=copy["headers"],
        signals=(
            {
                "signal_key": "warning",
                "label": str(copy["warning_label"]),
                "text": str(copy["warning"]),
            },
            {
                "signal_key": "note",
                "label": "NOTE",
                "text": str(copy["item"]),
            },
        ),
        icons=tuple(
            {"figure": "", "text": f"{copy['item']} {index}"}
            for index in range(1, 7)
        ),
    )
    if mode == "compact":
        shared_page.add_safety_symbols_page(
            writer,
            safety_sid=f"st_compact_safety_{language}",
            safety_title=f"compact_safety_{language}",
            safety_blocks=[
                ("h1", str(copy["h1"])),
                ("body", str(copy["warning"])),
                *[
                    ("list", f"• {copy['item']} {index}")
                    for index in range(1, 5)
                ],
            ],
            symbol_data=symbol_data,
            bundle_root=ROOT,
            data_root=ROOT,
            page_index=3,
            language=language,
        )
        return _result(writer, "sp_3")

    tail = [
        ("component", json.dumps({
            "kind": "warnbox",
            "label": copy["warning_label"],
            "texts": [copy["warning"]],
        }, ensure_ascii=False)),
        ("component", json.dumps({
            "kind": "warnbox",
            "label": copy["danger"],
            "texts": [copy["item"]],
        }, ensure_ascii=False)),
    ]
    writer.add_safety_symbols_page(
        f"st_safety_symbols_{language}",
        tail,
        [
            ("h1", str(copy["maintenance"])),
            ("body", str(copy["maintenance_body"])),
        ],
        _signals(copy),
        [
            {"figure": "", "text": f"{copy['item']} {index}"}
            for index in range(8)
        ],
        ROOT,
        2,
        language,
        title=str(copy["symbols"]),
        signal_headers=copy["headers"],
        icon_headers=copy["headers"],
    )
    return _result(writer, "sp_2")


class SafetyPanelGoldenTests(unittest.TestCase):
    def test_all_safety_densities_share_trilingual_golden(self) -> None:
        actual = {
            language: {
                mode: _snapshot(language, mode)
                for mode in ("standard", "compact", "maintenance")
            }
            for language in ("en", "fr", "es")
        }
        self.assertEqual(GOLDEN, actual)

    def test_page_composers_do_not_draw_safety_internals(self) -> None:
        sources = (
            inspect.getsource(pages.add_safety_page),
            inspect.getsource(shared_page.add_safety_symbols_page),
            inspect.getsource(symbols_page.add_safety_symbols_page),
        )
        expected_components = (
            "SafetyPanel",
            "CompactSafetyPanel",
            "SafetySymbolsPanel",
        )
        for source, component in zip(
            sources,
            expected_components,
            strict=True,
        ):
            self.assertIn(component, source)
            self.assertIn("available_height=", source)
            for token in (
                "frame_with_background",
                "heading_text",
                "_safety_section_story",
                "idml_safety_warning_top",
                "idml_compact_safety_title_body_gap",
                "idml_symbols_first_tail_height",
            ):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
