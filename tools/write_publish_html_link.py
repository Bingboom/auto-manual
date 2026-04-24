#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
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
from tools.queue_contract import HTML_LINK_FIELD, RTD_LINK_FIELD  # noqa: E402

HTML_LINK_FIELD_ALIASES = (
    HTML_LINK_FIELD,
    "HTML link",
    "HTMLLink",
    "HTML链接",
    "HTML 链接",
    "网页链接",
    "网页链接地址",
    "Vercel URL",
    "Vercel链接",
    "Vercel 链接",
)
RTD_LINK_FIELD_ALIASES = (
    RTD_LINK_FIELD,
    "RTD link",
    "RTDLink",
    "RTD链接",
    "RTD 链接",
    "ReadTheDocs_link",
    "Read the Docs link",
    "Read the Docs URL",
    "ReadTheDocs URL",
    "ReadTheDocs链接",
    "Read the Docs链接",
    "文档站链接",
)
_LINKISH_FIELD_TOKENS = ("html", "link", "vercel", "rtd", "readthedocs", "docs", "链接", "网页", "文档")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Write publish URLs back to Document_link.HTML_link / RTD_link.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--publish-url", default="", help="Resolved Vercel production URL")
    ap.add_argument(
        "--rtd-url",
        default=os.environ.get("AUTO_MANUAL_RTD_URL", ""),
        help="Optional stable Read the Docs URL. Defaults to AUTO_MANUAL_RTD_URL when set.",
    )
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


_NON_ALNUM_RE = re.compile(r"[^0-9A-Za-z]+")


def _normalize_field_name(value: str) -> str:
    return _NON_ALNUM_RE.sub("", str(value or "").strip()).lower()


def resolve_field_name(field_id_map: dict[str, str], target_name: str) -> str | None:
    if target_name in field_id_map:
        return target_name
    normalized_target = _normalize_field_name(target_name)
    if not normalized_target:
        return None
    matches = [
        field_name
        for field_name in field_id_map
        if _normalize_field_name(field_name) == normalized_target
    ]
    if not matches:
        return None
    return sorted(matches)[0]


def resolve_html_link_field_name(field_id_map: dict[str, str]) -> str | None:
    for alias in HTML_LINK_FIELD_ALIASES:
        resolved = resolve_field_name(field_id_map, alias)
        if resolved:
            return resolved
    return None


def resolve_rtd_link_field_name(field_id_map: dict[str, str]) -> str | None:
    for alias in RTD_LINK_FIELD_ALIASES:
        resolved = resolve_field_name(field_id_map, alias)
        if resolved:
            return resolved
    return None


def link_like_field_names(field_id_map: dict[str, str], *, extra_tokens: tuple[str, ...] = ()) -> tuple[str, ...]:
    tokens = tuple(token.lower() for token in (*_LINKISH_FIELD_TOKENS[:6], *extra_tokens))
    return tuple(
        sorted(
            field_name
            for field_name in field_id_map
            if any(token in field_name.lower() for token in tokens)
            or any(token in field_name for token in _LINKISH_FIELD_TOKENS[6:])
        )
    )


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


def persist_publish_urls(
    *,
    latest_meta_path: Path,
    payload: dict[str, Any],
    publish_url: str,
    rtd_url: str = "",
) -> tuple[Path, ...]:
    publish_url = publish_url.strip()
    rtd_url = rtd_url.strip()
    if not publish_url and not rtd_url:
        return ()
    updated_payload = dict(payload)
    if publish_url:
        updated_payload["publish_url"] = publish_url
    if rtd_url:
        updated_payload["rtd_url"] = rtd_url
    write_json(latest_meta_path, updated_payload)
    written = [latest_meta_path]
    version_path = version_meta_path(latest_meta_path, payload)
    if version_path is not None:
        write_json(version_path, updated_payload)
        written.append(version_path)
    return tuple(written)


def persist_publish_url(*, latest_meta_path: Path, payload: dict[str, Any], publish_url: str) -> tuple[Path, ...]:
    return persist_publish_urls(
        latest_meta_path=latest_meta_path,
        payload=payload,
        publish_url=publish_url,
        rtd_url="",
    )


def write_link_records(
    *,
    source: Any,
    binding: Any,
    record_ids: tuple[str, ...],
    field_name: str,
    link_url: str,
) -> int:
    writeback_record = {field_name: link_url}
    for record_id in record_ids:
        source.upsert_record(
            base_token=binding.base_token,
            table_id=binding.table_id,
            record_id=record_id,
            record=writeback_record,
        )
        print(f"[publish-html-link] Updated {record_id}: {field_name}={link_url}")
    return len(record_ids)


def write_named_link_field(
    *,
    source: Any,
    binding: Any,
    record_ids: tuple[str, ...],
    field_id_map: dict[str, str],
    canonical_field_name: str,
    field_aliases: tuple[str, ...],
    link_url: str,
    extra_lookup_tokens: tuple[str, ...] = (),
) -> int:
    link_url = link_url.strip()
    if not link_url:
        print(f"[publish-html-link] Skipping {canonical_field_name} writeback because the URL is empty.")
        return 0

    resolved_field_name = None
    for alias in field_aliases:
        resolved_field_name = resolve_field_name(field_id_map, alias)
        if resolved_field_name:
            break
    if resolved_field_name:
        return write_link_records(
            source=source,
            binding=binding,
            record_ids=record_ids,
            field_name=resolved_field_name,
            link_url=link_url,
        )

    nearby_fields = link_like_field_names(field_id_map, extra_tokens=extra_lookup_tokens)
    if nearby_fields:
        print(
            f"[publish-html-link] {canonical_field_name} lookup missed. Nearby link-like fields: "
            + ", ".join(nearby_fields)
        )
    else:
        print(f"[publish-html-link] {canonical_field_name} lookup missed. Field list returned no link-like fields.")

    attempted_fields: list[str] = []
    for fallback_field_name in _clean_texts(field_aliases):
        attempted_fields.append(fallback_field_name)
        try:
            return write_link_records(
                source=source,
                binding=binding,
                record_ids=record_ids,
                field_name=fallback_field_name,
                link_url=link_url,
            )
        except Exception as exc:
            print(
                f"[publish-html-link] Fallback writeback via {fallback_field_name} failed: {exc}",
                file=sys.stderr,
            )

    print(
        f"[publish-html-link] Document_link table does not expose a writable {canonical_field_name} field; "
        f"attempted={', '.join(attempted_fields)}. Skipping writeback."
    )
    return 0


def write_publish_html_link(
    *,
    config_path: Path,
    publish_url: str,
    rtd_url: str = "",
    releases_root: Path,
    explicit_record_ids: tuple[str, ...] = (),
) -> int:
    publish_url = publish_url.strip()
    rtd_url = rtd_url.strip()
    if not publish_url and not rtd_url:
        print("[publish-html-link] Skipping writeback because both publish_url and rtd_url are empty.")
        return 0

    meta_path = latest_publish_meta(releases_root)
    payload = read_json(meta_path)
    written_meta = persist_publish_urls(
        latest_meta_path=meta_path,
        payload=payload,
        publish_url=publish_url,
        rtd_url=rtd_url,
    )
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
    source = LarkCliSource(cli_bin=resolved_cli_bin, identity=identity)
    field_id_map = fetch_field_id_map(
        cli_bin=resolved_cli_bin,
        base_token=binding.base_token,
        table_id=binding.table_id,
        identity=identity,
        run_lark_cli_json=run_lark_cli_json,
    )
    html_written = write_named_link_field(
        source=source,
        binding=binding,
        record_ids=record_ids,
        field_id_map=field_id_map,
        canonical_field_name=HTML_LINK_FIELD,
        field_aliases=HTML_LINK_FIELD_ALIASES,
        link_url=publish_url,
        extra_lookup_tokens=("html", "vercel"),
    )
    rtd_written = write_named_link_field(
        source=source,
        binding=binding,
        record_ids=record_ids,
        field_id_map=field_id_map,
        canonical_field_name=RTD_LINK_FIELD,
        field_aliases=RTD_LINK_FIELD_ALIASES,
        link_url=rtd_url,
        extra_lookup_tokens=("rtd", "read the docs", "文档站"),
    )
    return max(html_written, rtd_written)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = resolve_repo_path(args.config)
    releases_root = resolve_repo_path(args.releases_root)
    try:
        written = write_publish_html_link(
            config_path=config_path,
            publish_url=args.publish_url,
            rtd_url=args.rtd_url,
            releases_root=releases_root,
            explicit_record_ids=_clean_texts(tuple(args.record_id)),
        )
    except Exception as exc:
        print(f"[publish-html-link] ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"[publish-html-link] Completed publish link writeback for {written} record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
