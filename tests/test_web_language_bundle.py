from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tools.gen_index_bundle import MaterializedBundle
from tools.web_language_bundle import materialize_web_language_projection, split_web_bundle


class LanguageBundleTests(unittest.TestCase):
    def project(self, language="fr"):
        return split_web_bundle(self.bundle, language=language, destination=self.root / language)

    def test_missing_mixed_translation_fails_before_output(self):
        self.bundle = replace(self.bundle, languages=("en", "fr", "de"))
        with self.assertRaisesRegex(ValueError, "no declared block"):
            self.project("de")
        self.assertFalse((self.root / "de").exists())

    def test_unknown_language_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the frozen bundle"):
            self.project("unknown")

    def test_implicit_foreign_preface_is_not_relabeled_as_target_language(self):
        page = self.bundle.page_dir / "00_preface.rst"
        page.write_text("English preface.\n\n**FR IMPORTANT**\n\nPréface française.\n")
        result = self.project()
        preface = result.page_paths[0].read_text()
        self.assertIn("Préface française", preface)
        self.assertNotIn("English preface", preface)
        self.assertNotIn("projection boundary", preface)

    def test_existing_destination_is_untouched(self):
        target = self.root / "fr"
        target.mkdir()
        (target / "keep").write_text("unchanged")
        with self.assertRaisesRegex(ValueError, "must be new"):
            self.project()
        self.assertEqual((target / "keep").read_text(), "unchanged")

    def test_canonical_projection_replaces_existing_bundle_and_rebases_paths(self):
        canonical = self.root / "canonical" / "rst"
        canonical.mkdir(parents=True)
        (canonical / "stale.rst").write_text("stale")
        self.bundle = replace(self.bundle, wrapper_index_path=self.root / "index.rst")
        result = materialize_web_language_projection(
            self.bundle,
            language="fr",
            destination=canonical,
            write_wrapper_index=True,
        )
        self.assertEqual(canonical.resolve(), result.bundle_dir)
        self.assertTrue(
            all(path.is_relative_to(canonical.resolve()) for path in result.page_paths)
        )
        self.assertFalse((canonical / "stale.rst").exists())
        self.assertIn(
            ".. include:: canonical/rst/index",
            self.bundle.wrapper_index_path.read_text(encoding="utf-8"),
        )

    def test_failed_projection_leaves_existing_canonical_bundle_untouched(self):
        canonical = self.root / "canonical" / "rst"
        canonical.mkdir(parents=True)
        sentinel = canonical / "keep"
        sentinel.write_text("unchanged")
        self.bundle = replace(self.bundle, languages=("en",))
        with self.assertRaisesRegex(ValueError, "outside the frozen bundle"):
            materialize_web_language_projection(
                self.bundle,
                language="fr",
                destination=canonical,
                write_wrapper_index=False,
            )
        self.assertEqual("unchanged", sentinel.read_text())

    def test_projection_rejects_symlink_destination_or_parent(self):
        real = self.root / "real"
        real.mkdir()
        direct = self.root / "direct"
        direct.symlink_to(real, target_is_directory=True)
        linked_parent = self.root / "linked-parent"
        linked_parent.symlink_to(real, target_is_directory=True)

        for destination in (direct, linked_parent / "rst"):
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(ValueError, "symbolic link"):
                    materialize_web_language_projection(
                        self.bundle,
                        language="fr",
                        destination=destination,
                        write_wrapper_index=False,
                    )

    def test_failed_rollback_preserves_previous_bundle_backup(self):
        canonical = self.root / "canonical" / "rst"
        canonical.mkdir(parents=True)
        (canonical / "keep").write_text("previous")
        wrapper_directory = self.root / "wrapper-directory"
        wrapper_directory.mkdir()
        self.bundle = replace(self.bundle, wrapper_index_path=wrapper_directory)
        original_rename = Path.rename

        def fail_restore(path: Path, target: Path) -> Path:
            if path.name == "previous":
                raise OSError("restore blocked")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", new=fail_restore):
            with self.assertRaisesRegex(RuntimeError, "previous bundle preserved at"):
                materialize_web_language_projection(
                    self.bundle,
                    language="fr",
                    destination=canonical,
                    write_wrapper_index=True,
                )

        backups = list(canonical.parent.glob(".web-language-projection.*/previous/keep"))
        self.assertEqual(1, len(backups))
        self.assertEqual("previous", backups[0].read_text())

    def test_failed_atomic_wrapper_replace_restores_bundle_and_wrapper(self):
        canonical = self.root / "canonical" / "rst"
        canonical.mkdir(parents=True)
        sentinel = canonical / "keep"
        sentinel.write_text("previous")
        wrapper = self.root / "wrapper.rst"
        wrapper.write_text("old wrapper")
        self.bundle = replace(self.bundle, wrapper_index_path=wrapper)

        with mock.patch("tools.web_language_bundle.os.replace", side_effect=OSError("blocked")):
            with self.assertRaisesRegex(OSError, "blocked"):
                materialize_web_language_projection(
                    self.bundle,
                    language="fr",
                    destination=canonical,
                    write_wrapper_index=True,
                )

        self.assertEqual("previous", sentinel.read_text())
        self.assertEqual("old wrapper", wrapper.read_text())

    def test_canonical_projection_rejects_symlink_destination_or_parent(self):
        real = self.root / "real"
        real.mkdir()
        direct = self.root / "direct"
        direct.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            materialize_web_language_projection(
                self.bundle, language="fr", destination=direct, write_wrapper_index=False,
            )

        linked_parent = self.root / "linked-parent"
        linked_parent.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            materialize_web_language_projection(
                self.bundle,
                language="fr",
                destination=linked_parent / "rst",
                write_wrapper_index=False,
            )

    def test_rollback_failure_preserves_previous_bundle_backup(self):
        canonical = self.root / "canonical" / "rst"
        canonical.mkdir(parents=True)
        (canonical / "keep").write_text("previous")
        wrapper_directory = self.root / "wrapper-directory"
        wrapper_directory.mkdir()
        self.bundle = replace(self.bundle, wrapper_index_path=wrapper_directory)
        original_rename = Path.rename

        def fail_restore(path: Path, target: Path) -> Path:
            if path.name == "previous":
                raise OSError("restore blocked")
            return original_rename(path, target)

        with (
            mock.patch.object(Path, "rename", new=fail_restore),
            self.assertRaisesRegex(RuntimeError, "previous bundle preserved at"),
        ):
            materialize_web_language_projection(
                self.bundle,
                language="fr",
                destination=canonical,
                write_wrapper_index=True,
            )

        backups = list(canonical.parent.glob(".web-language-projection.*/previous/keep"))
        self.assertEqual(1, len(backups))
        self.assertEqual("previous", backups[0].read_text())

    def test_nested_source_destination_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the source"):
            split_web_bundle(self.bundle, language="fr", destination=self.source / "derived")

    def test_foreign_nested_include_rejected_before_output(self):
        page = self.bundle.page_dir / "p20_chapter.rst"
        page.write_text(page.read_text() + "\n.. include:: chapter.rst\n")
        with self.assertRaisesRegex(ValueError, "foreign or unknown"):
            self.project()
        self.assertFalse((self.root / "fr").exists())

    def test_escaping_nested_include_rejected_before_output(self):
        outside = self.root / "external.rst"
        outside.write_text("Not part of bundle")
        page = self.bundle.page_dir / "p20_chapter.rst"
        page.write_text(page.read_text() + "\n.. include:: ../../external.rst\n")
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.project()
        self.assertFalse((self.root / "fr").exists())

    def test_neutral_fragment_and_frozen_asset_are_preserved(self):
        page = self.bundle.page_dir / "p20_chapter.rst"
        page.write_text(page.read_text() + "\n.. include:: neutral.rst\n")
        (page.parent / "neutral.rst").write_text("Shared structural fragment")
        (self.source / "asset.svg").write_text("<svg/>")
        result = self.project()
        self.assertTrue((result.page_dir / "neutral.rst").exists())
        self.assertEqual((result.bundle_dir / "asset.svg").read_bytes(), b"<svg/>")

    def test_asset_usage_manifest_is_projected_to_retained_rst_closure(self):
        manifest = self.source / "asset_usage_manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "assets": [
                        {
                            "asset_key": "shared",
                            "references": ["page/chapter.rst", "page/p20_chapter.rst"],
                        },
                        {"asset_key": "english-only", "references": ["page/chapter.rst"]},
                    ],
                    "rewrites": [
                        {"reference_path": "page/chapter.rst", "rendered_value": "en.png"},
                        {"reference_path": "page/p20_chapter.rst", "rendered_value": "fr.png"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        result = self.project()
        projected = json.loads(
            (result.bundle_dir / "asset_usage_manifest.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            [{"asset_key": "shared", "references": ["page/p20_chapter.rst"]}],
            projected["assets"],
        )
        self.assertEqual(
            [{"reference_path": "page/p20_chapter.rst", "rendered_value": "fr.png"}],
            projected["rewrites"],
        )

    def test_malformed_asset_usage_manifest_fails_before_projection(self):
        (self.source / "asset_usage_manifest.json").write_text(
            json.dumps({"assets": [], "rewrites": [{"reference_path": 7}]}),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "invalid RST reference"):
            self.project()
        self.assertFalse((self.root / "fr").exists())

    def test_index_outside_bundle_rejected(self):
        external = self.root / "external_index.rst"
        external.write_text(".. include:: source/page/chapter.rst\n")
        self.bundle = replace(self.bundle, index_path=external)
        with self.assertRaisesRegex(ValueError, "Index escapes"):
            self.project()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        page = self.source / "page"
        page.mkdir(parents=True)
        (page / "00_preface.rst").write_text(
            ".. raw:: latex\n\n   \\HBApplyLang{en}\n\n"
            "**EN IMPORTANT**\n\nEnglish preface.\n\n"
            "**FR IMPORTANT**\n\nPréface française.\n\n", encoding="utf-8")
        for name, lang in [("chapter.rst", "en"), ("p20_chapter.rst", "fr")]:
            (page / name).write_text(f".. raw:: latex\n\n   \\HBApplyLang{{{lang}}}\n\n{name}\n", encoding="utf-8")
        included = (page / "00_preface.rst", page / "p20_chapter.rst", page / "chapter.rst")
        index = self.source / "index.rst"
        index.write_text("\n".join(f".. include:: page/{p.name}\n" for p in included))
        self.bundle = MaterializedBundle(
            bundle_dir=self.source, page_dir=page, index_path=index,
            conf_path=self.source / "conf.py", conf_base_path=self.source / "conf_base.py",
            wrapper_index_path=self.source / "wrapper.rst", page_paths=included,
            title="Example manual", reference_doc=None, model="Example", region="US", lang=None,
            languages=("en", "fr"), lang_block_pages=(("00_preface.rst", "en"),),
        )

    def test_explicit_scope_preserves_order_and_original_bytes(self):
        original = {p: p.read_bytes() for p in self.source.rglob("*") if p.is_file()}
        result = split_web_bundle(self.bundle, language="fr", destination=self.root / "fr")
        self.assertEqual([p.name for p in result.page_paths], ["00_preface_fr.rst", "p20_chapter.rst"])
        self.assertEqual(result.languages, ("fr",))
        preface = result.page_paths[0].read_text()
        self.assertIn("Préface française", preface)
        self.assertNotIn("English preface", preface)
        self.assertIn(r"\HBApplyLang{fr}", preface)
        self.assertFalse((result.page_dir / "chapter.rst").exists())
        self.assertEqual(original, {p: p.read_bytes() for p in original})

    def test_undeclared_language_page_is_not_silently_retained(self):
        (self.bundle.page_dir / "chapter.rst").write_text("Undeclared copy")
        with self.assertRaisesRegex(ValueError, "explicit language"):
            split_web_bundle(self.bundle, language="en", destination=self.root / "en")
        self.assertFalse((self.root / "en").exists())

    def test_external_include_and_symlink_are_rejected(self):
        outside = self.root / "foreign.rst"
        outside.write_text("Foreign content")
        self.bundle.index_path.write_text(".. include:: ../foreign.rst\n")
        with self.assertRaisesRegex(ValueError, "escapes"):
            split_web_bundle(self.bundle, language="en", destination=self.root / "en")
        (self.source / "linked").symlink_to(outside)
        with self.assertRaises(Exception):
            split_web_bundle(self.bundle, language="en", destination=self.root / "en")
