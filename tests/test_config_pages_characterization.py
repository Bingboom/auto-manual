"""CQ-3.2: immutable config/page parsing outcomes; regenerate with --update."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

import yaml

from tools.config_pages import parse_config_pages
from tools.page_manifest import resolve_page_manifest_path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CORPUS = FIXTURES / "config_pages_corpus.json"
GOLDEN = FIXTURES / "config_pages_golden.json"
REPLACEMENTS = (None, "", " ", "x", "p01_slot", "../slot", -1, 0, 99, 1.5, True, [], {}, [""], ["en", "xx"])


def _paths(value, prefix=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield prefix + (key,)
            yield from _paths(item, prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value[:2]):
            yield prefix + (index,)
            yield from _paths(item, prefix + (index,))


def variants(cfg):
    yield "as-is", cfg
    for path in _paths(cfg):
        for action, value in [("delete", None), *[("set", v) for v in REPLACEMENTS]]:
            variant = copy.deepcopy(cfg)
            target = variant
            for step in path[:-1]:
                target = target[step]
            if action == "delete":
                del target[path[-1]]
            else:
                target[path[-1]] = value
            yield json.dumps([path, action, value]), variant


def _supplements():
    pages = [
        {"type": "cover_pdf", "file": " cover.pdf "},
        {"type": "csv_page", "page": " spec ", "source": "phase2", "langs": ["en"], "include_dir": " inc "},
        {"type": "generated_page", "page": " draft ", "engine": "draft_v1", "recipe": " recipe ",
         "template": " template ", "langs": ["en"], "include_dir": " inc ",
         "model_overrides": {"Model": {"recipe": " model recipe ", "template": " model template "}}},
        {"type": "pdf_insert", "langs": ["en"], "file_map": {"en": " en.pdf ", "fr": " fr.pdf "}},
        {"type": "rst_include", "file": " include.rst ", "lang": " en ",
         "lang_blocks": True, "ordinal_neutral": False},
    ]
    for page in pages:
        page.update(capability=" capability ", slot_id=" slot ")
        yield page["type"], {"pages": [page], "default_languages": ["en"], "model": "Model"}
    generated = pages[2]
    for override in ({"": {}}, {1: {}}, {"Model": {"unknown": 1}}, {"Model": {"recipe": "", "template": 3}}):
        yield f"overrides-{override}", {"pages": [{**generated, "model_overrides": override}]}
    yield "duplicate-slot", {"pages": [pages[0], pages[0]]}
    yield "mixed-slot", {"pages": [pages[0], {"type": "cover_pdf", "file": "other.pdf"}]}
    yield "invalid-consumes-slot", {"pages": [{**pages[0], "file": None}, pages[0]]}
    yield "lang-blocks-on-cover", {"pages": [{**pages[0], "lang_blocks": True}]}
    yield "ordinal-neutral-on-cover", {"pages": [{**pages[0], "ordinal_neutral": True}]}


def _cases(corpus):
    for name, raw in corpus["configs"].items():
        cfg = yaml.safe_load(raw)
        build = cfg.get("build", {})
        pages = cfg.get("pages")
        manifest = resolve_page_manifest_path(cfg, root=Path("."), model=build.get("default_model"),
                                              region=build.get("default_region"))
        manifest_key = manifest.as_posix() if manifest is not None else None
        if manifest_key in corpus["files"]:
            data = yaml.safe_load(corpus["files"][manifest_key])
            pages = data.get("pages") if isinstance(data, dict) else data
        yield name, {"pages": pages, "default_languages": build.get("languages"), "model": build.get("default_model")}
    for name, raw in corpus["files"].items():
        data = yaml.safe_load(raw)
        pages = data.get("pages") if isinstance(data, dict) else data
        yield "manifest:" + name, {"pages": pages, "default_languages": ["en"], "model": "JE-1000F"}
    yield from _supplements()


def snapshot():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    digests, total, exceptions = {}, 0, 0
    for name, cfg in _cases(corpus):
        lines = []
        for label, variant in variants(cfg):
            try:
                pages, issues = parse_config_pages(variant.get("pages"),
                                                  default_languages=variant.get("default_languages"),
                                                  model=variant.get("model"))
                outcome = [[asdict(page) for page in pages], [asdict(issue) for issue in issues]]
            except Exception as exc:  # Exceptions are part of the existing public behavior.
                outcome = f"!{type(exc).__name__}: {exc}"
                exceptions += 1
            lines.append(json.dumps([label, outcome], ensure_ascii=False))
            total += 1
        digests[name] = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    return {"variant_count": total, "exception_count": exceptions, "config_digests": digests}


class ConfigPagesCharacterizationTest(unittest.TestCase):
    def test_pages_issues_and_exceptions_match_golden(self):
        self.assertEqual(json.loads(GOLDEN.read_text(encoding="utf-8")), snapshot())


if __name__ == "__main__":
    if "--update" in sys.argv:
        GOLDEN.write_text(json.dumps(snapshot(), indent=1) + "\n", encoding="utf-8")
        print(f"wrote {GOLDEN}")
    else:
        unittest.main()
