import json
import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import review_site

REPO = Path(__file__).resolve().parents[1]


def write_draft(directory: Path, version: str, *, model="JHP-3600C", region="JP", day="2026-10-21",
                status="待母语审校", milestone="", rd_open=(), volume=(108, 1507), tools_sha="1a2b3c4",
                **overrides) -> Path:
    (directory / "assets").mkdir(parents=True)
    (directory / "draft.html").write_text(f"<title>{version}</title>", encoding="utf-8")
    (directory / "assets" / "a.svg").write_text("<svg/>", encoding="utf-8")
    if volume:
        (directory / review_site.SUMMARY).write_text(
            json.dumps({"units": volume[0], "words": volume[1], "chars": 1}), encoding="utf-8")
    manifest = {"model": model, "region": region, "language": "ja", "version": version, "date": day,
                "status": status, "html": "draft.html", "milestone": milestone, "summary": "s",
                "rd_open": list(rd_open), **overrides}
    if tools_sha is not None:
        manifest["tools_sha"] = tools_sha
    if rd_open is None:
        del manifest["rd_open"]
    (directory / review_site.MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return directory


def write_milestone(line: Path, version: str, milestone: str, **fields) -> Path:
    fields.setdefault("tools_sha", None)
    return write_draft(line / review_site.MILESTONES / version, version, status="历史版本",
                       milestone=milestone, **fields)


def issue(id_, kind="rd", status="open", **fields):
    item = {"id": id_, "title": f"title {id_}", "kind": kind, "status": status, **fields}
    if status != "open":
        item.setdefault("resolution", {"by": "R&D", "date": "2026-10-22", "evidence": "reply 3"})
    return item


def write_records(directory: Path, issues=None, decisions=None) -> None:
    """Write an issue register and/or a decisions file and point draft.json at them."""
    manifest = json.loads((directory / review_site.MANIFEST).read_text(encoding="utf-8"))
    if issues is not None:
        (directory / "issues.json").write_text(json.dumps(
            {"schema": review_site.ISSUES_SCHEMA, "issues": issues}, ensure_ascii=False), encoding="utf-8")
        manifest["issues"] = "issues.json"
        manifest.pop("rd_open", None)
    if decisions is not None:
        (directory / "records").mkdir(exist_ok=True)
        (directory / "records" / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False),
                                                              encoding="utf-8")
        manifest["decisions"] = "records/decisions.json"
    (directory / review_site.MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")


DECISION = {"id": "D01", "title": "keep the previous wording", "adopted": "previous-generation text",
            "date": "2026-10-22", "status": "applied", "source_type": "operator"}


def local_targets(page: Path):
    soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
    for tag in soup.select("a[href], link[href]"):
        href = tag["href"].split("#", 1)[0]
        if href and not href.startswith("http"):
            yield href, page.parent / href


class ReviewSiteTests(unittest.TestCase):
    def test_builds_an_overview_and_one_page_per_line(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            jhp = write_draft(drafts / "JHP-3600C" / "JP", "v0.69", rd_open=["50Hz／60Hz 默认值", "车充 24V"])
            write_milestone(jhp, "v0.9", "首个完整稿", day="2026-10-12", volume=(77, 879))
            write_milestone(jhp, "v0.62", "研发答复回填", day="2026-10-20")
            write_draft(drafts / "JE-1000F" / "US", "v0.3", model="JE-1000F", region="US", volume=None)
            lines, warnings = review_site.build(drafts, out)
            self.assertEqual(warnings, [])
            self.assertEqual([(line["model"], line["current"]["version"]) for line in lines],
                             [("JE-1000F", "v0.3"), ("JHP-3600C", "v0.69")])
            # Numeric version order: v0.62 > v0.9.
            self.assertEqual([m["version"] for m in lines[1]["milestones"]], ["v0.62", "v0.9"])
            index = BeautifulSoup((out / "index.html").read_text(encoding="utf-8"), "html.parser")
            self.assertEqual(index.select_one('meta[name="robots"]')["content"], "noindex,nofollow")
            rows = index.select("tbody > tr")
            self.assertEqual([row.td.get_text(strip=True) for row in rows], ["JE-1000F", "JHP-3600C"])
            row = rows[1].get_text(" ", strip=True)
            for expected in ("日规 JP", "v0.69", "2026-10-21", "待母语审校", "108 单元 · 1507 词", "2 项", "2 个"):
                self.assertIn(expected, row)
            self.assertIn("—", rows[0].get_text(" ", strip=True))  # no summary file → no volume
            self.assertEqual([tag.get_text(strip=True) for tag in index.select(".rd-nav-model")],
                             ["JE-1000F", "JHP-3600C"])
            line_page = out / "JHP-3600C" / "JP.html"
            page = BeautifulSoup(line_page.read_text(encoding="utf-8"), "html.parser")
            self.assertEqual(page.h1.get_text(strip=True), "JHP-3600C 日规 JP")
            self.assertEqual(page.select_one('.app-nav-link[aria-current="page"]')["href"], "../JHP-3600C/JP.html")
            self.assertEqual(len(page.select("#rd-open li")), 2)
            milestones = page.select_one("#milestones").get_text(" ", strip=True)
            for expected in ("研发答复回填", "首个完整稿", "77 单元 · 879 词"):
                self.assertIn(expected, milestones)
            for source in (out / "index.html", line_page, out / "JE-1000F" / "US.html"):
                for href, target in local_targets(source):
                    self.assertTrue(target.is_file(), f"{source.name}: {href}")
            self.assertTrue((out / "JHP-3600C/JP/milestones/v0.62/assets/a.svg").is_file())
            for name in review_site.STYLESHEETS:
                self.assertTrue((out / "_static" / name).is_file(), name)

    def test_empty_root_renders_an_empty_list(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            drafts.mkdir()
            self.assertEqual(review_site.build(drafts, out), ([], []))
            self.assertIn("还没有审核稿", (out / "index.html").read_text(encoding="utf-8"))

    def test_refuses_unsound_manifests(self):
        cases = {
            "path does not match": ("current", {"region": "US"}),
            "bad version": ("current", {"version": "0.69"}),
            "bad date": ("current", {"date": "2026/10/21"}),
            "html outside": ("current", {"html": "../x.html"}),
            "missing html": ("current", {"html": "none.html"}),
            "empty status": ("current", {"status": ""}),
            "rd_open not a list": ("current", {"rd_open": "x"}),
            "working draft without tools_sha": ("current", {"tools_sha": None}),
            "tools_sha not hex": ("current", {"tools_sha": "HEAD"}),
            "tools_sha too short": ("current", {"tools_sha": "1a2b3c"}),
            "milestone with a bad tools_sha": ("milestone", {"tools_sha": "main"}),
            "milestone folder is not its version": ("milestone", {"version": "v0.63"}),
            "milestone without a name": ("milestone", {"milestone": ""}),
        }
        for name, (which, overrides) in cases.items():
            with self.subTest(name), TemporaryDirectory() as temp:
                drafts = Path(temp) / "drafts"
                line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
                directory = line if which == "current" else write_milestone(line, "v0.62", "研发答复回填")
                manifest = json.loads((directory / review_site.MANIFEST).read_text(encoding="utf-8"))
                manifest.update(overrides)
                manifest = {key: value for key, value in manifest.items() if value is not None}
                (directory / review_site.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises(ValueError):
                    review_site.load_drafts(drafts)

    def test_refuses_version_directories_beside_the_working_draft(self):
        with TemporaryDirectory() as temp:
            drafts = Path(temp) / "drafts"
            line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
            write_draft(line / "v0.68", "v0.68")
            with self.assertRaisesRegex(ValueError, "JHP-3600C/JP/v0.68/draft.json"):
                review_site.load_drafts(drafts)
        with TemporaryDirectory() as temp:  # the old one-directory-per-version layout
            drafts = Path(temp) / "drafts"
            write_draft(drafts / "JHP-3600C" / "JP" / "v0.69", "v0.69")
            with self.assertRaisesRegex(ValueError, "git history"):
                review_site.load_drafts(drafts)
        with TemporaryDirectory() as temp:  # a milestone with no working draft
            drafts = Path(temp) / "drafts"
            write_milestone(drafts / "JHP-3600C" / "JP", "v0.62", "研发答复回填")
            with self.assertRaises(ValueError):
                review_site.load_drafts(drafts)

    def test_refuses_symlinks_inside_a_draft(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            directory = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
            secret = Path(temp) / "secret.txt"
            secret.write_text("x", encoding="utf-8")
            os.symlink(secret, directory / "assets" / "leak.txt")
            with self.assertRaises(RuntimeError):
                review_site.build(drafts, out)

    def test_issue_register_derives_rd_open_and_counts(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
            write_records(line, issues=[
                issue("R01", question="50Hz or 60Hz default?", extra_column="kept"),
                issue("R02", adoption={"decision": "keep previous text", "by": "operator", "date": "2026-10-22"}),
                issue("R03", status="confirmed"),
                issue("L01", kind="language"), issue("L02", kind="language", status="dropped"),
                issue("C01", kind="compliance"), issue("G01", kind="design", status="confirmed"),
            ], decisions=[DECISION, {**DECISION, "id": "D02"}])
            (lines, warnings) = review_site.build(drafts, out)
            current = lines[0]["current"]
            self.assertEqual(current["rd_open"], ["R01 title R01：50Hz or 60Hz default?", "R02 title R02"])
            self.assertEqual(current["open"], {"rd": 2, "language": 1, "compliance": 1, "design": 0, "content": 0})
            self.assertEqual(current["other_count"], 2)
            self.assertEqual(current["decisions"], 2)
            self.assertEqual(current["tools_sha"], "1a2b3c4")
            index = BeautifulSoup((out / "index.html").read_text(encoding="utf-8"), "html.parser")
            self.assertIn("其他待确认", index.select_one("thead").get_text())
            self.assertEqual(index.select_one("tbody tr").select("td")[7].get_text(strip=True), "2 项")
            page_path = out / "JHP-3600C" / "JP.html"
            page = BeautifulSoup(page_path.read_text(encoding="utf-8"), "html.parser")
            self.assertEqual(len(page.select("#rd-open li")), 2)
            other = page.select_one("#other-open")
            self.assertEqual([h.get_text(strip=True) for h in other.select("h3")], ["语言审校（1）", "合规（1）"])
            self.assertIn("1a2b3c4", page.get_text())
            self.assertIn("2 项", page.select_one(".kpi-row").get_text())
            self.assertIsNone(page.select_one("#cross-line"))
            for href, target in local_targets(page_path):
                self.assertTrue(target.is_file(), href)

    def test_line_without_a_register_shows_unknown_other_counts(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            write_draft(drafts / "JHP-3600C" / "JP", "v0.69", rd_open=["q"])
            lines, _ = review_site.build(drafts, out)
            self.assertIsNone(lines[0]["current"]["other_count"])
            index = BeautifulSoup((out / "index.html").read_text(encoding="utf-8"), "html.parser")
            self.assertEqual(index.select_one("tbody tr").select("td")[7].get_text(strip=True), "—")
            page = BeautifulSoup((out / "JHP-3600C" / "JP.html").read_text(encoding="utf-8"), "html.parser")
            self.assertIn("还没有问题清单", page.select_one("#other-open").get_text())

    def test_rd_open_may_stay_when_it_equals_the_register(self):
        with TemporaryDirectory() as temp:
            drafts = Path(temp) / "drafts"
            line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
            write_records(line, issues=[issue("R01", question="q"), issue("R02", status="confirmed")])
            manifest = json.loads((line / review_site.MANIFEST).read_text(encoding="utf-8"))
            for rd_open, ok in ((["R01 title R01：q"], True), (["R01 title R01"], False), ([], False)):
                with self.subTest(rd_open):
                    (line / review_site.MANIFEST).write_text(json.dumps({**manifest, "rd_open": rd_open}),
                                                             encoding="utf-8")
                    if ok:
                        self.assertEqual(review_site.load_drafts(drafts)[0][0]["current"]["rd_open"], rd_open)
                    else:
                        with self.assertRaisesRegex(ValueError, "JP/draft.json: rd_open differs"):
                            review_site.load_drafts(drafts)

    def test_refuses_unsound_issue_registers(self):
        cases = {
            "duplicate id": [issue("R01"), issue("R01")],
            "empty id": [issue("")],
            "no title": [{**issue("R01"), "title": ""}],
            "unknown kind": [issue("R01", kind="legal")],
            "unknown status": [issue("R01", status="answered")],
            "closed without resolution": [{**issue("R01", status="confirmed"), "resolution": None}],
            "resolution without evidence": [issue("R01", status="dropped", resolution={"by": "x", "date": "2026-10-22"})],
            "resolution date not ISO": [issue("R01", status="confirmed",
                                              resolution={"by": "x", "date": "22/10", "evidence": "e"})],
            "bad topic": [issue("R01", topic="Solar Input")],
            "question not text": [issue("R01", question=3)],
            "adoption without date": [issue("R01", adoption={"decision": "keep", "by": "op"})],
            "not an object": ["R01"],
        }
        for name, issues in cases.items():
            with self.subTest(name), TemporaryDirectory() as temp:
                drafts = Path(temp) / "drafts"
                line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
                write_records(line, issues=issues)
                with self.assertRaisesRegex(ValueError, "JP/issues.json: issues\\[") as caught:
                    review_site.load_drafts(drafts)
                self.assertNotIn("Traceback", str(caught.exception))

    def test_refuses_unsound_record_paths_and_files(self):
        def setup(line: Path, temp: str):
            outside = Path(temp) / "outside.json"
            outside.write_text("[]", encoding="utf-8")
            os.symlink(outside, line / "linked.json")
            (line / "folder").mkdir()
        cases = {
            "absolute": ("issues", lambda temp: str(Path(temp) / "outside.json"), "relative path"),
            "parent": ("issues", lambda temp: "../outside.json", "relative path"),
            "backslash": ("decisions", lambda temp: "records\\d.json", "relative path"),
            "symlink": ("decisions", lambda temp: "linked.json", "symbolic link"),
            "directory": ("issues", lambda temp: "folder", "regular file"),
            "missing": ("decisions", lambda temp: "none.json", "regular file"),
            "empty": ("issues", lambda temp: "", "relative path"),
        }
        for name, (key, value, message) in cases.items():
            with self.subTest(name), TemporaryDirectory() as temp:
                drafts = Path(temp) / "drafts"
                line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69", **{key: value(temp)})
                setup(line, temp)
                with self.assertRaisesRegex(ValueError, f"JP/draft.json: {key} .*{message}"):
                    review_site.load_drafts(drafts)
        with TemporaryDirectory() as temp:  # wrong schema / not JSON
            drafts = Path(temp) / "drafts"
            line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69", issues="issues.json")
            for content in ('{"schema": "review-issues/2", "issues": []}', "not json", "[]"):
                (line / "issues.json").write_text(content, encoding="utf-8")
                with self.subTest(content), self.assertRaisesRegex(ValueError, "JP/issues.json"):
                    review_site.load_drafts(drafts)

    def test_refuses_unsound_decisions(self):
        cases = {
            "bad id": [{**DECISION, "id": "D1"}],
            "duplicate id": [DECISION, DECISION],
            "no adopted": [{**DECISION, "adopted": ""}],
            "bad date": [{**DECISION, "date": "yesterday"}],
            "no status": [{key: value for key, value in DECISION.items() if key != "status"}],
            "not a list": {"D01": DECISION},
        }
        for name, decisions in cases.items():
            with self.subTest(name), TemporaryDirectory() as temp:
                drafts = Path(temp) / "drafts"
                line = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
                write_records(line, decisions=decisions)
                with self.assertRaisesRegex(ValueError, "JP/records/decisions.json"):
                    review_site.load_drafts(drafts)

    def test_cross_line_topics_warn_without_failing(self):
        def run(jp_status, us_status, *, us_model="JHP-3600C"):
            with TemporaryDirectory() as temp:
                drafts, out = Path(temp) / "drafts", Path(temp) / "out"
                jp = write_draft(drafts / "JHP-3600C" / "JP", "v0.69")
                us = write_draft(drafts / us_model / "US", "v0.3", model=us_model, region="US")
                write_records(jp, issues=[issue("R04", status=jp_status, topic="solar-input")])
                write_records(us, issues=[issue("R09", status=us_status, topic="solar-input"),
                                          issue("R10", topic="other-topic")])
                lines, warnings = review_site.build(drafts, out)
                pages = {line["region"]: BeautifulSoup((out / line["page"]).read_text(encoding="utf-8"),
                                                       "html.parser") for line in lines}
                return warnings, pages
        warnings, pages = run("open", "confirmed")
        self.assertEqual(len(warnings), 1)
        self.assertIn("JHP-3600C topic solar-input", warnings[0])
        self.assertIn("JP R04 open", warnings[0])
        self.assertIn("US R09 confirmed", warnings[0])
        for page in pages.values():
            self.assertIn("跨稿线待同步", page.select_one("#cross-line").get_text())
        for jp_status, us_status in (("open", "open"), ("confirmed", "confirmed"), ("dropped", "open"),
                                     ("confirmed", "dropped")):
            with self.subTest((jp_status, us_status)):
                warnings, pages = run(jp_status, us_status)
                self.assertEqual(warnings, [])
                self.assertIsNone(pages["JP"].select_one("#cross-line"))
        with self.subTest("other model"):
            self.assertEqual(run("open", "confirmed", us_model="JE-1000F")[0], [])

    def test_main_prints_warnings(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            write_records(write_draft(drafts / "JHP-3600C" / "JP", "v0.69"),
                          issues=[issue("R04", topic="solar-input")])
            write_records(write_draft(drafts / "JHP-3600C" / "US", "v0.3", region="US"),
                          issues=[issue("R09", status="confirmed", topic="solar-input")])
            with redirect_stdout(StringIO()) as printed:
                self.assertEqual(review_site.main([str(drafts), str(out)]), 0)
            self.assertIn("WARNING JHP-3600C topic solar-input", printed.getvalue())

    def test_every_draft_page_links_back_to_the_overview_in_the_output_only(self):
        pages = {
            "controls": '<body><header class="toolbar"><div class="controls"><button>x</button></div></header>',
            "actions": '<body class="p"><header class="preview-toolbar"><div class="toolbar-actions wide">'
                       '<a>y</a></div></header>',
            "bare": "<html><body data-x=1><p>z</p></body></html>",
            "already": '<body><header class="toolbar"><div class="controls"><button type="button" '
                       'class="to-overview">← 审核稿总览</button></div></header>',
        }
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            sources = {}
            for index, (name, html) in enumerate(pages.items()):
                line = write_draft(drafts / "JHP-3600C" / f"R{index}", "v0.69", region=f"R{index}")
                (line / "draft.html").write_bytes((html + "\r\n").encode("utf-8"))
                milestone = write_milestone(line, "v0.62", "研发答复回填", region=f"R{index}")
                (milestone / "draft.html").write_bytes(html.encode("utf-8"))
                sources[name] = (line / "draft.html", milestone / "draft.html")
            before = {path: path.read_bytes() for pair in sources.values() for path in pair}
            review_site.build(drafts, out)
            review_site.build(drafts, out)  # a rebuild over the output adds nothing twice
            self.assertEqual({path: path.read_bytes() for path in before}, before)  # sources untouched

            def built(name, which):
                return (out / sources[name][which].relative_to(drafts)).read_text(encoding="utf-8")
            for name in pages:
                for which, index in ((0, "../../index.html"), (1, "../../../../index.html")):
                    with self.subTest(name=name, which=which):
                        page = built(name, which)
                        soup = BeautifulSoup(page, "html.parser")
                        links = soup.select(".to-overview")
                        self.assertEqual(len(links), 1)
                        if name == "already":
                            self.assertNotIn("onclick", page)
                            continue
                        target = links[0].get("href") or links[0]["onclick"]
                        self.assertIn(index, target)
                        resolved = (out / sources[name][which].relative_to(drafts)).parent / index
                        self.assertEqual(resolved.resolve(), (out / "index.html").resolve())
                        if name == "bare":
                            self.assertIs(soup.body.contents[1], soup.select_one("nav.to-overview-bar"))
                            self.assertIn("@media print", page)
                        else:
                            group = soup.select_one("div.controls, div.toolbar-actions")
                            self.assertIs(group.contents[0], links[0])
                            self.assertEqual(links[0].name, "button")
            # Bytes are otherwise preserved, line endings included.
            self.assertTrue((out / sources["controls"][0].relative_to(drafts)).read_bytes().endswith(b"\r\n"))

    def test_read_the_docs_builds_the_review_site_before_the_bootstrap(self):
        config = (REPO / ".readthedocs.yaml").read_text(encoding="utf-8")
        review = config.index("elif [ -d docs/review-drafts ]")
        self.assertLess(config.index("docs/publish/web/conf.py"), review)
        self.assertLess(review, config.index("else\n"))
        self.assertIn('python -m tools.rtd.review_site docs/review-drafts "$READTHEDOCS_OUTPUT/html"', config)

    def test_workbench_review_entry_links_the_private_site_and_hides_without_a_url(self):
        env = Environment(loader=FileSystemLoader(str(review_site.ASSETS)))
        source = env.loader.get_source(env, "manual_workbench.html")[0]
        render = lambda text: env.from_string(text).render(pathto=lambda *args: "x")  # noqa: E731
        url = "https://ht-docs-review-doc-lib.readthedocs-hosted.com/"
        configured = "{% set review_site = '" + url + "' %}"
        self.assertEqual(source.count(configured), 1)
        shown = render(source)
        self.assertIn(f'href="{url}"', shown)
        self.assertIn("审核稿（私有）", shown)
        self.assertNotIn("审核稿（私有）", render(source.replace(configured, "{% set review_site = '' %}", 1)))


if __name__ == "__main__":
    unittest.main()
