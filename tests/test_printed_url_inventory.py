from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import printed_url_inventory


def _repo(tmp: str) -> Path:
    root = Path(tmp)
    (root / "docs" / "templates" / "page_us").mkdir(parents=True)
    (root / "configs").mkdir()
    (root / "data").mkdir()
    return root


class TestScan(unittest.TestCase):
    def test_urls_and_emails_are_collected_with_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            (root / "docs" / "templates" / "page_us" / "11_warranty.rst").write_text(
                "Visit https://support.jackery.com for help.\n"
                "Contact hello@jackery.com.\n",
                encoding="utf-8",
            )
            (root / "configs" / "config.us.yaml").write_text(
                "build:\n  rst_substitutions:\n    WARRANTY_EMAIL: hello@jackery.com\n",
                encoding="utf-8",
            )
            rows = printed_url_inventory.build_inventory_rows(root)
        by_target = {row["target"]: row for row in rows}
        self.assertIn("https://support.jackery.com", by_target)
        self.assertEqual(by_target["hello@jackery.com"]["kind"], "email")
        self.assertEqual(by_target["hello@jackery.com"]["occurrences"], "2")
        self.assertIn("configs/config.us.yaml", by_target["hello@jackery.com"]["sources"])

    def test_trailing_punctuation_is_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            (root / "docs" / "templates" / "a.rst").write_text(
                "见 https://example.com/manual。\n", encoding="utf-8"
            )
            rows = printed_url_inventory.build_inventory_rows(root)
        self.assertEqual(rows[0]["target"], "https://example.com/manual")

    def test_manual_entries_merge_for_qr_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            (root / "data" / "printed_url_manual_entries.csv").write_text(
                "target,kind,source_note\n"
                "https://qr.example.com/app,qr,back_cover QR asset\n",
                encoding="utf-8",
            )
            rows = printed_url_inventory.build_inventory_rows(root)
        self.assertEqual(rows[0]["target"], "https://qr.example.com/app")
        self.assertEqual(rows[0]["kind"], "qr")

    def test_binary_and_foreign_suffixes_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            (root / "docs" / "templates" / "img.png").write_bytes(b"https://not-a-real-scan.com")
            rows = printed_url_inventory.build_inventory_rows(root)
        self.assertEqual(rows, [])


class TestCheck(unittest.TestCase):
    def test_scan_then_check_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            (root / "docs" / "templates" / "a.rst").write_text(
                "https://example.com\n", encoding="utf-8"
            )
            self.assertEqual(
                printed_url_inventory.main(["--repo-root", str(root), "scan"]), 0
            )
            self.assertEqual(
                printed_url_inventory.main(["--repo-root", str(root), "check"]), 0
            )
            (root / "docs" / "templates" / "a.rst").write_text(
                "https://example.com\nhttps://new.example.com\n", encoding="utf-8"
            )
            self.assertEqual(
                printed_url_inventory.main(["--repo-root", str(root), "check"]), 1
            )


if __name__ == "__main__":
    unittest.main()


class _Record:
    """Minimal stand-in for AssetRecord's cross-check surface."""

    def __init__(self, asset_key: str, category: str, status: str) -> None:
        self.asset_key = asset_key
        self.category = category
        self.status = status


def _with_entries(root: Path, rows: str) -> None:
    (root / "data" / "printed_url_manual_entries.csv").write_text(
        "target,kind,asset_key,source_note\n" + rows, encoding="utf-8")


class TestQrCrossCheck(unittest.TestCase):
    def test_registered_approved_qr_is_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            _with_entries(root, "160102000404,qr,qr/back_cover,AI master p59\n")
            issues = printed_url_inventory.crosscheck_qr_targets(
                [_Record("qr/back_cover", "二维码", "✅成品")], repo_root=root)
        self.assertEqual(issues, ())

    def test_approved_qr_without_a_printed_target_is_an_error(self) -> None:
        """A QR's payload cannot be proofread off the page; it must be recorded."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            _with_entries(root, "")
            issues = printed_url_inventory.crosscheck_qr_targets(
                [_Record("qr/back_cover", "二维码", "✅成品")], repo_root=root)
        self.assertEqual([code for code, _, _ in issues], ["qr_target_unregistered"])

    def test_quarantined_qr_may_not_be_a_printed_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            _with_entries(root, "160102000161,qr,qr/frozen_reference,old revision\n")
            issues = printed_url_inventory.crosscheck_qr_targets(
                [_Record("qr/frozen_reference", "二维码", "⛔隔离")], repo_root=root)
        self.assertEqual([code for code, _, _ in issues], ["qr_target_not_shippable"])

    def test_printed_target_pointing_at_an_unregistered_asset_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            _with_entries(root, "160102000404,qr,qr/does_not_exist,stale pointer\n")
            issues = printed_url_inventory.crosscheck_qr_targets([], repo_root=root)
        self.assertEqual([code for code, _, _ in issues], ["qr_target_unknown_asset"])

    def test_non_qr_assets_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            _with_entries(root, "")
            issues = printed_url_inventory.crosscheck_qr_targets(
                [_Record("hero/lcd_display", "插图", "✅成品")], repo_root=root)
        self.assertEqual(issues, ())
