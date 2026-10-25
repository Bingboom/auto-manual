import json
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.test_rtd_review_site import issue, write_draft, write_records
from tools.rtd import review_table_sync as sync
from tools.rtd.web_reviews import FIELDS

SITE = "https://review.example.com"
COLUMNS = [*FIELDS.values(), "当前执笔"]


def row(model="JHP-3600C", region="JP", **cells):
    values = {FIELDS["model"]: model, FIELDS["name"]: "Portable Power Station", FIELDS["market"]: "日规",
              FIELDS["language"]: "日语", FIELDS["version"]: "v0.68", FIELDS["date"]: 1792944000000,
              FIELDS["status"]: "待研发确认", FIELDS["open"]: 3,
              FIELDS["draft"]: {"text": f"{model} {region} v0.68 审核稿", "link": f"{SITE}/{model}/{region}/old.html"},
              FIELDS["page"]: {"text": f"{model} {region} 审核页", "link": f"{SITE}/{model}/{region}.html"},
              "当前执笔": "someone"}
    values.update(cells)
    return values


class FakeLark:
    """Serves complete_rows pages and records upserts; record-get answers in lark-cli's read shapes."""

    def __init__(self, rows: dict[str, dict], *, drop: tuple[str, ...] = ()):
        self.rows, self.drop, self.upserts, self.gets = rows, drop, [], []

    def __call__(self, args):
        option = dict(zip(args[2::2], args[3::2], strict=True))
        if args[1] == "+record-list":
            ids = list(self.rows)
            return {"code": 0, "data": {"fields": COLUMNS, "record_id_list": ids, "total": len(ids),
                                        "has_more": False,
                                        "data": [[self.rows[i].get(c) for c in COLUMNS] for i in ids]}}
        record = option["--record-id"]
        if args[1] == "+record-upsert":
            fields = json.loads(option["--json"])
            self.upserts.append((record, fields))
            for name, value in fields.items():
                if name in self.drop:
                    continue
                if name == FIELDS["date"]:
                    value = value.replace(" ", "T") + ".000+08:00"
                self.rows[record][name] = value
            return {"code": 0, "data": {}}
        if args[1] == "+record-get":
            self.gets.append(record)
            assert option["--format"] == "json"
            return {"code": 0, "data": {"fields": COLUMNS, "data": [[self.rows[record].get(c) for c in COLUMNS]]}}
        raise AssertionError(args)


class ReviewTableSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.drafts = Path(self.temp.name) / "drafts"
        line = write_draft(self.drafts / "JHP-3600C" / "JP", "v0.69", day="2026-10-24", status="待母语审校",
                           nameplate_model="ZX-90", sales_model="")
        write_records(line, issues=[issue("R01", question="q"), issue("R02", status="confirmed"),
                                    issue("L01", kind="language")])

    def tearDown(self):
        self.temp.cleanup()

    def main(self, fake, *args):
        out = StringIO()
        code = sync.main([str(self.drafts), "--base-token", "bascn", "--site-url", SITE + "/", *args],
                         run=fake, sleep=lambda seconds: None, out=out)
        return code, out.getvalue()

    def planned(self):
        return {FIELDS["version"]: "v0.69", FIELDS["date"]: "2026-10-24 00:00:00", FIELDS["status"]: "待母语审校",
                FIELDS["open"]: 1,
                FIELDS["draft"]: f"[JHP-3600C JP v0.69 审核稿]({SITE}/JHP-3600C/JP/draft.html)",
                FIELDS["page"]: f"[JHP-3600C JP 审核页]({SITE}/JHP-3600C/JP.html)"}

    def test_dry_run_prints_the_plan_and_writes_nothing(self):
        fake = FakeLark({"recA": row()})
        code, out = self.main(fake)
        self.assertEqual(code, 0, out)
        self.assertEqual(fake.upserts, [])
        self.assertIn("JHP-3600C/JP recA: 5 change(s) (dry run)", out)
        self.assertIn("当前版本: v0.68 → v0.69", out)
        self.assertIn("待研发确认: 3 → 1", out)
        self.assertIn("更新日期: 2026-10-26 → 2026-10-24", out)

    def test_write_changes_only_owned_fields_and_reads_them_back(self):
        fake = FakeLark({"recA": row(), "recB": row(model="JE-1000F", region="US")})
        code, out = self.main(fake, "--write")
        self.assertEqual(code, 0, out)
        planned = self.planned()
        del planned[FIELDS["page"]]  # the row already links its review page
        self.assertEqual(fake.upserts, [("recA", planned)])
        self.assertEqual(fake.gets, ["recA"])
        for name in (FIELDS["model"], FIELDS["name"], FIELDS["market"], FIELDS["language"], "当前执笔"):
            self.assertEqual(fake.rows["recA"][name], row()[name])
        self.assertIn("recA 当前版本=v0.69", out)
        self.assertIn(f"recA 审核页=[JHP-3600C JP 审核页]({SITE}/JHP-3600C/JP.html)", out)
        # Idempotent: a second run finds nothing to write.
        code, out = self.main(fake, "--write")
        self.assertEqual((code, len(fake.upserts)), (0, 1), out)
        self.assertIn("JHP-3600C/JP recA: up to date", out)

    def test_write_sends_only_the_changed_fields(self):
        current = row(**{FIELDS["version"]: "v0.69", FIELDS["date"]: "2026-10-24T00:00:00.000+08:00",
                         FIELDS["status"]: "待母语审校",
                         FIELDS["draft"]: f"[JHP-3600C JP v0.69 审核稿]({SITE}/JHP-3600C/JP/draft.html)"})
        fake = FakeLark({"recA": current})
        code, out = self.main(fake, "--write")
        self.assertEqual(code, 0, out)
        self.assertEqual(fake.upserts, [("recA", {FIELDS["open"]: 1})])

    def test_read_back_mismatch_fails(self):
        fake = FakeLark({"recA": row()}, drop=(FIELDS["status"],))
        code, out = self.main(fake, "--write")
        self.assertEqual(code, 1)
        self.assertIn("ERROR JHP-3600C/JP recA: 状态 read back 待研发确认, expected 待母语审校", out)

    def test_refuses_a_line_whose_model_code_would_leak(self):
        for name, cells in {"product name": {FIELDS["name"]: "zx-90 Portable"},
                            "link text": {FIELDS["draft"]: "[ZX-90 draft](https://x.example/a.html)"}}.items():
            with self.subTest(name):
                fake = FakeLark({"recA": row(**cells)})
                code, out = self.main(fake, "--write")
                self.assertEqual((code, fake.upserts), (1, []))
                self.assertIn("contains a model code", out)
        manifest_path = self.drafts / "JHP-3600C" / "JP" / "draft.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_path.write_text(json.dumps({**manifest, "status": "ZX-90 审校", "nameplate_model": "",
                                             "sales_model": "ZX-90"}), encoding="utf-8")
        fake = FakeLark({"recA": row()})
        code, out = self.main(fake, "--write")
        self.assertEqual((code, fake.upserts), (1, []))
        self.assertIn("状态 (planned) contains a model code", out)

    def test_a_code_inside_the_public_model_is_not_a_leak(self):
        manifest_path = self.drafts / "JHP-3600C" / "JP" / "draft.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_path.write_text(json.dumps({**manifest, "nameplate_model": "JHP-3600C"}), encoding="utf-8")
        code, out = self.main(FakeLark({"recA": row()}))
        self.assertEqual(code, 0, out)

    def test_unmatched_duplicate_and_mismatched_rows_fail(self):
        cases = {
            "no row": ({"recB": row(model="JE-1000F", region="US")}, "create the row by hand"),
            "two rows": ({"recA": row(), "recC": row()}, "2 rows link /JHP-3600C/JP.html"),
            "model differs": ({"recA": row(**{FIELDS["model"]: "JE-1000F"})}, "has 型号 'JE-1000F'"),
        }
        for name, (rows, message) in cases.items():
            with self.subTest(name):
                fake = FakeLark(rows)
                code, out = self.main(fake, "--write")
                self.assertEqual((code, fake.upserts), (1, []))
                self.assertIn(message, out)

    def test_line_filter_and_unknown_line(self):
        fake = FakeLark({"recA": row()})
        self.assertEqual(self.main(fake, "--line", "JHP-3600C/JP")[0], 0)
        code, out = self.main(fake, "--line", "JE-1000F/US")
        self.assertEqual(code, 1)
        self.assertIn("no working draft for ['JE-1000F/US']", out)

    def test_invalid_drafts_and_missing_token_fail(self):
        (self.drafts / "JHP-3600C" / "JP" / "issues.json").write_text("{}", encoding="utf-8")
        code, out = self.main(FakeLark({"recA": row()}))
        self.assertEqual(code, 1)
        self.assertIn("issues.json", out)
        out = StringIO()
        self.assertEqual(sync.main([str(self.drafts), "--base-token", ""], run=FakeLark({}), out=out), 1)
        self.assertIn("no Base token", out.getvalue())

    def test_site_url_comes_from_the_workbench_template(self):
        self.assertEqual(sync.review_site_url(), "https://ht-docs-review-doc-lib.readthedocs-hosted.com")

    def test_link_cell_reads_both_shapes(self):
        self.assertEqual(sync.link_cell("[a b](https://x.example/p.html)"), ("a b", "https://x.example/p.html"))
        self.assertEqual(sync.link_cell({"text": "a", "link": "https://x.example/"}), ("a", "https://x.example/"))
        self.assertEqual(sync.link_cell(None), ("", ""))


if __name__ == "__main__":
    unittest.main()
