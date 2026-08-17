"""Expose the version-controlled Wukong bridge contract tests to repo CI."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


BRIDGE_DIR = Path(__file__).resolve().parents[1] / "agent" / "wukong-bridge"
BRIDGE_TEST_FILE = BRIDGE_DIR / "test_intake_contract.py"


def load_tests(loader, _tests, _pattern):
    """Load the bridge-local suite while keeping runtime files together."""
    sys.path.insert(0, str(BRIDGE_DIR))
    spec = importlib.util.spec_from_file_location(
        "_wukong_bridge_contract_tests", BRIDGE_TEST_FILE
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Wukong bridge tests from {BRIDGE_TEST_FILE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return loader.loadTestsFromModule(module)
