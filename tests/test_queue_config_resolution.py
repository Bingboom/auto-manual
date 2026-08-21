from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.queue_config_resolution import resolve_config_path_for_task

US_HOST_CONFIG = """
build:
  family_id: us-merged
  languages: [en, fr, es]
  include_lang_in_output_path: false
  queue_by_document_key: true
  default_region: US
"""

BP_CONFIG = """
build:
  family_id: bp-us
  queue_requires_build_family: true
  languages: [en, fr, es]
  include_lang_in_output_path: false
  queue_by_document_key: true
  default_region: US
"""


class QueueConfigResolutionGuardTests(unittest.TestCase):
    """P0 guard from the 2026-08-21 operator review: an opt-in-only family
    must never win a plain queue row. Without the guard the filename
    heuristics score config.bp-us.yaml above config.us.yaml (105:104)."""

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
