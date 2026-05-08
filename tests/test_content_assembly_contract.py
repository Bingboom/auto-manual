from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import content_assembly_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "content_assembly"
CONTRACT_PATH = REPO_ROOT / "docs" / "templates" / "assembly_contracts" / "03_product_overview.yaml"


class ContentAssemblyContractTests(unittest.TestCase):
    def _copy_fixtures(self, root: Path) -> Path:
        fixtures_dir = root / "content_assembly"
        shutil.copytree(FIXTURE_DIR, fixtures_dir)
        return fixtures_dir

    def _contract(
        self,
        root: Path,
        *,
        fallback: bool = True,
        blocks: tuple[str, ...] = ("product_identity", "feature_overview", "spec_summary", "asset_callout"),
        required_fields: tuple[str, ...] = ("product_name", "model_no"),
    ) -> Path:
        lines = [
            "page_id: 03_product_overview",
            "product_family: JE-1000F",
            "regions: [US, JP]",
            "langs: [en, ja]",
        ]
        if fallback:
            lines.extend(["fallback:", "  lang: en"])
        lines.append("blocks:")
        lines.extend(f"  - {block}" for block in blocks)
        lines.append("required_fields:")
        lines.extend(f"  - {field}" for field in required_fields)
        path = root / "contract.yaml"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_fixture_schema_should_pass(self) -> None:
        issues = content_assembly_contract.inspect_content_assembly_fixture_schema(FIXTURE_DIR)

        self.assertEqual([], issues)

    def test_contract_should_validate_current_us_jp_pilot(self) -> None:
        result = content_assembly_contract.validate_content_assembly_contract(
            contract_path=CONTRACT_PATH,
            fixtures_dir=FIXTURE_DIR,
            repo_root=REPO_ROOT,
        )

        self.assertTrue(result.valid, content_assembly_contract.render_content_assembly_report(result))

    def test_missing_fixture_header_should_fail_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixtures_dir = self._copy_fixtures(root)
            path = fixtures_dir / "content_blocks.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "block_id",
                        "block_type",
                        "parent_block_id",
                        "title_key",
                        "repeatable",
                        "region",
                        "lang",
                    ],
                )
                writer.writeheader()
                for row in rows:
                    row.pop("asset_key", None)
                    writer.writerow(row)

            issues = content_assembly_contract.inspect_content_assembly_fixture_schema(fixtures_dir)

        self.assertEqual(1, len(issues))
        self.assertEqual("fixture.header_missing", issues[0].code)
        self.assertEqual(("asset_key",), issues[0].missing)

    def test_unknown_block_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path = self._contract(root, blocks=("product_identity", "unknown_widget"))
            result = content_assembly_contract.validate_content_assembly_contract(
                contract_path=contract_path,
                fixtures_dir=FIXTURE_DIR,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        self.assertIn("contract.unknown_block_type", {issue.code for issue in result.issues})

    def test_missing_required_field_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path = self._contract(root, required_fields=("product_name", "serial_number"))
            result = content_assembly_contract.validate_content_assembly_contract(
                contract_path=contract_path,
                fixtures_dir=FIXTURE_DIR,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        matching = [issue for issue in result.issues if issue.code == "contract.required_field_missing"]
        self.assertEqual(1, len(matching))
        self.assertEqual(("serial_number",), matching[0].missing)

    def test_missing_asset_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixtures_dir = self._copy_fixtures(root)
            path = fixtures_dir / "asset_registry.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = [row for row in csv.DictReader(handle) if row["asset_key"] != "front_product"]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["asset_key", "path", "alt_key", "region", "lang", "required"],
                )
                writer.writeheader()
                writer.writerows(rows)

            result = content_assembly_contract.validate_content_assembly_contract(
                contract_path=CONTRACT_PATH,
                fixtures_dir=fixtures_dir,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        matching = [issue for issue in result.issues if issue.code == "fixture.asset_missing"]
        self.assertEqual({"front_product"}, {issue.missing[0] for issue in matching})

    def test_fallback_missing_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path = self._contract(root, fallback=False)
            result = content_assembly_contract.validate_content_assembly_contract(
                contract_path=contract_path,
                fixtures_dir=FIXTURE_DIR,
                repo_root=REPO_ROOT,
            )

        self.assertFalse(result.valid)
        self.assertIn("contract.fallback_missing", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
