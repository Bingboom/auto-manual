"""Frozen CLI/report contracts; all Feishu records are supplied in memory."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import lang_asset_sweep as sweep


GOLDEN = Path(__file__).parent / "fixtures" / "lang_asset_sweep_cli_golden.json"


def snapshots():
    results = {}
    for case in ("help", "required-out", "missing-tokens", "empty", "forks", "terminology"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "report.md"
            adj = root / "adjudication.md"
            args = {
                "help": ["--help"],
                "required-out": [],
                "missing-tokens": ["--out", str(out)],
            }.get(case, ["--out", str(out), "--adjudication", str(adj),
                         "--repo-root", str(root), "--tm-base-token", "tm-fixture",
                         "--doc-base-token", "doc-fixture"])
            rows = {}
            if case in {"forks", "terminology"}:
                rows = {
                    sweep.TM_SENTENCE_TABLE: [
                        {"record_id": "rec1", "en": "Power", "ko": "전원", "Status": "Approved"},
                        {"record_id": "rec2", "en": "Power", "ko": "옛전원"},
                        {"record_id": "rec3", "en": "Power", "ko": ""},
                        {"record_id": "rec4", "en": "Mode", "ko": "모드"},
                        {"record_id": "rec5", "en": "Mode", "ko": ""},
                    ],
                    sweep.TM_TERMS_TABLE: [
                        {"record_id": "term1", "en": "Power", "ko": "test"},
                        {"record_id": "term2", "en": "Mode", "ko": "모드."},
                    ],
                }
                for lang, title in (("en", "Power"), ("ko", "전원")):
                    folder = root / "docs" / "templates" / f"page_eu-{lang}"
                    folder.mkdir(parents=True)
                    (folder / "01.rst").write_text(f"{title}\n========\n", encoding="utf-8")
            if case == "terminology":
                args.append("--terminology")
                (root / "data").mkdir()
                (root / "data" / "terminology_rules.csv").write_text(
                    "rule_id,lang,deprecated_regex,preferred,allow_regex,note\n"
                    "OLD-POWER,ko,옛전원,전원,,retired\n", encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with (
                patch.object(sys, "argv", ["lang_asset_sweep.py", *args]),
                patch.dict(os.environ, {"FEISHU_TRANSLATION_MEMORY_BASE_TOKEN": "",
                                        "FEISHU_PHASE2_BASE_TOKEN": ""}),
                patch.object(sweep, "lark_dump", side_effect=lambda base, table: rows.get(table, [])),
                redirect_stdout(stdout), redirect_stderr(stderr),
            ):
                try:
                    code = sweep.main()
                except SystemExit as exc:
                    code = exc.code
            results[case] = {
                "exit_code": code,
                "stdout": stdout.getvalue().replace(tmp, "<TMP>"),
                "stderr": stderr.getvalue().replace(tmp, "<TMP>"),
                "report": out.read_text(encoding="utf-8") if out.exists() else None,
                "adjudication": adj.read_text(encoding="utf-8") if adj.exists() else None,
            }
    return results


class LangAssetSweepCliTests(unittest.TestCase):
    def test_cli_and_reports_match_frozen_contract(self):
        self.assertEqual(snapshots(), json.loads(GOLDEN.read_text(encoding="utf-8")))


if __name__ == "__main__":
    if sys.argv[1:] == ["--update"]:
        GOLDEN.write_text(json.dumps(snapshots(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        unittest.main()
