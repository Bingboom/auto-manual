"""Shared language jump navigation for whole-document Web manuals."""

from __future__ import annotations

import re
from collections.abc import Sequence

from bs4 import BeautifulSoup, NavigableString, Tag

from tools import lang_registry
from tools.manual_ir import ManualIR


class WebLanguageNavigationError(ValueError):
    """Raised when a declared multilingual document cannot form safe links."""


def _declared_language_specs(ir: ManualIR) -> tuple[lang_registry.LanguageSpec, ...]:
    declared = ir.metadata.get("declared_languages")
    if not isinstance(declared, (list, tuple)):
        return ()
    specs: list[lang_registry.LanguageSpec] = []
    seen: set[str] = set()
    for raw in declared:
        spec = lang_registry.language_spec(raw)
        if spec is None:
            raise WebLanguageNavigationError(
                f"Web language navigation has unknown declared language: {raw!r}"
            )
        if spec.code in seen:
            raise WebLanguageNavigationError(
                f"Web language navigation repeats declared language: {spec.code}"
            )
        seen.add(spec.code)
        specs.append(spec)
    return tuple(specs)


def _anchor_id(code: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", code.casefold()).strip("-")
    if not token:
        raise WebLanguageNavigationError(
            f"Web language navigation cannot form an anchor for {code!r}"
        )
    return f"hb-lang-{token}"


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


def add_web_language_navigation(
    ir: ManualIR,
    fragments: Sequence[str],
) -> tuple[str, ...]:
    """Add one shared nav and one stable anchor at each language boundary."""

    rendered = tuple(fragments)
    if len(rendered) != len(ir.pages):
        raise WebLanguageNavigationError(
            "Web language navigation requires one fragment per document page"
        )
    specs = _declared_language_specs(ir)
    if len(specs) < 2:
        return rendered

    declared_codes = {spec.code for spec in specs}
    first_page_by_language: dict[str, int] = {}
    for index, page in enumerate(ir.pages):
        spec = lang_registry.language_spec(page.language)
        if spec is None:
            raise WebLanguageNavigationError(
                f"Web language navigation has unknown page language: {page.language!r}"
            )
        if spec.code not in declared_codes:
            raise WebLanguageNavigationError(
                f"Web page language {spec.code!r} is not declared by the document"
            )
        first_page_by_language.setdefault(spec.code, index)
    missing = [spec.code for spec in specs if spec.code not in first_page_by_language]
    if missing:
        raise WebLanguageNavigationError(
            "Web language navigation has no page boundary for: " + ", ".join(missing)
        )

    soups = [BeautifulSoup(fragment, "html.parser") for fragment in rendered]
    _remove_matching_source_inventory(soups[0], specs)
    for spec in specs:
        anchor = soups[first_page_by_language[spec.code]].new_tag(
            "span",
            attrs={
                "id": _anchor_id(spec.code),
                "class": "hb-language-anchor",
                "data-language": spec.code,
                "aria-hidden": "true",
            },
        )
        soups[first_page_by_language[spec.code]].insert(0, anchor)

    nav = soups[0].new_tag(
        "nav",
        attrs={
            "class": "hb-language-nav",
            "aria-label": " / ".join(spec.native_name for spec in specs),
        },
    )
    language_list = soups[0].new_tag("ul", attrs={"class": "hb-language-list"})
    for spec in specs:
        item = soups[0].new_tag("li")
        link = soups[0].new_tag(
            "a",
            attrs={
                "class": "hb-language-link",
                "href": f"#{_anchor_id(spec.code)}",
                "hreflang": spec.code,
                "lang": spec.code,
                "data-language": spec.code,
            },
        )
        link.string = spec.native_name
        item.append(link)
        language_list.append(item)
    nav.append(language_list)
    soups[0].insert(0, nav)
    return tuple(str(soup) for soup in soups)


def protect_web_language_navigation_for_pandoc(
    html_text: str,
) -> tuple[str, dict[str, str]]:
    """Protect nav and empty boundary anchors from Pandoc's HTML flattening."""

    soup = BeautifulSoup(html_text, "html.parser")
    nodes = soup.select("nav.hb-language-nav, span.hb-language-anchor")
    if not nodes:
        return html_text, {}
    navs = [node for node in nodes if node.name == "nav"]
    if len(navs) != 1:
        raise WebLanguageNavigationError(
            f"Web language navigation expected one nav, found {len(navs)}"
        )
    protected: dict[str, str] = {}
    for node in nodes:
        token = f"AUTOMANUALWEBLANGUAGE{len(protected) + 1:04d}PLACEHOLDER"
        protected[token] = str(node)
        placeholder = soup.new_tag("p")
        placeholder.append(NavigableString(token))
        node.replace_with(placeholder)
    return str(soup), protected


def restore_web_language_navigation_after_pandoc(
    markdown_text: str,
    protected: dict[str, str],
) -> str:
    """Restore every protected language node exactly once."""

    restored = markdown_text
    for token, node_html in protected.items():
        occurrences = restored.count(token)
        if occurrences != 1:
            raise WebLanguageNavigationError(
                f"Pandoc Web language placeholder {token} occurred {occurrences} "
                "times; expected once"
            )
        restored = restored.replace(token, f"\n\n{node_html}\n\n")
    return restored


__all__ = [
    "WebLanguageNavigationError",
    "add_web_language_navigation",
    "protect_web_language_navigation_for_pandoc",
    "restore_web_language_navigation_after_pandoc",
]
