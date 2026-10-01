"""Freeze CQ-3.2 config validation, including ordering and existing crashes.

Inputs are all 27 configs and manifests frozen before the refactor. Filesystem
checks use an isolated tree; only its random absolute path is normalized.
Intentional behavior changes can regenerate with ``python -m
tests.test_validate_config_characterization --update``.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from tools import validate_config as subject

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CORPUS = FIXTURES / "config_validation_corpus.json"
GOLDEN = FIXTURES / "validate_config_golden.json"
REPLACEMENTS = (None, "", " ", "missing", "present.txt", "{model}", -1, 0, 1.5, True, [], {}, [""], ["en", "xx"])


def _paths(value, prefix=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield prefix + (key,)
            yield from _paths(item, prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value[:2]):
            yield prefix + (index,)
            yield from _paths(item, prefix + (index,))


def variants(cfg, *, recursive=True):
    yield "as-is", cfg
    for path in _paths(cfg):
        if not recursive and len(path) > 1:
            continue
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


def _supplement():
    """Valid sections let one-field mutations reach every validation segment."""
    paths = dict.fromkeys(("structured_data_dir", "page_blocks_dir"), "present-dir")
    paths.update(dict.fromkeys(("page_registry_csv", "spec_master_csv", "spec_footnotes_csv",
                               "spec_notes_csv", "spec_titles_csv"), "present.txt"))
    paths["docs_dir"] = "present-dir"
    paths["page_manifest"] = None
    source_keys = (f"{prefix}_source_{field}" for prefix in ("spec_rows", "page_placeholders")
                   for field in ("table_id", "table_id_env", "view_id", "view_id_env"))
    table = dict.fromkeys(("base_token_env", "table_id_env", "view_id_env", "table_id", "view_id"), "valid")
    return {
        "build": {"languages": ["en"], "default_model": "Model", "default_region": "US",
                  "include_lang_in_output_path": True, "targets": [{"model": "Model", "region": "US"}]},
        "paths": paths,
        "checks": {"allowed_foreign_identity_literals": ["valid"]},
        "sync": {"phase2": {"provider": "lark_cli", "cli_bin": "lark-cli", "base_token_env": "valid",
                            "export_root": "exports", "manifest_path": "manifest.json",
                            "spec_master_sources": dict.fromkeys(source_keys, "valid"),
                            "tables": {"spec_master": table, "unknown": {}, "lcd_icons": {}}}},
        "pages": [{"type": "rst_include", "file": "present.txt", "lang": "en"}],
    }


def _page_cases():
    pages = [
        {"type": "cover_pdf", "file": "present.txt"},
        {"type": "csv_page", "page": "spec", "langs": ["en"]},
        {"type": "generated_page", "page": "draft", "engine": "draft_v1", "recipe": "present.txt",
         "template": "present.txt", "langs": ["en"]},
        {"type": "pdf_insert", "langs": ["en", "fr"], "file_map": {"en": "present.txt"}},
        {"type": "rst_include", "file": "present.txt", "lang": "en"},
    ]
    for index, page in enumerate(pages):
        yield f"page-{index}", {"build": {"languages": ["en"]}, "pages": [page]}
    for text in ("asset:cover", "{model}.pdf", "missing.pdf"):
        yield text, {"build": {"languages": []}, "pages": [
            {"type": "cover_pdf", "file": text},
            {"type": "pdf_insert", "file_map": {"en": text}, "langs": ["en"]}]}


def snapshot():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    digests, total, exceptions = {}, 0, 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name, content in corpus["files"].items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        (root / "present-dir").mkdir()
        (root / "present.txt").touch()
        (root / "present-dir" / "local.txt").touch()
        cases = [(name, yaml.safe_load(raw), False) for name, raw in corpus["configs"].items()]
        cases += [("sections", _supplement(), True)]
        cases += [(name, cfg, True) for name, cfg in _page_cases()]
        # ROOT and environment are external boundaries; parser and validator run unchanged.
        with patch.object(subject, "ROOT", root), patch.dict(os.environ, {}, clear=True):
            for name, cfg, recursive in cases:
                lines = []
                for label, variant in variants(cfg, recursive=recursive):
                    for strict in (False, True):
                        try:
                            outcome = [(i.level, i.msg) for i in subject.validate(variant, strict)]
                        except Exception as exc:  # Existing exceptions are frozen, never swallowed in production.
                            outcome = f"!{type(exc).__name__}: {exc}"
                            exceptions += 1
                        line = json.dumps([label, strict, outcome], ensure_ascii=False)
                        lines.append(line.replace(str(root), "<ROOT>"))
                        total += 1
                digests[name] = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    return {"variant_count": total, "exception_count": exceptions, "config_digests": digests}


class ValidateConfigCharacterizationTest(unittest.TestCase):
    def test_outputs_and_exceptions_match_golden(self):
        self.assertEqual(json.loads(GOLDEN.read_text(encoding="utf-8")), snapshot())


if __name__ == "__main__":
    if "--update" in sys.argv:
        GOLDEN.write_text(json.dumps(snapshot(), indent=1) + "\n", encoding="utf-8")
        print(f"wrote {GOLDEN}")
    else:
        unittest.main()
