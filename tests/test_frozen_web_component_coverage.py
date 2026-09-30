"""Release regressions use the actual reviewed language packages, not counts alone."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.frozen_ai_web import replay_package
from tools.frozen_web_component_coverage import (
    audit_frozen_component_coverage, require_frozen_component_coverage,
)
from tools.manual_ir.hashing import value_sha256
from tools.web_language_release_evidence import require_publishable_manual_ir


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "manual_sources"
PACKAGES = (
    ("JE-1000F", "git-20260930-c38415f5-shared-keys/four-language", ("uk", "pt", "nl", "pl")),
    ("JE-2000F", "git-20260929-eb899f44-native-web/three-language", ("pt", "nl", "pl")),
    ("JE-2000E", "git-20260929-d6462454-native-web/three-language", ("pt", "nl", "pl")),
)


def package(model, version, language):
    return SOURCES / model / "EU/nine-language" / version / "web" / language


def read(path):
    return json.loads((path / "manual.ir.json").read_text())


def replace_component(raw, identity, node):
    def visit(value):
        if isinstance(value, dict):
            if value.get("kind") == "component" and value["component_spec"]["component_id"] == identity:
                value.clear()
                value.update(deepcopy(node))
                return True
            return any(visit(child) for child in value.values())
        return isinstance(value, list) and any(visit(child) for child in value)
    assert visit(raw["pages"])


def write_rehashed(raw, directory):
    for page in raw["pages"]:
        for block in page["blocks"]:
            block["content_sha256"] = value_sha256({"kind": block["kind"], "payload": block["payload"]})
    raw["content_sha256"] = value_sha256({
        "page_ids": [p["page_id"] for p in raw["pages"]],
        "block_hashes": [b["content_sha256"] for p in raw["pages"] for b in p["blocks"]],
    })
    (directory / "manual.ir.json").write_text(json.dumps(raw))


class FrozenWebComponentCoverageTests(unittest.TestCase):
    def setUp(self):
        self.package = package(PACKAGES[0][0], PACKAGES[0][1], "pl")
        self.raw = read(self.package)

    def test_all_ten_current_native_manuals_use_shared_components(self):
        for model, version, languages in PACKAGES:
            for language in languages:
                with self.subTest(model=model, language=language):
                    report = require_frozen_component_coverage(read(package(model, version, language)))
                    self.assertTrue(report["applicable"])
                    self.assertEqual(1, report["chapters"]["operations"]["HB-TABLE-KEY-COMBINATIONS"])

    def test_exact_pre_fix_release_is_rejected_in_all_four_languages(self):
        version = "git-20260929-c38415f5-ac-wall-complete/four-language"
        for language in PACKAGES[0][2]:
            with self.subTest(language=language):
                with self.assertRaisesRegex(ValueError, "HB-TABLE-KEY-COMBINATIONS"):
                    require_frozen_component_coverage(read(package("JE-1000F", version, language)))

    def test_replacing_key_table_with_prose_cannot_fake_inventory(self):
        replace_component(self.raw, "HB-TABLE-KEY-COMBINATIONS", {
            "kind": "paragraph", "schema_version": "manual-flow/v2",
            "children": [{"kind": "text", "text": "same copy but no shared layout"}],
        })
        issues = audit_frozen_component_coverage(self.raw)["issues"]
        self.assertTrue(any("HB-TABLE-KEY-COMBINATIONS" in issue for issue in issues))
        self.assertTrue(any("component_inventory" in issue for issue in issues))

    def test_deleting_declared_inventory_does_not_disable_admission(self):
        self.raw["metadata"].pop("component_inventory")
        with self.assertRaisesRegex(ValueError, "component_inventory"):
            require_frozen_component_coverage(self.raw)

    def test_extra_generic_table_and_image_are_rejected_outside_components(self):
        for kind in ("table", "image"):
            with self.subTest(kind=kind):
                raw = deepcopy(self.raw)
                raw["pages"][0]["blocks"][0]["payload"] = {"kind": kind}
                with self.assertRaisesRegex(ValueError, "unbound " + kind):
                    require_frozen_component_coverage(raw)

    def test_component_in_wrong_chapter_does_not_satisfy_coverage(self):
        operations = next(p for p in self.raw["pages"] if p["page_id"] == "operations")
        operations["page_id"] = "not-operations"
        with self.assertRaisesRegex(ValueError, "operations: required"):
            require_frozen_component_coverage(self.raw)

    def test_approved_overview_references_and_component_carriers_remain_valid(self):
        report = require_frozen_component_coverage(read(package(PACKAGES[1][0], PACKAGES[1][1], "nl")))
        self.assertEqual(2, report["chapters"]["product_overview"]["HB-SPECIAL-REFERENCE-FIGURE"])
        self.assertTrue(report["governed_reference_figures"])

    def test_import_admission_does_not_depend_on_model_or_localized_headings(self):
        self.raw["model"] = "ANOTHER-PORTABLE-MODEL"
        self.raw["language"] = "another-language"
        self.raw["metadata"]["title"] = "A different title"
        self.assertEqual([], audit_frozen_component_coverage(self.raw)["issues"])

    def test_non_native_projection_is_outside_this_import_contract(self):
        self.assertFalse(audit_frozen_component_coverage({"source": "rst"})["applicable"])

    def test_replay_and_publish_reject_semantic_regression_before_output(self):
        self.raw["metadata"]["shared_component_coverage"] = require_frozen_component_coverage(self.raw)
        replace_component(self.raw, "HB-TABLE-KEY-COMBINATIONS", {
            "kind": "paragraph", "schema_version": "manual-flow/v2",
            "children": [{"kind": "text", "text": "lost table"}],
        })
        # Rehash the mutation: the guard must reject valid IR with wrong
        # component coverage, not merely notice a stale content digest.
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_rehashed(self.raw, directory)
            with self.assertRaisesRegex(ValueError, "HB-TABLE-KEY-COMBINATIONS"):
                replay_package(directory)
            self.assertFalse((directory / self.raw["metadata"]["markdown_filename"]).exists())
            with self.assertRaisesRegex(RuntimeError, "HB-TABLE-KEY-COMBINATIONS"):
                require_publishable_manual_ir(directory)
            # Removing the new-build marker must never bypass release sealing.
            self.raw["metadata"].pop("shared_component_coverage")
            write_rehashed(self.raw, directory)
            with self.assertRaisesRegex(RuntimeError, "HB-TABLE-KEY-COMBINATIONS"):
                require_publishable_manual_ir(directory)

    def test_legacy_ai_can_replay_but_cannot_be_republished_with_generic_tables(self):
        self.raw["source"] = "frozen-ai-json"
        replace_component(self.raw, "HB-TABLE-KEY-COMBINATIONS", {
            "kind": "paragraph", "schema_version": "manual-flow/v2",
            "children": [{"kind": "text", "text": "legacy table omission"}],
        })
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_rehashed(self.raw, directory)
            with self.assertRaisesRegex(RuntimeError, "HB-TABLE-KEY-COMBINATIONS"):
                require_publishable_manual_ir(directory)


if __name__ == "__main__":
    unittest.main()
