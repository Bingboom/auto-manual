"""Per-target language scope: which languages one model actually ships.

A family config declares the languages of the *whole family* — the union
across every model in that region. ``configs/config.eu.yaml`` lists six
(en/fr/es/de/it/uk) because the EU line as a whole carries Ukrainian
templates, but JE-1000F does not ship Ukrainian. Deleting ``uk`` from the
family config would strip it from the models that do ship it, so the
per-model answer belongs in data, not in the config.

``data/model_languages.csv`` holds that answer keyed on the same
``<MODEL>_<REGION>`` document key the capability mirror uses. Resolution is
an intersection that preserves the family's declared order, so the family
config stays the single place that decides *ordering* and the data table
only ever subtracts.

Fail-open, twice over, for the same reason the capability gate is
(``tools/capability_pages.py``): missing inventory data must never change
what an existing line builds.

- No row for a target -> every family language is kept.
- A row that excludes *every* family language is a contradiction, not an
  instruction: the build keeps the family languages unchanged and
  ``check`` reports ``LANG_SCOPE_UNSHIPPED_LANGUAGE``. This is the
  ``configs/config.eu-uk.yaml`` case — a Ukrainian-only derivative config
  whose inherited default target is a model that ships no Ukrainian.

Structural problems in the table itself fail loudly (missing column,
duplicate key, blank cell, unregistered language code): a silently
mis-parsed row would ship a book in the wrong set of languages.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from tools.lang_registry import LANGUAGE_BY_CODE, canonical_language

MODEL_LANGUAGES_CSV = "model_languages.csv"

REQUIRED_COLUMNS = ("Document_key", "languages")

# Semicolon, not comma: this column is a list inside one CSV cell, and a
# half-width comma inside a field has bitten this repo's CSV contracts
# before (data/capability_page_rules.csv notes, dingtalk_delivery_map).
LANGUAGE_SEPARATOR = ";"


@dataclass(frozen=True)
class LanguageScope:
    """The languages one ``(model, region)`` target ships, and the why."""

    languages: tuple[str, ...]
    family_languages: tuple[str, ...]
    dropped: tuple[str, ...]
    undeclared: tuple[str, ...]
    document_key: str | None
    has_row: bool
    unshipped: bool

    @property
    def is_trimmed(self) -> bool:
        return bool(self.dropped)

    def notes(self) -> tuple[str, ...]:
        """Human-readable drop notes for build logs."""
        if not self.dropped:
            return ()
        return (
            f"{self.document_key} ships {list(self.languages)}; "
            f"dropped family language(s) {list(self.dropped)} per "
            f"data/{MODEL_LANGUAGES_CSV}",
        )


def _canonical_codes(raw: str, *, key: str, path: Path) -> tuple[str, ...]:
    codes: list[str] = []
    for token in raw.split(LANGUAGE_SEPARATOR):
        text = token.strip()
        if not text:
            continue
        code = canonical_language(text)
        if code is None:
            raise RuntimeError(
                f"{path}: row '{key}' lists unregistered language '{text}'; "
                "add it to tools/lang_registry.py first"
            )
        if code not in codes:
            codes.append(code)
    if not codes:
        raise RuntimeError(
            f"{path}: row '{key}' has an empty languages cell; remove the row "
            "to fall back to the family languages"
        )
    return tuple(codes)


def load_model_languages(data_dir: Path) -> dict[str, tuple[str, ...]]:
    """Document_key -> the languages that target ships."""
    path = data_dir / MODEL_LANGUAGES_CSV
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = {str(name).strip() for name in (reader.fieldnames or [])}
        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        if missing:
            raise RuntimeError(
                f"{path} is missing required column(s): {', '.join(missing)}"
            )
        out: dict[str, tuple[str, ...]] = {}
        for row in reader:
            key = (row.get("Document_key") or "").strip()
            if not key:
                continue
            if key in out:
                raise RuntimeError(
                    f"{path}: duplicate Document_key '{key}'; one row per target"
                )
            out[key] = _canonical_codes(
                row.get("languages") or "", key=key, path=path
            )
    return out


def resolve_target_languages(
    family_languages: list[str] | tuple[str, ...],
    *,
    model: str | None,
    region: str | None,
    data_dir: Path,
) -> LanguageScope:
    """Narrow ``family_languages`` to what ``(model, region)`` ships."""
    family = tuple(str(lang).strip() for lang in family_languages if str(lang).strip())
    if not model or not region:
        return LanguageScope(
            languages=family,
            family_languages=family,
            dropped=(),
            undeclared=(),
            document_key=None,
            has_row=False,
            unshipped=False,
        )

    document_key = f"{model}_{region}"
    shipped = load_model_languages(data_dir).get(document_key)
    if shipped is None:
        return LanguageScope(
            languages=family,
            family_languages=family,
            dropped=(),
            undeclared=(),
            document_key=document_key,
            has_row=False,
            unshipped=False,
        )

    # Compare on canonical codes so a family config spelling ("jp", "ukr")
    # still matches a registry-canonical table cell.
    kept = tuple(
        lang for lang in family
        if (canonical_language(lang) or lang) in shipped
    )
    dropped = tuple(lang for lang in family if lang not in kept)
    family_codes = {canonical_language(lang) or lang for lang in family}
    undeclared = tuple(code for code in shipped if code not in family_codes)

    if not kept:
        # Every family language is unshipped: keep the build byte-identical
        # and let check fail on the contradiction.
        return LanguageScope(
            languages=family,
            family_languages=family,
            dropped=(),
            undeclared=undeclared,
            document_key=document_key,
            has_row=True,
            unshipped=True,
        )

    return LanguageScope(
        languages=kept,
        family_languages=family,
        dropped=dropped,
        undeclared=undeclared,
        document_key=document_key,
        has_row=True,
        unshipped=False,
    )


def language_scope_label(languages: tuple[str, ...] | list[str]) -> str:
    """Render a language set as the printed ``MANUAL_LANGUAGE_SCOPE`` line.

    The literal in each family config (``English / French / Spanish``) is
    exactly this rendering of that family's languages; deriving it keeps a
    trimmed target's cover line honest instead of advertising a language
    the book no longer contains.
    """
    names: list[str] = []
    for lang in languages:
        code = canonical_language(lang)
        spec = LANGUAGE_BY_CODE.get(code) if code else None
        name = spec.display_name if spec is not None else str(lang).strip()
        if name and name not in names:
            names.append(name)
    return " / ".join(names)
