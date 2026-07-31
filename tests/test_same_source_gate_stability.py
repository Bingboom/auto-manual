"""CI-stability of the same-source gate inputs.

Two run-unstable inputs used to make the reference-layout gate structurally
un-passable on CI (pins made on one host could never match the next run):

1. re-synced review pages re-emitted attachment basenames with the CURRENT
   Feishu file token (tokens rotate on every export);
2. the IR ``snapshot_sha256`` hashed the snapshot manifest FILE, which embeds
   ``generated_at``.

These tests pin the fixes: frozen-name preservation across token rotation,
and a snapshot identity that depends only on table content digests.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.attachment_identity import (
    frozen_attachment_names,
    preserve_frozen_attachment_names,
)
from tools.manual_ir.builder import _normalized_page_sha256, _snapshot_sha256


FROZEN = """\
.. image:: _repo_assets/data/phase2/_attachments/symbols/1_warning_triangle_OldTokenAAAABBBBCCCC.png
.. image:: _repo_assets/data/phase2/_attachments/lcd_icons/3_battery_soc_OldTokenDDDDEEEEFFFF.png
"""

REFRESHED = """\
.. image:: _repo_assets/data/phase2/_attachments/symbols/1_warning_triangle_NewTokenGGGGHHHHIIII.png
.. image:: _repo_assets/data/phase2/_attachments/lcd_icons/3_battery_soc_NewTokenJJJJKKKKLLLL.png
"""


class PreserveFrozenAttachmentNamesTest(unittest.TestCase):
    def test_token_rotation_preserves_frozen_basenames(self) -> None:
        stable, preserved = preserve_frozen_attachment_names(
            frozen_text=FROZEN, refreshed_text=REFRESHED
        )
        self.assertEqual(preserved, 2)
        self.assertEqual(stable, FROZEN)

    def test_resync_of_identical_data_is_idempotent(self) -> None:
        once, _ = preserve_frozen_attachment_names(
            frozen_text=FROZEN, refreshed_text=REFRESHED
        )
        twice, preserved = preserve_frozen_attachment_names(
            frozen_text=once, refreshed_text=once
        )
        self.assertEqual(preserved, 0)
        self.assertEqual(twice, once)

    def test_new_identity_keeps_refreshed_name(self) -> None:
        refreshed = REFRESHED + (
            ".. image:: _repo_assets/data/phase2/_attachments/symbols/"
            "12_brand_new_icon_NewTokenMMMMNNNNOOOO.png\n"
        )
        stable, preserved = preserve_frozen_attachment_names(
            frozen_text=FROZEN, refreshed_text=refreshed
        )
        self.assertEqual(preserved, 2)
        self.assertIn("12_brand_new_icon_NewTokenMMMMNNNNOOOO.png", stable)

    def test_display_ordinal_change_still_matches_identity(self) -> None:
        refreshed = REFRESHED.replace("1_warning_triangle", "4_warning_triangle")
        stable, preserved = preserve_frozen_attachment_names(
            frozen_text=FROZEN, refreshed_text=refreshed
        )
        self.assertEqual(preserved, 2)
        self.assertIn("1_warning_triangle_OldTokenAAAABBBBCCCC.png", stable)

    def test_ambiguous_frozen_identity_is_left_untouched(self) -> None:
        frozen = FROZEN + (
            ".. image:: _repo_assets/data/phase2/_attachments/symbols/"
            "1_warning_triangle_OtherOldTokenPPPPQQQQ.png\n"
        )
        names = frozen_attachment_names(frozen)
        self.assertNotIn(
            ("symbols", "warning_triangle", ".png"), names,
            "ambiguous identities must be dropped, never guessed",
        )
        stable, preserved = preserve_frozen_attachment_names(
            frozen_text=frozen, refreshed_text=REFRESHED
        )
        self.assertIn("NewTokenGGGGHHHHIIII", stable)
        self.assertEqual(preserved, 1)  # lcd icon still preserved


class SyncReviewCopyPreservesFrozenNamesTest(unittest.TestCase):
    def test_copy_mode_keeps_frozen_attachment_basenames(self) -> None:
        from tools.review_support import SyncPlanEntry, sync_review_paths

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            review = root / "review"
            (runtime / "page").mkdir(parents=True)
            (review / "page").mkdir(parents=True)
            (review / "index.rst").write_text("index\n", encoding="utf-8")
            (review / "manifest.json").write_text("{}", encoding="utf-8")
            (runtime / "page" / "symbols_en.rst").write_text(REFRESHED, encoding="utf-8")
            (review / "page" / "symbols_en.rst").write_text(FROZEN, encoding="utf-8")

            copied = sync_review_paths(
                runtime_bundle_dir=runtime,
                review_dir=review,
                scope="params",
                plan=(SyncPlanEntry(relative_path=Path("page/symbols_en.rst"), mode="copy"),),
            )
            self.assertEqual(len(copied), 1)
            result = (review / "page" / "symbols_en.rst").read_text(encoding="utf-8")
            self.assertEqual(result, FROZEN, "re-sync must not rotate frozen attachment tokens")


class SnapshotIdentityStabilityTest(unittest.TestCase):
    @staticmethod
    def _write_snapshot(root: Path, *, generated_at: str, csv_text: str) -> None:
        root.mkdir()
        (root / "symbols_blocks.csv").write_text(csv_text, encoding="utf-8")
        (root / "snapshot_manifest.json").write_text(
            json.dumps(
                {
                    "provider": "lark_cli",
                    "generated_at": generated_at,
                    "tables": [
                        {
                            "logical_name": "symbols_blocks",
                            "file_name": "symbols_blocks.csv",
                            "sha256": "0" * 64,
                            "row_count": 1,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_timestamp_and_token_rotation_keep_identity_stable(self) -> None:
        csv_a = (
            "symbol_key,Figure\n"
            "warning,data/phase2/_attachments/symbols/1_warning_OldTokenAAAABBBBCCCC.png\n"
        )
        csv_b = (
            "symbol_key,Figure\n"
            "warning,data/phase2/_attachments/symbols/1_warning_NewTokenDDDDEEEEFFFF.png\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            self._write_snapshot(a, generated_at="2026-07-31T00:00:00+00:00", csv_text=csv_a)
            self._write_snapshot(b, generated_at="2026-07-31T12:00:00+00:00", csv_text=csv_b)
            self.assertEqual(
                _snapshot_sha256(a), _snapshot_sha256(b),
                "generated_at churn and attachment-token rotation must not change the snapshot identity",
            )

    def test_changed_table_content_changes_identity(self) -> None:
        csv_a = "symbol_key,text_en\nwarning,Hazardous practices.\n"
        csv_b = "symbol_key,text_en\nwarning,DIFFERENT WORDING.\n"
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            self._write_snapshot(a, generated_at="2026-07-31T00:00:00+00:00", csv_text=csv_a)
            self._write_snapshot(b, generated_at="2026-07-31T00:00:00+00:00", csv_text=csv_b)
            self.assertNotEqual(_snapshot_sha256(a), _snapshot_sha256(b))

    def test_legacy_manifest_without_tables_falls_back_to_file_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "snapshot_manifest.json").write_text("{\"provider\": \"x\"}", encoding="utf-8")
            self.assertIsNotNone(_snapshot_sha256(root))


class PageSourceShaStabilityTest(unittest.TestCase):
    """The per-page source_sha256 feeds the reference-layout contract pins."""

    @staticmethod
    def _write_page(path: Path, token: str) -> Path:
        path.write_text(
            ".. figure:: _assets/../_attachments/symbols/01_warning_"
            f"{token}.png\n\n   Warning symbol.\n",
            encoding="utf-8",
        )
        return path

    def test_attachment_token_rotation_keeps_page_sha_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write_page(Path(tmp) / "a.rst", "OldTokenAAAABBBBCCCC")
            b = self._write_page(Path(tmp) / "b.rst", "NewTokenDDDDEEEEFFFF")
            self.assertEqual(
                _normalized_page_sha256(a), _normalized_page_sha256(b),
                "attachment-token rotation must not change a page's pinned source_sha256",
            )

    def test_page_content_change_changes_page_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write_page(Path(tmp) / "a.rst", "OldTokenAAAABBBBCCCC")
            b = Path(tmp) / "b.rst"
            b.write_text(
                ".. figure:: _assets/../_attachments/symbols/01_warning_"
                "OldTokenAAAABBBBCCCC.png\n\n   DIFFERENT caption.\n",
                encoding="utf-8",
            )
            self.assertNotEqual(_normalized_page_sha256(a), _normalized_page_sha256(b))

    def test_attachment_ordinal_change_changes_page_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write_page(Path(tmp) / "a.rst", "OldTokenAAAABBBBCCCC")
            b = Path(tmp) / "b.rst"
            b.write_text(
                ".. figure:: _assets/../_attachments/symbols/02_warning_"
                "OldTokenAAAABBBBCCCC.png\n\n   Warning symbol.\n",
                encoding="utf-8",
            )
            self.assertNotEqual(
                _normalized_page_sha256(a), _normalized_page_sha256(b),
                "only the volatile token is normalized away; ordinal moves stay visible",
            )


if __name__ == "__main__":
    unittest.main()
