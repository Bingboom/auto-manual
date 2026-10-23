from __future__ import annotations

import hashlib
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.test_helpers import temp_test_root, write_text
from tools.web import frozen_package_registry as fpr

SHARED = "docs/renderers/contracts/web_manual.css"
OTHER = "tools/web/stylesheets.py"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_package(root: Path, key: str, pins: dict[str, bytes] | None = None) -> None:
    manifest: dict = {"schema_version": "auto-manual-frozen-web-source/v1"}
    if pins:
        manifest["repo_inputs"] = [{"path": rel, "sha256": sha(data)} for rel, data in pins.items()]
    write_text(root / key / "source_manifest.json", json.dumps(manifest))


def registry_with(*keys: str) -> dict:
    registry = fpr.empty_registry()
    for key in keys:
        registry["packages"][key] = {"approval": "MA-001", "registered": "2026-10-19", "known_drift": {}}
    return registry


def run_check(root: Path, registry: dict) -> tuple[fpr.RegistryResult, str]:
    fpr.write_registry(fpr.frozen_package_registry_of(root), registry)
    lines: list[str] = []
    return fpr.check_repository(root, printer=lines.append), "\n".join(lines)


class FrozenPackageRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._root_cm = temp_test_root()
        self.root = self._root_cm.__enter__()
        self.addCleanup(self._root_cm.__exit__, None, None, None)
        write_text(self.root / SHARED, "a { color: red; }\n")
        write_text(self.root / OTHER, "VALUE = 1\n")
        self.pinned = "manual_sources/M-1/EU/en/git-1"
        self.unpinned = "data/manual_sources/M-2/US/en"
        write_package(self.root, self.pinned, {SHARED: b"a { color: red; }\n", OTHER: b"VALUE = 1\n"})
        write_package(self.root, self.unpinned)

    def test_registered_packages_pass_and_unpinned_ones_are_reported_unknown(self) -> None:
        result, output = run_check(self.root, registry_with(self.pinned, self.unpinned))

        self.assertEqual(0, result.exit_code)
        self.assertEqual((self.unpinned,), result.unpinned)
        self.assertIn("2 packages (1 pin shared inputs, 1 without pins: impact unknown)", output)

    def test_unregistered_and_vanished_packages_fail(self) -> None:
        result, output = run_check(self.root, registry_with(self.pinned, "manual_sources/GONE/EU/en"))

        self.assertEqual(1, result.exit_code)
        self.assertEqual((self.unpinned,), result.new_packages)
        self.assertEqual(("manual_sources/GONE/EU/en",), result.removed_packages)
        self.assertIn(f"NEW {self.unpinned}", output)
        self.assertIn("GONE manual_sources/GONE/EU/en", output)

    def test_unrecorded_drift_fails_until_its_handling_is_recorded(self) -> None:
        registry = registry_with(self.pinned, self.unpinned)
        write_text(self.root / SHARED, "a { color: blue; }\n")

        result, output = run_check(self.root, registry)
        self.assertEqual(1, result.exit_code)
        self.assertEqual({self.pinned: (SHARED,)}, result.new_drift)
        self.assertIn(f"DRIFT {self.pinned}", output)

        fpr.record(self.root, registry, handling="keep-frozen", reason="released bytes unchanged",
                   today="2026-10-20", minutes=15)
        result, _ = run_check(self.root, registry)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, result.known_drift)
        self.assertEqual({"handling": "keep-frozen", "reason": "released bytes unchanged", "since": "2026-10-20"},
                         registry["packages"][self.pinned]["known_drift"][SHARED])
        self.assertEqual([{"date": "2026-10-20", "files": [SHARED], "packages": 1, "handling": "keep-frozen",
                           "reason": "released bytes unchanged", "minutes": 15}], registry["drift_log"])

    def test_new_drift_cannot_be_recorded_without_handling_and_reason(self) -> None:
        registry = registry_with(self.pinned, self.unpinned)
        write_text(self.root / OTHER, "VALUE = 2\n")

        with self.assertRaisesRegex(ValueError, "--handling"):
            fpr.record(self.root, registry, handling=None, reason=None, today="2026-10-20")
        with self.assertRaisesRegex(ValueError, "--reason"):
            fpr.record(self.root, registry, handling="rebuild-pending", reason=" ", today="2026-10-20")
        with self.assertRaisesRegex(ValueError, "--minutes"):
            fpr.record(self.root, registry, handling="rebuild-pending", reason="next revision", today="2026-10-20")
        with self.assertRaisesRegex(ValueError, "--minutes"):
            fpr.record(self.root, registry, handling="rebuild-pending", reason="next revision", today="2026-10-20",
                       minutes=-5)
        fpr.record(self.root, registry, handling="rebuild-pending", reason="next revision", today="2026-10-20",
                   minutes=0)
        self.assertEqual(0, registry["drift_log"][-1]["minutes"])

    def test_drift_that_went_away_is_stale_and_record_drops_it(self) -> None:
        registry = registry_with(self.pinned, self.unpinned)
        registry["packages"][self.pinned]["known_drift"][OTHER] = {
            "handling": "rebuild-pending", "reason": "x", "since": "2026-10-19"}

        result, output = run_check(self.root, registry)
        self.assertEqual(1, result.exit_code)
        self.assertEqual({self.pinned: (OTHER,)}, result.stale_drift)
        self.assertIn(f"STALE {self.pinned}", output)

        fpr.record(self.root, registry, handling=None, reason=None, today="2026-10-20")
        result, _ = run_check(self.root, registry)
        self.assertEqual(0, result.exit_code)
        self.assertEqual([], registry["drift_log"])

    def test_missing_pinned_file_is_drift_but_a_crlf_copy_is_not(self) -> None:
        (self.root / OTHER).unlink()
        write_text(self.root / SHARED, "")
        (self.root / SHARED).write_bytes(b"a { color: red; }\r\n")

        result, _ = run_check(self.root, registry_with(self.pinned, self.unpinned))

        self.assertEqual({self.pinned: (OTHER,)}, result.new_drift)

    def test_invalid_entries_fail(self) -> None:
        registry = registry_with(self.pinned, self.unpinned)
        registry["packages"][self.unpinned]["approval"] = " "
        registry["packages"][self.pinned]["known_drift"][SHARED] = {"handling": "ignore", "reason": "x"}

        result, output = run_check(self.root, registry)

        self.assertEqual(1, result.exit_code)
        self.assertEqual(2, len(result.invalid))
        self.assertIn("needs a non-empty approval reference", output)
        self.assertIn("handling must be one of keep-frozen, rebuild-pending", output)

    def test_missing_registry_is_an_error(self) -> None:
        lines: list[str] = []
        result = fpr.check_repository(self.root, printer=lines.append)

        self.assertEqual(2, result.exit_code)
        self.assertIn("missing registry", lines[0])

    def test_register_needs_a_package_and_an_approval_and_unregister_needs_it_gone(self) -> None:
        registry = registry_with(self.pinned)

        with self.assertRaisesRegex(ValueError, "approval"):
            fpr.register(self.root, registry, [self.unpinned], " ", "2026-10-20")
        with self.assertRaisesRegex(ValueError, "no source_manifest.json"):
            fpr.register(self.root, registry, ["manual_sources/NOPE"], "MA-002", "2026-10-20")
        with self.assertRaisesRegex(ValueError, "already registered"):
            fpr.register(self.root, registry, [self.pinned], "MA-002", "2026-10-20")
        added = fpr.register(self.root, registry, [f"{self.unpinned}/source_manifest.json"], "MA-002", "2026-10-20")
        self.assertEqual([self.unpinned], added)
        self.assertEqual("MA-002", registry["packages"][self.unpinned]["approval"])
        with self.assertRaisesRegex(ValueError, "still in the checkout"):
            fpr.unregister(self.root, registry, [self.pinned])

    def test_affected_packages_lists_who_pins_a_changed_file(self) -> None:
        self.assertEqual({self.pinned: (SHARED,)}, fpr.affected_packages(self.root, [SHARED, "README.md"]))
        self.assertEqual({}, fpr.affected_packages(self.root, ["README.md"]))

    def test_cli_register_and_record_write_the_registry(self) -> None:
        fpr.write_registry(fpr.frozen_package_registry_of(self.root), registry_with(self.pinned))
        write_text(self.root / SHARED, "changed\n")

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(0, fpr.main(["--repo-root", str(self.root), "register", self.unpinned,
                                          "--approval", "MA-003", "--date", "2026-10-20"]))
            self.assertEqual(2, fpr.main(["--repo-root", str(self.root), "record"]))
            self.assertEqual(2, fpr.main(["--repo-root", str(self.root), "record", "--handling", "keep-frozen",
                                          "--reason", "frozen release", "--date", "2026-10-20"]))
            self.assertEqual(0, fpr.main(["--repo-root", str(self.root), "record", "--handling", "keep-frozen",
                                          "--reason", "frozen release", "--minutes", "0", "--date", "2026-10-20"]))
            self.assertEqual(0, fpr.main(["--repo-root", str(self.root), "check"]))

        saved = json.loads(fpr.frozen_package_registry_of(self.root).read_text(encoding="utf-8"))
        self.assertEqual(["data/manual_sources/M-2/US/en", self.pinned], list(saved["packages"]))
        self.assertEqual(1, saved["drift_log"][0]["packages"])


if __name__ == "__main__":
    unittest.main()
