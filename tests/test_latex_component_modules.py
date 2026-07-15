from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LATEX_DIR = ROOT / "docs" / "renderers" / "latex"

COMPONENT_LOAD_ORDER = [
    "components_base.tex",
    "components_headings.tex",
    "components_special_pages.tex",
    "components_symbols.tex",
    "components_lcd.tex",
    "components_safety.tex",
    "components_spec.tex",
    "components_data_tables.tex",
    "components_warranty.tex",
]

EXPECTED_OWNERS = {
    "components_headings.tex": {
        "HBTitleLevelOne",
        "HBTitleLevelTwo",
        "HBTitleLevelThree",
    },
    "components_symbols.tex": {
        "HBSymbolTable",
        "HBSymbolTwoColumnTables",
        "HBSymbolSignalRow",
        "HBSymbolIconRow",
    },
    "components_lcd.tex": {
        "HBLcdIconTable",
        "HBLcdIconRow",
        "HBLcdModeTable",
        "HBLcdModeFirstGroup",
        "HBLcdModeSecondGroup",
    },
    "components_special_pages.tex": {
        "HBBackCoverPage",
        "HBAppStep",
        "HBInBoxThree",
        "HBOverviewPanel",
        "HBFccBlock",
        "HBPrefacePageBegin",
        "HBTocPageBegin",
    },
}

DEFINITION_PATTERN = re.compile(
    r"\\(?:providecommand|newcommand|renewcommand)\{\\([A-Za-z@]+)\}"
    r"|\\(?:newenvironment|NewEnviron|newtcolorbox)\{([A-Za-z@]+)\}"
)

ALLOWED_CROSS_MODULE_DEFINITIONS = {
    # Safety and symbol lockups both support the same legacy signal-word
    # overrides. They intentionally provide compatible defaults.
    "HBSignalWordFontSize",
    "HBSignalWordLeading",
    # Table environments locally restore LaTeX's built-in row multiplier.
    "arraystretch",
}


def _definitions(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {
        next(group for group in match.groups() if group)
        for match in DEFINITION_PATTERN.finditer(text)
    }


class LatexComponentModuleTests(unittest.TestCase):
    def test_theme_loads_component_modules_in_dependency_order(self) -> None:
        theme = (LATEX_DIR / "theme.tex").read_text(encoding="utf-8")
        positions = [theme.index(rf"\input{{{name}}}") for name in COMPONENT_LOAD_ORDER]
        self.assertEqual(sorted(positions), positions)

        conf = (ROOT / "docs" / "conf_base.py").read_text(encoding="utf-8")
        for name in COMPONENT_LOAD_ORDER:
            self.assertIn(f'"renderers/latex/{name}"', conf)

    def test_lcd_table_uses_the_shared_rounded_shell(self) -> None:
        component = (LATEX_DIR / "components_lcd.tex").read_text(encoding="utf-8")
        self.assertIn(r"\begin{HBSharedDataTable}", component)
        self.assertIn("HBcomp_table_text_indent", component)
        self.assertNotIn(r"\begin{longtable}", component)
        self.assertNotIn("rounded outer corner", component)

    def test_domain_components_have_one_owner(self) -> None:
        owners: dict[str, list[str]] = defaultdict(list)
        for path in sorted(LATEX_DIR.glob("components_*.tex")):
            for symbol in _definitions(path):
                owners[symbol].append(path.name)

        duplicates = {
            symbol: paths
            for symbol, paths in owners.items()
            if len(paths) > 1 and symbol not in ALLOWED_CROSS_MODULE_DEFINITIONS
        }
        self.assertEqual({}, duplicates)

        for filename, expected in EXPECTED_OWNERS.items():
            self.assertLessEqual(expected, _definitions(LATEX_DIR / filename))

    def test_base_file_contains_only_shared_foundations(self) -> None:
        base = (LATEX_DIR / "components_base.tex").read_text(encoding="utf-8")
        forbidden_prefixes = (
            "HBTitleLevel",
            "HBSymbol",
            "HBLcd",
            "HBFcc",
            "HBPreface",
            "HBToc",
            "HBInBox",
            "HBOverview",
            "HBApp",
            "HBBackCover",
        )
        for prefix in forbidden_prefixes:
            self.assertNotIn(prefix, base)
        self.assertLess(len(base.splitlines()), 400)

    def test_style_registry_is_complete_and_unique(self) -> None:
        registry = (LATEX_DIR / "STYLE_REGISTRY.md").read_text(encoding="utf-8")
        style_ids = re.findall(r"^\| `(HB-[A-Z0-9-]+)` \|", registry, re.MULTILINE)
        self.assertEqual(31, len(style_ids))
        self.assertEqual(len(style_ids), len(set(style_ids)))
        self.assertIn("34 visible variants", registry)
        for name in COMPONENT_LOAD_ORDER:
            self.assertIn(name, registry)


if __name__ == "__main__":
    unittest.main()
