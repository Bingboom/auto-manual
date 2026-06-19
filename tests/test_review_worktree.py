#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for git-worktree helpers + the backport template guard."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.review_worktree import (  # noqa: E402
    derive_review_source_rel,
    ensure_review_worktree,
    parse_worktree_for_ref,
    worktree_dirname,
)

REVIEW_DIR = "docs/_review/JE-1000F/EU"


class DeriveSourceRelTests(unittest.TestCase):
    def test_bare_page_name_goes_under_page_dir(self) -> None:
        self.assertEqual(
            derive_review_source_rel(REVIEW_DIR, "00_preface.rst"),
            "docs/_review/JE-1000F/EU/page/00_preface.rst",
        )

    def test_page_prefixed_is_kept(self) -> None:
        self.assertEqual(
            derive_review_source_rel(REVIEW_DIR, "page/00_preface.rst"),
            "docs/_review/JE-1000F/EU/page/00_preface.rst",
        )

    def test_full_review_path_is_accepted(self) -> None:
        full = "docs/_review/JE-1000F/EU/page/00_preface.rst"
        self.assertEqual(derive_review_source_rel(REVIEW_DIR, full), full)

    def test_template_path_is_refused(self) -> None:
        with self.assertRaises(RuntimeError):
            derive_review_source_rel(REVIEW_DIR, "docs/templates/page_eu/00_preface.rst")

    def test_build_path_is_refused(self) -> None:
        with self.assertRaises(RuntimeError):
            derive_review_source_rel(REVIEW_DIR, "docs/_build/JE-1000F/EU/rst/page/00_preface.rst")

    def test_parent_escape_is_refused(self) -> None:
        with self.assertRaises(RuntimeError):
            derive_review_source_rel(REVIEW_DIR, "../templates/00_preface.rst")

    def test_full_path_outside_review_dir_is_refused(self) -> None:
        with self.assertRaises(RuntimeError):
            derive_review_source_rel(REVIEW_DIR, "docs/_review/JE-1000F/US/page/00_preface.rst")

    def test_non_rst_is_refused(self) -> None:
        with self.assertRaises(RuntimeError):
            derive_review_source_rel(REVIEW_DIR, "00_preface.txt")


class WorktreeDirnameTests(unittest.TestCase):
    def test_slashes_become_dashes(self) -> None:
        self.assertEqual(worktree_dirname("codex/review-id-recvfw0zg4pzxs"), "review-codex-review-id-recvfw0zg4pzxs")


class ParseWorktreeTests(unittest.TestCase):
    PORCELAIN = (
        "worktree /repo/main\nHEAD abc\nbranch refs/heads/main\n\n"
        "worktree /wt/review-eu\nHEAD def\nbranch refs/heads/codex/review-id-recvhozfkgg7l0\n"
    )

    def test_finds_path_for_ref(self) -> None:
        self.assertEqual(
            parse_worktree_for_ref(self.PORCELAIN, "codex/review-id-recvhozfkgg7l0"), "/wt/review-eu"
        )

    def test_none_when_ref_absent(self) -> None:
        self.assertIsNone(parse_worktree_for_ref(self.PORCELAIN, "codex/review-id-other"))


class _FakeGit:
    def __init__(self, list_output: str = "") -> None:
        self.calls: list[list[str]] = []
        self.list_output = list_output

    def __call__(self, args: list[str]) -> str:
        self.calls.append(args)
        if args[:2] == ["worktree", "list"]:
            return self.list_output
        return ""


class EnsureWorktreeTests(unittest.TestCase):
    def test_reuses_existing_worktree(self) -> None:
        fake = _FakeGit("worktree /wt/review-eu\nbranch refs/heads/codex/r1\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = ensure_review_worktree("codex/r1", worktrees_root=tmp, run_git=fake)
        self.assertEqual(path, "/wt/review-eu")
        # no fetch / add when it already exists
        self.assertTrue(all(call[:1] != ["fetch"] and call[:2] != ["worktree", "add"] for call in fake.calls))

    def test_creates_when_missing(self) -> None:
        fake = _FakeGit("")  # no existing worktrees
        with tempfile.TemporaryDirectory() as tmp:
            path = ensure_review_worktree("codex/r1", worktrees_root=tmp, run_git=fake)
            self.assertEqual(path, str(Path(tmp) / "review-codex-r1"))
        self.assertIn(["fetch", "origin", "codex/r1"], fake.calls)
        add_calls = [c for c in fake.calls if c[:2] == ["worktree", "add"]]
        self.assertTrue(add_calls)
        self.assertNotIn("--no-checkout", add_calls[0])  # full checkout when no sparse_paths

    def test_creates_sparse_when_paths_given(self) -> None:
        fake = _FakeGit("")
        with tempfile.TemporaryDirectory() as tmp:
            ensure_review_worktree(
                "codex/r1", worktrees_root=tmp, run_git=fake, sparse_paths=["docs/_review/JE-1000F/EU"]
            )
        sparse_calls = [c for c in fake.calls if "sparse-checkout" in c]
        self.assertTrue(sparse_calls)
        self.assertIn("--cone", sparse_calls[0])
        self.assertIn("docs/_review/JE-1000F/EU", sparse_calls[0])


if __name__ == "__main__":
    unittest.main()
