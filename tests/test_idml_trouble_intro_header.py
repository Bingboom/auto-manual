"""Troubleshooting keeps the intro and the header the source declares.

Both were being discarded between the IR and the page. The intro was never
carried by `TroublePageData` at all, and the header row was removed by the
`payload[1:]` slice in `trouble_rows` -- a slice that made sense while the
rendered header came from a per-language copy dictionary, and stopped making
sense when #979 deleted that dictionary. The printed book shows both.

The projection now carries them and only the composition that places them asks
for them, so the other troubleshooting compositions render exactly what they
rendered before. The IDML goldens do not exercise this composition, so these
tests are the coverage for that guarantee as well as for the fix.
"""

from __future__ import annotations

import inspect
import unittest

from tools.idml import ir_projection
from tools.idml.data_stories import add_trouble_story
from tools.manual_ir import ManualBlock, ManualIR, ManualPage

INTRO = "次のいずれかのエラーコードが表示された場合は、対処方法に従ってください。"
HEADER = ["エラーコード", "対処方法"]
BODY_ROWS = [["F0", "製品を再起動してください。"], ["F1", "サポートへご連絡ください。"]]


def build_ir(*payloads: tuple[str, object], language: str = "jp") -> ManualIR:
    blocks = tuple(
        ManualBlock(
            block_id=f"block-{index}",
            source_ref=f"page/troubleshooting_{language}.rst#block-{index}",
            kind=kind,
            payload=payload,
            content_sha256=f"{index:064x}",
        )
        for index, (kind, payload) in enumerate(payloads, start=1)
    )
    page = ManualPage(
        page_id="troubleshooting",
        source_ref=f"page/troubleshooting_{language}.rst",
        source_path=f"page/troubleshooting_{language}.rst",
        language=language,
        source_sha256="a" * 64,
        skipped_raw=0,
        blocks=blocks,
    )
    return ManualIR(
        model="JBP-2000B",
        region="JP",
        language=language,
        source="fixture",
        bundle_root="fixture",
        bundle_sha256="b" * 64,
        snapshot_sha256="c" * 64,
        layout_params_sha256="d" * 64,
        style_contract_sha256="e" * 64,
        content_sha256="f" * 64,
        pages=(page,),
    )


FULL_PAGE = (
    ("h1", "トラブルシューティング"),
    ("body", INTRO),
    ("table", [HEADER, *BODY_ROWS]),
)


class TroubleProjection(unittest.TestCase):
    def test_header_row_is_carried_not_discarded(self) -> None:
        self.assertEqual(
            ("エラーコード", "対処方法"),
            ir_projection.trouble_header(build_ir(*FULL_PAGE), "jp"),
        )

    def test_intro_is_carried(self) -> None:
        self.assertEqual(INTRO, ir_projection.trouble_intro(build_ir(*FULL_PAGE), "jp"))

    def test_body_rows_still_exclude_the_header(self) -> None:
        """`rows` must not change, or every other target gains a row."""
        self.assertEqual(
            (("F0", "製品を再起動してください。"), ("F1", "サポートへご連絡ください。")),
            ir_projection.trouble_rows(build_ir(*FULL_PAGE), "jp"),
        )

    def test_page_data_exposes_all_three(self) -> None:
        data = ir_projection.trouble_page_data(build_ir(*FULL_PAGE), "jp")
        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual("トラブルシューティング", data.title)
        self.assertEqual(2, len(data.rows))
        self.assertEqual(INTRO, data.intro)
        self.assertEqual(("エラーコード", "対処方法"), data.header)

    def test_prose_after_the_table_is_not_taken_as_the_intro(self) -> None:
        """Only prose ahead of the table introduces it."""
        ir = build_ir(
            ("h1", "トラブルシューティング"),
            ("table", [HEADER, *BODY_ROWS]),
            ("body", "この段落は表の後ろにあります。"),
        )
        self.assertEqual("", ir_projection.trouble_intro(ir, "jp"))

    def test_a_page_without_an_intro_reports_none(self) -> None:
        ir = build_ir(("h1", "トラブルシューティング"), ("table", [HEADER, *BODY_ROWS]))
        self.assertEqual("", ir_projection.trouble_intro(ir, "jp"))

    def test_a_one_column_table_has_no_header_pair(self) -> None:
        ir = build_ir(("h1", "x"), ("table", [["only"], ["F0"]]))
        self.assertIsNone(ir_projection.trouble_header(ir, "jp"))


class StoryDefaultsProtectOtherCompositions(unittest.TestCase):
    def test_intro_and_header_default_to_absent(self) -> None:
        """The isolation guarantee, pinned.

        `troubleshooting` and `storage_troubleshooting` call this without the
        new arguments. If either default became truthy, BP@US, BP@EU and
        JE-3000C_KR would silently gain a paragraph and a row.
        """
        signature = inspect.signature(add_trouble_story)
        self.assertEqual("", signature.parameters["intro"].default)
        self.assertIsNone(signature.parameters["header"].default)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
