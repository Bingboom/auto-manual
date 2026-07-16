from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import review_bundle
from tools.asset_registry import AssetRegistryError
from tools.asset_rewrites import restore_registry_asset_uris


class TestReviewBundle(unittest.TestCase):
    def test_restore_asset_uris_rejects_non_asset_original_value(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_bundle = root / "source"
            target_bundle = root / "target"
            source_bundle.mkdir()
            (target_bundle / "page").mkdir(parents=True)
            target = target_bundle / "page" / "manual.rst"
            original = ".. image:: ../_assets/managed.png\n"
            target.write_text(original, encoding="utf-8")
            (source_bundle / "asset_usage_manifest.json").write_text(
                json.dumps(
                    {
                        "rewrites": [
                            {
                                "asset_key": "demo/managed",
                                "original_value": "docs/assets/managed.png",
                                "reference_kind": "registry-uri",
                                "reference_path": "page/manual.rst",
                                "rendered_value": "../_assets/managed.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(AssetRegistryError, "invalid original asset URI"):
                restore_registry_asset_uris(
                    source_bundle_dir=source_bundle,
                    target_bundle_dir=target_bundle,
                    strict=True,
                )

            self.assertEqual(original, target.read_text(encoding="utf-8"))

    def test_restore_asset_uris_rejects_rst_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_bundle = root / "source"
            target_bundle = root / "target"
            (target_bundle / "page").mkdir(parents=True)
            source_bundle.mkdir()
            victim = root / "victim.rst"
            original = ".. image:: ../target/_assets/managed.png\n"
            victim.write_text(original, encoding="utf-8")
            (target_bundle / "page" / "manual.rst").symlink_to(victim)
            (source_bundle / "asset_usage_manifest.json").write_text(
                json.dumps(
                    {
                        "rewrites": [
                            {
                                "asset_key": "demo/managed",
                                "original_value": "asset:demo/managed",
                                "reference_kind": "registry-uri",
                                "reference_path": "page/manual.rst",
                                "rendered_value": "../target/_assets/managed.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(AssetRegistryError, "symbolic link"):
                restore_registry_asset_uris(
                    source_bundle_dir=source_bundle,
                    target_bundle_dir=target_bundle,
                    strict=False,
                )

            self.assertEqual(original, victim.read_text(encoding="utf-8"))

    def test_materialize_review_bundle_should_copy_reviewable_rst_files_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            (runtime_dir / "page").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)

            (runtime_dir / "index.rst").write_text(".. include:: page/spec_en.rst\n", encoding="utf-8")
            (runtime_dir / "page" / "spec_en.rst").write_text(
                "Spec page\n\n.. image:: ../_assets/assets/managed.png\n",
                encoding="utf-8",
            )
            (runtime_dir / "generated" / "JE-1000F" / "spec_en.rst").write_text("Generated spec\n", encoding="utf-8")
            (runtime_dir / "conf.py").write_text("ignored\n", encoding="utf-8")
            (runtime_dir / "bundle_manifest.json").write_text(
                json.dumps(
                    {
                        "page_manifest": "docs/manifests/manual_us-en.yaml",
                        "recipe_ids": ["03_product_overview"],
                        "snippet_ids": ["wireless_reset_buttons"],
                        "spec_master": {"path": "data/phase2/Spec_Master.csv", "sha256": "abc"},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime_dir / "asset_usage_manifest.json").write_text(
                json.dumps(
                    {
                        "assets": [],
                        "rewrites": [
                            {
                                "asset_key": "demo/managed",
                                "original_value": "asset:demo/managed",
                                "ordinal": 1,
                                "reference_kind": "registry-uri",
                                "reference_path": "page/spec_en.rst",
                                "rendered_value": "../_assets/assets/managed.png",
                                "staged_path": "_assets/assets/managed.png",
                            }
                        ],
                        "schema_version": 2,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="en",
            )

            self.assertTrue(bundle.index_path.exists())
            self.assertTrue((bundle.review_dir / "page" / "spec_en.rst").exists())
            self.assertTrue((bundle.review_dir / "generated" / "JE-1000F" / "spec_en.rst").exists())
            self.assertFalse((bundle.review_dir / "conf.py").exists())
            self.assertIn(
                ".. image:: asset:demo/managed",
                (bundle.review_dir / "page" / "spec_en.rst").read_text(encoding="utf-8"),
            )

            manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("JE-1000F", manifest["model"])
            self.assertEqual("US", manifest["region"])
            self.assertEqual("en", manifest["lang"])
            self.assertIn("docs/_build/JE-1000F/US/en/rst", manifest["runtime_bundle_dir"])
            self.assertIn("docs/_review/JE-1000F/US/en", manifest["review_dir"])
            self.assertEqual("docs/manifests/manual_us-en.yaml", manifest["page_manifest"])
            self.assertEqual(["03_product_overview"], manifest["recipe_ids"])
            self.assertEqual(["wireless_reset_buttons"], manifest["snippet_ids"])
            self.assertEqual(1, manifest["semantic_asset_references"])

    def test_materialize_review_bundle_should_keep_existing_review_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            review_dir = docs_dir / "_review" / "JE-1000F" / "JP"
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "generated" / "JE-1000F").mkdir(parents=True)
            (review_dir / "index.rst").write_text(".. include:: page/custom.rst\n", encoding="utf-8")
            (review_dir / "page" / "custom.rst").write_text("Edited review content\n", encoding="utf-8")
            (review_dir / "generated" / "JE-1000F" / "spec_ja.rst").write_text("Edited generated\n", encoding="utf-8")

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="JP",
            )

            self.assertTrue(bundle.reused_existing)
            self.assertEqual("Edited review content\n", (review_dir / "page" / "custom.rst").read_text(encoding="utf-8"))

    def test_materialize_review_bundle_should_support_lang_scoped_runtime_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "es" / "rst"
            (runtime_dir / "page").mkdir(parents=True)
            (runtime_dir / "generated" / "JE-1000F").mkdir(parents=True)

            (runtime_dir / "index.rst").write_text(".. include:: page/spec_es.rst\n", encoding="utf-8")
            (runtime_dir / "page" / "spec_es.rst").write_text("Spec page\n", encoding="utf-8")
            (runtime_dir / "generated" / "JE-1000F" / "spec_es.rst").write_text("Generated spec\n", encoding="utf-8")

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="es",
            )

            manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("es", manifest["lang"])
            self.assertIn("docs/_build/JE-1000F/US/es/rst", manifest["runtime_bundle_dir"])
            self.assertIn("docs/_review/JE-1000F/US/es", manifest["review_dir"])

    def test_refresh_failure_preserves_existing_review_byte_for_byte(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "overrides" / "_assets").mkdir(parents=True)

            (runtime_dir / "index.rst").write_text(
                ".. include:: page/spec_en.rst\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "spec_en.rst").write_text(
                ".. image:: ../_assets/changed.png\n",
                encoding="utf-8",
            )
            (runtime_dir / "asset_usage_manifest.json").write_text(
                json.dumps(
                    {
                        "rewrites": [
                            {
                                "asset_key": "demo/managed",
                                "original_value": "asset:demo/managed",
                                "reference_kind": "registry-uri",
                                "reference_path": "page/spec_en.rst",
                                "rendered_value": "../_assets/managed.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            (review_dir / "index.rst").write_bytes(b"human index\n")
            (review_dir / "page" / "custom.rst").write_bytes(b"human edits\n")
            (review_dir / "overrides" / "_assets" / "custom.png").write_bytes(
                b"human override"
            )
            (review_dir / "manifest.json").write_bytes(b'{"human": true}\n')

            def snapshot() -> dict[str, bytes]:
                return {
                    path.relative_to(review_dir).as_posix(): path.read_bytes()
                    for path in sorted(review_dir.rglob("*"))
                    if path.is_file()
                }

            before = snapshot()
            with self.assertRaisesRegex(
                AssetRegistryError,
                "semantic asset rewrite provenance no longer matches",
            ):
                review_bundle.materialize_review_bundle(
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                    lang="en",
                    refresh_existing=True,
                )

            self.assertEqual(before, snapshot())
            self.assertEqual([], list(review_dir.parent.glob(f".{review_dir.name}.*")))

    def test_refresh_swap_failure_rolls_back_existing_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (runtime_dir / "index.rst").write_text(
                ".. include:: page/spec_en.rst\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "spec_en.rst").write_text(
                "fresh runtime\n",
                encoding="utf-8",
            )
            (review_dir / "index.rst").write_bytes(b"human index\n")
            (review_dir / "page" / "custom.rst").write_bytes(b"human edits\n")
            before = {
                path.relative_to(review_dir).as_posix(): path.read_bytes()
                for path in sorted(review_dir.rglob("*"))
                if path.is_file()
            }
            real_replace = review_bundle.os.replace

            def fail_publish(source: object, destination: object) -> None:
                source_path = Path(source)
                destination_path = Path(destination)
                if (
                    destination_path == review_dir
                    and source_path.name.startswith(f".{review_dir.name}.refresh-")
                    and not source_path.name.endswith(".previous")
                ):
                    raise OSError("simulated publish failure")
                real_replace(source, destination)

            with (
                mock.patch.object(review_bundle.os, "replace", side_effect=fail_publish),
                self.assertRaisesRegex(OSError, "simulated publish failure"),
            ):
                review_bundle.materialize_review_bundle(
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                    lang="en",
                    refresh_existing=True,
                )

            after = {
                path.relative_to(review_dir).as_posix(): path.read_bytes()
                for path in sorted(review_dir.rglob("*"))
                if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertEqual([], list(review_dir.parent.glob(f".{review_dir.name}.*")))

    def test_refresh_first_rename_interruption_rolls_back_existing_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (runtime_dir / "index.rst").write_text(
                ".. include:: page/spec_en.rst\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "spec_en.rst").write_text(
                "fresh runtime\n",
                encoding="utf-8",
            )
            (review_dir / "index.rst").write_bytes(b"human index\n")
            (review_dir / "page" / "custom.rst").write_bytes(b"human edits\n")
            before = {
                path.relative_to(review_dir).as_posix(): path.read_bytes()
                for path in sorted(review_dir.rglob("*"))
                if path.is_file()
            }
            real_replace = review_bundle.os.replace
            interrupted = False

            def interrupt_after_rename(source: object, destination: object) -> None:
                nonlocal interrupted
                source_path = Path(source)
                destination_path = Path(destination)
                real_replace(source, destination)
                if (
                    not interrupted
                    and source_path == review_dir
                    and destination_path.name.endswith(".previous")
                ):
                    interrupted = True
                    raise OSError("simulated post-rename interruption")

            with (
                mock.patch.object(
                    review_bundle.os,
                    "replace",
                    side_effect=interrupt_after_rename,
                ),
                self.assertRaisesRegex(OSError, "simulated post-rename interruption"),
            ):
                review_bundle.materialize_review_bundle(
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                    lang="en",
                    refresh_existing=True,
                )

            after = {
                path.relative_to(review_dir).as_posix(): path.read_bytes()
                for path in sorted(review_dir.rglob("*"))
                if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertEqual([], list(review_dir.parent.glob(f".{review_dir.name}.*")))

    def test_refresh_rejects_nested_override_symlink_without_touching_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "overrides" / "_assets").mkdir(parents=True)
            (runtime_dir / "index.rst").write_text(
                ".. include:: page/spec_en.rst\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "spec_en.rst").write_text(
                "fresh runtime\n",
                encoding="utf-8",
            )
            (review_dir / "index.rst").write_bytes(b"human index\n")
            (review_dir / "page" / "custom.rst").write_bytes(b"human edits\n")
            secret = Path(td) / "secret.bin"
            secret.write_bytes(b"must not be copied")
            override_link = review_dir / "overrides" / "_assets" / "leak.png"
            override_link.symlink_to(secret)

            with self.assertRaisesRegex(
                RuntimeError,
                "review overrides must not contain symbolic links",
            ):
                review_bundle.materialize_review_bundle(
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                    lang="en",
                    refresh_existing=True,
                )

            self.assertEqual(b"human index\n", (review_dir / "index.rst").read_bytes())
            self.assertEqual(b"human edits\n", (review_dir / "page" / "custom.rst").read_bytes())
            self.assertTrue(override_link.is_symlink())
            self.assertEqual([], list(review_dir.parent.glob(f".{review_dir.name}.*")))

    def test_refresh_rejects_runtime_index_symlink_without_touching_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            outside_index = Path(td) / "outside-index.rst"
            outside_index.write_bytes(b"must not enter review\n")
            (runtime_dir / "index.rst").symlink_to(outside_index)
            (runtime_dir / "page" / "spec_en.rst").write_bytes(b"runtime page\n")
            (review_dir / "index.rst").write_bytes(b"human index\n")
            (review_dir / "page" / "custom.rst").write_bytes(b"human edits\n")

            with self.assertRaisesRegex(
                RuntimeError,
                "runtime review index must not use a symbolic link",
            ):
                review_bundle.materialize_review_bundle(
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                    lang="en",
                    refresh_existing=True,
                )

            self.assertEqual(b"human index\n", (review_dir / "index.rst").read_bytes())
            self.assertEqual(b"human edits\n", (review_dir / "page" / "custom.rst").read_bytes())
            self.assertEqual([], list(review_dir.parent.glob(f".{review_dir.name}.*")))

    def test_refresh_rejects_runtime_page_symlink_without_touching_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (runtime_dir / "index.rst").write_bytes(b"runtime index\n")
            outside_page = Path(td) / "outside-page.rst"
            outside_page.write_bytes(b"must not enter review\n")
            (runtime_dir / "page" / "leak.rst").symlink_to(outside_page)
            (review_dir / "index.rst").write_bytes(b"human index\n")
            (review_dir / "page" / "custom.rst").write_bytes(b"human edits\n")

            with self.assertRaisesRegex(
                RuntimeError,
                "runtime review page source must not contain symbolic links",
            ):
                review_bundle.materialize_review_bundle(
                    docs_dir=docs_dir,
                    model="JE-1000F",
                    region="US",
                    lang="en",
                    refresh_existing=True,
                )

            self.assertEqual(b"human index\n", (review_dir / "index.rst").read_bytes())
            self.assertEqual(b"human edits\n", (review_dir / "page" / "custom.rst").read_bytes())
            self.assertEqual([], list(review_dir.parent.glob(f".{review_dir.name}.*")))

    def test_refresh_manifest_uses_published_path_not_old_review_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            runtime_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            review_dir = docs_dir / "_review" / "JE-1000F" / "US" / "en"
            (runtime_dir / "page").mkdir(parents=True)
            (review_dir / "page").mkdir(parents=True)
            (runtime_dir / "index.rst").write_text(
                ".. include:: page/spec_en.rst\n",
                encoding="utf-8",
            )
            (runtime_dir / "page" / "spec_en.rst").write_bytes(b"fresh runtime\n")
            (review_dir / "index.rst").write_bytes(b"human index\n")
            old_target = Path(td) / "old-target.rst"
            old_target.write_bytes(b"old symlink target\n")
            (review_dir / "page" / "spec_en.rst").symlink_to(old_target)

            bundle = review_bundle.materialize_review_bundle(
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
                lang="en",
                refresh_existing=True,
            )

            published_page = review_dir / "page" / "spec_en.rst"
            self.assertFalse(published_page.is_symlink())
            self.assertEqual(b"fresh runtime\n", published_page.read_bytes())
            manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(published_page.as_posix(), manifest["page_files"][0])


if __name__ == "__main__":
    unittest.main()
