#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.source_intake_staging import (  # noqa: E402
    STAGING_OVERRIDE_SCHEMA_VERSION,
    build_lark_staging_payload,
    build_staging_plan,
    decode_record_rows,
    write_staging_outputs,
)


def _row(*, page: str, section: str, row_key: str, value: str, value_ko: str,
         slot: str = "", line: int = 1, label: str = "Label", label_ko: str = "라벨") -> dict[str, object]:
    return {
        "Page": [page], "Section": [section], "Row_key": row_key, "Slot_key": slot,
        "Line_order": line, "Row_label_source": label, "Value_source": value,
        "Param_source": "", "Row_label_ko": label_ko, "Value_ko": value_ko, "Param_ko": "",
    }


class DecodeRecordRowsTests(unittest.TestCase):
    def test_decodes_lark_columnar_envelope(self):
        payload = {
            "ok": True,
            "data": {
                "fields": ["Row_key", "Value_source"],
                "data": [["capacity", "2048 Wh"]],
                "record_id_list": ["rec1"],
            },
        }
        self.assertEqual(
            decode_record_rows(payload),
            [{"Row_key": "capacity", "Value_source": "2048 Wh", "_record_id": "rec1"}],
        )

    def test_zero_line_order_is_rejected_instead_of_defaulted(self):
        row = _row(
            page="specifications",
            section="GENERAL INFO",
            row_key="capacity",
            value="2048 Wh",
            value_ko="2048 Wh",
            line=0,
        )
        with self.assertRaisesRegex(ValueError, "invalid Line_order"):
            build_staging_plan(
                spec_candidates=[row],
                spec_sibling=[row],
                placeholder_sibling=[],
                overrides={},
                document_key="JE-2000E_KR",
                localized_lang="ko",
            )


class StagingPlanTests(unittest.TestCase):
    def setUp(self):
        self.spec_sibling = [
            _row(page="specifications", section="GENERAL INFO", row_key="capacity",
                 value="1024 Wh", value_ko="1024 Wh", label="Capacity", label_ko="용량"),
        ]
        self.placeholders = [
            _row(page="operation_guide", section="SETTINGS", row_key="standby",
                 slot="value", value="2 hours", value_ko="2시간", label="Standby", label_ko=""),
        ]
        self.candidates = [{
            "Page": "specifications", "Section": "GENERAL INFO", "Row_key": "capacity",
            "Slot_key": "", "Line_order": 1, "label": "Capacity", "value": "2048 Wh",
            "status": "transformed", "spec_field": "额定容量", "raw": "2048Wh",
        }]
        self.overrides = {
            "schema_version": STAGING_OVERRIDE_SCHEMA_VERSION,
            "rows": [{
                "key": {"Page": "specifications", "Section": "GENERAL INFO", "Row_key": "capacity",
                        "Slot_key": "", "Line_order": 1},
                "fields": {"Value_ko": "2048 Wh", "note": "confirmed by spec"},
            }],
        }

    def test_builds_current_create_records_payload(self):
        plan = build_staging_plan(
            spec_candidates=self.candidates,
            spec_sibling=self.spec_sibling,
            placeholder_sibling=self.placeholders,
            overrides=self.overrides,
            document_key="JE-2000E_KR",
            localized_lang="ko",
        )
        self.assertEqual(plan["summary"]["row_count"], 2)
        self.assertEqual(plan["summary"]["spec_count"], 1)
        payload = build_lark_staging_payload(plan)
        self.assertEqual(list(payload), ["create_records"])
        self.assertNotIn("fields", payload)
        self.assertEqual(payload["create_records"][0]["document_key"], "JE-2000E_KR")
        self.assertTrue(all(record["确认"] is False for record in payload["create_records"]))
        inherited = next(record for record in payload["create_records"] if record["Row_key"] == "standby")
        self.assertEqual(inherited["状态"], "⚠️需确认")
        self.assertIn("Inherited from region sibling", inherited["备注"])

    def test_changed_source_requires_localized_override(self):
        with self.assertRaisesRegex(ValueError, "localized value must move"):
            build_staging_plan(
                spec_candidates=self.candidates,
                spec_sibling=self.spec_sibling,
                placeholder_sibling=self.placeholders,
                overrides={},
                document_key="JE-2000E_KR",
                localized_lang="ko",
            )

    def test_unknown_override_abstains(self):
        overrides = {"rows": [{
            "key": {"Page": "specifications", "Section": "GENERAL INFO", "Row_key": "missing",
                    "Slot_key": "", "Line_order": 1},
            "fields": {"Value_ko": "x"},
        }]}
        with self.assertRaisesRegex(ValueError, "does not match a sibling row"):
            build_staging_plan(
                spec_candidates=self.candidates,
                spec_sibling=self.spec_sibling,
                placeholder_sibling=self.placeholders,
                overrides=overrides,
                document_key="JE-2000E_KR",
                localized_lang="ko",
            )

    def test_writes_reviewable_outputs(self):
        plan = build_staging_plan(
            spec_candidates=self.candidates,
            spec_sibling=self.spec_sibling,
            placeholder_sibling=self.placeholders,
            overrides=self.overrides,
            document_key="JE-2000E_KR",
            localized_lang="ko",
        )
        with tempfile.TemporaryDirectory() as raw:
            paths = write_staging_outputs(plan, Path(raw))
            payload = json.loads(paths["payload"].read_text(encoding="utf-8"))
            self.assertEqual(len(payload["create_records"]), 2)
            self.assertIn("JE-2000E_KR", paths["review"].read_text(encoding="utf-8"))

    def test_stage_plan_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            inputs = {
                "candidates.json": self.candidates,
                "spec-sibling.json": self.spec_sibling,
                "placeholder-sibling.json": self.placeholders,
                "overrides.json": self.overrides,
            }
            for name, payload in inputs.items():
                (root / name).write_text(json.dumps(payload), encoding="utf-8")
            out_dir = root / "out"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "tools" / "source_intake.py"),
                    "stage-plan",
                    "--spec-candidates", str(root / "candidates.json"),
                    "--spec-sibling", str(root / "spec-sibling.json"),
                    "--placeholder-sibling", str(root / "placeholder-sibling.json"),
                    "--overrides", str(root / "overrides.json"),
                    "--document-key", "JE-2000E_KR",
                    "--localized-lang", "ko",
                    "--out", str(out_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("STAGING 2 SPECS 1 PLACEHOLDERS 1", completed.stdout)
            payload = json.loads(
                (out_dir / "spec_intake_staging_payload.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(payload["create_records"]), 2)


if __name__ == "__main__":
    unittest.main()
