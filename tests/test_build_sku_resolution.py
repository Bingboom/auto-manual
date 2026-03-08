from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import build_docs
from tools import gen_index_bundle


class TestSkuResolution(unittest.TestCase):
    def _write_product_vars(
        self,
        root: Path,
        skus: list[str],
        model_by_sku: dict[str, str] | None = None,
    ) -> None:
        csv_path = root / "data" / "phase1" / "product_variables.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["sku_id,var_key,var_value"]
        model_map = model_by_sku or {}
        for sku in skus:
            model = model_map.get(sku)
            if model:
                lines.append(f"{sku},model,{model}")
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

    def test_build_docs_should_resolve_sku_from_model(self) -> None:
        cfg = self._tokenized_cfg()
        cfg["build"] = {"default_model": "JHP-2000A"}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_product_vars(
                root,
                ["JB1000", "JB2000"],
                model_by_sku={"JB1000": "JHP-2000A", "JB2000": "JHP-3000A"},
            )
            with mock.patch.object(build_docs, "paths", SimpleNamespace(root=root)):
                picked = build_docs.resolve_build_sku(cfg, None)
            self.assertEqual("JB1000", picked)

    def test_gen_index_should_resolve_sku_from_model(self) -> None:
        cfg = self._tokenized_cfg()
        cfg["build"] = {"default_model": "JHP-2000A"}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_product_vars(
                root,
                ["JB1000", "JB2000"],
                model_by_sku={"JB1000": "JHP-2000A", "JB2000": "JHP-3000A"},
            )
            picked = gen_index_bundle.resolve_build_sku(cfg, None, root)
            self.assertEqual("JB1000", picked)


if __name__ == "__main__":
    unittest.main()
