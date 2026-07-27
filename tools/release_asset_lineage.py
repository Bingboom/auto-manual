"""Asset lineage for the release manifest, and the publish gate that guards it.

A shipped manual is only as traceable as the images inside it. The prepared
bundle already froze exactly which assets it consumed
(``asset_usage_manifest.json``) and fingerprinted the result
(``bundle_sha256``); this module lifts that record into the release manifest
so a released PDF can be traced back to the bytes of every illustration, the
registry snapshot they were resolved against, and the review status they
carried at the time.

The publish gate reads the same record. It blocks on a **used** asset that is
not ``✅成品`` — a temporary stand-in, a missing/debt row, or a quarantined
one must never reach print, where nothing can be corrected afterwards. It
deliberately does not block on ``legacy-path`` images: those are references
that never entered the registry (today they come from data-generated pages),
so blocking would stop every publish rather than surface the debt. They are
counted into the manifest instead, which keeps the number visible in release
lineage and lets it be ratcheted down later.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
# Flush so the gate line interleaves correctly with subprocess output.
_print = functools.partial(print, flush=True)
APPROVED_STATUS = "✅成品"
LEGACY_KIND = "legacy-path"
USAGE_MANIFEST_FILENAME = "asset_usage_manifest.json"
BUNDLE_MANIFEST_FILENAME = "bundle_manifest.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def collect_asset_lineage(*, bundle_dir: Path) -> dict[str, Any] | None:
    """Summarize one prepared bundle's frozen asset usage for the manifest.

    Returns ``None`` when the bundle has no usage manifest, so a target that
    predates asset finalization still produces a release manifest instead of
    failing — absence of lineage is reported by its absence, not by a crash.
    """
    usage = _read_json(bundle_dir / USAGE_MANIFEST_FILENAME)
    if usage is None:
        return None
    entries = usage.get("assets")
    if not isinstance(entries, list):
        return None

    used: list[dict[str, Any]] = []
    legacy_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        asset_key = entry.get("asset_key")
        if not asset_key or entry.get("reference_kind") == LEGACY_KIND:
            legacy_count += 1
            continue
        used.append(
            {
                "asset_key": asset_key,
                "format": entry.get("format"),
                "sha256": entry.get("sha256"),
                "status": entry.get("status"),
                "source": entry.get("source"),
                "staged_path": entry.get("staged_path"),
            }
        )
    used.sort(key=lambda row: (str(row["asset_key"]), str(row.get("staged_path") or "")))

    bundle_manifest = _read_json(bundle_dir / BUNDLE_MANIFEST_FILENAME) or {}
    snapshot = usage.get("registry_snapshot")
    return {
        "schema_version": SCHEMA_VERSION,
        "usage_manifest_schema_version": usage.get("schema_version"),
        "bundle_sha256": bundle_manifest.get("bundle_sha256"),
        "registry_snapshot": snapshot if isinstance(snapshot, dict) else None,
        "registry_asset_count": len(used),
        "legacy_path_count": legacy_count,
        "assets": used,
    }


def publish_blockers(lineage: dict[str, Any] | None) -> tuple[str, ...]:
    """Reasons this bundle must not be published, most specific first."""
    if lineage is None:
        return (
            "the prepared bundle has no asset usage manifest; "
            "publish requires frozen asset lineage",
        )
    blockers = [
        f"asset {row['asset_key']} is {row['status']}; "
        f"publish requires {APPROVED_STATUS}"
        for row in lineage.get("assets", ())
        if row.get("status") != APPROVED_STATUS
    ]
    return tuple(sorted(blockers))


def csv_columns(lineage: dict[str, Any] | None) -> dict[str, str]:
    """Flatten the lineage into scalar release-CSV columns (the I3 shape)."""
    record = lineage or {}
    snapshot = record.get("registry_snapshot") or {}
    return {
        "assets_registry_count": str(record.get("registry_asset_count") or 0),
        "assets_legacy_path_count": str(record.get("legacy_path_count") or 0),
        "assets_bundle_sha256": str(record.get("bundle_sha256") or ""),
        "assets_registry_snapshot_sha256": str(snapshot.get("sha256") or ""),
    }


def publish_asset_gate_for_target(
    *,
    docs_dir: Path,
    docs_build_dir: Path | None,
    target: tuple[str, str, str | None],
    printer=_print,
) -> None:
    """Resolve the prepared bundle for one publish target and gate it.

    Path resolution lives here rather than in the entrypoint so build.py
    stays a thin injector.
    """
    from tools.gen_index_bundle import bundle_dir_for_target
    from tools.utils.path_utils import docs_build_dir_of

    model, region, lang = target
    run_publish_asset_gate(
        bundle_dir=bundle_dir_for_target(
            docs_dir=docs_dir,
            docs_build_dir=docs_build_dir or docs_build_dir_of(docs_dir),
            model=model,
            region=region,
            lang=lang,
        ),
        printer=printer,
    )


def run_publish_asset_gate(*, bundle_dir: Path, printer=_print) -> None:
    """Fail the publish before any artifact is released, or report and pass."""
    lineage = collect_asset_lineage(bundle_dir=bundle_dir)
    blockers = publish_blockers(lineage)
    if blockers:
        for reason in blockers:
            printer(f"[publish-assets] BLOCKED {reason}")
        raise RuntimeError(
            f"publish blocked by {len(blockers)} asset lineage issue(s)"
        )
    record = lineage or {}
    printer(
        "[publish-assets] OK: "
        f"{record.get('registry_asset_count', 0)} registry asset(s), "
        f"{record.get('legacy_path_count', 0)} legacy path(s), "
        f"bundle {str(record.get('bundle_sha256') or '')[:12]}"
    )
