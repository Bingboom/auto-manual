import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import review_site

REPO = Path(__file__).resolve().parents[1]


def write_draft(directory: Path, version: str, *, model="JHP-3600C", region="JP", day="2026-10-21",
                status="待母语审校", milestone="", rd_open=(), volume=(108, 1507), **overrides) -> Path:
    (directory / "assets").mkdir(parents=True)
    (directory / "draft.html").write_text(f"<title>{version}</title>", encoding="utf-8")
    (directory / "assets" / "a.svg").write_text("<svg/>", encoding="utf-8")
    if volume:
        (directory / review_site.SUMMARY).write_text(
            json.dumps({"units": volume[0], "words": volume[1], "chars": 1}), encoding="utf-8")
    manifest = {"model": model, "region": region, "language": "ja", "version": version, "date": day,
                "status": status, "html": "draft.html", "milestone": milestone, "summary": "s",
                "rd_open": list(rd_open), **overrides}
    (directory / review_site.MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return directory


def write_milestone(line: Path, version: str, milestone: str, **fields) -> Path:
    return write_draft(line / review_site.MILESTONES / version, version, status="历史版本",
                       milestone=milestone, **fields)


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
            lines = review_site.build(drafts, out)
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
            self.assertEqual(review_site.build(drafts, out), [])
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
