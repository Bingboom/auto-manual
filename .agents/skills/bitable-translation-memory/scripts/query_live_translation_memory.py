from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.translation_memory import (  # noqa: E402
    TranslationMemoryEntry,
    normalize_language,
    payload_to_json,
    query_translation_memory_entries,
    render_translation_memory_payload,
    render_translation_prompt_context,
    split_translation_units,
)

DEFAULT_WIKI_TOKEN = "JKVAwNWlbilFiXkFc99cmRMPnhd"
DEFAULT_TABLE_ID = "tblnst8YURfRB1gY"
DEFAULT_VIEW_ID = "veweqW2fQv"
DEFAULT_PAGE_SIZE = 200
DEFAULT_MAX_RECORDS = 2000


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query the live Feishu Translation_Memory table as OpenClaw translation context.")
    parser.add_argument("--query-text", required=True, help="Phrase or sentence to search across all language columns")
    parser.add_argument("--source-lang", default="en", help="Source language column to match against")
    parser.add_argument("--target-lang", dest="target_lang", default=None, help="Target language column to return")
    parser.add_argument("--lang", dest="target_lang", default=None, help="Alias for --target-lang")
    parser.add_argument("--limit", type=int, default=8, help="Maximum unique matched sentence pairs to return")
    parser.add_argument("--per-unit-limit", type=int, default=3, help="Maximum candidates per split source unit")
    parser.add_argument("--format", choices=("markdown", "json", "prompt"), default="markdown", help="Output format")
    parser.add_argument("--no-split", dest="split_units", action="store_false", help="Treat the whole input as one query unit")
    parser.set_defaults(split_units=True)
    parser.add_argument("--wiki-token", default=DEFAULT_WIKI_TOKEN, help="Wiki node token for the translation-memory base")
    parser.add_argument("--table-id", default=DEFAULT_TABLE_ID, help="Bitable table id for sentence pairs")
    parser.add_argument("--view-id", default=DEFAULT_VIEW_ID, help="Bitable view id to read records from")
    parser.add_argument("--base-token", default=None, help="Optional base token override; skips wiki node resolution")
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS, help="Safety cap while paginating record-list")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_lang = normalize_language(args.source_lang) or "en"
    target_lang = normalize_language(args.target_lang)
    cli = resolve_lark_cli()
    base_token = args.base_token or resolve_base_token(cli=cli, wiki_token=args.wiki_token)
    language_fields = get_table_language_fields(cli=cli, base_token=base_token, table_id=args.table_id)
    rows = list_records(
        cli=cli,
        base_token=base_token,
        table_id=args.table_id,
        view_id=args.view_id,
        max_records=args.max_records,
    )
    entries = build_sentence_pair_entries(rows, language_fields=language_fields)
    query_units = split_translation_units(args.query_text) if args.split_units else [" ".join(args.query_text.split())]
    unit_matches = []
    seen_entry_keys: set[tuple[str, str, str]] = set()
    unique_entries: list[TranslationMemoryEntry] = []
    for source_unit in query_units:
        matched = query_translation_memory_entries(
            entries,
            query_text=source_unit,
            preferred_lang=target_lang,
            source_lang=source_lang,
            target_lang=target_lang,
            limit=args.per_unit_limit,
        )
        for entry in matched:
            key = (entry.table, entry.row_key or "", entry.source_text)
            if key not in seen_entry_keys:
                seen_entry_keys.add(key)
                unique_entries.append(entry)
        unit_matches.append(
            {
                "source_unit": source_unit,
                "match_count": len(matched),
                "entries": [entry.to_dict() for entry in matched],
            }
        )
    if len(unique_entries) > args.limit:
        unique_entries = unique_entries[: args.limit]
    payload = {
        "query_text": args.query_text,
        "source_lang": source_lang,
        "preferred_lang": target_lang,
        "target_lang": target_lang,
        "snapshot_root": f"lark-base:{args.table_id}/{args.view_id}",
        "query_units": query_units,
        "unit_matches": unit_matches,
        "match_count": sum(group["match_count"] for group in unit_matches),
        "unique_entry_count": len(unique_entries),
        "entries": [entry.to_dict() for entry in unique_entries],
    }
    if args.format == "json":
        emit(payload_to_json(payload))
        return 0
    if args.format == "prompt":
        emit(
            render_translation_prompt_context(
                query_text=args.query_text,
                source_lang=source_lang,
                target_lang=target_lang,
                memory_source=payload["snapshot_root"],
                unit_matches=unit_matches,
            )
        )
        return 0
    emit(render_translation_memory_payload(payload))
    return 0


def resolve_lark_cli() -> str:
    for candidate in ("lark-cli.cmd", "lark-cli", "lark-cli.ps1"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError("lark-cli was not found in PATH.")


def resolve_base_token(*, cli: str, wiki_token: str) -> str:
    payload = run_lark_json(
        [cli, "wiki", "spaces", "get_node", "--params", json.dumps({"token": wiki_token}, ensure_ascii=False)]
    )
    return str(payload["data"]["node"]["obj_token"])


def get_table_language_fields(*, cli: str, base_token: str, table_id: str) -> list[str]:
    payload = run_lark_json([cli, "base", "+table-get", "--base-token", base_token, "--table-id", table_id])
    fields = payload["data"]["fields"]
    return [str(field["field_name"]) for field in fields if str(field.get("type")) == "text"]


def list_records(*, cli: str, base_token: str, table_id: str, view_id: str, max_records: int) -> list[dict[str, object]]:
    offset = 0
    rows: list[dict[str, object]] = []
    while offset < max_records:
        payload = run_lark_json(
            [
                cli,
                "base",
                "+record-list",
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--view-id",
                view_id,
                "--offset",
                str(offset),
                "--limit",
                str(min(DEFAULT_PAGE_SIZE, max_records - offset)),
            ]
        )
        data = payload["data"]
        field_names = [str(name) for name in data.get("fields", [])]
        record_ids = [str(item) for item in data.get("record_id_list", [])]
        row_values = data.get("data", [])
        for record_id, values in zip(record_ids, row_values):
            row = {"record_id": record_id}
            for field_name, value in zip(field_names, values):
                row[field_name] = value
            rows.append(row)
        if not data.get("has_more"):
            break
        offset += len(record_ids)
    return rows


def build_sentence_pair_entries(rows: list[dict[str, object]], *, language_fields: list[str]) -> list[TranslationMemoryEntry]:
    entries: list[TranslationMemoryEntry] = []
    for row in rows:
        translations = {}
        for field_name in language_fields:
            value = str(row.get(field_name) or "").strip()
            if value:
                translations[field_name] = value
        if not translations:
            continue
        source_lang = "en" if translations.get("en") else next(iter(translations.keys()))
        entries.append(
            TranslationMemoryEntry(
                table="translation-memory-bitable",
                entry_type="sentence-pair",
                source_lang=source_lang,
                source_text=translations[source_lang],
                translations=translations,
                row_key=str(row.get("record_id") or ""),
            )
        )
    return entries


def run_lark_json(cmd: list[str]) -> dict[str, object]:
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"lark-cli failed: {' '.join(cmd)}")
    payload = json.loads(completed.stdout)
    if not payload.get("ok", True) and int(payload.get("code", 0) or 0) != 0:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def emit(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
