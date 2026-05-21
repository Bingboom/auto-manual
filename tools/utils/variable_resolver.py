from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

Row = Mapping[str, Any]

_TRUE_VALUES = {"1", "true", "yes", "y"}
_LANG_ALIASES = {
    "ja": ("ja", "jp"),
    "jp": ("jp", "ja"),
    "uk": ("uk", "ukr"),
    "ukr": ("ukr", "uk"),
    "br": ("br", "pt-br", "pt_br"),
    "pt-br": ("pt-br", "pt_br", "br"),
    "pt_br": ("pt_br", "pt-br", "br"),
}
_MODEL_SPLIT_RE = re.compile(r"[,;|]")


def parse_model_tokens(value: Any) -> tuple[str, ...]:
    """Return exact model tokens from a table cell."""
    if value is None:
        return ()

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ()
        parsed = _parse_list_like_text(text)
        if parsed is not None:
            return parse_model_tokens(parsed)
        return _split_model_text(text)

    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, Mapping)):
        tokens: list[str] = []
        for item in value:
            tokens.extend(parse_model_tokens(item))
        return tuple(dict.fromkeys(tokens))

    text = str(value).strip()
    return (text,) if text else ()


def resolve_variable_value(
    default_rows: Sequence[Row],
    override_rows: Sequence[Row] | None,
    variable_key: str,
    model: str | None = None,
    lang: str | None = None,
) -> str | None:
    """Resolve one variable value, then apply an exact language override."""
    base_value = _resolve_base_value(default_rows, variable_key=variable_key, model=model)
    if base_value is None:
        return None
    return _apply_override(
        override_rows or (),
        variable_key=variable_key,
        lang=lang,
        source_value=base_value,
    )


def resolve_variable(
    default_rows: Sequence[Row],
    override_rows: Sequence[Row] | None,
    variable_key: str,
    model: str | None = None,
    lang: str | None = None,
) -> str | None:
    return resolve_variable_value(default_rows, override_rows, variable_key, model, lang)


def resolve_variables(
    default_rows: Sequence[Row],
    override_rows: Sequence[Row] | None,
    model: str | None = None,
    lang: str | None = None,
) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for variable_key in _ordered_variable_keys(default_rows):
        value = resolve_variable_value(default_rows, override_rows, variable_key, model, lang)
        if value is not None:
            resolved[variable_key] = value
    return resolved


def _resolve_base_value(
    rows: Sequence[Row],
    *,
    variable_key: str,
    model: str | None,
) -> str | None:
    key_rows = [row for row in rows if _field(row, "Variable_key", "variable_key") == variable_key]
    requested_model = (model or "").strip()

    if requested_model:
        exact_rows = [
            row
            for row in key_rows
            if requested_model in parse_model_tokens(_field(row, "Model", "model"))
            or requested_model in parse_model_tokens(
                _field(row, "Model_key", "model_key", "Model_Key", "model_text", "Model_text")
            )
        ]
        if len(exact_rows) > 1:
            raise ValueError(
                f"Duplicate exact variable defaults for {variable_key!r} and model {requested_model!r}"
            )
        if exact_rows:
            return _field(exact_rows[0], "Value", "value") or None

    default_rows = [row for row in key_rows if _is_default(row)]
    if len(default_rows) > 1:
        raise ValueError(f"Duplicate default variable values for {variable_key!r}")
    if default_rows:
        return _field(default_rows[0], "Value", "value") or None
    return None


def _apply_override(
    rows: Sequence[Row],
    *,
    variable_key: str,
    lang: str | None,
    source_value: str,
) -> str:
    requested_langs = _lang_candidates(lang)
    if not requested_langs:
        return source_value

    exact_rows = [
        row
        for row in rows
        if _field(row, "Variable_key", "variable_key") == variable_key
        and _field(row, "lang", "Lang", "language", "Language").casefold() in requested_langs
        and _field(
            row,
            "source_value",
            "Source_value",
            "Source_Value",
            "from_prefix",
            "From_prefix",
            "from_value",
            "From_value",
        )
        == source_value
    ]
    if len(exact_rows) > 1:
        raise ValueError(
            f"Duplicate variable overrides for {variable_key!r}, lang {lang!r}, source {source_value!r}"
        )
    if exact_rows:
        return _field(exact_rows[0], "Value", "value", "to_prefix", "To_prefix", "to_value", "To_value")
    return source_value


def _ordered_variable_keys(rows: Sequence[Row]) -> tuple[str, ...]:
    keys: list[str] = []
    for row in rows:
        key = _field(row, "Variable_key", "variable_key")
        if key and key not in keys:
            keys.append(key)
    return tuple(keys)


def _is_default(row: Row) -> bool:
    value = row.get("is_default", row.get("Is_Default", row.get("default", row.get("Default"))))
    if isinstance(value, bool):
        return value
    return str(value or "").strip().casefold() in _TRUE_VALUES


def _field(row: Row, *names: str) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value:
                return value
    return ""


def _lang_candidates(lang: str | None) -> tuple[str, ...]:
    raw = (lang or "").strip().casefold()
    if not raw:
        return ()
    return _LANG_ALIASES.get(raw, (raw,))


def _parse_list_like_text(text: str) -> Any | None:
    if not ((text.startswith("[") and text.endswith("]")) or (text.startswith("(") and text.endswith(")"))):
        return None
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return None
    if isinstance(parsed, (list, tuple, set)):
        return parsed
    return None


def _split_model_text(text: str) -> tuple[str, ...]:
    stripped = text.strip().strip("[](){}")
    tokens = []
    for token in _MODEL_SPLIT_RE.split(stripped):
        normalized = token.strip().strip("'\"")
        if normalized:
            tokens.append(normalized)
    return tuple(dict.fromkeys(tokens))


__all__ = [
    "parse_model_tokens",
    "resolve_variable",
    "resolve_variable_value",
    "resolve_variables",
]
