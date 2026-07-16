from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import build_docs, build_docs_bundle
from tools.gen_index_bundle import MaterializedBundle


class TestBuildDocsReviewCompat(unittest.TestCase):
    def test_review_overlay_allowlist_rejects_escaping_skeleton_include(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle_dir = Path(td) / "rst"
            bundle_dir.mkdir()
            (bundle_dir / "index.rst").write_text(
                ".. include:: ../outside.rst\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "unsafe RST include"):
                build_docs_bundle._existing_review_overlay_paths(bundle_dir)

    def test_prepare_manual_bundle_should_fallback_to_legacy_review_dir_for_lang_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "es" / "rst"
            bundle_dir.mkdir(parents=True, exist_ok=True)
            (bundle_dir / "page").mkdir(parents=True, exist_ok=True)
            (bundle_dir / "generated" / "JE-1000F").mkdir(parents=True, exist_ok=True)
            (bundle_dir / "index.rst").write_text("runtime index\n", encoding="utf-8")
            (bundle_dir / "page" / "overview.rst").write_text("runtime overview\n", encoding="utf-8")
            (bundle_dir / "generated" / "JE-1000F" / "spec_es.rst").write_text("runtime spec\n", encoding="utf-8")

            legacy_review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (legacy_review_dir / "page").mkdir(parents=True, exist_ok=True)
            (legacy_review_dir / "page" / "overview.rst").write_text("review overview\n", encoding="utf-8")

            bundle = MaterializedBundle(
                bundle_dir=bundle_dir,
                page_dir=bundle_dir / "page",
                index_path=bundle_dir / "index.rst",
                conf_path=bundle_dir / "conf.py",
                conf_base_path=bundle_dir / "conf_base.py",
                wrapper_index_path=docs_dir / "index.rst",
                page_paths=(),
                title="Demo",
                reference_doc=None,
                model="JE-1000F",
                region="US",
                lang="es",
            )

            with (
                mock.patch.object(build_docs, "paths", SimpleNamespace(docs_dir=docs_dir)),
                mock.patch.object(build_docs, "materialize_bundle", return_value=bundle),
                mock.patch.object(build_docs, "overlay_review_onto_bundle") as overlay_review_bundle,
                mock.patch.object(build_docs, "overlay_review_content_onto_bundle") as overlay_review_content,
                mock.patch.object(
                    build_docs,
                    "finalize_materialized_bundle",
                    return_value=bundle,
                ) as finalize_bundle,
            ):
                result = build_docs.prepare_manual_bundle(
                    {"doc_type": "manual_bundle"},
                    model="JE-1000F",
                    region="US",
                    lang="es",
                    source_mode="review",
                )

        self.assertEqual(bundle, result)
        overlay_review_bundle.assert_not_called()
        finalize_bundle.assert_called_once()
        overlay_review_content.assert_called_once_with(
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            model="JE-1000F",
            region="US",
            lang=None,
            target_lang="es",
            allowed_relative_paths=(
                Path("page") / "overview.rst",
                Path("generated") / "JE-1000F" / "spec_es.rst",
            ),
            allow_index=False,
        )

    def test_prepare_manual_bundle_review_asis_materializes_skeleton_only_and_overlays(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1800B" / "JP" / "rst"
            (bundle_dir / "page").mkdir(parents=True, exist_ok=True)
            (bundle_dir / "index.rst").write_text("skeleton index\n", encoding="utf-8")

            review_dir = docs_dir / "_review" / "JE-1800B" / "JP"
            (review_dir / "page").mkdir(parents=True, exist_ok=True)
            (review_dir / "index.rst").write_text("review index\n", encoding="utf-8")
            (review_dir / "page" / "overview.rst").write_text("review overview\n", encoding="utf-8")

            bundle = MaterializedBundle(
                bundle_dir=bundle_dir,
                page_dir=bundle_dir / "page",
                index_path=bundle_dir / "index.rst",
                conf_path=bundle_dir / "conf.py",
                conf_base_path=bundle_dir / "conf_base.py",
                wrapper_index_path=docs_dir / "index.rst",
                page_paths=(),
                title="Demo",
                reference_doc=None,
                model="JE-1800B",
                region="JP",
                lang=None,
            )

            with (
                mock.patch.object(build_docs, "paths", SimpleNamespace(docs_dir=docs_dir)),
                mock.patch.object(build_docs, "materialize_bundle", return_value=bundle) as materialize,
                mock.patch.object(build_docs, "overlay_review_onto_bundle") as overlay_review_bundle,
                mock.patch.object(build_docs, "overlay_review_content_onto_bundle") as overlay_review_content,
                mock.patch.object(
                    build_docs,
                    "finalize_materialized_bundle",
                    return_value=bundle,
                ) as finalize_bundle,
            ):
                result = build_docs.prepare_manual_bundle(
                    {"doc_type": "manual_bundle"},
                    model="JE-1800B",
                    region="JP",
                    source_mode="review-asis",
                )

        self.assertEqual(bundle, result)
        # Skeleton-only materialization: no page is rendered from the data-root.
        self.assertTrue(materialize.call_args.kwargs["skeleton_only"])
        self.assertFalse(materialize.call_args.kwargs["finalize_assets"])
        # The committed review bundle is still overlaid to supply the content.
        overlay_review_bundle.assert_called_once()
        overlay_review_content.assert_not_called()
        finalize_bundle.assert_called_once()

    def test_review_asis_lang_fallback_uses_skeleton_index_as_overlay_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "en" / "rst"
            (bundle_dir / "page").mkdir(parents=True, exist_ok=True)
            (bundle_dir / "index.rst").write_text(
                ".. include:: page/00_preface.rst\n\n"
                ".. include:: page/spec_en.rst\n",
                encoding="utf-8",
            )

            shared_review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (shared_review_dir / "page").mkdir(parents=True, exist_ok=True)
            (shared_review_dir / "index.rst").write_text(
                "shared review index\n",
                encoding="utf-8",
            )
            (shared_review_dir / "manifest.json").write_text(
                '{"lang": null, "page_manifest": "docs/manifests/manual_us.yaml"}\n',
                encoding="utf-8",
            )
            (shared_review_dir / "page" / "00_preface.rst").write_text(
                "review preface\n",
                encoding="utf-8",
            )
            (shared_review_dir / "page" / "spec_en.rst").write_text(
                "review spec\n",
                encoding="utf-8",
            )

            bundle = MaterializedBundle(
                bundle_dir=bundle_dir,
                page_dir=bundle_dir / "page",
                index_path=bundle_dir / "index.rst",
                conf_path=bundle_dir / "conf.py",
                conf_base_path=bundle_dir / "conf_base.py",
                wrapper_index_path=docs_dir / "index.rst",
                page_paths=(),
                title="Demo",
                reference_doc=None,
                model="JE-1000F",
                region="US",
                lang="en",
            )

            with (
                mock.patch.object(build_docs, "paths", SimpleNamespace(docs_dir=docs_dir)),
                mock.patch.object(build_docs, "materialize_bundle", return_value=bundle),
                mock.patch.object(build_docs, "overlay_review_onto_bundle") as overlay_review_bundle,
                mock.patch.object(
                    build_docs,
                    "finalize_materialized_bundle",
                    return_value=bundle,
                ) as finalize_bundle,
            ):
                result = build_docs.prepare_manual_bundle(
                    {"doc_type": "manual_bundle"},
                    model="JE-1000F",
                    region="US",
                    lang="en",
                    source_mode="review-asis",
                )
                preface_text = (bundle_dir / "page" / "00_preface.rst").read_text(
                    encoding="utf-8"
                )
                spec_text = (bundle_dir / "page" / "spec_en.rst").read_text(
                    encoding="utf-8"
                )

        self.assertEqual(bundle, result)
        overlay_review_bundle.assert_not_called()
        finalize_bundle.assert_called_once()
        self.assertEqual("review preface\n", preface_text)
        self.assertEqual("review spec\n", spec_text)


if __name__ == "__main__":
    unittest.main()
