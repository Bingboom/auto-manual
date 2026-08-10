from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.release_rebuild import load_release_rebuild_plan, verify_release_rebuild
from tools.release_snapshot import freeze_release_snapshot


class ReleaseRebuildTests(unittest.TestCase):
    def _release_fixture(
        self,
        root: Path,
        *,
        artifact_payloads: dict[str, bytes] | None = None,
    ) -> tuple[Path, dict[str, object], dict[str, bytes]]:
        config = root / "configs" / "config.us-en.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("build:\n  languages: [en]\n", encoding="utf-8")
        data_root = root / "data" / "phase2"
        shutil.copytree(Path(__file__).parent / "fixtures" / "phase2", data_root)
        snapshot_dir = (
            root
            / "reports"
            / "releases"
            / "M"
            / "US"
            / "en"
            / "versions"
            / "1.0"
            / "snapshot"
        )
        frozen = freeze_release_snapshot(
            cfg={},
            repo_root=root,
            data_root=data_root,
            model="M",
            region="US",
            languages=["en"],
            snapshot_dir=snapshot_dir,
        )
        payloads = artifact_payloads or {
            "word_output": b"stable-docx",
            "md_output": b"stable-markdown",
            "pdf_output": b"stable-pdf",
        }
        suffixes = {
            "word_output": ("word", ".docx"),
            "md_output": ("md", ".md"),
            "pdf_output": ("pdf", ".pdf"),
        }
        toolchain: dict[str, object] = {
            "schema_version": 1,
            "python": "fixture",
        }
        manifest: dict[str, object] = {
            "git_sha": "a" * 40,
            "config_path": "configs/config.us-en.yaml",
            "model": "M",
            "region": "US",
            "build_languages": ["en"],
            "release_version": "1.0",
            "toolchain": toolchain,
            "snapshot": {
                "path": snapshot_dir.relative_to(root).as_posix(),
                "identity_path": frozen.identity_path.relative_to(root).as_posix(),
                "snapshot_sha256": frozen.identity["snapshot_sha256"],
                "target_matrix": frozen.identity["target_matrix"],
            },
            "reproducibility": {
                "schema_version": 1,
                "policy": "git-commit-source-date-epoch-v1",
                "source_date_epoch": 1_785_513_828,
                "artifact_contract": "sha256-byte-equivalence",
                "artifacts": ["word_output", "md_output", "pdf_output"],
            },
        }
        for key, payload in payloads.items():
            directory, suffix = suffixes[key]
            manifest[key] = {
                "path": f"docs/_build/M/US/en/{directory}/manual{suffix}",
                "exists": True,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        manifest_path = root / "reports" / "releases" / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, toolchain, payloads

    def _runner(
        self,
        *,
        payloads: dict[str, bytes],
        snapshot_sha256: str,
        mismatched_key: str | None = None,
        review_overlay: dict[str, str] | None = None,
    ):
        def run(command, *, cwd, env=None, check, text):
            del cwd, env, check, text
            command = list(command)
            if command[:3] == ["git", "worktree", "add"]:
                checkout = Path(command[4])
                checkout.mkdir(parents=True)
                (checkout / "build.py").write_text("# fixture\n", encoding="utf-8")
            elif len(command) > 1 and Path(command[1]).name == "build.py":
                staging = Path(command[command.index("--staging-root") + 1])
                outputs: dict[str, dict[str, object]] = {}
                locations = {
                    "word_output": ("word", ".docx"),
                    "md_output": ("md", ".md"),
                    "pdf_output": ("pdf", ".pdf"),
                }
                for key, payload in payloads.items():
                    if key == mismatched_key:
                        payload += b"-drift"
                    directory, suffix = locations[key]
                    path = staging / "docs" / "_build" / "M" / "US" / "en" / directory / f"manual{suffix}"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(payload)
                    outputs[key] = {
                        "path": path.as_posix(),
                        "exists": True,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                reproducibility: dict[str, object] = {
                    "source_date_epoch": 1_785_513_828,
                }
                if review_overlay is not None:
                    reproducibility["review_overlay"] = review_overlay
                rebuilt = {
                    "git_sha": "a" * 40,
                    "snapshot": {"snapshot_sha256": snapshot_sha256},
                    "reproducibility": reproducibility,
                    **outputs,
                }
                rebuilt_path = (
                    staging
                    / "reports"
                    / "releases"
                    / "M"
                    / "US"
                    / "en"
                    / "manifests"
                    / "rebuilt.json"
                )
                rebuilt_path.parent.mkdir(parents=True, exist_ok=True)
                rebuilt_path.write_text(json.dumps(rebuilt), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)

        return run

    def test_plan_should_fail_closed_on_snapshot_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path, _toolchain, _payloads = self._release_fixture(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            snapshot_dir = root / manifest["snapshot"]["path"]
            (snapshot_dir / "Spec_Notes.csv").write_text("drift\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "drifted"):
                load_release_rebuild_plan(manifest_path, repo_root=root)

    def test_verify_should_rebuild_all_contract_artifacts_byte_for_byte(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path, toolchain, payloads = self._release_fixture(root)
            plan = load_release_rebuild_plan(manifest_path, repo_root=root)

            report_path, report = verify_release_rebuild(
                manifest_path,
                repo_root=root,
                runner=self._runner(
                    payloads=payloads,
                    snapshot_sha256=plan.snapshot_sha256,
                ),
                toolchain_collector=lambda **_kwargs: toolchain,
            )

            self.assertEqual("passed", report["status"])
            self.assertTrue(report_path.is_file())
            self.assertEqual(
                {"word_output", "md_output", "pdf_output"},
                set(report["artifacts"]),
            )
            self.assertTrue(
                all(record["matched"] for record in report["artifacts"].values())
            )

    def test_verify_should_write_failure_report_for_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path, toolchain, payloads = self._release_fixture(root)
            plan = load_release_rebuild_plan(manifest_path, repo_root=root)
            report_path = root / "reports" / "failed.json"

            with self.assertRaisesRegex(RuntimeError, "pdf_output"):
                verify_release_rebuild(
                    manifest_path,
                    report_path=report_path,
                    repo_root=root,
                    runner=self._runner(
                        payloads=payloads,
                        snapshot_sha256=plan.snapshot_sha256,
                        mismatched_key="pdf_output",
                    ),
                    toolchain_collector=lambda **_kwargs: toolchain,
                )

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual("failed", report["status"])
            self.assertFalse(report["artifacts"]["pdf_output"]["matched"])

    def test_verify_should_restore_recorded_review_overlay_before_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path, toolchain, payloads = self._release_fixture(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            review_overlay = {
                "source_ref": "review/M-US",
                "source_sha": "b" * 40,
                "target_path": "docs/_review/M/US",
                "tree_sha": "c" * 40,
            }
            manifest["reproducibility"]["review_overlay"] = review_overlay
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            plan = load_release_rebuild_plan(manifest_path, repo_root=root)
            calls: list[tuple[list[str], dict[str, str] | None]] = []
            base_runner = self._runner(
                payloads=payloads,
                snapshot_sha256=plan.snapshot_sha256,
                review_overlay=review_overlay,
            )

            def runner(command, *, cwd, env=None, check, text):
                calls.append((list(command), env))
                return base_runner(command, cwd=cwd, env=env, check=check, text=text)

            _report_path, report = verify_release_rebuild(
                manifest_path,
                repo_root=root,
                runner=runner,
                toolchain_collector=lambda **_kwargs: toolchain,
            )

            self.assertEqual(review_overlay, report["review_overlay"])
            self.assertTrue(
                any(
                    command[:3] == ["git", "restore", "--source"]
                    and command[3] == "b" * 40
                    for command, _env in calls
                )
            )
            publish_envs = [
                env
                for command, env in calls
                if len(command) > 1 and Path(command[1]).name == "build.py"
            ]
            self.assertEqual("b" * 40, publish_envs[0]["AUTO_MANUAL_REVIEW_OVERLAY_SHA"])


if __name__ == "__main__":
    unittest.main()
