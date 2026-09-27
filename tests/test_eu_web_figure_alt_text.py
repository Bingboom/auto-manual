"""EU Web figures must not describe themselves as placeholders.

The EU single-language Web manuals published figure alt text such as
"AC charging cable image placeholder." or "Abbildung des AC-Ladekabels als
Platzhalter." -- screen readers announced every such figure as unfinished.

These tests resolve, for every target of the EU single-language configs, the
page carriers that the build reads (manifest defaults, per-target manifests
and generated-page model overrides) and fail when any figure alt text still
uses a language's placeholder wording. JE-1000F/EU renders its Web routes from
the committed review derivative, so its review pages in the frozen source's
build languages are checked too. Carriers of lines that are not published on
the Web (KR, AU, US runtime templates) are out of scope here.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

from tools.config_loader import load_config_mapping
from tools.config_pages import GeneratedPage, RstIncludePage, parse_config_pages

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EU_SINGLE_LANGUAGE_LINES = ("en", "de", "es", "fr", "it", "uk")
JE1000F_EU_SOURCE = ROOT / "manual_sources" / "JE-1000F" / "EU" / "en-fr" / "2.0"

# The wording each language's carriers used for an unfinished figure.
PLACEHOLDER_WORDING = re.compile(
    r"placeholder|Platzhalter|Segnaposto|Заглушка|Marcador de posición|marcador de tienda",
    re.IGNORECASE,
)
ALT_TEXT = re.compile(r"^\s*:alt:\s*(?P<option>.*?)\s*$|alt=\"(?P<attribute>[^\"]*)\"", re.MULTILINE)
REVIEW_PAGE_LANGUAGE = re.compile(r"\\HBApplyLang\{(?P<lang>[a-z-]+)\}")


def figure_alt_texts(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [
        match.group("option") if match.group("option") is not None else match.group("attribute")
        for match in ALT_TEXT.finditer(text)
    ]


def eu_web_carriers() -> dict[Path, set[str]]:
    """Carrier path -> the EU single-language targets whose build reads it."""
    carriers: dict[Path, set[str]] = {}
    for line in EU_SINGLE_LANGUAGE_LINES:
        config = load_config_mapping(ROOT / "configs" / f"config.eu-{line}.yaml")
        paths = config["paths"]
        per_target = paths.get("page_manifests") or {}
        for target in config["build"]["targets"]:
            model, region = target["model"], target["region"]
            manifest_path = ROOT / per_target.get(f"{model}_{region}", paths["page_manifest"])
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            pages, issues = parse_config_pages(manifest["pages"], model=model)
            errors = [issue.msg for issue in issues if issue.level == "ERROR"]
            if errors:
                raise AssertionError(f"{manifest_path}: {errors}")
            for page in pages:
                if isinstance(page, GeneratedPage):
                    relative = page.template
                elif isinstance(page, RstIncludePage):
                    relative = page.file
                else:
                    continue
                carriers.setdefault(DOCS / relative, set()).add(f"{model}/{region}/{line}")
    return carriers


def je1000f_eu_web_review_pages() -> list[Path]:
    """Review pages of the languages the frozen JE-1000F/EU source builds."""
    manifest = json.loads((JE1000F_EU_SOURCE / "source_manifest.json").read_text(encoding="utf-8"))
    languages = set(manifest["build_configs"])
    pages = []
    for record in manifest["review_files"]:
        path = ROOT / record["path"]
        if "/page/" not in record["path"] or path.suffix != ".rst":
            continue
        declared = REVIEW_PAGE_LANGUAGE.search(path.read_text(encoding="utf-8"))
        if declared and declared.group("lang") in languages:
            pages.append(path)
    return pages


class EuWebFigureAltTextTests(unittest.TestCase):
    def test_eu_web_carriers_resolve(self) -> None:
        carriers = eu_web_carriers()
        # One shared carrier, one per-model override and one per-target
        # manifest page, so a resolution regression cannot pass vacuously.
        self.assertIn(DOCS / "templates/page_shared/de/02_whats_in_the_box.rst", carriers)
        self.assertIn(DOCS / "templates/targets/je3000c/05_operation_guide_uk.rst", carriers)
        self.assertIn("JE-2000E/EU/it", carriers[DOCS / "templates/page_eu-it/05_operation_guide_je2000e.rst"])
        for path in carriers:
            self.assertTrue(path.is_file(), path)

    def test_no_eu_web_carrier_calls_a_figure_a_placeholder(self) -> None:
        offenders = [
            f"{path.relative_to(ROOT)} ({', '.join(sorted(targets))}): {alt}"
            for path, targets in sorted(eu_web_carriers().items())
            for alt in figure_alt_texts(path)
            if PLACEHOLDER_WORDING.search(alt)
        ]
        self.assertEqual([], offenders)

    def test_no_je1000f_eu_web_review_page_calls_a_figure_a_placeholder(self) -> None:
        pages = je1000f_eu_web_review_pages()
        # en + fr/es/de/it: seven pages with figures per language at least.
        self.assertGreaterEqual(len(pages), 35)
        offenders = [
            f"{path.relative_to(ROOT)}: {alt}"
            for path in pages
            for alt in figure_alt_texts(path)
            if PLACEHOLDER_WORDING.search(alt)
        ]
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
