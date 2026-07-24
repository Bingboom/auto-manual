from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tools.attachment_identity import stage_bundle_attachment_aliases
from tools.data_snapshot import resolve_active_data_root


def _existing_review_overlay_paths(bundle_dir: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for root_name in ("page", "generated"):
        root_dir = bundle_dir / root_name
        if not root_dir.exists():
            continue
        paths.extend(path.relative_to(bundle_dir) for path in sorted(root_dir.rglob("*.rst")) if path.is_file())

    # ``review-asis`` deliberately materializes only a conf/asset skeleton.
    # Its generated index still declares the target-language page filenames,
    # so use those declarations to select the matching rows from a shared
    # multi-language review bundle even though ``page/`` is still empty.
    index_path = bundle_dir / "index.rst"
    if index_path.is_file():
        include_prefix = ".. include::"
        for line in index_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith(include_prefix):
                continue
            raw_value = stripped[len(include_prefix) :].strip()
            relative = Path(raw_value)
            if (
                not raw_value
                or relative.is_absolute()
                or ".." in relative.parts
                or not relative.parts
                or relative.parts[0] not in {"page", "generated"}
                or relative.suffix.casefold() != ".rst"
            ):
                raise RuntimeError(
                    f"Review skeleton has an unsafe RST include: {raw_value!r}"
                )
            paths.append(relative)
    return tuple(dict.fromkeys(paths))


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
    draft_placeholders: bool = False,
    valid_source_modes: set[str],
    materialize_bundle: Callable[..., Any],
    review_bundle_exists: Callable[..., bool],
    overlay_review_onto_bundle: Callable[..., None],
    review_content_exists: Callable[..., bool],
    overlay_review_content_onto_bundle: Callable[..., None],
    finalize_materialized_bundle: Callable[..., Any],
    docs_dir: Path,
    repo_root: Path,
    printer: Callable[[str], None] = print,
) -> Any:
    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type != "manual_bundle":
        raise RuntimeError(f"Unsupported doc_type: {doc_type}")
    if source_mode not in valid_source_modes:
        raise RuntimeError(f"Unsupported source mode: {source_mode}")

    # "review-asis" renders the committed review bundle without re-deriving any
    # page from the build data-root: only the conf/asset skeleton is materialized
    # and the review overlay supplies every content page. This is what lets a
    # review-only render (e.g. the CI HTML preview) succeed for a model that is
    # absent from the data-root.
    skeleton_only = source_mode == "review-asis"
    bundle = materialize_bundle(
        cfg,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        ensure_csv_pages=True,
        page_selector=page_selector,
        bundle_dir_override=(output_root / "rst") if output_root else None,
        write_wrapper_index=write_wrapper_index,
        draft_placeholders=draft_placeholders,
        skeleton_only=skeleton_only,
        finalize_assets=False,
    )
    review_applied = False
    applied_review_dir: Path | None = None
    if source_mode in {"auto", "review", "review-asis"}:
        review_lang_candidates = [lang]
        if (lang or "").strip():
            review_lang_candidates.append(None)
        for review_lang in review_lang_candidates:
            lang_fallback = bool((lang or "").strip()) and review_lang is None
            if review_bundle_exists(docs_dir=docs_dir, model=model, region=region, lang=review_lang):
                if lang_fallback:
                    overlay_result = overlay_review_content_onto_bundle(
                        bundle_dir=bundle.bundle_dir,
                        docs_dir=docs_dir,
                        model=model,
                        region=region,
                        lang=review_lang,
                        target_lang=lang,
                        allowed_relative_paths=_existing_review_overlay_paths(bundle.bundle_dir),
                        allow_index=False,
                    )
                else:
                    overlay_result = overlay_review_onto_bundle(
                        bundle_dir=bundle.bundle_dir,
                        docs_dir=docs_dir,
                        model=model,
                        region=region,
                        lang=review_lang,
                    )
                if overlay_result is None:
                    continue
                if isinstance(overlay_result, Path):
                    applied_review_dir = overlay_result
                review_applied = True
                break
            if review_content_exists(docs_dir=docs_dir, model=model, region=region, lang=review_lang):
                overlay_result = overlay_review_content_onto_bundle(
                    bundle_dir=bundle.bundle_dir,
                    docs_dir=docs_dir,
                    model=model,
                    region=region,
                    lang=review_lang,
                    target_lang=lang if lang_fallback else None,
                    allowed_relative_paths=_existing_review_overlay_paths(bundle.bundle_dir) if lang_fallback else None,
                    allow_index=not lang_fallback,
                )
                if overlay_result is None:
                    continue
                if isinstance(overlay_result, Path):
                    applied_review_dir = overlay_result
                review_applied = True
                break
        if source_mode in {"review", "review-asis"} and not review_applied:
            raise RuntimeError(
                "Review bundle not found for "
                f"model='{model or ''}', region='{region or ''}'. "
                "Run 'python build.py review ...' first."
            )
    # Stage synced bitable attachments (lcd_icons / symbols) for EVERY bundle,
    # not only review overlays: runtime materialization also writes
    # data/phase2/_attachments/... references into the csv pages, and when the
    # ACTIVE data root is not the repo snapshot (e.g. the queue workers'
    # .tmp/review-start/phase2) those references resolve nowhere in the build
    # tree, so the asset finalizer hard-fails (bundle asset reference not
    # found). Staging copies the files from the active data root into the
    # bundle's _repo_assets and rewrites the references to bundle-relative
    # paths, which the finalizer accepts wherever the data root lives.
    active_data_root = resolve_active_data_root(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    alias_report = stage_bundle_attachment_aliases(
        bundle.bundle_dir,
        active_data_root,
    )
    if alias_report.missing:
        raise RuntimeError(
            ("Review bundle" if review_applied else "Bundle")
            + " has unresolved attachment(s): "
            + ", ".join(alias_report.missing)
        )
    if alias_report.aliases:
        printer(
            f"[build] Staged {alias_report.aliases} frozen attachment alias(es) "
            f"across {alias_report.rewritten_files} "
            + ("review" if review_applied else "bundle")
            + " file(s)"
        )
    bundle = finalize_materialized_bundle(
        bundle,
        cfg=cfg,
        docs_dir=docs_dir,
        repo_root=repo_root,
        asset_override_root=(
            applied_review_dir / "overrides"
            if applied_review_dir is not None
            and (applied_review_dir / "overrides").is_dir()
            else None
        ),
    )
    printer(f"[build] Prepared bundle: {bundle.bundle_dir}")
    printer("[build] Bundle source: review" if review_applied else "[build] Bundle source: runtime")
    return bundle
