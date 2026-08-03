#!/usr/bin/env python3
"""Drop published artifacts into a local delivery outbox with a signed manifest.

The outbox is the hand-off point between this repo and the delivery agent that
uploads to DingTalk: the build writes files plus one `delivery_manifest.json`,
the agent reads them, uploads, registers the row, and writes its own
`status.json` beside the manifest. Ownership is one-way — this repo only ever
creates the manifest and never mutates it, so agent progress can never be
confused with build output.

The outbox root is env-gated (`AUTO_MANUAL_DELIVERY_OUTBOX_ROOT`). With no root
configured this module is inert, which is what keeps CI and every existing
worker unchanged. The root is expected to live outside the git tree (the mirror
checkout ignores `/output/`), because delivery payloads are runtime artifacts,
not source.

Fail-closed choices: a declared artifact that is missing aborts the drop rather
than shipping a partial payload, an unmapped DingTalk target aborts before any
file is copied, and job directories are never silently reused — a colliding job
id is an error, since two different builds sharing one outbox slot would make
the manifest lie about which files belong to which build.

Recorded provenance is deliberately literal: `git_ref` is the queue row's
Git_ref value, not a resolved commit sha. The build worktree is removed before
this point, so resolving it here would mean re-resolving a ref that may have
moved — a wrong sha is worse than an honest ref.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.dingtalk_delivery_map import (  # noqa: E402 - after bootstrap
    DingTalkDeliveryTarget,
    resolve_delivery_target,
)
from tools.manual_ir.hashing import file_sha256  # noqa: E402 - after bootstrap

DELIVERY_OUTBOX_ROOT_ENV = "AUTO_MANUAL_DELIVERY_OUTBOX_ROOT"
DELIVERY_MANIFEST_FILENAME = "delivery_manifest.json"
DELIVERY_MANIFEST_SCHEMA_VERSION = 1
DELIVERY_STATUS_PENDING = "pending"

_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class DeliveryOutboxResult:
    job_dir: Path
    manifest_path: Path
    file_count: int


def delivery_outbox_root(
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> Path | None:
    """Return the configured outbox root, or None when delivery is not enabled."""

    env = environ if environ is not None else os.environ
    raw = str(env.get(DELIVERY_OUTBOX_ROOT_ENV, "")).strip()
    return Path(raw).expanduser() if raw else None


def _safe_segment(value: str, *, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError(f"delivery outbox job id needs a non-empty {label}")
    if not _SAFE_SEGMENT_RE.match(text):
        raise RuntimeError(
            f"delivery outbox job id rejects {label}={text!r}: "
            "only letters, digits, dot, underscore and hyphen are allowed"
        )
    return text


def build_job_id(
    *,
    model: str,
    region: str,
    lang: str,
    version: str,
    built_at: datetime,
) -> str:
    """Build a filesystem-safe, build-unique job id."""

    parts = (
        _safe_segment(model, label="model"),
        _safe_segment(region, label="region"),
        _safe_segment(lang, label="lang"),
        _safe_segment(version, label="version"),
        built_at.astimezone().strftime("%Y%m%dT%H%M%S%z"),
    )
    return "_".join(parts)


def _file_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"delivery outbox artifact is missing: {path}")
    return {
        "name": path.name,
        "size": path.stat().st_size,
        "sha256": file_sha256(path),
    }


def build_delivery_manifest(
    *,
    job_id: str,
    model: str,
    region: str,
    lang: str,
    version: str,
    git_ref: str,
    workflow_action: str,
    built_at: datetime,
    queue_record_ids: tuple[str, ...],
    document_link_url: str,
    files: list[Path],
    delivery_target: DingTalkDeliveryTarget,
) -> dict[str, Any]:
    """Build the hand-off contract describing one delivery payload."""

    return {
        "schema_version": DELIVERY_MANIFEST_SCHEMA_VERSION,
        "status": DELIVERY_STATUS_PENDING,
        "job_id": job_id,
        "source": {
            "model": model,
            "region": region,
            "lang": lang,
            "version": version,
            "git_ref": git_ref,
            "workflow_action": workflow_action,
            "built_at": built_at.astimezone().isoformat(),
            "queue_record_ids": list(queue_record_ids),
            "document_link_url": document_link_url,
        },
        "dingtalk_target": delivery_target.as_manifest_fields(),
        "files": [_file_record(path) for path in files],
    }


def write_delivery_outbox(
    *,
    outbox_root: Path,
    model: str,
    region: str,
    lang: str,
    version: str,
    git_ref: str,
    workflow_action: str,
    built_at: datetime,
    queue_record_ids: tuple[str, ...] = (),
    document_link_url: str = "",
    files: list[Path],
    delivery_map_path: Path | None = None,
    root: Path | None = None,
) -> DeliveryOutboxResult:
    """Copy artifacts plus a manifest into a fresh outbox job directory."""

    if not files:
        raise RuntimeError("delivery outbox needs at least one artifact to deliver")

    delivery_target = resolve_delivery_target(
        model=model,
        region=region,
        lang=lang,
        path=delivery_map_path,
        root=root,
    )
    job_id = build_job_id(
        model=model,
        region=region,
        lang=lang,
        version=version,
        built_at=built_at,
    )
    manifest = build_delivery_manifest(
        job_id=job_id,
        model=model,
        region=region,
        lang=lang,
        version=version,
        git_ref=git_ref,
        workflow_action=workflow_action,
        built_at=built_at,
        queue_record_ids=queue_record_ids,
        document_link_url=document_link_url,
        files=files,
        delivery_target=delivery_target,
    )

    job_dir = outbox_root / job_id
    if job_dir.exists():
        raise RuntimeError(
            f"delivery outbox job directory already exists: {job_dir}; "
            "clear the consumed job or wait for the next build timestamp"
        )
    job_dir.mkdir(parents=True)
    for path in files:
        shutil.copy2(path, job_dir / path.name)

    manifest_path = job_dir / DELIVERY_MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    verify_delivery_manifest(manifest_path)
    return DeliveryOutboxResult(
        job_dir=job_dir,
        manifest_path=manifest_path,
        file_count=len(files),
    )


def verify_delivery_manifest(manifest_path: Path) -> dict[str, Any]:
    """Re-read a written manifest and check every declared file landed intact."""

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != DELIVERY_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"delivery manifest schema_version mismatch: {manifest_path}"
        )
    records = payload.get("files")
    if not isinstance(records, list) or not records:
        raise RuntimeError(f"delivery manifest declares no files: {manifest_path}")
    for record in records:
        name = str(record.get("name") or "").strip()
        if not name:
            raise RuntimeError(f"delivery manifest has an unnamed file: {manifest_path}")
        delivered = manifest_path.parent / name
        if not delivered.is_file():
            raise RuntimeError(f"delivery outbox is missing declared file: {delivered}")
        if file_sha256(delivered) != record.get("sha256"):
            raise RuntimeError(f"delivery outbox file digest mismatch: {delivered}")
    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify a delivery outbox manifest against its files.",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help=f"path to a {DELIVERY_MANIFEST_FILENAME} written by a build",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    manifest_path = Path(args.manifest).expanduser()
    payload = verify_delivery_manifest(manifest_path)
    target = payload.get("dingtalk_target", {})
    print(
        f"[delivery-outbox] {payload.get('job_id')} verified: "
        f"{len(payload.get('files', []))} file(s) -> "
        f"{target.get('project_code')}/{target.get('safety_regulation')}/{target.get('language')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
