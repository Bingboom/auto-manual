from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def prepare_manual_bundle(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    data_root: str | None = None,
    source_mode: str = "auto",
    page_selector: str | None = None,
    output_root: Path | None = None,
    write_wrapper_index: bool = True,
    valid_source_modes: set[str],
    materialize_bundle: Callable[..., Any],
    review_bundle_exists: Callable[..., bool],
    overlay_review_onto_bundle: Callable[..., None],
    review_content_exists: Callable[..., bool],
    overlay_review_content_onto_bundle: Callable[..., None],
    docs_dir: Path,
    printer: Callable[[str], None] = print,
) -> Any:
    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type != "manual_bundle":
        raise RuntimeError(f"Unsupported doc_type: {doc_type}")
    if source_mode not in valid_source_modes:
        raise RuntimeError(f"Unsupported source mode: {source_mode}")

    bundle = materialize_bundle(
        cfg,
        model=model,
        region=region,
        data_root=data_root,
        ensure_csv_pages=True,
        page_selector=page_selector,
        bundle_dir_override=(output_root / "rst") if output_root else None,
        write_wrapper_index=write_wrapper_index,
    )
    review_applied = False
    if source_mode in {"auto", "review"}:
        review_lang_candidates = [lang]
        if (lang or "").strip():
            review_lang_candidates.append(None)
        for review_lang in review_lang_candidates:
            if review_bundle_exists(docs_dir=docs_dir, model=model, region=region, lang=review_lang):
                overlay_review_onto_bundle(
                    bundle_dir=bundle.bundle_dir,
                    docs_dir=docs_dir,
                    model=model,
                    region=region,
                    lang=review_lang,
                )
                review_applied = True
                break
            if review_content_exists(docs_dir=docs_dir, model=model, region=region, lang=review_lang):
                overlay_review_content_onto_bundle(
                    bundle_dir=bundle.bundle_dir,
                    docs_dir=docs_dir,
                    model=model,
                    region=region,
                    lang=review_lang,
                )
                review_applied = True
                break
        if source_mode == "review" and not review_applied:
            raise RuntimeError(
                "Review bundle not found for "
                f"model='{model or ''}', region='{region or ''}'. "
                "Run 'python build.py review ...' first."
            )
    printer(f"[build] Prepared bundle: {bundle.bundle_dir}")
    printer("[build] Bundle source: review" if review_applied else "[build] Bundle source: runtime")
    return bundle
