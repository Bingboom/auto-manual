from __future__ import annotations

import contextlib
import csv
import io
import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from tools.source_intake import main as source_intake_main
from tools.source_intake_closure import (
    build_apply_report,
    build_approval_report,
    build_closure_report,
    run_check_commands,
    write_apply_report,
    write_approval_report,
)
from tools.source_intake_model import (
    TARGET_MANUAL_COPY,
    TARGET_PAGE_PLACEHOLDERS,
    TARGET_SPEC_FOOTNOTES,
    TARGET_SPEC_MASTER,
)
from tools.source_intake_runtime import (
    build_change_request_report,
    candidates_payload,
    enrich_candidates_with_snapshot,
    extract_candidates_from_text,
)
from tools.source_record_index import build_index, index_json_text


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fixture_data_root(root: Path) -> None:
    _write_csv(
        root / "Spec_Master.csv",
        [
            "document_key",
            "Page",
            "Section",
            "Line_order",
            "Row_key",
            "Slot_key",
            "Row_label_source",
            "Param_source",
            "Value_source",
        ],
        [
            {
                "document_key": "JE-2000F_EU",
                "Page": "specifications",
                "Section": "OUTPUT PORTS",
                "Line_order": "1",
                "Row_key": "usb_c",
                "Slot_key": "100w",
                "Row_label_source": "USB-C Output 100W",
                "Param_source": "",
                "Value_source": "100 W",
            },
            {
                "document_key": "JE-2000F_EU",
                "Page": "Product overview",
                "Section": "FRONT VIEW",
                "Line_order": "1",
                "Row_key": "power_button",
                "Slot_key": "front.label",
                "Row_label_source": "Power Button",
                "Param_source": "",
                "Value_source": "Power",
            },
        ],
    )
    _write_csv(
        root / "Manual_Copy_Source.csv",
        ["copy_key", "source_text", "notes"],
        [{"copy_key": "product_overview.page_title", "source_text": "PRODUCT OVERVIEW", "notes": ""}],
    )
    (root / "source_record_index.json").write_text(
        index_json_text(
            build_index(
                {
                    "Spec_Master": [
                        (
                            {
                                "document_key": "JE-2000F_EU",
                                "Row_key": "usb_c",
                                "Slot_key": "100w",
                                "Line_order": "1",
                                "Section": "OUTPUT PORTS",
                            },
                            "recSpec",
                        )
                    ],
                    "Page_Placeholders_Source": [
                        (
                            {
                                "document_key": "JE-2000F_EU",
                                "Row_key": "power_button",
                                "Slot_key": "front.label",
                                "Line_order": "1",
                                "Section": "FRONT VIEW",
                            },
                            "recPlaceholder",
                        )
                    ],
                    "Manual_Copy_Source": [
                        (
                            {
                                "copy_key": "product_overview.page_title",
                                "Is_Latest": "TRUE",
                            },
                            "recCopy",
                        )
                    ],
                }
            )
        ),
        encoding="utf-8",
    )


_SOURCE = """# Specifications

## OUTPUT PORTS

| Row_key | Slot_key | Row_label_source | Value_source |
| --- | --- | --- | --- |
| usb_c | 100w | USB-C Output 100W | 100 W max. |
|  |  | Mystery Label | Mystery value |

# Product Overview

## FRONT VIEW

| Row_key | Slot_key | Row_label_source | Value_source |
| --- | --- | --- | --- |
| power_button | front.label | Power Button | Main Power |

# Copy

| copy_key | page_id | copy_type | source_text |
| --- | --- | --- | --- |
| product_overview.page_title | 03_product_overview | page_title | PRODUCT OVERVIEW |

# Footnotes

| Footnote_id | Text |
| --- | --- |
| ac_bypass | AC bypass footnote. |
"""


class _MemorySourceTableTransport:
    def __init__(self, rows: dict[tuple[str, str, str], str]) -> None:
        self.rows = dict(rows)

    def get(self, *, table: str, record_id: str, field: str) -> str:
        return self.rows[(table, record_id, field)]

    def upsert(self, *, table: str, record_id: str, field: str, value: str) -> None:
        self.rows[(table, record_id, field)] = value


def _fixture_candidates_and_change_report(data_root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    candidates = enrich_candidates_with_snapshot(
        extract_candidates_from_text(_SOURCE, document_key="JE-2000F_EU"),
        data_root=data_root,
    )
    return candidates, build_change_request_report(candidates, data_root=data_root)


def _run_cli(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return source_intake_main(argv)


class SourceIntakeTests(unittest.TestCase):
    def test_extracts_candidates_for_supported_source_tables(self) -> None:
        candidates = extract_candidates_from_text(
            _SOURCE,
            document_key="JE-2000F_EU",
            source_lang="en",
            version="1.0",
        )

        targets = [candidate["target_table"] for candidate in candidates]
        self.assertIn(TARGET_SPEC_MASTER, targets)
        self.assertIn(TARGET_PAGE_PLACEHOLDERS, targets)
        self.assertIn(TARGET_MANUAL_COPY, targets)
        self.assertIn(TARGET_SPEC_FOOTNOTES, targets)
        missing_key = next(candidate for candidate in candidates if candidate["fields"].get("Row_label_source") == "Mystery Label")
        self.assertEqual(missing_key["status"], "needs_review")
        self.assertIn("missing Row_key", missing_key["warnings"][0])

    def test_snapshot_enrichment_classifies_updates_and_noops(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td)
            _fixture_data_root(data_root)
            candidates = enrich_candidates_with_snapshot(
                extract_candidates_from_text(_SOURCE, document_key="JE-2000F_EU"),
                data_root=data_root,
            )

        by_table = {candidate["target_table"]: candidate for candidate in candidates if candidate["status"] == "ready"}
        self.assertEqual(by_table[TARGET_SPEC_MASTER]["operation"], "update")
        self.assertEqual(by_table[TARGET_PAGE_PLACEHOLDERS]["operation"], "update")
        self.assertEqual(by_table[TARGET_MANUAL_COPY]["operation"], "noop")
        self.assertEqual(by_table[TARGET_SPEC_FOOTNOTES]["operation"], "create")

    def test_builds_change_requests_for_existing_updates_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td)
            _fixture_data_root(data_root)
            _candidates, report = _fixture_candidates_and_change_report(data_root)

        self.assertEqual(report["summary"]["requests"], 2)
        by_table = {request["table"]: request for request in report["requests"]}
        self.assertEqual(by_table[TARGET_SPEC_MASTER]["record_id"], "recSpec")
        self.assertEqual(by_table[TARGET_SPEC_MASTER]["field"], "Value_source")
        self.assertEqual(by_table[TARGET_SPEC_MASTER]["new_value"], "100 W max.")
        self.assertEqual(by_table[TARGET_PAGE_PLACEHOLDERS]["record_id"], "recPlaceholder")
        self.assertNotIn(TARGET_SPEC_FOOTNOTES, by_table)

    def test_cli_writes_candidates_report_and_change_request(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_root = root / "phase2"
            out_dir = root / "out"
            source = root / "source.md"
            source.write_text(_SOURCE, encoding="utf-8")
            _fixture_data_root(data_root)

            exit_code = _run_cli(
                [
                    "run",
                    "--input",
                    str(source),
                    "--document-key",
                    "JE-2000F_EU",
                    "--data-root",
                    str(data_root),
                    "--out",
                    str(out_dir),
                    "--run-id",
                    "test-source-intake",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((out_dir / "source_intake_candidates.json").is_file())
            self.assertTrue((out_dir / "source_intake_report.md").is_file())
            self.assertTrue((out_dir / "source_intake_source_table_change_request.json").is_file())
            payload = json.loads((out_dir / "source_intake_candidates.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["candidates"], 5)
            self.assertEqual(payload["summary"]["needs_review"], 1)

    def test_approval_report_selects_resolved_change_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td)
            _fixture_data_root(data_root)
            _candidates, change_report = _fixture_candidates_and_change_report(data_root)

        approval = build_approval_report(
            change_report,
            approved_hashes=["unknown-hash"],
            approve_all_resolved=True,
            reviewer="qa",
        )

        self.assertEqual(approval["summary"]["requests"], 2)
        self.assertEqual(approval["summary"]["resolved_requests"], 2)
        self.assertEqual(approval["summary"]["approved_hashes"], 2)
        self.assertEqual(approval["summary"]["unknown_hashes"], 1)
        self.assertEqual(approval["unknown_hashes"], ["unknown-hash"])

    def test_apply_report_dry_run_and_write_use_existing_writer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_root = root / "phase2"
            out_dir = root / "out"
            _fixture_data_root(data_root)
            _candidates, change_report = _fixture_candidates_and_change_report(data_root)
            change_path = out_dir / "source_intake_source_table_change_request.json"
            change_path.parent.mkdir(parents=True)
            change_path.write_text(json.dumps(change_report, ensure_ascii=False), encoding="utf-8")
            approval = build_approval_report(change_report, approved_hashes=[], approve_all_resolved=True)
            approval_path = write_approval_report(approval, out_dir)["approval"]

            dry_run = build_apply_report(change_path, approval_path=approval_path)
            transport = _MemorySourceTableTransport(
                {
                    (TARGET_SPEC_MASTER, "recSpec", "Value_source"): "100 W",
                    (TARGET_PAGE_PLACEHOLDERS, "recPlaceholder", "Value_source"): "Power",
                }
            )
            written = build_apply_report(
                change_path,
                approval_path=approval_path,
                transport=transport,
                write=True,
            )

        self.assertFalse(dry_run["external_write"])
        self.assertEqual(dry_run["summary"]["apply"], 2)
        self.assertEqual({item["status"] for item in dry_run["applied"]}, {"planned"})
        self.assertTrue(written["external_write"])
        self.assertEqual(written["summary"]["written"], 2)
        self.assertEqual(transport.rows[(TARGET_SPEC_MASTER, "recSpec", "Value_source")], "100 W max.")
        self.assertEqual(transport.rows[(TARGET_PAGE_PLACEHOLDERS, "recPlaceholder", "Value_source")], "Main Power")

    def test_closure_report_passes_with_sync_and_build_checks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_root = root / "phase2"
            out_dir = root / "out"
            _fixture_data_root(data_root)
            candidates, change_report = _fixture_candidates_and_change_report(data_root)
            candidates_path = out_dir / "source_intake_candidates.json"
            change_path = out_dir / "source_intake_source_table_change_request.json"
            out_dir.mkdir(parents=True)
            candidates_path.write_text(
                json.dumps(
                    candidates_payload(
                        candidates,
                        run_id="closure-test",
                        source="fixture",
                        document_key="JE-2000F_EU",
                        data_root=data_root,
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            change_path.write_text(json.dumps(change_report, ensure_ascii=False), encoding="utf-8")
            approval = build_approval_report(change_report, approved_hashes=[], approve_all_resolved=True)
            approval_path = write_approval_report(approval, out_dir)["approval"]
            apply_path = write_apply_report(build_apply_report(change_path, approval_path=approval_path), out_dir)[
                "apply"
            ]
            check_commands = [
                f"sync-data-fixture={shlex.quote(sys.executable)} -c \"print('sync ok')\"",
                f"build-fixture={shlex.quote(sys.executable)} -c \"print('build ok')\"",
            ]
            command_results = run_check_commands(check_commands, cwd=root)
            closure = build_closure_report(
                candidates_path=candidates_path,
                change_request_path=change_path,
                approval_path=approval_path,
                apply_report_path=apply_path,
                command_results=command_results,
            )

        self.assertTrue(closure["summary"]["passed"])
        self.assertTrue(all(closure["phase_status"].values()))

    def test_cli_runs_p4_to_p7_dry_run_closure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_root = root / "phase2"
            out_dir = root / "out"
            source = root / "source.md"
            source.write_text(_SOURCE, encoding="utf-8")
            _fixture_data_root(data_root)

            self.assertEqual(
                _run_cli(
                    [
                        "run",
                        "--input",
                        str(source),
                        "--document-key",
                        "JE-2000F_EU",
                        "--data-root",
                        str(data_root),
                        "--out",
                        str(out_dir),
                        "--run-id",
                        "test-source-intake",
                    ]
                ),
                0,
            )
            self.assertEqual(
                _run_cli(
                    [
                        "approve",
                        "--report",
                        str(out_dir / "source_intake_source_table_change_request.json"),
                        "--approve-all-resolved",
                        "--reviewer",
                        "qa",
                        "--out",
                        str(out_dir),
                    ]
                ),
                0,
            )
            self.assertEqual(
                _run_cli(
                    [
                        "apply",
                        "--report",
                        str(out_dir / "source_intake_source_table_change_request.json"),
                        "--approval",
                        str(out_dir / "source_intake_approval.json"),
                        "--out",
                        str(out_dir),
                    ]
                ),
                0,
            )
            self.assertEqual(
                _run_cli(
                    [
                        "verify",
                        "--candidates",
                        str(out_dir / "source_intake_candidates.json"),
                        "--change-request",
                        str(out_dir / "source_intake_source_table_change_request.json"),
                        "--approval",
                        str(out_dir / "source_intake_approval.json"),
                        "--apply-report",
                        str(out_dir / "source_intake_apply.json"),
                        "--check-command",
                        f"sync-data-fixture={shlex.quote(sys.executable)} -c \"print('sync ok')\"",
                        "--check-command",
                        f"build-fixture={shlex.quote(sys.executable)} -c \"print('build ok')\"",
                        "--cwd",
                        str(root),
                        "--out",
                        str(out_dir),
                    ]
                ),
                0,
            )

            closure = json.loads((out_dir / "source_intake_closure.json").read_text(encoding="utf-8"))
            self.assertTrue(closure["summary"]["passed"])
            self.assertTrue((out_dir / "source_intake_closure.md").is_file())


if __name__ == "__main__":
    unittest.main()
