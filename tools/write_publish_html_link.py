#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from tools.process_docs.build_publish_latest_site import latest_publish_meta  # noqa: E402
from tools.queue_bound_binding import collect_queue_preflight_errors, resolve_document_link_binding  # noqa: E402
from tools.queue_bound_lark_ops import run_lark_cli_json  # noqa: E402
from tools.queue_contract import HTML_LINK_FIELD  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Write the Vercel publish URL back to Document_link.HTML_link.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--publish-url", required=True, help="Resolved Vercel production URL")
    ap.add_argument(
        "--releases-root",
        default="reports/releases",
        help="Release metadata root, relative to repo root by default.",
    )
    ap.add_argument(
        "--record-id",
        action="append",
        default=[],
        help="Optional Document_link record_id override. Repeat to target multiple rows.",
    )
    return ap.parse_args(argv)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _clean_texts(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return tuple(deduped)


def target_record_ids_from_publish_meta(
    payload: dict[str, Any],
    *,
    explicit_record_ids: tuple[str, ...] = (),
) -> tuple[str, ...]:
    if explicit_record_ids:
        return _clean_texts(explicit_record_ids)
    raw_ids = payload.get("queue_record_ids")
    if isinstance(raw_ids, list):
        return _clean_texts(tuple(str(item) for item in raw_ids))
    raw_id = str(payload.get("queue_record_id") or "").strip()
    return (raw_id,) if raw_id else ()


def version_meta_path(latest_meta_path: Path, payload: dict[str, Any]) -> Path | None:
    version = str(payload.get("version") or "").strip()
    if not version:
        return None
    lang_root = latest_meta_path.parent.parent
    candidate = lang_root / "versions" / version / "publish_meta.json"
    return candidate if candidate.exists() else None


def persist_publish_url(*, latest_meta_path: Path, payload: dict[str, Any], publish_url: str) -> tuple[Path, ...]:
    publish_url = publish_url.strip()
    if not publish_url:
        return ()
    updated_payload = dict(payload)
    updated_payload["publish_url"] = publish_url
    write_json(latest_meta_path, updated_payload)
    written = [latest_meta_path]
    version_path = version_meta_path(latest_meta_path, payload)
    if version_path is not None:
        write_json(version_path, updated_payload)
        written.append(version_path)
    return tuple(written)


def write_publish_html_link(
    *,
    config_path: Path,
    publish_url: str,
    releases_root: Path,
    explicit_record_ids: tuple[str, ...] = (),
) -> int:
    publish_url = publish_url.strip()
    if not publish_url:
        print("[publish-html-link] Skipping writeback because publish_url is empty.")
        return 0

    meta_path = latest_publish_meta(releases_root)
    payload = read_json(meta_path)
    written_meta = persist_publish_url(latest_meta_path=meta_path, payload=payload, publish_url=publish_url)
    if written_meta:
        print(
            "[publish-html-link] Updated publish metadata: "
            + ", ".join(display_path(path) for path in written_meta)
        )

    record_ids = target_record_ids_from_publish_meta(payload, explicit_record_ids=explicit_record_ids)
    if not record_ids:
        print("[publish-html-link] No queue record ids were recorded for the latest publish metadata; skipping HTML_link writeback.")
        return 0

    cfg = load_config(config_path)
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("publish HTML_link writeback preflight failed:\n- " + "\n- ".join(errors))

    binding = resolve_document_link_binding(cfg)
    resolved_cli_bin = cli_bin(cfg)
    identity = phase2_identity()
    field_id_map = fetch_field_id_map(
        cli_bin=resolved_cli_bin,
        base_token=binding.base_token,
        table_id=binding.table_id,
        identity=identity,
        run_lark_cli_json=run_lark_cli_json,
    )
    if HTML_LINK_FIELD not in field_id_map:
        print(f"[publish-html-link] Document_link table does not expose {HTML_LINK_FIELD}; skipping writeback.")
        return 0

    source = LarkCliSource(cli_bin=resolved_cli_bin, identity=identity)
    writeback_record = {HTML_LINK_FIELD: publish_url}
    for record_id in record_ids:
        source.upsert_record(
            base_token=binding.base_token,
            table_id=binding.table_id,
            record_id=record_id,
            record=writeback_record,
        )
        print(f"[publish-html-link] Updated {record_id}: {HTML_LINK_FIELD}={publish_url}")
    return len(record_ids)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = resolve_repo_path(args.config)
    releases_root = resolve_repo_path(args.releases_root)
    try:
        written = write_publish_html_link(
            config_path=config_path,
            publish_url=args.publish_url,
            releases_root=releases_root,
            explicit_record_ids=_clean_texts(tuple(args.record_id)),
        )
    except Exception as exc:
        print(f"[publish-html-link] ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"[publish-html-link] Completed HTML_link writeback for {written} record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
