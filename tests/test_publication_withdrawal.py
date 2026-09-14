from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tests import test_publish_branch_assembly
from tools import publication_withdrawal as actions
from tools import publish_branch_assembly as assembly


class PublicationWithdrawalTests(unittest.TestCase):
    _write_target = test_publish_branch_assembly.PublishBranchAssemblyTests._write_target

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "publish"
        for model, lang, default in (("M", "en", True), ("M", "fr", False), ("OTHER", "en", True)):
            self._write_target(self.root, model=model, region="EU", lang=lang, version="1.0",
                               git_ref="a" * 40, legacy_default=default, language_scope="single")
        self.assemble()
        self.snapshot = self.root / "cold-snapshot"
        shutil.copytree(self.output, self.snapshot)

    def assemble(self):
        return assembly.assemble_web_publish_branch(repo_root=self.root,
            releases_root=self.root / "reports/releases", output_dir=self.output, title="Manuals")

    def change(self, action="withdraw", **kwargs):
        arguments = dict(output_dir=self.output, action=action, model="M", region="EU", lang="en",
                         version="1.0", reason="Controlled local drill", operator="Test operator",
                         before_ref="a" * 40 if action == "withdraw" else "b" * 40,
                         restore_ref="a" * 40,
                         expected_manifest_sha256=actions.manifest_sha256(self.output))
        arguments.update(kwargs)
        return actions.change_publication_state(**arguments)

    @staticmethod
    def inventory(root):
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def test_withdraw_restore_preserves_other_model_and_explicitly_moves_default(self):
        other = self.inventory(self.output / "sources/web/OTHER")
        french = (self.output / "sources/web/M/EU/fr/md/manual_m_eu_fr_web_publish_1.0.md").read_bytes()
        receipt = self.change(default_language="fr")
        self.assertIsNone(receipt["candidate_ref"])
        self.assertIsNone(receipt["deployed_ref"])
        self.assertEqual("a" * 40, receipt["event"]["restore_ref"])
        self.assertIsNone(receipt["event"]["new_route"])
        self.assertEqual(other, self.inventory(self.output / "sources/web/OTHER"))
        self.assertFalse((self.output / "sources/web/M/EU/en/md").exists())
        notice = self.output / "web/M/EU/en/md/manual_m_eu_en_web_publish_1.0.md"
        self.assertIn("Publication withdrawn", notice.read_text())
        self.assertNotIn("M/EU/en/md/manual", (self.output / "web/index.md").read_text())
        self.assertEqual(french, (self.output / "sources/web/M/EU/fr/md/manual_m_eu_fr_web_publish_1.0.md").read_bytes())
        self.change("restore", restore_snapshot=self.snapshot, default_language="en")
        self.assertEqual(self.inventory(self.snapshot / "sources/web/M/EU/en"),
                         self.inventory(self.output / "sources/web/M/EU/en"))
        before_content = {k: v for k, v in self.inventory(self.snapshot / "sources/web").items()
                          if not k.endswith("publish_meta.json")}
        after_content = {k: v for k, v in self.inventory(self.output / "sources/web").items()
                         if not k.endswith("publish_meta.json")}
        self.assertEqual(before_content, after_content)
        self.assertNotIn("Publication withdrawn", notice.read_text())
        self.assertEqual(["withdraw", "restore"], [e["action"] for e in actions.publication_actions(self.output)])
        self.assemble()  # The explicit restore, not an ordinary retry, releases the block.

    def test_normal_assembly_cannot_reintroduce_withdrawn_version(self):
        self.change(default_language="fr")
        before = self.inventory(self.output)
        with self.assertRaisesRegex(RuntimeError, "explicit restoration"):
            self.assemble()
        self.assertEqual(before, self.inventory(self.output))

    def test_nondefault_withdrawal_preserves_sibling_bytes_and_short_alias_notice(self):
        english = self.inventory(self.output / "sources/web/M/EU/en")
        self.change(lang="fr")
        self.assertEqual(english, self.inventory(self.output / "sources/web/M/EU/en"))
        alias = self.output / "web/manual_m_eu_fr_web_publish_1.0.md"
        self.assertIn("Publication withdrawn", alias.read_text())

    def test_default_change_version_and_manifest_preconditions_fail_atomically(self):
        before = self.inventory(self.output)
        for kwargs, message in (({}, "default_language"), ({"version": "9.0"}, "currently published"),
                                ({"expected_manifest_sha256": "0" * 64}, "manifest changed")):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(RuntimeError, message):
                self.change(**kwargs)
            self.assertEqual(before, self.inventory(self.output))

    def test_wrong_restore_ref_or_drifted_cold_snapshot_fails_atomically(self):
        self.change(default_language="fr")
        before = self.inventory(self.output)
        with self.assertRaisesRegex(RuntimeError, "pinned snapshot"):
            self.change("restore", restore_snapshot=self.snapshot, restore_ref="c" * 40)
        target = self.snapshot / "sources/web/M/EU/en/md/assets/demo.png"
        target.write_bytes(b"modified asset")
        with self.assertRaises(RuntimeError):
            self.change("restore", restore_snapshot=self.snapshot, default_language="en")
        self.assertEqual(before, self.inventory(self.output))

    def test_rebuild_failure_leaves_original_bytes_and_ledger_unchanged(self):
        before = self.inventory(self.output)
        with patch.object(assembly, "rebuild_web_source", side_effect=RuntimeError("injected rebuild failure")):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                self.change(default_language="fr")
        self.assertEqual(before, self.inventory(self.output))

    def test_other_version_may_publish_but_withdrawn_version_stays_blocked(self):
        self.change(default_language="fr")
        self._write_target(self.root, model="M", region="EU", lang="en", version="2.0",
                           git_ref="c" * 40, legacy_default=False, language_scope="single")
        # The ordinary staging contract correctly refuses a stale pointer
        # that would clear the explicitly selected French default.
        french_pointer = self.root / "reports/releases/M/EU/fr/latest/web/publish_meta.json"
        payload = json.loads(french_pointer.read_text())
        payload["legacy_default"] = True
        french_pointer.write_text(json.dumps(payload))
        self.assemble()
        actions.reject_withdrawn_version(self.output, model="M", region="EU", lang="en", version="2.0")
        with self.assertRaisesRegex(RuntimeError, "explicit restoration"):
            actions.reject_withdrawn_version(self.output, model="M", region="EU", lang="en", version="1.0")

    def test_malformed_ledger_rejected_before_reentry(self):
        self.change(default_language="fr")
        ledger = self.output / "sources/publication_actions.json"
        payload = json.loads(ledger.read_text())
        payload["actions"][0]["notice_routes"] = ["../escape.md"]
        ledger.write_text(json.dumps(payload))
        with self.assertRaisesRegex(RuntimeError, "invalid publication action ledger"):
            self.assemble()

    def test_restore_without_withdrawal_and_unsafe_target_are_rejected(self):
        for kwargs in ({"action": "restore", "restore_snapshot": self.snapshot}, {"model": "../M"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(RuntimeError):
                self.change(**kwargs)
