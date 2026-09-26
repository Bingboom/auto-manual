from __future__ import annotations

import io
import json
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


class FakeRun:
    """``run(args)`` for git and gh, answering from in-memory fixtures."""

    def __init__(self, *, main: str, prs: dict[int, tuple[list[str], str]]):
        self.main = main
        self.prs = prs
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> str:
        self.calls.append(args)
        if args[:1] == ["git"] and "show" in args:
            return self.main
        if args[:1] == ["git"]:
            return ""
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

    def test_rev_numbers_come_from_the_ledger(self):
        run = FakeRun(main=LEDGER, prs={9: ([nid.TABLES["rev"].path],
                                            diff('| <a id="rev-46"></a>REV-46 | x | — | x | planned | a |'))})
        nxt, why = nid.report("rev", run=run, root=self.root, fetch=False)
        self.assertEqual((nxt, why), ("REV-47", "main has up to REV-45; open PRs reserve REV-46 (#9)"))


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
