"""A spec group may declare that it has no heading.

The BP@JP book prints its eleven specification rows as one continuous table.
BP@US and BP@EU print the same data in three groups with an INPUT / OUTPUT
PORTS heading, and the grouping mechanism was written for them: a group's title
fell back to the first selected section's own title whenever the group did not
supply one. An empty string is falsy, so `"title": ""` fell through to
`基本情報` and there was no way to ask for no heading at all.

A declared title is now honoured verbatim. Groups that omit the key keep
inheriting, which is what keeps the US and EU contracts rendering unchanged --
no contract in the repo declares an empty title, so the change is inert for
every one of them.
"""

from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml.shared_page import grouped_spec_sections
from tools.idml.style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"

SECTIONS = [
    {"title": "基本情報", "rows": [["製品の名称", "x"], ["型番", "y"]]},
    {"title": "入力ポート", "rows": [["DC 拡張ポート (入力)", "a"]]},
    {"title": "出力ポート", "rows": [["DC 拡張ポート (出力)", "b"]]},
    {"title": "温度範囲", "rows": [["充電温度", "c"]]},
]


def group(*groups: dict) -> list[dict]:
    return grouped_spec_sections(
        [dict(section) for section in SECTIONS],
        {"specifications": {"section_groups": list(groups)}},
    )


class DeclaredGroupTitles(unittest.TestCase):
    def test_empty_title_renders_rows_without_a_heading_or_orphan_marker(self) -> None:
        for native in (False, True):
            for title in ("", " ", "基本情報"):
                with self.subTest(native=native, title=title):
                    writer = IdmlWriter(
                        load_layout_params(ROOT / "data/layout_params.csv"),
                        language="ja", native_structure_markers=native,
                    )
                    sid = writer.add_spec_story(
                        group({"source_indices": [0, 1, 2, 3], "title": title}),
                        lang="ja", title="主な仕様", layout_variant="compact",
                    )
                    story = dict(writer.stories)[sid]
                    all_stories = "".join(xml for _, xml in writer.stories)
                    visible_text = "".join(
                        node.text or "" for _, xml in writer.stories
                        for node in ET.fromstring(xml).iter("Content")
                    )
                    self.assertEqual(
                        bool(title.strip()),
                        f'AppliedParagraphStyle="{paragraph_style_ref("HB Spec Section")}"' in story,
                    )
                    if not title.strip():
                        self.assertFalse("section_marker" in all_stories)
                        self.assertFalse("●" in story)
                    for section in SECTIONS:
                        for label, _value in section["rows"]:
                            self.assertIn(label, visible_text)

    def test_empty_title_means_no_heading(self) -> None:
        result = group({"source_indices": [0, 1, 2, 3], "title": ""})
        self.assertEqual(1, len(result))
        self.assertEqual("", result[0]["title"])

    def test_one_group_keeps_every_row_in_source_order(self) -> None:
        result = group({"source_indices": [0, 1, 2, 3], "title": ""})
        self.assertEqual(
            ["製品の名称", "型番", "DC 拡張ポート (入力)", "DC 拡張ポート (出力)", "充電温度"],
            [row[0] for row in result[0]["rows"]],
        )

    def test_an_omitted_title_still_inherits(self) -> None:
        """The behaviour the US and EU contracts rely on."""
        result = group(
            {"source_indices": [0]},
            {"source_indices": [1, 2], "title": "入力/出力ポート"},
            {"source_indices": [3]},
        )
        self.assertEqual(
            ["基本情報", "入力/出力ポート", "温度範囲"],
            [section["title"] for section in result],
        )

    def test_declared_title_wins_over_the_source_title(self) -> None:
        result = group({"source_indices": [0], "title": "上書き"},
                       {"source_indices": [1, 2, 3]})
        self.assertEqual("上書き", result[0]["title"])

    def test_no_groups_declared_leaves_sections_alone(self) -> None:
        untouched = grouped_spec_sections([dict(s) for s in SECTIONS], None)
        self.assertEqual(
            [s["title"] for s in SECTIONS], [s["title"] for s in untouched]
        )

    def test_every_source_section_must_be_covered_exactly_once(self) -> None:
        with self.assertRaises(ValueError):
            group({"source_indices": [0, 1], "title": ""})
        with self.assertRaises(ValueError):
            group({"source_indices": [0, 0, 1, 2, 3], "title": ""})


class ShippedContractsAreUnaffected(unittest.TestCase):
    def test_only_bp_jp_declares_an_empty_title(self) -> None:
        """Pins the blast radius of honouring declared titles.

        If another target later declares `"title": ""` it will start losing a
        heading it used to inherit, and this test is where that shows up.
        """
        declaring: dict[str, list[str]] = {}
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            empties = [
                path.stem
                for page in data.get("pages", [])
                for grp in (
                    ((page.get("composition_data") or {}).get("specifications") or {})
                    .get("section_groups") or []
                )
                if "title" in grp and not str(grp.get("title") or "")
            ]
            if empties:
                declaring[path.stem] = empties
        self.assertEqual(["jbp2000b_jp_v1_candidate"], sorted(declaring))

    def test_bp_jp_prints_one_continuous_table(self) -> None:
        data = json.loads(
            (CONTRACTS / "jbp2000b_jp_v1_candidate.json").read_text(encoding="utf-8")
        )
        groups = [
            grp
            for page in data.get("pages", [])
            for grp in (
                ((page.get("composition_data") or {}).get("specifications") or {})
                .get("section_groups") or []
            )
        ]
        self.assertEqual(1, len(groups))
        self.assertEqual("", groups[0]["title"])
        self.assertEqual([0, 1, 2, 3], groups[0]["source_indices"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
