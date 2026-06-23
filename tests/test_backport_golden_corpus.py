#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden corpus for cloud-doc backport routing (L1 of the closed-loop test plan).

This is a *table-driven regression corpus*: every row is a ``(baseline, fetched)``
document pair plus the routing the backport pipeline must produce for it. One
parametrized test (:meth:`test_route_matrix`) runs ``build_report`` over every row
and asserts the delta count, the route-class histogram, and — where relevant — the
resolved source table and the semantic-review flag.

Why a corpus rather than scattered one-off tests:

- Each route class (``repo_review_text`` / ``source_table_suggestion`` /
  ``image_asset_delta`` / ``needs_human_mapping`` / ``repo_template_text``) and each
  noise class (highlight metadata, image re-host, no-op) is covered side by side, so
  a routing regression in any one of them is caught by the same test.
- Coverage spans the nine review languages (en/fr/es/de/it/uk/ja/zh/pt-BR), so a
  language-specific break in prose routing surfaces immediately.

**How to grow it:** when a real cloud-doc surfaces a new noise/routing edge (the way
``manual_je2000f_eu_0.5`` drove PR #466), add ONE row to ``_CASES`` capturing the
minimal ``baseline``/``fetched`` pair and its expected routing. The corpus then guards
that edge forever. Prefer adding a row here over a bespoke test method.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.cloud_doc_backport import build_report
from tools.token_resolution_map import build_value_index

# A neutral one-word prose edit per review language. Each must stay plain prose:
# no digits+units (would trip the data-like heuristic) and no output<->button term
# swap (would trip semantic gating) — so every row routes to repo_review_text.
_PROSE_EDITS = {
    "en": ("The device starts charging automatically.", "The device begins charging automatically."),
    "fr": ("L'appareil démarre la charge automatiquement.", "L'appareil commence la charge automatiquement."),
    "es": ("El dispositivo inicia la carga automáticamente.", "El dispositivo comienza la carga automáticamente."),
    "de": ("Das Gerät beginnt automatisch zu laden.", "Das Gerät startet automatisch zu laden."),
    "it": ("Il dispositivo avvia la carica automaticamente.", "Il dispositivo inizia la carica automaticamente."),
    "uk": ("Пристрій починає заряджання автоматично.", "Пристрій розпочинає заряджання автоматично."),
    "ja": ("デバイスは自動的に充電を開始します。", "デバイスは自動的に充電を始めます。"),
    "zh": ("设备会自动开始充电。", "设备将自动开始充电。"),
    "pt-BR": ("O dispositivo inicia o carregamento automaticamente.", "O dispositivo começa o carregamento automaticamente."),
}

_TABLE_BASE = "| Port | Type |\n| --- | --- |\n| Sortie | USB-A |"
_TABLE_EDIT = "| Port | Type |\n| --- | --- |\n| Entrée | USB-A |"

# Each case: name, baseline, fetched, doc_type, value_index (None | "fr"),
# expected total_deltas, expected route-class histogram, and optional checks
# (source_table for a resolved Class D row, semantic for the gating row).
_CASES: list[dict] = [
    # --- Group A: noise must NOT become a review/source write ---
    {
        "name": "noop_identical",
        "baseline": "Charge the battery fully.",
        "fetched": "Charge the battery fully.",
        "total": 0,
        "routes": {},
    },
    {
        "name": "feishu_highlight_metadata_only",
        "baseline": "Charge the battery fully.",
        "fetched": '<text bgcolor="rgb(255,246,122)">Charge the battery fully.</text>',
        "total": 0,
        "routes": {},
    },
    {
        "name": "image_rehost_is_noise",
        "baseline": "| ![pic](https://x/img/TOKEN_A) |",
        "fetched": "| ![pic](https://x/img/TOKEN_B) |",
        "total": 0,
        "routes": {},
    },
    {
        "name": "image_added_is_asset_delta",
        "baseline": "",
        "fetched": "| ![new image](https://x/img/TOKEN_B) |",
        "total": 1,
        "routes": {"image_asset_delta": 1},
    },
    # --- Group B: Class R prose, every review language ---
    *(
        {
            "name": f"prose_edit_{lang}",
            "baseline": base,
            "fetched": now,
            "total": 1,
            "routes": {"repo_review_text": 1},
        }
        for lang, (base, now) in _PROSE_EDITS.items()
    ),
    # --- Group C: Class D source-table routing ---
    {
        "name": "table_row_edit_is_source_table",
        "baseline": _TABLE_BASE,
        "fetched": _TABLE_EDIT,
        "total": 1,
        "routes": {"source_table_suggestion": 1},
    },
    {
        "name": "spec_value_resolves_to_spec_master",
        "baseline": "Sortie USB-A 18 W",
        "fetched": "Sortie USB-A 20 W",
        "value_index": "fr",
        "total": 1,
        "routes": {"source_table_suggestion": 1},
        "source_table": "Spec_Master",
    },
    {
        "name": "page_value_resolves_to_page_placeholders",
        "baseline": "Bouton Marche",
        "fetched": "Bouton Démarrer",
        "value_index": "fr",
        "total": 1,
        "routes": {"source_table_suggestion": 1},
        "source_table": "Page_Placeholders_Source",
    },
    {
        "name": "unit_bearing_prose_is_data_like_without_index",
        "baseline": "The output is 18 W maximum.",
        "fetched": "The output is 20 W maximum.",
        "total": 1,
        "routes": {"source_table_suggestion": 1},
    },
    # --- Group D: semantic terminology gating ---
    {
        "name": "output_to_button_swap_needs_human",
        "baseline": "Press the power output to begin.",
        "fetched": "Press the power button to begin.",
        "total": 1,
        "routes": {"needs_human_mapping": 1},
        "semantic": True,
    },
    # --- Group E: Class T template-maintenance document ---
    {
        "name": "template_doc_prose_is_template_text",
        "baseline": "Insert the model name here.",
        "fetched": "Insert the product name here.",
        "doc_type": "template",
        "total": 1,
        "routes": {"repo_template_text": 1},
    },
]


class BackportGoldenCorpusTests(unittest.TestCase):
    """Run every corpus row through ``build_report`` and assert its routing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        # Page=Specifications -> Spec_Master; any other page -> Page_Placeholders_Source.
        (root / "Spec_Master.csv").write_text(
            "document_key,Page,Row_key,Slot_key,Source_lang,Value_fr\n"
            "JE-2000F_EU,Specifications,usb_a,front.spec,fr,Sortie USB-A 18 W\n"
            "JE-2000F_EU,Product overview,power,front.label,fr,Bouton Marche\n",
            encoding="utf-8",
        )
        cls._value_index = {"fr": build_value_index(root, "fr")}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _report(self, case: dict) -> dict:
        value_index = self._value_index.get(case["value_index"]) if case.get("value_index") else None
        return build_report(
            run_id="corpus",
            doc_type=case.get("doc_type", "review"),
            doc_url="https://x.feishu.cn/wiki/corpus",
            baseline_path=Path("baseline.md"),
            fetched_text=case["fetched"],
            baseline_text=case["baseline"],
            command=["test"],
            source_path=None,
            section_title=None,
            value_index=value_index,
        )

    def test_route_matrix(self) -> None:
        for case in _CASES:
            with self.subTest(case=case["name"]):
                report = self._report(case)
                summary = report["summary"]
                self.assertEqual(
                    summary["total_deltas"],
                    case["total"],
                    f"{case['name']}: unexpected delta count",
                )
                self.assertEqual(
                    summary["route_classes"],
                    case["routes"],
                    f"{case['name']}: unexpected route histogram",
                )
                if "source_table" in case:
                    tables = [
                        delta["source_ref"]["table"]
                        for delta in report["deltas"]
                        if delta.get("source_ref")
                    ]
                    self.assertIn(
                        case["source_table"],
                        tables,
                        f"{case['name']}: expected a {case['source_table']} source_ref",
                    )
                if case.get("semantic"):
                    self.assertGreaterEqual(summary["semantic_review_required"], 1)
                    flagged = [
                        delta
                        for delta in report["deltas"]
                        if delta.get("semantic_review", {}).get("required")
                    ]
                    self.assertTrue(flagged, f"{case['name']}: expected a semantic_review flag")

    def test_corpus_covers_every_route_class(self) -> None:
        """Guard that the corpus keeps exercising all five route classes + the no-op."""
        seen = set()
        for case in _CASES:
            seen.update(case["routes"].keys())
        self.assertEqual(
            seen,
            {
                "repo_review_text",
                "source_table_suggestion",
                "image_asset_delta",
                "needs_human_mapping",
                "repo_template_text",
            },
            "golden corpus must keep at least one row per route class",
        )
        self.assertTrue(
            any(case["routes"] == {} for case in _CASES),
            "golden corpus must keep at least one pure-noise (zero-delta) row",
        )


if __name__ == "__main__":
    unittest.main()
