#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The scaffold's contract: mechanical fields reproduced, judgment left visible.

The round-trip against the committed JBP-2000B_US plan is the honest measure of
what the scaffold saves — everything it emits must MATCH the hand-written plan,
and everything it cannot emit must surface as a named TODO rather than a guess.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from test_idml_target_assembly_plan import _manual_ir, _payload  # noqa: E402

from tools.idml.target_assembly_scaffold import (  # noqa: E402
    JUDGMENT_HINTS,
    ROLE_COMPOSITION,
    main,
    scaffold_plan,
)
from tools.idml.target_assembly_plan import (  # noqa: E402
    normalize_target_assembly_plan,
)

MECHANICAL_FIELDS = (
    "source_ref",
    "language",
    "page_role",
    "composition_id",
    "composition_type",
    "start_page",
    "page_count",
)


class ScaffoldRoundTripTests(unittest.TestCase):
    """Scaffold the committed plan's own page list and diff the two."""

    def setUp(self) -> None:
        self.committed = _payload()
        self.ir = _manual_ir(self.committed)
        self.draft, self.todos = scaffold_plan(
            self.ir,
            physical_pages=self.committed["physical_page_count"],
        )

    def test_every_mechanical_field_matches_the_hand_written_plan(self) -> None:
        self.assertEqual(len(self.committed["pages"]), len(self.draft["pages"]))
        for hand, drafted in zip(
            self.committed["pages"], self.draft["pages"], strict=True,
        ):
            for field in MECHANICAL_FIELDS:
                with self.subTest(page=hand["source_ref"], field=field):
                    self.assertEqual(hand[field], drafted[field])

    def test_judgment_fields_are_never_invented(self) -> None:
        """The scaffold must not guess composition_data or flow_split values."""
        for drafted in self.draft["pages"]:
            self.assertNotIn("composition_data", drafted)
            self.assertNotIn("flow_split", drafted)

    def test_every_judgment_the_plan_made_is_named_in_the_todos(self) -> None:
        """Each composition type that carries hand judgment in the committed
        plan must appear in the sidecar todo list — the diff IS the judgment."""
        judged_types = {
            page["composition_type"]
            for page in self.committed["pages"]
            if "composition_data" in page or "flow_split" in page
        }
        todo_text = "\n".join(self.todos)
        for ctype in sorted(judged_types):
            with self.subTest(composition_type=ctype):
                self.assertIn(ctype, JUDGMENT_HINTS)
                self.assertIn(f"[{ctype}]", todo_text)

    def test_the_draft_normalizes_as_is(self) -> None:
        """Judgment fields are additive: the bare skeleton must load."""
        plan = normalize_target_assembly_plan(
            self.draft,
            self.ir,
            source_path=Path("scaffold-draft.json"),
        )
        self.assertEqual(
            self.committed["physical_page_count"],
            plan["composition_count"],
        )

    def test_header_never_claims_approval(self) -> None:
        self.assertEqual("candidate", self.draft["status"])
        self.assertIs(False, self.draft["production_eligible"])
        self.assertEqual(self.committed["target"], self.draft["target"])


class ScaffoldGuardTests(unittest.TestCase):
    def test_an_unmapped_role_becomes_a_blocking_todo_not_a_guess(self) -> None:
        committed = _payload()
        ir = _manual_ir(committed)
        # Re-point one page at a role outside the mapping (app_setup is a JE
        # host page role no compact plan has packed yet).
        pages = list(ir.pages)
        victim = pages[5]
        renamed = type(victim)(
            page_id=victim.page_id,
            source_ref="page/12_app_setup_placeholder.rst",
            source_path=victim.source_path,
            language=victim.language,
            source_sha256=victim.source_sha256,
            skipped_raw=victim.skipped_raw,
            blocks=victim.blocks,
        )
        pages[5] = renamed
        ir = type(ir)(**{**ir.to_dict(), "pages": tuple(pages)})

        draft, todos = scaffold_plan(ir, physical_pages=28)

        drafted = draft["pages"][5]
        self.assertTrue(drafted["composition_type"].startswith("TODO_"))
        self.assertTrue(any("没有脚手架映射" in item for item in todos))

    def test_role_mapping_stays_inside_the_validators_vocabulary(self) -> None:
        """Every scaffolded composition type must be one the renderer or the
        story flow can dispatch — the mapping must not invent vocabulary."""
        from tools.idml.target_assembly_render import SPECIAL_COMPOSITION_TYPES

        story_flow_types = {
            "front_cover", "preface", "toc", "warranty", "back_cover",
        }
        allowed = set(SPECIAL_COMPOSITION_TYPES) | story_flow_types
        for role, ctype in ROLE_COMPOSITION.items():
            with self.subTest(role=role.value):
                self.assertIn(ctype, allowed)

    def test_cli_writes_draft_and_sidecar_and_refuses_overwrite(self) -> None:
        committed = _payload()
        ir = _manual_ir(committed)
        with tempfile.TemporaryDirectory() as tmp:
            ir_path = Path(tmp) / "manual.ir.json"
            ir_path.write_text(
                json.dumps(ir.to_dict(), ensure_ascii=False), encoding="utf-8",
            )
            out = Path(tmp) / "draft_v1_candidate.json"
            rc = main([
                "--ir", str(ir_path),
                "--physical-pages", str(committed["physical_page_count"]),
                "--out", str(out),
            ])
            self.assertEqual(0, rc)
            self.assertTrue(out.exists())
            sidecar = out.with_suffix(".todos.md")
            self.assertTrue(sidecar.exists())
            self.assertIn("reference_pdf", sidecar.read_text(encoding="utf-8"))
            with self.assertRaises(SystemExit):
                main([
                    "--ir", str(ir_path),
                    "--physical-pages", "28",
                    "--out", str(out),
                ])


if __name__ == "__main__":
    unittest.main()
