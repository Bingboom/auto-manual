"""The group message is literal text plus validated links, grouped by what needs deciding first."""
from copy import deepcopy
import json
import unittest

from tools.rtd import intelligence_push as push

TODAY = "2026-10-21"
TEMPLATE = "https://example.feishu.cn/base/bascnX?table=tblX&record={record_id}"


def item(event_id, *, due=None, reviewed=False, record_id=None, title=None, url=None):
    review = ({"status": "reviewed", "decision": "立项核查", "reviewed_by": "李四", "reviewed_on": TODAY}
              if reviewed else {"status": "pending", "decision": None, "reviewed_by": None, "reviewed_on": None})
    return {"event_id": event_id, "title": title or f"事件 {event_id}", "market": "DE", "verification": "unverified",
            "decision": {"question": f"{event_id} 怎么决定？", "owner": None, "due_on": due}, "review": review,
            "record_id": record_id, "url": url}


def digest(*items):
    reviewed = sum(entry["review"]["status"] == "reviewed" for entry in items)
    return {"items": list(items), "counts": {"events": len(items), "pending": len(items) - reviewed,
                                             "reviewed": reviewed}}


def texts(content):
    return [element["text"] for line in content["zh_cn"]["content"] for element in line]


def links(content):
    return [(element["text"], element["href"]) for line in content["zh_cn"]["content"]
            for element in line if element["tag"] == "a"]


class GroupTests(unittest.TestCase):
    def test_pending_items_group_by_due_date(self):
        for due, expected in (("2026-10-20", "overdue"), (TODAY, "due_soon"), ("2026-10-28", "due_soon"),
                              ("2026-10-29", "pending"), (None, "pending")):
            with self.subTest(due=due):
                self.assertEqual(push.group_of(item("a", due=due), TODAY), expected)
        self.assertEqual(push.group_of(item("a", due="2026-10-01", reviewed=True), TODAY), "reviewed")


class ContentTests(unittest.TestCase):
    def test_sections_follow_urgency_and_judged_events_are_only_counted(self):
        content = push.post_content(digest(item("later"), item("soon", due="2026-10-25"),
                                           item("late", due="2026-10-01"), item("done", reviewed=True)),
                                    today=TODAY)
        self.assertEqual(content["zh_cn"]["title"], "外部情报待决策 · 2026-10-21")
        lines = texts(content)
        self.assertEqual(lines[0], "待决策 3 条（已逾期 1）· 已有人工判断 1 条 · 共 4 条")
        order = [lines.index(text) for text in ("【已逾期（1）】", "[DE] 事件 late", "【7 天内到期（1）】",
                                                 "[DE] 事件 soon", "【待决策（1）】", "[DE] 事件 later")]
        self.assertEqual(order, sorted(order))
        self.assertNotIn("[DE] 事件 done", lines)
        self.assertIn("  决策人：待指派 · 截止：未设定 · 待核实线索", lines)

    def test_nothing_pending_and_no_sync_report_sends_nothing(self):
        self.assertIsNone(push.post_content(digest(item("done", reviewed=True)), today=TODAY))
        self.assertIsNone(push.post_content(digest(), today=TODAY, report={"problems": [], "notices": []}))

    def test_intake_text_stays_literal_and_only_safe_links_are_links(self):
        hostile = "**粗体** [链接](https://evil.example) <at user_id=\"all\"></at> @所有人"
        content = push.post_content(digest(item("x", title=hostile, record_id="recX1",
                                                url="javascript:alert(1)")), today=TODAY, record_url=TEMPLATE)
        self.assertIn(f"[DE] {hostile}", texts(content))
        self.assertEqual({element["tag"] for line in content["zh_cn"]["content"] for element in line}, {"text", "a"})
        self.assertEqual(links(content), [("去填写判断", TEMPLATE.replace("{record_id}", "recX1"))])
        self.assertEqual(links(push.post_content(digest(item("x", record_id="rec/../x")), today=TODAY,
                                                 record_url=TEMPLATE)), [])

    def test_long_text_is_shortened_and_the_page_is_linked(self):
        content = push.post_content(digest(item("x", title="很" * 500, url="https://site.example/p#event-x")),
                                    today=TODAY, page_url="https://site.example/p")
        title = next(text for text in texts(content) if text.startswith("[DE] "))
        self.assertEqual(len(title), len("[DE] ") + push.MAX_TEXT)
        self.assertTrue(title.endswith("…"))
        self.assertEqual(links(content), [("查看详情", "https://site.example/p#event-x"),
                                          ("外部情报", "https://site.example/p")])

    def test_long_lists_stop_at_the_cap_and_say_how_many_are_left(self):
        many = [item(f"e{index:02}", due="2026-10-01") for index in range(push.MAX_LISTED + 3)]
        lines = texts(push.post_content(digest(*many), today=TODAY))
        self.assertEqual(sum(text.startswith("[DE] ") for text in lines), push.MAX_LISTED)
        self.assertIn("  另有 3 条未列出，见完整列表", lines)

    def test_sync_report_lists_recorded_judgments_and_rows_to_fix(self):
        report = {"added": [{"record_id": "recN", "event_id": "new", "title": "新事件", "message": ""}],
                  "judged": [{"record_id": "recJ", "event_id": "done", "title": "已判断事件", "message": ""}],
                  "revised": [{"record_id": "recR", "event_id": "open", "title": "仍待决策", "message": ""}],
                  "problems": [{"record_id": "recB", "event_id": "ev-0", "title": "", "message": "缺少标题"}],
                  "notices": [{"record_id": "recJ", "event_id": "done", "title": "已判断事件",
                               "message": "人工判断早于修订日期"}],
                  "gone": [{"record_id": "recG", "event_id": "gone", "title": "旧事件", "message": "找不到这一行"}]}
        content = push.post_content(digest(item("done", reviewed=True), item("open"), item("new", reviewed=True)),
                                    today=TODAY, record_url=TEMPLATE, report=report)
        lines = texts(content)
        start = lines.index("【本次同步录入的人工判断（2）】")
        self.assertEqual(lines[start + 1:start + 3], ["• 新事件：立项核查（李四，2026-10-21）",
                                                      "• 已判断事件：立项核查（李四，2026-10-21）"])
        self.assertIn("【需处理的表格行（3）】", lines)
        self.assertIn("• （未填标题）：缺少标题", lines)
        self.assertIn("• 旧事件：找不到这一行", lines)
        self.assertIn(("去修改", TEMPLATE.replace("{record_id}", "recB")), links(content))
        self.assertNotIn(("去修改", TEMPLATE.replace("{record_id}", "recG")), links(content))
        only_fixes = push.post_content(digest(item("done", reviewed=True)), today=TODAY,
                                       report={"problems": report["problems"]})
        self.assertIn("待决策 0 条（已逾期 0）· 已有人工判断 1 条 · 共 1 条", texts(only_fixes))

    def test_record_url_templates_are_checked(self):
        self.assertEqual(push.check_record_url(""), "")
        self.assertEqual(push.check_record_url(TEMPLATE), TEMPLATE)
        for template in ("https://example.feishu.cn/base/x", "http://example.feishu.cn/{record_id}",
                         "https://a.example/{record_id}/{record_id}", "javascript:{record_id}"):
            with self.subTest(template=template):
                with self.assertRaises(ValueError):
                    push.check_record_url(template)


class SendTests(unittest.TestCase):
    def content(self):
        return push.post_content(digest(item("late", due="2026-10-01")), today=TODAY)

    def test_key_is_stable_per_chat_content_and_day_and_fits_feishu(self):
        content = self.content()
        key = push.idempotency_key("oc_1", content, TODAY)
        self.assertEqual(key, push.idempotency_key("oc_1", deepcopy(content), TODAY))
        self.assertRegex(key, r"^ei-20261021-[0-9a-f]{16}$")
        self.assertLessEqual(len(key), 50)
        changed = deepcopy(content)
        changed["zh_cn"]["title"] = "外部情报待决策 · 更正"
        self.assertEqual(len({key, push.idempotency_key("oc_2", content, TODAY),
                              push.idempotency_key("oc_1", content, "2026-10-22"),
                              push.idempotency_key("oc_1", changed, TODAY)}), 4)

    def test_send_posts_once_as_post_and_returns_a_receipt_without_the_chat(self):
        calls = []

        def run(args):
            calls.append(args)
            return {"code": 0, "data": {"message_id": "om_1"}}

        content = self.content()
        receipt = push.send(run, chat_id="oc_1", content=content, key="ei-k")
        (args,) = calls
        self.assertEqual(args[:2], ["im", "+messages-send"])
        self.assertEqual(args[args.index("--chat-id") + 1], "oc_1")
        self.assertEqual(args[args.index("--msg-type") + 1], "post")
        self.assertEqual(json.loads(args[args.index("--content") + 1]), content)
        self.assertEqual(args[args.index("--idempotency-key") + 1], "ei-k")
        self.assertEqual(receipt, {"status": "sent", "message_id": "om_1", "idempotency_key": "ei-k"})
        self.assertIsNone(push.send(lambda args: {"code": 0}, chat_id="oc_1", content=content,
                                    key="ei-k")["message_id"])

    def test_preview_shows_links_after_their_labels(self):
        content = push.post_content(digest(item("x", record_id="recX")), today=TODAY, record_url=TEMPLATE)
        text = push.preview(content)
        self.assertTrue(text.startswith("外部情报待决策 · 2026-10-21\n"))
        self.assertIn("去填写判断 <https://example.feishu.cn/base/bascnX?table=tblX&record=recX>", text)


if __name__ == "__main__":
    unittest.main()
