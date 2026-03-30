from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.validate_layout_params import validate


class TestValidateLayoutParams(unittest.TestCase):
    def _write_csv(self, root: Path, body: str) -> Path:
        p = root / "layout_params.csv"
        p.write_text(body, encoding="utf-8")
        return p

    def test_duplicate_key_reports_line(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(
                root,
                "\n".join(
                    [
                        "key,value,unit,comment",
                        "foo,1,mm,a",
                        "foo,2,mm,b",
                    ]
                )
                + "\n",
            )
            issues = validate(csv_path)
            msgs = [i.msg for i in issues if i.level == "ERROR"]
            self.assertTrue(any("line" in m and "Duplicate key" in m for m in msgs))

    def test_numeric_error_should_include_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(
                root,
                "\n".join(
                    [
                        "key,value,unit,comment",
                        "foo,not-a-number,mm,bad",
                    ]
                )
                + "\n",
            )
            issues = validate(csv_path)
            msgs = [i.msg for i in issues if i.level == "ERROR"]
            numeric_msg = next(m for m in msgs if "Numeric value expected" in m)
            self.assertIn("line", numeric_msg)


if __name__ == "__main__":
    unittest.main()

