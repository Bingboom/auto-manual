from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import gen_index_bundle
from tools.safe_copy import copy_regular_file_no_symlinks, copytree_replace_no_symlinks


class TestRuntimeBundleSafeCopy(unittest.TestCase):
    @staticmethod
    def _write_runtime_fixture(root: Path) -> tuple[Path, dict[str, object]]:
        docs_dir = root / "docs"
        template_dir = docs_dir / "templates" / "page_en"
        data_dir = root / "data" / "phase2"
        template_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)

        (docs_dir / "conf_base.py").write_text("", encoding="utf-8")
        (template_dir / "demo.rst").write_text("Hello\n", encoding="utf-8")
        (data_dir / "Spec_Master.csv").write_text(
            "Section,Row_key,Line_order,Page,Model,Region,Is_Latest,enabled,Value_source\n"
            "GENERAL INFO,product_name,1,specifications,M1,US,1,1,Demo Product\n",
            encoding="utf-8",
        )
        (root / "data" / "asset_registry.csv").write_text(
            "asset_key,\u7c7b\u522b,\u8bed\u8a00\u7ef4\u5ea6,\u72b6\u6001,\u5f85\u65e0\u5b57\u5316,\u9002\u7528\u673a\u578b,\u9002\u7528\u533a\u57df,"
            "\u5bfc\u51fa\u7269\u8def\u5f84,\u8bed\u8a00\u53d8\u4f53,\u5185\u5bb9\u54c8\u5e0c,\u5907\u6ce8\n",
            encoding="utf-8",
        )

        cfg: dict[str, object] = {
            "build": {
                "languages": ["en"],
                "default_model": "M1",
                "default_region": "US",
            },
            "paths": {"spec_master_csv": "data/phase2/Spec_Master.csv"},
            "pages": [
                {
                    "type": "rst_include",
                    "lang": "en",
                    "file": "templates/page_en/demo.rst",
                }
            ],
        }
        return docs_dir, cfg

    def test_runtime_static_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir, cfg = self._write_runtime_fixture(root)
            static_dir = docs_dir / "_static"
            static_dir.mkdir()
            outside = root / "outside.css"
            outside.write_text("outside\n", encoding="utf-8")
            (static_dir / "alias.css").symlink_to(outside)

            with self.assertRaisesRegex(
                RuntimeError,
                "bundle support source must not contain symbolic links",
            ):
                gen_index_bundle.materialize_bundle(
                    cfg,
                    docs_dir=docs_dir,
                    repo_root=root,
                )

            copied_alias = docs_dir / "_build" / "M1" / "US" / "rst" / "_static" / "alias.css"
            self.assertFalse(copied_alias.exists())
            self.assertFalse(copied_alias.is_symlink())

    def test_runtime_junk_is_excluded_and_does_not_change_bundle_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir, cfg = self._write_runtime_fixture(root)
            static_dir = docs_dir / "_static"
            latex_dir = docs_dir / "renderers" / "latex"
            common_assets_dir = (
                docs_dir / "templates" / "word_template" / "common_assets" / "symbols"
            )
            static_dir.mkdir()
            latex_dir.mkdir(parents=True)
            common_assets_dir.mkdir(parents=True)

            (static_dir / "style.css").write_text("body {}\n", encoding="utf-8")
            (latex_dir / "manual.sty").write_text("% stable\n", encoding="utf-8")
            (common_assets_dir / "mark.svg").write_text("<svg />\n", encoding="utf-8")

            junk_files = {
                static_dir / "__pycache__" / "module.pyc": b"pycache-v1",
                static_dir / ".mypy_cache" / "state.json": b"mypy-v1",
                static_dir / ".pytest_cache" / "state": b"pytest-v1",
                static_dir / "module.pyc": b"pyc-v1",
                static_dir / "module.PYO": b"pyo-v1",
                static_dir / ".DS_Store": b"finder-v1",
                static_dir / "style.css.swp": b"swap-v1",
                static_dir / "style.css.swo": b"swap-old-v1",
                static_dir / "render.tmp": b"temp-v1",
                static_dir / "notes~": b"backup-v1",
                static_dir / ".#style.css": b"lock-v1",
                latex_dir / "__pycache__" / "renderer.pyc": b"renderer-v1",
                common_assets_dir / ".DS_Store": b"asset-finder-v1",
            }
            for path, content in junk_files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            first_bundle = gen_index_bundle.materialize_bundle(
                cfg,
                docs_dir=docs_dir,
                repo_root=root,
            )
            first_manifest = json.loads(first_bundle.manifest_path.read_text(encoding="utf-8"))

            expected_support_paths = [
                "_assets/templates/word_template/common_assets/symbols/mark.svg",
                "_static/style.css",
                "renderers/latex/manual.sty",
            ]
            self.assertEqual(
                expected_support_paths,
                [row["path"] for row in first_manifest["support_file_records"]],
            )

            for path in junk_files:
                path.write_bytes(path.read_bytes() + b"-changed")
            new_junk = latex_dir / "editor-file.tmp"
            new_junk.write_bytes(b"new junk")

            second_bundle = gen_index_bundle.materialize_bundle(
                cfg,
                docs_dir=docs_dir,
                repo_root=root,
            )
            second_manifest = json.loads(second_bundle.manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(
                first_manifest["support_file_records"],
                second_manifest["support_file_records"],
            )
            self.assertEqual(
                first_manifest["bundle_sha256"],
                second_manifest["bundle_sha256"],
            )
            self.assertFalse((second_bundle.bundle_dir / "renderers" / "latex" / new_junk.name).exists())

    def test_regular_file_copy_rejects_symlinked_destination_parent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root = root / "source"
            destination_root = root / "bundle"
            outside = root / "outside"
            source_root.mkdir()
            destination_root.mkdir()
            outside.mkdir()
            source = source_root / "source.txt"
            source.write_text("trusted\n", encoding="utf-8")
            (destination_root / "nested").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "destination.*symbolic link"):
                copy_regular_file_no_symlinks(
                    source,
                    destination_root / "nested" / "copied.txt",
                    source_root=source_root,
                    destination_root=destination_root,
                    label="fixture",
                )

            self.assertFalse((outside / "copied.txt").exists())

    def test_tree_copy_rejects_symlinked_destination_parent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            destination_root = root / "bundle"
            outside = root / "outside"
            source.mkdir()
            destination_root.mkdir()
            outside.mkdir()
            (source / "style.css").write_text("body {}\n", encoding="utf-8")
            (destination_root / "nested").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "destination.*symbolic link"):
                copytree_replace_no_symlinks(
                    source,
                    destination_root / "nested" / "static",
                    destination_root=destination_root,
                    label="fixture tree",
                )

            self.assertFalse((outside / "static").exists())

    def test_regular_file_copy_rejects_directory_destination(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root = root / "source"
            destination_root = root / "bundle"
            destination = destination_root / "index.rst"
            source_root.mkdir()
            destination.mkdir(parents=True)
            source = source_root / "payload.txt"
            source.write_bytes(b"untrusted replacement")
            outside = root / "outside.txt"
            outside.write_bytes(b"original")
            (destination / source.name).symlink_to(outside)

            with self.assertRaisesRegex(RuntimeError, "destination is not a regular file"):
                copy_regular_file_no_symlinks(
                    source,
                    destination,
                    source_root=source_root,
                    destination_root=destination_root,
                    label="fixture",
                )

            self.assertEqual(b"original", outside.read_bytes())


if __name__ == "__main__":
    unittest.main()
