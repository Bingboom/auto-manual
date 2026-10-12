"""Admission checks must survive deletions, relocation and claimed inventories."""
from copy import deepcopy
import unittest

from tools.prepared_component_coverage import audit_prepared_component_coverage, chapter_digest, node_digest


def component(identity):
    return {"kind": "component", "component_spec": {"component_id": identity}}


def page(identity, *nodes):
    return {"page_id": identity, "blocks": [{"payload": n} for n in nodes]}


class PreparedCoverageTests(unittest.TestCase):
    def setUp(self):
        self.raw = {
            "source": "prepared-document", "model": "TEST", "region": "EU", "language": "en",
            "metadata": {"projection": "whole-document-components/v1"},
            "pages": [page("operation.rst", component("HB-TABLE-AUTO-RESUME"))],
        }
        self.policy = {
            "target": {"model": "TEST", "region": "EU", "language": "en"},
            "capabilities": {"ac-resume": True, "app": False},
            "chapters": [
                {"id": "operation", "pages": ["operation.rst"], "capability": "ac-resume",
                 "requirements": [{"id": "resume", "components": ["HB-TABLE-AUTO-RESUME"], "minimum": 1}]},
                {"id": "app", "pages": ["app.rst"], "capability": "app", "requirements": []},
            ],
            "legacy_debt": [],
        }

    def audit(self):
        return audit_prepared_component_coverage(self.raw, self.policy)

    def test_actual_chapter_components_pass_without_report_marker(self):
        self.assertEqual(self.audit()["issues"], [])

    def test_removed_component_is_not_saved_by_claimed_inventory(self):
        self.raw["metadata"]["component_inventory"] = {"HB-TABLE-AUTO-RESUME": 1}
        self.raw["pages"][0]["blocks"] = []
        self.assertIn("operation/resume: expected at least 1, found 0", self.audit()["issues"])

    def test_component_in_wrong_chapter_does_not_count(self):
        self.raw["pages"].append(page("other.rst", component("HB-TABLE-AUTO-RESUME")))
        self.raw["pages"][0]["blocks"] = []
        self.assertTrue(self.audit()["issues"])

    def test_removed_or_renamed_chapter_is_rejected(self):
        self.raw["pages"][0]["page_id"] = "new.rst"
        self.assertIn("operation: required page missing: operation.rst", self.audit()["issues"])

    def test_unknown_capability_is_not_equivalent_to_false(self):
        del self.policy["capabilities"]["ac-resume"]
        with self.assertRaisesRegex(ValueError, "unknown capability"):
            self.audit()

    def test_battery_pack_policy_does_not_require_ac_or_app(self):
        self.policy["capabilities"]["ac-resume"] = False
        self.raw["pages"] = [page("safety.rst", {"kind": "paragraph", "children": []})]
        self.assertEqual(self.audit()["issues"], [])

    def test_duplicate_page_and_wrong_target_are_rejected(self):
        self.raw["pages"].append(deepcopy(self.raw["pages"][0]))
        self.assertIn("duplicate page: operation.rst", self.audit()["issues"])
        self.raw["language"] = "de"
        with self.assertRaisesRegex(ValueError, "target"):
            self.audit()

    def legacy_table(self):
        table = {"kind": "table", "children": [{"kind": "text", "text": "approved source"}]}
        self.raw["pages"][0]["blocks"] = [{"payload": table}]
        self.policy["legacy_debt"] = [{
            "id": "old-resume", "page_id": "operation.rst", "location": "0",
            "kind": "table", "sha256": node_digest(table), "reason": "Reviewed migration debt",
        }]
        self.policy["chapters"][0]["requirements"][0]["legacy_debt"] = ["old-resume"]
        return table

    def test_exact_legacy_debt_is_visible_and_can_satisfy_only_named_requirement(self):
        self.legacy_table()
        report = self.audit()
        self.assertEqual(report["issues"], [])
        self.assertEqual([r["id"] for r in report["legacy_debt"]], ["old-resume"])
        self.assertEqual(report["components"], {})

    def test_legacy_debt_cannot_grow_change_or_move(self):
        table = self.legacy_table()
        before = deepcopy(self.raw)
        for mode in ("duplicate", "edit", "move"):
            with self.subTest(mode=mode):
                self.raw = deepcopy(before)
                if mode == "duplicate":
                    self.raw["pages"][0]["blocks"].append({"payload": table})
                elif mode == "edit":
                    self.raw["pages"][0]["blocks"][0]["payload"]["children"][0]["text"] = "changed"
                else:
                    self.raw["pages"][0]["blocks"].insert(0, {"payload": {"kind": "text", "text": "prefix"}})
                self.assertTrue(self.audit()["issues"])

    def test_unused_exception_must_be_removed_after_migration(self):
        self.legacy_table()
        self.raw["pages"][0]["blocks"] = [{"payload": component("HB-TABLE-AUTO-RESUME")}]
        self.assertIn("unused legacy debt: old-resume", self.audit()["issues"])

    def test_generic_table_outside_known_chapters_cannot_silently_enter(self):
        self.raw["pages"].append(page("new.rst", {"kind": "table", "children": []}))
        self.assertIn("new.rst/0: unbound table", self.audit()["issues"])

    def test_carrier_table_inside_component_is_owned(self):
        node = self.raw["pages"][0]["blocks"][0]["payload"]
        node["carrier_flow"] = [{"kind": "table", "children": []}]
        self.assertEqual(self.audit()["issues"], [])

    def test_plain_image_in_app_requires_explicit_binding(self):
        self.policy["capabilities"]["app"] = True
        self.policy["chapters"][1]["inspect_images"] = True
        self.raw["pages"].append(page("app.rst", {"kind": "image", "source": "assets/a.png"}))
        self.assertIn("app.rst/0: unbound image", self.audit()["issues"])

    def test_a_candidate_cannot_disable_checks_with_projection_metadata(self):
        self.raw["metadata"] = {}
        with self.assertRaisesRegex(ValueError, "projection"):
            self.audit()

    def test_finished_panel_is_governed_artwork_not_an_app_component(self):
        digest = "a" * 64
        image = {"kind": "image", "source": "assets/panel.png", "presentation": {"html": {
            "attributes": {"class": ["manual-finished-illustration"],
                           "data-web-finished-panel-path": "original/panel.png",
                           "data-web-finished-panel-sha256": digest},
        }}}
        self.raw["metadata"].update({
            "asset_sha256": {"assets/panel.png": digest},
            "illustration_provenance": {"illustrations": [{"path": "original/panel.png", "sha256": digest}]},
        })
        self.policy["capabilities"]["app"] = True
        self.policy["chapters"][1].update({"inspect_images": True, "requirements": [
            {"id": "app", "components": ["HB-SPECIAL-APP"]},
        ]})
        self.raw["pages"].append(page("app.rst", image))
        report = self.audit()
        self.assertEqual(len(report["governed_finished_panels"]), 1)
        self.assertIn("app/app: expected at least 1, found 0", report["issues"])
        self.raw["metadata"]["asset_sha256"]["assets/panel.png"] = "b" * 64
        self.assertTrue(any("lacks matching provenance" in i for i in self.audit()["issues"]))

    def test_a_new_hb_class_does_not_manufacture_shared_ownership(self):
        node = {"kind": "table", "presentation": {"html": {"attributes": {
            "class": ["hb-made-up-shared-table"],
        }}}}
        self.raw["pages"].append(page("extra.rst", node))
        self.assertIn("extra.rst/0: unbound table", self.audit()["issues"])

    def test_duplicate_exception_or_unexplained_debt_rejected(self):
        self.legacy_table()
        self.policy["legacy_debt"].append(deepcopy(self.policy["legacy_debt"][0]))
        with self.assertRaisesRegex(ValueError, "unique identities"):
            self.audit()
        self.policy["legacy_debt"].pop()
        self.policy["legacy_debt"][0]["reason"] = " "
        with self.assertRaisesRegex(ValueError, "review reasons"):
            self.audit()

    def test_repeated_app_download_does_not_replace_device_add_variant(self):
        self.policy["capabilities"]["app"] = True
        self.policy["chapters"][1]["requirements"] = [
            {"id": "download", "components": ["HB-SPECIAL-APP/download"]},
            {"id": "device-add", "components": ["HB-SPECIAL-APP/add-device"]},
        ]
        download = component("HB-SPECIAL-APP")
        download["component_spec"]["variant"] = "download"
        self.raw["pages"].append(page("app.rst", download, deepcopy(download)))
        report = self.audit()
        self.assertEqual(report["components"]["HB-SPECIAL-APP"], 2)
        self.assertIn("app/device-add: expected at least 1, found 0", report["issues"])

    def test_legacy_chapter_cannot_grow_and_is_not_shared_component_coverage(self):
        self.policy["capabilities"]["app"] = True
        self.policy["chapters"][1].update({"inspect_images": True, "requirements": [
            {"id": "download", "components": ["HB-SPECIAL-APP/download"], "legacy_debt": ["old-app"]},
        ]})
        app = page("app.rst", {"kind": "image", "source": "assets/old.png"})
        self.raw["pages"].append(app)
        self.policy["legacy_debt"] = [{"id": "old-app", "page_id": "app.rst", "location": "",
            "kind": "chapter", "sha256": chapter_digest(app), "reason": "Reviewed old App panel"}]
        report = self.audit()
        self.assertEqual(report["issues"], [])
        self.assertNotIn("HB-SPECIAL-APP", report["components"])
        app["blocks"].append({"payload": {"kind": "image", "source": "assets/new.png"}})
        self.assertIn("unused legacy debt: old-app", self.audit()["issues"])

    def test_chapter_digest_ignores_only_component_source_directory(self):
        first = page("app.rst", component("HB-CALLOUT-STRIP"))
        spec = first["blocks"][0]["payload"]["component_spec"]
        spec["source_ref"] = "/tmp/first/page.rst#note"
        second = deepcopy(first)
        second["blocks"][0]["payload"]["component_spec"]["source_ref"] = "/relocated/page.rst#note"
        self.assertEqual(chapter_digest(first), chapter_digest(second))
        spec["source_ref"] = "/tmp/first/other.rst#note"
        self.assertNotEqual(chapter_digest(first), chapter_digest(second))

    def test_new_page_needs_applicability_review(self):
        self.policy["expected_pages"] = ["operation.rst"]
        self.raw["pages"].append(page("new-app.rst", {"kind": "paragraph", "children": []}))
        self.assertIn("unexpected page: new-app.rst", self.audit()["issues"])

    def test_rehashed_asset_metadata_cannot_reapprove_legacy_artwork(self):
        self.legacy_table()
        self.policy["legacy_debt"][0]["asset_sha256"] = {"assets/old.png": "a" * 64}
        self.raw["metadata"]["asset_sha256"] = {"assets/old.png": "a" * 64}
        self.assertEqual(self.audit()["issues"], [])
        self.raw["metadata"]["asset_sha256"]["assets/old.png"] = "b" * 64
        self.assertIn("legacy debt asset changed: old-resume/assets/old.png", self.audit()["issues"])
