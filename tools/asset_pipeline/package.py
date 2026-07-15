"""Atomic manifest and deterministic ZIP assembly for asset intake."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from tools.asset_pipeline.extract import (
    extract_artifacts,
    pymupdf_versions,
    sha256_file,
    validate_source,
)
from tools.asset_pipeline.models import (
    ArtifactRecord,
    AssetIntakeError,
    IntakeRecipe,
    IntakeResult,
    SourceInspection,
)

MANIFEST_NAME = "manifest.json"
ARTIFACTS_CSV_NAME = "artifacts.csv"
PACKAGE_NAME = "asset-package.zip"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_FILE_MODE = 0o100644 << 16


def _gate_manifest(status: str, reasons: tuple[str, ...]) -> dict[str, Any]:
    return {"reasons": list(reasons), "status": status}


def _archive_manifest(recipe: IntakeRecipe) -> dict[str, Any]:
    archive: dict[str, Any] = {
        "pages": {
            "first": recipe.archive.pages.first,
            "last": recipe.archive.pages.last,
        },
        "pdf": {"path_pattern": recipe.archive.pdf.path_pattern},
    }
    if recipe.archive.previews is not None:
        archive["previews"] = {
            "default_scale": recipe.archive.previews.default_scale,
            "page_scale": {
                str(page): scale for page, scale in recipe.archive.previews.page_scale
            },
            "path_pattern": recipe.archive.previews.path_pattern,
        }
    return archive


def _page_catalog_manifest(recipe: IntakeRecipe) -> list[dict[str, Any]]:
    return [
        {
            "build_eligible": row.build_eligible,
            "gate": _gate_manifest(row.gate.status, row.gate.reasons),
            "locale": row.locale,
            "page": row.page,
            "page_key": row.page_key,
            "risk_tags": list(row.risk_tags),
            "role": row.role,
        }
        for row in recipe.page_catalog
    ]


def _asset_manifest(recipe: IntakeRecipe) -> list[dict[str, Any]]:
    return [
        {
            "asset_key": asset.asset_key,
            "build_eligible": asset.build_eligible,
            "gate": _gate_manifest(asset.gate.status, asset.gate.reasons),
            "outputs": [output.as_manifest() for output in asset.outputs],
            "page": asset.page,
            "risk_tags": list(asset.risk_tags),
            "scope": {
                "locales": list(asset.scope.locales),
                "models": list(asset.scope.models),
                "regions": list(asset.scope.regions),
            },
            "text_policy": asset.text_policy,
            "transforms": [transform.as_manifest() for transform in asset.transforms],
            "visual_review_required": asset.visual_review_required,
        }
        for asset in recipe.assets
    ]


def build_manifest(
    recipe: IntakeRecipe,
    inspection: SourceInspection,
    artifacts: tuple[ArtifactRecord, ...],
    *,
    artifacts_csv_sha256: str,
) -> dict[str, Any]:
    """Build a path- and time-independent manifest payload."""

    return {
        "archive": _archive_manifest(recipe),
        "artifacts": [record.as_manifest() for record in artifacts],
        "assets": _asset_manifest(recipe),
        "coordinate_contract": {
            "bbox_origin": recipe.coordinate_contract.bbox_origin,
            "bbox_space": recipe.coordinate_contract.bbox_space,
            "bbox_units": recipe.coordinate_contract.bbox_units,
            "page_numbering": recipe.coordinate_contract.page_numbering,
        },
        "indexes": {
            "artifacts_csv": {
                "path": ARTIFACTS_CSV_NAME,
                "sha256": artifacts_csv_sha256,
            }
        },
        "manifest_version": 1,
        "page_catalog": _page_catalog_manifest(recipe),
        "normalization": {
            "engine": recipe.normalization.engine,
            "forbidden_pdf_markers": list(recipe.normalization.forbidden_pdf_markers),
            "max_render_pixels": recipe.normalization.max_render_pixels,
            "pdf_save": {
                "clean": recipe.normalization.pdf_save.clean,
                "deflate": recipe.normalization.pdf_save.deflate,
                "garbage": recipe.normalization.pdf_save.garbage,
                "no_new_id": recipe.normalization.pdf_save.no_new_id,
            },
            "validated_version": recipe.normalization.validated_version,
            "validated_mupdf_version": recipe.normalization.validated_mupdf_version,
        },
        "recipe_sha256": hashlib.sha256(recipe.canonical_bytes).hexdigest(),
        "runtime": {
            "mupdf_version": pymupdf_versions()[1],
            "pymupdf_version": pymupdf_versions()[0],
        },
        "source": {
            "ai_private_data_count": inspection.ai_private_data_count,
            "ai_metadata_count": inspection.ai_metadata_count,
            "page_count": inspection.page_count,
            "piece_info_count": inspection.piece_info_count,
            "sha256": inspection.sha256,
            "source_key": recipe.source.source_key,
        },
    }


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, separators=(",", ": "))
        + "\n"
    ).encode("utf-8")


def canonical_artifacts_csv_bytes(artifacts: tuple[ArtifactRecord, ...]) -> bytes:
    """Render a stable, spreadsheet-friendly artifact index."""

    fieldnames = (
        "path",
        "repo_path",
        "asset_key",
        "kind",
        "format",
        "source_page",
        "gate_status",
        "build_eligible",
        "visual_review_required",
        "text_policy",
        "sha256",
        "expected_sha256",
        "byte_size",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for artifact in sorted(artifacts, key=lambda item: item.path):
        writer.writerow(
            {
                "path": artifact.path,
                "repo_path": artifact.repo_path or "",
                "asset_key": artifact.asset_key or "",
                "kind": artifact.kind,
                "format": artifact.format,
                "source_page": artifact.source_page,
                "gate_status": artifact.gate_status,
                "build_eligible": str(artifact.build_eligible).upper(),
                "visual_review_required": str(artifact.visual_review_required).upper(),
                "text_policy": artifact.text_policy or "",
                "sha256": artifact.sha256,
                "expected_sha256": artifact.expected_sha256 or "",
                "byte_size": artifact.byte_size,
            }
        )
    return stream.getvalue().encode("utf-8")


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ZIP_FILE_MODE
    info.flag_bits |= 0x800
    return info


def write_deterministic_zip(
    package_path: Path,
    *,
    root: Path,
    relative_paths: tuple[str, ...],
) -> None:
    """Write sorted files with fixed metadata and maximum deflate compression."""

    if len(set(relative_paths)) != len(relative_paths):
        raise AssetIntakeError("package input paths must be unique")
    with zipfile.ZipFile(package_path, "w") as bundle:
        for relative_path in sorted(relative_paths):
            data = root.joinpath(*relative_path.split("/")).read_bytes()
            bundle.writestr(
                _zip_info(relative_path),
                data,
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def _prepare_staging(output_root: Path) -> Path:
    if output_root.exists():
        raise AssetIntakeError(f"asset output root already exists: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{output_root.name}.tmp-", dir=output_root.parent))


def run_intake(
    *,
    source_path: Path,
    recipe: IntakeRecipe,
    output_root: Path,
) -> IntakeResult:
    """Validate, extract, package, then atomically expose one complete run."""

    inspection = validate_source(source_path, recipe)
    staging = _prepare_staging(output_root)
    try:
        artifact_root = staging / "artifacts"
        artifact_root.mkdir()
        artifacts = extract_artifacts(source_path, recipe, artifact_root)
        source_sha256_after = sha256_file(source_path)
        if source_sha256_after != inspection.sha256:
            raise AssetIntakeError(
                "source bytes changed during intake: "
                f"started at {inspection.sha256}, ended at {source_sha256_after}"
            )
        artifacts_csv_path = staging / ARTIFACTS_CSV_NAME
        artifacts_csv_path.write_bytes(canonical_artifacts_csv_bytes(artifacts))
        artifacts_csv_sha256 = sha256_file(artifacts_csv_path)
        manifest = build_manifest(
            recipe,
            inspection,
            artifacts,
            artifacts_csv_sha256=artifacts_csv_sha256,
        )
        manifest_path = staging / MANIFEST_NAME
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        package_path = staging / PACKAGE_NAME
        package_members = (
            ARTIFACTS_CSV_NAME,
            MANIFEST_NAME,
            *(record.path for record in artifacts),
        )
        write_deterministic_zip(
            package_path,
            root=staging,
            relative_paths=tuple(package_members),
        )
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return IntakeResult(
        output_root=output_root,
        manifest_path=output_root / MANIFEST_NAME,
        artifacts_csv_path=output_root / ARTIFACTS_CSV_NAME,
        package_path=output_root / PACKAGE_NAME,
        artifacts=artifacts,
    )


def result_summary(result: IntakeResult) -> dict[str, Any]:
    """Return a concise user-facing summary without embedding absolute paths."""

    counts: dict[str, int] = {}
    for artifact in result.artifacts:
        counts[artifact.kind] = counts.get(artifact.kind, 0) + 1
    return {
        "artifact_count": len(result.artifacts),
        "artifact_kinds": dict(sorted(counts.items())),
        "artifacts_csv": ARTIFACTS_CSV_NAME,
        "artifacts_csv_sha256": sha256_file(result.artifacts_csv_path),
        "manifest": MANIFEST_NAME,
        "package": PACKAGE_NAME,
        "package_sha256": sha256_file(result.package_path),
    }
