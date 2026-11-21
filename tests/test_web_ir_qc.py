from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from tools.corpus.discover import discover_ir_pairs
from tools.web.ir_qc import (
    AUDIT_SCHEMA_VERSION,
    PROVENANCE_SCHEMA_VERSION,
    audit_manual_ir,
    build_ir_provenance,
    main,
    resolve_callout_severity,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def _callout_component(label: str, body: str, variant: str | None = None) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "schema_version": "component-spec/v1",
        "component_id": "HB-CALLOUT-STRIP",
        "slots": [
            {"role": "label", "content": label, "content_kind": "inline_text"},
            {"role": "body", "content": body, "content_kind": "rich_text"},
        ],
    }
    if variant is not None:
        spec["variant"] = variant
    return {
        "kind": "component",
        "component_spec": spec,
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
                                        "children": [_paragraph(label)],
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


def _page(page_id: str, language: str, blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "page_id": page_id,
        "language": language,
        "source_path": f"{page_id}.rst",
        "source_ref": page_id,
        "source_sha256": "0" * 64,
        "blocks": [{"kind": "flow", "payload": blk} for blk in blocks],
    }


def _write_ir_bundle(
    pkg_dir: Path,
    *,
    language: str,
    pages: list[dict[str, Any]],
    assets: dict[str, bytes] | None = None,
    asset_sha_override: dict[str, str] | None = None,
    overview_instance_id: str | None = None,
) -> Path:
    pkg_dir.mkdir(parents=True, exist_ok=True)
    asset_sha256: dict[str, str] = {}
    for rel_path, content in (assets or {}).items():
        target = pkg_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        asset_sha256[rel_path] = hashlib.sha256(content).hexdigest()
    if asset_sha_override is not None:
        asset_sha256.update(asset_sha_override)

    metadata: dict[str, Any] = {
        "asset_sha256": asset_sha256,
        "publication_eligible": True,
    }
    if overview_instance_id is not None:
        metadata["overview_instance"] = {
            "component_id": "HB-SPECIAL-OVERVIEW",
            "instance_id": overview_instance_id,
        }

    ir_payload = {
        "schema_version": "manual-ir/v2",
        "model": "MOD-ALPHA",
        "region": "US",
        "language": language,
        "content_sha256": "a" * 64,
        "metadata": metadata,
        "pages": pages,
    }
    ir_path = pkg_dir / "manual.ir.json"
    ir_path.write_text(json.dumps(ir_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return ir_path


class WebIrQcTests(unittest.TestCase):
    """Unit and integration tests for tools.web.ir_qc."""

    def test_clean_bundle_passes_with_zero_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            en_ir = _write_ir_bundle(
                root / "en",
                language="en",
                assets={"assets/logo.png": b"png-bytes"},
                pages=[
                    _page(
                        "01_intro_en.rst",
                        "en",
                        [
                            _heading(1, "Product Overview"),
                            _paragraph("Connect the AC cable to charge the power station."),
                            _callout_component("WARNING", "Keep away from water."),
                        ],
                    )
                ],
            )
            fr_ir = _write_ir_bundle(
                root / "fr",
                language="fr",
                assets={"assets/logo.png": b"png-bytes"},
                pages=[
                    _page(
                        "01_intro_fr.rst",
                        "fr",
                        [
                            _heading(1, "Présentation du produit"),
                            _paragraph("Branchez le câble secteur pour charger la station."),
                            _callout_component("AVERTISSEMENT", "Tenir à l'écart de l'eau."),
                        ],
                    )
                ],
            )
            report = audit_manual_ir(fr_ir, anchor_ir_path=en_ir)
            self.assertEqual(report["schema_version"], AUDIT_SCHEMA_VERSION)
            self.assertEqual(report["summary"]["errors"], 0)
            self.assertEqual(report["summary"]["warnings"], 0)
            self.assertEqual(report["findings"], [])

    def test_unresolved_markers_and_empty_heading_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ir_path = _write_ir_bundle(
                root / "en",
                language="en",
                pages=[
                    _page(
                        "02_specs_en.rst",
                        "en",
                        [
                            _heading(1, "   "),
                            _paragraph("Output voltage is {{voltage}}."),
                            _list_block("==unmatched text=="),
                            _table_block(["Parameter", "Value"], [["Input", "{{input_spec}}"]]),
                        ],
                    )
                ],
            )
            report = audit_manual_ir(ir_path)
            types = [item["type"] for item in report["findings"]]
            self.assertEqual(report["summary"]["errors"], 4)
            self.assertIn("empty_heading", types)
            self.assertIn("unresolved_template_marker", types)
            self.assertIn("unresolved_tm_marker", types)

    def test_untranslated_english_residue_vs_allowlisted_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            en_ir = _write_ir_bundle(
                root / "en",
                language="en",
                pages=[
                    _page(
                        "03_ports_en.rst",
                        "en",
                        [
                            _paragraph("USB-C"),
                            _paragraph("Wi-Fi / Bluetooth"),
                            _paragraph("Jackery Explorer"),
                            _paragraph("USB-C (100W)"),
                            _paragraph("FCC / CE / UKCA / RoHS"),
                            _paragraph("Connect the AC power cable before charging."),
                        ],
                    )
                ],
            )
            de_ir = _write_ir_bundle(
                root / "de",
                language="de",
                pages=[
                    _page(
                        "03_ports_de.rst",
                        "de",
                        [
                            _paragraph("USB-C"),
                            _paragraph("Wi-Fi / Bluetooth"),
                            _paragraph("Jackery Explorer"),
                            _paragraph("USB-C (100W)"),
                            _paragraph("FCC / CE / UKCA / RoHS"),
                            _paragraph("Connect the AC power cable before charging."),
                        ],
                    )
                ],
            )
            report = audit_manual_ir(de_ir, anchor_ir_path=en_ir)
            residue = [
                item
                for item in report["findings"]
                if item["type"] == "untranslated_english_residue"
            ]
            self.assertEqual(len(residue), 1)
            self.assertEqual(residue[0]["text"], "Connect the AC power cable before charging.")

    def test_callout_severity_parity_and_cjk_kr_recognition(self) -> None:
        self.assertEqual(resolve_callout_severity("警告"), "warning")
        self.assertEqual(resolve_callout_severity("注意"), "caution")
        self.assertEqual(resolve_callout_severity("注記"), "note")
        self.assertEqual(resolve_callout_severity("경고"), "warning")
        self.assertEqual(resolve_callout_severity("주의"), "caution")
        self.assertEqual(resolve_callout_severity("小心"), "caution")
        self.assertEqual(resolve_callout_severity("提示"), "note")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            en_ir = _write_ir_bundle(
                root / "en",
                language="en",
                pages=[
                    _page(
                        "04_safety_en.rst",
                        "en",
                        [
                            _callout_component("WARNING", "High voltage hazard."),
                            _callout_component("CAUTION", "Do not drop."),
                        ],
                    )
                ],
            )
            ja_ir = _write_ir_bundle(
                root / "ja",
                language="ja",
                pages=[
                    _page(
                        "04_safety_ja.rst",
                        "ja",
                        [
                            _callout_component("警告", "高電圧に注意してください。"),
                            _callout_component("MYSTERY_SIGNAL", "不明なラベル。"),
                        ],
                    )
                ],
            )
            report = audit_manual_ir(ja_ir, anchor_ir_path=en_ir)
            types = [item["type"] for item in report["findings"]]
            self.assertIn("unknown_callout_severity", types)
            self.assertIn("callout_severity_mismatch", types)
            mismatch = next(
                item for item in report["findings"] if item["type"] == "callout_severity_mismatch"
            )
            self.assertEqual(mismatch["anchor_severities"], ["warning", "caution"])
            self.assertEqual(mismatch["target_severities"], ["warning", "unknown"])

    def test_terms_glossary_compliance_approved_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            terms_path = root / "terms.json"
            terms_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "record_id": "recTermApproved1",
                                "fields": {
                                    "Status": "Approved",
                                    "en": "power station",
                                    "fr": "station d'énergie / centrale électrique",
                                },
                            },
                            {
                                "record_id": "recTermApproved2",
                                "fields": {
                                    "Status": "Approved",
                                    "en": "solar panel",
                                    "fr": "panneau solaire",
                                },
                            },
                            {
                                "record_id": "recTermDraft",
                                "fields": {
                                    "Status": "Draft",
                                    "en": "battery pack",
                                    "fr": "bloc-batterie",
                                },
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            en_ir = _write_ir_bundle(
                root / "en",
                language="en",
                pages=[
                    _page(
                        "05_charge_en.rst",
                        "en",
                        [
                            _paragraph("Charge the power station with a solar panel."),
                            _paragraph("Connect the extra battery pack."),
                        ],
                    )
                ],
            )
            fr_ir = _write_ir_bundle(
                root / "fr",
                language="fr",
                pages=[
                    _page(
                        "05_charge_fr.rst",
                        "fr",
                        [
                            _paragraph("Chargez la station d'énergie avec un module photovoltaïque."),
                            _paragraph("Branchez la batterie supplémentaire."),
                        ],
                    )
                ],
            )
            report = audit_manual_ir(fr_ir, anchor_ir_path=en_ir, terms_path=terms_path)
            term_findings = [
                item for item in report["findings"] if item["type"] == "term_glossary_mismatch"
            ]
            self.assertEqual(len(term_findings), 1)
            self.assertEqual(term_findings[0]["term_record_id"], "recTermApproved2")
            self.assertEqual(term_findings[0]["en_term"], "solar panel")
            self.assertEqual(term_findings[0]["expected_target_terms"], ["panneau solaire"])
            self.assertEqual(term_findings[0]["page_stem"], "05_charge")

    def test_broken_asset_sha256_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ir_path = _write_ir_bundle(
                root / "en",
                language="en",
                assets={"assets/ok.png": b"good", "assets/tampered.png": b"actual"},
                asset_sha_override={
                    "assets/tampered.png": "f" * 64,
                    "assets/missing.png": "1" * 64,
                },
                pages=[_page("01_cover_en.rst", "en", [_heading(1, "Cover")])],
            )
            report = audit_manual_ir(ir_path, verify_assets=True)
            broken = [item for item in report["findings"] if item["type"] == "broken_asset"]
            self.assertEqual(len(broken), 2)
            reasons = {item["asset_path"]: item["reason"] for item in broken}
            self.assertEqual(reasons["assets/tampered.png"], "sha256_mismatch")
            self.assertEqual(reasons["assets/missing.png"], "missing_file")

            skipped_report = audit_manual_ir(ir_path, verify_assets=False)
            self.assertEqual(skipped_report["summary"]["errors"], 0)

    def test_provenance_attribution_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matched_bytes = b"matched-asset-payload"
            matched_sha = hashlib.sha256(matched_bytes).hexdigest()
            unreg_bytes = b"unregistered-asset-payload"

            registry_csv = root / "asset_registry.csv"
            registry_csv.write_text(
                "asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,导出物路径,语言变体,内容哈希,备注\n"
                f"overview/hero,,插图,中立,✅成品,FALSE,MOD-ALPHA,US,assets,en,hero.png:{matched_sha},\n",
                encoding="utf-8",
            )
            tm_json = root / "tm.json"
            tm_json.write_text(
                json.dumps(
                    [
                        {
                            "record_id": "recTM_approved",
                            "fields": {
                                "Status": "Approved",
                                "en": "Press and hold the power button.",
                                "es": "Mantenga pulsado el botón de encendido.",
                            },
                        },
                        {
                            "record_id": "recTM_draft",
                            "fields": {
                                "Status": "Draft",
                                "en": "Do not submerge in water.",
                                "es": "No sumergir en agua.",
                            },
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            en_ir = _write_ir_bundle(
                root / "en",
                language="en",
                pages=[
                    _page(
                        "01_op_en.rst",
                        "en",
                        [
                            _paragraph("Press and hold the power button."),
                            _paragraph("Do not submerge in water."),
                            _callout_component("NOTE", "Read before use."),
                        ],
                    )
                ],
            )
            es_ir = _write_ir_bundle(
                root / "es",
                language="es",
                assets={"assets/hero.png": matched_bytes, "assets/extra.png": unreg_bytes},
                overview_instance_id="mod-alpha-us-overview-v1",
                pages=[
                    _page(
                        "01_op_es.rst",
                        "es",
                        [
                            _paragraph("Mantenga pulsado el botón de encendido."),
                            _paragraph("No sumergir en agua."),
                            _callout_component("NOTA", "Leer antes de usar."),
                        ],
                    )
                ],
            )

            out_sidecar = root / "out" / "provenance.json"
            prov = build_ir_provenance(
                es_ir,
                anchor_ir_path=en_ir,
                asset_registry_csv=registry_csv,
                tm_json_path=tm_json,
                output_path=out_sidecar,
            )
            self.assertEqual(prov["schema_version"], PROVENANCE_SCHEMA_VERSION)
            self.assertTrue(out_sidecar.is_file())
            self.assertEqual(prov["visual_assets"]["total_packaged_assets"], 2)
            self.assertEqual(prov["visual_assets"]["registered_asset_count"], 1)
            self.assertEqual(prov["visual_assets"]["unique_asset_keys"], ["overview/hero"])
            self.assertEqual(
                [a["rel_path"] for a in prov["visual_assets"]["unregistered_assets"]],
                ["assets/extra.png"],
            )
            self.assertEqual(prov["tm_attribution"]["status"], "attributed")
            self.assertEqual(prov["tm_attribution"]["matched_tm_record_ids"], ["recTM_approved"])
            self.assertEqual(prov["tm_attribution"]["matched_segment_count"], 1)
            self.assertEqual(prov["components"]["component_ids"], ["HB-CALLOUT-STRIP"])
            self.assertEqual(prov["components"]["component_block_count"], 1)
            self.assertEqual(prov["components"]["overview_instance_id"], "mod-alpha-us-overview-v1")

            no_tm_prov = build_ir_provenance(es_ir, asset_registry_csv=registry_csv)
            self.assertEqual(no_tm_prov["tm_attribution"]["status"], "not_provided")
            self.assertIsNone(no_tm_prov["tm_attribution"]["matched_segment_count"])

            # Verify CLI audit (--strict exits 1 on warning, 0 when clean) & provenance subprocess.
            cli_clean = main(["audit", "--ir", str(es_ir), "--anchor-ir", str(en_ir), "--strict"])
            self.assertEqual(cli_clean, 0)

            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.web.ir_qc",
                    "provenance",
                    "--ir",
                    str(es_ir),
                    "--asset-registry",
                    str(registry_csv),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            parsed = json.loads(proc.stdout)
            self.assertEqual(parsed["schema_version"], PROVENANCE_SCHEMA_VERSION)

    def test_audit_cli_strict_exits_nonzero_on_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            en_ir = _write_ir_bundle(
                root / "en",
                language="en",
                pages=[_page("01_p_en.rst", "en", [_paragraph("Charge battery fully.")])],
            )
            fr_ir = _write_ir_bundle(
                root / "fr",
                language="fr",
                pages=[_page("01_p_fr.rst", "fr", [_paragraph("Charge battery fully.")])],
            )
            out_path = root / "qc.json"
            self.assertEqual(
                main(["audit", "--ir", str(fr_ir), "--anchor-ir", str(en_ir), "--output", str(out_path)]),
                0,
            )
            self.assertEqual(
                main(["audit", "--ir", str(fr_ir), "--anchor-ir", str(en_ir), "--strict"]),
                1,
            )
            saved = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["summary"]["warnings"], 1)

    def test_smoke_discovered_real_ir_pair(self) -> None:
        _discovered, pairs, _abstentions, _skipped = discover_ir_pairs(repo_root=REPO_ROOT)
        self.assertGreater(len(pairs), 0)
        pair = pairs[0]
        report = audit_manual_ir(pair.target.path, anchor_ir_path=pair.anchor.path)
        self.assertEqual(report["schema_version"], AUDIT_SCHEMA_VERSION)
        self.assertEqual(report["summary"]["errors"], 0)

        prov = build_ir_provenance(pair.target.path, anchor_ir_path=pair.anchor.path)
        self.assertEqual(prov["schema_version"], PROVENANCE_SCHEMA_VERSION)
        self.assertEqual(prov["tm_attribution"]["status"], "not_provided")
        self.assertEqual(prov["visual_assets"]["status"], "attributed")

    def test_callout_alias_normalization_and_strict_malformed_rejection(self) -> None:
        self.assertEqual(resolve_callout_severity("Remarks"), "note")
        self.assertEqual(resolve_callout_severity("  remark : "), "note")
        self.assertEqual(resolve_callout_severity("Mise en garde"), "caution")
        self.assertEqual(resolve_callout_severity("Warm Tip"), "tip")
        self.assertEqual(resolve_callout_severity("info"), "note")
        self.assertEqual(resolve_callout_severity("充電に関する安全上のご注意"), "caution")
        self.assertEqual(resolve_callout_severity("使用上 のご注意"), "caution")
        self.assertEqual(resolve_callout_severity("ご使用前の確認"), "note")
        self.assertEqual(resolve_callout_severity("⚠"), "unknown")
        self.assertEqual(resolve_callout_severity("banana"), "unknown")
        self.assertEqual(resolve_callout_severity("WAARSCHU"), "unknown")
        self.assertEqual(resolve_callout_severity("OSTRZE"), "unknown")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            en_ir = _write_ir_bundle(
                root / "en",
                language="en",
                pages=[
                    _page(
                        "04_safety_en.rst",
                        "en",
                        [
                            _callout_component("Caution", "Check polarity.", variant="caution"),
                            _callout_component("Remarks", "Auto sleep in 2h.", variant="note"),
                            _callout_component("WARNING", "High voltage hazard.", variant="warning"),
                        ],
                    )
                ],
            )
            fr_ir = _write_ir_bundle(
                root / "fr",
                language="fr",
                pages=[
                    _page(
                        "04_safety_fr.rst",
                        "fr",
                        [
                            _callout_component("Mise en garde", "Vérifiez la polarité.", variant="caution"),
                            _callout_component("Remarque", "Veille automatique en 2 h.", variant="note"),
                            _callout_component("AVERTISSEMENT", "Risque haute tension.", variant="warning"),
                        ],
                    )
                ],
            )
            clean_pair_report = audit_manual_ir(fr_ir, anchor_ir_path=en_ir)
            self.assertEqual(clean_pair_report["summary"]["warnings"], 0)

            icon_valid_ir = _write_ir_bundle(
                root / "nl_icon",
                language="nl",
                pages=[
                    _page(
                        "04_safety_nl.rst",
                        "nl",
                        [
                            _callout_component("⚠", "Brandgevaar.", variant="warning"),
                            _callout_component("⚠️", "Gevaar.", variant="warning"),
                        ],
                    )
                ],
            )
            self.assertEqual(audit_manual_ir(icon_valid_ir)["summary"]["warnings"], 0)

            malformed_ir = _write_ir_bundle(
                root / "nl_bad",
                language="nl",
                pages=[
                    _page(
                        "04_safety_nl.rst",
                        "nl",
                        [
                            _callout_component("WAARSCHU", "Broken label.", variant="warning"),
                            _callout_component("banana", "Bogus label.", variant="note"),
                            _callout_component("⚠", "Missing explicit variant."),
                        ],
                    )
                ],
            )
            malformed_report = audit_manual_ir(malformed_ir)
            unknown_labels = [
                item["label"]
                for item in malformed_report["findings"]
                if item["type"] == "unknown_callout_severity"
            ]
            self.assertEqual(unknown_labels, ["WAARSCHU", "banana", "⚠"])

            downgraded_fr_ir = _write_ir_bundle(
                root / "fr_bad",
                language="fr",
                pages=[
                    _page(
                        "04_safety_fr.rst",
                        "fr",
                        [
                            _callout_component("Mise en garde", "Vérifiez la polarité.", variant="caution"),
                            _callout_component("Remarque", "Veille automatique en 2 h.", variant="note"),
                            _callout_component("Remarque", "Gravité dégradée.", variant="note"),
                        ],
                    )
                ],
            )
            downgrade_report = audit_manual_ir(downgraded_fr_ir, anchor_ir_path=en_ir)
            mismatches = [
                item
                for item in downgrade_report["findings"]
                if item["type"] == "callout_severity_mismatch"
            ]
            self.assertEqual(len(mismatches), 1)
            self.assertEqual(mismatches[0]["anchor_severities"], ["caution", "note", "warning"])
            self.assertEqual(mismatches[0]["target_severities"], ["caution", "note", "note"])
