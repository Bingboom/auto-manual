"""Explorer 300 and 880 Pro US English Git-only Web candidates (outlined-PDF transcriptions).

JE-300E, JE-300E-SG, JE-300C and JE-880B: source identity, input inventory,
candidate status, shared-style admission, shared symbol bytes and cold replay.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.manual_ir.hashing import file_sha256
from tools.utils.path_utils import PathSegments
from tools.web.prepared_style_audit import require_prepared_style_admission

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "JE-300E": "manual_sources/JE-300E/US/en/git-20261027-04bd8b90",
    "JE-300E-SG": "manual_sources/JE-300E-SG/US/en/git-20261027-e47cb322",
    "JE-300C": "manual_sources/JE-300C/US/en/git-20261027-a1128b25",
    "JE-880B": "manual_sources/JE-880B/US/en/git-20261027-640e83ca",
}
CANDIDATE = "review-candidate-no-release-authorization"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def drifted(package: Path) -> list[str]:
    return [row["path"] for row in read(package / "source_manifest.json")["repo_inputs"]
            if not (ROOT / row["path"]).is_file() or file_sha256(ROOT / row["path"]) != row["sha256"]]


def tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): file_sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


class Explorer300UsEnWebTests(unittest.TestCase):
    def packages(self):
        for model, relative in PACKAGES.items():
            package = ROOT / relative
            if not package.is_dir():
                self.fail(f"{model}: package missing at {relative}")
            yield model, package

    def test_source_identity_and_inventory(self):
        for model, package in self.packages():
            with self.subTest(model=model):
                manifest = read(package / "source_manifest.json")
                self.assertEqual(manifest["target"]["model"], model)
                self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
                self.assertEqual(manifest["target"]["technical_version"], package.name)
                original = manifest["original_source"]
                digest = hashlib.sha256((package / original["filename"]).read_bytes()).hexdigest()
                self.assertEqual(digest, original["sha256"])
                self.assertTrue(package.name.endswith("-" + digest[:8]))
                self.assertEqual(read(package / "source/en/content.json")["source_sha256"], digest)
                self.assertEqual(manifest["route"], f"{model}/US/en/md")
                self.assertIs(manifest["legacy_default"], True)
                files = sorted(p for p in tree(package) if p != "source_manifest.json" and "__pycache__" not in p)
                self.assertEqual(sorted(row["path"] for row in manifest["inputs"]), files)
                # Feishu file tokens never enter the package.
                text = (package / "source_manifest.json").read_text(encoding="utf-8")
                self.assertNotIn("file_token", text)

    def test_candidates_carry_no_release_acceptance(self):
        for model, package in self.packages():
            with self.subTest(model=model):
                manifest = read(package / "source_manifest.json")
                metadata = read(package / "web/en" / PathSegments.MANUAL_IR_JSON)["metadata"]
                if manifest["publication_status"] == CANDIDATE:
                    self.assertFalse((package / "source/approval.json").exists())
                    self.assertIs(metadata["publication_eligible"], False)
                else:
                    self.assertIs(metadata["publication_eligible"], True)
                    self.assertEqual(metadata["operator_source_acceptance"], read(package / "source/approval.json"))

    def test_shared_style_admission(self):
        for model, package in self.packages():
            with self.subTest(model=model):
                manifest = read(package / "source_manifest.json")
                report = require_prepared_style_admission(package / "web/en", manifest)
                self.assertEqual(report["issues"], [])

    def test_shared_symbols_are_byte_identical(self):
        for model, package in self.packages():
            with self.subTest(model=model):
                for row in read(package / "source/symbols.json"):
                    if row.get("shared_path"):
                        self.assertEqual(file_sha256(package / row["local_path"]), file_sha256(ROOT / row["shared_path"]))

    def test_cold_replay_matches_the_frozen_web_tree(self):
        for model, package in self.packages():
            with self.subTest(model=model):
                if drifted(package):
                    self.skipTest(f"{model}: shared inputs changed since this candidate was frozen")
                module = load(f"rebuild_{model.replace('-', '_')}", package / "rebuild.py")
                with tempfile.TemporaryDirectory() as temp:
                    output = Path(temp) / "en"
                    with redirect_stdout(io.StringIO()):
                        module.rebuild(output)
                    self.assertEqual(tree(output), tree(package / "web/en"))


if __name__ == "__main__":
    unittest.main()
