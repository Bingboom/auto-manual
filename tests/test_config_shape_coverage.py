from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import build_docs
from tools.config_loader import load_config_mapping


ROOT = Path(__file__).resolve().parents[1]
CONFIGS_DIR = ROOT / "configs"


def _config_paths(configs_dir: Path = CONFIGS_DIR) -> tuple[Path, ...]:
    return tuple(sorted(configs_dir.glob("config*.yaml")))


def _load_and_resolve_target(config_path: Path) -> build_docs.BuildTarget:
    cfg = load_config_mapping(config_path)
    targets = build_docs.resolve_build_targets(
        cfg,
        arg_model=None,
        arg_region=None,
        arg_lang=None,
        all_targets=True,
    )
    if len(targets) != 1:
        raise RuntimeError(f"Expected one configured target for {config_path.name}, got {targets!r}")

    target = targets[0]
    if not target.model or not target.region:
        raise RuntimeError(f"Config {config_path.name} resolved an incomplete target: {target!r}")
    return target


class TestConfigShapeCoverage(unittest.TestCase):
    def test_every_config_loads_and_resolves_one_target(self) -> None:
        config_paths = _config_paths()
        self.assertGreater(len(config_paths), 0)

        resolved_paths: list[Path] = []
        for config_path in config_paths:
            with self.subTest(config=config_path.name):
                target = _load_and_resolve_target(config_path)
                self.assertTrue(target.model)
                self.assertTrue(target.region)
                resolved_paths.append(config_path)

        self.assertEqual(config_paths, tuple(resolved_paths))

    def test_bad_config_injection_fails_target_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad_config = Path(td) / "config.injected-bad.yaml"
            bad_config.write_text(
                "build:\n"
                "  default_model: JE-1000F\n"
                "  default_region: US\n"
                "  targets: not-a-list\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, r"build\.targets must be a list"):
                _load_and_resolve_target(bad_config)


if __name__ == "__main__":
    unittest.main()
