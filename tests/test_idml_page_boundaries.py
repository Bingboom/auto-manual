#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural gates against hand-drawn page geometry.

The per-component boundary tests enumerate specific functions, so the failure
mode they cannot see is the one the next product line actually has: a NEW
composer, a NEW model branch, a NEW finalize stretch. These gates are
structural — they walk whatever exists, so new code is covered the day it is
written:

* every function named ``add_*_page`` anywhere in ``tools/idml`` is a page
  composer by convention and must not touch component internals;
* style may not branch on model names or page numbers anywhere in
  ``tools/idml`` beyond the explicitly whitelisted legacy back-cover profile;
* model-name string literals in code are ratcheted at today's exact set —
  the copy-paste template for the next hand-drawing round is a new literal;
* the finalize script may write ``geometricBounds`` only inside the three
  audited functions (one labelled-carrier grower, two documented exceptions
  — see the usage guide §4).

Each whitelist entry names the legacy it covers. Shrinking a whitelist is
progress; growing one needs the same review as a shared-style change.
"""
from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDML = ROOT / "tools" / "idml"

# ── rule data ────────────────────────────────────────────────────────────────

# Component internals no composer may reference. Prefix matching over both
# Name and Attribute nodes, so `writer._symbols_signal_table(...)` and a bare
# import alias are caught alike.
FORBIDDEN_INTERNAL_SUBSTRINGS = (
    "panel_metrics",
    "symbols_panel_metrics",
    "frame_with_background",
    "fixed_panel_primitives",
)
FORBIDDEN_PRIVATE_PREFIXES = (
    "_symbols_",
    "_safety_",
    "_troubleshooting_",
    "_fcc_",
    "_lcd_",
)

# The one legacy style branch that predates the component boundaries: the
# back-cover profile fallback in page_placed.py. The boundary audit declared
# it out of scope; retiring it (profile → reference-plan data) deletes these
# entries. Nothing else may compare a model-ish name against a literal.
ALLOWED_MODEL_COMPARISONS = {
    ("page_placed.py", "je1000f"),
    ("page_placed.py", "jbp2000b"),
}

# Model-name string literals in tools/idml code (docstrings excluded), pinned
# at today's exact set. All three files are data-plane uses; a NEW pair here
# means someone is wiring a model name into renderer code — route it through
# composition/config data instead (usage guide §1).
MODEL_LITERAL_PATTERN = re.compile(r"jbp[-_ ]?2000b|je[-_]?\d{3,4}[a-z]?", re.I)
ALLOWED_MODEL_LITERALS = {
    ("asset_contracts.py", "asset:controls/je1000f_us/network_pairing_panel"),
    ("prose_image.py", "/app/je1000f_us/add_device_je1000f_us.png"),
    ("prose_image.py", "/app/je1000f_us/connect_result_je1000f_us.png"),
    ("page_placed.py", "docs/renderers/latex/assets/back_cover_qr_jbp2000b.pdf"),
    ("page_placed.py", "jbp2000b"),
    ("page_placed.py", "je1000f"),
}

# geometricBounds writers in the finalize script: the labelled-carrier grower
# plus the two exceptions documented in the usage guide §4. A new function
# that stretches frames must argue its way into this set in review.
ALLOWED_GEOMETRY_WRITERS = {
    "growTableTerminalCarrier",
    "fitTerminalCarrierFrames",
    "resizeComposedTableShell",
}


def _idml_sources() -> list[Path]:
    return [
        path for path in sorted(IDML.rglob("*.py"))
        if "__pycache__" not in path.parts
    ]


def _referenced_names(node: ast.AST):
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            yield child.id, child.lineno
        elif isinstance(child, ast.Attribute):
            yield child.attr, child.lineno


class ComposerBoundaryTests(unittest.TestCase):
    def test_every_add_page_composer_avoids_component_internals(self) -> None:
        """Non-enumerative version of the per-composer inspect tests: any
        function following the ``add_*_page`` composer convention, in any
        module, present or future."""
        composers = 0
        violations: list[str] = []
        for path in _idml_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not (node.name.startswith("add_") and node.name.endswith("_page")):
                    continue
                composers += 1
                for name, lineno in _referenced_names(node):
                    internal = any(
                        fragment in name
                        for fragment in FORBIDDEN_INTERNAL_SUBSTRINGS
                    ) or any(
                        name.startswith(prefix)
                        for prefix in FORBIDDEN_PRIVATE_PREFIXES
                    )
                    if internal:
                        violations.append(
                            f"{path.name}:{lineno} {node.name} references "
                            f"component internal {name!r}"
                        )
        self.assertGreaterEqual(
            composers, 10,
            "the composer convention scan found suspiciously few add_*_page "
            "functions — did the naming convention change?",
        )
        self.assertEqual(
            [], violations,
            "page composers must pass data/language/variant/rectangle only; "
            "move the geometry into the owning component "
            "(code-as-doc/dev/style_component_usage_guide.md §2)",
        )

    def test_composers_import_no_private_component_names(self) -> None:
        violations: list[str] = []
        for path in _idml_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                module = node.module or ""
                if "components" not in module:
                    continue
                for alias in node.names:
                    if alias.name.startswith("_"):
                        violations.append(
                            f"{path.name}:{node.lineno} imports private "
                            f"{alias.name!r} from {module}"
                        )
        self.assertEqual([], violations)

    def test_style_never_branches_on_model_or_page_number(self) -> None:
        """Equality comparisons of a model/page_number name against a literal
        are the flagship reject-shape (usage guide §9). Scope filtering via
        ``in``/``not in`` membership is data-plane and stays allowed."""
        found: set[tuple[str, str]] = set()
        offenders: list[str] = []
        for path in _idml_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare):
                    continue
                if not all(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
                    continue
                parts = [node.left, *node.comparators]
                mentions = " ".join(ast.dump(part) for part in parts).lower()
                if "model" not in mentions and "page_number" not in mentions:
                    continue
                literals = [
                    part.value for part in parts
                    if isinstance(part, ast.Constant)
                    and isinstance(part.value, (str, int))
                    and not isinstance(part.value, bool)
                ]
                for value in literals:
                    key = (path.name, str(value))
                    found.add(key)
                    if key not in ALLOWED_MODEL_COMPARISONS:
                        offenders.append(f"{path.name}:{node.lineno} == {value!r}")
        self.assertEqual(
            [], offenders,
            "style must not branch on model/page identity; select behaviour "
            "through composition data or config "
            "(code-as-doc/dev/style_component_usage_guide.md §1)",
        )

    def test_model_name_literals_are_ratcheted(self) -> None:
        docstrings: set[str] = set()
        found: set[tuple[str, str]] = set()
        for path in _idml_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    text = ast.get_docstring(node)
                    if text:
                        docstrings.add(text)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                    continue
                if node.value in docstrings:
                    continue
                if MODEL_LITERAL_PATTERN.search(node.value) and len(node.value) < 200:
                    found.add((path.name, node.value))
        new = found - ALLOWED_MODEL_LITERALS
        self.assertEqual(
            set(), new,
            "new model-name literal in renderer code — carry the identity in "
            "composition/config data instead; if genuinely data-plane, add it "
            "to ALLOWED_MODEL_LITERALS with a review",
        )


class FinalizeGeometryGateTests(unittest.TestCase):
    def test_geometry_writes_stay_in_the_three_audited_functions(self) -> None:
        source = (IDML / "indesign_finalize.jsx").read_text(encoding="utf-8")
        functions = [
            (match.start(), match.group(1))
            for match in re.finditer(r"function\s+([A-Za-z0-9_]+)\s*\(", source)
        ]
        writers: set[str] = set()
        for match in re.finditer(r"\.geometricBounds\s*=", source):
            enclosing = [name for start, name in functions if start < match.start()]
            writers.add(enclosing[-1] if enclosing else "(module scope)")
        self.assertEqual(
            ALLOWED_GEOMETRY_WRITERS, writers,
            "a finalize function gained or lost a geometricBounds write; "
            "carriers are the only sanctioned growth surface "
            "(usage guide §4 and its two documented exceptions)",
        )


# ── Phase C: component regression registry ──────────────────────────────────
#
# Every complete panel component declares its regression matrix here. A new
# Panel class that is not registered fails the census test; a registered
# component whose fixture loses a (density, language) cell fails the matrix
# test. Adapters return the covered cells from each component's actual
# regression source, because the fixtures are heterogeneous by history.

def _json_matrix(fixture: str) -> set[tuple[str, str]]:
    payload = json.loads(
        (ROOT / "tests" / "fixtures" / fixture).read_text(encoding="utf-8")
    )
    return {
        (density, language)
        for density, languages in payload.items()
        for language in languages
    }


def _safety_matrix(mode: str) -> set[tuple[str, str]]:
    from tests.test_idml_safety_panel_golden import GOLDEN

    return {
        (mode, language)
        for language, modes in GOLDEN.items()
        if mode in modes
    }


def _storage_matrix() -> set[tuple[str, str]]:
    from tests.test_idml_fixed_panel_golden import STORAGE_GOLDEN

    return {("standard", language) for language in STORAGE_GOLDEN}


COMPONENT_REGRESSION_REGISTRY: dict[str, dict] = {
    "SymbolsPanel": {
        "declared": {(d, lang) for d in ("standard", "compact")
                     for lang in ("en", "fr", "es")},
        "covered": lambda: _json_matrix("idml_symbols_panel_golden.json"),
    },
    "FccPanel": {
        "declared": {(d, lang) for d in ("standard", "compact")
                     for lang in ("en", "fr", "es")},
        "covered": lambda: _json_matrix("idml_fixed_panel_golden.json"),
    },
    "InboxPanel": {
        "declared": {(d, lang) for d in ("standard", "compact")
                     for lang in ("en", "fr", "es")},
        "covered": lambda: _json_matrix("idml_fixed_panel_golden.json"),
    },
    "FccInboxPanel": {
        "declared": {(d, lang) for d in ("standard", "compact")
                     for lang in ("en", "fr", "es")},
        "covered": lambda: _json_matrix("idml_fixed_panel_golden.json"),
    },
    "SafetyPanel": {
        "declared": {("standard", lang) for lang in ("en", "fr", "es")},
        "covered": lambda: _safety_matrix("standard"),
    },
    "CompactSafetyPanel": {
        "declared": {("compact", lang) for lang in ("en", "fr", "es")},
        "covered": lambda: _safety_matrix("compact"),
    },
    "SafetySymbolsPanel": {
        "declared": {("maintenance", lang) for lang in ("en", "fr", "es")},
        "covered": lambda: _safety_matrix("maintenance"),
    },
    "StoragePanel": {
        "declared": {("standard", lang) for lang in ("en", "fr", "es")},
        "covered": _storage_matrix,
    },
}


class ComponentRegressionRegistryTests(unittest.TestCase):
    def _panel_classes(self) -> set[str]:
        names: set[str] = set()
        for path in sorted((IDML / "components").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not node.name.endswith("Panel"):
                    continue
                names.add(node.name)
        return names

    def test_every_panel_class_is_registered(self) -> None:
        """A new complete component must declare its regression matrix the day
        it is born — this census is what makes the registry a gate rather
        than a list."""
        panels = self._panel_classes()
        unregistered = panels - set(COMPONENT_REGRESSION_REGISTRY)
        self.assertEqual(
            set(), unregistered,
            "register the new panel's (density, language) matrix in "
            "COMPONENT_REGRESSION_REGISTRY with a fixture adapter",
        )
        stale = set(COMPONENT_REGRESSION_REGISTRY) - panels
        self.assertEqual(set(), stale, "registry names a panel that no longer exists")

    def test_every_declared_cell_has_regression_coverage(self) -> None:
        for name, entry in COMPONENT_REGRESSION_REGISTRY.items():
            covered = entry["covered"]()
            missing = entry["declared"] - covered
            with self.subTest(component=name):
                self.assertEqual(
                    set(), missing,
                    f"{name} declares cells with no golden coverage",
                )


if __name__ == "__main__":
    unittest.main()
