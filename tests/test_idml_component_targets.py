from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.idml.component_targets import resolve_component_target
from tools.idml.reference_layout_plan import ReferenceLayoutPlanError
from tools.manual_ir import build_manual_ir


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "tests" / "fixtures" / "idml_bundle"
DATA = ROOT / "tests" / "fixtures" / "phase2"
PLAN_REF = "docs/renderers/contracts/reference_layout/plan.json"
TARGET = {"model": "JE-1000F", "region": "US", "languages": ["en", "fr", "es"]}
DECLARATION = {"language": "en", "status": "pilot", "evidence": "native review"}


class ComponentTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ir = build_manual_ir(
            root=ROOT, bundle_root=BUNDLE, model="JE-1000F", region="US",
            lang="en", source="test", data_root=DATA)

    def _root(
        self,
        tmp: str,
        *,
        entry: dict | None = None,
        pages: list[dict] | None = None,
        extra_entries: tuple[dict, ...] = (),
        plan_changes: dict | None = None,
    ) -> Path:
        root = Path(tmp)
        plan_path = root / PLAN_REF
        plan_path.parent.mkdir(parents=True)
        plan = {
            "schema_version": "approved-reference-layout-plan/v2",
            "target": TARGET,
            "approval": {"status": "approved"},
            "pages": pages if pages is not None else [
                {
                    "source_ref": page.source_ref,
                    "source_sha256": page.source_sha256,
                    "language": page.language,
                }
                for page in self.ir.pages
            ],
        }
        plan.update(plan_changes or {})
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        registered = entry if entry is not None else {
            "target": TARGET,
            "path": PLAN_REF,
            "component_targets": [DECLARATION],
        }
        (root / "docs/renderers/contracts/reference_layout_registry.json").write_text(
            json.dumps({
                "schema_version": "approved-reference-layout-registry/v1",
                "plans": [registered, *extra_entries],
            }),
            encoding="utf-8",
        )
        return root

    def test_every_pinned_source_activates_the_declared_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = resolve_component_target(
                self.ir, root=self._root(tmp), language="en")
        assert target is not None
        self.assertTrue(target.active)
        self.assertEqual("JE-1000F/US/en", target.label)
        self.assertEqual("pilot", target.status)
        self.assertEqual(
            {page.source_ref for page in self.ir.pages}, target.built_sources,
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            target.report()
        self.assertIn(
            f"COMPONENT TARGET OK (pilot): JE-1000F/US/en | "
            f"pinned={len(self.ir.pages)}/{len(self.ir.pages)} by {PLAN_REF}",
            out.getvalue(),
        )

    def test_content_drift_is_inert_and_names_both_digests(self) -> None:
        drifted = self.ir.pages[3]
        pages = [
            {
                "source_ref": page.source_ref,
                "source_sha256": "0" * 64 if page is drifted else page.source_sha256,
                "language": page.language,
            }
            for page in self.ir.pages
            if page is not self.ir.pages[-1]
        ]
        with tempfile.TemporaryDirectory() as tmp:
            target = resolve_component_target(
                self.ir, root=self._root(tmp, pages=pages), language="en")
        assert target is not None
        self.assertFalse(target.active)
        self.assertEqual(
            (
                f"{drifted.source_ref}: source_sha256 does not match "
                f"(pinned=000000000000, built={drifted.source_sha256[:12]})",
                f"{self.ir.pages[-1].source_ref}: not pinned by {PLAN_REF}",
            ),
            target.issues,
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            target.report()
        lines = out.getvalue().splitlines()
        self.assertEqual(
            "[export-idml] WARNING: COMPONENT TARGET INERT (pilot): "
            "JE-1000F/US/en keeps the ordinary layout; 2 issue(s)",
            lines[0],
        )
        self.assertEqual(3, len(lines))

    def test_the_checked_in_pilot_is_inert_for_fixture_content(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            target = resolve_component_target(self.ir, root=ROOT, language="en")
        assert target is not None
        self.assertEqual("pilot", target.status)
        self.assertFalse(target.active)
        self.assertEqual("", out.getvalue())

    def test_only_a_declared_single_language_build_is_a_component_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            self.assertIsNone(
                resolve_component_target(self.ir, root=root, language="fr"))
            self.assertIsNone(
                resolve_component_target(self.ir, root=root, language=None))
            self.assertIsNone(resolve_component_target(
                replace(self.ir, region="AU"), root=root, language="en"))
            self.assertIsNone(resolve_component_target(
                replace(self.ir, model="JE-1000G"), root=root, language="en"))
            bilingual = replace(
                self.ir,
                pages=(
                    *self.ir.pages,
                    replace(self.ir.pages[0], source_ref="page/x_fr.rst", language="fr"),
                ),
            )
            self.assertIsNone(
                resolve_component_target(bilingual, root=root, language="en"))
            undeclared = self._root(
                str(Path(tmp) / "undeclared"),
                entry={"target": TARGET, "path": PLAN_REF},
            )
            self.assertIsNone(
                resolve_component_target(self.ir, root=undeclared, language="en"))

    def test_an_explicit_plan_supersedes_the_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(
                tmp,
                extra_entries=({
                    "target": {"model": "JE-1000F", "region": "US", "languages": ["en"]},
                    "path": PLAN_REF,
                },),
            )
            approved = resolve_component_target(self.ir, root=root, language="en")
            assembly = resolve_component_target(
                self.ir,
                root=self._root(str(Path(tmp) / "assembly")),
                language="en",
                assembly_plan=Path("configs/assembly.json"),
            )
        assert approved is not None and assembly is not None
        self.assertEqual(
            ("superseded by the approved reference plan registered for this build",),
            approved.issues,
        )
        self.assertEqual(
            ("superseded by the configured target assembly plan configs/assembly.json",),
            assembly.issues,
        )

    def test_compositions_and_the_lcd_profile_need_an_active_target(self) -> None:
        refs = [page.source_ref for page in self.ir.pages]
        pages = [
            {
                "source_ref": page.source_ref,
                "source_sha256": page.source_sha256,
                "language": page.language,
                "composition_id": "en_pair" if index < 2 else f"en_{index}",
            }
            for index, page in enumerate(self.ir.pages)
        ]
        pages.append({
            "source_ref": "page/cover-en.rst",
            "source_sha256": "1" * 64,
            "language": "en",
            "composition_id": "front_cover",
        })
        profile = {"row_presentation": [{"source_no": "1", "display_no": "1"}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(
                tmp,
                pages=pages,
                plan_changes={
                    "idml_contract": {
                        "editable_components": {"lcd_icon_table": profile},
                    },
                },
            )
            target = resolve_component_target(self.ir, root=root, language="en")
        assert target is not None
        self.assertTrue(target.active)
        pair = target.composition("pair", tuple(refs[:2]))
        assert pair is not None
        self.assertEqual("registered-component", pair["plan_source"])
        self.assertEqual(1, pair["physical_page_count"])
        self.assertEqual(
            [(ref, "pair", "en_pair", 1, 1) for ref in refs[:2]],
            [
                (
                    page["source_path"], page["composition_type"],
                    page["composition_id"], page["start_page"], page["page_count"],
                )
                for page in pair["pages"]
            ],
        )
        self.assertIsNone(target.composition("mixed", (refs[0], refs[2])))
        self.assertIsNone(target.composition("cover", ("page/cover-en.rst",)))
        self.assertEqual(profile, target.lcd_profile())
        inert = replace(target, issues=("drift",))
        self.assertIsNone(inert.composition("pair", tuple(refs[:2])))
        self.assertIsNone(inert.lcd_profile())
        self.assertTrue(target.serves("EN-us"))
        self.assertFalse(target.serves("fr"))
        self.assertFalse(inert.serves("en"))
        invalid = replace(
            target,
            plan={
                **target.plan,
                "idml_contract": {
                    "editable_components": {"lcd_icon_table": {"row_presentation": []}},
                },
            },
        )
        with self.assertRaisesRegex(ReferenceLayoutPlanError, "LCD profile is invalid"):
            invalid.lcd_profile()

    def test_malformed_declarations_and_plans_fail_closed(self) -> None:
        cases = (
            ({"component_targets": {"language": "en"}}, None, "must be a list"),
            ({"component_targets": [{**DECLARATION, "langauge": "en"}]}, None, "unknown keys"),
            ({"component_targets": [{**DECLARATION, "status": "approved"}]}, None, "status must be"),
            ({"component_targets": [{**DECLARATION, "evidence": " "}]}, None, "evidence"),
            ({"component_targets": [DECLARATION, DECLARATION]}, None, "repeats language"),
            ({}, {"approval": {"status": "candidate"}}, "not approved"),
            ({}, {"target": {**TARGET, "region": "EU"}}, "does not match its registry"),
            ({}, {"schema_version": "unknown/v9"}, "schema is unsupported"),
            ({}, {"pages": {}}, "pages must be a list"),
        )
        for entry_changes, plan_changes, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as tmp:
                entry = {
                    "target": TARGET,
                    "path": PLAN_REF,
                    "component_targets": [DECLARATION],
                    **entry_changes,
                }
                root = self._root(tmp, entry=entry, plan_changes=plan_changes)
                with self.assertRaisesRegex(ReferenceLayoutPlanError, message):
                    resolve_component_target(self.ir, root=root, language="en")


if __name__ == "__main__":
    unittest.main()
