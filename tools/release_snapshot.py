from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from tools.data_snapshot import inspect_phase2_snapshot, resolve_phase2_export_root
from tools.utils.path_utils import PathSegments, release_snapshot_identity_of


@dataclass(frozen=True)
class FrozenReleaseSnapshot:
    snapshot_dir: Path
    identity_path: Path
    identity: dict[str, Any]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(source_root: Path) -> list[dict[str, object]]:
    identity_name = PathSegments.RELEASE_SNAPSHOT_IDENTITY_JSON
    rows: list[dict[str, object]] = []
    for path in sorted(source_root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"release snapshot cannot archive symlink: {path}")
        if not path.is_file() or path.name == identity_name:
            continue
        rows.append(
            {
                "path": path.relative_to(source_root).as_posix(),
                "size": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    return rows


def _inventory_sha256(files: Iterable[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for row in files:
        digest.update(str(row["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(row["sha256"]).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _target_matrix(*, model: str, region: str, languages: Iterable[str]) -> list[dict[str, str]]:
    return [
        {"model": model, "region": region, "lang": lang}
        for lang in languages
        if lang
    ]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"release snapshot identity cannot be read: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"release snapshot identity must be a JSON object: {path}")
    return payload


def _same_binding(existing: dict[str, Any], candidate: dict[str, Any]) -> bool:
    return all(
        existing.get(key) == candidate.get(key)
        for key in ("snapshot_sha256", "source_revision", "target_matrix")
    )


def freeze_release_snapshot(
    *,
    cfg: dict[str, Any],
    repo_root: Path,
    data_root: str | Path | None,
    model: str,
    region: str,
    languages: Iterable[str],
    snapshot_dir: Path,
    frozen_at: datetime | None = None,
) -> FrozenReleaseSnapshot:
    status = inspect_phase2_snapshot(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    if not status.valid:
        details = "; ".join(status.issues)
        raise RuntimeError(f"release snapshot source is incomplete: {details}")

    source_root = resolve_phase2_export_root(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    source_manifest = status.manifest_path
    manifest_payload = _read_json(source_manifest)
    files = _inventory(source_root)
    if not files:
        raise RuntimeError(f"release snapshot source contains no files: {source_root}")

    frozen_at_value = frozen_at or datetime.now(timezone.utc)
    manifest_sha256 = _file_sha256(source_manifest)
    identity: dict[str, Any] = {
        "schema_version": 1,
        "frozen_at": frozen_at_value.isoformat(),
        "source_revision": {
            "kind": "phase2-snapshot-manifest-sha256",
            "value": manifest_sha256,
        },
        "source_manifest": {
            "sha256": manifest_sha256,
            "generated_at": manifest_payload.get("generated_at"),
            "provider": manifest_payload.get("provider"),
        },
        "target_matrix": _target_matrix(
            model=model,
            region=region,
            languages=languages,
        ),
        "snapshot_sha256": _inventory_sha256(files),
        "files": files,
    }

    identity_path = release_snapshot_identity_of(snapshot_dir)
    if snapshot_dir.exists():
        if not identity_path.exists():
            raise RuntimeError(
                f"release snapshot directory already exists without identity: {snapshot_dir}"
            )
        existing = _read_json(identity_path)
        if not _same_binding(existing, identity):
            raise RuntimeError(
                "release snapshot is immutable and the existing version is bound to different input: "
                f"{snapshot_dir}"
            )
        archived_files = _inventory(snapshot_dir)
        archived_sha256 = _inventory_sha256(archived_files)
        if archived_sha256 != existing.get("snapshot_sha256"):
            raise RuntimeError(f"release snapshot archive has drifted: {snapshot_dir}")
        return FrozenReleaseSnapshot(snapshot_dir, identity_path, existing)

    snapshot_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{snapshot_dir.name}-",
        dir=str(snapshot_dir.parent),
    ) as temp_dir:
        staged = Path(temp_dir) / snapshot_dir.name
        shutil.copytree(source_root, staged)
        staged_identity_path = release_snapshot_identity_of(staged)
        staged_identity_path.write_text(
            json.dumps(identity, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        copied_files = _inventory(staged)
        if copied_files != files:
            raise RuntimeError("release snapshot copy verification failed")
        staged.replace(snapshot_dir)

    return FrozenReleaseSnapshot(snapshot_dir, identity_path, identity)
