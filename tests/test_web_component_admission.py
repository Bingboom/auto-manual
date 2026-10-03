"""Fresh admission verifies actual IR independently of self-reported coverage."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.prepared_admission_fixture import install_prepared_admission_fixture
from tools.manual_ir import read_manual_ir
from tools.manual_ir.hashing import value_sha256
from tools.web_component_admission import require_fresh_component_admission


class FreshComponentAdmissionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.policy = install_prepared_admission_fixture(self, self.root, model="MODEL", language="en")
        self.path = self.root / "manual.ir.json"
        self.original = json.loads(self.path.read_text())

    def admit(self, **changes):
        return require_fresh_component_admission(self.root, **{
            "model": "MODEL", "region": "EU", "language": "en", **changes,
        })

    def rehash(self, raw):
        hashes = []
        for page in raw["pages"]:
            for block in page["blocks"]:
                block["content_sha256"] = value_sha256({"kind": block["kind"], "payload": block["payload"]})
                hashes.append(block["content_sha256"])
        raw["metadata"]["block_count"] = len(hashes)
        raw["metadata"]["page_count"] = len(raw["pages"])
        raw["content_sha256"] = value_sha256({"page_ids": [p["page_id"] for p in raw["pages"]], "block_hashes": hashes})
        self.path.write_text(json.dumps(raw))
        read_manual_ir(self.path)  # Demonstrate rejection is not an envelope/hash failure.

    def test_valid_components_need_no_opt_in_marker(self):
        self.assertEqual(self.admit()["components"], {"HB-TABLE-SPEC": 1})

    def test_missing_or_symlink_sidecar_is_rejected(self):
        self.path.rename(self.root / "hidden.json")
        with self.assertRaisesRegex(RuntimeError, "requires a real manual IR"):
            self.admit()
        self.path.symlink_to(self.root / "hidden.json")
        with self.assertRaisesRegex(RuntimeError, "requires a real manual IR"):
            self.admit()

    def test_rehashed_deletion_is_rejected_even_with_fake_inventory(self):
        raw = deepcopy(self.original)
        raw["pages"][0]["blocks"] = []
        raw["metadata"]["component_inventory"] = {"HB-TABLE-SPEC": 1}
        self.rehash(raw)
        with self.assertRaisesRegex(RuntimeError, "expected at least 1"):
            self.admit()

    def test_rehashed_move_cannot_satisfy_original_chapter(self):
        raw = deepcopy(self.original)
        raw["pages"][0]["page_id"] = "other.rst"
        self.rehash(raw)
        with self.assertRaisesRegex(RuntimeError, "required page missing"):
            self.admit()

    def test_removed_projection_marker_is_rejected(self):
        raw = deepcopy(self.original)
        raw["metadata"].pop("projection")
        self.rehash(raw)
        with self.assertRaisesRegex(RuntimeError, "requires prepared-document"):
            self.admit()

    def test_wrong_expected_target_is_rejected(self):
        for changes in ({"model": "OTHER"}, {"region": "UK"}, {"language": "fr"}):
            with self.subTest(changes=changes), self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                self.admit(**changes)

    def test_pending_review_blocks_fresh_admission(self):
        raw = deepcopy(self.original)
        raw["metadata"]["pending_source_review"] = ["rating"]
        self.rehash(raw)
        with self.assertRaisesRegex(RuntimeError, "pending source review"):
            self.admit()

    def test_other_regions_keep_existing_admission_scope(self):
        self.path.unlink()
        self.assertIsNone(self.admit(region="US"))

    def test_unregistered_frozen_locale_identity_is_preserved(self):
        # Native import owns extended locale validation. Admission must not
        # collapse a valid native `nl` to None via the phase2 language registry.
        ir = read_manual_ir(self.path)
        from dataclasses import replace
        ir = replace(ir, language="nl")
        with patch("tools.web_component_admission.read_manual_ir", return_value=ir), \
             patch("tools.web_component_admission.audit_prepared_component_coverage", return_value={"issues": []}), \
             patch("tools.web_component_admission.render_document_fragments"):
            self.assertEqual(self.admit(language="nl")["language_baseline"]["status"], "not_enrolled")

    def test_queue_rejects_missing_ir_before_creating_destination(self):
        from tools.queue_outputs import stage_web_publish_assets_to_host_repo
        self.path.unlink()
        md = self.root / "manual.md"
        md.write_text("# Manual")
        html = self.root / "html"
        html.mkdir()
        (html / "index.html").write_text("<h1>Manual</h1>")
        destination = self.root / "release"
        with self.assertRaisesRegex(RuntimeError, "requires a real manual IR"):
            stage_web_publish_assets_to_host_repo(
                built_md_output_path=md, built_html_dir=html,
                host_config_path=self.root / "config.yaml", model="MODEL", region="EU", version="1",
                publish_release_version_dir_for_target=lambda **kwargs: destination,
            )
        self.assertFalse(destination.exists())

    def test_enrolled_candidate_blocks_both_input_kinds(self):
        from tools.prepared_component_policy import POLICY_SCHEMA
        from tools.web_language_baseline import require_language_baseline
        policy = self.root / 'policy.json'
        policy.write_text(json.dumps({
            'schema_version': POLICY_SCHEMA,
            'language_baselines': {'MODEL/EU': {
                'schema_version': 'web-language-baseline/v1',
                'baseline_language': 'en', 'status': 'candidate',
            }},
        }))
        def independent_contract(raw, root):
            return require_language_baseline(raw, root, contract_path=policy)
        with patch('tools.web_component_admission.require_language_baseline', side_effect=independent_contract):
            for source in ('prepared-document', 'frozen-ai-json', 'frozen-pdf-json'):
                with self.subTest(source=source):
                    raw = deepcopy(self.original)
                    raw['source'] = source
                    raw['metadata'].pop('language_baseline', None)
                    self.rehash(raw)
                    with self.assertRaisesRegex(RuntimeError, 'not operator-approved'):
                        self.admit()
