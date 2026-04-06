from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable


def normalize_sphinx_tag_value(value: str | None) -> str | None:
    text = (value or "").strip().lower()
    if not text:
        return None
    normalized = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return normalized or None


def sphinx_tag_args(
    *,
    model: str | None = None,
    region: str | None = None,
    lang: str | None = None,
    normalize_sphinx_tag_value: Callable[[str | None], str | None],
) -> list[str]:
    args: list[str] = []
    for prefix, value in (("model", model), ("region", region), ("lang", lang)):
        normalized = normalize_sphinx_tag_value(value)
        if normalized:
            args.extend(["-t", f"{prefix}_{normalized}"])
    return args


def load_configured_html_theme(conf_base_path: Path) -> str | None:
    if not conf_base_path.exists():
        return None
    for line in conf_base_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("html_theme"):
            continue
        _, _, raw = stripped.partition("=")
        value = raw.split("#", 1)[0].strip().strip("\"'")
        return value or None
    return None


def should_use_minimal_html_theme(
    conf_dir: Path,
    requested_minimal: bool,
    *,
    load_configured_html_theme: Callable[[Path], str | None],
    find_spec: Callable[[str], Any],
    printer: Callable[[str], None] = print,
) -> bool:
    if requested_minimal:
        return True
    theme_name = load_configured_html_theme(conf_dir / "conf_base.py")
    if not theme_name or theme_name in {"alabaster", "classic", "basic"}:
        return False
    if find_spec(theme_name) is not None:
        return False
    printer(f"[build] HTML theme '{theme_name}' not available, fallback to alabaster")
    return True


def body_tag_with_class(body_tag: str, class_name: str) -> str:
    class_match = re.search(r'\bclass=(["\'])(.*?)\1', body_tag, re.IGNORECASE | re.DOTALL)
    if class_match:
        quote = class_match.group(1)
        classes = class_match.group(2).split()
        if class_name in classes:
            return body_tag
        new_classes = " ".join([*classes, class_name]).strip()
        return body_tag[: class_match.start()] + f'class={quote}{new_classes}{quote}' + body_tag[class_match.end() :]
    return body_tag[:-1] + f' class="{class_name}">'


def language_label(lang: str, *, labels: dict[str, str]) -> str:
    key = (lang or "").strip().lower()
    return labels.get(key, key.upper() or "Unknown")


def variant_key(variant: Any) -> tuple[str, str]:
    return (variant.region.upper(), variant.lang.lower())


def variant_priority(variant: Any) -> tuple[int, str]:
    return (1 if variant.lang_in_output_path else 0, variant.html_dir_token)


def effective_variants_for_current(
    variants: list[Any],
    *,
    current_variant: Any,
    variant_key: Callable[[Any], tuple[str, str]],
    variant_priority: Callable[[Any], tuple[int, str]],
) -> list[Any]:
    selected: dict[tuple[str, str], Any] = {}
    for variant in sorted(variants, key=lambda item: (item.region.upper(), item.lang.lower(), item.html_dir_token)):
        key = variant_key(variant)
        existing = selected.get(key)
        if existing is None or variant_priority(variant) > variant_priority(existing):
            selected[key] = variant
    selected[variant_key(current_variant)] = current_variant
    return sorted(selected.values(), key=lambda item: (item.region.upper(), item.lang.lower(), item.html_dir_token))
