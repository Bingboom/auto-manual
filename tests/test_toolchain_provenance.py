from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools import toolchain_provenance


class TestCommandVersion(unittest.TestCase):
    def test_missing_binary_records_none(self) -> None:
        self.assertIsNone(
            toolchain_provenance.command_version("xelatex", which=lambda _: None)
        )

    def test_first_line_of_version_output_wins(self) -> None:
        def fake_run(cmd, **kwargs):
            return SimpleNamespace(stdout="XeTeX 3.141592653\nkpathsea ...\n", stderr="")

        version = toolchain_provenance.command_version(
            "xelatex", which=lambda _: "/usr/bin/xelatex", run=fake_run
        )
        self.assertEqual(version, "XeTeX 3.141592653")

    def test_stderr_only_output_is_used(self) -> None:
        def fake_run(cmd, **kwargs):
            return SimpleNamespace(stdout="", stderr="tool 1.2.3\n")

        version = toolchain_provenance.command_version(
            "tool", which=lambda _: "/usr/bin/tool", run=fake_run
        )
        self.assertEqual(version, "tool 1.2.3")

    def test_broken_binary_records_unknown(self) -> None:
        def raising_run(cmd, **kwargs):
            raise OSError("boom")

        version = toolchain_provenance.command_version(
            "tool", which=lambda _: "/usr/bin/tool", run=raising_run
        )
        self.assertEqual(version, "unknown")


class TestPackageVersions(unittest.TestCase):
    def test_known_and_missing_packages(self) -> None:
        versions = toolchain_provenance.package_versions(("PyYAML", "definitely-not-installed-xyz"))
        self.assertIsNotNone(versions["PyYAML"])
        self.assertIsNone(versions["definitely-not-installed-xyz"])


class TestInDesignVersion(unittest.TestCase):
    def test_non_darwin_records_none(self) -> None:
        self.assertIsNone(toolchain_provenance.indesign_version(platform="linux"))

    def test_darwin_without_app_records_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(
                toolchain_provenance.indesign_version(
                    applications_root=Path(tmp), platform="darwin"
                )
            )

    def test_darwin_reads_newest_bundle_version(self) -> None:
        import plistlib

        with tempfile.TemporaryDirectory() as tmp:
            for year, version in (("2024", "19.5"), ("2026", "21.0")):
                contents = (
                    Path(tmp)
                    / f"Adobe InDesign {year}"
                    / f"Adobe InDesign {year}.app"
                    / "Contents"
                )
                contents.mkdir(parents=True)
                with (contents / "Info.plist").open("wb") as handle:
                    plistlib.dump({"CFBundleShortVersionString": version}, handle)
            result = toolchain_provenance.indesign_version(
                applications_root=Path(tmp), platform="darwin"
            )
        self.assertEqual(result, "Adobe InDesign 2026 21.0")


class TestCollectAndRender(unittest.TestCase):
    def test_collect_shape_and_lock_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / toolchain_provenance.LOCK_FILENAME).write_text("a==1\n", encoding="utf-8")
            toolchain = toolchain_provenance.collect_toolchain(
                repo_root=root, which=lambda _: None, platform="linux"
            )
        self.assertEqual(toolchain["schema_version"], 1)
        self.assertIn("python", toolchain)
        self.assertIsNone(toolchain["xelatex"])
        self.assertIsNone(toolchain["indesign"])
        self.assertIsNotNone(toolchain["requirements_lock"]["sha256"])

    def test_collect_without_lock_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            toolchain = toolchain_provenance.collect_toolchain(
                repo_root=Path(tmp), which=lambda _: None, platform="linux"
            )
        self.assertIsNone(toolchain["requirements_lock"]["sha256"])

    def test_render_summary_mentions_missing_tools_and_lock(self) -> None:
        lines = toolchain_provenance.render_summary_lines(
            {
                "python": "CPython 3.12.0",
                "platform": "test",
                "packages": {"sphinx": "7.1.2", "numpy": None},
                "xelatex": None,
                "pandoc": "pandoc 3.9",
                "indesign": None,
                "requirements_lock": {"path": "requirements.lock", "sha256": None},
            }
        )
        text = "\n".join(lines)
        self.assertIn("xelatex: not found", text)
        self.assertIn("pandoc 3.9", text)
        self.assertIn("numpy missing", text)
        self.assertIn("requirements.lock: absent", text)


if __name__ == "__main__":
    unittest.main()
