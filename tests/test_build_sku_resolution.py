from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import build_docs
from tools import gen_index_bundle


class TestSkuResolution(unittest.TestCase):
    def _write_product_vars(self, root: Path, skus: list[str]) -> None:
        csv_path = root / "data" / "phase1" / "product_variables.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["sku_id,var_key,var_value"]
        for sku in skus:
            lines.append(f"{sku},product_name,{sku}")
        csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _tokenized_cfg(self) -> dict:
        return {
            "build": {},
            "pages": [
                {
                    "type": "csv_page",
                    "page": "safety",
                    "include_dir": "generated/{sku}",
                }
            ],
        }

    def test_explicit_sku_wins(self) -> None:
        cfg = self._tokenized_cfg()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_product_vars(root, ["JB1000", "JB2000"])
            with mock.patch.object(build_docs, "paths", SimpleNamespace(root=root)):
                picked = build_docs.resolve_build_sku(cfg, "JB2000")
            self.assertEqual("JB2000", picked)

    def test_build_docs_should_fail_fast_when_tokenized_and_multi_sku_without_arg(self) -> None:
        cfg = self._tokenized_cfg()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_product_vars(root, ["JB1000", "JB2000"])
            with mock.patch.object(build_docs, "paths", SimpleNamespace(root=root)):
                with self.assertRaises(RuntimeError):
                    build_docs.resolve_build_sku(cfg, None)

    def test_gen_index_should_fail_fast_when_tokenized_and_multi_sku_without_arg(self) -> None:
        cfg = self._tokenized_cfg()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_product_vars(root, ["JB1000", "JB2000"])
            with self.assertRaises(RuntimeError):
                gen_index_bundle.resolve_build_sku(cfg, None, root)


if __name__ == "__main__":
    unittest.main()
