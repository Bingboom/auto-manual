"""Run the config-wide doctor sweep and one production IDML smoke target.

The scheduled workflow uses committed phase2 fixtures, so this lane measures
repository/rendering drift without depending on Feishu credentials or a live
snapshot.  Target discovery is shared with the config-derived CI check lane:
adding a target to any ``configs/config*.yaml`` file automatically adds one
doctor run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.ci_check_targets import CheckTarget, discover_targets  # noqa: E402
from tools.idml.check import check_idml  # noqa: E402
from tools.idml.export_paths import default_bundle_root, default_output_path  # noqa: E402


REPORT_SCHEMA_VERSION = "nightly-render/v1"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class DoctorResult:
    config: str
    model: str
    region: str
    lang: str | None
    status: str
    reason: str
    returncode: int


@dataclass(frozen=True)
class PilotArtifact:
    path: str
    sha256: str | None
    issues: tuple[str, ...]


@dataclass(frozen=True)
class PilotResult:
    config: str
    model: str
    region: str
    lang: str | None
    status: str
    reason: str
    returncode: int
    artifact: PilotArtifact | None


Runner = Callable[[Sequence[str]], CommandResult]
ArtifactProbe = Callable[[CheckTarget], PilotArtifact]


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _command_reason(result: CommandResult, success: str, failure: str) -> str:
    if result.returncode == 0:
        return success
    detail = result.stderr.strip() or result.stdout.strip()
    return (detail or failure)[-2000:]


def build_doctor_command(
    target: CheckTarget,
    *,
    repo_root: Path,
    data_root: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(repo_root / "build.py"),
        "doctor",
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
    return command


def build_pilot_command(
    target: CheckTarget,
    *,
    repo_root: Path,
    data_root: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(repo_root / "build.py"),
        "idml",
        "--config",
        str(target.config_path),
        "--model",
        target.model,
        "--region",
        target.region,
        "--source",
        "runtime",
        "--data-root",
        str(data_root),
        "--skip-root-index",
        "--idml-mode",
        "production",
    ]
    if target.lang:
        command.extend(["--lang", target.lang])
    return command


def default_runner(command: Sequence[str]) -> CommandResult:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def resolve_pilot_target(
    targets: Sequence[CheckTarget],
    *,
    pilot_config: Path,
    pilot_model: str,
    pilot_region: str,
    pilot_lang: str | None,
) -> CheckTarget:
    config_matches = [target for target in targets if target.config_path.resolve() == pilot_config.resolve()]
    if len(config_matches) != 1:
        raise RuntimeError(
            f"Pilot config must resolve exactly one registered target: {pilot_config} "
            f"(matches={len(config_matches)})"
        )
    target = config_matches[0]
    requested = (pilot_model.strip(), pilot_region.strip().upper(), (pilot_lang or "").strip().lower() or None)
    actual = (target.model, target.region.upper(), (target.lang or "").lower() or None)
    if actual != requested:
        raise RuntimeError(
            "Pilot target does not match the registered config target: "
            f"requested={requested!r} actual={actual!r}"
        )
    return target


def make_artifact_probe(*, repo_root: Path) -> ArtifactProbe:
    def probe(target: CheckTarget) -> PilotArtifact:
        lang = target.lang or "en"
        bundle_root = default_bundle_root(repo_root, target.model, target.region, lang)
        artifact_path = default_output_path(repo_root, target.model, target.region, lang, bundle_root)
        if not artifact_path.is_file():
            return PilotArtifact(
                path=_relative_path(artifact_path, repo_root),
                sha256=None,
                issues=("production IDML artifact is missing",),
            )
        issues = tuple(check_idml(artifact_path))
        return PilotArtifact(
            path=_relative_path(artifact_path, repo_root),
            sha256=hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            issues=issues,
        )

    return probe


def build_report(
    doctor_results: Sequence[DoctorResult],
    pilot_result: PilotResult,
) -> dict[str, object]:
    doctor_counts = {
        status: sum(result.status == status for result in doctor_results)
        for status in ("PASS", "FAIL")
    }
    pilot_payload = asdict(pilot_result)
    artifact_payload = pilot_payload.get("artifact")
    if isinstance(artifact_payload, dict):
        artifact_payload["issues"] = list(artifact_payload["issues"])
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "doctor": {
            "counts": doctor_counts,
            "results": [asdict(result) for result in doctor_results],
        },
        "pilot": pilot_payload,
    }


def run_nightly(
    *,
    targets: Sequence[CheckTarget],
    pilot_target: CheckTarget,
    repo_root: Path,
    data_root: Path,
    report_path: Path | None,
    runner: Runner = default_runner,
    artifact_probe: ArtifactProbe | None = None,
) -> tuple[int, dict[str, object]]:
    doctor_results: list[DoctorResult] = []
    for target in targets:
        config = _relative_path(target.config_path, repo_root)
        print(f"[nightly-render] doctor {config} {target.model}/{target.region}/{target.lang or '-'}")
        result = runner(build_doctor_command(target, repo_root=repo_root, data_root=data_root))
        doctor_results.append(
            DoctorResult(
                config=config,
                model=target.model,
                region=target.region,
                lang=target.lang,
                status="PASS" if result.returncode == 0 else "FAIL",
                reason=_command_reason(
                    result,
                    "build.py doctor passed",
                    "build.py doctor failed",
                ),
                returncode=result.returncode,
            )
        )

    pilot_config = _relative_path(pilot_target.config_path, repo_root)
    print(
        f"[nightly-render] production IDML pilot {pilot_config} "
        f"{pilot_target.model}/{pilot_target.region}/{pilot_target.lang or '-'}"
    )
    pilot_command_result = runner(
        build_pilot_command(pilot_target, repo_root=repo_root, data_root=data_root)
    )
    artifact: PilotArtifact | None = None
    pilot_reason = _command_reason(
        pilot_command_result,
        "production IDML build passed",
        "production IDML build failed",
    )
    pilot_status = "PASS" if pilot_command_result.returncode == 0 else "FAIL"
    if pilot_command_result.returncode == 0:
        probe = artifact_probe or make_artifact_probe(repo_root=repo_root)
        artifact = probe(pilot_target)
        if artifact.issues:
            pilot_status = "FAIL"
            pilot_reason = "; ".join(artifact.issues)

    pilot_result = PilotResult(
        config=pilot_config,
        model=pilot_target.model,
        region=pilot_target.region,
        lang=pilot_target.lang,
        status=pilot_status,
        reason=pilot_reason,
        returncode=pilot_command_result.returncode,
        artifact=artifact,
    )
    report = build_report(doctor_results, pilot_result)
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = report["doctor"]["counts"]  # type: ignore[index]
    print(
        f"[nightly-render] SUMMARY doctor_pass={counts['PASS']} doctor_fail={counts['FAIL']} "
        f"pilot={pilot_result.status}"
    )
    failed = bool(counts["FAIL"]) or pilot_result.status != "PASS"
    return (1 if failed else 0), report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configs-dir", default="configs")
    parser.add_argument("--data-root", default="tests/fixtures/phase2")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--report", required=True)
    parser.add_argument("--pilot-config", required=True)
    parser.add_argument("--pilot-model", required=True)
    parser.add_argument("--pilot-region", required=True)
    parser.add_argument("--pilot-lang", default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    configs_dir = (repo_root / args.configs_dir).resolve()
    targets = discover_targets(configs_dir)
    pilot_config = Path(args.pilot_config)
    if not pilot_config.is_absolute():
        pilot_config = repo_root / pilot_config
    pilot_target = resolve_pilot_target(
        targets,
        pilot_config=pilot_config,
        pilot_model=args.pilot_model,
        pilot_region=args.pilot_region,
        pilot_lang=args.pilot_lang,
    )
    return run_nightly(
        targets=targets,
        pilot_target=pilot_target,
        repo_root=repo_root,
        data_root=(repo_root / args.data_root).resolve(),
        report_path=(repo_root / args.report).resolve(),
    )[0]


if __name__ == "__main__":
    raise SystemExit(main())
