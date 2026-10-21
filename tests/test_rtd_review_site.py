import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import review_site

REPO = Path(__file__).resolve().parents[1]


def write_draft(root: Path, version: str, *, model="JHP-3600C", region="JP", day="2026-10-21",
                status="待母语审校", milestone="", rd_open=(), volume=(108, 1507), **overrides) -> Path:
    directory = root / model / region / version
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


class ReviewSiteTests(unittest.TestCase):
    def test_builds_one_row_per_line_with_history_and_copied_drafts(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            write_draft(drafts, "v0.9", day="2026-10-12", status="历史版本", milestone="首个完整稿", volume=(77, 879))
            write_draft(drafts, "v0.69", rd_open=["50Hz／60Hz 默认值", "车充 24V"])
            write_draft(drafts, "v0.62", day="2026-10-20", status="历史版本", milestone="研发答复回填")
            write_draft(drafts, "v0.3", model="JE-1000F", region="US", volume=None)
            lines = review_site.build(drafts, out)
            self.assertEqual([(line["model"], line["latest"]["version"]) for line in lines],
                             [("JE-1000F", "v0.3"), ("JHP-3600C", "v0.69")])
            # Numeric version order: v0.69 > v0.62 > v0.9.
            self.assertEqual([d["version"] for d in lines[1]["history"]], ["v0.62", "v0.9"])
            soup = BeautifulSoup((out / "index.html").read_text(encoding="utf-8"), "html.parser")
            self.assertEqual(soup.select_one('meta[name="robots"]')["content"], "noindex,nofollow")
            rows = soup.select("tbody > tr:not(.rd-history-row)")
            self.assertEqual([row.td.get_text(strip=True) for row in rows], ["JE-1000F", "JHP-3600C"])
            jhp = rows[1].get_text(" ", strip=True)
            for expected in ("v0.69", "2026-10-21", "待母语审校", "108 单元 · 1507 词", "2 项"):
                self.assertIn(expected, jhp)
            self.assertIn("—", rows[0].get_text(" ", strip=True))  # no summary file → no volume
            for link in soup.select("a[href]"):
                if not link["href"].startswith("http"):
                    self.assertTrue((out / link["href"]).is_file(), link["href"])
            self.assertTrue((out / "drafts/JHP-3600C/JP/v0.62/assets/a.svg").is_file())
            for name in review_site.STYLESHEETS:
                self.assertTrue((out / "_static" / name).is_file(), name)
            history = soup.select_one(".rd-history-row").get_text(" ", strip=True)
            self.assertIn("研发答复回填", history)
            self.assertIn("77 单元 · 879 词", history)

    def test_empty_root_renders_an_empty_list(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            drafts.mkdir()
            self.assertEqual(review_site.build(drafts, out), [])
            self.assertIn("还没有审核稿", (out / "index.html").read_text(encoding="utf-8"))

    def test_refuses_unsound_manifests(self):
        cases = {
            "path does not match": dict(model="JHP-3600C", version="v0.69", overrides={"version": "v0.70"}),
            "bad version": dict(model="JHP-3600C", version="0.69", overrides={}),
            "bad date": dict(model="JHP-3600C", version="v0.69", overrides={"date": "2026/10/21"}),
            "html outside": dict(model="JHP-3600C", version="v0.69", overrides={"html": "../x.html"}),
            "missing html": dict(model="JHP-3600C", version="v0.69", overrides={"html": "none.html"}),
            "empty status": dict(model="JHP-3600C", version="v0.69", overrides={"status": ""}),
            "rd_open not a list": dict(model="JHP-3600C", version="v0.69", overrides={"rd_open": "x"}),
        }
        for name, case in cases.items():
            with self.subTest(name), TemporaryDirectory() as temp:
                drafts = Path(temp) / "drafts"
                directory = write_draft(drafts, case["version"])
                manifest = json.loads((directory / review_site.MANIFEST).read_text(encoding="utf-8"))
                manifest.update(case["overrides"])
                (directory / review_site.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises(ValueError):
                    review_site.load_drafts(drafts)

    def test_refuses_symlinks_inside_a_draft(self):
        with TemporaryDirectory() as temp:
            drafts, out = Path(temp) / "drafts", Path(temp) / "out"
            directory = write_draft(drafts, "v0.69")
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

    def test_workbench_review_entry_hides_until_the_site_url_is_set(self):
        env = Environment(loader=FileSystemLoader(str(review_site.ASSETS)))
        source = env.loader.get_source(env, "manual_workbench.html")[0]
        render = lambda text: env.from_string(text).render(pathto=lambda *args: "x")  # noqa: E731
        self.assertNotIn("审核稿（私有）", render(source))
        shown = render(source.replace("{% set review_site = '' %}", "{% set review_site = 'https://r.example/' %}", 1))
        self.assertIn('href="https://r.example/"', shown)
        self.assertIn("审核稿（私有）", shown)


if __name__ == "__main__":
    unittest.main()
