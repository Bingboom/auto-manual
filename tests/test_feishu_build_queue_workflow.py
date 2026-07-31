from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "feishu-build-queue.yml"
PACKAGE_MANIFEST_PATH = REPO_ROOT / ".github" / "texlive-apt-packages.txt"
SMOKE_TEX_PATH = REPO_ROOT / ".github" / "texlive-cache-smoke.tex"


def _workflow_steps() -> list[dict[str, object]]:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return workflow["jobs"]["process-queue"]["steps"]


def _step_named(name: str) -> tuple[int, dict[str, object]]:
    for index, step in enumerate(_workflow_steps()):
        if step.get("name") == name:
            return index, step
    raise AssertionError(f"missing workflow step: {name}")


class FeishuBuildQueueWorkflowTests(unittest.TestCase):
    def test_workflow_yaml_parses_and_texlive_cache_precedes_install(self) -> None:
        cache_index, cache_step = _step_named("Cache XeLaTeX apt archives")
        install_index, install_step = _step_named("Install XeLaTeX runtime for publish PDF")
        process_index, _ = _step_named("Process Feishu build queue")

        self.assertLess(cache_index, install_index)
        self.assertLess(install_index, process_index)
        self.assertEqual("actions/cache@v4", cache_step["uses"])
        self.assertEqual("texlive-apt-cache", cache_step["id"])
        self.assertEqual("install-texlive", install_step["id"])

    def test_cache_key_is_bound_to_os_arch_and_package_manifest(self) -> None:
        _, cache_step = _step_named("Cache XeLaTeX apt archives")
        cache_with = cache_step["with"]
        self.assertEqual("${{ runner.temp }}/texlive-apt-cache", cache_with["path"])
        self.assertEqual(
            "texlive-apt-${{ runner.os }}-${{ runner.arch }}-"
            "${{ hashFiles('.github/texlive-apt-packages.txt') }}",
            cache_with["key"],
        )

    def test_install_uses_only_the_versioned_package_manifest_and_cache_dir(self) -> None:
        packages = [
            line.strip()
            for line in PACKAGE_MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(sorted(set(packages)), packages)
        self.assertIn("texlive-xetex", packages)
        self.assertIn("texlive-lang-cjk", packages)
        self.assertIn("fonts-noto-cjk", packages)

        _, install_step = _step_named("Install XeLaTeX runtime for publish PDF")
        script = str(install_step["run"])
        self.assertIn(".github/texlive-apt-packages.txt", script)
        self.assertIn('Dir::Cache::archives="${apt_cache}"', script)
        self.assertIn("APT::Keep-Downloaded-Packages=true", script)
        self.assertIn('"${texlive_packages[@]}"', script)
        self.assertIn('sudo chown -R "$(id -u):$(id -g)" "${apt_cache}"', script)

    def test_workflow_records_cache_hit_and_install_duration(self) -> None:
        install_index, _ = _step_named("Install XeLaTeX runtime for publish PDF")
        report_index, report_step = _step_named("Report XeLaTeX cache timing")
        self.assertLess(install_index, report_index)
        report = str(report_step["run"])
        self.assertIn("steps.texlive-apt-cache.outputs.cache-hit", report)
        self.assertIn("steps.install-texlive.outputs.elapsed-seconds", report)
        self.assertIn("GITHUB_STEP_SUMMARY", report)

    def test_smoke_dispatch_builds_pdf_without_consuming_queue(self) -> None:
        steps = _workflow_steps()
        smoke_index, smoke_step = _step_named("Build deterministic XeLaTeX cache smoke PDF")
        process_index, process_step = _step_named("Process Feishu build queue")

        self.assertTrue(SMOKE_TEX_PATH.is_file())
        self.assertLess(smoke_index, process_index)
        self.assertEqual("${{ inputs.texlive_smoke_only }}", smoke_step["if"])
        self.assertEqual("${{ !inputs.texlive_smoke_only }}", process_step["if"])
        self.assertIn("SOURCE_DATE_EPOCH", smoke_step["env"])
        self.assertIn("sha256sum texlive-cache-smoke.pdf", str(smoke_step["run"]))
        self.assertEqual(steps, _workflow_steps())


if __name__ == "__main__":
    unittest.main()
