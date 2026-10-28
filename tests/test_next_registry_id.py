from __future__ import annotations

import io
import json
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools import next_registry_id as nid

MAIN_REGISTRY = """\
## Registry

| ID | Scope | Grant | Expiry | Status |
| --- | --- | --- | --- | --- |
| MA-170 | x | y | z | 生效 |

| ID | Scope | Grant | Expiry | Status |
| --- | --- | --- | --- | --- |
| MA-169 | x | y | z | 已失效 |
"""

LEDGER = """\
| <a id="rev-44"></a>REV-44 | SSOT | — | x | done | a |
| <a id="rev-45"></a>REV-45 | Agent | REV-44 | x | planned | a |
| G1 发布基线 | REV-01–12 验收 | 未验收 |
"""


def diff(*added: str, context: str = "") -> str:
    lines = ["diff --git a/f b/f", "@@ -1,3 +1,4 @@", f" {context}" if context else " ## Registry"]
    lines += [f"+{line}" for line in added]
    return "\n".join(lines) + "\n"


ARCHIVE = """\
## Expired registry rows

| ID | Scope | Grant | Expiry | Status |
| --- | --- | --- | --- | --- |
| MA-180 | x | y | z | 已失效 |
"""


class FakeRun:
    """``run(args)`` for git and gh, answering from in-memory fixtures.

    ``main`` is one text for every ``git show``, or a ``{path: text}`` map where a
    missing path fails the way ``git show`` does.
    """

    def __init__(self, *, main: str | dict[str, str], prs: dict[int, tuple[list[str], str]],
                 gh_works: bool = True, origin: str = "https://github.com/Bingboom/auto-manual.git"):
        self.main = main
        self.prs = prs
        self.gh_works = gh_works
        self.origin = origin
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> str:
        self.calls.append(args)
        if args[:1] == ["git"] and "show" in args:
            if isinstance(self.main, str):
                return self.main
            path = args[-1].split(":", 1)[1]
            if path not in self.main:
                raise subprocess.CalledProcessError(128, args)
            return self.main[path]
        if args[:1] == ["git"] and "get-url" in args:
            return self.origin + "\n"
        if args[:1] == ["git"]:
            return ""
        if args[:1] == ["gh"] and not self.gh_works:
            raise subprocess.CalledProcessError(1, args)
        if args[:3] == ["gh", "pr", "list"]:
            return json.dumps([{"number": n, "files": [{"path": p} for p in files]}
                               for n, (files, _) in self.prs.items()])
        if args[:3] == ["gh", "pr", "diff"]:
            return self.prs[int(args[3])][1]
        raise AssertionError(f"unexpected command {args}")


class ParsingTests(unittest.TestCase):
    def test_reads_row_numbers_of_both_tables(self):
        self.assertEqual(nid.numbers(MAIN_REGISTRY.splitlines(), nid.TABLES["ma"]), {169, 170})
        self.assertEqual(nid.numbers(LEDGER.splitlines(), nid.TABLES["rev"]), {44, 45})

    def test_diff_mode_counts_only_added_rows(self):
        text = diff("| MA-171 | new | g | e | 生效 |", context="| MA-170 | x | y | z | 生效 |")
        lines = text.splitlines() + ["-| MA-168 | old | g | e | 生效 |"]
        self.assertEqual(nid.numbers(lines, nid.TABLES["ma"], added_only=True), {171})

    def test_labels_keep_the_table_width(self):
        self.assertEqual((nid.label(nid.TABLES["ma"], 7), nid.label(nid.TABLES["rev"], 7)), ("MA-007", "REV-07"))
        self.assertEqual(nid.next_free(set()), 1)


class ReportTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        registry = self.root / nid.TABLES["ma"].path
        registry.parent.mkdir(parents=True)
        registry.write_text(MAIN_REGISTRY, encoding="utf-8")

    def test_open_prs_reserve_new_numbers_but_not_edited_rows(self):
        run = FakeRun(main=MAIN_REGISTRY, prs={
            1277: ([nid.TABLES["ma"].path], diff("| MA-171 | new | g | e | 生效 |", "| MA-169 | x | y | z | 已失效（…） |")),
            1276: ([nid.TABLES["ma"].path, "other.md"], diff("| MA-172 | new | g | e | 生效 |")),
            1300: (["unrelated.py"], ""),
        })
        nxt, why = nid.report("ma", run=run, root=self.root)
        self.assertEqual(nxt, "MA-173")
        self.assertEqual(why, "main has up to MA-170; open PRs reserve MA-171 (#1277), MA-172 (#1276)")
        # A PR that does not touch the registry is never diffed.
        self.assertNotIn(["gh", "pr", "diff", "1300"], run.calls)
        self.assertIn(["git", "-C", str(self.root), "fetch", "-q", "origin", "main"], run.calls)

    def test_this_checkout_counts_and_fetch_can_be_skipped(self):
        registry = self.root / nid.TABLES["ma"].path
        registry.write_text(MAIN_REGISTRY.replace("| MA-170 |", "| MA-174 | mine | g | e | 生效 |\n| MA-170 |"),
                            encoding="utf-8")
        run = FakeRun(main=MAIN_REGISTRY, prs={})
        nxt, why = nid.report("ma", run=run, root=self.root, fetch=False)
        self.assertEqual((nxt, why), ("MA-175", "main has up to MA-170; this checkout adds MA-174"))
        self.assertFalse(any("fetch" in call for call in run.calls))

    def test_archived_rows_on_main_or_here_count_as_used(self):
        ma = nid.TABLES["ma"]
        run = FakeRun(main={ma.path: MAIN_REGISTRY, ma.archive: ARCHIVE}, prs={})
        self.assertEqual(nid.report("ma", run=run, root=self.root, fetch=False),
                         ("MA-181", "main has up to MA-180"))
        archive = self.root / ma.archive
        archive.write_text(ARCHIVE.replace("| MA-180 |", "| MA-182 | moved | g | e | 已失效 |\n| MA-180 |"),
                           encoding="utf-8")
        self.assertEqual(nid.report("ma", run=run, root=self.root, fetch=False),
                         ("MA-183", "main has up to MA-180; this checkout adds MA-182"))

    def test_an_archive_main_lacks_reads_as_empty_but_the_registry_must_exist(self):
        ma = nid.TABLES["ma"]
        run = FakeRun(main={ma.path: MAIN_REGISTRY}, prs={})
        self.assertEqual(nid.report("ma", run=run, root=self.root, fetch=False),
                         ("MA-171", "main has up to MA-170"))
        with self.assertRaises(subprocess.CalledProcessError):
            nid.report("ma", run=FakeRun(main={}, prs={}), root=self.root, fetch=False)

    def test_moving_rows_to_the_archive_reserves_nothing(self):
        ma = nid.TABLES["ma"]
        run = FakeRun(main={ma.path: MAIN_REGISTRY, ma.archive: ARCHIVE}, prs={
            1290: ([ma.archive], diff("| MA-170 | x | y | z | 已失效（…） |", context="| MA-180 | x | y | z | 已失效 |")),
            1291: ([ma.archive], diff("| MA-184 | new | g | e | 生效 |")),
        })
        nxt, why = nid.report("ma", run=run, root=self.root, fetch=False)
        self.assertEqual((nxt, why), ("MA-185", "main has up to MA-180; open PRs reserve MA-184 (#1291)"))
        # A PR that touches only the archive is still diffed.
        self.assertIn(["gh", "pr", "diff", "1290"], run.calls)

    def test_rev_numbers_come_from_the_ledger(self):
        run = FakeRun(main=LEDGER, prs={9: ([nid.TABLES["rev"].path],
                                            diff('| <a id="rev-46"></a>REV-46 | x | — | x | planned | a |'))})
        nxt, why = nid.report("rev", run=run, root=self.root, fetch=False)
        self.assertEqual((nxt, why), ("REV-47", "main has up to REV-45; open PRs reserve REV-46 (#9)"))


class FakeApi:
    """``http(url)`` for the GitHub REST endpoints the fallback reads."""

    def __init__(self, prs: dict[int, list[dict]], raw: dict[str, str] | None = None):
        self.prs = prs
        self.raw = raw or {}
        self.urls: list[str] = []

    def __call__(self, url: str) -> str:
        self.urls.append(url)
        if url in self.raw:
            return self.raw[url]
        base = f"{nid.GITHUB_API}/repos/Bingboom/auto-manual/pulls"
        if url.startswith(f"{base}?state=open"):
            return json.dumps([{"number": n} for n in self.prs] if "page=1" in url else [])
        number = int(url[len(base) + 1:].split("/", 1)[0])
        return json.dumps(self.prs[number] if "page=1" in url else [])


class ApiFallbackTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_open_prs_come_from_the_api_when_gh_cannot_run(self):
        ma = nid.TABLES["ma"]
        raw_url = "https://github.com/Bingboom/auto-manual/raw/abc/code-as-doc/dev/merge_authorizations.md"
        api = FakeApi({
            1634: [{"filename": ma.path, "patch": "@@ -1 +1,2 @@\n+| MA-171 | new | g | e | 生效 |\n | MA-170 | x |"}],
            1635: [{"filename": ma.path, "raw_url": raw_url}],  # no patch: GitHub left out a large diff
            1636: [{"filename": "tools/other.py", "patch": "+| MA-999 | not the registry |"}],
            1637: [{"filename": ma.archive, "patch": "+| MA-169 | x | y | z | 已失效 |"}],
        }, raw={raw_url: MAIN_REGISTRY.replace("| MA-170 |", "| MA-172 | big | g | e | 生效 |\n| MA-170 |")})
        run = FakeRun(main={ma.path: MAIN_REGISTRY}, prs={}, gh_works=False,
                      origin="http://local_proxy@127.0.0.1:41241/git/Bingboom/auto-manual")
        nxt, why = nid.report("ma", run=run, root=self.root, fetch=False, http=api)
        self.assertEqual(nxt, "MA-173")
        self.assertEqual(why, "main has up to MA-170; open PRs reserve MA-171 (#1634), MA-172 (#1635); "
                              "open PRs read from the GitHub API (gh unavailable)")

    def test_pages_follow_until_a_short_page(self):
        api_pages = {1: [{"n": i} for i in range(100)], 2: [{"n": 100}]}
        seen: list[str] = []

        def http(url: str) -> str:
            seen.append(url)
            return json.dumps(api_pages.get(int(url.rsplit("page=", 1)[1]), []))
        self.assertEqual(len(nid._pages("https://api.example/items?state=open", http)), 101)
        self.assertEqual(seen, ["https://api.example/items?state=open&per_page=100&page=1",
                                "https://api.example/items?state=open&per_page=100&page=2"])

    def test_slug_reads_https_ssh_and_proxied_origins(self):
        for origin in ("https://github.com/Bingboom/auto-manual.git", "git@github.com:Bingboom/auto-manual.git",
                       "http://local_proxy@127.0.0.1:41241/git/Bingboom/auto-manual/"):
            run = FakeRun(main="", prs={}, origin=origin)
            self.assertEqual(nid.github_slug(run=run, root=self.root), "Bingboom/auto-manual", origin)
        with self.assertRaises(ValueError):
            nid.github_slug(run=FakeRun(main="", prs={}, origin="nowhere"), root=self.root)


class UniqueTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        ma = nid.TABLES["ma"]
        (self.root / ma.path).parent.mkdir(parents=True)
        (self.root / ma.path).write_text(MAIN_REGISTRY, encoding="utf-8")
        (self.root / ma.archive).write_text(ARCHIVE, encoding="utf-8")
        (self.root / nid.TABLES["rev"].path).write_text(LEDGER, encoding="utf-8")

    def check(self) -> tuple[int, list[str]]:
        lines: list[str] = []
        return nid.check_unique(self.root, printer=lines.append), lines

    def test_unique_numbers_pass(self):
        self.assertEqual(self.check(), (0, ["[registry-ids] MA and REV numbers are unique"]))

    def test_a_number_taken_by_two_rows_fails_across_registry_and_archive(self):
        ma = nid.TABLES["ma"]
        (self.root / ma.path).write_text(MAIN_REGISTRY.replace("| MA-170 |", "| MA-180 | mine | g | e | 生效 |\n| MA-170 |"),
                                         encoding="utf-8")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "[registry-ids] MA-180 is used by 2 rows")
        self.assertIn("python -m tools.next_registry_id ma|rev", lines[1])

    def test_rev_numbers_must_be_unique_too(self):
        rev = self.root / nid.TABLES["rev"].path
        rev.write_text(LEDGER + '| <a id="rev-45"></a>REV-45 | again | — | x | planned | a |\n', encoding="utf-8")
        self.assertEqual(nid.duplicates(self.root), [("REV-45", 2)])

    def test_historical_pairs_are_allowed_but_not_a_third_row(self):
        ma = nid.TABLES["ma"]
        pair = "| MA-067 | first | g | e | 已失效 |\n| MA-067 | second | g | e | 已失效 |\n"
        (self.root / ma.archive).write_text(ARCHIVE + pair, encoding="utf-8")
        self.assertEqual(nid.duplicates(self.root), [])
        (self.root / ma.archive).write_text(ARCHIVE + pair + "| MA-067 | third | g | e | 生效 |\n", encoding="utf-8")
        self.assertEqual(nid.duplicates(self.root), [("MA-067", 3)])

    def test_the_checked_in_tables_have_no_new_duplicates(self):
        self.assertEqual(nid.duplicates(Path(nid.__file__).resolve().parents[1]), [])


class CliTests(unittest.TestCase):
    def test_prints_the_id_on_stdout_and_the_reason_on_stderr(self):
        with patch.object(nid, "report", return_value=("MA-173", "main has up to MA-172")), \
                redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            self.assertEqual(nid.main(["ma", "--no-fetch"]), 0)
        self.assertEqual((out.getvalue(), err.getvalue()), ("MA-173\n", "main has up to MA-172\n"))

    def test_a_failing_command_is_an_error(self):
        def boom(*args, **kwargs):
            raise OSError("gh not found")
        with patch.object(nid, "report", side_effect=boom), redirect_stdout(io.StringIO()), \
                redirect_stderr(io.StringIO()) as err:
            self.assertEqual(nid.main(["rev"]), 1)
        self.assertIn("gh not found", err.getvalue())


if __name__ == "__main__":
    unittest.main()
