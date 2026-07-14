"""Language-tree parity check (Milestone I1).

Cross-language structural drift has been discovered by humans three times
(the AU bundle shipping leftover FR/ES preface blocks, the KR line building
as an English shell, #654's silently vanished ES/FR App pages). This module
is the sensor: three data-driven rules over a built/review bundle, wired
into ``check`` next to the capability gate.

- R1 ``LANG_PARITY_FOREIGN_SHELL``: a bundle whose language uses a
  non-Latin script (ko/ja/zh/uk) must actually contain that script on every
  prose-bearing page. Catches untranslated "English shell" pages. Latin
  languages (fr/es/de/…) are *not* separable from English this way — that
  limitation is deliberate; a lexicon check can ratchet in later.
- R2 ``LANG_PARITY_FOREIGN_LANG_BLOCK``: language-tagged blocks
  (``**FR IMPORTANT**`` headers, ``\\HBApplyLang{xx}``) whose language is
  outside the family's configured languages. Catches the AU FR/ES leftover.
- R3 ``LANG_PARITY_MISSING_LANG_PAGE`` / ``LANG_PARITY_FOREIGN_LANG_PAGE``:
  generated per-language pages (``spec_<lang>.rst`` …) must exist for every
  family language once any family language has that page kind, and a
  lang-suffixed page outside the family is a leftover. Catches the
  missing-FR/ES-data-pages class.

Thresholds start conservative (the historical incidents sit at ~0% target
script); tighten only with bundle evidence, the capability-gate lesson.

Pre-existing findings are debt, not news: ``data/lang_parity_known_exceptions.csv``
registers them explicitly (model, region, code, page, note) so check stays
green while the decision routes to the operator — only NEW drift fails.
Remove a row once its underlying content decision lands.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# R1: pages with fewer Latin letters than this carry too little prose to judge.
MIN_LATIN_CHARS_FOR_SHELL_CHECK = 200
# R1: below this share of target-script characters the page counts as a shell.
# The real incidents sat at ~0%; genuinely translated pages with heavy Latin
# terminology (USB-C, AC/DC, URLs) still land far above this.
SHELL_TARGET_SCRIPT_RATIO = 0.05

_SCRIPT_RANGES: dict[str, str] = {
    # Hangul syllables + jamo
    "ko": "가-힣ᄀ-ᇿ㄰-㆏",
    # Kana; kanji is added separately because it is shared with zh
    "ja": "぀-ゟ゠-ヿ一-鿿",
    "zh": "一-鿿㐀-䶿",
    # Cyrillic
    "uk": "Ѐ-ӿ",
    "ukr": "Ѐ-ӿ",
}

# Language tokens that may legitimately suffix a generated page stem.
_LANG_SUFFIX_TOKENS = (
    "en", "fr", "es", "de", "it", "uk", "ukr", "ja", "jp", "ko", "zh",
    "br", "pt-br", "pt_br",
)

# R2: `**FR IMPORTANT**`-style language-tag block headers.
_LANG_TAG_BLOCK_RE = re.compile(r"^\s*\*\*(EN|FR|ES|DE|IT|UK|JA|KO|ZH|PT|BR)[ \-—]", re.MULTILINE)
_APPLY_LANG_RE = re.compile(r"\\HBApplyLang\{([a-zA-Z-]+)\}")

_DIRECTIVE_LINE_RE = re.compile(r"^\s*(\.\.|:)\S*")
_URL_RE = re.compile(r"https?://\S+|[\w.+-]+@[\w-]+\.[\w.]+")

KNOWN_EXCEPTIONS_CSV = "lang_parity_known_exceptions.csv"


def load_known_exceptions(data_dir: Path) -> set[tuple[str, str, str, str]]:
    """(model, region, code, page) tuples registered as accepted debt."""
    path = data_dir / KNOWN_EXCEPTIONS_CSV
    if not path.exists():
        return set()
    out: set[tuple[str, str, str, str]] = set()
    for row in csv.DictReader(path.open(encoding="utf-8")):
        key = tuple((row.get(field) or "").strip()
                    for field in ("model", "region", "code", "page"))
        if all(key):
            out.add(key)  # type: ignore[arg-type]
    return out


def _normalize_lang(lang: str) -> str:
    token = (lang or "").strip().lower().replace("_", "-")
    if token == "jp":
        return "ja"
    if token == "ukr":
        return "uk"
    if token in ("pt-br", "ptbr", "br"):
        return "br"
    return token


def _lang_tag_aliases(lang: str) -> set[str]:
    """Upper-case tags that mean this language in `**XX …**` block headers."""
    normalized = _normalize_lang(lang)
    aliases = {normalized.upper()}
    if normalized == "ja":
        aliases.add("JP")
    if normalized == "uk":
        aliases.add("UKR")
    if normalized == "br":
        aliases.update({"PT", "BR"})
    return aliases


def _prose_text(page_text: str) -> str:
    lines = [
        line
        for line in page_text.splitlines()
        if not _DIRECTIVE_LINE_RE.match(line)
    ]
    return _URL_RE.sub(" ", "\n".join(lines))


def _script_counts(text: str, lang: str) -> tuple[int, int]:
    """(latin_letters, target_script_chars) over prose text."""
    ranges = _SCRIPT_RANGES.get(_normalize_lang(lang))
    latin = len(re.findall(r"[A-Za-z]", text))
    if not ranges:
        return latin, 0
    target = len(re.findall(f"[{ranges}]", text))
    return latin, target


def _page_lang_suffix(stem: str) -> str | None:
    if "_" not in stem:
        return None
    tail = stem.rsplit("_", 1)[1].lower()
    return tail if tail in _LANG_SUFFIX_TOKENS else None


def collect_lang_parity_issues(*, bundle_dir: Path, langs: list[str],
                               model: str, region: str, issue_cls,
                               exceptions: set[tuple[str, str, str, str]] | None = None) -> list:
    page_dir = bundle_dir / "page"
    if not page_dir.is_dir():
        return []
    family_langs = {_normalize_lang(lang) for lang in langs if str(lang).strip()}
    if not family_langs:
        return []
    family_tags: set[str] = set()
    for lang in family_langs:
        family_tags |= _lang_tag_aliases(lang)
    known = exceptions or set()

    issues: list = []

    def _append(code: str, page_key: str, **kwargs) -> None:
        if (model, region, code, page_key) in known:
            return
        issues.append(issue_cls(code=code, model=model, region=region, **kwargs))
    kinds_by_lang: dict[str, dict[str, Path]] = {}

    for page in sorted(page_dir.glob("*.rst")):
        text = page.read_text(encoding="utf-8", errors="replace")

        # R2: language-tagged blocks outside the family.
        foreign_tags = sorted(
            {tag for tag in _LANG_TAG_BLOCK_RE.findall(text) if tag not in family_tags}
        )
        foreign_apply = sorted(
            {code for code in _APPLY_LANG_RE.findall(text)
             if _normalize_lang(code) not in family_langs}
        )
        if foreign_tags or foreign_apply:
            detail = ", ".join(foreign_tags + [f"\\HBApplyLang{{{c}}}" for c in foreign_apply])
            _append(
                "LANG_PARITY_FOREIGN_LANG_BLOCK", page.name,
                message=(f"{page.name} carries language-tagged content outside "
                         f"the family languages {sorted(family_langs)}: {detail}"),
                path=page,
            )

        # R3 inventory: lang-suffixed generated pages.
        suffix = _page_lang_suffix(page.stem)
        if suffix is not None:
            normalized_suffix = _normalize_lang(suffix)
            kind = page.stem.rsplit("_", 1)[0]
            kinds_by_lang.setdefault(kind, {})[normalized_suffix] = page
            if normalized_suffix not in family_langs:
                _append(
                    "LANG_PARITY_FOREIGN_LANG_PAGE", page.name,
                    message=(f"{page.name} is a '{suffix}' page but the family "
                             f"languages are {sorted(family_langs)} — leftover "
                             "from another line?"),
                    path=page,
                )
                continue

        # R1: script shell — only for languages whose script is separable.
        page_lang = suffix if suffix is not None else (langs[0] if len(family_langs) == 1 else None)
        if page_lang is None:
            continue
        normalized_page_lang = _normalize_lang(page_lang)
        if normalized_page_lang not in _SCRIPT_RANGES:
            continue
        if normalized_page_lang not in family_langs:
            continue
        latin, target = _script_counts(_prose_text(text), page_lang)
        total = latin + target
        if latin < MIN_LATIN_CHARS_FOR_SHELL_CHECK or total == 0:
            continue
        if target / total < SHELL_TARGET_SCRIPT_RATIO:
            _append(
                "LANG_PARITY_FOREIGN_SHELL", page.name,
                message=(f"{page.name} should be '{page_lang}' but carries "
                         f"almost no {page_lang}-script text "
                         f"({target} target-script vs {latin} latin chars) — "
                         "untranslated shell?"),
                path=page,
            )

    # R3: every family language must have each generated page kind that any
    # family language has.
    for kind, by_lang in sorted(kinds_by_lang.items()):
        family_hits = {lang for lang in by_lang if lang in family_langs}
        if not family_hits:
            continue
        for lang in sorted(family_langs - set(by_lang)):
            _append(
                "LANG_PARITY_MISSING_LANG_PAGE", f"{kind}_{lang}",
                message=(f"page kind '{kind}' exists for {sorted(family_hits)} "
                         f"but not for family language '{lang}'"),
                path=page_dir,
            )
    return issues
