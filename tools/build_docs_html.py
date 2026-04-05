from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def write_html_manual_meta(
    html_out_dir: Path,
    *,
    docs_build_dir: Path,
    model: str | None,
    region: str | None,
    lang: str,
    title: str,
    lang_in_output_path: bool,
    manual_meta_file_name: str,
) -> Path:
    if not (model or "").strip():
        raise RuntimeError("HTML manual metadata requires a model")
    if not (region or "").strip():
        raise RuntimeError("HTML manual metadata requires a region")

    html_dir_token = html_out_dir.relative_to(docs_build_dir).as_posix()
    payload = {
        "model": model.strip(),
        "region": region.strip(),
        "lang": lang.strip(),
        "title": title.strip(),
        "html_dir": html_dir_token,
        "lang_in_output_path": bool(lang_in_output_path),
    }
    meta_path = html_out_dir / manual_meta_file_name
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta_path


def load_html_manual_variant(
    meta_path: Path,
    *,
    docs_build_dir: Path,
    variant_cls: type[Any],
) -> Any | None:
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None

    model = str(raw.get("model", "")).strip()
    region = str(raw.get("region", "")).strip()
    lang = str(raw.get("lang", "")).strip().lower()
    title = str(raw.get("title", "")).strip()
    html_dir_token = str(raw.get("html_dir", "")).strip()
    if not (model and region and lang and html_dir_token):
        return None

    html_dir = docs_build_dir / Path(html_dir_token)
    lang_in_output_path = bool(raw.get("lang_in_output_path", False))
    return variant_cls(
        model=model,
        region=region,
        lang=lang,
        title=title,
        html_dir=html_dir,
        html_dir_token=html_dir_token,
        lang_in_output_path=lang_in_output_path,
    )


def collect_model_html_variants(
    *,
    model: str | None,
    docs_build_dir: Path,
    manual_meta_file_name: str,
    target_component: Callable[[str | None, str], str],
    load_html_manual_variant: Callable[[Path], Any | None],
) -> list[Any]:
    if not (model or "").strip():
        return []

    model_dir = docs_build_dir / target_component(model, "_shared")
    if not model_dir.exists():
        return []

    variants: list[Any] = []
    for meta_path in sorted(model_dir.rglob(manual_meta_file_name)):
        variant = load_html_manual_variant(meta_path)
        if variant is None or variant.model != model:
            continue
        if not (variant.html_dir / "index.html").exists():
            continue
        variants.append(variant)
    return variants


def inject_manual_switcher_into_html(
    html_path: Path,
    markup: str | None,
    *,
    switcher_block_re: Any,
    body_tag_re: Any,
    body_tag_with_class: Callable[[str, str], str],
    body_switcher_class: str,
) -> bool:
    original = html_path.read_text(encoding="utf-8")
    stripped = switcher_block_re.sub("", original).strip()
    body_match = body_tag_re.search(stripped)
    if body_match is None:
        return False

    body_tag = body_match.group(0)
    new_body_tag = body_tag_with_class(body_tag, body_switcher_class)
    updated = stripped[: body_match.start()] + new_body_tag + stripped[body_match.end() :]
    insert_at = body_match.start() + len(new_body_tag)
    if markup:
        updated = updated[:insert_at] + "\n" + markup + "\n" + updated[insert_at:]
    updated = updated + "\n"
    if updated == original:
        return False
    html_path.write_text(updated, encoding="utf-8")
    return True


def strip_html_cover_section(
    html_path: Path,
    *,
    manual_cover_section_re: Any,
) -> bool:
    original = html_path.read_text(encoding="utf-8")
    updated, count = manual_cover_section_re.subn("", original, count=1)
    if count == 0 or updated == original:
        return False
    html_path.write_text(updated, encoding="utf-8")
    return True


def refresh_model_html_switchers(
    *,
    model: str | None,
    docs_build_dir: Path,
    collect_model_html_variants: Callable[[], list[Any]],
    build_manual_switcher_markup: Callable[..., str | None],
    inject_manual_switcher_into_html: Callable[[Path, str | None], bool],
) -> None:
    variants = collect_model_html_variants()
    if not variants:
        return

    for current_variant in variants:
        for html_path in sorted(current_variant.html_dir.glob("*.html")):
            markup = build_manual_switcher_markup(
                current_variant=current_variant,
                variants=variants,
                current_html_path=html_path,
            )
            inject_manual_switcher_into_html(html_path, markup)
