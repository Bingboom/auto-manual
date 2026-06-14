#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import zipfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

from lxml import etree

REPO_ROOT = Path(__file__).resolve().parents[4]
TM_SCRIPT = REPO_ROOT / ".agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W}

LANGUAGE_ALIASES = {
    "chinese": "zh",
    "cn": "zh",
    "de": "de",
    "deutsch": "de",
    "english": "en",
    "en": "en",
    "es": "es",
    "espanol": "es",
    "espana": "es",
    "fr": "fr",
    "francais": "fr",
    "french": "fr",
    "german": "de",
    "it": "it",
    "italian": "it",
    "ja": "ja",
    "japanese": "ja",
    "jp": "ja",
    "ko": "ko",
    "korean": "ko",
    "kr": "ko",
    "portuguese": "pt-br",
    "pt": "pt-br",
    "pt-br": "pt-br",
    "ptbr": "pt-br",
    "spanish": "es",
    "uk": "uk",
    "ukrainian": "uk",
    "zh": "zh",
    "zh-cn": "zh",
}

LANGUAGE_LABELS = {
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "pt-br": "Português (Brasil)",
    "uk": "Українська",
    "zh": "中文",
}

IMPORTANT_LABELS = {
    "de": "WICHTIG",
    "en": "IMPORTANT",
    "es": "IMPORTANTE",
    "fr": "IMPORTANT",
    "it": "IMPORTANTE",
    "ja": "重要",
    "ko": "중요",
    "pt-br": "IMPORTANTE",
    "uk": "ВАЖЛИВО",
    "zh": "重要",
}

FONT_BY_LANG = {
    "ja": "Yu Gothic",
    "ko": "Malgun Gothic",
    "zh": "Microsoft YaHei",
}

COLOR_HEX = {
    "yellow": "FFFF00",
    "lightyellow": "FFF5B8",
    "green": "92D050",
    "lightgreen": "C6EFCE",
    "cyan": "00FFFF",
    "pink": "FFC0CB",
    "gray": "D9D9D9",
    "grey": "D9D9D9",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "that",
    "to",
    "with",
}

SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


@dataclass(frozen=True)
class Pair:
    source: str
    target: str
    row_key: str
    kind: str


def w(tag: str) -> str:
    return f"{{{W}}}{tag}"


def normalize_language(raw: str | None) -> str:
    value = (raw or "").strip().lower().replace("_", "-")
    if not value:
        return ""
    ascii_value = strip_accents(value)
    return LANGUAGE_ALIASES.get(value) or LANGUAGE_ALIASES.get(ascii_value) or value


def resolve_color(raw: str) -> str:
    value = raw.strip().lower().lstrip("#")
    if value in COLOR_HEX:
        return COLOR_HEX[value]
    if len(value) == 6 and all(ch in "0123456789abcdef" for ch in value):
        return value.upper()
    raise SystemExit(f"Unsupported highlight color: {raw}")


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def value_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(value_text(item) for item in value if value_text(item)).strip()
    if isinstance(value, dict):
        for key in ("text", "value", "name"):
            if key in value:
                return value_text(value[key])
    return str(value).strip()


def load_tm_helper():
    spec = importlib.util.spec_from_file_location("live_tm_helper", TM_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Translation_Memory helper from {TM_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_live_tm_rows(args: argparse.Namespace) -> tuple[list[str], list[dict[str, object]]]:
    helper = load_tm_helper()
    cache_dir = None if args.no_cache or args.cache_ttl_seconds <= 0 else helper.resolve_cache_dir(args.cache_dir)
    cache_key = helper.build_cache_key(
        wiki_token=args.tm_wiki_token,
        base_token=args.tm_base_token,
        table_id=args.tm_table_id,
        view_id=args.tm_view_id,
        max_records=args.max_records,
    )
    cached = helper.load_cached_table_snapshot(
        cache_dir=cache_dir,
        cache_key=cache_key,
        max_age_seconds=args.cache_ttl_seconds,
    )
    if cached is not None:
        return cached

    cli = helper.resolve_lark_cli()
    base_token = args.tm_base_token or helper.resolve_base_token(cli=cli, wiki_token=args.tm_wiki_token)
    language_fields = helper.get_table_language_fields(cli=cli, base_token=base_token, table_id=args.tm_table_id)
    rows = helper.list_records(
        cli=cli,
        base_token=base_token,
        table_id=args.tm_table_id,
        view_id=args.tm_view_id,
        max_records=args.max_records,
    )
    helper.save_cached_table_snapshot(
        cache_dir=cache_dir,
        cache_key=cache_key,
        wiki_token=args.tm_wiki_token,
        table_id=args.tm_table_id,
        view_id=args.tm_view_id,
        max_records=args.max_records,
        language_fields=language_fields,
        rows=rows,
    )
    return language_fields, rows


def build_pairs(
    rows: list[dict[str, object]],
    language_fields: list[str],
    source_lang: str,
    target_lang: str,
) -> tuple[list[Pair], list[str]]:
    field_by_lang = {normalize_language(field): field for field in language_fields}
    source_field = field_by_lang.get(source_lang)
    target_field = field_by_lang.get(target_lang)
    if source_field is None or target_field is None:
        available = sorted(lang for lang in field_by_lang if lang)
        raise RuntimeError(
            f"Translation_Memory lacks requested source/target columns: {source_lang}->{target_lang}; "
            f"available language columns: {', '.join(available)}"
        )

    pairs: list[Pair] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        source = value_text(row.get(source_field))
        target = value_text(row.get(target_field))
        if not source or not target:
            continue
        row_key = value_text(row.get("record_id"))
        pairs.append(Pair(source=source, target=target, row_key=row_key, kind="row"))

        source_parts = [part.strip() for part in re.split(r"\s*/\s*/\s*", source) if part.strip()]
        target_parts = [part.strip() for part in re.split(r"\s*/\s*/\s*", target) if part.strip()]
        if len(source_parts) == len(target_parts) and len(source_parts) > 1:
            for index, (source_part, target_part) in enumerate(zip(source_parts, target_parts), start=1):
                pairs.append(
                    Pair(
                        source=source_part,
                        target=target_part,
                        row_key=f"{row_key}#{index}",
                        kind="segment",
                    )
                )
    return pairs, sorted(lang for lang in field_by_lang if lang)


def base_norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").translate(SUBSCRIPT_MAP)
    text = strip_accents(text)
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    text = text.replace("⎓", "dc").replace("~", " ")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def abstract_norm(text: str) -> str:
    text = base_norm(text)
    text = re.sub(r"https?://\S+|[\w.-]+@[\w.-]+", "{contact}", text)
    text = re.sub(r"\bjackery explorer\s+\d+(?:\s+plus)?\b", "jackery explorer {model}", text)
    text = re.sub(r"\bexplorer\s+\d+(?:\s+plus)?\b", "explorer {model}", text)
    text = re.sub(r"\bjackery battery pack\s+\d+\b", "jackery battery pack {model}", text)
    text = re.sub(r"\bbattery pack\s+\d+\b", "battery pack {model}", text)
    text = re.sub(r"\bje-\d+[a-z]*\b", "{modelno}", text)
    text = re.sub(r"\bthis product\b", "the product", text)
    text = re.sub(r"\ball the instructions\b", "all instructions", text)
    text = re.sub(
        r"\b\d+(?:[.,]\d+)?(?:\s*[x×-]\s*\d+(?:[.,]\d+)?)*"
        r"(?:\s*(?:v|w|wh|ah|a|hz|ms|s|hours?|months?|years?|kg|cm|mm|%|°c|dc|ac|soc))?\b",
        "{n}",
        text,
    )
    text = re.sub(r"[^\w{}\u3040-\u30ff\u3400-\u9fff%+./-]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> set[str]:
    found = re.findall(r"[\w{}%+./-]+|[\u3040-\u30ff]+|[\u3400-\u9fff]+", abstract_norm(text), flags=re.UNICODE)
    return {token for token in found if token not in STOPWORDS and token not in {"{n}", "{model}", "{modelno}", "{contact}"}}


def split_units(text: str) -> list[str]:
    text = " ".join((text or "").split())
    if not text:
        return []
    units = re.split(r"(?<=[.!?。！？])\s+(?=[A-Z0-9*\"'(\u3040-\u30ff\u3400-\u9fff])", text)
    return [unit.strip() for unit in units if unit.strip()]


def find_phrases(pattern: str, text: str) -> list[str]:
    return [match.group(0) for match in re.finditer(pattern, text, flags=re.I)]


def adapt_target(target: str, source: str, query: str) -> str:
    result = target
    phrase_patterns = [
        r"\bJackery Explorer\s+\d+(?:\s+Plus)?\b",
        r"\bExplorer\s+\d+(?:\s+Plus)?\b",
        r"\bJackery Battery Pack\s+\d+\b",
        r"\bBattery Pack\s+\d+\b",
        r"\bJE-\d+[A-Za-z]*\b",
        r"https?://\S+",
        r"[\w.-]+@[\w.-]+",
    ]
    for pattern in phrase_patterns:
        for source_item, query_item in zip(find_phrases(pattern, source), find_phrases(pattern, query)):
            result = re.sub(re.escape(source_item), query_item, result, flags=re.I)

    number_pattern = (
        r"\b\d+(?:[.,]\d+)?(?:\s*[x×-]\s*\d+(?:[.,]\d+)?)*"
        r"(?:\s*(?:V|W|Wh|Ah|A|Hz|ms|s|hours?|months?|years?|kg|cm|mm|%|°C|DC|AC|SOC))?\b"
    )
    for source_item, query_item in zip(find_phrases(number_pattern, source), find_phrases(number_pattern, query)):
        if source_item != query_item:
            result = re.sub(re.escape(source_item), query_item, result, count=1)
    return result


class Matcher:
    def __init__(self, pairs: list[Pair], *, min_fuzzy_score: float) -> None:
        self.pairs = pairs
        self.min_fuzzy_score = min_fuzzy_score
        self.exact: dict[str, Pair] = {}
        self.abstract: dict[str, Pair] = {}
        for pair in pairs:
            self.exact.setdefault(base_norm(pair.source), pair)
            self.abstract.setdefault(abstract_norm(pair.source), pair)

    def best_pair(self, text: str) -> tuple[Pair | None, float, str]:
        if len(text.strip()) < 2:
            return None, 0.0, "empty"
        exact_key = base_norm(text)
        if exact_key in self.exact:
            return self.exact[exact_key], 1.0, "exact"
        abstract_key = abstract_norm(text)
        if abstract_key in self.abstract and len(text) > 2:
            return self.abstract[abstract_key], 0.98, "parameter"

        query_tokens = tokens(text)
        if not query_tokens:
            return None, 0.0, "no-tokens"

        best_score = 0.0
        best_pair: Pair | None = None
        best_reason = ""
        for pair in self.pairs:
            pair_tokens = tokens(pair.source)
            if not pair_tokens:
                continue
            overlap = len(query_tokens & pair_tokens)
            coverage = overlap / len(query_tokens)
            source_coverage = overlap / len(pair_tokens)
            if coverage < 0.45:
                continue
            ratio = SequenceMatcher(None, abstract_key, abstract_norm(pair.source)).ratio()
            score = ratio * 0.68 + coverage * 0.24 + min(source_coverage, 1.0) * 0.08
            if score > best_score:
                best_score = score
                best_pair = pair
                best_reason = f"fuzzy ratio={ratio:.2f} coverage={coverage:.2f}"

        text_len = len(base_norm(text))
        threshold = max(self.min_fuzzy_score, 0.93 if text_len < 25 else 0.86 if text_len < 90 else 0.82)
        if best_pair and best_score >= threshold:
            return best_pair, best_score, best_reason
        return None, best_score, best_reason or "below-threshold"

    def translate(self, text: str) -> tuple[str | None, dict[str, object] | None]:
        pair, score, reason = self.best_pair(text)
        if pair is not None:
            return adapt_target(pair.target, pair.source, text), {
                "mode": "full",
                "source": text,
                "match_source": pair.source,
                "row_key": pair.row_key,
                "score": round(score, 4),
                "reason": reason,
                "kind": pair.kind,
            }

        units = split_units(text)
        if len(units) <= 1:
            return None, None
        translated_units: list[str] = []
        records: list[dict[str, object]] = []
        for unit in units:
            pair, score, reason = self.best_pair(unit)
            if pair is None:
                translated_units.append(unit)
                continue
            translated_units.append(adapt_target(pair.target, pair.source, unit))
            records.append(
                {
                    "source": unit,
                    "match_source": pair.source,
                    "row_key": pair.row_key,
                    "score": round(score, 4),
                    "reason": reason,
                    "kind": pair.kind,
                }
            )
        if records:
            return " ".join(translated_units), {"mode": "split", "source": text, "matched_units": records}
        return None, None


def para_text(p_el: etree._Element) -> str:
    return "".join(p_el.xpath(".//w:t/text()", namespaces=NS)).strip()


def first_run_props(p_el: etree._Element) -> etree._Element | None:
    rpr = p_el.find(".//w:rPr", NS)
    return copy.deepcopy(rpr) if rpr is not None else None


def make_rpr(base_rpr: etree._Element | None, *, highlight_color: str, target_lang: str) -> etree._Element:
    rpr = copy.deepcopy(base_rpr) if base_rpr is not None else etree.Element(w("rPr"))
    for tag in ("shd", "highlight"):
        for existing in rpr.findall(w(tag)):
            rpr.remove(existing)
    shd = etree.SubElement(rpr, w("shd"))
    shd.set(w("val"), "clear")
    shd.set(w("color"), "auto")
    shd.set(w("fill"), highlight_color)

    font_name = FONT_BY_LANG.get(target_lang)
    if font_name:
        rfonts = rpr.find(w("rFonts"))
        if rfonts is None:
            rfonts = etree.SubElement(rpr, w("rFonts"))
        rfonts.set(w("eastAsia"), font_name)
    return rpr


def set_para_text(p_el: etree._Element, text: str, *, highlight_color: str, target_lang: str) -> None:
    base_rpr = first_run_props(p_el)
    for child in list(p_el):
        if child.tag != w("pPr"):
            p_el.remove(child)
    r_el = etree.SubElement(p_el, w("r"))
    r_el.append(make_rpr(base_rpr, highlight_color=highlight_color, target_lang=target_lang))
    for index, chunk in enumerate(text.split("\n")):
        if index:
            etree.SubElement(r_el, w("br"))
        t_el = etree.SubElement(r_el, w("t"))
        t_el.text = chunk
        if chunk.startswith(" ") or chunk.endswith(" "):
            t_el.set(f"{{{XML}}}space", "preserve")


def top_level_paragraph_texts(body: etree._Element) -> list[tuple[int, etree._Element, str]]:
    values = []
    for index, child in enumerate(list(body)):
        if child.tag == w("p"):
            values.append((index, child, para_text(child)))
    return values


def looks_like_language_heading(text: str) -> bool:
    normalized = base_norm(text)
    return bool(
        re.match(
            r"^(fr|es|de|it|uk|ja|jp|ko|kr|pt|pt-br|zh|cn)\s+"
            r"(important|importante|wichtig|важливо|重要|중요)",
            normalized,
        )
    )


def collapse_leading_multilingual_notice(
    body: etree._Element,
    *,
    target_lang: str,
    highlight_color: str,
    end_text: str,
) -> list[dict[str, object]]:
    top_paras = top_level_paragraph_texts(body)
    if len(top_paras) < 4:
        return []
    first_other_lang = None
    for position, (_index, _p_el, text) in enumerate(top_paras[1:], start=1):
        if looks_like_language_heading(text):
            first_other_lang = position
            break
    if first_other_lang is None:
        return []

    end_position = None
    end_norm = base_norm(end_text)
    for position, (_index, _p_el, text) in enumerate(top_paras[first_other_lang + 1 :], start=first_other_lang + 1):
        if base_norm(text) == end_norm:
            end_position = position
            break
    if end_position is None:
        return []

    changes: list[dict[str, object]] = []
    label = LANGUAGE_LABELS.get(target_lang, target_lang)
    important = IMPORTANT_LABELS.get(target_lang, "IMPORTANT")
    replacements = {0: label, 1: important}
    for position, replacement in replacements.items():
        _index, p_el, before = top_paras[position]
        set_para_text(p_el, replacement, highlight_color=highlight_color, target_lang=target_lang)
        changes.append({"mode": "collapse-leading-notice", "source": before, "target": replacement})

    children = list(body)
    delete_top_indices = [top_paras[position][0] for position in range(first_other_lang, end_position)]
    for top_index in sorted(delete_top_indices, reverse=True):
        body.remove(children[top_index])
    changes.append(
        {
            "mode": "collapse-leading-notice-delete",
            "deleted_paragraph_count": len(delete_top_indices),
            "end_text": end_text,
        }
    )
    return changes


def preprocess_docx(
    input_docx: Path,
    output_docx: Path,
    report_path: Path,
    matcher: Matcher,
    *,
    source_lang: str,
    target_lang: str,
    highlight_color: str,
    collapse_notice: bool,
    front_matter_end_text: str,
) -> dict[str, object]:
    temp_dir = Path(tempfile.mkdtemp(prefix="tm-docx-preprocess-"))
    try:
        with zipfile.ZipFile(input_docx) as zin:
            zin.extractall(temp_dir)
        document_path = temp_dir / "word/document.xml"
        parser = etree.XMLParser(remove_blank_text=False)
        root = etree.parse(str(document_path), parser).getroot()
        body = root.find(".//w:body", NS)
        if body is None:
            raise RuntimeError("word/document.xml has no w:body")

        changes: list[dict[str, object]] = []
        if collapse_notice:
            changes.extend(
                collapse_leading_multilingual_notice(
                    body,
                    target_lang=target_lang,
                    highlight_color=highlight_color,
                    end_text=front_matter_end_text,
                )
            )

        for p_el in root.xpath(".//w:p", namespaces=NS):
            text = para_text(p_el)
            if not text:
                continue
            if p_el.xpath(".//w:drawing|.//w:pict|.//w:object", namespaces=NS):
                continue
            translated, record = matcher.translate(text)
            if not translated or translated == text:
                continue
            set_para_text(p_el, translated, highlight_color=highlight_color, target_lang=target_lang)
            if record:
                changes.append(record)

        document_path.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True))
        output_docx.parent.mkdir(parents=True, exist_ok=True)
        if output_docx.exists():
            output_docx.unlink()
        with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as zout:
            for path in temp_dir.rglob("*"):
                if path.is_file():
                    zout.write(path, path.relative_to(temp_dir).as_posix())

        report = {
            "input_docx": str(input_docx),
            "output_docx": str(output_docx),
            "source_lang": source_lang,
            "target_lang": target_lang,
            "change_count": len(changes),
            "changes": changes,
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_json(cmd: list[str], *, cwd: Path | None = None) -> dict[str, object]:
    completed = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"Command failed: {' '.join(cmd)}")
    output = completed.stdout.strip()
    json_start = output.find("{")
    if json_start == -1:
        raise RuntimeError(f"Command did not return JSON: {' '.join(cmd)}\n{output}")
    payload = json.loads(output[json_start:])
    if payload.get("ok") is False or int(payload.get("code", 0) or 0) != 0:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def url_token(url: str, kind: str) -> str:
    path_parts = [part for part in urlparse(url).path.split("/") if part]
    for index, part in enumerate(path_parts[:-1]):
        if part == kind:
            return path_parts[index + 1]
    return ""


def download_or_export_source(args: argparse.Namespace, work_dir: Path) -> tuple[Path, dict[str, object], dict[str, object] | None]:
    if args.input_docx:
        input_docx = Path(args.input_docx).expanduser().resolve()
        if not input_docx.exists():
            raise FileNotFoundError(input_docx)
        return input_docx, {}, None

    if not args.url:
        raise RuntimeError("Either --url or --input-docx is required.")

    inspect = run_json(["lark-cli", "drive", "+inspect", "--url", args.url, "--as", args.as_identity, "--json"])
    data = inspect["data"]
    doc_type = str(data.get("type") or "")
    token = str(data.get("token") or "")
    title = str(data.get("title") or "source.docx")

    if doc_type == "file":
        if not title.lower().endswith(".docx"):
            raise RuntimeError(f"Only .docx Drive files are supported for file sources, got: {title}")
        output_name = title
        run_json(
            [
                "lark-cli",
                "drive",
                "+download",
                "--file-token",
                token,
                "--output",
                output_name,
                "--overwrite",
                "--as",
                args.as_identity,
                "--json",
            ],
            cwd=work_dir,
        )
        return work_dir / output_name, inspect, resolve_wiki_node(args, inspect)

    if doc_type in {"doc", "docx"}:
        output_name = title if title.lower().endswith(".docx") else f"{title}.docx"
        run_json(
            [
                "lark-cli",
                "drive",
                "+export",
                "--doc-type",
                doc_type,
                "--file-extension",
                "docx",
                "--token",
                token,
                "--file-name",
                output_name,
                "--output-dir",
                ".",
                "--overwrite",
                "--as",
                args.as_identity,
                "--json",
            ],
            cwd=work_dir,
        )
        return work_dir / output_name, inspect, resolve_wiki_node(args, inspect)

    raise RuntimeError(f"Unsupported Lark source type for DOCX preprocessing: {doc_type}")


def resolve_wiki_node(args: argparse.Namespace, inspect: dict[str, object]) -> dict[str, object] | None:
    data = inspect.get("data") or {}
    if not isinstance(data, dict):
        return None
    wiki_node = data.get("wiki_node")
    if isinstance(wiki_node, dict) and wiki_node.get("node_token"):
        payload = run_json(
            [
                "lark-cli",
                "wiki",
                "spaces",
                "get_node",
                "--params",
                json.dumps({"token": wiki_node["node_token"]}, ensure_ascii=False),
                "--as",
                args.as_identity,
                "--json",
            ]
        )
        return payload.get("data", {}).get("node") if isinstance(payload.get("data"), dict) else None

    token = str(data.get("token") or "")
    doc_type = str(data.get("type") or "")
    if token and doc_type:
        cmd = [
            "lark-cli",
            "wiki",
            "+node-get",
            "--node-token",
            token,
            "--obj-type",
            doc_type,
            "--as",
            args.as_identity,
            "--json",
        ]
        try:
            payload = run_json(cmd)
        except Exception:
            return None
        node = payload.get("data")
        return node if isinstance(node, dict) else None
    return None


def default_output_name(source_name: str, source_lang: str, target_lang: str) -> str:
    base = source_name[:-5] if source_name.lower().endswith(".docx") else source_name
    marker = f"_{source_lang}_"
    replacement = f"_{target_lang}_"
    if marker in base:
        base = base.replace(marker, replacement, 1)
    elif base.endswith(f"_{source_lang}"):
        base = f"{base[: -len(source_lang)]}{target_lang}"
    else:
        base = f"{base}_{target_lang}"
    if not base.endswith("_tm_preprocessed"):
        base = f"{base}_tm_preprocessed"
    return f"{base}.docx"


def upload_same_path(
    args: argparse.Namespace,
    output_docx: Path,
    source_node: dict[str, object] | None,
    work_dir: Path,
    output_name: str,
) -> dict[str, object] | None:
    if args.no_upload:
        return None
    if args.folder_token:
        cmd = [
            "lark-cli",
            "drive",
            "+upload",
            "--file",
            output_docx.name,
            "--folder-token",
            args.folder_token,
            "--name",
            output_name,
            "--as",
            args.as_identity,
            "--json",
        ]
        return run_json(cmd, cwd=work_dir)

    parent_node_token = str((source_node or {}).get("parent_node_token") or "")
    if not parent_node_token:
        raise RuntimeError("Cannot resolve source parent Wiki node; pass --folder-token or --no-upload.")
    cmd = [
        "lark-cli",
        "drive",
        "+upload",
        "--file",
        output_docx.name,
        "--wiki-token",
        parent_node_token,
        "--name",
        output_name,
        "--as",
        args.as_identity,
        "--json",
    ]
    return run_json(cmd, cwd=work_dir)


def count_yellow_runs(docx_path: Path, color: str) -> int:
    with zipfile.ZipFile(docx_path) as zin:
        root = etree.fromstring(zin.read("word/document.xml"))
    return len(root.xpath(f'.//w:rPr/w:shd[@w:fill="{color}"]', namespaces=NS))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess a Lark/Feishu DOCX with live Translation_Memory matches.")
    parser.add_argument("--url", help="Feishu/Lark file, docx, doc, or wiki URL")
    parser.add_argument("--input-docx", help="Local DOCX path for dry-run/testing")
    parser.add_argument("--source-lang", required=True, help="Source language code, e.g. en/fr/es/de/it/ko/ja/zh/pt-BR")
    parser.add_argument("--target-lang", required=True, help="Target language code, e.g. fr/es/de/it/ko/ja/zh/pt-BR")
    parser.add_argument("--output-name", help="Output DOCX file name; defaults to source name with target lang marker")
    parser.add_argument("--work-dir", default=None, help="Working directory; defaults to a timestamped /tmp folder")
    parser.add_argument("--highlight-color", default="yellow", help="Highlight color name or RRGGBB hex; default yellow")
    parser.add_argument("--min-fuzzy-score", type=float, default=0.0, help="Extra fuzzy score floor; built-in safety floors still apply")
    parser.add_argument("--collapse-leading-multilingual-notice", action="store_true", help="Delete leading non-target IMPORTANT/IMPORTANTE language blocks")
    parser.add_argument("--front-matter-end-text", default="IMPORTANT SAFETY INFORMATION", help="First heading after leading multilingual notice")
    parser.add_argument("--no-upload", action="store_true", help="Do not upload; leave processed DOCX locally")
    parser.add_argument("--folder-token", help="Upload to this Drive folder if source path cannot be resolved")
    parser.add_argument("--as", dest="as_identity", default="bot", choices=("user", "bot"), help="lark-cli identity")
    parser.add_argument("--cache-ttl-seconds", type=int, default=86400)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--tm-wiki-token", default="X3O8wCpXPifqGKkP2sYccyxznQb")
    parser.add_argument("--tm-table-id", default="tbl6gKPJPTvOcTWv")
    parser.add_argument("--tm-view-id", default="veweqW2fQv")
    parser.add_argument("--tm-base-token", default=None)
    parser.add_argument("--max-records", type=int, default=2000)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_lang = normalize_language(args.source_lang)
    target_lang = normalize_language(args.target_lang)
    if not source_lang or not target_lang:
        raise SystemExit("--source-lang and --target-lang are required")
    if source_lang == target_lang:
        raise SystemExit("source and target languages must differ")

    highlight_color = resolve_color(args.highlight_color)
    work_dir = Path(args.work_dir).expanduser().resolve() if args.work_dir else Path(tempfile.gettempdir()) / f"lark-tm-preprocess-{int(time.time())}"
    work_dir.mkdir(parents=True, exist_ok=True)

    input_docx, inspect_payload, source_node = download_or_export_source(args, work_dir)
    language_fields, rows = load_live_tm_rows(args)
    pairs, available_langs = build_pairs(rows, language_fields, source_lang, target_lang)
    matcher = Matcher(pairs, min_fuzzy_score=args.min_fuzzy_score)

    output_name = args.output_name or default_output_name(input_docx.name, source_lang, target_lang)
    output_docx = work_dir / output_name
    report_path = work_dir / f"{Path(output_name).stem}.report.json"
    report = preprocess_docx(
        input_docx,
        output_docx,
        report_path,
        matcher,
        source_lang=source_lang,
        target_lang=target_lang,
        highlight_color=highlight_color,
        collapse_notice=args.collapse_leading_multilingual_notice,
        front_matter_end_text=args.front_matter_end_text,
    )
    upload_payload = upload_same_path(args, output_docx, source_node, work_dir, output_name)

    result = {
        "ok": True,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "available_languages": available_langs,
        "pair_count": len(pairs),
        "change_count": report["change_count"],
        "highlight_color": highlight_color,
        "highlighted_runs": count_yellow_runs(output_docx, highlight_color),
        "work_dir": str(work_dir),
        "output_docx": str(output_docx),
        "report_json": str(report_path),
        "upload": upload_payload.get("data") if isinstance(upload_payload, dict) else None,
        "source_inspect": inspect_payload.get("data") if isinstance(inspect_payload, dict) else None,
        "source_wiki_node": source_node,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
