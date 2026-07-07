"""Font-map support for template-backed IDML exports."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from xml.sax.saxutils import escape


FONTMAP_DIR_NAME = "字体映射"
FONTMAP_INDEX_NAME = "语言字体映射.yml"
_ATTR_ENTITIES = {'"': "&quot;"}


@dataclass(frozen=True)
class FontReplacement:
    family: str
    style: str | None = None


@dataclass(frozen=True)
class IdmlFontMap:
    source_path: Path
    replacements: dict[str, FontReplacement]
    paragraph_style_attrs: dict[str, str]

    @property
    def target_styles(self) -> dict[str, set[str]]:
        styles: dict[str, set[str]] = {}
        for repl in self.replacements.values():
            styles.setdefault(repl.family, set()).add(repl.style or "Regular")
        return styles


def load_template_font_map(
    template_path: Path,
    lang: str,
    fontmap_dir: Path | None = None,
) -> IdmlFontMap | None:
    base = fontmap_dir or template_path.parent / FONTMAP_DIR_NAME
    index = base / FONTMAP_INDEX_NAME
    if not index.exists():
        return None
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    data = yaml.safe_load(index.read_text(encoding="utf-8")) or {}
    fontmap_name = _fontmap_name_for_lang(data, lang)
    if not fontmap_name:
        return None
    fontmap_path = base / fontmap_name
    if not fontmap_path.exists():
        return None
    payload = json.loads(fontmap_path.read_text(encoding="utf-8"))
    preserve = set(payload.get("_preserve") or [])
    replacements = {
        src: FontReplacement(str(spec["family"]), spec.get("style"))
        for src, spec in (payload.get("fonts") or {}).items()
        if src not in preserve and spec.get("family")
    }
    return IdmlFontMap(
        source_path=fontmap_path,
        replacements=replacements,
        paragraph_style_attrs={
            str(k): str(v)
            for k, v in (payload.get("paragraph_style_attrs") or {}).items()
        },
    )


def apply_styles_font_map(styles_xml: str, font_map: IdmlFontMap | None) -> str:
    if not font_map:
        return styles_xml

    def replace_style_block(match: re.Match[str]) -> str:
        block = _apply_paragraph_attrs(match.group(0), font_map)
        applied = re.search(
            r'<AppliedFont type="string">([^<]+)</AppliedFont>',
            block,
        )
        if not applied:
            return block
        repl = font_map.replacements.get(applied.group(1))
        if not repl:
            return block
        block = (
            block[:applied.start(1)]
            + escape(repl.family)
            + block[applied.end(1):]
        )
        if repl.style:
            block = _replace_font_style(block, repl.style)
        return block

    return re.sub(
        r'<(?:ParagraphStyle|CharacterStyle)\b[\s\S]*?</(?:ParagraphStyle|CharacterStyle)>',
        replace_style_block,
        styles_xml,
    )


def ensure_font_families(fonts_xml: str, font_map: IdmlFontMap | None) -> str:
    if not font_map:
        return fonts_xml
    for family, styles in font_map.target_styles.items():
        if f'Name="{family}"' not in fonts_xml:
            fonts_xml = fonts_xml.replace(
                "</idPkg:Fonts>",
                "\n" + _font_family_xml(family, sorted(styles)) + "\n</idPkg:Fonts>",
            )
    return fonts_xml


def apply_fonts_font_map(
    fonts_xml: str,
    font_map: IdmlFontMap | None,
    *,
    preserve_families: set[str] | None = None,
) -> str:
    if not font_map:
        return fonts_xml
    fonts_xml = _retarget_composite_fonts(fonts_xml, font_map)
    preserved = preserve_families or set()
    for source, repl in font_map.replacements.items():
        if source in preserved or source == repl.family:
            continue
        fonts_xml = _remove_font_family(fonts_xml, source)
    return ensure_font_families(fonts_xml, font_map)


def _fontmap_name_for_lang(data: dict, lang: str) -> str | None:
    languages = data.get("languages") or {}
    scripts = data.get("scripts") or {}
    lowered = {str(k).lower(): v for k, v in languages.items()}
    entry = lowered.get(_lang_alias(lang))
    if entry is None:
        prefix = (lang or "en").split("-", 1)[0].lower()
        entry = next(
            (v for k, v in lowered.items() if k.split("-", 1)[0] == prefix),
            None,
        )
    if not entry:
        entry = lowered.get("en-us")
    script_name = entry.get("script") if isinstance(entry, dict) else None
    script = scripts.get(script_name) if script_name else None
    if not isinstance(script, dict):
        return None
    fontmap = script.get("fontmap")
    return str(fontmap) if fontmap else None


def _lang_alias(lang: str) -> str:
    normalized = (lang or "en").replace("_", "-").lower()
    aliases = {
        "en": "en-us",
        "fr": "fr-fr",
        "es": "es-es",
        "de": "de-de",
        "it": "it-it",
        "ja": "ja-jp",
        "jp": "ja-jp",
        "ko": "ko-kr",
        "kr": "ko-kr",
        "zh": "zh-cn",
        "cn": "zh-cn",
        "uk": "uk-ua",
        "ru": "ru-ru",
        "pt": "pt-pt",
        "br": "pt-pt",
        "pt-br": "pt-pt",
    }
    return aliases.get(normalized, normalized)


def _apply_paragraph_attrs(block: str, font_map: IdmlFontMap) -> str:
    if not font_map.paragraph_style_attrs or not block.startswith("<ParagraphStyle"):
        return block
    opening = re.match(r"<ParagraphStyle\b[^>]*>", block)
    if not opening:
        return block
    tag = opening.group(0)
    for key, value in font_map.paragraph_style_attrs.items():
        attr = f'{key}="{escape(value, _ATTR_ENTITIES)}"'
        if re.search(rf'\b{re.escape(key)}="[^"]*"', tag):
            tag = re.sub(rf'\b{re.escape(key)}="[^"]*"', attr, tag, count=1)
        else:
            tag = tag[:-1] + " " + attr + ">"
    return tag + block[opening.end():]


def _replace_font_style(block: str, style: str) -> str:
    value = escape(style, _ATTR_ENTITIES)
    if re.search(r'\bFontStyle="[^"]*"', block):
        block = re.sub(r'\bFontStyle="[^"]*"', f'FontStyle="{value}"', block, count=1)
    if re.search(r'<FontStyle type="string">[^<]*</FontStyle>', block):
        block = re.sub(
            r'<FontStyle type="string">[^<]*</FontStyle>',
            f'<FontStyle type="string">{escape(style)}</FontStyle>',
            block,
            count=1,
        )
    return block


def _retarget_composite_fonts(fonts_xml: str, font_map: IdmlFontMap) -> str:
    def replace_entry(match: re.Match[str]) -> str:
        block = match.group(0)
        applied = re.search(
            r'<AppliedFont type="string">([^<]+)</AppliedFont>',
            block,
        )
        if not applied:
            return block
        repl = font_map.replacements.get(applied.group(1))
        if not repl:
            return block
        block = (
            block[:applied.start(1)]
            + escape(repl.family)
            + block[applied.end(1):]
        )
        if repl.style:
            block = _replace_font_style(block, repl.style)
        return block

    return re.sub(
        r'<CompositeFontEntry\b[\s\S]*?</CompositeFontEntry>',
        replace_entry,
        fonts_xml,
    )


def _remove_font_family(fonts_xml: str, family: str) -> str:
    name = escape(family, _ATTR_ENTITIES)
    self_closing = re.compile(
        rf'\n?\s*<FontFamily\b(?=[^>]*\bName="{re.escape(name)}")[^>]*/>'
    )
    fonts_xml = self_closing.sub("", fonts_xml)
    paired = re.compile(
        rf'\n?\s*<FontFamily\b(?=[^>]*\bName="{re.escape(name)}")[\s\S]*?</FontFamily>'
    )
    return paired.sub("", fonts_xml)


def _font_family_xml(family: str, styles: list[str]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", family.lower()).strip("_") or "font"
    base_ps = re.sub(r"[^A-Za-z0-9]+", "", family) or "Font"
    lines = [f'  <FontFamily Self="ff_{slug}" Name="{escape(family, _ATTR_ENTITIES)}">']
    for style in styles:
        style_slug = re.sub(r"[^a-z0-9]+", "_", style.lower()).strip("_") or "regular"
        ps_style = re.sub(r"[^A-Za-z0-9]+", "", style) or "Regular"
        lines.append(
            f'    <Font Self="ff_{slug}_{style_slug}" '
            f'FontFamily="{escape(family, _ATTR_ENTITIES)}" '
            f'Name="{escape(family + " " + style, _ATTR_ENTITIES)}" '
            f'PostScriptName="{base_ps}-{ps_style}" Status="Installed" '
            f'FontStyleName="{escape(style, _ATTR_ENTITIES)}" FontType="OpenTypeCFF"/>'
        )
    lines.append("  </FontFamily>")
    return "\n".join(lines)
