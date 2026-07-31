import unittest
from unittest.mock import patch

from tools.check_review_branch_sync import (
    build_report,
    build_structured_ledger,
    region_of,
    scope_hits,
    token_matches_region,
)
from tools.review_propagation_ledger import (
    MERGE_PARAMS_SAFE,
    NEEDS_HUMAN,
    ReviewBranchSnapshot,
    classify_merge_params_change,
    source_affects_review_branch,
)


class ScopeHitsTests(unittest.TestCase):
    def test_lang_tokened_paths(self):
        hits = scope_hits(
            [
                "docs/templates/page_jp/06_ups_mode.rst",
                "docs/manifests/manual_jp.yaml",
                "docs/templates/recipes/jp/03_product_overview.yaml",
                "docs/templates/page_us-en/01_fcc.rst",
            ]
        )
        self.assertEqual(sorted(hits), ["jp", "us-en"])
        self.assertIn("docs/manifests/manual_jp.yaml", hits["jp"])
        self.assertIn("docs/templates/recipes/jp/03_product_overview.yaml", hits["jp"])

    def test_region_agnostic_templates_scope_star(self):
        hits = scope_hits(
            [
                "docs/templates/page_shared/foo.rst",
                "docs/templates/snippets/bar.rst",
                "docs/templates/word_template/common_assets/x.svg",
                "docs/templates/contracts/spec.yaml",
                "docs/templates/cover_template.rst",
            ]
        )
        self.assertEqual(list(hits), ["*"])
        self.assertEqual(len(hits["*"]), 5)

    def test_mixed_scopes(self):
        hits = scope_hits(["docs/templates/page_jp/x.rst", "docs/templates/snippets/y.rst"])
        self.assertEqual(sorted(hits), ["*", "jp"])

    def test_ignores_unrelated_paths(self):
        self.assertEqual(
            scope_hits(
                [
                    "tools/x.py",
                    "docs/_build/a.rst",
                    "docs/_review/JE-900B/JP/page/charging.rst",
                    "docs/manifests/notes.txt",
                    "README.md",
                ]
            ),
            {},
        )


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

    def test_region_agnostic_flags_all_branches(self):
        hits = {"*": ["docs/templates/snippets/bar.rst"]}
        branches = ["review/JE-900B-JP", "review/JE-1000F-US", "review/JE-2000F-CN"]
        msg, affected = build_report(hits, branches)
        self.assertTrue(affected)
        self.assertIn("ALL (region-agnostic)", msg)
        for branch in branches:
            line = next(ln for ln in msg.splitlines() if branch in ln)
            self.assertIn("likely affected", line)

    def test_advisory_language_present(self):
        msg, _ = build_report({"jp": ["docs/manifests/manual_jp.yaml"]}, [])
        self.assertIn("sync-review", msg)
        self.assertIn("PLACEHOLDER", msg)
        self.assertIn("refresh-review", msg)


class MergeParamsSafetyTests(unittest.TestCase):
    def test_placeholder_only_change_is_safe_when_review_line_keeps_old_skeleton(self):
        result = classify_merge_params_change(
            old_template="Power: |POWER| W\n",
            new_template="Rated power: |POWER| W\n",
            review_text="Power: 1500 W\n",
        )

        self.assertEqual(result.classification, MERGE_PARAMS_SAFE)
        self.assertEqual(result.reason_code, "placeholder_lines_unedited")

    def test_authored_edit_on_placeholder_line_requires_human(self):
        result = classify_merge_params_change(
            old_template="Power: |POWER| W\n",
            new_template="Rated power: |POWER| W\n",
            review_text="Reviewer wording: 1500 W\n",
        )

        self.assertEqual(result.classification, NEEDS_HUMAN)
        self.assertEqual(result.reason_code, "authored_placeholder_line")

    def test_non_placeholder_change_requires_human(self):
        result = classify_merge_params_change(
            old_template="Heading\nPower: |POWER| W\n",
            new_template="New heading\nPower: |POWER| W\n",
            review_text="Heading\nPower: 1500 W\n",
        )

        self.assertEqual(result.classification, NEEDS_HUMAN)
        self.assertEqual(result.reason_code, "non_parameter_change")


class StructuredLedgerTests(unittest.TestCase):
    def test_manifest_reference_excludes_unrelated_shared_language(self):
        snapshot = ReviewBranchSnapshot(
            branch="review/JE-1000F-JP",
            region="JP",
            seed_git_sha="seed-sha",
            page_manifest="docs/manifests/manual_jp.yaml",
        )
        reads = {
            ("seed-sha", "docs/manifests/manual_jp.yaml"):
                "pages:\n  - file: templates/page_jp/06_ups_mode.rst\n",
            ("HEAD", "docs/manifests/manual_jp.yaml"):
                "pages:\n  - file: templates/page_jp/06_ups_mode.rst\n",
        }
        with patch(
            "tools.review_propagation_ledger.git_text",
            side_effect=lambda ref, path, _cwd: reads.get((ref, path)),
        ):
            affected = source_affects_review_branch(
                source_path="docs/templates/page_shared/en/06_ups_mode.rst",
                scope_matches=True,
                snapshot=snapshot,
                cwd=None,
            )

        self.assertFalse(affected)

    def test_json_rows_use_manifest_metadata_instead_of_legacy_branch_name(self):
        snapshot = ReviewBranchSnapshot(
            branch="review/id-record-123",
            branch_head="branch-head",
            manifest_path="docs/_review/JE-1000F/US/manifest.json",
            model="JE-1000F",
            region="US",
            lang=None,
            seed_git_sha="seed-sha",
            page_manifest="docs/manifests/manual_us.yaml",
            page_files=("docs/_review/JE-1000F/US/page/03_product_overview_placeholder.rst",),
        )
        reads = {
            ("seed-sha", "docs/manifests/manual_us.yaml"):
                "pages:\n  - template: templates/page_us-en/03_product_overview_placeholder.rst\n",
            ("HEAD", "docs/manifests/manual_us.yaml"):
                "pages:\n  - template: templates/page_us-en/03_product_overview_placeholder.rst\n",
            ("seed-sha", "docs/templates/page_us-en/03_product_overview_placeholder.rst"):
                "Power: |POWER| W\n",
            ("HEAD", "docs/templates/page_us-en/03_product_overview_placeholder.rst"):
                "Rated power: |POWER| W\n",
            (
                "origin/review/id-record-123",
                "docs/_review/JE-1000F/US/page/03_product_overview_placeholder.rst",
            ): "Power: 1500 W\n",
        }

        with (
            patch(
                "tools.check_review_branch_sync.inspect_review_branch",
                return_value=snapshot,
            ),
            patch(
                "tools.review_propagation_ledger.git_text",
                side_effect=lambda ref, path, _cwd: reads.get((ref, path)),
            ),
            patch(
                "tools.check_review_branch_sync.git_sha",
                return_value="head-sha",
            ),
        ):
            payload = build_structured_ledger(
                {"us-en": ["docs/templates/page_us-en/03_product_overview_placeholder.rst"]},
                ["review/id-record-123"],
                remote="origin",
                cwd=None,
            )

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["summary"]["merge_params_safe"], 1)
        self.assertEqual(len(payload["rows"]), 1)
        row = payload["rows"][0]
        self.assertEqual(row["review_branch"], "review/id-record-123")
        self.assertEqual(row["model"], "JE-1000F")
        self.assertEqual(row["region"], "US")
        self.assertEqual(row["classification"], MERGE_PARAMS_SAFE)
        self.assertEqual(
            row["review_paths"],
            ["docs/_review/JE-1000F/US/page/03_product_overview_placeholder.rst"],
        )

    def test_unresolved_branch_is_retained_as_needs_human(self):
        snapshot = ReviewBranchSnapshot(
            branch="review/id-unresolved",
            error="review_manifest_missing",
        )
        with (
            patch(
                "tools.check_review_branch_sync.inspect_review_branch",
                return_value=snapshot,
            ),
            patch("tools.check_review_branch_sync.git_sha", return_value="head-sha"),
        ):
            payload = build_structured_ledger(
                {"*": ["docs/templates/snippets/shared.rst"]},
                ["review/id-unresolved"],
                remote="origin",
                cwd=None,
            )

        self.assertEqual(len(payload["rows"]), 1)
        self.assertIsNone(payload["rows"][0]["affected"])
        self.assertEqual(payload["rows"][0]["classification"], NEEDS_HUMAN)
        self.assertEqual(payload["rows"][0]["reason_code"], "review_manifest_missing")
        self.assertEqual(payload["summary"]["unresolved"], 1)


if __name__ == "__main__":
    unittest.main()
