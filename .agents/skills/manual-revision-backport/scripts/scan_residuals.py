#!/usr/bin/env python3
"""Convergence check for a manual back-port: scan for OLD terms that SHOULD be gone.

The dangerous failure mode of this workflow is declaring "all done" when some of the
reviewer's changes were never actually applied (the revised .docx was built from an
older snapshot, so it is easy to lose track). This tool makes "done" verifiable: you
give it the per-language OLD substrings the revision removed, and it greps both the
repo templates and the live Feishu record dumps for any survivors. Zero residuals in
scope == converged. Run it before claiming completion.

Terms file (JSON): {"es": ["coche", "automóvil"], "it": ["uscita AC", "Modalita"], ...}
Keys are language codes; values are substrings that should no longer appear in that
language's content.

Usage:
    python3 scan_residuals.py --terms terms.json \
        --templates 'docs/templates/page_eu-*/*.rst' 'docs/templates/page_shared/*/*.rst' \
        --feishu /tmp/spec.json /tmp/ph.json --scope EU

Feishu dumps are the JSON from `lark-cli api GET .../records --page-all --format json`.
Exit code is non-zero when residuals are found, so it can gate a check.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

LANG_ALIASES = {"uk": ("uk", "ukr")}  # field suffix variants


def txt(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "".join((s.get("text", "") or "") if isinstance(s, dict) else ("" if s is None else str(s)) for s in v)
    return str(v)


def field_lang(field, langs):
    fl = field.lower()
    for lang in langs:
        suffixes = LANG_ALIASES.get(lang, (lang,))
        for suf in suffixes:
            if fl.endswith("_" + suf) or fl in (f"icon_{suf}", f"text_{suf}", f"corrective_measures_{suf}", f"value_{suf}", f"row_label_{suf}", f"param_{suf}"):
                return lang
    return None


def path_lang(path, langs):
    for lang in langs:
        if re.search(rf"(?:^|[-/]){re.escape(lang)}(?:[-/]|$)", path):
            return lang
    return None


def doc_scope_value(fields):
    for key in ("document_key", "Document_key_link", "Region", "Model"):
        v = fields.get(key)
        if isinstance(v, list) and v:
            return " ".join(s.get("text", "") for s in v if isinstance(s, dict))
        if isinstance(v, str):
            return v
    return ""


def scan_templates(globs, terms):
    hits = []
    for g in globs:
        for f in glob.glob(g, recursive=True):
            if not os.path.isfile(f):
                continue
            content = open(f, encoding="utf-8", errors="replace").read()
            lang = path_lang(f, list(terms))
            check_langs = [lang] if lang else list(terms)
            for L in check_langs:
                for term in terms.get(L, []):
                    if term in content:
                        hits.append((f, L, term))
    return hits


def scan_feishu(files, terms, scope):
    hits = []
    langs = list(terms)
    for fn in files:
        data = json.load(open(fn, encoding="utf-8"))
        for rec in data.get("data", {}).get("items", []):
            fields = rec.get("fields", {})
            if scope:
                sv = doc_scope_value(fields)
                # keep rows in scope, plus shared rows (no document_key / Region at all)
                has_scope_keys = any(k in fields for k in ("document_key", "Document_key_link", "Region"))
                if has_scope_keys and scope not in sv:
                    continue
            for field, val in fields.items():
                L = field_lang(field, langs)
                if not L:
                    continue
                t = txt(val)
                for term in terms.get(L, []):
                    if term in t:
                        hits.append((f"{os.path.basename(fn)}::{field}", L, term))
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scan templates + Feishu dumps for residual OLD terms that should be gone.")
    ap.add_argument("--terms", required=True, help="JSON file: {lang: [old substrings]}")
    ap.add_argument("--templates", nargs="*", default=[], help="Glob(s) of repo files to scan")
    ap.add_argument("--feishu", nargs="*", default=[], help="lark-cli record JSON dump(s) to scan")
    ap.add_argument("--scope", default=None, help="Keep only Feishu rows whose document_key/Region contains this (e.g. EU); shared rows always kept")
    args = ap.parse_args(argv)
    terms = json.load(open(args.terms, encoding="utf-8"))

    t_hits = scan_templates(args.templates, terms)
    f_hits = scan_feishu(args.feishu, terms, args.scope)

    print(f"=== template residuals: {len(t_hits)} ===")
    for f, L, term in t_hits:
        print(f"  {f}  [{L}] {term!r}")
    print(f"=== feishu residuals: {len(f_hits)} ===")
    for f, L, term in f_hits:
        print(f"  {f}  [{L}] {term!r}")
    total = len(t_hits) + len(f_hits)
    print(f"\nTOTAL residuals: {total}  ({'CONVERGED' if total == 0 else 'NOT converged — apply or scope-explain each'})")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
