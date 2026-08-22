"""Run the lightweight check gate for every configured build target.

The driver deliberately keeps target discovery separate from execution.  A
config without a matching fixture ``document_key`` is an explicit SKIP, while
an executable target is delegated to the normal ``build.py check`` command.
This lets the CI job grow with ``configs/config*.yaml`` without changing the
existing US/JP jobs or silently treating missing fixtures as coverage.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import build_docs  # noqa: E402
from tools.config_loader import load_config_mapping  # noqa: E402


@dataclass(frozen=True)
class CheckTarget:
    config_path: Path
    model: str
    region: str
    lang: str | None

    @property
    def document_key(self) -> str:
        return f"{self.model}_{self.region}"


@dataclass(frozen=True)
class CheckResult:
    config: str
    model: str | None
    region: str | None
    lang: str | None
    document_key: str | None
    status: str
    reason: str
    returncode: int | None = None


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


Runner = Callable[[Sequence[str]], CommandResult]


def discover_targets(configs_dir: Path) -> tuple[CheckTarget, ...]:
    """Resolve every target from every config file in ``configs_dir``."""

    targets: list[CheckTarget] = []
    for config_path in sorted(configs_dir.glob("config*.yaml")):
        cfg = load_config_mapping(config_path)
        resolved = build_docs.resolve_build_targets(
            cfg,
            arg_model=None,
            arg_region=None,
            arg_lang=None,
            all_targets=True,
        )
        if not resolved:
            raise RuntimeError(f"Config {config_path.name} resolved no targets")
        for target in resolved:
            if not target.model or not target.region:
                raise RuntimeError(
                    f"Config {config_path.name} resolved an incomplete target: {target!r}"
                )
            targets.append(
                CheckTarget(
                    config_path=config_path,
                    model=target.model,
                    region=target.region,
                    lang=target.lang,
                )
            )
    if not targets:
        raise RuntimeError(f"No config*.yaml files found under {configs_dir}")
    return tuple(targets)


def fixture_document_keys(data_root: Path) -> set[str]:
    """Return normalized document keys from the phase2 Spec_Master fixture."""

    spec_master = data_root / "Spec_Master.csv"
    if not spec_master.exists():
        raise RuntimeError(f"Fixture is missing {spec_master}")

    with spec_master.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = {str(name).strip().lower() for name in (reader.fieldnames or [])}
        if "document_key" not in fieldnames:
            raise RuntimeError(f"Fixture is missing the document_key column: {spec_master}")
        key_column = next(name for name in (reader.fieldnames or ()) if name.strip().lower() == "document_key")
        return {
            str(row.get(key_column) or "").strip()
            for row in reader
            if str(row.get(key_column) or "").strip()
        }


def _relative_config(config_path: Path, repo_root: Path) -> str:
    try:
        return config_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return config_path.as_posix()


def build_check_command(
    target: CheckTarget,
    *,
    repo_root: Path,
    data_root: Path,
    staging_root: Path | None = None,
) -> list[str]:
    command = [
        sys.executable,
        str(repo_root / "build.py"),
        "check",
        "--config",
        str(target.config_path),
        "--model",
        target.model,
        "--region",
        target.region,
        "--data-root",
        str(data_root),
    ]
    if target.lang:
        command.extend(["--lang", target.lang])
    if staging_root is not None:
        command.extend(["--staging-root", str(staging_root)])
    return command


def _default_runner(command: Sequence[str]) -> CommandResult:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def evaluate_targets(
    targets: Iterable[CheckTarget],
    *,
    fixture_keys: set[str],
    repo_root: Path,
    data_root: Path,
    runner: Runner = _default_runner,
    staging_root: Path | None = None,
) -> tuple[CheckResult, ...]:
    results: list[CheckResult] = []
    for target in targets:
        config = _relative_config(target.config_path, repo_root)
        if target.document_key not in fixture_keys:
            results.append(
                CheckResult(
                    config=config,
                    model=target.model,
                    region=target.region,
                    lang=target.lang,
                    document_key=target.document_key,
                    status="SKIP",
                    reason=f"fixture missing document_key {target.document_key}",
                )
            )
            continue

        command_result = runner(
            build_check_command(
                target,
                repo_root=repo_root,
                data_root=data_root,
                staging_root=staging_root,
            )
        )
        results.append(
            CheckResult(
                config=config,
                model=target.model,
                region=target.region,
                lang=target.lang,
                document_key=target.document_key,
                status="PASS" if command_result.returncode == 0 else "FAIL",
                reason=(
                    "build.py check passed"
                    if command_result.returncode == 0
                    else (command_result.stdout.strip() or command_result.stderr.strip() or "build.py check failed")[-1000:]
                ),
                returncode=command_result.returncode,
            )
        )
    return tuple(results)


def _load_ratchet_counts(path: Path) -> tuple[int, int | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"SKIP ratchet file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"SKIP ratchet file is not valid JSON: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("skip_count"), int):
        raise RuntimeError(f"SKIP ratchet file must contain integer skip_count: {path}")
    fail_count = payload.get("fail_count")
    if fail_count is not None and not isinstance(fail_count, int):
        raise RuntimeError(f"ratchet file fail_count must be an integer when present: {path}")
    return payload["skip_count"], fail_count


def load_skip_baseline(path: Path) -> int:
    return _load_ratchet_counts(path)[0]


def load_fail_baseline(path: Path) -> int | None:
    """The FAIL ratchet is opt-in per file so an older baseline still loads."""
    return _load_ratchet_counts(path)[1]


def build_report(
    results: Sequence[CheckResult],
    *,
    baseline_skip_count: int,
    baseline_fail_count: int | None = None,
) -> dict[str, object]:
    counts = {status: sum(result.status == status for result in results) for status in ("PASS", "SKIP", "FAIL")}
    denominator = counts["PASS"] + counts["SKIP"] + counts["FAIL"]
    coverage = counts["PASS"] / denominator if denominator else 0.0
    report: dict[str, object] = {
        "schema_version": 1,
        "counts": counts,
        "coverage": coverage,
        "coverage_definition": "PASS/(PASS+SKIP+FAIL)",
        "skip_ratchet": {
            "baseline": baseline_skip_count,
            "current": counts["SKIP"],
            "passed": counts["SKIP"] <= baseline_skip_count,
        },
        "results": [asdict(result) for result in results],
    }
    # The FAIL ratchet is what makes the observation lane mean something. The
    # lane runs with --observation, which reports FAIL rows without failing, so
    # before this a target regressing from PASS to FAIL was invisible in CI —
    # only the SKIP ratchet could turn the job red. The baseline records the
    # failures that are already known and separately tracked; one more than
    # that fails the run even in observation mode.
    if baseline_fail_count is not None:
        report["fail_ratchet"] = {
            "baseline": baseline_fail_count,
            "current": counts["FAIL"],
            "passed": counts["FAIL"] <= baseline_fail_count,
        }
    return report


def run_driver(
    *,
    configs_dir: Path,
    data_root: Path,
    repo_root: Path,
    skip_baseline: Path,
    report_path: Path | None = None,
    staging_root: Path | None = None,
    fail_on_failures: bool = True,
    runner: Runner = _default_runner,
) -> tuple[int, dict[str, object]]:
    targets = discover_targets(configs_dir)
    fixture_keys = fixture_document_keys(data_root)
    results = evaluate_targets(
        targets,
        fixture_keys=fixture_keys,
        repo_root=repo_root,
        data_root=data_root,
        runner=runner,
        staging_root=staging_root,
    )
    baseline, baseline_fail = _load_ratchet_counts(skip_baseline)
    report = build_report(
        results,
        baseline_skip_count=baseline,
        baseline_fail_count=baseline_fail,
    )
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = report["counts"]
    assert isinstance(counts, dict)
    for result in results:
        print(f"[{result.status}] {result.config} {result.document_key}: {result.reason}")
    print(
        "[ci-check-targets] "
        f"PASS={counts['PASS']} SKIP={counts['SKIP']} FAIL={counts['FAIL']} "
        f"coverage={float(report['coverage']):.4f} "
        f"definition={report['coverage_definition']}"
    )
    ratchet = report["skip_ratchet"]
    assert isinstance(ratchet, dict)
    if not ratchet["passed"]:
        print(
            f"[ci-check-targets] SKIP ratchet failed: current={ratchet['current']} "
            f"baseline={ratchet['baseline']}",
            file=sys.stderr,
        )
    fail_ratchet = report.get("fail_ratchet")
    fail_ratchet_failed = False
    if isinstance(fail_ratchet, dict) and not fail_ratchet["passed"]:
        fail_ratchet_failed = True
        newly = [result for result in results if result.status == "FAIL"]
        print(
            f"[ci-check-targets] FAIL ratchet failed: current={fail_ratchet['current']} "
            f"baseline={fail_ratchet['baseline']} — failing targets: "
            + ", ".join(f"{r.config} {r.document_key}" for r in newly),
            file=sys.stderr,
        )
    exit_code = (
        1
        if (fail_on_failures and counts["FAIL"]) or not ratchet["passed"] or fail_ratchet_failed
        else 0
    )
    return exit_code, report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configs-dir", default="configs")
    parser.add_argument("--data-root", default="tests/fixtures/phase2")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--skip-baseline", default=".github/ci_check_targets_skip_baseline.json")
    parser.add_argument("--report", default=None, help="Optional JSON report path")
    parser.add_argument("--staging-root", default=None, help="Optional root for generated check outputs")
    parser.add_argument(
        "--observation",
        action="store_true",
        help="Report target FAIL rows without failing the observation lane; SKIP ratchet still fails",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    return run_driver(
        configs_dir=(repo_root / args.configs_dir).resolve(),
        data_root=(repo_root / args.data_root).resolve(),
        repo_root=repo_root,
        skip_baseline=(repo_root / args.skip_baseline).resolve(),
        report_path=(repo_root / args.report).resolve() if args.report else None,
        staging_root=(repo_root / args.staging_root).resolve() if args.staging_root else None,
        fail_on_failures=not args.observation,
    )[0]


if __name__ == "__main__":
    raise SystemExit(main())
