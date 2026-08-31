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
            "2812194ef954e31f1e99a5e9655998336861249360999147824793b2a196696f",
            "367bb5ac714e2d658308ffe0c5032a087584f9dc6fcaa2448ae99e946795cf42",
        ),
        "compact": (
            "eb410a51580912995124b9d87e70b642445ab7c49ea53e6e212dad6e82bb50d4",
            "6397d856944a4aed6215c5be0d4f3e78404a1513b97b05971ca62c5f5699a4a3",
        ),
        "maintenance": (
            "5a1ecf52fae7704c70437ca9aa63e71a3443d2f5bf5ea5fa007fa20efacc6ff9",
            "f26786221092faef3c7500e1024655f591e154902d630fd7a01c4f96fddf5a79",
        ),
    },
    "fr": {
        "standard": (
            "ef46ef3a1ecec771f503c6f06deebb359d9dae645b3d851318a285f7d5c1a572",
            "9c3852c0c5e371c2ee265b0f1d379ffabdcd094093468048ae21adf8d81a671f",
        ),
        "compact": (
            "07811d7923bc180990d6a17ec655c05982b152268b67f10c155f9ea09644f81f",
            "61c9c9f588e59a1026f63dad1430eee13843a0c57e2686404d07d279f0563b09",
        ),
        "maintenance": (
            "5c9687d92ef903eb40be8b59cc27821881ba27be30d96dff06ad73e5f54d761c",
            "8bb4e59356ee597a071b70ecb1057ce192b8907bc87f7401b380026c801e2e48",
        ),
    },
    "es": {
        "standard": (
            "45a09c3be28b9d944b9e34b0560e79a695752e8be28505b873cf5df1554d6ae2",
            "5eb73f80aefa0d305578763ff2b4dd83c8a6f36eecc3aee5d648e7336905b8ef",
        ),
        "compact": (
            "e0ad890a4cd47d537ee97c654978be2a536c0796fa7e028e7813b4c707aa3872",
            "4eb8c754165429df77ef1f722fecf485f79cf1841ec657e588c6d5a8903a9198",
        ),
        "maintenance": (
            "8bbc7d534b09464cf48c21e71152fe220b55a1a2d2587b8b26cb6d2c47a5fa50",
            "a3a40aa84151d67a59949501bc26718a02437ceca5f21cffe605bb9138354d9d",
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
