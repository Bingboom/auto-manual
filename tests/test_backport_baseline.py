#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the cloud-doc backport render baseline store (approach C)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.backport_baseline import (  # noqa: E402
    baseline_rel_path,
    load_baseline,
    safe_doc_token,
    store_baseline,
)

REVIEW_DIR = "docs/_review/JE-1000F/EU"
TOKEN = "Yp4ww6196iPMa6kIqI3cinEonNd"


class SafeTokenTests(unittest.TestCase):
    def test_keeps_alnum_dash_underscore(self) -> None:
        self.assertEqual(safe_doc_token(TOKEN), TOKEN)

    def test_replaces_unsafe_and_truncates(self) -> None:
        self.assertEqual(safe_doc_token("a/b c.d"), "a-b-c-d")
        self.assertEqual(len(safe_doc_token("x" * 200)), 64)

    def test_empty_falls_back(self) -> None:
        self.assertEqual(safe_doc_token(""), "doc")
        self.assertEqual(safe_doc_token("///"), "doc")


class BaselinePathTests(unittest.TestCase):
    def test_path_under_backport_dir(self) -> None:
        self.assertEqual(
            baseline_rel_path(REVIEW_DIR, TOKEN),
            f"docs/_review/JE-1000F/EU/.backport/{TOKEN}.baseline.md",
        )

    def test_requires_review_dir(self) -> None:
        with self.assertRaises(ValueError):
            baseline_rel_path("", TOKEN)


class StoreLoadTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rel = store_baseline(tmp, REVIEW_DIR, TOKEN, "rendered preface text")
            self.assertEqual(rel, f"docs/_review/JE-1000F/EU/.backport/{TOKEN}.baseline.md")
            self.assertTrue((Path(tmp) / rel).is_file())
            self.assertEqual(load_baseline(tmp, REVIEW_DIR, TOKEN), "rendered preface text\n")

    def test_load_missing_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(load_baseline(tmp, REVIEW_DIR, TOKEN))

    def test_store_appends_trailing_newline_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store_baseline(tmp, REVIEW_DIR, TOKEN, "already has newline\n")
            self.assertEqual(load_baseline(tmp, REVIEW_DIR, TOKEN), "already has newline\n")


if __name__ == "__main__":
    unittest.main()
