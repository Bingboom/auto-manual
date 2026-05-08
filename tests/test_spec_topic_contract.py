from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import spec_topic_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "spec_topics"


class SpecTopicContractTests(unittest.TestCase):
    def _copy_fixtures(self, root: Path) -> Path:
        fixtures_dir = root / "spec_topics"
        shutil.copytree(FIXTURE_DIR, fixtures_dir)
        return fixtures_dir

    def _rewrite_csv(self, path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_fixture_schema_should_pass(self) -> None:
        issues = spec_topic_contract.inspect_spec_topic_fixture_schema(FIXTURE_DIR)

        self.assertEqual([], issues)

    def test_spec_topics_should_validate_current_pilot(self) -> None:
        result = spec_topic_contract.validate_spec_topic_fixtures(fixtures_dir=FIXTURE_DIR)

        self.assertTrue(result.valid, spec_topic_contract.render_spec_topic_report(result))

    def test_missing_fixture_header_should_fail_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "spec_topics.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            fieldnames = ["topic_id", "topic_type", "page", "section", "product_family", "status", "description"]
            for row in rows:
                row.pop("section_order", None)
            self._rewrite_csv(path, rows, fieldnames)

            issues = spec_topic_contract.inspect_spec_topic_fixture_schema(fixtures_dir)

        self.assertEqual(1, len(issues))
        self.assertEqual("spec_topic.header_missing", issues[0].code)
        self.assertEqual(("section_order",), issues[0].missing)

    def test_unknown_topic_type_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "spec_topics.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0].keys())
            rows[0]["topic_type"] = "wide_table"
            self._rewrite_csv(path, rows, fieldnames)

            result = spec_topic_contract.validate_spec_topic_fixtures(fixtures_dir=fixtures_dir)

        self.assertFalse(result.valid)
        self.assertIn("spec_topic.unknown_topic_type", {issue.code for issue in result.issues})

    def test_missing_topic_reference_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "spec_topic_rows.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0].keys())
            rows[0]["topic_id"] = "missing.topic"
            self._rewrite_csv(path, rows, fieldnames)

            result = spec_topic_contract.validate_spec_topic_fixtures(fixtures_dir=fixtures_dir)

        self.assertFalse(result.valid)
        self.assertIn("spec_topic.topic_ref_missing", {issue.code for issue in result.issues})

    def test_duplicate_selector_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            path = fixtures_dir / "spec_topic_values.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0].keys())
            duplicate = dict(rows[0])
            duplicate["topic_value_id"] = "duplicate.product_name"
            rows.append(duplicate)
            self._rewrite_csv(path, rows, fieldnames)

            result = spec_topic_contract.validate_spec_topic_fixtures(fixtures_dir=fixtures_dir)

        self.assertFalse(result.valid)
        self.assertIn("spec_topic.duplicate_selector", {issue.code for issue in result.issues})

    def test_required_topic_row_without_values_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fixtures_dir = self._copy_fixtures(Path(td))
            values_path = fixtures_dir / "spec_topic_values.csv"
            with values_path.open("r", encoding="utf-8", newline="") as handle:
                rows = [row for row in csv.DictReader(handle) if row["topic_row_id"] != "spec.general_info.capacity.1"]
                fieldnames = list(rows[0].keys())
            self._rewrite_csv(values_path, rows, fieldnames)

            result = spec_topic_contract.validate_spec_topic_fixtures(fixtures_dir=fixtures_dir)

        self.assertFalse(result.valid)
        self.assertIn("spec_topic.required_row_value_missing", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
