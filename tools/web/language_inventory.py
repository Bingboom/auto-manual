"""Language checks and the merged-language inventory line for whole-document Web manuals.

The in-page language bar is retired: the publication portal's locale picker
switches languages, so a merged multilingual document gets no nav or anchors.
"""

from __future__ import annotations

from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag

from tools import lang_registry
from tools.manual_ir import ManualIR


class WebLanguageInventoryError(ValueError):
    """Raised when a declared multilingual document's languages are inconsistent."""


def _declared_language_specs(ir: ManualIR) -> tuple[lang_registry.LanguageSpec, ...]:
    declared = ir.metadata.get("declared_languages")
    if not isinstance(declared, (list, tuple)):
        return ()
    specs: list[lang_registry.LanguageSpec] = []
    seen: set[str] = set()
    for raw in declared:
        spec = lang_registry.language_spec(raw)
        if spec is None:
            raise WebLanguageInventoryError(
                f"Web document has unknown declared language: {raw!r}"
            )
        if spec.code in seen:
            raise WebLanguageInventoryError(
                f"Web document repeats declared language: {spec.code}"
            )
        seen.add(spec.code)
        specs.append(spec)
    return tuple(specs)


def _remove_matching_source_inventory(
    soup: BeautifulSoup,
    specs: Sequence[lang_registry.LanguageSpec],
) -> None:
    first_block = next(
        (child for child in soup.contents if isinstance(child, Tag)),
        None,
    )
    if not isinstance(first_block, Tag) or first_block.name != "p":
        return
    text = " ".join(first_block.get_text(" ", strip=True).split())
    inventories = {
        " / ".join(spec.display_name for spec in specs),
        " / ".join(spec.native_name for spec in specs),
    }
    if text in inventories:
        first_block.decompose()


def strip_web_language_inventory(
    ir: ManualIR,
    fragments: Sequence[str],
) -> tuple[str, ...]:
    """Check page languages and drop a leading merged-language inventory line."""

    rendered = tuple(fragments)
    if len(rendered) != len(ir.pages):
        raise WebLanguageInventoryError(
            "Web language checks require one fragment per document page"
        )
    from tools.manual_ir.external_languages import frozen_language_issues

    frozen_issues = frozen_language_issues(ir)
    if frozen_issues is not None:
        if frozen_issues:
            raise WebLanguageInventoryError("; ".join(frozen_issues))
        # One explicitly source-bound locale; the publication portal owns the
        # cross-book selector. Do not register fictitious phase2 columns here.
        return rendered
    specs = _declared_language_specs(ir)
    if len(specs) < 2:
        return rendered

    declared_codes = {spec.code for spec in specs}
    languages_with_pages: set[str] = set()
    for page in ir.pages:
        spec = lang_registry.language_spec(page.language)
        if spec is None:
            raise WebLanguageInventoryError(
                f"Web document has unknown page language: {page.language!r}"
            )
        if spec.code not in declared_codes:
            raise WebLanguageInventoryError(
                f"Web page language {spec.code!r} is not declared by the document"
            )
        languages_with_pages.add(spec.code)
    missing = [spec.code for spec in specs if spec.code not in languages_with_pages]
    if missing:
        raise WebLanguageInventoryError(
            "Web document has no page for declared language: " + ", ".join(missing)
        )

    # Serialize every fragment through the same parser as before, so only the
    # inventory line changes.
    soups = [BeautifulSoup(fragment, "html.parser") for fragment in rendered]
    _remove_matching_source_inventory(soups[0], specs)
    return tuple(str(soup) for soup in soups)


__all__ = [
    "WebLanguageInventoryError",
    "strip_web_language_inventory",
]
