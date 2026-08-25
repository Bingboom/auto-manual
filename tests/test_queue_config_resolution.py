from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.queue_config_resolution import resolve_config_path_for_task

US_HOST_CONFIG = """
build:
  family_id: us-merged
  language_family: us-merged
  languages: [en, fr, es]
  include_lang_in_output_path: false
  queue_by_document_key: true
  default_model: JE-1000F
  default_region: US
  targets:
    - model: JE-1000F
      region: US
"""

BP_CONFIG = """
build:
  family_id: bp-us
  language_family: us-merged
  queue_requires_target_match: true
  languages: [en, fr, es]
  include_lang_in_output_path: false
  queue_by_document_key: true
  default_model: JBP-2000B
  default_region: US
  targets:
    - model: JBP-2000B
      region: US
"""


class QueueConfigResolutionGuardTests(unittest.TestCase):
    """A target-specific skeleton may share a row language family safely."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmp.name)
        configs = self.repo_root / "configs"
        configs.mkdir()
        (configs / "config.us.yaml").write_text(US_HOST_CONFIG, encoding="utf-8")
        (configs / "config.bp-us.yaml").write_text(BP_CONFIG, encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    @staticmethod
    def _loader(path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def test_plain_us_row_still_resolves_to_the_host_config(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            region="US",
            lang=None,
            build_family=None,
            config_loader=self._loader,
        )
        self.assertEqual("config.us.yaml", resolved.name)

    def test_plain_us_row_with_lang_still_resolves_to_the_host_config(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            region="US",
            lang="en",
            build_family=None,
            config_loader=self._loader,
        )
        self.assertEqual("config.us.yaml", resolved.name)

    def test_jbp_draft_resolves_bp_config_from_target_and_language_family(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            model="JBP-2000B",
            region="US",
            lang=None,
            build_family="us-merged",
            workflow_action="draft",
            config_loader=self._loader,
        )
        self.assertEqual("config.bp-us.yaml", resolved.name)

    def test_jbp_publish_resolves_bp_config_from_target_and_language_family(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            model="JBP-2000B",
            region="US",
            lang=None,
            build_family="us-merged",
            workflow_action="publish",
            config_loader=self._loader,
        )
        self.assertEqual("config.bp-us.yaml", resolved.name)

    def test_host_target_keeps_host_config_for_shared_language_family(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            model="JE-1000F",
            region="US",
            lang=None,
            build_family="us-merged",
            workflow_action="draft",
            config_loader=self._loader,
        )
        self.assertEqual("config.us.yaml", resolved.name)

    def test_unregistered_host_target_uses_generic_host_fallback(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            model="JE-1000H",
            region="US",
            lang=None,
            build_family="us-merged",
            workflow_action="draft",
            config_loader=self._loader,
        )
        self.assertEqual("config.us.yaml", resolved.name)

    def test_jbp_without_build_family_uses_exact_target_config(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            model="JBP-2000B",
            region="US",
            lang=None,
            build_family=None,
            workflow_action="draft",
            config_loader=self._loader,
        )
        self.assertEqual("config.bp-us.yaml", resolved.name)

    def test_jbp_rejects_language_family_not_supported_by_its_target_config(self) -> None:
        config_path = self.repo_root / "configs" / "config.us-en.yaml"
        config_path.write_text(
            """
build:
  family_id: us-en
  languages: [en]
  include_lang_in_output_path: true
  default_model: JE-1000F
  default_region: US
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "does not support Build_family='us-en'"):
            resolve_config_path_for_task(
                repo_root=self.repo_root,
                model="JBP-2000B",
                region="US",
                lang="en",
                build_family="us-en",
                workflow_action="draft",
                config_loader=self._loader,
            )

    def test_explicit_build_family_resolves_to_the_bp_config(self) -> None:
        resolved = resolve_config_path_for_task(
            repo_root=self.repo_root,
            region="US",
            lang=None,
            build_family="bp-us",
            config_loader=self._loader,
        )
        self.assertEqual("config.bp-us.yaml", resolved.name)


if __name__ == "__main__":
    unittest.main()
