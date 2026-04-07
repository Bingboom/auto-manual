from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import build_docs
from tools.gen_index_bundle import MaterializedBundle


class TestBuildDocsReviewCompat(unittest.TestCase):
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
        overlay_review_content.assert_called_once_with(
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            model="JE-1000F",
            region="US",
            lang=None,
            allowed_relative_paths=(
                Path("page") / "overview.rst",
                Path("generated") / "JE-1000F" / "spec_es.rst",
            ),
            allow_index=False,
        )


if __name__ == "__main__":
    unittest.main()
