"""The hand-run loop: a dry run touches nothing, --write writes, --push sends once, secrets stay out."""
import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.rtd import intelligence_loop as loop
from tools.rtd import intelligence_sync as sync
from tools.rtd import intelligence_delivery as delivery
from tools.rtd.intelligence_events import CONTENT_DIR, EVENTS_FILE, encode_intake, load_events

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "external_intel" / "events.json"
TOKEN = "bascnSECRETTOKEN"
TEMPLATE = "https://example.feishu.cn/base/bascnX?table=tblX&record={record_id}"


def cells(**changes):
    values = {column: "" for column in sync.COLUMNS}
    values.update({sync.TITLE: "德国户储补贴调整", sync.KIND: "政策", sync.MARKET: "DE", sync.OCCURRED: "2026-10-20",
                   sync.SOURCE_KIND: "外部事件", sync.STATUS: "未核实", sync.SUMMARY: "传闻 KfW 调整户储补贴。",
                   sync.BOUNDARY: "仅为线索。", sync.QUESTION: "是否请德国渠道核实？", sync.DUE: "2026-10-25"})
    values.update(changes)
    return [values[column] for column in sync.COLUMNS]


class FakeLark:
    def __init__(self, rows, *, fail=None):
        self.rows, self.fail, self.calls = rows, fail, []

    def __call__(self, args):
        self.calls.append(args)
        if self.fail and args[:2] == self.fail:
            raise RuntimeError(f"Lark CLI command failed with exit code 1: lark-cli {' '.join(args)}")
        if args[:2] == ["base", "+record-list"]:
            return {"code": 0, "data": {"fields": list(sync.COLUMNS), "data": self.rows, "total": len(self.rows),
                                        "has_more": False, "record_id_list": [f"rec{i}" for i in range(len(self.rows))]}}
        return {"code": 0, "data": {"message_id": "om_1"}}

    def sent(self):
        return [args for args in self.calls if args[:2] == ["im", "+messages-send"]]


class LoopTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.enterContext(patch.dict("os.environ", {delivery.STATE_ENV: str(self.root / "runtime")}))
        self.path = self.root / CONTENT_DIR / EVENTS_FILE
        self.path.parent.mkdir()
        self.path.write_bytes(FIXTURE.read_bytes())
        self.lark = FakeLark([cells(), cells(**{sync.TITLE: ""})])

    def main(self, *argv, lark=None):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = loop.main([*argv, "--knowledge-dir", str(self.root), "--today", "2026-10-21"],
                             run=lark or self.lark)
        return code, stream.getvalue()

    def sync(self, *flags, **options):
        return self.main("sync", "--base-token", TOKEN, "--table-id", "tblX", *flags, **options)

    def test_dry_run_reports_changes_and_writes_nothing(self):
        before = self.path.read_bytes()
        code, output = self.sync()
        self.assertEqual(code, 0)
        self.assertIn("rows: added 1, revised 0", output)
        self.assertIn("1 not used", output)
        self.assertIn("would change (dry run; add --write to write it)", output)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.lark.sent(), [])
        self.assertFalse(delivery.state_path(self.root).exists())

    def test_write_produces_a_loadable_intake_and_a_rerun_is_unchanged(self):
        code, output = self.sync("--write")
        self.assertEqual(code, 0)
        self.assertIn("written (3 events)", output)
        events = {event["id"]: event for event in load_events(self.root)["events"]}
        self.assertEqual(events[sync.derived_id("rec0")]["intake_record_id"], "rec0")
        self.assertIn("nl-self-consumption-research", events)
        written = self.path.read_bytes()
        code, output = self.sync("--write")
        self.assertIn("unchanged", output.splitlines()[-1])
        self.assertEqual(self.path.read_bytes(), written)

    def test_push_after_a_dry_run_prints_the_message_and_sends_nothing(self):
        code, output = self.sync("--push", "--record-url", TEMPLATE)
        self.assertEqual(code, 0)
        self.assertIn("push (dry run, idempotency key ei-20261021-", output)
        self.assertIn("【7 天内到期（1）】", output)
        self.assertIn("【需处理的表格行（1）】", output)
        self.assertIn("record=rec1", output)
        self.assertEqual(self.lark.sent(), [])

    def test_write_and_push_sends_one_post_built_from_the_written_file(self):
        code, output = self.sync("--write", "--push", "--chat-id", "oc_1", "--site-url", "https://site.example/en/x/")
        self.assertEqual(code, 0)
        (args,) = self.lark.sent()
        content = json.loads(args[args.index("--content") + 1])
        lines = ["".join(element["text"] for element in line) for line in content["zh_cn"]["content"]]
        self.assertIn("• [DE] 德国户储补贴调整", lines)
        hrefs = [element["href"] for line in content["zh_cn"]["content"] for element in line if element["tag"] == "a"]
        self.assertIn("https://site.example/en/x/research/product-intelligence.html", hrefs)
        receipt = json.loads(output.splitlines()[-1])
        self.assertEqual((receipt["status"], receipt["message_id"]), ("sent", "om_1"))
        self.assertEqual(receipt["events_snapshot_id"], load_events(self.root)["snapshot_id"])
        self.assertNotIn("oc_1", output)

    def test_transport_failures_print_no_command_text(self):
        for fail, flags in ((["base", "+record-list"], ()), (["im", "+messages-send"], ("--write", "--push"))):
            with self.subTest(fail=fail):
                code, output = self.sync(*flags, "--chat-id", "oc_1", lark=FakeLark([cells()], fail=fail))
                self.assertEqual(code, 1)
                self.assertIn("(RuntimeError)", output)
                self.assertNotIn(TOKEN, output)
                self.assertNotIn("exit code", output)

    def test_missing_columns_are_named(self):
        columns = [column for column in sync.COLUMNS if column != sync.REVIEWED]

        def run(args):
            return {"code": 0, "data": {"fields": columns, "data": [], "total": 0, "has_more": False,
                                        "record_id_list": []}}

        code, output = self.sync(lark=run)
        self.assertEqual(code, 1)
        self.assertIn("missing columns: 复核日期", output)

    def test_required_configuration_and_link_checks(self):
        self.assertEqual(self.main("sync")[0], 1)
        self.assertIn("need --chat-id", self.sync("--write", "--push")[1])
        self.assertIn("need --chat-id", self.main("push")[1])
        self.assertIn("record URL must be", self.main("push", "--dry-run", "--record-url", "https://x.example/")[1])
        self.assertIn("--site-url must be an HTTPS URL", self.main("push", "--dry-run", "--site-url", "http://x")[1])
        self.assertEqual(self.lark.calls, [])

    def test_push_alone_sends_the_file_as_it_is(self):
        code, output = self.main("push", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("【待决策（2）】", output)
        code, output = self.main("push", "--chat-id", "oc_1")
        self.assertEqual((code, len(self.lark.sent())), (0, 1))
        self.path.write_text("{", encoding="utf-8")
        self.assertEqual(self.main("push", "--dry-run")[0], 1)

    def test_unreadable_policy_records_warn_on_sync_and_stop_the_push(self):
        (self.root / "market-policy").mkdir()
        (self.root / "market-policy" / "records.json").write_text("{", encoding="utf-8")
        code, output = self.sync("--push")
        self.assertEqual(code, 1)
        self.assertIn("WARNING market-policy records are unreadable", output)
        self.assertIn("ERROR   cannot build the digest", output)

    def test_an_invalid_intake_is_never_overwritten(self):
        self.path.write_text(json.dumps({"schema_version": "external-intel-events/v0", "events": []}),
                             encoding="utf-8")
        before = self.path.read_bytes()
        code, output = self.sync("--write")
        self.assertEqual(code, 1)
        self.assertIn("cannot take this sync", output)
        self.assertEqual(self.path.read_bytes(), before)

    def reviewed_row(self):
        self.path.write_bytes(encode_intake({"schema_version": "external-intel-events/v1", "events": []}))
        return cells(**{sync.DECISION: "批准渠道核实", sync.REVIEWER: "李四", sync.REVIEWED: "2026-10-21"})

    def test_failed_judgment_notification_replays_exact_message_without_resync(self):
        rows = [self.reviewed_row()]
        failed = FakeLark(rows, fail=["im", "+messages-send"])
        code, _ = self.sync("--write", "--push", "--chat-id", "oc_1", lark=failed)
        self.assertEqual(code, 1)
        saved = delivery.load(self.root)
        self.assertIsNotNone(saved)
        self.assertNotIn(TOKEN, delivery.state_path(self.root).read_text())
        self.assertNotIn("oc_1", delivery.state_path(self.root).read_text())
        before = self.path.read_bytes()
        retry = FakeLark([])  # A retry must not erase the report by rereading the table.
        code, output = self.sync("--write", "--push", "--chat-id", "oc_1", lark=retry)
        self.assertEqual(code, 0)
        self.assertEqual(retry.calls, failed.sent())
        self.assertIn("本次同步录入的人工判断", retry.sent()[0][retry.sent()[0].index("--content") + 1])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(delivery.load(self.root))
        self.assertEqual(json.loads(output.splitlines()[-1])["events_snapshot_id"], saved["events_snapshot_id"])

    def test_push_alone_and_later_day_retry_use_original_key_content_and_snapshot(self):
        failed = FakeLark([self.reviewed_row()], fail=["im", "+messages-send"])
        self.sync("--write", "--push", "--chat-id", "oc_1", lark=failed)
        retry = FakeLark([])
        code, _ = self.main("push", "--chat-id", "oc_1", "--today", "2026-10-22", lark=retry)
        self.assertEqual(code, 0)
        self.assertEqual(retry.calls, failed.sent())

    def test_saved_push_dry_run_and_wrong_destination_preserve_pending_state(self):
        failed = FakeLark([self.reviewed_row()], fail=["im", "+messages-send"])
        self.sync("--write", "--push", "--chat-id", "oc_1", lark=failed)
        state = delivery.state_path(self.root).read_bytes()
        reader = FakeLark([])
        for argv in (("push", "--dry-run"), ("sync", "--base-token", TOKEN, "--table-id", "tblX", "--push")):
            code, output = self.main(*argv, lark=reader)
            self.assertEqual(code, 0)
            self.assertIn("saved message, dry run", output)
        code, _ = self.main("push", "--chat-id", "oc_other", lark=reader)
        self.assertEqual(code, 1)
        code, _ = self.sync("--write", lark=reader)
        self.assertEqual(code, 1)
        self.assertEqual(reader.calls, [])
        self.assertEqual(delivery.state_path(self.root).read_bytes(), state)

    def test_candidate_write_failure_is_recovered_before_sending_the_saved_message(self):
        lark = FakeLark([self.reviewed_row()])
        before = self.path.read_bytes()
        with patch.object(loop, "_write", side_effect=OSError("disk unavailable")):
            code, _ = self.sync("--write", "--push", "--chat-id", "oc_1", lark=lark)
        self.assertEqual((code, lark.sent()), (1, []))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNotNone(delivery.load(self.root))
        retry = FakeLark([])
        code, _ = self.main("push", "--chat-id", "oc_1", lark=retry)
        self.assertEqual((code, len(retry.sent())), (0, 1))
        self.assertNotEqual(self.path.read_bytes(), before)
        self.assertEqual(load_events(self.root)["events"][0]["review"]["status"], "reviewed")

    def test_newer_operator_edit_is_not_overwritten_or_sent_as_the_saved_candidate(self):
        failed = FakeLark([self.reviewed_row()], fail=["im", "+messages-send"])
        self.sync("--write", "--push", "--chat-id", "oc_1", lark=failed)
        document = json.loads(self.path.read_bytes())
        document["events"][0]["title"] = "人工新改动"
        self.path.write_bytes(encode_intake(document))
        changed = self.path.read_bytes()
        retry = FakeLark([])
        code, _ = self.main("push", "--chat-id", "oc_1", lark=retry)
        self.assertEqual((code, retry.sent(), self.path.read_bytes()), (1, [], changed))
        self.assertIsNotNone(delivery.load(self.root))

    def test_unacknowledged_send_keeps_the_original_pending_message(self):
        lark = FakeLark([self.reviewed_row()])

        def no_ack(args):
            return lark(args) if args[:2] == ["base", "+record-list"] else {"code": 0, "data": {}}

        code, _ = self.sync("--write", "--push", "--chat-id", "oc_1", lark=no_ack)
        self.assertEqual(code, 1)
        self.assertIsNotNone(delivery.load(self.root))

    def test_cannot_save_pending_message_never_commits_the_candidate_or_sends(self):
        lark = FakeLark([self.reviewed_row()])
        before = self.path.read_bytes()
        with patch.object(delivery, "save", side_effect=OSError("disk unavailable")):
            code, _ = self.sync("--write", "--push", "--chat-id", "oc_1", lark=lark)
        self.assertEqual((code, lark.sent(), self.path.read_bytes()), (1, [], before))

    def test_invalid_pending_state_cannot_be_overwritten_or_sent(self):
        state = delivery.state_path(self.root)
        state.parent.mkdir(parents=True)
        state.write_text('{"schema_version": "unknown"}')
        before = state.read_bytes()
        code, _ = self.main("push", "--chat-id", "oc_1")
        self.assertEqual((code, self.lark.sent(), state.read_bytes()), (1, [], before))

    def test_failed_standalone_push_checks_its_original_intake_before_retry(self):
        failed = FakeLark([], fail=["im", "+messages-send"])
        code, _ = self.main("push", "--chat-id", "oc_1", lark=failed)
        self.assertEqual(code, 1)
        self.path.write_text('{"schema_version":"external-intel-events/v1","events":[]}')
        changed = self.path.read_bytes()
        retry = FakeLark([])
        code, _ = self.main("push", "--chat-id", "oc_1", lark=retry)
        self.assertEqual((code, retry.sent(), self.path.read_bytes()), (1, [], changed))
        self.assertIsNotNone(delivery.load(self.root))


if __name__ == "__main__":
    unittest.main()
