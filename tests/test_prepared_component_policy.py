"""Trusted enrollment is independent of candidate headings and inventories."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.prepared_component_policy import POLICY_FILENAME, resolve_prepared_component_policy
from tools.utils.path_utils import get_paths


class PreparedPolicyTests(unittest.TestCase):
    def test_native_profile_still_rejects_deleted_lcd_components(self):
        from copy import deepcopy
        from tools.prepared_component_coverage import audit_prepared_component_coverage

        root = Path(__file__).resolve().parents[1]
        source = root / "manual_sources/JE-3600A/EU/en/git-20261002-47a346dc/web/en/manual.ir.json"
        raw = json.loads(source.read_text())
        policy = resolve_prepared_component_policy(
            model="JE-3600A", region="EU", language="en",
            source_sha256="47a346dcfec4966ac98fbe1426e4f2b89cf54a964e4d1baf2ad9c7b02dc78043",
        )
        raw["metadata"]["page_slots"] = policy["expected_slots"]
        self.assertEqual(audit_prepared_component_coverage(raw, policy)["issues"], [])
        changed = deepcopy(raw)
        page = next(p for p in changed["pages"] if p["page_id"] == "lcd_display")
        page["blocks"] = []
        # Even the old, untouched self-reported inventory cannot waive the map.
        issues = audit_prepared_component_coverage(changed, policy)["issues"]
        self.assertTrue(any("lcd_display/HB-TABLE-LCD" in issue for issue in issues), issues)

    def test_reviewed_source_profile_preserves_historical_projection(self):
        identity = dict(model="JE-3600A", region="EU", language="en")
        historical = resolve_prepared_component_policy(**identity)
        native = resolve_prepared_component_policy(
            **identity,
            source_sha256="47a346dcfec4966ac98fbe1426e4f2b89cf54a964e4d1baf2ad9c7b02dc78043",
        )
        self.assertIn("safety_en.rst", historical["expected_pages"])
        self.assertNotIn("safety", historical["expected_pages"])
        self.assertEqual(native["expected_slots"]["safety"], "native/safety")
        self.assertEqual(len(native["expected_pages"]), 16)
        self.assertEqual(resolve_prepared_component_policy(**identity, source_sha256="0" * 64), historical)
        with self.assertRaisesRegex(ValueError, "applicability must be reviewed"):
            resolve_prepared_component_policy(
                model="NEW", region="EU", language="en",
                source_sha256="47a346dcfec4966ac98fbe1426e4f2b89cf54a964e4d1baf2ad9c7b02dc78043",
            )

    def test_all_reviewed_targets_resolve_against_capability_ssot(self):
        contract = json.loads((get_paths().renderer_contracts_dir / POLICY_FILENAME).read_text())
        self.assertEqual(len(contract["targets"]), 75)
        for key in contract["targets"]:
            model, region, language = key.split("/")
            with self.subTest(target=key):
                policy = resolve_prepared_component_policy(model=model, region=region, language=language)
                self.assertTrue(policy["expected_pages"])
                self.assertEqual(set(policy["expected_pages"]), set(policy["expected_slots"]))

    def test_renamed_csv_and_template_slots_use_reviewed_identity(self):
        policy = resolve_prepared_component_policy(model="JBP-2000B", region="EU", language="de")
        chapter = next(r for r in policy["chapters"] if r["id"] == "symbol_meaning_de.rst")
        self.assertTrue(any("HB-TABLE-SYMBOL-SIGNAL" in r["id"] for r in chapter["requirements"]))
        policy = resolve_prepared_component_policy(model="JE-1000F", region="EU", language="en")
        self.assertEqual(policy["expected_slots"]["11_warranty.rst"], "templates/page_shared/en/11_warranty.rst")

    def test_capability_change_requires_applicability_review(self):
        with patch("tools.prepared_component_policy.load_capabilities", return_value={"JE-1000H_EU": {}}):
            with self.assertRaisesRegex(ValueError, "capability requires review"):
                resolve_prepared_component_policy(model="JE-1000H", region="EU", language="en")

    def test_unregistered_target_or_missing_capability_decision_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "applicability must be reviewed"):
            resolve_prepared_component_policy(model="NEW", region="EU", language="en")
        with patch("tools.prepared_component_policy.load_known_missing", return_value={}):
            with self.assertRaisesRegex(ValueError, "unreviewed missing capability"):
                resolve_prepared_component_policy(model="JA-AD01A", region="EU", language="en")

    def test_accessory_does_not_inherit_host_app_or_ac_requirements(self):
        policy = resolve_prepared_component_policy(model="JA-AD01A", region="EU", language="en")
        identities = [r["id"] for c in policy["chapters"] for r in c["requirements"]]
        self.assertFalse(any("APP/" in i or "AUTO-RESUME/" in i for i in identities))

    def test_unreviewed_debt_category_fails_closed(self):
        contract = json.loads((get_paths().renderer_contracts_dir / POLICY_FILENAME).read_text())
        contract["debt_reasons"] = {}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "policy.json"
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValueError, "unreviewed component debt category"):
                resolve_prepared_component_policy(model="JA-AD01A", region="EU", language="en", contract_path=path)

    def test_newly_enabled_capability_needs_chapter_review(self):
        from tools.check.docs_capability import load_capabilities
        capabilities = load_capabilities(get_paths().data_dir)
        capabilities["JE-3600A_EU"]["AC/DC输出记忆恢复"] = True
        with patch("tools.prepared_component_policy.load_capabilities", return_value=capabilities):
            with self.assertRaisesRegex(ValueError, "new capability has no reviewed chapter"):
                resolve_prepared_component_policy(model="JE-3600A", region="EU", language="en")
