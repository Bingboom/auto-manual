"""The product-matrix sync check (tools/product_matrix_base/sync.py, ``check`` CLI, publish step).

Every product and project is invented (JE-*, P-FAKE-*): project numbers never belong in this repository.
"""
from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tests import test_product_matrix_base as matrix_tests  # a module, so its tests are not collected twice
from tools.product_matrix_base import publish, snapshot, sync
from tools.product_matrix_base.__main__ import main

READ = datetime(2026, 11, 17, tzinfo=timezone.utc)
LATER = datetime(2026, 11, 18, 1, 2, 3, tzinfo=timezone.utc)


def base():
    return matrix_tests.SnapshotTest().base()


def failing(_args):
    return {"ok": False, "error": {"code": 99, "message": "row JE-A/US P-FAKE-1 could not be read"}}


class SnapshotTimesTest(unittest.TestCase):
    def test_source_modified_at_is_the_latest_fact_record_time_and_content_ignores_times(self):
        fake = base()
        fake.rows["事实"][0]["记录时间"] = "2026-11-10 09:00:00"  # Beijing time, as the loader writes it
        fake.rows["事实"][1]["记录时间"] = 1795000000000  # read back as epoch ms
        document = snapshot.build_snapshot(fake, now=READ)
        self.assertEqual(document["source_modified_at"], "2026-11-18T11:06:40Z")
        fake.rows["事实"][1]["记录时间"] = None
        self.assertEqual(snapshot.build_snapshot(fake, now=READ)["source_modified_at"], "2026-11-10T01:00:00Z")
        again = snapshot.build_snapshot(base(), now=LATER)
        plain = snapshot.build_snapshot(base(), now=READ)
        self.assertNotEqual(again["read_at"], plain["read_at"])
        self.assertEqual(snapshot.content_digest(again), snapshot.content_digest(plain))
        self.assertNotEqual(snapshot.content_digest(document), snapshot.content_digest(plain))


class CheckTest(unittest.TestCase):
    def test_an_unchanged_base_is_current_and_confirms_the_snapshot(self):
        committed = snapshot.build_snapshot(base(), now=READ)
        status, fresh = sync.check(base(), committed, None, now=LATER)
        self.assertIsNone(fresh)
        self.assertEqual((status["status"], status["last_success"], status["lag"]["behind"]),
                         ("current", "2026-11-18T01:02:03Z", False))
        self.assertEqual(status["snapshot"]["read_at"], "2026-11-17T00:00:00Z")
        self.assertEqual(status["source"]["content_sha256"], status["snapshot"]["content_sha256"])
        self.assertEqual((status["schema"], status["kind"], status["checked_at"]),
                         (sync.STATUS_SCHEMA, "product_matrix", "2026-11-18T01:02:03Z"))

    def test_a_changed_base_is_behind_with_a_reason_and_refresh_returns_the_new_snapshot(self):
        committed = snapshot.build_snapshot(base(), now=READ)
        moved = base()
        moved.rows["事实"][1].update(数值=335, 记录时间="2026-11-18 08:00:00")
        status, fresh = sync.check(moved, committed, {"last_success": "2026-11-17T00:00:00Z"}, now=LATER)
        self.assertIsNone(fresh)
        self.assertEqual((status["status"], status["lag"]["behind"], status["last_success"]),
                         ("behind", True, "2026-11-17T00:00:00Z"))
        self.assertIn("飞书有更晚的事实记录（2026-11-18T00:00:00Z）", status["lag"]["reason"])
        status, fresh = sync.check(moved, committed, None, now=LATER, refresh=True)
        self.assertEqual((status["status"], status["stage"], status["last_success"]),
                         ("refreshed", "snapshot-built", "2026-11-18T01:02:03Z"))
        self.assertEqual(fresh["read_at"], "2026-11-18T01:02:03Z")
        self.assertEqual(status["snapshot"]["content_sha256"], snapshot.content_digest(fresh))
        added = base()
        added.rows["产品"].append({"产品键": "JE-C/EU", "型号": "JE-C", "市场": ["EU"], "_id": "r3"})
        self.assertIn("产品 2→3", sync.lag(committed, snapshot.build_snapshot(added, now=LATER)))

    def test_an_older_schema_or_no_snapshot_is_behind(self):
        committed = snapshot.build_snapshot(base(), now=READ)
        old = {**committed, "schema": "hello-docs-product-matrix-snapshot/v1.1"}
        del old["built_at"]
        self.assertIn("v1.1 早于当前的", sync.check(base(), old, None, now=LATER)[0]["lag"]["reason"])
        self.assertEqual(sync.check(base(), None, None, now=LATER)[0]["lag"]["reason"], "还没有可读的已提交快照")

    def test_a_failed_read_keeps_the_last_success_and_never_echoes_row_data(self):
        committed = snapshot.build_snapshot(base(), now=READ)
        status, fresh = sync.check(failing, committed, {"last_success": "2026-11-17T00:00:00Z"}, now=LATER,
                                   refresh=True)
        self.assertIsNone(fresh)
        self.assertEqual((status["status"], status["stage"], status["last_success"], status["error_type"]),
                         ("failed", "source-read", "2026-11-17T00:00:00Z", "LoadError"))
        self.assertIsNone(status["lag"]["behind"])
        self.assertIsNone(status["source"])
        self.assertNotIn("P-FAKE", json.dumps(status, ensure_ascii=False))

    def test_only_a_new_verdict_new_content_or_an_old_confirmation_is_committed(self):
        committed = snapshot.build_snapshot(base(), now=READ)
        first, _ = sync.check(base(), committed, None, now=READ)
        self.assertTrue(sync.worth_committing(first, None))
        next_day, _ = sync.check(base(), committed, first, now=LATER)
        self.assertFalse(sync.worth_committing(next_day, first))  # no timestamp-only commit
        later, _ = sync.check(base(), committed, first, now=datetime(2026, 11, 20, tzinfo=timezone.utc))
        self.assertTrue(sync.worth_committing(later, first))  # CONFIRM_AFTER_DAYS old
        failed, _ = sync.check(failing, committed, first, now=LATER)
        self.assertTrue(sync.worth_committing(failed, first))
        self.assertFalse(sync.worth_committing(sync.check(failing, committed, failed, now=LATER)[0], failed))
        moved = base()
        moved.rows["事实"][1]["数值"] = 335
        refreshed, _ = sync.check(moved, committed, first, now=LATER, refresh=True)
        self.assertTrue(sync.worth_committing(refreshed, first))
        settled, _ = sync.check(moved, snapshot.build_snapshot(moved, now=LATER), refreshed, now=LATER)
        self.assertFalse(sync.worth_committing(settled, refreshed))  # refreshed and current agree


class CommandTest(unittest.TestCase):
    def run_check(self, out: Path, *args: str, runner=None) -> tuple[int, str]:
        stdout = io.StringIO()
        with patch("tools.product_matrix_base.__main__.lark_runner", return_value=runner or base()), \
                redirect_stdout(stdout):
            code = main(["check", "--out", str(out), "--base-token", "fake", *args])
        return code, stdout.getvalue()

    def test_dry_run_write_refresh_and_failure(self):
        with TemporaryDirectory() as tmp:
            root = matrix_tests.SnapshotTest.checkout(Path(tmp), "private", "hello docs", "Hello-Docs.git")
            out = root / "docs" / "knowledge" / "product-matrix"
            out.mkdir()
            committed = snapshot.build_snapshot(base(), now=READ)
            snapshot.write_snapshot(out / "snapshot.json", committed)
            code, text = self.run_check(out, "--now", "2026-11-18T01:02:03Z")
            self.assertEqual(code, 0)
            self.assertIn("dry run", text)
            self.assertFalse((out / "status.json").exists())
            code, _ = self.run_check(out, "--now", "2026-11-18T01:02:03Z", "--write", "--log", str(Path(tmp) / "r.json"))
            status = json.loads((out / "status.json").read_text(encoding="utf-8"))
            self.assertEqual((code, status["status"], status["checked_at"]), (0, "current", "2026-11-18T01:02:03Z"))
            self.assertEqual(json.loads((Path(tmp) / "r.json").read_text(encoding="utf-8")), status)
            moved = base()
            moved.rows["事实"][1]["数值"] = 335
            code, _ = self.run_check(out, "--now", "2026-11-19T00:00:00+08:00", "--write", runner=moved)
            self.assertEqual(code, 1)  # behind: the snapshot stays
            self.assertEqual(json.loads((out / "snapshot.json").read_text(encoding="utf-8")), committed)
            code, text = self.run_check(out, "--now", "2026-11-19T00:00:00Z", "--write", "--refresh", runner=moved)
            fresh = json.loads((out / "snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual((code, fresh["read_at"], fresh["schema"]), (0, "2026-11-19T00:00:00Z", snapshot.SCHEMA))
            code, text = self.run_check(out, "--now", "2026-11-20T00:00:00Z", "--write", runner=failing)
            status = json.loads((out / "status.json").read_text(encoding="utf-8"))
            self.assertEqual((code, status["status"], status["last_success"]), (2, "failed", "2026-11-19T00:00:00Z"))
            self.assertNotIn("P-FAKE", text)
            self.assertEqual(self.run_check(out, "--refresh")[0], 2)  # --refresh needs --write

    def test_it_refuses_a_public_checkout(self):
        with TemporaryDirectory() as tmp:
            public = matrix_tests.SnapshotTest.checkout(Path(tmp), "public", "auto-manual", "auto-manual")
            code, text = self.run_check(public / "docs" / "knowledge" / "product-matrix", "--write")
            self.assertEqual(code, 2)
            self.assertIn("ERROR", text)
            self.assertFalse((public / "docs" / "knowledge" / "product-matrix" / "status.json").exists())


class PublishTest(unittest.TestCase):
    def test_the_snapshot_goes_up_only_after_a_refresh_and_the_status_only_when_worth_it(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = publish.directory(root)
            folder.mkdir(parents=True)
            committed = snapshot.build_snapshot(base(), now=READ)
            snapshot.write_snapshot(folder / "snapshot.json", committed)
            status, _ = sync.check(base(), committed, None, now=READ)
            snapshot.write_snapshot(folder / "status.json", status)
            self.assertEqual([p.name for p, _ in publish.candidates(root, status)], ["status.json"])
            self.assertEqual([p.name for p, _ in publish.candidates(root, {"status": "refreshed"})],
                             ["snapshot.json", "status.json"])
            main_copy = Path(tmp) / "main"
            main_copy.mkdir()
            snapshot.write_snapshot(main_copy / "status.json", status)
            self.assertTrue(publish.skip(folder / "status.json", main_copy / "status.json"))
            self.assertFalse(publish.skip(folder / "status.json", main_copy / "absent" / "status.json"))
            snapshot.write_snapshot(main_copy / "snapshot.json", committed)
            self.assertTrue(publish.skip(folder / "snapshot.json", main_copy / "snapshot.json"))

    def test_submission_is_confined_to_the_product_matrix_directory_and_waits_for_review(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = publish.directory(root)
            folder.mkdir(parents=True)
            status, _ = sync.check(failing, None, None, now=READ)
            snapshot.write_snapshot(folder / "status.json", status)
            calls = []

            def execute(args, cwd=None):
                calls.append(list(args))
                return "[]" if args[:3] == ["gh", "pr", "list"] else ""

            with patch("tools.workspace_refresh_publish.command", side_effect=execute):
                publish.submit(root)
        configure_idx = calls.index(["git", "config", "credential.helper", "!gh auth git-credential"])
        sparse_idx = calls.index(["git", "sparse-checkout", "set", "docs/knowledge/product-matrix"])
        self.assertLess(configure_idx, sparse_idx)
        self.assertIn(["git", "add", "--", "docs/knowledge/product-matrix/status.json"], calls)
        create = next(call for call in calls if call[:3] == ["gh", "pr", "create"])
        self.assertIn(publish.BRANCH, create)
        self.assertFalse(any(call[:3] == ["gh", "pr", "merge"] for call in calls))

    def test_publish_main_records_leak_free_submission_stage_on_failure(self):
        from tools.workspace_refresh_publish import CommandFailed, recorded_failure

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = publish.directory(root)
            folder.mkdir(parents=True)
            status, _ = sync.check(failing, None, None, now=READ)
            snapshot.write_snapshot(folder / "status.json", status)
            report_path = root / "result.json"
            snapshot.write_snapshot(report_path, status)

            def execute(args, cwd=None):
                if args[:2] == ["git", "push"]:
                    raise CommandFailed("git", 128, "permission-denied")
                return "[]" if args[:3] == ["gh", "pr", "list"] else ""

            stdout = io.StringIO()
            with patch("tools.workspace_refresh_publish.command", side_effect=execute), redirect_stdout(stdout):
                code = publish.main(["--root", str(root), "--report", str(report_path)])
            saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(code, 1)
        self.assertIn("stage push (CommandFailed: git exit 128, reason permission-denied)", stdout.getvalue())
        self.assertEqual((saved["stage"], saved["submission_stage"], saved["error_reason"]),
                         ("review-submission", "push", "permission-denied"))
        self.assertEqual(recorded_failure(saved), "stage push (CommandFailed: git exit 128, reason permission-denied)")


if __name__ == "__main__":
    unittest.main()
