#!/usr/bin/env python3
"""Write deterministic Read the Docs URLs for Web Publish queue rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.listen_build_queue_lark import fetch_field_id_map  # noqa: E402
from tools.phase2_support import LarkCliSource, cli_bin, load_config, phase2_identity  # noqa: E402
from tools.queue_bound_binding import collect_queue_preflight_errors, resolve_document_link_binding  # noqa: E402
from tools.queue_bound_lark_ops import run_lark_cli_json  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402
from tools.write_publish_html_link import (  # noqa: E402
    display_path,
    resolve_html_link_field_name,
    target_record_ids_from_publish_meta,
    write_html_link_records,
)


DEFAULT_RTD_BASE_URL = "https://ht-doc.readthedocs.io/en/latest"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write Read the Docs Web Publish URLs back to Document_link.HTML_link."
    )
    parser.add_argument("--config", required=True, help="Config YAML path")
    parser.add_argument("--base-url", default=DEFAULT_RTD_BASE_URL)
    parser.add_argument("--releases-root", default="reports/releases")
    parser.add_argument("--record-id", action="append", default=[])
    return parser.parse_args(argv)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()


def latest_web_publish_metadata(releases_root: Path) -> list[Path]:
    return sorted(
        releases_root.glob(
            f"*/*/*/{PathSegments.LATEST}/{PathSegments.WEB}/{PathSegments.PUBLISH_META_JSON}"
        )
    )


def _read_metadata(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Web Publish metadata root must be an object: {path}")
    if str(payload.get("schema_version") or "") != "auto-manual-web-publish/v1":
        raise RuntimeError(f"Unsupported Web Publish metadata schema: {path}")
    return payload


def target_rtd_url(*, base_url: str, payload: dict[str, Any]) -> str:
    model = str(payload.get("model") or "").strip()
    region = str(payload.get("region") or "").strip()
    markdown_path = Path(str(payload.get("md_output_path") or "").strip())
    if not model or not region or not markdown_path.stem:
        raise RuntimeError("Web Publish metadata is missing model, region, or md_output_path")
    return f"{base_url.rstrip('/')}/{model}/{region}/md/{markdown_path.stem}.html"


def persist_rtd_url(*, metadata_path: Path, payload: dict[str, Any], url: str) -> None:
    updated = dict(payload)
    updated["publish_url"] = url
    metadata_path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_web_publish_html_links(
    *,
    config_path: Path,
    base_url: str,
    releases_root: Path,
    explicit_record_ids: tuple[str, ...] = (),
) -> int:
    metadata_paths = latest_web_publish_metadata(releases_root)
    if not metadata_paths:
        raise RuntimeError(f"No Web Publish metadata found under {releases_root}")
    targets: list[tuple[tuple[str, ...], str]] = []
    explicit = {item.strip() for item in explicit_record_ids if item.strip()}
    for metadata_path in metadata_paths:
        payload = _read_metadata(metadata_path)
        recorded_ids = target_record_ids_from_publish_meta(payload)
        if explicit and not explicit.intersection(recorded_ids):
            continue
        record_ids = tuple(sorted(explicit.intersection(recorded_ids))) if explicit else recorded_ids
        if not record_ids:
            continue
        url = target_rtd_url(base_url=base_url, payload=payload)
        persist_rtd_url(metadata_path=metadata_path, payload=payload, url=url)
        print(f"[web-publish-link] Updated metadata: {display_path(metadata_path)} -> {url}")
        targets.append((record_ids, url))
    if explicit and not targets:
        raise RuntimeError(
            "No Web Publish metadata matched the requested queue record ids: "
            + ", ".join(sorted(explicit))
        )

    cfg = load_config(config_path)
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("Web Publish HTML_link writeback preflight failed:\n- " + "\n- ".join(errors))
    binding = resolve_document_link_binding(cfg)
    resolved_cli_bin = cli_bin(cfg)
    identity = phase2_identity()
    source = LarkCliSource(cli_bin=resolved_cli_bin, identity=identity)
    field_id_map = fetch_field_id_map(
        cli_bin=resolved_cli_bin,
        base_token=binding.base_token,
        table_id=binding.table_id,
        identity=identity,
        run_lark_cli_json=run_lark_cli_json,
    )
    field_name = resolve_html_link_field_name(field_id_map)
    if not field_name:
        raise RuntimeError("Document_link does not expose a writable HTML_link field")
    return sum(
        write_html_link_records(
            source=source,
            binding=binding,
            record_ids=record_ids,
            field_name=field_name,
            publish_url=url,
        )
        for record_ids, url in targets
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        written = write_web_publish_html_links(
            config_path=resolve_repo_path(args.config),
            base_url=str(args.base_url),
            releases_root=resolve_repo_path(args.releases_root),
            explicit_record_ids=tuple(str(item).strip() for item in args.record_id if str(item).strip()),
        )
    except Exception as exc:
        print(f"[web-publish-link] ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"[web-publish-link] Completed HTML_link writeback for {written} record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
