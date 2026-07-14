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
