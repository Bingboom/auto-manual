from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from tools.corpus.align import is_noise_segment, normalize_page_stem
from tools.corpus.harvest_web_ir import (
    HARVEST_SCHEMA_VERSION,
    harvest_web_ir,
    tm_column_for_lang,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_CONTENT_ATTRIBUTES = {
    "page_title",
    "table_header",
    "panel_title",
    "part_name",
    "section_title",
}


def _text(value: str) -> dict[str, Any]:
    return {"kind": "text", "text": value}


def _heading(level: int, value: str) -> dict[str, Any]:
    return {"kind": "heading", "level": level, "children": [_text(value)]}


def _paragraph(value: str) -> dict[str, Any]:
    return {"kind": "paragraph", "children": [_text(value)]}


def _list_block(*items: str) -> dict[str, Any]:
    return {
        "kind": "list",
        "ordered": False,
        "children": [
            {"kind": "list_item", "children": [_paragraph(item)]}
            for item in items
        ],
    }


def _table_block(headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
    head = {
        "kind": "table_head",
        "children": [
            {
                "kind": "table_row",
                "children": [
                    {"kind": "table_cell", "header": True, "children": [_paragraph(h)]}
                    for h in headers
                ],
            }
        ],
    }
    body = {
        "kind": "table_body",
        "children": [
            {
                "kind": "table_row",
                "children": [
                    {"kind": "table_cell", "header": False, "children": [_paragraph(c)]}
                    for c in row
                ],
            }
            for row in rows
        ],
    }
    return {"kind": "table", "children": [head, body]}


def _callout_component(label: str, body: str) -> dict[str, Any]:
    return {
        "kind": "component",
        "component_spec": {
            "schema_version": "component-spec/v1",
            "component_id": "HB-CALLOUT-STRIP",
            "slots": [
                {"role": "label", "content": label, "content_kind": "inline_text"},
                {"role": "body", "content": body, "content_kind": "rich_text"},
            ],
        },
        "carrier_flow": [
            {
                "kind": "table",
                "children": [
                    {
                        "kind": "table_body",
                        "children": [
                            {
                                "kind": "table_row",
                                "children": [
                                    {
                                        "kind": "table_cell",
                                        "header": False,
                                        "presentation": {
                                            "html": {"attributes": {"class": "manual-callout-label"}}
                                        },
                                        "children": [_text(label)],
                                    },
                                    {
                                        "kind": "table_cell",
                                        "header": False,
                                        "presentation": {
                                            "html": {"attributes": {"class": "manual-callout-body"}}
                                        },
                                        "children": [_paragraph(body)],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _write_ir(
    path: Path,
    *,
    model: str,
    region: str,
    language: str,
    pages: list[dict[str, Any]],
    publication_eligible: bool | None = True,
    content_sha256: str | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": "manual-ir/v2",
        "model": model,
        "region": region,
        "language": language,
        "content_sha256": content_sha256 or f"sha-{model}-{region}-{language}-{len(pages)}",
        "metadata": {
            "publication_eligible": publication_eligible,
        },
        "pages": pages,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _page(page_id: str, *payloads: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": page_id,
        "blocks": [{"kind": "flow", "payload": p} for p in payloads],
    }


class TestHarvestWebIrToTm(unittest.TestCase):
    def test_language_column_mapping_and_page_stem_normalization(self) -> None:
        self.assertEqual(tm_column_for_lang("ja"), "jp")
        self.assertEqual(tm_column_for_lang("pt-br"), "pt-BR")
        self.assertEqual(tm_column_for_lang("pt-BR"), "pt-BR")
        self.assertEqual(tm_column_for_lang("nl"), "nl")
        self.assertEqual(tm_column_for_lang("pl"), "pl")
        self.assertEqual(tm_column_for_lang("pt"), "pt")
        self.assertEqual(tm_column_for_lang("de"), "de")
        self.assertEqual(tm_column_for_lang("fr"), "fr")
        self.assertEqual(tm_column_for_lang("es"), "es")

        self.assertEqual(normalize_page_stem("disclaimer_de.rst"), "disclaimer")
        self.assertEqual(normalize_page_stem("disclaimer_en.rst"), "disclaimer")
        self.assertEqual(normalize_page_stem("disclaimer_pt-br.rst"), "disclaimer")
        self.assertEqual(normalize_page_stem("page-01"), "page-01")
        self.assertEqual(normalize_page_stem("regulatory_compliance.rst"), "regulatory_compliance")

    def test_noise_filtering(self) -> None:
        noise_cases = [
            "",
            "1",
            "●",
            "123.45",
            "---",
            "3600Wh",
            "120V~ 60Hz",
            "473 × 359 × 373 mm",
            "≥0.66 ft (≈200 mm)",
            "0°C - 40°C",
            "JE-3600A",
            "JBP-1000B-SIL",
            "F0-FF",
            "https://www.jackery.com/support",
            "support@jackery.com",
        ]
        for sample in noise_cases:
            self.assertTrue(is_noise_segment(sample), f"Expected noise: {sample!r}")

        valid_cases = [
            "WARNING",
            "Storage Temperature",
            "Charge the battery every 3 months.",
            "On",
        ]
        for sample in valid_cases:
            self.assertFalse(is_noise_segment(sample), f"Expected non-noise: {sample!r}")

    def test_same_package_and_split_package_alignment_and_staging_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Same-package EU multi-locale (en + de, fr, es, nl, pl, pt)
            eu_pkg = root / "manual_sources" / "MOD-A" / "EU" / "pkg1" / "web"
            en_pages = [
                _page(
                    "safety_en.rst",
                    _heading(1, "SAFETY INSTRUCTIONS"),
                    _paragraph("Read all instructions before use."),
                    _list_block("Keep dry.", "Do not disassemble."),
                    _callout_component("WARNING", "Keep away from fire."),
                    _table_block(["Symbol", "Meaning"], [["●", "3600Wh"]]),
                ),
                _page("spec_en.rst", _paragraph("3600Wh"), _paragraph("JE-3600A")),
            ]
            translations = {
                "de": ("SICHERHEITSHINWEISE", "Lesen Sie alle Anweisungen vor der Verwendung.", "Trocken halten.", "Nicht zerlegen.", "WARNUNG", "Von Feuer fernhalten.", "Symbol", "Bedeutung"),
                "fr": ("CONSIGNES DE SÉCURITÉ", "Lisez toutes les instructions avant utilisation.", "Garder au sec.", "Ne pas démonter.", "AVERTISSEMENT", "Tenir éloigné du feu.", "Symbole", "Signification"),
                "es": ("INSTRUCCIONES DE SEGURIDAD", "Lea todas las instrucciones antes de usar.", "Mantener seco.", "No desmontar.", "ADVERTENCIA", "Mantener alejado del fuego.", "Símbolo", "Significado"),
                "nl": ("VEILIGHEIDSINSTRUCTIES", "Lees alle instructies voor gebruik.", "Droog houden.", "Niet demonteren.", "WAARSCHUWING", "Uit de buurt van vuur houden.", "Symbool", "Betekenis"),
                "pl": ("INSTRUKCJE BEZPIECZEŃSTWA", "Przeczytaj wszystkie instrukcje przed użyciem.", "Przechowywać w suchym miejscu.", "Nie demontować.", "OSTRZEŻENIE", "Trzymać z dala od ognia.", "Symbol", "Znaczenie"),
                "pt": ("INSTRUÇÕES DE SEGURANÇA", "Leia todas as instruções antes de usar.", "Manter seco.", "Não desmontar.", "AVISO", "Manter afastado do fogo.", "Símbolo", "Significado"),
            }
            _write_ir(eu_pkg / "en" / "manual.ir.json", model="MOD-A", region="EU", language="en", pages=en_pages)
            for lang, vals in translations.items():
                h1, p1, li1, li2, cw, cb, th1, th2 = vals
                _write_ir(
                    eu_pkg / lang / "manual.ir.json",
                    model="MOD-A",
                    region="EU",
                    language=lang,
                    pages=[
                        _page(
                            f"safety_{lang}.rst",
                            _heading(1, h1),
                            _paragraph(p1),
                            _list_block(li1, li2),
                            _callout_component(cw, cb),
                            _table_block([th1, th2], [["●", "3600Wh"]]),
                        ),
                        _page(f"spec_{lang}.rst", _paragraph("3600Wh"), _paragraph("JE-3600A")),
                    ],
                )

            # Split-package JP (en in one pkg, ja in added-locales pkg)
            jp_base = root / "data" / "manual_sources" / "MOD-B" / "JP"
            _write_ir(
                jp_base / "en" / "pkg-en" / "web" / "en" / "manual.ir.json",
                model="MOD-B",
                region="JP",
                language="en",
                pages=[_page("disclaimer_en.rst", _heading(2, "Disclaimer"), _paragraph("Read all instructions before use."))],
            )
            _write_ir(
                jp_base / "added-locales" / "pkg-ja" / "web" / "ja" / "manual.ir.json",
                model="MOD-B",
                region="JP",
                language="ja",
                pages=[_page("disclaimer_ja.rst", _heading(2, "免責事項"), _paragraph("ご使用前にすべての説明書をお読みください。"))],
            )

            report, staging = harvest_web_ir(
                repo_root=root,
                roots=[root / "manual_sources", root / "data" / "manual_sources"],
            )
            self.assertEqual(report["schema_version"], HARVEST_SCHEMA_VERSION)
            self.assertEqual(report["summary"]["abstained_packages"], 0)
            self.assertEqual(report["summary"]["abstained_pages"], 0)
            self.assertEqual(report["summary"]["conflicts"], 0)

            rows_by_en = {row["en"]: row for row in report["new_rows"]}
            self.assertEqual(rows_by_en["SAFETY INSTRUCTIONS"]["content_attribute"], "section_title")
            self.assertEqual(rows_by_en["WARNING"]["content_attribute"], "panel_title")
            self.assertEqual(rows_by_en["Symbol"]["content_attribute"], "table_header")
            self.assertIsNone(rows_by_en["Keep dry."]["content_attribute"])
            self.assertEqual(
                rows_by_en["Read all instructions before use."]["translations"]["jp"],
                "ご使用前にすべての説明書をお読みください。",
            )
            self.assertEqual(rows_by_en["Read all instructions before use."]["translations"]["nl"], "Lees alle instructies voor gebruik.")
            self.assertEqual(rows_by_en["Read all instructions before use."]["translations"]["pl"], "Przeczytaj wszystkie instrukcje przed użyciem.")
            self.assertEqual(rows_by_en["Read all instructions before use."]["translations"]["pt"], "Leia todas as instruções antes de usar.")
            self.assertNotIn("3600Wh", rows_by_en)
            self.assertNotIn("JE-3600A", rows_by_en)

            create_records = staging["create_records"]
            self.assertEqual(len(create_records), len(report["new_rows"]))
            for rec in create_records:
                self.assertEqual(rec["Status"], "Draft")
                self.assertEqual(rec["用途标签"], ["manual_copy"])
                if "content_attribute" in rec:
                    self.assertIsInstance(rec["content_attribute"], list)
                    self.assertTrue(set(rec["content_attribute"]).issubset(VALID_CONTENT_ATTRIBUTES))

    def test_structural_mismatch_and_ambiguous_anchor_abstentions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "manual_sources" / "MOD-C" / "US" / "pkg1" / "web"
            _write_ir(
                pkg / "en" / "manual.ir.json",
                model="MOD-C",
                region="US",
                language="en",
                pages=[
                    _page("page-01", _heading(1, "Overview"), _list_block("Item A", "Item B")),
                    _page("page-02", _heading(1, "Warranty"), _paragraph("Standard warranty.")),
                ],
            )
            _write_ir(
                pkg / "fr" / "manual.ir.json",
                model="MOD-C",
                region="US",
                language="fr",
                pages=[
                    # Structural mismatch: 3 list items instead of 2
                    _page("page-01", _heading(1, "Aperçu"), _list_block("Élément A", "Élément B", "Élément C")),
                    _page("page-02", _heading(1, "Garantie"), _paragraph("Garantie standard.")),
                    _page("page-99", _paragraph("Extra page without anchor.")),
                ],
            )

            # Ambiguous split-package: 2 distinct approved anchors for MOD-D/US
            split = root / "manual_sources" / "MOD-D" / "US"
            anchor_a = _write_ir(
                split / "en" / "v1" / "web" / "en" / "manual.ir.json",
                model="MOD-D",
                region="US",
                language="en",
                content_sha256="aaa",
                pages=[_page("intro", _paragraph("Hello world"))],
            )
            _write_ir(
                split / "en" / "v2" / "web" / "en" / "manual.ir.json",
                model="MOD-D",
                region="US",
                language="en",
                content_sha256="bbb",
                pages=[_page("intro", _paragraph("Hello world updated"))],
            )
            _write_ir(
                split / "added" / "web" / "es" / "manual.ir.json",
                model="MOD-D",
                region="US",
                language="es",
                pages=[_page("intro", _paragraph("Hola mundo"))],
            )

            report, _ = harvest_web_ir(repo_root=root, roots=[root / "manual_sources"])
            abstained_reasons = {(a["page_stem"], a["reason"]) for a in report["abstained_pages"]}
            self.assertIn(("page-01", "structural_signature_mismatch"), abstained_reasons)
            self.assertIn(("page-99", "missing_anchor_page"), abstained_reasons)
            rows_by_en = {row["en"]: row for row in report["new_rows"]}
            self.assertIn("Standard warranty.", rows_by_en)
            self.assertNotIn("Overview", rows_by_en)
            self.assertEqual(report["summary"]["abstained_packages"], 1)
            self.assertEqual(report["abstained_packages"][0]["reason"], "ambiguous_anchor_candidates")

            # Explicit --anchor-ir resolves the split-package ambiguity
            resolved_report, _ = harvest_web_ir(
                repo_root=root,
                roots=[root / "manual_sources"],
                model="MOD-D",
                region="US",
                explicit_anchor_irs=[anchor_a],
            )
            self.assertEqual(resolved_report["summary"]["abstained_packages"], 0)
            self.assertEqual(resolved_report["new_rows"][0]["translations"]["es"], "Hola mundo")

    def test_conflict_abstention_and_allow_model_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for model, de_text in (("M1", "Batteriespeicher"), ("M2", "Akku-Pack")):
                pkg = root / "manual_sources" / model / "EU" / "p" / "web"
                _write_ir(
                    pkg / "en" / "manual.ir.json",
                    model=model,
                    region="EU",
                    language="en",
                    pages=[_page("intro", _paragraph("Battery Pack"), _paragraph("Keep dry."))],
                )
                _write_ir(
                    pkg / "de" / "manual.ir.json",
                    model=model,
                    region="EU",
                    language="de",
                    pages=[_page("intro", _paragraph(de_text), _paragraph("Trocken halten."))],
                )

            consensus_report, consensus_staging = harvest_web_ir(
                repo_root=root, roots=[root / "manual_sources"]
            )
            self.assertEqual(consensus_report["summary"]["conflicts"], 1)
            self.assertEqual(consensus_report["conflicts"][0]["en"], "Battery Pack")
            rows_by_en = {row["en"]: row for row in consensus_report["new_rows"]}
            self.assertNotIn("Battery Pack", rows_by_en)
            self.assertIn("Keep dry.", rows_by_en)
            self.assertEqual(len(consensus_staging["create_records"]), 1)

            variant_report, variant_staging = harvest_web_ir(
                repo_root=root,
                roots=[root / "manual_sources"],
                allow_model_variants=True,
            )
            self.assertEqual(variant_report["summary"]["conflicts"], 0)
            battery_rows = [r for r in variant_report["new_rows"] if r["en"] == "Battery Pack"]
            self.assertEqual(len(battery_rows), 2)
            self.assertEqual({r["model_scope"] for r in battery_rows}, {"M1", "M2"})
            self.assertEqual(len(variant_staging["create_records"]), 3)

    def test_tm_snapshot_dedup_and_backfill_json_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "manual_sources" / "MOD-E" / "EU" / "p" / "web"
            _write_ir(
                pkg / "en" / "manual.ir.json",
                model="MOD-E",
                region="EU",
                language="en",
                pages=[
                    _page(
                        "safety",
                        _paragraph("Already complete."),
                        _paragraph("Needs French backfill."),
                        _paragraph("Brand new string."),
                    )
                ],
            )
            for lang, lines in (
                ("de", ("Bereits komplett.", "Braucht FR-Backfill.", "Ganz neuer Text.")),
                ("fr", ("Déjà complet.", "Besoin de FR.", "Nouveau texte.")),
            ):
                _write_ir(
                    pkg / lang / "manual.ir.json",
                    model="MOD-E",
                    region="EU",
                    language=lang,
                    pages=[_page("safety", *(_paragraph(t) for t in lines))],
                )

            json_snap = root / "tm_cache.json"
            json_snap.write_text(
                json.dumps(
                    {
                        "schema_version": 3,
                        "rows": [
                            {"record_id": "rec1", "en": "Already complete.", "de": "Bereits komplett.", "fr": "Déjà complet.", "Status": "Approved"},
                            {"record_id": "rec2", "en": "Needs French backfill.", "de": "Braucht FR-Backfill.", "fr": "", "Status": "Approved"},
                            {"record_id": "rec3", "en": "Brand new string.", "de": "Old", "fr": "Old", "Status": "Deprecated"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            rep_json, stg_json = harvest_web_ir(
                repo_root=root,
                roots=[root / "manual_sources"],
                tm_snapshot_path=json_snap,
            )
            self.assertEqual(rep_json["summary"]["skipped_existing_in_tm"], 2)
            self.assertEqual(rep_json["summary"]["backfill_candidates"], 1)
            self.assertEqual(rep_json["backfill_candidates"][0]["en"], "Needs French backfill.")
            self.assertEqual(rep_json["backfill_candidates"][0]["missing_fields"], {"fr": "Besoin de FR."})
            self.assertEqual(rep_json["backfill_candidates"][0]["tm_record_ids"], ["rec2"])
            self.assertEqual([r["en"] for r in rep_json["new_rows"]], ["Brand new string."])
            self.assertEqual(len(stg_json["create_records"]), 1)

            csv_snap = root / "Translation_Memory.csv"
            with csv_snap.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["_record_id", "en", "de", "fr", "Status"])
                writer.writeheader()
                writer.writerow({"_record_id": "rec10", "en": "Already complete.", "de": "Bereits komplett.", "fr": "Déjà complet.", "Status": "Approved"})
                writer.writerow({"_record_id": "rec11", "en": "Needs French backfill.", "de": "Braucht FR-Backfill.", "fr": "", "Status": ""})

            rep_csv, _ = harvest_web_ir(
                repo_root=root,
                roots=[root / "manual_sources"],
                tm_snapshot_path=csv_snap,
            )
            self.assertEqual(rep_csv["summary"]["backfill_candidates"], 1)
            self.assertEqual(rep_csv["backfill_candidates"][0]["tm_record_ids"], ["rec11"])
            self.assertEqual([r["en"] for r in rep_csv["new_rows"]], ["Brand new string."])

    def test_cli_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            report_path = out_dir / "report.json"
            staging_path = out_dir / "staging.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.corpus",
                    "harvest-web-ir",
                    "--model",
                    "JA-TS02A",
                    "--region",
                    "US",
                    "--report-out",
                    str(report_path),
                    "--staging-out",
                    str(staging_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            staging = json.loads(staging_path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], HARVEST_SCHEMA_VERSION)
            self.assertGreater(report["summary"]["new_rows"], 50)
            self.assertEqual(len(staging["create_records"]), report["summary"]["create_records"])

    def test_real_committed_packages_smoke(self) -> None:
        report, staging = harvest_web_ir(
            repo_root=REPO_ROOT,
            model="JBP-3600A",
            region="EU",
        )
        self.assertGreater(report["summary"]["aligned_pages"], 100)
        self.assertGreater(report["summary"]["new_rows"], 50)
        self.assertEqual(len(staging["create_records"]), report["summary"]["create_records"])
        for rec in staging["create_records"]:
            self.assertEqual(rec["Status"], "Draft")
            self.assertEqual(rec["用途标签"], ["manual_copy"])
            if "content_attribute" in rec:
                self.assertTrue(set(rec["content_attribute"]).issubset(VALID_CONTENT_ATTRIBUTES))


if __name__ == "__main__":
    unittest.main()
