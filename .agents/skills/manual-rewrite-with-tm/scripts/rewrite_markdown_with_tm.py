#!/usr/bin/env python3
import argparse
import csv
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


QUERY_SCRIPT = Path('.agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py')
DEFAULT_TERM_TABLE = Path('.agents/skills/manual-rewrite-with-tm/references/term-priority.example.tsv')
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?。！？])\s+(?=(?:[A-Z0-9#*`\[]|\*\*|==))')


@dataclass
class Segment:
    kind: str
    text: str


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
    lines = prompt_output.splitlines()
    for line in lines:
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
    parser.add_argument('--no-highlight-unmatched', action='store_true')
    args = parser.parse_args()

    input_path = Path(args.input)
    content = input_path.read_text(encoding='utf-8')
    terms = load_term_table(args.term_table)
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
