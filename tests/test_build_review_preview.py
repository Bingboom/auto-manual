from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "process_docs" / "build_review_preview.py"
MODULE_SPEC = importlib.util.spec_from_file_location("build_review_preview_test_module", MODULE_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
build_review_preview = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(build_review_preview)


class TestBuildReviewPreview(unittest.TestCase):
    def test_git_value_should_prefer_github_env_fallbacks(self) -> None:
        with mock.patch.dict(
            build_review_preview.os.environ,
            {"GITHUB_HEAD_REF": "feature/review-preview"},
            clear=True,
        ):
            with mock.patch.object(build_review_preview, "capture", return_value="fallback") as capture_mock:
                value = build_review_preview.git_value(
                    ["VERCEL_GIT_COMMIT_REF", "GITHUB_HEAD_REF", "GITHUB_REF_NAME"],
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                )

        self.assertEqual("feature/review-preview", value)
        capture_mock.assert_not_called()

    def test_git_value_should_fall_back_to_git_when_env_is_empty(self) -> None:
        with mock.patch.dict(build_review_preview.os.environ, {}, clear=True):
            with mock.patch.object(build_review_preview, "capture", return_value="main") as capture_mock:
                value = build_review_preview.git_value(
                    ["VERCEL_GIT_COMMIT_REF", "GITHUB_HEAD_REF", "GITHUB_REF_NAME"],
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                )

        self.assertEqual("main", value)
        capture_mock.assert_called_once()

    def test_github_pull_request_id_should_prefer_explicit_env_value(self) -> None:
        with mock.patch.dict(
            build_review_preview.os.environ,
            {
                "VERCEL_GIT_PULL_REQUEST_ID": "91",
                "GITHUB_REF": "refs/pull/44/merge",
            },
            clear=True,
        ):
            value = build_review_preview.github_pull_request_id()

        self.assertEqual("91", value)

    def test_github_pull_request_id_should_parse_github_ref(self) -> None:
        with mock.patch.dict(
            build_review_preview.os.environ,
            {"GITHUB_REF": "refs/pull/44/merge"},
            clear=True,
        ):
            value = build_review_preview.github_pull_request_id()

        self.assertEqual("44", value)


if __name__ == "__main__":
    unittest.main()
