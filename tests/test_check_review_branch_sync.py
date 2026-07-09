import unittest

from tools.check_review_branch_sync import (
    build_report,
    region_of,
    scope_hits,
    token_matches_region,
)


class ScopeHitsTests(unittest.TestCase):
    def test_matches_templates_and_manifests(self):
        hits = scope_hits(
            [
                "docs/templates/page_jp/06_ups_mode.rst",
                "docs/templates/page_jp/01_meaning_of_symbols.rst",
                "docs/manifests/manual_jp.yaml",
                "docs/templates/page_us/safety_en.rst",
                "tools/build_docs.py",
                "docs/_review/JE-900B/JP/page/charging.rst",
            ]
        )
        self.assertEqual(sorted(hits), ["jp", "us"])
        self.assertIn("docs/manifests/manual_jp.yaml", hits["jp"])
        self.assertEqual(hits["us"], ["docs/templates/page_us/safety_en.rst"])

    def test_ignores_unrelated_paths(self):
        self.assertEqual(scope_hits(["tools/x.py", "docs/_build/a.rst", "README.md"]), {})


class RegionTests(unittest.TestCase):
    def test_region_of(self):
        self.assertEqual(region_of("review/JE-1000F-JP"), "JP")
        self.assertEqual(region_of("review/JE-900B-JP"), "JP")
        self.assertEqual(region_of("review/JE-1000F-AU"), "AU")
        self.assertIsNone(region_of("feat/whatever"))

    def test_token_matches_region(self):
        self.assertTrue(token_matches_region("jp", "JP"))
        self.assertTrue(token_matches_region("us", "US"))
        self.assertTrue(token_matches_region("au-en", "AU"))
        self.assertFalse(token_matches_region("jp", "US"))
        self.assertFalse(token_matches_region("jp", None))


class BuildReportTests(unittest.TestCase):
    def test_flags_affected_branch(self):
        hits = {"jp": ["docs/manifests/manual_jp.yaml"]}
        branches = ["review/JE-900B-JP", "review/JE-1000F-US"]
        msg, affected = build_report(hits, branches)
        self.assertTrue(affected)
        self.assertIn("review/JE-900B-JP", msg)
        self.assertIn("likely affected", msg)
        # the US branch is listed but not flagged as affected by a JP change
        jp_line = next(line for line in msg.splitlines() if "review/JE-900B-JP" in line)
        us_line = next(line for line in msg.splitlines() if "review/JE-1000F-US" in line)
        self.assertIn("likely affected", jp_line)
        self.assertNotIn("likely affected", us_line)

    def test_no_branches_no_affected(self):
        msg, affected = build_report({"jp": ["docs/templates/page_jp/x.rst"]}, [])
        self.assertFalse(affected)
        self.assertIn("none found", msg)

    def test_remote_unreachable(self):
        msg, affected = build_report({"jp": ["docs/templates/page_jp/x.rst"]}, None)
        self.assertFalse(affected)
        self.assertIn("remote unreachable", msg)

    def test_advisory_language_present(self):
        msg, _ = build_report({"jp": ["docs/manifests/manual_jp.yaml"]}, [])
        self.assertIn("sync-review", msg)
        self.assertIn("PLACEHOLDER", msg)
        self.assertIn("refresh-review", msg)


if __name__ == "__main__":
    unittest.main()
