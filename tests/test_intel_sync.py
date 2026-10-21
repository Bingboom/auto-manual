"""The 外部情报 table syncs into append-only event revisions; bad rows never cost good state."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.intel import sync
from tools.intel.events import INTAKE_SCHEMA, validated_cases

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "external_intel" / "events.json"
TODAY = "2026-10-21"
SOURCE = "官方 | KfW 公告 | https://www.kfw.de/notice | 核对补贴调整日期 | 2026-10-21"


def row(changes: dict | None = None) -> dict:
    """A complete external-event row; ``changes`` overrides columns."""
    cells = {column: "" for column in sync.COLUMNS}
    cells.update({sync.TITLE: "德国户储补贴调整", sync.KIND: "政策", sync.MARKET: "DE",
                  sync.OCCURRED: "2026-10-20", sync.SOURCE_KIND: "外部事件", sync.STATUS: "未核实",
                  sync.SUMMARY: "传闻 KfW 调整户储补贴。", sync.BOUNDARY: "仅为线索，未核实。",
                  sync.QUESTION: "是否请德国渠道核实？"})
    cells.update(changes or {})
    return cells


def judged(day: str = TODAY, decision: str = "先由德国渠道核实") -> dict:
    return {sync.DECISION: decision, sync.REVIEWER: "李四", sync.REVIEWED: day}


def table_runner(columns, rows):
    def run(args):
        return {"code": 0, "data": {"fields": columns, "data": rows, "total": len(rows), "has_more": False,
                                    "record_id_list": [f"rec{i}" for i in range(len(rows))]}}
    return run


class CellTests(unittest.TestCase):
    def test_text_cells_join_rich_text_options_people_and_links(self):
        self.assertEqual(sync.cell_text([{"type": "text", "text": "见 "},
                                         {"type": "url", "text": "公告", "link": "https://a.example/x"}]),
                         "见 https://a.example/x")
        self.assertEqual(sync.cell_text([{"name": "张三", "id": "ou_1"}, {"name": "李四"}]), "张三、李四")
        self.assertEqual(sync.cell_text(["政策", "市场"]), "政策、市场")
        self.assertEqual(sync.cell_text({"link": "https://a.example", "text": "a"}), "https://a.example")
        self.assertEqual(sync.cell_text({"type": 1, "value": [{"type": "text", "text": "查找值"}]}), "查找值")
        self.assertEqual((sync.cell_text(None), sync.cell_text(True), sync.cell_text(12)), ("", "", "12"))

    def test_dates_read_epoch_milliseconds_in_business_time_and_written_dates(self):
        midnight_shanghai = 1792857600000  # 2026-10-25 00:00 +08:00 is still 10-24 in UTC
        for value, expected in ((midnight_shanghai, "2026-10-25"), (str(midnight_shanghai), "2026-10-25"),
                                ([midnight_shanghai], "2026-10-25"), ("2026/10/21", "2026-10-21"),
                                ("2026年10月1日", "2026-10-01"), ("2026-10-21 08:00", "2026-10-21"),
                                ([{"text": "2026-10-21"}], "2026-10-21"), (None, None), ("", None), ([], None)):
            with self.subTest(value=value):
                self.assertEqual(sync.cell_date(value), expected)
        for value in ("明天", "2026-02-30", True, 10 ** 20):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    sync.cell_date(value)


class RowTests(unittest.TestCase):
    def read(self, changes=None):
        return sync.read_row(row(changes))

    def test_complete_row_maps_to_intake_fields(self):
        parts, problems = self.read({sync.OWNER: [{"name": "渠道经理"}], sync.DUE: "2026/10/28",
                                     sync.HYPOTHESES: "可能改变购买节奏\n\n  补贴退坡  ", sync.SOURCES: SOURCE})
        self.assertEqual(problems, [])
        self.assertEqual(parts["entry"], {"title": "德国户储补贴调整", "kind": "policy", "market": "DE",
                                          "occurred_on": "2026-10-20", "source_kind": "external_event"})
        self.assertEqual(parts["facts"]["decision_owner"], "渠道经理")
        self.assertEqual(parts["facts"]["decide_by"], "2026-10-28")
        self.assertEqual(parts["facts"]["hypotheses"], ["可能改变购买节奏", "补贴退坡"])
        self.assertEqual(parts["facts"]["sources"], [{"kind": "official", "title": "KfW 公告",
                                                      "url": "https://www.kfw.de/notice",
                                                      "checked_on": "2026-10-21", "note": "核对补贴调整日期"}])
        self.assertIsNone(parts["judgment"])

    def test_option_aliases_and_full_width_source_bars_are_accepted(self):
        parts, problems = self.read({sync.KIND: "竞品动态", sync.STATUS: "事件要点已核实",
                                     sync.SOURCES: "官方来源｜KfW｜https://www.kfw.de/n｜说明｜2026-10-21｜2026-10-01"})
        self.assertEqual(problems, [])
        self.assertEqual((parts["entry"]["kind"], parts["facts"]["status"]), ("competitor", "verified"))
        self.assertEqual(parts["facts"]["sources"][0]["published_on"], "2026-10-01")

    def test_missing_and_malformed_fields_are_named_in_chinese(self):
        _, problems = self.read({sync.TITLE: "", sync.KIND: "传闻", sync.OCCURRED: "下周", sync.QUESTION: "",
                                 sync.STATUS: "", sync.DUE: "尽快"})
        for text in ("缺少标题", "类型应为政策、市场、竞品之一", "发生日期不是日期", "缺少需要决策",
                     "来源状态应为已核实、未核实、需求之一", "截止日期不是日期"):
            self.assertIn(text, problems)

    def test_source_lines_need_kind_title_https_link_note_and_dates(self):
        for line in ("https://www.kfw.de/notice", "博客 | t | https://a.example | n | 2026-10-21",
                     "官方 | t | http://a.example | n | 2026-10-21", "官方 | t | https://a.example | n | 昨天",
                     "官方 | t | https://a.example |  | 2026-10-21", "官方 | t | https://a.example | n | 2026-10-21 | 早前"):
            with self.subTest(line=line):
                parts, problems = self.read({sync.SOURCES: line})
                self.assertEqual(parts["facts"]["sources"], [])
                self.assertTrue(any(problem.startswith("来源") for problem in problems))

    def test_verified_events_need_an_official_source(self):
        _, problems = self.read({sync.STATUS: "已核实", sync.SOURCES: "二手 | 媒体 | https://a.example | n | 2026-10-21"})
        self.assertIn("已核实的事件至少需要一条官方来源", problems)
        self.assertEqual(self.read({sync.STATUS: "已核实", sync.SOURCES: SOURCE})[1], [])

    def test_policy_rows_join_a_record_and_state_no_facts(self):
        policy = {sync.SOURCE_KIND: "市场政策记录", sync.POLICY_ID: "nl-net-metering", sync.STATUS: "",
                  sync.SUMMARY: "", sync.BOUNDARY: ""}
        parts, problems = self.read(policy)
        self.assertEqual(problems, [])
        self.assertEqual(parts["entry"]["source_record_id"], "nl-net-metering")
        self.assertNotIn("summary", parts["facts"])
        self.assertIn("市场政策记录的事实来自政策快照，请清空来源状态、发生了什么、适用边界、来源",
                      self.read({**policy, sync.SUMMARY: "自写的政策事实"})[1])
        self.assertIn("市场政策记录需要填写政策记录ID", self.read({**policy, sync.POLICY_ID: ""})[1])
        self.assertIn("只有市场政策记录才填写政策记录ID", self.read({sync.POLICY_ID: "nl-net-metering"})[1])

    def test_a_judgment_is_all_three_fields_or_none(self):
        parts, problems = self.read(judged())
        self.assertEqual((parts["judgment"], problems),
                         ({"decision": "先由德国渠道核实", "reviewed_by": "李四", "reviewed_on": TODAY}, []))
        parts, problems = self.read({sync.DECISION: "先核实"})
        self.assertIsNone(parts["judgment"])
        self.assertIn("人工判断、复核人和复核日期要一起填写", problems)

    def test_table_without_the_columns_stops_and_blank_rows_are_skipped(self):
        columns = list(sync.COLUMNS)
        rows = [[row()[column] for column in columns], ["" for _ in columns], [None for _ in columns]]
        self.assertEqual([record for record, _ in sync.read_table(table_runner(columns, rows), "b", "t")], ["rec0"])
        with self.assertRaisesRegex(sync.TableShapeError, "需要决策, 决策人"):
            sync.read_table(table_runner([c for c in columns if c not in (sync.QUESTION, sync.OWNER)], []), "b", "t")


class MergeTests(unittest.TestCase):
    def merge(self, previous, rows, today=TODAY, **options):
        document, report = sync.merge(previous, rows, today=today, **options)
        validated_cases(document)
        return document, report

    def first(self, changes=None, record="recA"):
        return self.merge(None, [(record, row(changes))])

    @staticmethod
    def events(document):
        return {case["id"]: case for case in document["events"]}

    def test_new_row_becomes_revision_one_linked_to_its_row(self):
        document, report = self.first()
        (case,) = document["events"]
        self.assertEqual((case["id"], case["intake_record_id"]), (sync.derived_id("recA"), "recA"))
        self.assertRegex(case["id"], r"^ev-[0-9a-f]{10}$")
        self.assertEqual(case["revisions"][0]["revision"], 1)
        self.assertEqual(case["revisions"][0]["recorded_on"], TODAY)
        self.assertEqual(case["revisions"][0]["reason"], "从飞书多维表首次录入")
        self.assertEqual(case["revisions"][0]["review"], {"status": "pending", "decision": None})
        self.assertEqual([note["event_id"] for note in report["added"]], [case["id"]])
        named, _ = self.first({sync.ID: "de-storage-subsidy"})
        self.assertEqual(named["events"][0]["id"], "de-storage-subsidy")

    def test_unchanged_rows_add_nothing_and_the_document_is_stable(self):
        document, _ = self.first()
        again, report = self.merge(document, [("recA", row())], today="2026-10-30")
        self.assertEqual(again, document)
        self.assertEqual((report["unchanged"], report["revised"], report["notices"]), (1, [], []))

    def test_changed_facts_append_a_revision_and_keep_the_old_one(self):
        document, _ = self.first()
        revised, report = self.merge(document, [("recA", row({sync.SUMMARY: "KfW 已公告。"}))], today="2026-10-22")
        revisions = revised["events"][0]["revisions"]
        self.assertEqual(revisions[0], document["events"][0]["revisions"][0])
        self.assertEqual((revisions[1]["revision"], revisions[1]["recorded_on"], revisions[1]["summary"],
                          revisions[1]["reason"]), (2, "2026-10-22", "KfW 已公告。", "飞书多维表更新"))
        self.assertEqual(len(report["revised"]), 1)

    def test_a_judgment_on_unchanged_facts_is_recorded_as_its_own_revision(self):
        document, _ = self.first()
        judged_document, report = self.merge(document, [("recA", row(judged("2026-10-23")))], today="2026-10-24")
        latest = judged_document["events"][0]["revisions"][-1]
        self.assertEqual(latest["review"], {"status": "reviewed", "decision": "先由德国渠道核实",
                                            "reviewed_by": "李四", "reviewed_on": "2026-10-23"})
        self.assertEqual((latest["revision"], latest["reason"], latest["summary"]), (2, "录入人工判断", "传闻 KfW 调整户储补贴。"))
        self.assertEqual(len(report["judged"]), 1)

    def test_facts_edited_after_a_judgment_wait_for_a_new_one(self):
        document, _ = self.merge(None, [("recA", row(judged()))])
        self.assertEqual(document["events"][0]["revisions"][0]["review"]["status"], "reviewed")
        edited = row({**judged(), sync.SUMMARY: "KfW 已公告。"})
        stale, report = self.merge(document, [("recA", edited)], today="2026-10-22")
        latest = stale["events"][0]["revisions"]
        self.assertEqual([revision["review"]["status"] for revision in latest], ["reviewed", "pending"])
        self.assertIn("人工判断早于修订日期 2026-10-22，未计入", report["notices"][0]["message"])
        again, report = self.merge(stale, [("recA", edited)], today="2026-10-23")
        self.assertEqual(again, stale)
        self.assertEqual(len(report["notices"]), 1)
        confirmed, report = self.merge(stale, [("recA", {**edited, sync.REVIEWED: "2026-10-22"})], today="2026-10-23")
        self.assertEqual(confirmed["events"][0]["revisions"][-1]["review"]["status"], "reviewed")
        self.assertEqual((len(report["judged"]), report["notices"]), (1, []))

    def test_clearing_a_judgment_reopens_the_decision(self):
        document, _ = self.merge(None, [("recA", row(judged()))])
        reopened, report = self.merge(document, [("recA", row())], today="2026-10-22")
        latest = reopened["events"][0]["revisions"][-1]
        self.assertEqual((latest["review"]["status"], latest["reason"]), ("pending", "撤回人工判断"))
        self.assertEqual(len(report["reopened"]), 1)

    def test_delayed_judgment_remains_reviewed_on_unchanged_later_syncs(self):
        document, _ = self.first()
        cells = row(judged("2026-10-23"))
        accepted, _ = self.merge(document, [("recA", cells)], today="2026-10-24")
        for day in ("2026-10-24", "2026-10-25", "2026-11-01"):
            repeated, report = self.merge(accepted, [("recA", cells)], today=day)
            self.assertEqual(repeated, accepted)
            self.assertEqual((report["unchanged"], report["reopened"], report["notices"]), (1, [], []))

    def test_same_day_fact_change_requires_an_explicit_new_judgment(self):
        original, _ = self.first(judged())
        cells = row({**judged(), sync.SUMMARY: "与原判断相反的新事实", sync.QUESTION: "是否撤销原决定？"})
        changed, report = self.merge(original, [("recA", cells)])
        self.assertEqual(changed["events"][0]["revisions"][-1]["review"]["status"], "pending")
        self.assertIn("原人工判断未重新确认", report["notices"][0]["message"])
        for day in (TODAY, "2026-10-22"):
            again, report = self.merge(changed, [("recA", cells)], today=day)
            self.assertEqual(again, changed)
            self.assertEqual(len(report["notices"]), 1)
        confirmed = {**cells, sync.DECISION: "已重新核对新事实，撤销原决定"}
        accepted, report = self.merge(changed, [("recA", confirmed)])
        self.assertEqual(len(report["judged"]), 1)
        self.assertEqual(accepted["events"][0]["revisions"][-1]["review"]["status"], "reviewed")
        self.assertEqual(self.merge(accepted, [("recA", confirmed)], today="2026-10-22")[0], accepted)

    def test_invalidated_judgment_can_be_cleared_then_explicitly_reentered(self):
        original, _ = self.first(judged())
        facts = {sync.SUMMARY: "更新后的事实"}
        pending, _ = self.merge(original, [("recA", row({**facts, **judged()}))])
        cleared, _ = self.merge(pending, [("recA", row(facts))])
        accepted, report = self.merge(cleared, [("recA", row({**facts, **judged()}))])
        self.assertEqual(len(report["judged"]), 1)
        self.assertEqual(accepted["events"][0]["revisions"][-1]["review"]["status"], "reviewed")

    def test_legacy_judgment_revision_does_not_expire_from_its_sync_date(self):
        document, _ = self.first()
        cells = row(judged("2026-10-23"))
        accepted, _ = self.merge(document, [("recA", cells)], today="2026-10-24")
        for revision in accepted["events"][0]["revisions"]:
            revision.pop("intake_judgment_sha256")
        again, report = self.merge(accepted, [("recA", cells)], today="2026-10-25")
        self.assertEqual((again, report["unchanged"]), (accepted, 1))

    def test_change_note_is_used_once_then_the_default_reason_returns(self):
        document, _ = self.first({sync.REASON: "录入线索"})
        self.assertEqual(document["events"][0]["revisions"][0]["reason"], "录入线索")
        revised, _ = self.merge(document, [("recA", row({sync.REASON: "录入线索", sync.SUMMARY: "新事实"}))])
        self.assertEqual(revised["events"][0]["revisions"][-1]["reason"], "飞书多维表更新")
        noted, _ = self.merge(revised, [("recA", row({sync.REASON: "补充公告", sync.SUMMARY: "更新事实"}))])
        self.assertEqual(noted["events"][0]["revisions"][-1]["reason"], "补充公告")

    def test_relabelling_changes_the_entry_without_a_revision(self):
        document, _ = self.first()
        relabelled, report = self.merge(document, [("recA", row({sync.TITLE: "德国 KfW 补贴调整", sync.MARKET: "EU"}))])
        case = relabelled["events"][0]
        self.assertEqual((case["title"], case["market"], len(case["revisions"])), ("德国 KfW 补贴调整", "EU", 1))
        self.assertEqual(len(report["relabelled"]), 1)

    def test_a_bad_row_keeps_its_event_and_a_bad_new_row_adds_nothing(self):
        document, _ = self.first()
        kept, report = self.merge(document, [("recA", row({sync.QUESTION: ""})), ("recB", row({sync.TITLE: ""}))])
        self.assertEqual(kept, document)
        self.assertEqual([(note["record_id"], note["title"]) for note in report["problems"]],
                         [("recA", "德国户储补贴调整"), ("recB", "")])
        self.assertIn("缺少需要决策", report["problems"][0]["message"])

    def test_an_event_whose_row_is_gone_is_kept_and_reported(self):
        document, _ = self.first()
        kept, report = self.merge(document, [])
        self.assertEqual(kept, document)
        self.assertEqual([(note["record_id"], note["message"]) for note in report["gone"]],
                         [("recA", "多维表中已找不到这一行，事件按上次状态保留")])
        self.assertEqual(report["notices"], [])

    def test_a_recreated_row_takes_back_its_event_by_id(self):
        document, _ = self.first({sync.ID: "de-storage"})
        taken, report = self.merge(document, [("recNEW", row({sync.ID: "de-storage", sync.SUMMARY: "KfW 已公告。"}))])
        (case,) = taken["events"]
        self.assertEqual((case["intake_record_id"], len(case["revisions"])), ("recNEW", 2))
        self.assertEqual(case["revisions"][0], document["events"][0]["revisions"][0])
        self.assertEqual((report["gone"], report["problems"]), ([], []))
        refused, report = self.merge(document, [("recNEW", row({sync.ID: "de-storage", sync.TITLE: ""}))])
        self.assertEqual(refused, document)
        self.assertEqual([note["record_id"] for note in report["gone"]], ["recA"])

    def test_hand_written_events_are_adopted_by_id_and_keep_history_and_lens(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        us = fixture["events"][1]
        adopt = row({sync.ID: us["id"], sync.TITLE: us["title"], sync.KIND: "市场", sync.MARKET: "US",
                     sync.OCCURRED: us["occurred_on"], sync.STATUS: "已核实", sync.SUMMARY: "EIA 年度回顾。",
                     sync.BOUNDARY: "不代表单户停电时长。", sync.SOURCES: SOURCE, sync.QUESTION: "是否启动验证？"})
        document, report = self.merge(fixture, [("recUS", adopt)])
        case = self.events(document)[us["id"]]
        self.assertEqual(case["intake_record_id"], "recUS")
        self.assertEqual(case["revisions"][:3], us["revisions"])
        self.assertEqual(case["revisions"][3]["revision"], 4)
        self.assertEqual(case["product_lens"], us["product_lens"])
        self.assertEqual(self.events(document)["nl-self-consumption-research"], fixture["events"][0])
        self.assertEqual(len(report["revised"]), 1)

    def test_event_ids_are_fixed_unique_and_well_formed(self):
        document, _ = self.first({sync.ID: "de-storage"})
        cases = {
            "renamed": ([("recA", row({sync.ID: "de-other"}))], "事件ID已固定为 de-storage"),
            "taken": ([("recA", row()), ("recB", row({sync.ID: "de-storage"}))], "事件ID de-storage 已属于另一行"),
            "malformed": ([("recA", row()), ("recC", row({sync.ID: "DE 补贴"}))], "事件ID只用小写字母"),
            "repeated": ([("recA", row()), ("recD", row({sync.ID: "de-new"})), ("recE", row({sync.ID: "de-new"}))],
                         "事件ID de-new 在表中重复"),
        }
        for name, (rows, message) in cases.items():
            with self.subTest(name):
                result, report = self.merge(document, rows)
                self.assertTrue(report["problems"])
                self.assertTrue(all(message in note["message"] for note in report["problems"]))
                self.assertEqual(self.events(result)["de-storage"], document["events"][0])
        cleared, report = self.merge(document, [("recA", row({sync.ID: ""}))])
        self.assertEqual((cleared, report["problems"]), (document, []))

    def test_source_kind_and_policy_record_are_fixed_once_synced(self):
        document, _ = self.first()
        policy = row({sync.SOURCE_KIND: "市场政策记录", sync.POLICY_ID: "nl-net-metering", sync.STATUS: "",
                      sync.SUMMARY: "", sync.BOUNDARY: ""})
        kept, report = self.merge(document, [("recA", policy)])
        self.assertEqual(kept, document)
        self.assertIn("不能修改来源类型或政策记录ID", report["problems"][0]["message"])

    def test_unknown_policy_records_are_noticed_not_refused(self):
        policy = row({sync.SOURCE_KIND: "市场政策记录", sync.POLICY_ID: "de-kfw", sync.STATUS: "",
                      sync.SUMMARY: "", sync.BOUNDARY: ""})
        document, report = self.merge(None, [("recP", policy)], policy_ids={"nl-net-metering"})
        self.assertEqual(document["events"][0]["source_record_id"], "de-kfw")
        self.assertIn("政策记录ID de-kfw 不在市场政策快照中", report["notices"][0]["message"])
        self.assertEqual(self.merge(None, [("recP", policy)], policy_ids={"de-kfw"})[1]["notices"], [])

    def test_invalid_previous_intake_and_backdated_syncs_stop_the_sync(self):
        document, _ = self.first()
        with self.assertRaisesRegex(ValueError, "precedes"):
            sync.merge(document, [("recA", row())], today="2026-10-20")
        broken = deepcopy(document)
        broken["events"][0]["revisions"][0]["revision"] = 2
        with self.assertRaises(ValueError):
            sync.merge(broken, [("recA", row())], today=TODAY)
        with self.assertRaises(ValueError):
            sync.merge({"schema_version": "external-intel-events/v0", "events": []}, [], today=TODAY)

    def test_merge_never_mutates_its_inputs(self):
        document, _ = self.first()
        before, cells = deepcopy(document), row({sync.SUMMARY: "新事实"})
        frozen = deepcopy(cells)
        self.merge(document, [("recA", cells)])
        self.assertEqual((document, cells), (before, frozen))

    def test_validation_failures_are_reported_as_row_problems(self):
        case = self.first()[0]["events"][0]
        case["revisions"][0]["sources"] = [{"kind": "official"}]
        self.assertIn("未通过事件校验", sync._validation_problem(case))
        self.assertEqual(sync._validation_problem(self.first()[0]["events"][0]), "")
        self.assertEqual(INTAKE_SCHEMA, self.first()[0]["schema_version"])


if __name__ == "__main__":
    unittest.main()
