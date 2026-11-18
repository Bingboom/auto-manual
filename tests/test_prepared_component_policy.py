"""Trusted enrollment is independent of candidate headings and inventories."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.prepared_component_policy import POLICY_FILENAME, resolve_prepared_component_policy
from tools.utils.path_utils import get_paths


class PreparedPolicyTests(unittest.TestCase):
    def test_native_english_warranty_cannot_replace_year_cards_with_plain_sections(self):
        from copy import deepcopy
        from tools.prepared_component_coverage import audit_prepared_component_coverage

        reviewed_sources = {
            "JE-100A": ("dc3deaa0ae9354f22561f5012d0393cd062d323db55d1a34de903e464f0590be", 4),
            "JE-1500B": ("fb1999ca77c8f33b9f4289f85516f016f3423b34009565da58576d45cdf1d30b", 4),
            "JE-1000B": ("3d3811235b31549a715692644c0494be3d512ab42384b460fbc4c8346a03566d", 4),
            "JE-1000C": ("01e7d65a118edfa03ed891225f774f43d87109019a8dbc37bc206a6ba6f1e7a8", 4),
            "JE-2000C": ("62883ec1eddc0adeadeb0db2dc3d520898cae233c4be32ca1364db650ace396e", 4),
            "JE-2000D": ("c03fa2906129cd5ad0f162e0291775d5a1a974b68c42d249e9f78e7738e81aec", 5),
            "JE-3000B": ("dd37870b3953283aef6d8860f755bd095720f0257ea3f3738b8f3ff44ceaf68d", 5),
        }
        for model, (source_sha256, section_count) in reviewed_sources.items():
            with self.subTest(model=model):
                policy = resolve_prepared_component_policy(
                    model=model, region="EU", language="en", source_sha256=source_sha256,
                )
                warranty = next(c for c in policy["chapters"] if c["id"] == "warranty")
                # Isolate the warranty rule while exercising the production coverage audit.
                policy = {
                    **policy, "chapters": [warranty], "expected_pages": ["warranty"],
                    "expected_slots": {"warranty": policy["expected_slots"]["warranty"]},
                    "legacy_debt": [],
                }
                identities = ["HB-WARRANTY-SECTION/rounded-card"] * section_count
                identities.append("HB-WARRANTY-YEARS/numeric-badges")
                if model == "JE-3000B":
                    identities.append("HB-CALLOUT-STRIP/note")
                blocks = [
                    {"payload": {"kind": "component", "component_spec": {
                        "component_id": identity.split("/", 1)[0],
                        "variant": identity.split("/", 1)[1],
                    }}} for identity in identities
                ]
                raw = {
                    **policy["target"], "source": "prepared-document",
                    "metadata": {
                        "projection": "whole-document-components/v1",
                        "page_slots": policy["expected_slots"],
                        "component_inventory": {"HB-WARRANTY-YEARS": 1},
                    },
                    "pages": [{"page_id": "warranty", "blocks": blocks}],
                }
                self.assertEqual(audit_prepared_component_coverage(raw, policy)["issues"], [])
                plain_period = deepcopy(raw)
                year_card = plain_period["pages"][0]["blocks"][section_count]
                year_card["payload"]["component_spec"] = {
                    "component_id": "HB-WARRANTY-SECTION", "variant": "rounded-card",
                }
                # Extra generic sections and an unchanged self-reported inventory
                # must not admit the missing shared year-card presentation.
                issues = audit_prepared_component_coverage(plain_period, policy)["issues"]
                self.assertTrue(any("HB-WARRANTY-YEARS" in issue for issue in issues), issues)

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
        self.assertEqual(len(contract["targets"]), 83)
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
