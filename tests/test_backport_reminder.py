from __future__ import annotations

import unittest

from tools import backport_reminder


def _record(
    *,
    status: str = "InReview",
    cloud_doc: str = "https://example.feishu.cn/docx/TOKEN123abc",
    git_ref: str = "review/JE-1000F-US",
    document_id: str = "JE-1000F_US_0.3",
) -> dict:
    return {
        "record_id": "rec1",
        "fields": {
            "Review_status": status,
            "飞书云文档": cloud_doc,
            "Git_ref": git_ref,
            "Document_ID": document_id,
        },
    }


class TestInReviewDocs(unittest.TestCase):
    def test_in_review_row_with_doc_is_listed(self) -> None:
        docs = backport_reminder.in_review_docs([_record()])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["git_ref"], "review/JE-1000F-US")
        self.assertEqual(docs[0]["review_dir"], "docs/_review/JE-1000F/US")

    def test_non_in_review_and_docless_rows_are_skipped(self) -> None:
        rows = [
            _record(status="Done"),
            _record(cloud_doc=""),
            _record(git_ref=""),
            _record(document_id="not-parsable"),
        ]
        self.assertEqual(backport_reminder.in_review_docs(rows), [])

    def test_duplicate_branch_doc_pairs_deduped(self) -> None:
        docs = backport_reminder.in_review_docs([_record(), _record()])
        self.assertEqual(len(docs), 1)


class TestCheckDocs(unittest.TestCase):
    def _doc(self) -> dict:
        return backport_reminder.in_review_docs([_record()])[0]

    def test_missing_baseline_needs_attention(self) -> None:
        report = backport_reminder.check_docs(
            [self._doc()],
            fetch=lambda url, lark_cli: "whatever",
            baseline_reader=lambda ref, path, remote, repo_root: None,
        )
        self.assertEqual(report["by_status"], {backport_reminder.NO_BASELINE: 1})
        self.assertFalse(report["ok"])

    def test_doc_equal_to_baseline_is_synced(self) -> None:
        text = "# Title\n\nCharge the battery fully.\n"
        report = backport_reminder.check_docs(
            [self._doc()],
            fetch=lambda url, lark_cli: text,
            baseline_reader=lambda ref, path, remote, repo_root: text,
        )
        self.assertEqual(report["by_status"], {backport_reminder.SYNCED: 1})
        self.assertTrue(report["ok"])

    def test_doc_differing_from_baseline_is_pending(self) -> None:
        report = backport_reminder.check_docs(
            [self._doc()],
            fetch=lambda url, lark_cli: "# Title\n\nReviewer changed this sentence.\n",
            baseline_reader=lambda ref, path, remote, repo_root: "# Title\n\nOld text.\n",
        )
        self.assertEqual(report["by_status"], {backport_reminder.PENDING: 1})
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["needs_attention"]), 1)

    def test_whitespace_only_difference_is_synced(self) -> None:
        report = backport_reminder.check_docs(
            [self._doc()],
            fetch=lambda url, lark_cli: "# Title\n\nCharge   the battery.\n",
            baseline_reader=lambda ref, path, remote, repo_root: "# Title\n\nCharge the battery.\n",
        )
        self.assertEqual(report["by_status"], {backport_reminder.SYNCED: 1})

    def test_fetch_failure_is_reported_not_raised(self) -> None:
        def boom(url: str, lark_cli: str) -> str:
            raise RuntimeError("lark unreachable")

        report = backport_reminder.check_docs(
            [self._doc()],
            fetch=boom,
            baseline_reader=lambda ref, path, remote, repo_root: "baseline",
        )
        self.assertEqual(report["by_status"], {backport_reminder.ERROR: 1})
        self.assertFalse(report["ok"])

    def test_baseline_path_uses_review_dir_and_token(self) -> None:
        report = backport_reminder.check_docs(
            [self._doc()],
            fetch=lambda url, lark_cli: "x",
            baseline_reader=lambda ref, path, remote, repo_root: "x",
        )
        self.assertIn(
            "docs/_review/JE-1000F/US/.backport/", report["results"][0]["baseline_path"]
        )


if __name__ == "__main__":
    unittest.main()
