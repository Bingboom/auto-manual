from __future__ import annotations

import contextlib
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools import ops_catalog_sync as sync_tool


BASE_URL = "https://ht-doc.readthedocs.io"

# Realistic rows: taken from the 2026-09-19 live snapshot of the ops catalog
# sheet (rev04 evidence), trimmed to three books.
HEADER = "文档ID,型号,市场,语言,当前版本,正文链接,根别名链接,语言范围声明,目标构建时间UTC,内容提交,收录状态,负责人,运营状态,下次复盘日期,运营备注"
ROW_JBP_EN = (
    "JBP-2000B/EU/en,JBP-2000B,EU,en,2.0-20260913,"
    "https://ht-doc.readthedocs.io/JBP-2000B/EU/en/md/manual_jbp2000b_eu.html,"
    "https://ht-doc.readthedocs.io/manual_jbp2000b_eu.html,single,"
    "2026-09-13T23:13:00+00:00,108e1c9f0fe0eeab2d042fd6f1b526b3dac6559f,发布目录收录,,待评估,,"
)
ROW_H_EN_STALE = (
    "JE-1000H/EU/en,JE-1000H,EU,en,2.0-20260913,"
    "https://ht-doc.readthedocs.io/JE-1000H/EU/en/md/manual_je1000h_eu_en.html,"
    "https://ht-doc.readthedocs.io/manual_je1000h_eu_en.html,single,"
    "2026-09-13T22:55:51+00:00,505c484a838740a12823fa4ba78af1fb4c04d81c,发布目录收录,夏冰,跟进中,2026-10-01,手工备注"
)


def target_payload(
    model: str,
    region: str,
    lang: str,
    *,
    version: str = "2.0",
    built_at: str = "2026-09-16T09:54:02+00:00",
    git_ref: str = "c99b7169e3a16381d235d6cf5bf171962b0ad90b",
    language_scope: str = "single",
    legacy_default: bool = False,
    stem: str | None = None,
) -> dict:
    if stem is None:
        stem = f"manual_{model.replace('-', '').lower()}_{region.lower()}_{lang}"
    payload = {
        "schema_version": "auto-manual-web-publish-target/v2",
        "model": model,
        "region": region,
        "lang": lang,
        "version": version,
        "built_at": built_at,
        "git_ref": git_ref,
        "route": f"{model}/{region}/{lang}/md",
        "manual": f"{stem}.md",
        "language_scope": language_scope,
        "legacy_default": legacy_default,
    }
    if legacy_default:
        payload["legacy_route"] = f"{model}/{region}/md"
        payload["legacy_aliases"] = [stem]
    return payload


def manifest_payload(targets: list[dict]) -> dict:
    return {
        "schema_version": sync_tool.MANIFEST_SCHEMA,
        "built_at": "2026-09-17T07:23:17+00:00",
        "targets": targets,
    }


def annotated_csv(rows: list[str], *, start_row: int = 1) -> str:
    return "\n".join(f"[row={start_row + index}] {row}" for index, row in enumerate(rows))


class FakeRunner:
    """Canned lark-cli transport: records every arg list, serves per-command
    payloads, and lets tests mutate the sheet state between calls."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.grid_rows = 60
        self.sheet_lines: dict[int, str] = {}
        self.fail_ranges: set[str] = set()
        self.bitable_pages: list[dict] = []
        self.revision = 27

    def set_sheet(self, lines: list[str]) -> None:
        self.sheet_lines = {index + 1: line for index, line in enumerate(lines)}

    def _flag(self, args: list[str], name: str) -> str:
        return args[args.index(name) + 1]

    def __call__(self, *, cli_bin: str, args: list[str]) -> dict:
        self.calls.append(list(args))
        command = args[1]
        if command == "+workbook-info":
            # Real 1.0.69 shape: row_count sits flat on the sheet entry
            # (live probe 2026-09-19); grid_properties is the defensive
            # fallback shape also accepted by sheet_grid_rows.
            return {
                "ok": True,
                "data": {
                    "sheets": [
                        {"sheet_id": "15c75c", "sheet_name": "说明书目录", "row_count": self.grid_rows, "column_count": 20}
                    ]
                },
            }
        if command == "+revision-get":
            return {"ok": True, "data": {"revision": self.revision}}
        if command == "+csv-get":
            cell_range = self._flag(args, "--range")
            start, end = cell_range.split(":")
            first = int("".join(ch for ch in start if ch.isdigit()))
            last = int("".join(ch for ch in end if ch.isdigit()))
            lines = [
                f"[row={row}] " + self.sheet_lines.get(row, "," * 14)
                for row in range(first, min(last, self.grid_rows) + 1)
            ]
            return {"ok": True, "data": {"annotated_csv": "\n".join(lines), "revision": self.revision}}
        if command == "+cells-set":
            cell_range = self._flag(args, "--range")
            if cell_range in self.fail_ranges:
                raise RuntimeError(f"injected failure for {cell_range}")
            cells = json.loads(self._flag(args, "--cells"))
            start, _end = cell_range.split(":")
            row_number = int("".join(ch for ch in start if ch.isdigit()))
            existing = next(csv.reader(io.StringIO(self.sheet_lines.get(row_number, "," * 14))))
            existing = (existing + [""] * 15)[:15]
            offset = ord(start[0]) - ord("A")
            if "--allow-overwrite=false" in args:
                touched = existing[offset : offset + len(cells[0])]
                if any(str(value).strip() for value in touched):
                    raise RuntimeError("target cells are not empty")
            for index, cell in enumerate(cells[0]):
                if "value" in cell:
                    existing[offset + index] = str(cell["value"])
            buffer = io.StringIO()
            csv.writer(buffer, lineterminator="").writerow(existing)
            self.sheet_lines[row_number] = buffer.getvalue()
            self.revision += 1
            return {"ok": True, "data": {"updated_cells_count": len(cells[0])}}
        if command == "+record-list":
            offset = int(self._flag(args, "--offset"))
            if offset == 0 and self.bitable_pages:
                return self.bitable_pages[0]
            return {"ok": True, "data": {"fields": [], "data": [], "record_id_list": []}}
        raise AssertionError(f"unexpected lark-cli command: {args}")


def make_ops(runner: FakeRunner) -> sync_tool.LarkOps:
    return sync_tool.LarkOps(cli_bin="lark-cli", identity="bot", runner=runner)


class CatalogTargetTests(unittest.TestCase):
    def test_machine_values_with_and_without_alias(self) -> None:
        payload = manifest_payload(
            [
                target_payload("JBP-2000B", "EU", "en", version="2.0-20260913", legacy_default=True, stem="manual_jbp2000b_eu"),
                target_payload("JE-1000H", "EU", "de"),
            ]
        )
        targets = sync_tool.catalog_targets(payload, base_url=BASE_URL)
        by_key = {target.key: target for target in targets}
        with_alias = by_key[("JBP-2000B", "EU", "en")]
        self.assertEqual(
            with_alias.page_url,
            "https://ht-doc.readthedocs.io/JBP-2000B/EU/en/md/manual_jbp2000b_eu.html",
        )
        self.assertEqual(
            with_alias.alias_url, "https://ht-doc.readthedocs.io/manual_jbp2000b_eu.html"
        )
        no_alias = by_key[("JE-1000H", "EU", "de")]
        self.assertEqual(no_alias.alias_url, "")
        values = with_alias.machine_values()
        self.assertEqual(len(values), sync_tool.MACHINE_COL_COUNT)
        self.assertEqual(values[0], "JBP-2000B/EU/en")
        self.assertEqual(values[10], "发布目录收录")

    def test_unsafe_alias_is_rejected(self) -> None:
        bad = target_payload("JBP-2000B", "EU", "en", legacy_default=True, stem="manual_jbp2000b_eu")
        bad["legacy_aliases"] = ["../evil"]
        with self.assertRaises(RuntimeError):
            sync_tool.catalog_targets(manifest_payload([bad]), base_url=BASE_URL)

    def test_manifest_schema_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            sync_tool.manifest_targets({"schema_version": "wrong", "targets": []})


class SheetParsingTests(unittest.TestCase):
    def test_parses_quoted_commas_and_pads_columns(self) -> None:
        line = '[row=2] JBP-2000B/EU/en,JBP-2000B,EU,en,"2,0",x,y,single,t,g,发布目录收录'
        rows = sync_tool.parse_annotated_csv(line)
        self.assertEqual(rows[0][0], 2)
        self.assertEqual(rows[0][1][4], "2,0")
        self.assertEqual(len(rows[0][1]), 15)

    def test_header_mismatch_refuses_everything(self) -> None:
        data = {"annotated_csv": annotated_csv(["列A,列B", ROW_JBP_EN])}
        with self.assertRaisesRegex(RuntimeError, "header"):
            sync_tool.load_sheet_rows(data)

    def test_missing_row_prefix_is_an_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "row=N"):
            sync_tool.parse_annotated_csv("no prefix here")


class PlanSyncTests(unittest.TestCase):
    def _rows(self, lines: list[str]) -> list[sync_tool.SheetRow]:
        return sync_tool.load_sheet_rows({"annotated_csv": annotated_csv([HEADER, *lines])})

    def test_identical_rows_produce_no_writes(self) -> None:
        payload = manifest_payload(
            [
                target_payload(
                    "JBP-2000B",
                    "EU",
                    "en",
                    version="2.0-20260913",
                    built_at="2026-09-13T23:13:00+00:00",
                    git_ref="108e1c9f0fe0eeab2d042fd6f1b526b3dac6559f",
                    legacy_default=True,
                    stem="manual_jbp2000b_eu",
                )
            ]
        )
        targets = sync_tool.catalog_targets(payload, base_url=BASE_URL)
        plan = sync_tool.plan_sync(targets, self._rows([ROW_JBP_EN]))
        self.assertFalse(plan.has_writes)
        self.assertEqual(len(plan.in_sync), 1)

    def test_human_column_differences_do_not_trigger_updates(self) -> None:
        payload = manifest_payload(
            [
                target_payload(
                    "JBP-2000B",
                    "EU",
                    "en",
                    version="2.0-20260913",
                    built_at="2026-09-13T23:13:00+00:00",
                    git_ref="108e1c9f0fe0eeab2d042fd6f1b526b3dac6559f",
                    legacy_default=True,
                    stem="manual_jbp2000b_eu",
                )
            ]
        )
        targets = sync_tool.catalog_targets(payload, base_url=BASE_URL)
        with_owner = ROW_JBP_EN.rsplit(",发布目录收录,,待评估,,", 1)[0] + ",发布目录收录,夏冰,跟进中,2026-12-01,备注"
        plan = sync_tool.plan_sync(targets, self._rows([with_owner]))
        self.assertFalse(plan.has_writes)

    def test_stale_machine_columns_plan_an_update_and_keep_human_values(self) -> None:
        payload = manifest_payload(
            [target_payload("JE-1000H", "EU", "en", version="2.0", legacy_default=True)]
        )
        targets = sync_tool.catalog_targets(payload, base_url=BASE_URL)
        plan = sync_tool.plan_sync(targets, self._rows([ROW_H_EN_STALE]))
        self.assertEqual(len(plan.updates), 1)
        update = plan.updates[0]
        self.assertEqual(update["row"], 2)
        changed = {change["column"] for change in update["changed"]}
        self.assertEqual(changed, {"当前版本", "目标构建时间UTC", "内容提交"})
        self.assertEqual(update["human_values_before"], ["夏冰", "跟进中", "2026-10-01", "手工备注"])

    def test_new_target_appends_and_departed_row_is_orphan(self) -> None:
        payload = manifest_payload([target_payload("JE-1000H", "EU", "de")])
        targets = sync_tool.catalog_targets(payload, base_url=BASE_URL)
        plan = sync_tool.plan_sync(targets, self._rows([ROW_JBP_EN]))
        self.assertEqual([item["doc_id"] for item in plan.appends], ["JE-1000H/EU/de"])
        self.assertEqual([item["doc_id"] for item in plan.orphans], ["JBP-2000B/EU/en"])

    def test_duplicate_keys_are_never_written(self) -> None:
        payload = manifest_payload(
            [target_payload("JBP-2000B", "EU", "en", legacy_default=True, stem="manual_jbp2000b_eu")]
        )
        targets = sync_tool.catalog_targets(payload, base_url=BASE_URL)
        plan = sync_tool.plan_sync(targets, self._rows([ROW_JBP_EN, ROW_JBP_EN]))
        self.assertEqual(len(plan.duplicates), 1)
        self.assertFalse(plan.updates)
        self.assertFalse(plan.appends)


class SyncWriteTests(unittest.TestCase):
    def _manifest(self, tmp: Path) -> Path:
        payload = manifest_payload(
            [
                target_payload(
                    "JBP-2000B",
                    "EU",
                    "en",
                    version="2.0-20260913",
                    built_at="2026-09-13T23:13:00+00:00",
                    git_ref="108e1c9f0fe0eeab2d042fd6f1b526b3dac6559f",
                    legacy_default=True,
                    stem="manual_jbp2000b_eu",
                ),
                target_payload("JE-1000H", "EU", "en", version="2.0", legacy_default=True),
                target_payload("JE-1000H", "EU", "de"),
            ]
        )
        path = tmp / "publish_manifest.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def _run(self, runner: FakeRunner, manifest: Path, *extra: str) -> int:
        argv = [
            "sync",
            "--manifest-path",
            str(manifest),
            "--spreadsheet-token",
            "TOKEN",
            "--sheet-id",
            "15c75c",
            *extra,
        ]
        args = sync_tool.parse_args(argv)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code, report = (
                sync_tool.run_sync(args, make_ops(runner))
                if args.mode == "sync"
                else sync_tool.run_reconcile(args, make_ops(runner))
            )
        self.report = report
        return code

    def test_dry_run_plans_but_never_writes(self) -> None:
        runner = FakeRunner()
        runner.set_sheet([HEADER, ROW_JBP_EN, ROW_H_EN_STALE])
        with TemporaryDirectory() as tmp:
            code = self._run(runner, self._manifest(Path(tmp)))
        self.assertEqual(code, 0)
        self.assertFalse(any(call[1] == "+cells-set" for call in runner.calls))
        self.assertEqual(len(self.report["plan"]["updates"]), 1)
        self.assertEqual(len(self.report["plan"]["appends"]), 1)

    def test_write_updates_machine_columns_and_appends_with_readback(self) -> None:
        runner = FakeRunner()
        runner.set_sheet([HEADER, ROW_JBP_EN, ROW_H_EN_STALE])
        with TemporaryDirectory() as tmp:
            code = self._run(runner, self._manifest(Path(tmp)), "--write")
        self.assertEqual(code, 0)
        set_calls = [call for call in runner.calls if call[1] == "+cells-set"]
        ranges = [call[call.index("--range") + 1] for call in set_calls]
        self.assertEqual(ranges, ["A3:K3", "A4:O4"])  # update writes machine cols only
        update_cells = json.loads(set_calls[0][set_calls[0].index("--cells") + 1])
        self.assertEqual(len(update_cells[0]), 11)
        self.assertTrue(all("cell_styles" not in cell for cell in update_cells[0]))
        append_call = set_calls[1]
        self.assertIn("--allow-overwrite=false", append_call)
        append_cells = json.loads(append_call[append_call.index("--cells") + 1])
        self.assertEqual(len(append_cells[0]), 15)
        self.assertTrue(all("cell_styles" in cell for cell in append_cells[0]))
        self.assertEqual(append_cells[0][12]["value"], "待评估")
        self.assertNotIn("value", append_cells[0][11])  # 负责人 stays empty
        # Human columns on the updated row survived byte-for-byte.
        after = next(csv.reader(io.StringIO(runner.sheet_lines[3])))
        self.assertEqual(after[11:15], ["夏冰", "跟进中", "2026-10-01", "手工备注"])
        self.assertEqual(after[4], "2.0")
        self.assertEqual(after[9], "c99b7169e3a16381d235d6cf5bf171962b0ad90b")
        self.assertFalse(self.report["write"]["failures"])

    def test_write_is_idempotent(self) -> None:
        runner = FakeRunner()
        runner.set_sheet([HEADER, ROW_JBP_EN, ROW_H_EN_STALE])
        with TemporaryDirectory() as tmp:
            manifest = self._manifest(Path(tmp))
            self.assertEqual(self._run(runner, manifest, "--write"), 0)
            first_write_calls = sum(1 for call in runner.calls if call[1] == "+cells-set")
            self.assertEqual(self._run(runner, manifest, "--write"), 0)
        second_write_calls = sum(1 for call in runner.calls if call[1] == "+cells-set")
        self.assertEqual(first_write_calls, second_write_calls)  # no new writes
        self.assertEqual(len(self.report["plan"]["updates"]), 0)
        self.assertEqual(len(self.report["plan"]["appends"]), 0)
        self.assertEqual(self.report["plan"]["in_sync"], 3)

    def test_failed_row_is_recorded_and_does_not_block_others(self) -> None:
        runner = FakeRunner()
        runner.set_sheet([HEADER, ROW_JBP_EN, ROW_H_EN_STALE])
        runner.fail_ranges.add("A3:K3")
        with TemporaryDirectory() as tmp:
            code = self._run(runner, self._manifest(Path(tmp)), "--write")
        self.assertEqual(code, 1)
        failures = self.report["write"]["failures"]
        self.assertEqual([item["doc_id"] for item in failures], ["JE-1000H/EU/en"])
        applied = self.report["write"]["applied"]
        self.assertEqual([item["doc_id"] for item in applied], ["JE-1000H/EU/de"])


class ReconcileTests(unittest.TestCase):
    def _receipt_page(self, entries: list[tuple[str, str, str]]) -> dict:
        fields = ["Task_id", "Workflow_action", "HTML_link"]
        return {
            "ok": True,
            "data": {
                "fields": fields,
                "data": [[task, action, link] for task, action, link in entries],
                "record_id_list": [f"rec{i}" for i in range(len(entries))],
            },
        }

    def _whitelist(self, tmp: Path, entries: list[dict]) -> Path:
        path = tmp / "whitelist.json"
        path.write_text(
            json.dumps(
                {"schema_version": sync_tool.WHITELIST_SCHEMA, "entries": entries},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def _run(self, runner: FakeRunner, manifest: Path, whitelist: Path) -> tuple[int, dict]:
        argv = [
            "reconcile",
            "--manifest-path",
            str(manifest),
            "--spreadsheet-token",
            "TOKEN",
            "--sheet-id",
            "15c75c",
            "--doc-link-base-token",
            "BASE",
            "--doc-link-table-id",
            "TBL",
            "--whitelist",
            str(whitelist),
        ]
        args = sync_tool.parse_args(argv)
        with contextlib.redirect_stdout(io.StringIO()):
            return sync_tool.run_reconcile(args, make_ops(runner))

    def test_whitelisted_diffs_exit_zero_and_are_listed(self) -> None:
        runner = FakeRunner()
        runner.set_sheet([HEADER, ROW_JBP_EN])
        runner.bitable_pages = [self._receipt_page([])]
        payload = manifest_payload(
            [
                target_payload(
                    "JBP-2000B",
                    "EU",
                    "en",
                    version="2.0-20260913",
                    built_at="2026-09-13T23:13:00+00:00",
                    git_ref="108e1c9f0fe0eeab2d042fd6f1b526b3dac6559f",
                    legacy_default=True,
                    stem="manual_jbp2000b_eu",
                )
            ]
        )
        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "m.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            whitelist = self._whitelist(
                Path(tmp),
                [
                    {
                        "kind": "target_unregistered",
                        "key": "JBP-2000B/EU/en",
                        "reason": "M0-05 Git-only baseline",
                    }
                ],
            )
            code, report = self._run(runner, manifest, whitelist)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(len(report["known_diffs"]), 1)
        self.assertEqual(report["new_diffs"], [])

    def test_new_difference_exits_one(self) -> None:
        runner = FakeRunner()
        runner.set_sheet([HEADER, ROW_JBP_EN])
        runner.bitable_pages = [self._receipt_page([])]
        payload = manifest_payload(
            [
                target_payload(
                    "JBP-2000B",
                    "EU",
                    "en",
                    version="2.0-20260913",
                    built_at="2026-09-13T23:13:00+00:00",
                    git_ref="108e1c9f0fe0eeab2d042fd6f1b526b3dac6559f",
                    legacy_default=True,
                    stem="manual_jbp2000b_eu",
                ),
                target_payload("JE-1000H", "EU", "de"),
            ]
        )
        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "m.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            whitelist = self._whitelist(
                Path(tmp),
                [
                    {
                        "kind": "target_unregistered",
                        "key": "JBP-2000B/EU/en",
                        "reason": "M0-05 Git-only baseline",
                    },
                    {
                        "kind": "target_unregistered",
                        "key": "JE-1000H/EU/de",
                        "reason": "M0-05 Git-only baseline",
                    },
                ],
            )
            code, report = self._run(runner, manifest, whitelist)
        self.assertEqual(code, 1)
        kinds = {item["kind"] for item in report["new_diffs"]}
        self.assertEqual(kinds, {"ops_missing_row"})

    def test_receipt_link_matching_and_flat_form_classification(self) -> None:
        targets = [
            sync_tool.CatalogTarget(
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.3",
                built_at="2026-08-14T11:05:39+00:00",
                git_ref="review/JE-1000F-US",
                language_scope="legacy_unspecified",
                page_url="https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html",
                alias_url="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
            )
        ]
        receipts = [
            {"Task_id": "JE-1000F_US_2.3", "HTML_link": "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html"},
            {"Task_id": "JE-1000F_US_2.2", "HTML_link": "https://ht-doc.readthedocs.io/manual_je1000f_us.html"},
            {"Task_id": "GHOST_1.0", "HTML_link": "https://ht-doc.readthedocs.io/manual_ghost.html"},
        ]
        diffs = sync_tool.reconcile_diffs(targets, [], receipts)
        by_kind: dict[str, list[sync_tool.Diff]] = {}
        for diff in diffs:
            by_kind.setdefault(diff.kind, []).append(diff)
        self.assertEqual([d.key for d in by_kind["receipt_flat_form_link"]], ["JE-1000F_US_2.2"])
        self.assertEqual([d.key for d in by_kind["receipt_unmatched_link"]], ["GHOST_1.0"])
        # The nested link registered the target, so no target_unregistered diff.
        self.assertNotIn("target_unregistered", by_kind)

    def test_markdown_rendered_url_cells_are_extracted(self) -> None:
        value = "[https://ht-doc.readthedocs.io/a.html](https://ht-doc.readthedocs.io/a.html)"
        self.assertEqual(sync_tool.extract_link(value), "https://ht-doc.readthedocs.io/a.html")
        self.assertEqual(
            sync_tool.extract_link([{"text": "https://x.example/y.html", "link": "https://x.example/y.html"}]),
            "https://x.example/y.html",
        )
        self.assertEqual(sync_tool.extract_link(None), "")

    def test_rendered_pair_extraction_prefers_the_link_target(self) -> None:
        """Shared shape parser: reconcile reports where a cell actually points.

        ``extract_link`` stays the lenient reconcile reader — unlike the
        receipt lane's fail-closed comparison, it reports a best-effort link
        rather than rejecting. When the two halves disagree the target is what
        a reader would open, so the target wins over the label.
        """
        self.assertEqual(
            sync_tool.extract_link("[click here](https://ht-doc.readthedocs.io/b.html)"),
            "https://ht-doc.readthedocs.io/b.html",
        )
        self.assertEqual(
            sync_tool.extract_link("[https://a.example/a.html](https://b.example/b.html)"),
            "https://b.example/b.html",
        )
        # Non-rendered cells still fall back to the first URL in the text.
        self.assertEqual(
            sync_tool.extract_link("see https://ht-doc.readthedocs.io/c.html for details"),
            "https://ht-doc.readthedocs.io/c.html",
        )

    def test_whitelist_schema_is_enforced(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "w.json"
            path.write_text(json.dumps({"schema_version": "nope", "entries": []}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                sync_tool.load_whitelist(path)


class CommittedWhitelistTests(unittest.TestCase):
    def test_committed_whitelist_loads_and_indexes(self) -> None:
        path = sync_tool.ops_catalog_reconcile_whitelist_of(sync_tool.ROOT)
        payload = sync_tool.load_whitelist(path)
        index = sync_tool.whitelist_index(payload)
        self.assertTrue(index)
        for (kind, key), reason in index.items():
            self.assertTrue(kind)
            self.assertTrue(key)
            self.assertTrue(reason, f"whitelist entry ({kind}, {key}) must carry a reason")


if __name__ == "__main__":
    unittest.main()
