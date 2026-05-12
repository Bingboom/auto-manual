from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import topic_map_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "topic_map"


class TopicMapContractTests(unittest.TestCase):
    def _copy_fixtures(self, root: Path) -> Path:
        fixtures_dir = root / "topic_map"
        shutil.copytree(FIXTURE_DIR, fixtures_dir)
        return fixtures_dir

    def _rewrite_csv(self, path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_fixture_schema_should_pass(self) -> None:
        issues = topic_map_contract.inspect_topic_map_fixture_schema(FIXTURE_DIR)

        self.assertEqual([], issues)

    def test_topic_map_should_validate_current_product_overview_pilot(self) -> None:
        result = topic_map_contract.validate_topic_map_fixtures(
            fixtures_dir=FIXTURE_DIR,
            repo_root=REPO_ROOT,
        )

        self.assertTrue(result.valid, topic_map_contract.render_topic_map_report(result))

    def test_missing_fixture_header_should_fail_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "topic_registry.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            fieldnames = [
                "topic_id",
                "topic_type",
                "topic_title",
                "repeatable",
                "owner",
                "status",
                "description",
            ]
            for row in rows:
                row.pop("template_path", None)
            self._rewrite_csv(path, rows, fieldnames)

            issues = topic_map_contract.inspect_topic_map_fixture_schema(fixtures_dir)

        self.assertEqual(1, len(issues))
        self.assertEqual("topic_map.header_missing", issues[0].code)
        self.assertEqual(("template_path",), issues[0].missing)

    def test_unknown_topic_type_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "topic_registry.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0].keys())
            rows[0]["topic_type"] = "unknown_widget"
            self._rewrite_csv(path, rows, fieldnames)

            result = topic_map_contract.validate_topic_map_fixtures(
                fixtures_dir=fixtures_dir,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        self.assertIn("topic_map.unknown_topic_type", {issue.code for issue in result.issues})

    def test_missing_topic_reference_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "topic_fields.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0].keys())
            rows[0]["topic_id"] = "missing.topic"
            self._rewrite_csv(path, rows, fieldnames)

            result = topic_map_contract.validate_topic_map_fixtures(
                fixtures_dir=fixtures_dir,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        self.assertIn("topic_map.topic_ref_missing", {issue.code for issue in result.issues})

    def test_missing_asset_path_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "topic_assets.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0].keys())
            rows[0]["asset_path"] = "docs/templates/word_template/common_assets/overview/missing.png"
            self._rewrite_csv(path, rows, fieldnames)

            result = topic_map_contract.validate_topic_map_fixtures(
                fixtures_dir=fixtures_dir,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        self.assertIn("topic_map.asset_missing", {issue.code for issue in result.issues})

    def test_missing_fallback_should_fail_for_localized_page_topic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "page_topic_map.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0].keys())
            for row in rows:
                if row["region"] == "JP" and row["lang"] == "ja":
                    row["fallback_lang"] = ""
                    break
            self._rewrite_csv(path, rows, fieldnames)

            result = topic_map_contract.validate_topic_map_fixtures(
                fixtures_dir=fixtures_dir,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        self.assertIn("topic_map.fallback_missing", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
