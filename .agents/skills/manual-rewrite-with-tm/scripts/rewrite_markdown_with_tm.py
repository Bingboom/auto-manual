#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[4]
QUERY_SCRIPT = REPO_ROOT / '.agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py'
DEFAULT_TERM_TABLE = REPO_ROOT / '.agents/skills/manual-rewrite-with-tm/references/term-priority.example.tsv'
DEFAULT_TERM_SOURCE = REPO_ROOT / '.agents/skills/manual-rewrite-with-tm/references/term-source.md'
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?。！？])\s+(?=(?:[A-Z0-9#*`\[]|\*\*|==))')
TERM_CACHE_SCHEMA = 1
TERM_CACHE_TTL_SECONDS = 900


@dataclass
class Segment:
    kind: str
    text: str


@dataclass
class FeishuTermSource:
    wiki_token: str
    table_id: str
    view_id: str
    wiki_url: str = ''


def run_tm_query(text: str, source_lang: str, target_lang: str) -> str:
    cmd = [
        'python3',
        str(QUERY_SCRIPT),
        '--query-text', text,
        '--source-lang', source_lang,
        '--target-lang', target_lang,
        '--format', 'prompt',
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'translation memory query failed')
    return proc.stdout


def resolve_lark_cli() -> str:
    for candidate in ('lark-cli.cmd', 'lark-cli', 'lark-cli.ps1'):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError('lark-cli was not found in PATH.')


def run_lark_json(cmd: List[str]) -> dict:
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"lark-cli failed: {' '.join(cmd)}")
    payload = json.loads(completed.stdout)
    if not payload.get('ok', True) and int(payload.get('code', 0) or 0) != 0:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def resolve_cache_dir() -> Path:
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Caches' / 'auto-manual' / 'manual-rewrite-with-tm'
    xdg_cache_home = os.environ.get('XDG_CACHE_HOME')
    if xdg_cache_home:
        return Path(xdg_cache_home) / 'auto-manual' / 'manual-rewrite-with-tm'
    if os.name == 'nt':
        local_app_data = os.environ.get('LOCALAPPDATA')
        if local_app_data:
            return Path(local_app_data) / 'auto-manual' / 'manual-rewrite-with-tm'
    return Path.home() / '.cache' / 'auto-manual' / 'manual-rewrite-with-tm'


def parse_term_source_md(path: Path) -> Optional[FeishuTermSource]:
    if not path.exists():
        return None
    values: Dict[str, str] = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'-\s+(wiki_url|wiki_token|table_id|view_id):\s+`(.+?)`\s*$', line.strip())
        if m:
            values[m.group(1)] = m.group(2)
    if values.get('wiki_token') and values.get('table_id') and values.get('view_id'):
        return FeishuTermSource(
            wiki_token=values['wiki_token'],
            table_id=values['table_id'],
            view_id=values['view_id'],
            wiki_url=values.get('wiki_url', ''),
        )
    return None


def resolve_base_token(cli: str, wiki_token: str) -> str:
    payload = run_lark_json([cli, 'wiki', 'spaces', 'get_node', '--params', json.dumps({'token': wiki_token}, ensure_ascii=False)])
    return str(payload['data']['node']['obj_token'])


def list_records(cli: str, base_token: str, table_id: str, view_id: str, max_records: int = 2000) -> List[dict]:
    page_size = 200
    offset = 0
    rows: List[dict] = []
    while offset < max_records:
        payload = run_lark_json([
            cli, 'base', '+record-list',
            '--base-token', base_token,
            '--table-id', table_id,
            '--view-id', view_id,
            '--offset', str(offset),
            '--limit', str(min(page_size, max_records - offset)),
        ])
        data = payload['data']
        field_names = [str(name) for name in data.get('fields', [])]
        record_ids = [str(item) for item in data.get('record_id_list', [])]
        row_values = data.get('data', [])
        for record_id, values in zip(record_ids, row_values):
            row = {'record_id': record_id}
            for field_name, value in zip(field_names, values):
                row[field_name] = value
            rows.append(row)
        if not data.get('has_more'):
            break
        offset += len(record_ids)
    return rows


def build_term_cache_key(source: FeishuTermSource, target_lang: str) -> str:
    raw = json.dumps({
        'wiki_token': source.wiki_token,
        'table_id': source.table_id,
        'view_id': source.view_id,
        'target_lang': target_lang,
    }, sort_keys=True)
    return str(abs(hash(raw)))


def load_cached_terms(cache_path: Path) -> Optional[Dict[str, str]]:
    try:
        payload = json.loads(cache_path.read_text(encoding='utf-8'))
    except Exception:
        return None
    if int(payload.get('schema_version', 0) or 0) != TERM_CACHE_SCHEMA:
        return None
    fetched_at = float(payload.get('fetched_at', 0) or 0)
    if fetched_at <= 0 or time.time() - fetched_at > TERM_CACHE_TTL_SECONDS:
        return None
    terms = payload.get('terms')
    if not isinstance(terms, dict):
        return None
    return {str(k): str(v) for k, v in terms.items()}


def save_cached_terms(cache_path: Path, terms: Dict[str, str]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'schema_version': TERM_CACHE_SCHEMA,
        'fetched_at': time.time(),
        'terms': terms,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')


def pick_lang_field(row: dict, preferred: List[str]) -> Optional[str]:
    lowered = {str(k).lower(): k for k in row.keys()}
    for name in preferred:
        if name.lower() in lowered:
            return str(lowered[name.lower()])
    return None


def build_terms_from_rows(rows: List[dict], target_lang: str) -> Dict[str, str]:
    terms: Dict[str, str] = {}
    for row in rows:
        src_field = pick_lang_field(row, ['en', 'source', 'source text', 'english'])
        tgt_field = pick_lang_field(row, [target_lang, 'de', 'target', 'target text', 'german', 'deutsch'])
        if not src_field or not tgt_field:
            continue
        src = str(row.get(src_field) or '').strip()
        tgt = str(row.get(tgt_field) or '').strip()
        if src and tgt:
            terms[src] = tgt
    return terms


def load_terms_from_feishu(source: FeishuTermSource, target_lang: str) -> Dict[str, str]:
    cache_dir = resolve_cache_dir()
    cache_path = cache_dir / f"term-table-{build_term_cache_key(source, target_lang)}.json"
    cached = load_cached_terms(cache_path)
    if cached:
        return cached
    cli = resolve_lark_cli()
    base_token = resolve_base_token(cli, source.wiki_token)
    rows = list_records(cli, base_token, source.table_id, source.view_id)
    terms = build_terms_from_rows(rows, target_lang)
    if terms:
        save_cached_terms(cache_path, terms)
    return terms


def load_term_table(path: Optional[str]) -> Dict[str, str]:
    table_path = Path(path) if path else DEFAULT_TERM_TABLE
    if not table_path.exists():
        return {}
    terms: Dict[str, str] = {}
    with table_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            src = (row.get('source') or '').strip()
            tgt = (row.get('target') or '').strip()
            if src and tgt:
                terms[src] = tgt
    return terms


def load_terms(term_table: Optional[str], use_feishu_term_source: bool, target_lang: str) -> Dict[str, str]:
    local_terms = load_term_table(term_table)
    if not use_feishu_term_source:
        return local_terms
    source = parse_term_source_md(DEFAULT_TERM_SOURCE)
    if not source:
        return local_terms
    try:
        remote_terms = load_terms_from_feishu(source, target_lang)
    except Exception:
        remote_terms = {}
    merged = dict(local_terms)
    merged.update(remote_terms)
    return merged


def apply_term_priority(text: str, terms: Dict[str, str]) -> str:
    if not terms:
        return text
    items = sorted(terms.items(), key=lambda kv: len(kv[0]), reverse=True)
    out = text
    for src, tgt in items:
        out = re.sub(rf'(?<![A-Za-z0-9]){re.escape(src)}(?![A-Za-z0-9])', tgt, out)
    return out


def split_markdown(content: str) -> List[Segment]:
    lines = content.splitlines(keepends=True)
    segments: List[Segment] = []
    buf: List[str] = []
    current_kind: Optional[str] = None
    in_code = False

    def flush():
        nonlocal buf, current_kind
        if buf:
            segments.append(Segment(current_kind or 'text', ''.join(buf)))
            buf = []
            current_kind = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            kind = 'codefence'
            in_code = not in_code if current_kind == 'codefence' or not in_code else in_code
        elif in_code:
            kind = 'codefence'
        elif not stripped:
            kind = 'blank'
        elif stripped.startswith('#'):
            kind = 'heading'
        elif stripped.startswith('|'):
            kind = 'table'
        elif re.match(r'^!\[.*\]\(.*\)$', stripped):
            kind = 'image'
        elif re.match(r'^[*-]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            kind = 'list'
        else:
            kind = 'text'

        if current_kind is None:
            current_kind = kind
            buf.append(line)
        elif kind == current_kind and kind not in {'heading', 'image', 'blank'}:
            buf.append(line)
        else:
            flush()
            current_kind = kind
            buf.append(line)
    flush()
    return segments


def parse_prompt_candidates(prompt_output: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for line in prompt_output.splitlines():
        m = re.search(r'`(.+?)` -> `(.+?)`', line)
        if m:
            pairs.append((m.group(1), m.group(2)))
    return pairs


def normalize_for_pattern(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\b\d+(?:[.,]\d+)?\b', '<NUM>', text)
    text = re.sub(r'\b(?:[A-Z]{1,8}-)?\d+[A-Z0-9-]*\b', '<ID>', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_params(text: str) -> List[str]:
    return re.findall(r'\b(?:[A-Z]{1,8}-)?\d+[A-Z0-9./-]*\b|\b\d+(?:[.,]\d+)?(?:W|V|A|Hz|Wh|°C|°F|ms|%|mm|cm|kg|lbs)?\b', text)


def replace_params(skeleton: str, source_example: str, new_source: str) -> Optional[str]:
    old_params = extract_params(source_example)
    new_params = extract_params(new_source)
    if not old_params or len(old_params) != len(new_params):
        return None
    result = skeleton
    for old, new in zip(old_params, new_params):
        result = result.replace(old, new, 1)
    return result


def translate_unit(text: str, source_lang: str, target_lang: str, highlight_unmatched: bool) -> str:
    stripped = text.strip()
    if not stripped:
        return text
    prompt = run_tm_query(stripped, source_lang, target_lang)
    candidates = parse_prompt_candidates(prompt)
    for src, tgt in candidates:
        if src.strip() == stripped:
            return text.replace(stripped, tgt)
    norm = normalize_for_pattern(stripped)
    for src, tgt in candidates:
        if normalize_for_pattern(src) == norm:
            reused = replace_params(tgt, src, stripped)
            if reused:
                return text.replace(stripped, reused)
    return text.replace(stripped, f'=={stripped}==') if highlight_unmatched else text


def split_sentences(text: str) -> List[str]:
    parts = re.split(SENTENCE_SPLIT_RE, text)
    return [p for p in parts if p]


def translate_segment(text: str, source_lang: str, target_lang: str, highlight_unmatched: bool, terms: Dict[str, str]) -> str:
    if not text.strip():
        return text
    text = apply_term_priority(text, terms)
    sentences = split_sentences(text)
    if len(sentences) <= 1:
        return translate_unit(text, source_lang, target_lang, highlight_unmatched)
    rebuilt: List[str] = []
    for sentence in sentences:
        trailing_ws = ''
        m = re.search(r'(\s+)$', sentence)
        if m:
            trailing_ws = m.group(1)
            sentence_core = sentence[:-len(trailing_ws)]
        else:
            sentence_core = sentence
        rebuilt.append(translate_unit(sentence_core, source_lang, target_lang, highlight_unmatched) + trailing_ws)
    return ''.join(rebuilt)


def process_table_block(text: str, source_lang: str, target_lang: str, highlight_unmatched: bool, terms: Dict[str, str]) -> str:
    out_lines = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped or re.fullmatch(r'[|\-: ]+', stripped):
            out_lines.append(line)
            continue
        cells = line.split('|')
        new_cells = []
        for cell in cells:
            raw = cell
            cell_stripped = cell.strip()
            if not cell_stripped:
                new_cells.append(raw)
                continue
            if re.search(r'!\[.*\]\(.*\)', cell_stripped):
                new_cells.append(raw)
                continue
            replaced = translate_segment(cell_stripped, source_lang, target_lang, highlight_unmatched, terms)
            new_cells.append(raw.replace(cell_stripped, replaced, 1))
        out_lines.append('|'.join(new_cells))
    return ''.join(out_lines)


def process_markdown(content: str, source_lang: str, target_lang: str, highlight_unmatched: bool, terms: Dict[str, str]) -> str:
    segments = split_markdown(content)
    out: List[str] = []
    for seg in segments:
        if seg.kind in {'blank', 'image', 'codefence'}:
            out.append(seg.text)
        elif seg.kind == 'table':
            out.append(process_table_block(seg.text, source_lang, target_lang, highlight_unmatched, terms))
        else:
            out.append(translate_segment(seg.text, source_lang, target_lang, highlight_unmatched, terms))
    return ''.join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description='Rewrite markdown with translation-memory-first rules.')
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('-o', '--output', help='Output markdown file')
    parser.add_argument('--source-lang', default='en')
    parser.add_argument('--target-lang', required=True)
    parser.add_argument('--term-table', help='TSV term table with source and target columns')
    parser.add_argument('--use-feishu-term-source', action='store_true', help='Load bound Feishu term source first, then fall back to local TSV')
    parser.add_argument('--no-highlight-unmatched', action='store_true')
    args = parser.parse_args()

    input_path = Path(args.input)
    content = input_path.read_text(encoding='utf-8')
    terms = load_terms(args.term_table, args.use_feishu_term_source, args.target_lang)
    result = process_markdown(
        content,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        highlight_unmatched=not args.no_highlight_unmatched,
        terms=terms,
    )

    if args.output:
        Path(args.output).write_text(result, encoding='utf-8')
    else:
        sys.stdout.write(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
