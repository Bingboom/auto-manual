"""Tests for all-region ManualIR v2 native knowledge corpus and observation export."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import unittest

from tools.manual_knowledge.ir_export import (
    build_ir_observations,
    extract_ir_sections,
    ir_callout_severity,
    ir_cjk_topics,
    ir_section_kind,
    main as ir_export_main,
    make_ir_corpus,
)
from tools.manual_knowledge.observe import SCHEMA as OBS_SCHEMA, judge_previous
from tools.utils.path_utils import repo_root


def _text(value: str) -> dict[str, Any]:
    return {"kind": "text", "text": value}


def _heading(value: str, *, level: int = 1, anchor: str = "") -> dict[str, Any]:
    node: dict[str, Any] = {"kind": "heading", "level": level, "children": [_text(value)]}
    if anchor:
        node["anchor"] = anchor
    return node


def _paragraph(value: str) -> dict[str, Any]:
    return {"kind": "paragraph", "children": [_text(value)]}


def _callout_comp(label: str, body: str, *, variant: str = "warning", source_ref: str = "callout-1") -> dict[str, Any]:
    return {
        "kind": "component",
        "component_spec": {
            "schema_version": "component-spec/v1",
            "component_id": "HB-CALLOUT-STRIP",
            "variant": variant,
            "source_ref": source_ref,
            "slots": [
                {"role": "label", "content_kind": "inline_text", "content": label},
                {"role": "body", "content_kind": "rich_text", "content": body},
            ],
        },
    }


def _ir_bundle(
    *,
    model: str,
    region: str,
    language: str,
    pages: list[dict[str, Any]],
    publication_eligible: bool = True,
    product_name: str = "",
    revision: str = "1.0",
) -> dict[str, Any]:
    meta: dict[str, Any] = {"publication_eligible": publication_eligible, "revision": revision}
    if product_name:
        meta["product_name"] = product_name
    return {
        "schema_version": "manual-ir/v2",
        "model": model,
        "region": region,
        "language": language,
        "content_sha256": f"sha-{model}-{region}-{language}",
        "metadata": meta,
        "pages": pages,
    }


def _write_ir(root: Path, rel_path: str, payload: dict[str, Any]) -> Path:
    dest = root / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


class IRSectionExtractionTests(unittest.TestCase):
    """Verify direct flow/component extraction from manual-ir/v2 without HTML scraping."""

    def test_extracts_callouts_lists_tables_images_and_components(self) -> None:
        pages = [
            {
                "page_id": "safety",
                "blocks": [
                    {
                        "block_id": "b1",
                        "source_ref": "safety#1",
                        "kind": "flow",
                        "payload": _heading("Important Safety", level=2, anchor="safety"),
                    },
                    {
                        "block_id": "b2",
                        "source_ref": "safety#2",
                        "kind": "flow",
                        "payload": _callout_comp("⚠", "Icon-only warning stays unknown.", source_ref="safety#c0"),
                    },
                    {
                        "block_id": "b3",
                        "source_ref": "safety#3",
                        "kind": "flow",
                        "payload": {
                            "kind": "list",
                            "ordered": True,
                            "start": 2,
                            "children": [
                                {"kind": "list_item", "children": [_paragraph("First step")]},
                                {
                                    "kind": "list_item",
                                    "children": [
                                        _paragraph("Second step"),
                                        {"kind": "list", "ordered": False, "children": [{"kind": "list_item", "children": [_paragraph("Nested note")]}]},
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        "block_id": "b4",
                        "source_ref": "safety#4",
                        "kind": "flow",
                        "payload": {
                            "kind": "table",
                            "children": [
                                {
                                    "kind": "table_row",
                                    "children": [
                                        {"kind": "table_cell", "header": True, "children": [_text("Port")]},
                                        {"kind": "table_cell", "header": True, "children": [_text("Rating")]},
                                    ],
                                },
                                {
                                    "kind": "table_row",
                                    "children": [
                                        {"kind": "table_cell", "header": False, "children": [{"kind": "image", "alt": "USB-C icon", "source": "usb.svg"}]},
                                        {"kind": "table_cell", "header": False, "children": [_text("100 W")]},
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        "block_id": "b5",
                        "source_ref": "safety#5",
                        "kind": "flow",
                        "payload": {"kind": "paragraph", "hidden": True, "children": [_text("Hidden text must be ignored")]},
                    },
                ],
            },
            {
                "page_id": "components",
                "flow": [
                    _heading("Components", level=2, anchor="components"),
                    {
                        "kind": "component",
                        "component_spec": {
                            "component_id": "HB-SPEC-TABLE",
                            "source_ref": "specs#t1",
                            "slots": [
                                {"role": "rows", "content": [{"label": "Capacity", "values": [{"text": "1070 Wh"}]}]},
                            ],
                        },
                    },
                    {
                        "kind": "component",
                        "component_spec": {
                            "component_id": "HB-SYMBOL-PAIR-TABLE",
                            "source_ref": "sym#t1",
                            "slots": [
                                {"role": "rows", "content": [{"icon_alt": "Fire symbol", "meaning_text": "Keep away from fire."}]},
                            ],
                        },
                    },
                    {
                        "kind": "component",
                        "component_spec": {
                            "component_id": "HB-OPERATION-GUIDE",
                            "source_ref": "op#g1",
                            "slots": [
                                {"role": "steps", "content": [{"parts": [{"text": "Power On"}, {"text": "Press 1s"}]}]},
                            ],
                        },
                    },
                    {
                        "kind": "component",
                        "component_spec": {
                            "component_id": "HB-OVERVIEW",
                            "source_ref": "ov#1",
                            "slots": [
                                {"role": "views", "content": [{"alt": "Front view", "callouts": [{"label": "AC Port", "body": ["120 V"]}]}]},
                            ],
                        },
                    },
                ],
            },
        ]
        ir_doc = _ir_bundle(model="JE-TEST", region="US", language="en", pages=pages)
        sections, coverage = extract_ir_sections(ir_doc)

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]["title"], "Important Safety")
        self.assertEqual(sections[0]["level"], 2)
        blocks0 = sections[0]["blocks"]
        self.assertEqual(blocks0[0]["type"], "callout")
        self.assertEqual(blocks0[0]["severity"], "unknown")
        self.assertEqual(blocks0[0]["component_id"], "HB-CALLOUT-STRIP")
        self.assertEqual(blocks0[1]["type"], "list")
        self.assertTrue(blocks0[1]["ordered"])
        self.assertEqual(blocks0[1]["items"][1]["children"][0]["items"][0]["text"], "Nested note")
        self.assertEqual(blocks0[2]["type"], "table")
        self.assertEqual(blocks0[2]["rows"][1][0]["image_alts"], ["USB-C icon"])
        self.assertNotIn("Hidden text", json.dumps(sections))

        comp_blocks = sections[1]["blocks"]
        self.assertEqual([b.get("component_id") for b in comp_blocks], [
            "HB-SPEC-TABLE",
            "HB-SYMBOL-PAIR-TABLE",
            "HB-OPERATION-GUIDE",
            "HB-OVERVIEW",
            "HB-OVERVIEW",
        ])
        self.assertEqual(coverage["sections"], 2)
        self.assertEqual(coverage["callouts"], 1)
        self.assertEqual(coverage["lists"], 1)
        self.assertEqual(coverage["tables"], 3)
        self.assertEqual(coverage["components"], 5)
        self.assertEqual(coverage["images"], 3)
        self.assertEqual(coverage["images_with_alt"], 3)

    def test_cjk_and_kr_callout_severities_and_topics(self) -> None:
        cases = [
            ("警告", "warning"),
            ("注意", "caution"),
            ("注記", "note"),
            ("メモ", "note"),
            ("注", "note"),
            ("ヒント", "tip"),
            ("重要", "note"),
            ("경고", "warning"),
            ("주의", "caution"),
            ("참고", "note"),
            ("팁", "tip"),
            ("중요", "note"),
            ("小心", "caution"),
            ("说明", "note"),
            ("备注", "note"),
            ("提示", "tip"),
        ]
        for label, expected in cases:
            self.assertEqual(ir_callout_severity(label), expected, label)

        self.assertEqual(ir_section_kind("安全上のご注意"), "safety")
        self.assertEqual(ir_section_kind("중요 안전 정보"), "safety")
        self.assertEqual(ir_section_kind("PSE 規格適合"), "compliance")
        self.assertEqual(ir_section_kind("KC 규정 준수"), "compliance")
        self.assertEqual(ir_section_kind("法规合规说明"), "compliance")
        self.assertEqual(ir_section_kind("記号について"), "symbols")
        self.assertEqual(ir_section_kind("기호의 의미"), "symbols")
        self.assertEqual(ir_section_kind("符号说明"), "symbols")

        topics = ir_cjk_topics("感電や火災、水濡れを防ぐため、充電や保管・輸送、廃棄、分解・修理はお子様の手の届かない場所で行ってください。")
        self.assertEqual(
            set(topics),
            {"electrical_shock", "fire", "water", "charging", "storage_transport", "disposal", "disassembly", "children"},
        )
        kr_topics = ir_cjk_topics("감전, 화재, 물, 충전, 보관, 운송, 폐기, 어린이, 분해 및 수리")
        self.assertEqual(
            set(kr_topics),
            {"electrical_shock", "fire", "water", "charging", "storage_transport", "disposal", "children", "disassembly"},
        )


class AllRegionCorpusAndObservationTests(unittest.TestCase):
    """Verify multi-region corpus construction, deduplication, observation enrichment, and freshness."""

    def test_multi_region_corpus_dedup_observations_and_judge_previous(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            jp_pages = [
                {
                    "page_id": "safety",
                    "flow": [
                        _heading("安全上のご注意", level=1, anchor="jp-safety"),
                        _callout_comp("警告", "感電や火災のおそれがあります。子供の手の届かない場所に保管してください。", variant="warning"),
                        _callout_comp("注意", "充電中は水濡れを避け、分解や修理をしないでください。", variant="caution"),
                        _paragraph("廃棄時は自治体の指示に従ってください。"),
                    ],
                },
                {
                    "page_id": "compliance",
                    "flow": [
                        _heading("PSE 規格適合", level=1, anchor="jp-pse"),
                        _paragraph("本製品は PSE および TELEC 基準に適合しています。"),
                    ],
                },
            ]
            kr_pages = [
                {
                    "page_id": "safety",
                    "flow": [
                        _heading("중요 안전 정보", level=1, anchor="kr-safety"),
                        _callout_comp("경고", "감전 및 화재 위험을 방지하기 위해 어린이 손이 닿지 않는 곳에 보관하십시오.", variant="warning"),
                        _callout_comp("주의", "충전 중 물에 닿지 않도록 하고 임의로 분해하거나 수리하지 마십시오.", variant="caution"),
                    ],
                },
                {
                    "page_id": "symbols",
                    "flow": [
                        _heading("기호의 의미", level=1, anchor="kr-symbols"),
                        {
                            "kind": "component",
                            "component_spec": {
                                "component_id": "HB-TABLE-SYMBOL-SIGNAL",
                                "source_ref": "kr/symbols/sig",
                                "slots": [
                                    {"role": "rows", "content": [{"label": "경고", "meaning_text": "심각한 부상"}, {"label": "주의", "meaning_text": "경미한 부상"}]},
                                ],
                            },
                        },
                        {
                            "kind": "component",
                            "component_spec": {
                                "component_id": "HB-TABLE-SYMBOL-ICON",
                                "source_ref": "kr/symbols/icon",
                                "slots": [
                                    {"role": "panels", "content": [[{"icon_alt": "KC", "meaning_text": "KC 안전 인증 기호"}]]},
                                ],
                            },
                        },
                    ],
                },
            ]
            cn_pages = [
                {
                    "page_id": "safety",
                    "flow": [
                        _heading("注意事项", level=1, anchor="cn-safety"),
                        _callout_comp("警告", "切勿拆卸或修理，避免触电或火灾。", variant="warning"),
                        _paragraph("请勿在潮湿或有液体环境下充电，并远离儿童存放及运输、按规定废弃。"),
                    ],
                },
            ]
            us_pages = [
                {
                    "page_id": "fcc",
                    "flow": [
                        _heading("FCC Compliance", level=1, anchor="us-fcc"),
                        _paragraph("This device complies with part 15 of the FCC Rules and UL standards."),
                    ],
                },
            ]
            eu_pages = [
                {
                    "page_id": "safety",
                    "flow": [
                        _heading("Safety", level=1, anchor="eu-safety"),
                        _callout_comp("WARNING", "Do not expose to rain or water. Keep away from children.", variant="warning"),
                    ],
                },
            ]

            # Write duplicate JP candidates to exercise deterministic deduplication
            _write_ir(root, "manual_sources/JE-M1/JP/candidates/old/manual.ir.json", _ir_bundle(model="JE-M1", region="JP", language="ja", pages=jp_pages, publication_eligible=False))
            _write_ir(root, "manual_sources/JE-M1/JP/r1/manual.ir.json", _ir_bundle(model="JE-M1", region="JP", language="ja", pages=jp_pages, publication_eligible=True, product_name="Explorer M1"))
            _write_ir(root, "manual_sources/JE-M1/JP/r2/manual.ir.json", _ir_bundle(model="JE-M1", region="JP", language="ja", pages=jp_pages, publication_eligible=True, product_name="Explorer M1"))
            _write_ir(root, "manual_sources/JE-M1/KR/manual.ir.json", _ir_bundle(model="JE-M1", region="KR", language="ko", pages=kr_pages, publication_eligible=True))
            _write_ir(root, "manual_sources/JE-M1/CN/manual.ir.json", _ir_bundle(model="JE-M1", region="CN", language="zh", pages=cn_pages, publication_eligible=True))
            _write_ir(root, "manual_sources/JE-M1/US/manual.ir.json", _ir_bundle(model="JE-M1", region="US", language="en", pages=us_pages, publication_eligible=True))
            _write_ir(root, "manual_sources/JE-M1/EU/manual.ir.json", _ir_bundle(model="JE-M1", region="EU", language="en", pages=eu_pages, publication_eligible=False))

            corpus = make_ir_corpus(roots=(root / "manual_sources",), repo_root_path=root)
            self.assertEqual(corpus["region"], "ALL")
            self.assertEqual(corpus["regions"], ["CN", "EU", "JP", "KR", "US"])
            self.assertEqual(corpus["counts"]["editions"], 5)
            self.assertEqual(len(corpus["skipped_duplicates"]), 2)
            self.assertIn("manual_sources/JE-M1/JP/candidates/old/manual.ir.json", corpus["skipped_duplicates"])
            self.assertIn("manual_sources/JE-M1/JP/r1/manual.ir.json", corpus["skipped_duplicates"])

            eligible_only = make_ir_corpus(roots=(root / "manual_sources",), publication_eligible_only=True, repo_root_path=root)
            self.assertEqual(eligible_only["regions"], ["CN", "JP", "KR", "US"])

            obs = build_ir_observations(corpus, features={})
            self.assertEqual(obs["schema"], OBS_SCHEMA)
            by_region = {r: [it for it in obs["items"] if it["observed_context"]["region"] == r] for r in corpus["regions"]}
            self.assertTrue(any(it["category"] == "compliance" and "PSE" in it["legislation"] for it in by_region["JP"]))
            self.assertTrue(any("electrical_shock" in it["topic"] for it in by_region["JP"]))
            self.assertTrue(any(it["severity"] == "caution" and "disassembly" in it["topic"] for it in by_region["KR"]))
            # KR signal legend (경고/주의) must NOT be extracted as warning items
            self.assertFalse(any(it["source"]["source_ref"] == "kr/symbols/sig" for it in by_region["KR"]))
            self.assertTrue(any("electrical_shock" in it["topic"] for it in by_region["CN"]))
            self.assertTrue(any("FCC" in it.get("legislation", []) and "UL" in it.get("legislation", []) for it in by_region["US"]))

            # Edit one JP file and verify judge_previous marks only changed items stale
            jp_pages_v2 = list(jp_pages)
            jp_pages_v2[0] = {
                "page_id": "safety",
                "flow": [
                    _heading("安全上のご注意", level=1, anchor="jp-safety"),
                    _callout_comp("警告", "感電や火災のおそれがあります。子供の手の届かない場所に保管してください。", variant="warning"),
                    _callout_comp("注意", "充電中は水濡れを避け、分解や修理を絶対に行わないでください。", variant="caution"),
                    _paragraph("廃棄時は自治体の指示に従ってください。"),
                ],
            }
            _write_ir(root, "manual_sources/JE-M1/JP/r2/manual.ir.json", _ir_bundle(model="JE-M1", region="JP", language="ja", pages=jp_pages_v2, publication_eligible=True, product_name="Explorer M1"))
            corpus_v2 = make_ir_corpus(roots=(root / "manual_sources",), repo_root_path=root)
            obs_v2 = build_ir_observations(corpus_v2, features={})
            verdict = judge_previous(obs, obs_v2["items"], corpus_v2)
            self.assertEqual(verdict["items"]["stale"], 1)
            self.assertGreater(verdict["items"]["fresh"], 5)

            # Exercise CLI flags
            prev_path = root / "prev_obs.json"
            prev_path.write_text(json.dumps(obs, ensure_ascii=False), encoding="utf-8")
            out_corpus = root / "out" / "corpus.json"
            out_obs = root / "out" / "obs.json"
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = ir_export_main([
                    "--root", str(root / "manual_sources"),
                    "--output-corpus", str(out_corpus),
                    "--output-observations", str(out_obs),
                    "--previous-observations", str(prev_path),
                ])
            self.assertEqual(rc, 0)
            cli_out = json.loads(buf.getvalue())
            self.assertEqual(cli_out["status"], "ok")
            self.assertEqual(cli_out["previous"]["items"]["stale"], 1)
            self.assertTrue(out_corpus.is_file())
            self.assertTrue(out_obs.is_file())

    def test_real_repo_multi_region_integration(self) -> None:
        root = repo_root()
        real_roots = [
            root / "data" / "manual_sources" / "JBP-3600A",
            root / "data" / "manual_sources" / "JE-300E",
            root / "manual_sources" / "JE-3000C" / "KR",
        ]
        existing_roots = [p for p in real_roots if p.exists()]
        self.assertGreaterEqual(len(existing_roots), 3)

        corpus = make_ir_corpus(roots=existing_roots, repo_root_path=root)
        self.assertEqual(corpus["region"], "ALL")
        self.assertTrue({"US", "EU", "JP", "KR"}.issubset(set(corpus["regions"])))
        self.assertGreaterEqual(corpus["counts"]["editions"], 5)

        observations = build_ir_observations(corpus)
        self.assertEqual(observations["schema"], OBS_SCHEMA)
        self.assertGreater(observations["summary"]["items"], 50)
        observed_regions = {item["observed_context"]["region"] for item in observations["items"]}
        self.assertTrue({"US", "EU", "JP", "KR"}.issubset(observed_regions))


if __name__ == "__main__":
    unittest.main()
