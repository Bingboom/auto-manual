"""系统建设 (2026-11 layout): the 阶段门 stepper, the lane each 近期事项 row belongs to, and the lane cards'
status, name, figures and ledger tally. The shipped page itself is rendered in test_rtd_system_workspace."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.test_rtd_system_workspace import LEDGER, TODAY, contract, registry
from tools.rtd import system_workspace as sw

LEDGER_URL = "https://github.com/o/auto-manual/blob/main/ledger.md"


def gate_views(data: dict, ledger_text: str = LEDGER):
    return sw._gate_and_now_views(data, sw.parse_ledger(ledger_text), data["focus"]["lanes"], LEDGER_URL)


class StepperTests(unittest.TestCase):
    def test_the_current_gate_names_its_open_rows_then_the_next_gate(self):
        data = contract()
        gates, _ = gate_views(data)
        view = sw.stepper_view(gates, data["now_next"])
        self.assertEqual([gate["id"] for gate in view["gates"]], ["G1", "G2"])
        self.assertEqual((view["current"], view["next_gate"], view["folded"]), ("G1", "G2", []))
        self.assertEqual(view["steps"], ["在验项", "验收 G1", "开始 G2 维护试点"])

    def test_unlabelled_rows_are_counted_and_a_folded_gate_leaves_the_steps(self):
        data = contract()
        data["now_next"]["gates"][1]["fold"] = True
        gates, _ = gate_views(data)
        view = sw.stepper_view(gates, {"now_labels": {}})
        self.assertEqual(view["steps"], ["完成 G1 剩余 1 项", "验收 G1"])
        self.assertEqual(([gate["id"] for gate in view["folded"]], view["next_gate"]), (["G2"], ""))

    def test_a_done_gate_hands_over_to_the_next(self):
        gates, _ = gate_views(contract(), LEDGER.replace("| REV-01 | x | verifying |", "| REV-01 | x | done |"))
        view = sw.stepper_view(gates, {"now_labels": {"REV-02": "在验项"}})
        self.assertEqual([gate["state"] for gate in view["gates"]], ["done", "idle"])
        self.assertEqual((view["current"], view["steps"]), ("G2", ["完成 G2 剩余 1 项", "验收 G2"]))

    def test_no_gates_no_stepper(self):
        self.assertIsNone(sw.stepper_view([], {}))


class NowContextTests(unittest.TestCase):
    def test_a_lane_listing_the_row_wins_over_a_gate_holding_it(self):
        _, now = gate_views(contract())
        self.assertEqual([(row["rev"], row["label"], row["context"]) for row in now], [("REV-02", "在验项", "语料")])

    def test_a_gate_row_names_its_lane_and_place(self):
        data = contract()
        data["focus"]["lanes"][1].pop("revs")
        _, now = gate_views(data)
        self.assertEqual(now[0]["context"], "网页化 · G1 最后一项")
        data["now_next"]["gates"][0]["revs"] = ["REV-02..REV-03"]
        _, now = gate_views(data)
        self.assertEqual(now[0]["context"], "网页化 · G1 剩余 2 项")


class LaneCardTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "ledger.md").write_text(LEDGER, encoding="utf-8")

    def lanes(self, data: dict, **kwargs) -> dict:
        view = sw.build_context(data, root=self.root, ledger=sw.parse_ledger(LEDGER), facts=None, today=TODAY,
                                registry=registry(), assets=self.root, **kwargs)
        return {lane["id"]: lane for group in view["focus"]["groups"] for lane in group["lanes"]}

    def test_status_name_condition_card_and_tally(self):
        data = contract()
        data["focus"]["lanes"][1]["title"] = "语料 · 同期推进"
        lanes = self.lanes(data)
        # A lane with one capability item shows that item's status, else its card's; neither, no chip.
        self.assertEqual((lanes["web"]["status"], lanes["web"]["status_label"]), ("in_progress", "建设中"))
        self.assertEqual((lanes["sk"]["status"], lanes["tm"]["status"]), ("in_progress", ""))
        self.assertEqual((lanes["tm"]["name"], lanes["tm"]["condition"]), ("语料", "同期推进"))
        self.assertEqual((lanes["web"]["name"], lanes["web"]["condition"]), ("网页化", ""))
        # 能力与证据 opens the lane's card, or the card of its first item.
        self.assertEqual((lanes["web"]["card"], lanes["sk"]["card"], lanes["tm"]["card"]), ("prod", "prod", ""))
        self.assertEqual((lanes["web"]["tally"], lanes["tm"]["tally"], lanes["sk"]["tally"]),
                         ("G1 1 / 2", "台账 0 / 2", ""))

    def test_review_capability_and_source_figures(self):
        data = contract()
        data["focus"]["lanes"][0]["metrics"] = ["capabilities"]
        data["focus"]["lanes"][1]["metrics"] = ["reviews", "sources"]
        lanes = self.lanes(data, reviews=[{"open": 17}, {"open": 2}])
        (capabilities,) = lanes["web"]["metrics"]
        self.assertEqual((capabilities["label"], capabilities["value"], capabilities["unit"], capabilities["sub"]),
                         ("生产能力", "1 / 2", "可用", "网页 · IDML"))
        reviews, sources = lanes["tm"]["metrics"]
        self.assertEqual((reviews["label"], reviews["value"], reviews["unit"], reviews["sub"]),
                         ("工作台输出 · 审核中", "2", "本", "待研发确认 19 项"))
        self.assertEqual((sources["value"], sources["unit"]), (str(len(registry())), "类"))
        # Without the snapshot's 审核稿 rows the figure reads 无数据, never zero.
        self.assertTrue(self.lanes(data)["tm"]["metrics"][0]["no_data"])

    def test_the_contract_accepts_the_new_figures(self):
        data = contract()
        data["focus"]["lanes"][1]["metrics"] = ["reviews", "sources", "capabilities"]
        self.assertFalse([finding for finding in sw._focus_findings(
            data["focus"], card_ids={"prod": {"web", "idml"}}, gate_ids={"G1", "G2"},
            ledger=sw.parse_ledger(LEDGER), has_corpus=False) if "metric" in finding.message])


if __name__ == "__main__":
    unittest.main()
