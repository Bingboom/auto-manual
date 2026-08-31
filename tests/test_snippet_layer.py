from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.draft_engine import (
    SNIPPET_TOKEN_PREFIX,
    load_snippet_registry,
    resolve_snippet_tokens,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REGISTRY = DOCS / "templates" / "snippets" / "registry.yaml"
SNIPPET_DIR = DOCS / "templates" / "snippets" / "battery_long_storage_advisory"
BP_LANGS = ("en", "fr", "es", "it")


class SnippetLayerTests(unittest.TestCase):
    """Skeleton slice S3: the section-module layer stops being an empty shell."""

    def setUp(self) -> None:
        self.entries = load_snippet_registry(REGISTRY)

    def test_registry_is_no_longer_empty_and_covers_the_bp_language_set(self) -> None:
        ids = {entry.snippet_id for entry in self.entries}
        self.assertIn("battery_long_storage_advisory", ids)
        langs = {
            entry.lang
            for entry in self.entries
            if entry.snippet_id == "battery_long_storage_advisory"
        }
        self.assertEqual(set(BP_LANGS), langs)

    def test_include_pages_splice_the_snippet_verbatim(self) -> None:
        # Byte conservation is the whole safety argument for extracting a
        # module: the spliced text must equal the snippet file exactly, so a
        # page's rendered bytes (and its pinned layout digest) do not move.
        for lang in BP_LANGS:
            with self.subTest(lang=lang):
                source = (DOCS / "templates" / "page_bp" / lang / "09_storage.rst").read_text(
                    encoding="utf-8"
                )
                self.assertIn(SNIPPET_TOKEN_PREFIX, source)
                rendered, used = resolve_snippet_tokens(
                    source,
                    registry_entries=self.entries,
                    registry_path=REGISTRY,
                    docs_dir=DOCS,
                    lang=lang,
                    model="JBP-2000B",
                    region="US",
                    substitutions={},
                    vars_map={},
                    slot_map=None,
                    label="test",
                )
                body = (SNIPPET_DIR / f"{lang}.rst").read_text(encoding="utf-8").rstrip("\n")
                self.assertEqual(["battery_long_storage_advisory"], used)
                self.assertNotIn(SNIPPET_TOKEN_PREFIX, rendered)
                self.assertIn(body, rendered)

    def test_text_without_a_token_is_returned_unchanged_and_does_no_registry_work(self) -> None:
        # Every existing rst_include page takes this path. It must be a
        # byte-identical no-op, and must not even need a valid registry.
        text = "STORAGE\n=======\n\nnothing to splice here\n"
        rendered, used = resolve_snippet_tokens(
            text,
            registry_entries=[],
            registry_path=Path("/nonexistent/registry.yaml"),
            docs_dir=DOCS,
            lang="en",
            model=None,
            region=None,
            substitutions={},
            vars_map={},
            slot_map=None,
            label="test",
        )
        self.assertEqual(text, rendered)
        self.assertEqual([], used)

    def test_unknown_snippet_id_fails_loudly(self) -> None:
        with self.assertRaises(RuntimeError):
            resolve_snippet_tokens(
                "{{snippet:does_not_exist}}\n",
                registry_entries=self.entries,
                registry_path=REGISTRY,
                docs_dir=DOCS,
                lang="en",
                model=None,
                region="US",
                substitutions={},
                vars_map={},
                slot_map=None,
                label="test",
            )

    def test_generated_pages_still_require_a_recipe_bound_slot(self) -> None:
        # On a generated page the token names a recipe slot, not an id, so an
        # unbound token must stay an error instead of silently resolving.
        with self.assertRaises(RuntimeError):
            resolve_snippet_tokens(
                "{{snippet:unbound_slot}}\n",
                registry_entries=self.entries,
                registry_path=REGISTRY,
                docs_dir=DOCS,
                lang="en",
                model=None,
                region="US",
                substitutions={},
                vars_map={},
                slot_map={},
                label="test",
            )

    def test_required_placeholders_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "s.rst").write_text("| needs |X|\n", encoding="utf-8")
            registry = tmp_path / "registry.yaml"
            registry.write_text(
                "snippets:\n"
                "  - snippet_id: s\n"
                "    lang: en\n"
                "    file: s.rst\n"
                "    required_placeholders: [X]\n",
                encoding="utf-8",
            )
            entries = load_snippet_registry(registry)
            with self.assertRaises(RuntimeError):
                resolve_snippet_tokens(
                    "{{snippet:s}}\n",
                    registry_entries=entries,
                    registry_path=registry,
                    docs_dir=tmp_path,
                    lang="en",
                    model=None,
                    region=None,
                    substitutions={},
                    vars_map={},
                    slot_map=None,
                    label="test",
                )

    def test_host_copies_are_measured_not_collapsed(self) -> None:
        # S3 proves the layer works; collapsing the host copies is rollout work
        # that needs a byte diff per copy. This asserts the inventory so the
        # debt stays visible and a silent partial collapse turns it red.
        shared = DOCS / "templates" / "page_shared"
        copies = [
            path
            for path in sorted(shared.glob("*/09_storage_and_maintenance.rst"))
            if "unchargeable" in path.read_text(encoding="utf-8")
            or "impossible de le recharger" in path.read_text(encoding="utf-8")
            or "imposible recargarlo" in path.read_text(encoding="utf-8")
            or "aufgeladen" in path.read_text(encoding="utf-8")
        ]
        self.assertGreaterEqual(len(copies), 3, "host copies unexpectedly gone")
        for path in copies:
            with self.subTest(path=path.name):
                self.assertNotIn(
                    SNIPPET_TOKEN_PREFIX,
                    path.read_text(encoding="utf-8"),
                    "host copy was collapsed in S3; that is rollout work",
                )


class SnippetOrphanScopeTests(unittest.TestCase):
    def test_orphan_hood_is_repo_wide_not_per_target(self) -> None:
        # The registry is one global table shared by every line, so a snippet
        # the BP line consumes must not read as an orphan from a JP host
        # target's point of view. Before S3 the check only counted draft-recipe
        # bindings, which made every line-specific snippet a per-target
        # ORPHAN_SNIPPET failure.
        from tools.snippet_references import repo_wide_snippet_references

        referenced = repo_wide_snippet_references(DOCS)
        self.assertIn("battery_long_storage_advisory", referenced)

    def test_token_and_recipe_slot_both_count_as_references(self) -> None:
        from tools.snippet_references import repo_wide_snippet_references

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            templates = docs / "templates"
            (templates / "recipes" / "line").mkdir(parents=True)
            (templates / "page_x").mkdir(parents=True)
            (templates / "page_x" / "p.rst").write_text(
                "X\n=\n\n{{snippet:by_token}}\n", encoding="utf-8"
            )
            (templates / "recipes" / "line" / "r.yaml").write_text(
                "page_id: p\ntemplate: t.rst\nsnippet_slots:\n  slot_a: by_recipe\n",
                encoding="utf-8",
            )
            referenced = repo_wide_snippet_references(docs)
            self.assertEqual({"by_token", "by_recipe"}, referenced)


if __name__ == "__main__":
    unittest.main()
