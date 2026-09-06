"""Drop out-of-scope language blocks from a multi-language RST page.

Some pages are not one language's page — they carry every family language
inline, one tagged block after another. The preface is the whole
population: ``docs/templates/page_eu/00_preface.rst`` runs EN → FR → ES →
DE → IT → UK in one file, and ``docs/templates/page_shared/en/00_preface.rst``
runs EN → FR → ES. Language-scoped *page* selection cannot help there,
because from the manifest's point of view that is a single ``lang: en``
page.

This is the class of drift that produced the AU leftover incident and the
``JE-1000F/US`` preface row in ``data/lang_parity_known_exceptions.csv``:
a single-language line inheriting a multi-language template and shipping
blocks it should not. The fork-a-template workaround
(``00_preface_single_language.rst``) fixes one line and leaves the next one
to rediscover the problem.

Trimming is **opt-in per manifest entry** (``lang_blocks: true``), never
sniffed: ``**IT ...**`` is a legitimate bold run in ordinary prose, and a
heuristic that deleted it would silently drop real content.

Two marker forms are recognised, and one page may use both:

- ``\\HBLangTagLine{XX}{...}`` inside a ``.. raw:: latex`` block (LaTeX)
- ``**XX ...**`` as a bold header line (the ``.. only:: not latex`` twin)

Text before the first marker belongs to the page's own language — the
leading English block of both prefaces is untagged in its bold form.

Directive blocks are kept or dropped whole, so a dropped block never
leaves an empty ``.. only::`` behind. Non-marker lines inside a boundary
``raw:: latex`` block are *structure*, not language content, and survive
their block being dropped: ``\\HBPrefacePageBegin`` shares a block with
``\\HBLangTagLine{EN}`` and ``\\HBPrefacePageEnd`` sits in a block of its
own. Losing either would break the LaTeX page.

When nothing is out of scope the input string is returned unchanged, so a
family that ships every language it declares keeps byte-identical output.
"""
from __future__ import annotations

import re
from pathlib import Path

from tools.lang_registry import LANGUAGE_REGISTRY, canonical_language

# `**FR IMPORTANT**`-style header. The tag must be followed by a separator
# so `**FRAGILE**` is not read as a French block.
_BOLD_TAG_RE = re.compile(r"^\s*\*\*([A-Za-z][A-Za-z_-]{1,5})[ \-—]")
_LANG_TAG_LINE_RE = re.compile(r"\\HBLangTagLine\{([A-Za-z_-]+)\}")
_APPLY_LANG_RE = re.compile(r"\\HBApplyLang\{([^{}]+)\}")
_PAGE_INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$")
_DIRECTIVE_RE = re.compile(r"^\s*\.\.\s+\S+::")
_RAW_LATEX_RE = re.compile(r"^\s*\.\.\s+raw::\s*latex\s*$")

# Only tags that name a registered language may open a block. Anything else
# is ordinary bold prose.
_KNOWN_TAGS = frozenset(
    alias.upper() for spec in LANGUAGE_REGISTRY for alias in spec.aliases
)
_DISPLAY_NAME_LANGUAGES = {
    spec.display_name.casefold(): spec.code for spec in LANGUAGE_REGISTRY
}


def _tag_language(token: str) -> str | None:
    if token.upper() not in _KNOWN_TAGS:
        return None
    return canonical_language(token)


def _directive_block_end(lines: list[str], start: int) -> int:
    """Index just past the directive block opened at ``start``."""
    index = start + 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    while index < len(lines) and (
        not lines[index].strip() or lines[index][:1] in (" ", "\t")
    ):
        index += 1
    return index


def _marker_in(block: list[str]) -> str | None:
    """The language a directive block's body opens, if any."""
    for line in block:
        match = _LANG_TAG_LINE_RE.search(line)
        if match:
            lang = _tag_language(match.group(1))
            if lang:
                return lang
        bold = _BOLD_TAG_RE.match(line)
        if bold:
            lang = _tag_language(bold.group(1))
            if lang:
                return lang
    return None


def _trim_language_scope_line(line: str, *, scope: set[str]) -> str:
    """Trim an explicit ``English / French`` catalogue when fully recognized."""
    newline = ""
    body = line
    if body.endswith("\r\n"):
        body, newline = body[:-2], "\r\n"
    elif body.endswith("\n"):
        body, newline = body[:-1], "\n"
    leading = body[: len(body) - len(body.lstrip())]
    trailing = body[len(body.rstrip()) :]
    tokens = [token.strip() for token in body.strip().split("/")]
    if len(tokens) < 2:
        return line
    resolved = [_DISPLAY_NAME_LANGUAGES.get(token.casefold()) for token in tokens]
    if any(language is None for language in resolved):
        return line
    kept = [
        token
        for token, language in zip(tokens, resolved, strict=True)
        if language in scope
    ]
    if not kept or len(kept) == len(tokens):
        return line
    return f"{leading}{' / '.join(kept)}{trailing}{newline}"


def marker_languages(text: str) -> tuple[str, ...]:
    """Languages this page opens a tagged block for, in first-seen order."""
    found: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if _DIRECTIVE_RE.match(lines[index]):
            end = _directive_block_end(lines, index)
            lang = _marker_in(lines[index:end])
            if lang and lang not in found:
                found.append(lang)
            index = end
            continue
        bold = _BOLD_TAG_RE.match(lines[index])
        if bold:
            lang = _tag_language(bold.group(1))
            if lang and lang not in found:
                found.append(lang)
        index += 1
    return tuple(found)


def trim_language_blocks(
    text: str,
    *,
    languages: list[str] | tuple[str, ...],
    page_lang: str | None = None,
) -> tuple[str, tuple[str, ...]]:
    """Return ``(trimmed_text, dropped_languages)``.

    ``languages`` is the target's resolved language scope; ``page_lang``
    owns everything before the first marker.
    """
    scope = {
        code for code in (canonical_language(lang) for lang in languages) if code
    }
    if not scope:
        return text, ()

    dropped = tuple(lang for lang in marker_languages(text) if lang not in scope)
    if not dropped:
        return text, ()

    current = canonical_language(page_lang) if page_lang else None
    lines = text.splitlines(keepends=True)
    bare = [line.rstrip("\n") for line in lines]
    kept: list[str] = []
    index = 0
    while index < len(lines):
        if _DIRECTIVE_RE.match(bare[index]):
            end = _directive_block_end(bare, index)
            block = lines[index:end]
            marker = _marker_in(bare[index:end])
            if marker is not None:
                current = marker
            if current is None or current in scope:
                kept.extend(block)
            elif _RAW_LATEX_RE.match(bare[index]):
                structure = [
                    line for line in block[1:]
                    if not _LANG_TAG_LINE_RE.search(line)
                ]
                if any(line.strip() for line in structure):
                    kept.append(block[0])
                    kept.extend(structure)
            index = end
            continue

        bold = _BOLD_TAG_RE.match(bare[index])
        if bold:
            lang = _tag_language(bold.group(1))
            if lang:
                current = lang
        if current is None or current in scope:
            kept.append(lines[index])
        index += 1

    kept = [_trim_language_scope_line(line, scope=scope) for line in kept]
    trimmed = "".join(kept)
    if trimmed and not trimmed.endswith("\n"):
        trimmed += "\n"
    return trimmed, dropped


def trim_bundle_language_blocks(
    *,
    bundle_dir: Path,
    lang_block_pages: tuple[tuple[str, str | None], ...] | list[tuple[str, str | None]],
    languages: list[str] | tuple[str, ...],
) -> list[tuple[str, tuple[str, ...]]]:
    """Re-apply the trim to already-written bundle pages.

    A review overlay replaces a materialized page with the committed
    ``docs/_review`` derivative, which is shared by a region's merged and
    single-language configs and therefore holds every language the *merged*
    book needs. Trimming the template at materialization time cannot reach it,
    so this runs again on the bundle copy. ``docs/_review`` itself is never
    written — the master stays multi-language and each derivative build trims
    its own copy.

    Returns ``[(file_name, dropped_languages), ...]`` for pages it changed.
    """
    changed: list[tuple[str, tuple[str, ...]]] = []
    if not languages:
        return changed
    for file_name, page_lang in lang_block_pages:
        page_path = bundle_dir / "page" / file_name
        if not page_path.is_file():
            continue
        original = page_path.read_text(encoding="utf-8")
        trimmed, dropped = trim_language_blocks(
            original, languages=list(languages), page_lang=page_lang
        )
        if not dropped or trimmed == original:
            continue
        page_path.write_text(trimmed, encoding="utf-8")
        changed.append((file_name, dropped))
    return changed


def _declared_page_language(page_path: Path) -> str | None:
    """Return one explicit page language, or ``None`` when not unambiguous."""
    try:
        text = page_path.read_text(encoding="utf-8")
    except OSError:
        return None

    marker_tokens = _APPLY_LANG_RE.findall(text)
    marker_languages = {
        canonical_language(token.strip()) for token in marker_tokens
    }
    if None in marker_languages or len(marker_languages) != 1:
        return None
    return next(iter(marker_languages))


def trim_bundle_language_pages(
    *,
    bundle_dir: Path,
    languages: list[str] | tuple[str, ...],
) -> list[tuple[str, str]]:
    """Remove out-of-scope review page includes from the bundle index.

    A committed merged review derivative may predate a target-language scope
    reduction. Keep the review files byte-identical and project only its
    explicitly declared in-scope pages into the generated bundle index.
    Unknown and genuinely multi-language pages remain included; inline
    language blocks are handled separately by ``trim_bundle_language_blocks``.
    """
    scope = {
        code for code in (canonical_language(lang) for lang in languages) if code
    }
    index_path = bundle_dir / "index.rst"
    if not scope or not index_path.is_file():
        return []

    lines = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept: list[str] = []
    dropped: list[tuple[str, str]] = []
    for line in lines:
        match = _PAGE_INCLUDE_RE.match(line.rstrip("\r\n"))
        if match is None:
            kept.append(line)
            continue

        relative = Path(match.group(1))
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or len(relative.parts) < 2
            or relative.parts[0] != "page"
            or relative.suffix.casefold() != ".rst"
        ):
            kept.append(line)
            continue

        language = _declared_page_language(bundle_dir / relative)
        if language is None or language in scope:
            kept.append(line)
            continue
        dropped.append((relative.relative_to("page").as_posix(), language))

    if dropped:
        index_path.write_text("".join(kept), encoding="utf-8")
    return dropped
