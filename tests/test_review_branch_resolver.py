#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the cloud-doc -> review-branch resolver (文档构建表 lookup)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.review_branch_resolver import (  # noqa: E402
    doc_token,
    match_review_branch,
    parse_document_id,
)


def _rec(cloud: str, git_ref: str, document_id: str, status: str = "InReview", pr: str = "") -> dict:
    return {
        "record_id": "rec" + document_id,
        "fields": {
            "飞书云文档": cloud,
            "Git_ref": git_ref,
            "Document_ID": document_id,
            "Review_status": status,
            "PR_url": pr,
        },
    }


# A real build-table value is a markdown-wrapped /docx/ URL.
US_DOC = "[https://test-degwga5x6ex8.feishu.cn/docx/TVWodb25Co2mQGxN4YacegWvnQb](https://test-degwga5x6ex8.feishu.cn/docx/TVWodb25Co2mQGxN4YacegWvnQb)"
US_URL = "https://test-degwga5x6ex8.feishu.cn/docx/TVWodb25Co2mQGxN4YacegWvnQb"


class DocTokenTests(unittest.TestCase):
    def test_extracts_docx_wiki_and_markdown(self) -> None:
        self.assertEqual(doc_token("https://x.feishu.cn/docx/ABC123"), "ABC123")
        self.assertEqual(doc_token("https://x.feishu.cn/wiki/ABC123?table=t"), "ABC123")
        self.assertEqual(doc_token(US_DOC), "TVWodb25Co2mQGxN4YacegWvnQb")
        self.assertEqual(doc_token("no token here"), "")


class ParseDocumentIdTests(unittest.TestCase):
    def test_parses_model_region_version(self) -> None:
        self.assertEqual(parse_document_id("JE-1000F_US_1.4"), ("JE-1000F", "US", "1.4"))

    def test_region_keeps_internal_dash(self) -> None:
        self.assertEqual(parse_document_id("JE-1000F_pt-BR_1.4"), ("JE-1000F", "pt-BR", "1.4"))

    def test_language_segment_is_not_part_of_region(self) -> None:
        # JE-1000F_EU_en_0.8: region is EU (the _review tree stops at the region);
        # the language segment (en) must NOT leak into the region (was "EU_en" bug).
        self.assertEqual(parse_document_id("JE-1000F_EU_en_0.8"), ("JE-1000F", "EU", "0.8"))

    def test_too_short_is_none(self) -> None:
        self.assertIsNone(parse_document_id("JE-1000F"))
        self.assertIsNone(parse_document_id(""))


class MatchReviewBranchTests(unittest.TestCase):
    def test_matches_by_docx_token(self) -> None:
        records = [
            _rec("https://x.feishu.cn/docx/OTHER", "codex/review-id-other", "JE-2000F_EU_0.1"),
            _rec(US_DOC, "codex/review-id-recvfw0zg4pzxs", "JE-1000F_US_1.4", pr="pr106"),
        ]
        result = match_review_branch(US_URL, records)
        assert result is not None
        self.assertEqual(result["git_ref"], "codex/review-id-recvfw0zg4pzxs")
        self.assertEqual(result["model"], "JE-1000F")
        self.assertEqual(result["region"], "US")
        self.assertEqual(result["review_dir"], "docs/_review/JE-1000F/US")
        self.assertEqual(result["pr_url"], "pr106")

    def test_no_match_returns_none(self) -> None:
        records = [_rec("https://x.feishu.cn/docx/OTHER", "codex/review-id-other", "JE-2000F_EU_0.1")]
        self.assertIsNone(match_review_branch(US_URL, records))

    def test_blank_url_returns_none(self) -> None:
        self.assertIsNone(match_review_branch("", [_rec(US_DOC, "ref", "JE-1000F_US_1.4")]))

    def test_prefers_in_review_over_other_status(self) -> None:
        records = [
            _rec(US_DOC, "codex/old", "JE-1000F_US_1.2", status="merged"),
            _rec(US_DOC, "codex/active", "JE-1000F_US_1.4", status="InReview"),
        ]
        result = match_review_branch(US_URL, records)
        assert result is not None
        self.assertEqual(result["git_ref"], "codex/active")

    def test_same_ref_across_versions_is_not_ambiguous(self) -> None:
        records = [
            _rec(US_DOC, "codex/same", "JE-1000F_US_1.3", status="InReview"),
            _rec(US_DOC, "codex/same", "JE-1000F_US_1.4", status="InReview"),
        ]
        result = match_review_branch(US_URL, records)
        assert result is not None
        self.assertEqual(result["git_ref"], "codex/same")

    def test_distinct_refs_is_ambiguous(self) -> None:
        records = [
            _rec(US_DOC, "codex/one", "JE-1000F_US_1.3", status="InReview"),
            _rec(US_DOC, "codex/two", "JE-1000F_US_1.4", status="InReview"),
        ]
        with self.assertRaises(RuntimeError):
            match_review_branch(US_URL, records)

    def test_record_without_git_ref_is_ignored(self) -> None:
        records = [_rec(US_DOC, "", "JE-1000F_US_1.4")]
        self.assertIsNone(match_review_branch(US_URL, records))


if __name__ == "__main__":
    unittest.main()
