from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import build_docs, build_docs_bundle
from tools.gen_index_bundle import MaterializedBundle


class TestBuildDocsReviewCompat(unittest.TestCase):
    def test_web_language_source_uses_full_shared_review_with_target_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "web" / "source" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "index.rst").write_text("source index\n", encoding="utf-8")
            review_dir = docs_dir / "_review" / "JE-1000F" / "US"
            (review_dir / "page").mkdir(parents=True)
            (review_dir / "index.rst").write_text(
                ".. include:: page/cover-en.rst\n\n.. include:: page/p20_chapter.rst\n",
                encoding="utf-8",
            )
            bundle = MaterializedBundle(
                bundle_dir=bundle_dir,
                page_dir=bundle_dir / "page",
                index_path=bundle_dir / "index.rst",
                conf_path=bundle_dir / "conf.py",
                conf_base_path=bundle_dir / "conf_base.py",
                wrapper_index_path=docs_dir / "index.rst",
                page_paths=(), title="Demo", reference_doc=None,
                model="JE-1000F", region="US", lang="en",
                languages=("en", "fr", "es"),
            )

            with (
                mock.patch.object(
                    build_docs_bundle,
                    "get_paths",
                    return_value=SimpleNamespace(docs_dir=docs_dir, root=Path(td)),
                ),
                mock.patch.object(
                    build_docs_bundle,
                    "materialize_web_language_source_bundle",
                    return_value=bundle,
                ) as materialize,
                mock.patch.object(build_docs_bundle, "overlay_review_onto_bundle") as overlay_full,
                mock.patch.object(
                    build_docs_bundle, "overlay_review_content_onto_bundle"
                ) as overlay_partial,
                mock.patch.object(
                    build_docs_bundle,
                    "finalize_materialized_bundle",
                    side_effect=lambda value, **_kwargs: value,
                ),
            ):
                result = build_docs.prepare_web_language_source_bundle(
                    {
                        "doc_type": "manual_bundle",
                        "build": {
                            "web_language_block_pages": {"00_preface.rst": "en"}
                        },
                    },
                    model="JE-1000F", region="US", lang="en",
                    source_mode="review-asis",
                    output_root=bundle_dir.parent,
                    write_wrapper_index=False,
                )

        self.assertIsNot(result, bundle)
        self.assertEqual((('00_preface.rst', 'en'),), result.lang_block_pages)
        self.assertEqual("en", materialize.call_args.kwargs["lang"])
        self.assertTrue(materialize.call_args.kwargs["skeleton_only"])
        overlay_full.assert_called_once()
        overlay_partial.assert_not_called()

    def test_web_language_block_pages_reject_unsafe_config(self) -> None:
        bundle = MaterializedBundle(
            bundle_dir=Path("bundle"),
            page_dir=Path("bundle/page"),
            index_path=Path("bundle/index.rst"),
            conf_path=Path("bundle/conf.py"),
            conf_base_path=Path("bundle/conf_base.py"),
            wrapper_index_path=Path("docs/index.rst"),
            page_paths=(),
            title="Demo",
            reference_doc=None,
            model="JE-1000F",
            region="US",
            lang="en",
        )
        for mapping in ({"../escape.rst": "en"}, {"00_preface.rst": "unknown"}):
            with self.subTest(mapping=mapping), self.assertRaises(RuntimeError):
                build_docs_bundle._with_web_language_block_pages(
                    bundle,
                    cfg={"build": {"web_language_block_pages": mapping}},
                )

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

    def test_review_asis_drops_pages_outside_resolved_bundle_languages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "EU" / "rst"
            (bundle_dir / "page").mkdir(parents=True, exist_ok=True)
            (bundle_dir / "index.rst").write_text(
                "five-language skeleton index\n",
                encoding="utf-8",
            )

            review_dir = docs_dir / "_review" / "JE-1000F" / "EU"
            (review_dir / "page").mkdir(parents=True, exist_ok=True)
            (review_dir / "index.rst").write_text(
                ".. include:: page/p66_03_product_overview_placeholder.rst\n\n"
                ".. include:: page/p81_03_product_overview_placeholder.rst\n",
                encoding="utf-8",
            )
            (review_dir / "page" / "p66_03_product_overview_placeholder.rst").write_text(
                ".. raw:: latex\n\n   \\HBApplyLang{it}\n",
                encoding="utf-8",
            )
            (review_dir / "page" / "p81_03_product_overview_placeholder.rst").write_text(
                ".. raw:: latex\n\n   \\HBApplyLang{uk}\n",
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
                region="EU",
                lang=None,
                languages=("en", "fr", "es", "de", "it"),
            )

            with (
                mock.patch.object(build_docs, "paths", SimpleNamespace(docs_dir=docs_dir)),
                mock.patch.object(build_docs, "materialize_bundle", return_value=bundle),
                mock.patch.object(
                    build_docs,
                    "finalize_materialized_bundle",
                    return_value=bundle,
                ),
            ):
                build_docs.prepare_manual_bundle(
                    {"doc_type": "manual_bundle"},
                    model="JE-1000F",
                    region="EU",
                    source_mode="review-asis",
                )

            index = (bundle_dir / "index.rst").read_text(encoding="utf-8")
            self.assertIn("p66_03_product_overview_placeholder.rst", index)
            self.assertNotIn("p81_03_product_overview_placeholder.rst", index)

    def test_review_overlay_keeps_declared_preface_for_block_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "fr" / "rst"
            page_dir = bundle_dir / "page"
            page_dir.mkdir(parents=True)
            (bundle_dir / "index.rst").write_text(
                ".. include:: page/00_preface.rst\n",
                encoding="utf-8",
            )
            (page_dir / "00_preface.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\HBApplyLang{en}\n"
                "   \\HBLangTagLine{EN}{IMPORTANT}\n\n"
                "English copy.\n\n"
                ".. raw:: latex\n\n"
                "   \\HBLangTagLine{FR}{IMPORTANT}\n\n"
                "French copy.\n",
                encoding="utf-8",
            )
            bundle = MaterializedBundle(
                bundle_dir=bundle_dir,
                page_dir=page_dir,
                index_path=bundle_dir / "index.rst",
                conf_path=bundle_dir / "conf.py",
                conf_base_path=bundle_dir / "conf_base.py",
                wrapper_index_path=docs_dir / "index.rst",
                page_paths=(),
                title="Demo",
                reference_doc=None,
                model="JE-1000F",
                region="US",
                lang="fr",
                languages=("fr",),
                lang_block_pages=(("00_preface.rst", "en"),),
            )

            with (
                mock.patch.object(build_docs, "paths", SimpleNamespace(docs_dir=docs_dir)),
                mock.patch.object(build_docs, "materialize_bundle", return_value=bundle),
                mock.patch.object(
                    build_docs,
                    "review_bundle_exists",
                    side_effect=lambda **kwargs: kwargs["lang"] is None,
                ),
                mock.patch.object(
                    build_docs,
                    "overlay_review_content_onto_bundle",
                    return_value=bundle_dir,
                ),
                mock.patch.object(
                    build_docs,
                    "finalize_materialized_bundle",
                    return_value=bundle,
                ),
            ):
                build_docs.prepare_manual_bundle(
                    {"doc_type": "manual_bundle"},
                    model="JE-1000F",
                    region="US",
                    lang="fr",
                    source_mode="review-asis",
                )

            self.assertIn(
                "page/00_preface.rst",
                (bundle_dir / "index.rst").read_text(encoding="utf-8"),
            )
            projected = (page_dir / "00_preface.rst").read_text(encoding="utf-8")
            self.assertNotIn("English copy.", projected)
            self.assertIn("French copy.", projected)


class TestSharedReviewPagePathPairs(unittest.TestCase):
    def test_shared_preface_pairs_across_language_scopes(self) -> None:
        """The trilingual preface is lang=en in the merged family manifest but
        lang=es/fr in the single-language manifests; pairing must fall back to
        identical source file + page name so review-asis still maps it."""
        from tools.review_support import _shared_review_page_path_pairs
        from tools.target_defaults import FAMILY_DEFAULT_CONFIGS

        family_config = FAMILY_DEFAULT_CONFIGS["US"]
        for target_config in ("configs/config.us-es.yaml", "configs/config.us-fr.yaml"):
            with self.subTest(target_config=target_config):
                pairs = dict(
                    _shared_review_page_path_pairs(
                        family_config_path=family_config,
                        target_config_path=target_config,
                        model="JE-1000F",
                        region="US",
                    )
                )
                self.assertEqual(
                    "page/00_preface.rst", pairs.get("page/00_preface.rst"),
                    f"shared preface must pair for {target_config}: {sorted(pairs)}",
                )


if __name__ == "__main__":
    unittest.main()
