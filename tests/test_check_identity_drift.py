from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.check_identity_drift import _is_truthy, find_identity_drift_matches

_HEADER = ["Model", "Region", "Is_Latest", "Row_key", "Source_lang", "Value_source"]


def _write_spec_master(root: Path, rows: list[dict]) -> Path:
    path = root / "Spec_Master.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in _HEADER})
    return path


def _write_bundle(root: Path, text: str) -> Path:
    bundle = root / "bundle"
    (bundle / "page").mkdir(parents=True)
    (bundle / "page" / "spec.rst").write_text(text, encoding="utf-8")
    return bundle


class IsTruthyTests(unittest.TestCase):
    def test_blank_counts_as_latest_matching_the_build(self) -> None:
        # The build renders blank-Is_Latest rows, so the drift gate must too.
        self.assertTrue(_is_truthy(""))
        self.assertTrue(_is_truthy("  "))

    def test_only_explicit_true_tokens_are_truthy(self) -> None:
        for token in ("1", "true", "TRUE", "yes", "y"):
            self.assertTrue(_is_truthy(token))
        for token in ("0", "false", "no", "n", "maybe"):
            self.assertFalse(_is_truthy(token))


class FindIdentityDriftTests(unittest.TestCase):
    def test_foreign_identity_in_blank_is_latest_row_is_still_forbidden(self) -> None:
        # The foreign row has a blank Is_Latest (valid: the build renders it), so
        # its product name must still be collected as a forbidden literal.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = _write_spec_master(
                root,
                [
                    {"Model": "JE-1000F", "Region": "US", "Is_Latest": "1",
                     "Row_key": "product_name", "Source_lang": "en",
                     "Value_source": "Jackery Explorer 1000 Plus"},
                    {"Model": "JE-2000F", "Region": "US", "Is_Latest": "",
                     "Row_key": "product_name", "Source_lang": "en",
                     "Value_source": "Jackery Explorer 2000"},
                ],
            )
            bundle = _write_bundle(root, "The Jackery Explorer 2000 ships worldwide.\n")
            matches = find_identity_drift_matches(
                bundle_dir=bundle, spec_master_csv=csv_path,
                model="JE-1000F", region="US", langs=["en"],
            )
            self.assertTrue(any(m.literal == "Jackery Explorer 2000" for m in matches))

    def test_foreign_literal_that_is_substring_of_current_name_does_not_false_fire(self) -> None:
        # "Explorer 1000" (foreign) is a substring of the current
        # "Explorer 1000 Plus" — a line carrying only the current name must NOT
        # be flagged (the N vs N-Plus catalog naming pattern).
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = _write_spec_master(
                root,
                [
                    {"Model": "JE-1000F", "Region": "US", "Is_Latest": "1",
                     "Row_key": "product_name", "Source_lang": "en",
                     "Value_source": "Jackery Explorer 1000 Plus"},
                    {"Model": "JE-1000A", "Region": "US", "Is_Latest": "1",
                     "Row_key": "product_name", "Source_lang": "en",
                     "Value_source": "Jackery Explorer 1000"},
                ],
            )
            bundle = _write_bundle(root, "Meet the Jackery Explorer 1000 Plus.\n")
            matches = find_identity_drift_matches(
                bundle_dir=bundle, spec_master_csv=csv_path,
                model="JE-1000F", region="US", langs=["en"],
            )
            self.assertEqual(matches, ())

    def test_standalone_foreign_name_still_flagged_even_when_current_name_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = _write_spec_master(
                root,
                [
                    {"Model": "JE-1000F", "Region": "US", "Is_Latest": "1",
                     "Row_key": "product_name", "Source_lang": "en",
                     "Value_source": "Jackery Explorer 1000 Plus"},
                    {"Model": "JE-1000A", "Region": "US", "Is_Latest": "1",
                     "Row_key": "product_name", "Source_lang": "en",
                     "Value_source": "Jackery Explorer 1000"},
                ],
            )
            bundle = _write_bundle(
                root,
                "The Explorer 1000 Plus replaces the older Jackery Explorer 1000 model.\n",
            )
            matches = find_identity_drift_matches(
                bundle_dir=bundle, spec_master_csv=csv_path,
                model="JE-1000F", region="US", langs=["en"],
            )
            self.assertTrue(any(m.literal == "Jackery Explorer 1000" for m in matches))


if __name__ == "__main__":
    unittest.main()
