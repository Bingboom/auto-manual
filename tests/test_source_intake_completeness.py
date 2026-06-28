#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the spec-sheet intake completeness gate."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.source_intake_completeness import (  # noqa: E402
    IDENTITY_FIELDS, check_completeness, logical_key,
)


def _row(rk, sec="GENERAL INFO", slot="", line=1, label="L", value="V"):
    return {"Row_key": rk, "Section": sec, "Slot_key": slot, "Line_order": line, "label": label,
            "value": value, "document_key": "JE-2000E_JP", "Source_lang": "ja", "Page": "specifications"}


class CompletenessTests(unittest.TestCase):
    def test_passes_when_candidates_cover_reference(self):
        ref = [_row("capacity"), _row("weight")]
        cand = [_row("capacity"), _row("weight")]
        rep = check_completeness(cand, ref)
        self.assertTrue(rep.passed)
        self.assertIn("✅", rep.summary())

    def test_missing_row_detected(self):
        ref = [_row("capacity"), _row("weight"), _row("dc_expansion_port", sec="INPUT PORTS")]
        cand = [_row("capacity"), _row("weight")]
        rep = check_completeness(cand, ref)
        self.assertFalse(rep.passed)
        self.assertIn(("dc_expansion_port", "", "INPUT PORTS", "1"), rep.missing_rows)

    def test_section_distinguishes_same_rowkey(self):
        # dc_expansion_port appears in both INPUT and OUTPUT -> two distinct logical rows
        ref = [_row("dc_expansion_port", sec="INPUT PORTS"), _row("dc_expansion_port", sec="OUTPUT PORTS")]
        cand = [_row("dc_expansion_port", sec="INPUT PORTS")]   # OUTPUT missing
        rep = check_completeness(cand, ref)
        self.assertEqual(rep.missing_rows, [("dc_expansion_port", "", "OUTPUT PORTS", "1")])

    def test_field_gap_detected(self):
        ref = [_row("capacity")]
        bad = _row("capacity"); bad["Source_lang"] = ""    # missing identity field
        rep = check_completeness([bad], ref)
        self.assertFalse(rep.passed)
        self.assertEqual(rep.field_gaps[0][1], ["Source_lang"])

    def test_value_optional_unless_required(self):
        ref = [_row("capacity")]
        pending = _row("capacity"); pending["value"] = ""   # value not yet filled
        # identity-only check passes (row exists); value not required by default
        self.assertTrue(check_completeness([pending], ref).passed)
        # but requiring value flags it
        rep = check_completeness([pending], ref, required_fields=IDENTITY_FIELDS + ("value",))
        self.assertFalse(rep.passed)

    def test_extra_row_flagged(self):
        ref = [_row("capacity")]
        cand = [_row("capacity"), _row("mystery")]
        rep = check_completeness(cand, ref)
        self.assertIn(("mystery", "", "GENERAL INFO", "1"), rep.extra_rows)

    def test_logical_key_normalizes_line(self):
        self.assertEqual(logical_key({"Row_key": "x", "Line_order": "2.0", "Section": "S"}),
                         ("x", "", "S", "2"))


if __name__ == "__main__":
    unittest.main()
