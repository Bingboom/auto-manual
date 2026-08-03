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

A job is assembled under a `.partial` directory and renamed into place only
after its manifest verifies, so a consumable job directory never exists in a
half-written state. Any failure after the partial directory appears removes it;
the outbox therefore holds finished jobs or nothing, never a `status: pending`
manifest describing a payload the build already rejected.

Other fail-closed choices: a declared artifact that is missing aborts before
anything is created, two artifacts sharing one basename abort rather than
silently overwriting each other inside the job directory, and a colliding job
id is an error since two builds sharing one slot would make the manifest lie.

`delivery_key` is the consumer's idempotency handle. A rebuild of the same
version legitimately produces a second job, and a runner that loses its claim
mid-publish can leave a job whose row never got written, so the agent must
dedupe rather than assume one job equals one delivery. Closing that window
repo-side would cost an extra Feishu read per publish to prevent a duplicate
the key already collapses, which is not worth it.

Recorded provenance is deliberately literal: `git_ref` is the queue row's
Git_ref value, not a resolved commit sha. The build worktree is removed before
this point, so resolving it here would mean re-resolving a ref that may have
moved — a wrong sha is worse than an honest ref.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
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
    DeliveryTargetNotMapped,
    DingTalkDeliveryTarget,
    resolve_delivery_target,
)
from tools.manual_ir.hashing import (  # noqa: E402 - after bootstrap
    file_sha256,
    value_sha256,
)

DELIVERY_OUTBOX_ROOT_ENV = "AUTO_MANUAL_DELIVERY_OUTBOX_ROOT"
DELIVERY_MANIFEST_FILENAME = "delivery_manifest.json"
DELIVERY_MANIFEST_SCHEMA_VERSION = 1
DELIVERY_STATUS_FILENAME = "status.json"
PARTIAL_JOB_SUFFIX = ".partial"

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
    version: str,
    built_at: datetime,
) -> str:
    """Build a filesystem-safe, build-unique job id.

    The timestamp is normalized to UTC with a `Z` suffix rather than `%z`: a
    numeric offset renders as `+0800`, and `+` is a reserved character that
    decodes to a space in URLs and form encodings — the job id travels into row
    status notes and the delivery agent's paths, so it stays in the safe set.
    """

    parts = (
        _safe_segment(model, label="model"),
        _safe_segment(region, label="region"),
        _safe_segment(version, label="version"),
        built_at.astimezone().astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
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


def _reject_basename_collisions(files: list[Path]) -> None:
    """Refuse two artifacts that would land on one name inside the job dir."""

    seen: dict[str, Path] = {}
    for path in files:
        clash = seen.get(path.name)
        if clash is not None:
            raise RuntimeError(
                "delivery outbox artifacts collide on one file name "
                f"{path.name!r}: {clash} and {path}"
            )
        seen[path.name] = path


def build_delivery_key(
    *,
    delivery_target: DingTalkDeliveryTarget,
    model: str,
    region: str,
    version: str,
    file_records: list[dict[str, Any]],
) -> str:
    """Stable idempotency handle for the consumer to dedupe deliveries on.

    Derived from the already-computed file digests rather than re-reading the
    artifacts, so a delivery drop hashes each file exactly once.
    """

    payload = "|".join(
        (
            delivery_target.project_code,
            delivery_target.safety_regulation,
            model,
            region,
            version,
            *(
                f"{record['name']}:{record['sha256']}"
                for record in sorted(file_records, key=lambda item: str(item["name"]))
            ),
        )
    )
    return value_sha256(payload)


def build_delivery_manifest(
    *,
    job_id: str,
    model: str,
    region: str,
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

    # No progress field lives here: the manifest is immutable build output and
    # the delivery agent tracks progress in its own status.json. A frozen
    # "pending" in here would read as live state and mislead every consumer.
    # File records first: a missing artifact must surface as this module's own
    # error before anything else touches the payload.
    file_records = [_file_record(path) for path in files]
    return {
        "schema_version": DELIVERY_MANIFEST_SCHEMA_VERSION,
        "job_id": job_id,
        "delivery_key": build_delivery_key(
            delivery_target=delivery_target,
            model=model,
            region=region,
            version=version,
            file_records=file_records,
        ),
        "source": {
            "model": model,
            "region": region,
            "version": version,
            "git_ref": git_ref,
            "workflow_action": workflow_action,
            "built_at": built_at.astimezone().isoformat(),
            "queue_record_ids": list(queue_record_ids),
            "document_link_url": document_link_url,
        },
        "dingtalk_target": delivery_target.as_manifest_fields(),
        "files": file_records,
    }


def write_delivery_outbox(
    *,
    outbox_root: Path,
    model: str,
    region: str,
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
    """Assemble one outbox job atomically: build under .partial, then rename."""

    if not files:
        raise RuntimeError("delivery outbox needs at least one artifact to deliver")
    _reject_basename_collisions(files)

    delivery_target = resolve_delivery_target(
        model=model,
        region=region,
        path=delivery_map_path,
        root=root,
    )
    job_id = build_job_id(
        model=model,
        region=region,
        version=version,
        built_at=built_at,
    )
    manifest = build_delivery_manifest(
        job_id=job_id,
        model=model,
        region=region,
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
    staging_dir = outbox_root / f"{job_id}{PARTIAL_JOB_SUFFIX}"
    if job_dir.exists():
        raise RuntimeError(
            f"delivery outbox job directory already exists: {job_dir}; "
            "clear the consumed job or wait for the next build timestamp"
        )
    if staging_dir.exists():
        shutil.rmtree(staging_dir)

    # Everything below assembles inside staging_dir so a consumable job never
    # exists half-written; any failure removes it rather than publishing a
    # pending manifest for a payload this build already rejected.
    try:
        staging_dir.mkdir(parents=True)
        for path in files:
            shutil.copy2(path, staging_dir / path.name)
        staging_manifest = staging_dir / DELIVERY_MANIFEST_FILENAME
        staging_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        verify_delivery_manifest(staging_manifest)
        staging_dir.replace(job_dir)
    except BaseException:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return DeliveryOutboxResult(
        job_dir=job_dir,
        manifest_path=job_dir / DELIVERY_MANIFEST_FILENAME,
        file_count=len(files),
    )


def publish_delivery_files(
    *,
    artifact_output_path: Path | None,
    word_output_path: Path | None,
    pdf_output_path: Path | None,
    md_output_path: Path | None,
) -> list[Path]:
    """Pick the deliverable files for a publish drop, de-duplicated, order stable.

    Directory outputs (latex/, html/) are intentionally excluded: the DingTalk
    delivery rows carry a print PDF and its companion documents, and copying
    whole render trees into every job would bloat the outbox without a consumer.
    """

    ordered = [pdf_output_path, artifact_output_path, word_output_path, md_output_path]
    selected: list[Path] = []
    seen: set[Path] = set()
    for path in ordered:
        if path is None or not path.is_file():
            continue
        resolved = path.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        selected.append(path)
    return selected


def drop_publish_delivery_outbox(
    *,
    model: str,
    region: str,
    version: str,
    git_ref: str,
    workflow_action: str,
    built_at: datetime,
    queue_record_ids: tuple[str, ...],
    document_link_url: str,
    artifact_output_path: Path | None,
    word_output_path: Path | None,
    pdf_output_path: Path | None,
    md_output_path: Path | None,
    stderr: Any = sys.stderr,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> tuple[str, ...]:
    """Best-effort outbox drop for one published group; returns row status notes.

    This is the queue's only entry point and it never raises: the artifact has
    already reached the knowledge base by this point, so a delivery-side problem
    must not turn a good build into a failed row. Outcomes are reported as row
    status notes so nothing hides in the logs:

    - no note at all when delivery is not configured,
    - `delivery_outbox=skipped` when this target is deliberately not delivered
      (another product line, or a region with no DingTalk row yet) — a good
      build of an undelivered target is not a failure and must not be alarmed,
    - `delivery_outbox=failed` only when a *mapped* target could not be dropped.
    """

    try:
        outbox_root = delivery_outbox_root(environ=environ)
    except Exception as exc:  # noqa: BLE001 - a bad env value must not fail the row
        # e.g. `~someone/outbox` where that user does not exist on this host:
        # Path.expanduser() raises, and this used to escape into the queue.
        message = str(exc).strip() or exc.__class__.__name__
        print(
            f"[build-queue] WARNING delivery outbox root is unusable: {message}",
            file=stderr,
        )
        return ("delivery_outbox=failed", f"delivery_outbox_error={message}")
    if outbox_root is None:
        return ()

    try:
        files = publish_delivery_files(
            artifact_output_path=artifact_output_path,
            word_output_path=word_output_path,
            pdf_output_path=pdf_output_path,
            md_output_path=md_output_path,
        )
        result = write_delivery_outbox(
            outbox_root=outbox_root,
            model=model,
            region=region,
            version=version,
            git_ref=git_ref,
            workflow_action=workflow_action,
            built_at=built_at,
            queue_record_ids=queue_record_ids,
            document_link_url=document_link_url,
            files=files,
        )
    except DeliveryTargetNotMapped as exc:
        message = str(exc).strip() or exc.__class__.__name__
        print(
            f"[build-queue] delivery outbox skipped for {model}/{region}: {message}",
            file=stderr,
        )
        return ("delivery_outbox=skipped",)
    except Exception as exc:  # noqa: BLE001 - side channel must not fail the row
        message = str(exc).strip() or exc.__class__.__name__
        print(
            f"[build-queue] WARNING delivery outbox drop failed for "
            f"{model}/{region}: {message}",
            file=stderr,
        )
        return ("delivery_outbox=failed", f"delivery_outbox_error={message}")

    print(
        f"[build-queue] delivery outbox {result.job_dir.name}: "
        f"{result.file_count} file(s) -> {result.job_dir}"
    )
    return ("delivery_outbox=ok", f"delivery_outbox_job={result.job_dir.name}")


def verify_delivery_manifest(manifest_path: Path) -> dict[str, Any]:
    """Re-read a written manifest and check every declared file landed intact."""

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != DELIVERY_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"delivery manifest schema_version mismatch: {manifest_path}"
        )
    if not str(payload.get("delivery_key") or "").strip():
        raise RuntimeError(f"delivery manifest has no delivery_key: {manifest_path}")

    target = payload.get("dingtalk_target")
    if not isinstance(target, dict):
        raise RuntimeError(f"delivery manifest has no dingtalk_target: {manifest_path}")
    for field in ("project_code", "safety_regulation"):
        if not str(target.get(field) or "").strip():
            raise RuntimeError(
                f"delivery manifest dingtalk_target is missing {field}: {manifest_path}"
            )
    if not isinstance(target.get("languages"), list) or not target["languages"]:
        raise RuntimeError(
            f"delivery manifest dingtalk_target lists no languages: {manifest_path}"
        )

    source = payload.get("source")
    if not isinstance(source, dict):
        raise RuntimeError(f"delivery manifest has no source block: {manifest_path}")
    for field in ("model", "region", "version"):
        if not str(source.get(field) or "").strip():
            raise RuntimeError(
                f"delivery manifest source is missing {field}: {manifest_path}"
            )

    records = payload.get("files")
    if not isinstance(records, list) or not records:
        raise RuntimeError(f"delivery manifest declares no files: {manifest_path}")
    for record in records:
        name = str(record.get("name") or "").strip()
        if not name:
            raise RuntimeError(f"delivery manifest has an unnamed file: {manifest_path}")
        # A declared name is a plain file name inside the job directory. Verify
        # would otherwise follow a tampered "../.." into arbitrary paths.
        if name != Path(name).name or name in {".", ".."}:
            raise RuntimeError(
                f"delivery manifest file name must be a plain file name, got {name!r}: "
                f"{manifest_path}"
            )
        delivered = manifest_path.parent / name
        if not delivered.is_file():
            raise RuntimeError(f"delivery outbox is missing declared file: {delivered}")
        if file_sha256(delivered) != record.get("sha256"):
            raise RuntimeError(f"delivery outbox file digest mismatch: {delivered}")
        declared_size = record.get("size")
        if isinstance(declared_size, int) and delivered.stat().st_size != declared_size:
            raise RuntimeError(f"delivery outbox file size mismatch: {delivered}")
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
        f"{target.get('project_code')}/{target.get('safety_regulation')} "
        f"[{', '.join(str(item) for item in target.get('languages', []))}]"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
