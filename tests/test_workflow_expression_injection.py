# -*- coding: utf-8 -*-
"""Guard against script injection through ``${{ }}`` in workflow shell code.

GitHub expands ``${{ }}`` into the script text before the shell parses it, so
an untrusted value (dispatch inputs, ``github.event.*``, branch names) inside a
``run:`` block or an ``actions/github-script`` ``script:`` can execute as code.
Untrusted values must reach the script through the step's ``env:`` instead.
This guard is default-deny: every expression inside shell or inline code must
be on the trusted list below.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"
VALIDATOR = REPO_ROOT / "scripts" / "validate_dispatch_inputs.sh"
PYTHON_RECORD_ID_SOURCE = REPO_ROOT / "tools" / "publish_locale_identity.py"

_EXPRESSION = re.compile(r"\$\{\{\s*(.*?)\s*\}\}", re.DOTALL)

_STRING_LITERAL = re.compile(r"'(?:[^']|'')*'")
_CONTEXT_REFERENCE = re.compile(
    r"\b(?:github|inputs|steps|env|vars|secrets|runner|job|jobs|matrix|needs|strategy)"
    r"(?:\.[A-Za-z0-9_-]+|\[[^\]]*\])*"
)

# Values set by GitHub, the runner or repository administrators, never by
# whoever dispatches or triggers the run.
_TRUSTED_REFERENCES = {
    "github.sha",
    "github.run_id",
    "github.run_number",
    "github.run_attempt",
    "github.repository",
    "github.repository_owner",
    "github.workspace",
    "github.server_url",
    "github.token",
    "job.status",
}
# `env.*` is deliberately absent: an env value may itself come from an input.
_TRUSTED_PREFIXES = ("runner.", "vars.", "secrets.")
# Step outputs the workflow computes itself from trusted data only.
_TRUSTED_STEP_OUTPUTS = {
    # actions/cache hit flag, `date +%s` arithmetic and `sha256sum` output.
    "steps.texlive-apt-cache.outputs.cache-hit",
    "steps.install-texlive.outputs.elapsed-seconds",
    "steps.texlive-smoke.outputs.pdf-sha256",
    # "${RUNNER_TEMP}/hello-docs-publish".
    "steps.publish-tree.outputs.path",
}


def _references(expression: str) -> list[str]:
    return _CONTEXT_REFERENCE.findall(_STRING_LITERAL.sub("''", expression))


def _is_trusted_reference(reference: str) -> bool:
    return (
        reference in _TRUSTED_REFERENCES
        or reference in _TRUSTED_STEP_OUTPUTS
        or reference.startswith(_TRUSTED_PREFIXES)
    )


def _is_trusted(expression: str) -> bool:
    """Every context the expression reads must be trusted (literals are fine)."""
    return all(_is_trusted_reference(ref) for ref in _references(expression))


def _definition_files() -> list[Path]:
    return sorted(WORKFLOWS_DIR.glob("*.y*ml")) + sorted(ACTIONS_DIR.glob("**/action.y*ml"))


def _steps(document: dict) -> list[tuple[str, dict]]:
    if "jobs" in document:
        return [
            (job_id, step)
            for job_id, job in (document["jobs"] or {}).items()
            for step in (job.get("steps") or [])
        ]
    runs = document.get("runs") or {}
    return [("composite", step) for step in (runs.get("steps") or [])]


def _code_blocks(step: dict) -> list[tuple[str, str]]:
    blocks = []
    if "run" in step:
        blocks.append(("run", str(step["run"])))
    uses = str(step.get("uses") or "")
    script = (step.get("with") or {}).get("script")
    if uses.startswith("actions/github-script") and script is not None:
        blocks.append(("script", str(script)))
    return blocks


def scan_code_expressions() -> list[tuple[str, str, str, str]]:
    """Return (file, step, block kind, expression) for every ``${{ }}`` in code."""
    found = []
    for path in _definition_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for job_id, step in _steps(document):
            label = f"{job_id}: {step.get('name') or step.get('id') or step.get('uses')}"
            for kind, code in _code_blocks(step):
                for match in _EXPRESSION.finditer(code):
                    rel = path.relative_to(REPO_ROOT).as_posix()
                    found.append((rel, label, kind, match.group(1)))
    return found


class TestWorkflowExpressionInjection(unittest.TestCase):
    def test_definition_files_are_scanned(self) -> None:
        names = {path.name for path in _definition_files()}
        self.assertIn("feishu-web-publish-queue.yml", names)
        self.assertIn("web-publish-receipt.yml", names)
        self.assertIn("action.yml", names)

    def test_no_untrusted_expression_inside_shell_or_inline_code(self) -> None:
        offenders = [item for item in scan_code_expressions() if not _is_trusted(item[3])]
        self.assertEqual(
            [],
            offenders,
            "move these values into the step's env: and reference them as quoted "
            "shell variables (or process.env / os.environ in inline code)",
        )

    def test_trusted_step_output_allowlist_is_not_stale(self) -> None:
        used = {ref for item in scan_code_expressions() for ref in _references(item[3])}
        self.assertEqual(set(), _TRUSTED_STEP_OUTPUTS - used)

    def test_classifier_rejects_known_injection_sources(self) -> None:
        for expression in (
            "inputs.queue_record_id",
            "inputs.queue_record_ids || ''",
            "github.event.repository.default_branch",
            "github.event.client_payload.record_id",
            "github.head_ref",
            "github.event.pull_request.title",
            "steps.anything.outputs.value",
            "vars.FLAG || inputs.limit",
            "inputs['deploy-timeout-seconds']",
            "env.AUTO_MANUAL_RTD_VERIFY_RPS",
        ):
            self.assertFalse(_is_trusted(expression), expression)
        for expression in (
            "github.run_id",
            "runner.temp",
            "steps.texlive-apt-cache.outputs.cache-hit || 'false'",
            "hashFiles('inputs.x')",
        ):
            self.assertTrue(_is_trusted(expression), expression)


class TestDispatchInputValidator(unittest.TestCase):
    def test_record_id_pattern_matches_the_python_contract(self) -> None:
        python_source = PYTHON_RECORD_ID_SOURCE.read_text(encoding="utf-8")
        python_pattern = re.search(
            r'_QUEUE_RECORD_ID_RE = re\.compile\(r"([^"]+)"\)', python_source
        )
        shell_pattern = re.search(
            r"^RECORD_ID_RE='\^(.+)\$'$", VALIDATOR.read_text(encoding="utf-8"), re.MULTILINE
        )
        self.assertIsNotNone(python_pattern)
        self.assertIsNotNone(shell_pattern)
        self.assertEqual(python_pattern.group(1), shell_pattern.group(1))

    def test_queue_workflows_validate_inputs_before_processing(self) -> None:
        for filename, processing_step in (
            ("feishu-build-queue.yml", "Process Feishu build queue"),
            ("feishu-draft-build-queue.yml", "Process Feishu draft queue"),
            ("feishu-start-review.yml", "Process review-start queue"),
            ("feishu-web-publish-queue.yml", "Process Feishu Web Publish queue"),
            ("web-publish-receipt.yml", "Verify deployment and register HTML_link"),
        ):
            with self.subTest(filename=filename):
                document = yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))
                (job,) = document["jobs"].values()
                names = [str(step.get("name") or "") for step in job["steps"]]
                validate = names.index("Validate dispatch inputs")
                self.assertLess(validate, names.index("Validate required secrets"))
                self.assertLess(validate, names.index(processing_step))
                self.assertIn(
                    "scripts/validate_dispatch_inputs.sh", str(job["steps"][validate]["run"])
                )

    @unittest.skipIf(shutil.which("bash") is None, "bash is required")
    def test_validator_accepts_well_formed_and_rejects_shell_payloads(self) -> None:
        def run(record_id: str, record_ids: str) -> int:
            return subprocess.run(
                [
                    "bash",
                    str(VALIDATOR),
                    "record-id",
                    "QUEUE_RECORD_ID",
                    "record-ids",
                    "QUEUE_RECORD_IDS",
                ],
                env={"PATH": "/usr/bin:/bin", "QUEUE_RECORD_ID": record_id, "QUEUE_RECORD_IDS": record_ids},
                capture_output=True,
                text=True,
                check=False,
            ).returncode

        self.assertEqual(0, run("", ""))
        self.assertEqual(0, run("recAbC123", ""))
        self.assertEqual(0, run("rec_publish", "recA, recB ,,rec-c"))
        self.assertEqual(1, run('rec1"; id; "', ""))
        self.assertEqual(1, run("$(id)", ""))
        self.assertEqual(1, run("", "recA,$(id)"))
        self.assertEqual(1, run("", "recA\nrecB"))
        self.assertEqual(1, run("REC123", ""))


if __name__ == "__main__":
    unittest.main()
