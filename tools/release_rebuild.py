#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.release_reproducibility import (  # noqa: E402
    REPRODUCIBILITY_POLICY,
    REPRODUCIBILITY_SCHEMA_VERSION,
    REVIEW_OVERLAY_PATH_ENV,
    REVIEW_OVERLAY_REF_ENV,
    REVIEW_OVERLAY_SHA_ENV,
    SOURCE_DATE_EPOCH_ENV,
    ReviewOverlayProvenance,
)
from tools.release_snapshot import verify_frozen_release_snapshot  # noqa: E402
from tools.toolchain_provenance import collect_toolchain  # noqa: E402
from tools.utils.path_utils import (  # noqa: E402
    release_rebuild_verification_of,
    release_snapshot_identity_of,
)

_FULL_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_KEYS = ("word_output", "md_output", "pdf_output")


@dataclass(frozen=True)
class ExpectedArtifact:
    key: str
    path: str
    sha256: str


@dataclass(frozen=True)
class ReleaseRebuildPlan:
    manifest_path: Path
    git_sha: str
    config_path: str
    model: str
    region: str
    release_version: str
    snapshot_dir: Path
    snapshot_sha256: str
    target_matrix: tuple[dict[str, str], ...]
    source_date_epoch: int
    review_overlay: ReviewOverlayProvenance | None
    toolchain: dict[str, Any]
    artifacts: tuple[ExpectedArtifact, ...]


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} cannot be read: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object: {path}")
    return payload


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"release manifest requires non-empty {key}")
    return value.strip()


def _repo_relative_path(repo_root: Path, raw: str, *, label: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        raise RuntimeError(f"{label} must be repository-relative: {raw}")
    resolved = (repo_root / path).resolve(strict=False)
    try:
        resolved.relative_to(repo_root.resolve(strict=False))
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes the repository: {raw}") from exc
    return resolved


def _required_sha256(value: object, *, label: str) -> str:
    normalized = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise RuntimeError(f"{label} must be a full SHA-256 digest")
    return normalized


def _expected_target_matrix(manifest: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    model = _required_text(manifest, "model")
    region = _required_text(manifest, "region")
    languages = manifest.get("build_languages")
    if not isinstance(languages, list) or not languages:
        raise RuntimeError("release manifest requires a non-empty build_languages list")
    rows: list[dict[str, str]] = []
    for language in languages:
        normalized = str(language or "").strip()
        if not normalized:
            raise RuntimeError("release manifest build_languages contains an empty value")
        rows.append({"model": model, "region": region, "lang": normalized})
    return tuple(rows)


def _review_overlay_from_manifest(
    reproducibility: Mapping[str, Any],
) -> ReviewOverlayProvenance | None:
    raw = reproducibility.get("review_overlay")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise RuntimeError("release manifest review_overlay must be an object")
    source_ref = _required_text(raw, "source_ref")
    source_sha = _required_text(raw, "source_sha").lower()
    if not _FULL_GIT_SHA_RE.fullmatch(source_sha):
        raise RuntimeError("release manifest review_overlay source_sha must be a full Git SHA")
    tree_sha = _required_text(raw, "tree_sha").lower()
    if not _FULL_GIT_SHA_RE.fullmatch(tree_sha):
        raise RuntimeError("release manifest review_overlay tree_sha must be a full Git SHA")
    target_path = _required_text(raw, "target_path")
    normalized_target = Path(target_path).as_posix().strip("/")
    if Path(target_path).is_absolute() or not normalized_target.startswith("docs/_review/"):
        raise RuntimeError("release manifest review_overlay target_path is not a review subtree")
    if ".." in Path(normalized_target).parts:
        raise RuntimeError("release manifest review_overlay target_path escapes the repository")
    return ReviewOverlayProvenance(
        source_ref=source_ref,
        source_sha=source_sha,
        target_path=normalized_target,
        tree_sha=tree_sha,
    )


def load_release_rebuild_plan(
    manifest_path: Path,
    *,
    repo_root: Path = ROOT,
) -> ReleaseRebuildPlan:
    resolved_manifest = (
        manifest_path
        if manifest_path.is_absolute()
        else repo_root / manifest_path
    ).resolve(strict=False)
    manifest = _read_json_object(resolved_manifest, label="release manifest")

    git_sha = _required_text(manifest, "git_sha").lower()
    if not _FULL_GIT_SHA_RE.fullmatch(git_sha):
        raise RuntimeError("release manifest git_sha must be a full 40-character commit SHA")
    config_raw = _required_text(manifest, "config_path")
    config_path = _repo_relative_path(repo_root, config_raw, label="config_path")
    if not config_path.is_file():
        raise RuntimeError(f"release manifest config_path is missing: {config_raw}")

    release_version = _required_text(manifest, "release_version")
    model = _required_text(manifest, "model")
    region = _required_text(manifest, "region")
    target_matrix = _expected_target_matrix(manifest)

    snapshot = manifest.get("snapshot")
    if not isinstance(snapshot, dict):
        raise RuntimeError("release manifest is not bound to a frozen snapshot")
    snapshot_raw = _required_text(snapshot, "path")
    snapshot_dir = _repo_relative_path(repo_root, snapshot_raw, label="snapshot.path")
    identity_raw = _required_text(snapshot, "identity_path")
    identity_path = _repo_relative_path(
        repo_root,
        identity_raw,
        label="snapshot.identity_path",
    )
    if identity_path != release_snapshot_identity_of(snapshot_dir).resolve(strict=False):
        raise RuntimeError("release manifest snapshot identity path is not canonical")
    snapshot_sha256 = _required_sha256(
        snapshot.get("snapshot_sha256"),
        label="snapshot.snapshot_sha256",
    )
    manifest_matrix = snapshot.get("target_matrix")
    if manifest_matrix != list(target_matrix):
        raise RuntimeError("release manifest snapshot target matrix does not match target")
    verify_frozen_release_snapshot(
        snapshot_dir,
        expected_sha256=snapshot_sha256,
        expected_target_matrix=target_matrix,
    )

    reproducibility = manifest.get("reproducibility")
    if not isinstance(reproducibility, dict):
        raise RuntimeError("release manifest lacks reproducibility contract")
    if reproducibility.get("schema_version") != REPRODUCIBILITY_SCHEMA_VERSION:
        raise RuntimeError("release manifest uses an unsupported reproducibility schema")
    if reproducibility.get("policy") != REPRODUCIBILITY_POLICY:
        raise RuntimeError("release manifest uses an unsupported reproducibility policy")
    if reproducibility.get("artifact_contract") != "sha256-byte-equivalence":
        raise RuntimeError("release manifest does not require byte-equivalent artifacts")
    source_date_epoch = reproducibility.get("source_date_epoch")
    if not isinstance(source_date_epoch, int) or isinstance(source_date_epoch, bool) or source_date_epoch < 0:
        raise RuntimeError("release manifest requires a non-negative source_date_epoch")
    if reproducibility.get("artifacts") != list(_ARTIFACT_KEYS):
        raise RuntimeError("release manifest reproducibility artifact set is incomplete")
    review_overlay = _review_overlay_from_manifest(reproducibility)

    expected_artifacts: list[ExpectedArtifact] = []
    for key in _ARTIFACT_KEYS:
        record = manifest.get(key)
        if not isinstance(record, dict) or record.get("exists") is not True:
            raise RuntimeError(f"release manifest requires existing {key}")
        artifact_path = _required_text(record, "path")
        _repo_relative_path(repo_root, artifact_path, label=f"{key}.path")
        expected_artifacts.append(
            ExpectedArtifact(
                key=key,
                path=artifact_path,
                sha256=_required_sha256(record.get("sha256"), label=f"{key}.sha256"),
            )
        )

    toolchain = manifest.get("toolchain")
    if not isinstance(toolchain, dict):
        raise RuntimeError("release manifest requires toolchain provenance")

    return ReleaseRebuildPlan(
        manifest_path=resolved_manifest,
        git_sha=git_sha,
        config_path=config_raw,
        model=model,
        region=region,
        release_version=release_version,
        snapshot_dir=snapshot_dir,
        snapshot_sha256=snapshot_sha256,
        target_matrix=target_matrix,
        source_date_epoch=source_date_epoch,
        review_overlay=review_overlay,
        toolchain=dict(toolchain),
        artifacts=tuple(expected_artifacts),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_checked(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    try:
        return runner(
            list(command),
            cwd=str(cwd),
            env=dict(env) if env is not None else None,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"command failed: {' '.join(command)}") from exc


def _verify_commit_exists(
    plan: ReleaseRebuildPlan,
    *,
    repo_root: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    _run_checked(
        ["git", "cat-file", "-e", f"{plan.git_sha}^{{commit}}"],
        cwd=repo_root,
        runner=runner,
    )
    if plan.review_overlay is not None:
        _run_checked(
            ["git", "cat-file", "-e", f"{plan.review_overlay.source_sha}^{{commit}}"],
            cwd=repo_root,
            runner=runner,
        )


def _find_rebuilt_manifest(staging_root: Path) -> Path:
    manifests = sorted((staging_root / "reports" / "releases").rglob("manifests/*.json"))
    if len(manifests) != 1:
        raise RuntimeError(
            "historical publish must produce exactly one release manifest; "
            f"found {len(manifests)}"
        )
    return manifests[0]


def _rebuilt_artifact_path(
    record: Mapping[str, Any],
    *,
    checkout: Path,
    staging_root: Path,
    key: str,
) -> Path:
    raw = _required_text(record, "path")
    candidate = Path(raw)
    resolved = (
        candidate if candidate.is_absolute() else checkout / candidate
    ).resolve(strict=False)
    try:
        resolved.relative_to(staging_root.resolve(strict=False))
    except ValueError as exc:
        raise RuntimeError(f"rebuilt {key} escaped isolated staging root: {raw}") from exc
    if not resolved.is_file():
        raise RuntimeError(f"rebuilt {key} is missing: {resolved}")
    return resolved


def _compare_rebuilt_manifest(
    plan: ReleaseRebuildPlan,
    rebuilt_manifest_path: Path,
    *,
    checkout: Path,
    staging_root: Path,
) -> dict[str, Any]:
    rebuilt = _read_json_object(rebuilt_manifest_path, label="rebuilt release manifest")
    if rebuilt.get("git_sha") != plan.git_sha:
        raise RuntimeError("rebuilt release manifest changed git_sha")
    rebuilt_reproducibility = rebuilt.get("reproducibility")
    if not isinstance(rebuilt_reproducibility, dict) or (
        rebuilt_reproducibility.get("source_date_epoch") != plan.source_date_epoch
    ):
        raise RuntimeError("rebuilt release manifest changed source_date_epoch")
    expected_review_overlay = (
        plan.review_overlay.as_record() if plan.review_overlay is not None else None
    )
    if rebuilt_reproducibility.get("review_overlay") != expected_review_overlay:
        if expected_review_overlay is not None or "review_overlay" in rebuilt_reproducibility:
            raise RuntimeError("rebuilt release manifest changed review_overlay provenance")
    rebuilt_snapshot = rebuilt.get("snapshot")
    if not isinstance(rebuilt_snapshot, dict) or (
        rebuilt_snapshot.get("snapshot_sha256") != plan.snapshot_sha256
    ):
        raise RuntimeError("rebuilt release manifest changed snapshot_sha256")

    artifact_report: dict[str, Any] = {}
    for expected in plan.artifacts:
        record = rebuilt.get(expected.key)
        if not isinstance(record, dict) or record.get("exists") is not True:
            raise RuntimeError(f"rebuilt release manifest lacks {expected.key}")
        path = _rebuilt_artifact_path(
            record,
            checkout=checkout,
            staging_root=staging_root,
            key=expected.key,
        )
        actual_sha256 = _sha256(path)
        manifest_sha256 = _required_sha256(
            record.get("sha256"),
            label=f"rebuilt {expected.key}.sha256",
        )
        if actual_sha256 != manifest_sha256:
            raise RuntimeError(f"rebuilt {expected.key} bytes disagree with rebuilt manifest")
        artifact_report[expected.key] = {
            "name": path.name,
            "expected_sha256": expected.sha256,
            "actual_sha256": actual_sha256,
            "matched": actual_sha256 == expected.sha256,
        }
    return artifact_report


def verify_release_rebuild(
    manifest_path: Path,
    *,
    report_path: Path | None = None,
    repo_root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    toolchain_collector: Callable[..., dict[str, Any]] = collect_toolchain,
) -> tuple[Path, dict[str, Any]]:
    plan = load_release_rebuild_plan(manifest_path, repo_root=repo_root)
    current_toolchain = toolchain_collector(repo_root=repo_root)
    if current_toolchain != plan.toolchain:
        raise RuntimeError(
            "current toolchain does not exactly match the release manifest; "
            "rebuild on the recorded release environment"
        )
    _verify_commit_exists(plan, repo_root=repo_root, runner=runner)

    output_report = report_path
    if output_report is None:
        output_report = release_rebuild_verification_of(plan.snapshot_dir.parent)
    elif not output_report.is_absolute():
        output_report = repo_root / output_report
    output_report = output_report.resolve(strict=False)
    try:
        output_report.relative_to(plan.snapshot_dir.resolve(strict=False))
    except ValueError:
        pass
    else:
        raise RuntimeError("rebuild verification report cannot be written inside immutable snapshot")

    artifact_report: dict[str, Any]
    with tempfile.TemporaryDirectory(prefix="auto-manual-release-rebuild-") as td:
        temp_root = Path(td)
        checkout = temp_root / "checkout"
        staging_root = temp_root / "staging"
        _run_checked(
            ["git", "worktree", "add", "--detach", str(checkout), plan.git_sha],
            cwd=repo_root,
            runner=runner,
        )
        try:
            env = dict(os.environ)
            env[SOURCE_DATE_EPOCH_ENV] = str(plan.source_date_epoch)
            if plan.review_overlay is not None:
                overlay = plan.review_overlay
                _run_checked(
                    [
                        "git",
                        "restore",
                        "--source",
                        overlay.source_sha,
                        "--staged",
                        "--worktree",
                        "--",
                        overlay.target_path,
                    ],
                    cwd=checkout,
                    runner=runner,
                )
                env[REVIEW_OVERLAY_REF_ENV] = overlay.source_ref
                env[REVIEW_OVERLAY_SHA_ENV] = overlay.source_sha
                env[REVIEW_OVERLAY_PATH_ENV] = overlay.target_path
            _run_checked(
                [
                    sys.executable,
                    str(checkout / "build.py"),
                    "publish",
                    "--config",
                    plan.config_path,
                    "--model",
                    plan.model,
                    "--region",
                    plan.region,
                    "--data-root",
                    str(plan.snapshot_dir),
                    "--staging-root",
                    str(staging_root),
                    "--version",
                    plan.release_version,
                ],
                cwd=checkout,
                env=env,
                runner=runner,
            )
            rebuilt_manifest = _find_rebuilt_manifest(staging_root)
            artifact_report = _compare_rebuilt_manifest(
                plan,
                rebuilt_manifest,
                checkout=checkout,
                staging_root=staging_root,
            )
        finally:
            _run_checked(
                ["git", "worktree", "remove", "--force", str(checkout)],
                cwd=repo_root,
                runner=runner,
            )

    passed = all(bool(record["matched"]) for record in artifact_report.values())
    report: dict[str, Any] = {
        "schema_version": 1,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "failed",
        "manifest_path": plan.manifest_path.as_posix(),
        "git_sha": plan.git_sha,
        "release_version": plan.release_version,
        "snapshot_sha256": plan.snapshot_sha256,
        "source_date_epoch": plan.source_date_epoch,
        "review_overlay": (
            plan.review_overlay.as_record() if plan.review_overlay is not None else None
        ),
        "toolchain_match": True,
        "artifacts": artifact_report,
    }
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not passed:
        mismatches = [key for key, record in artifact_report.items() if not record["matched"]]
        raise RuntimeError(
            "historical release rebuild is not byte-equivalent: " + ", ".join(mismatches)
        )
    return output_report, report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild a versioned release from its Git SHA and frozen snapshot.",
    )
    parser.add_argument("--manifest", required=True, help="Versioned release manifest JSON")
    parser.add_argument("--report", default=None, help="Optional verification report path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report_path, _report = verify_release_rebuild(
            Path(args.manifest),
            report_path=Path(args.report) if args.report else None,
        )
    except RuntimeError as exc:
        print(f"[release-rebuild] ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"[release-rebuild] byte-equivalence verified: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
