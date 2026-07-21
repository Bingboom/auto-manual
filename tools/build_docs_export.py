from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from tools.asset_registry import AssetRegistryError
from tools.build_docs_artifacts import (
    build_markdown_artifact,
    build_pdf_artifact,
    build_word_artifact,
    finalize_html_artifact,
    resolve_build_artifact_plan,
)
from tools.asset_usage import ASSET_USAGE_MANIFEST_FILENAME
from tools.gen_index_bundle_assets import raw_html_asset_values
from tools.safe_copy import copy_regular_file_no_symlinks
from tools.utils.path_utils import PathSegments, latex_renderer_of


def _copy_attachment_images_for_latex(
    bundle_dir: Path,
    latex_out_dir: Path,
    printer: Callable[[str], None],
) -> None:
    """Flat-copy synced bitable attachment images into the LaTeX build dir.

    Raw-latex renderers reference these by bare basename via
    \\HBImageOrPlaceholder -> \\IfFileExists; Sphinx only copies images it
    sees in ``.. image::`` directives, so without this step every icon
    cell silently rendered as an empty placeholder
    (reports/typography_gap/2026-07-03 #3).
    """
    image_roots = sorted(
        (bundle_dir / "_repo_assets").glob("**/_attachments"),
    )
    # word_template common assets are also referenced by bare basename from
    # raw latex (e.g. HBInBoxThree -> main_unit1.png); the static
    # latex_additional_files list in conf_base.py only carries a couple of
    # them, so sweep the whole bundled common_assets tree as well.
    common_assets = bundle_dir / "_assets" / "templates" / "word_template" / "common_assets"
    if common_assets.is_dir():
        image_roots.append(common_assets)
    dynamic_latex_assets = latex_renderer_of(bundle_dir) / PathSegments.ASSETS
    if dynamic_latex_assets.is_dir():
        image_roots.append(dynamic_latex_assets)
    copied = 0
    # The registry declares target-scoped overrides homed under
    # renderers/latex/assets whose basenames MATCH the shared asset they
    # override (charging/je1000f_us/car_charge over charging/car_charge,
    # 2026-07-20 first live case) — for those, the override wins the flat
    # latex dir by design. "The shared asset" is identified by BYTES, not by
    # who copied it: Sphinx pre-copies the common_assets image whenever a
    # page references it via ``.. image::`` (the run-5 finding), so a
    # pre-existing dst whose bytes equal a generic root's same-basename file
    # is the same override scenario. The rule is symmetric in arrival order
    # (run-8 finding: pages that reference the asset through its semantic key
    # make Sphinx materialize the OVERRIDE bytes first — the shared generic
    # copy must then yield, not raise). Anything else — Sphinx-copied bytes
    # matching neither side, or two generic roots disagreeing — is a real
    # collision and still raises.
    generic_sources: dict[str, bytes] = {}
    override_sources: dict[str, bytes] = {}
    for root in image_roots:
        target = override_sources if root == dynamic_latex_assets else generic_sources
        for src in sorted(root.rglob("*")):
            if src.is_file() and src.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf"):
                target.setdefault(src.name, src.read_bytes())
    for root in image_roots:
        is_override_root = root == dynamic_latex_assets
        for src in sorted(root.rglob("*")):
            if not src.is_file() or src.suffix.lower() not in (".png", ".jpg", ".jpeg", ".pdf"):
                continue
            dst = latex_out_dir / src.name
            content = src.read_bytes()
            if dst.exists() or dst.is_symlink():
                if dst.is_symlink() or not dst.is_file():
                    raise AssetRegistryError(
                        f"LaTeX asset basename collision for {src.name}: {src} -> {dst}"
                    )
                if dst.read_bytes() == content:
                    continue
                if is_override_root and dst.read_bytes() == generic_sources.get(src.name):
                    printer(
                        f"[build] target-scoped override: {src.name} from renderers/latex/assets "
                        "replaces the shared copy"
                    )
                    dst.write_bytes(content)
                    continue
                if not is_override_root and dst.read_bytes() == override_sources.get(src.name):
                    printer(
                        f"[build] shared copy of {src.name} skipped: the latex dir already "
                        "carries the target-scoped override"
                    )
                    continue
                raise AssetRegistryError(
                    f"LaTeX asset basename collision for {src.name}: {src} -> {dst}"
                )
            dst.write_bytes(content)
            copied += 1
    if copied:
        printer(f"[build] Copied {copied} attachment/asset image(s) into latex dir")


def _bundle_file(root: Path, relative_value: object, *, label: str) -> Path:
    raw_value = str(relative_value or "").strip()
    relative = Path(raw_value)
    if not raw_value or relative.is_absolute() or ".." in relative.parts:
        raise AssetRegistryError(f"{label} has an unsafe bundle path: {raw_value!r}")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AssetRegistryError(f"{label} must not use a symbolic link: {raw_value}")
    try:
        canonical = current.resolve(strict=True)
        canonical.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise AssetRegistryError(f"{label} is outside or missing from the bundle: {raw_value}") from exc
    if not canonical.is_file():
        raise AssetRegistryError(f"{label} is not a regular file: {raw_value}")
    return canonical


def _copy_raw_html_assets_for_html(
    bundle_dir: Path,
    html_out_dir: Path,
    printer: Callable[[str], None],
) -> None:
    """Copy exactly the accounted local assets referenced by raw HTML ``src``."""

    bundle_root = bundle_dir.resolve(strict=True)
    manifest_path = _bundle_file(
        bundle_root,
        ASSET_USAGE_MANIFEST_FILENAME,
        label="asset usage manifest",
    )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssetRegistryError(f"asset usage manifest is invalid: {manifest_path}") from exc
    rewrites = payload.get("rewrites") if isinstance(payload, dict) else None
    if not isinstance(rewrites, list):
        raise AssetRegistryError(f"asset usage manifest has invalid rewrites: {manifest_path}")

    rendered_by_reference: dict[str, set[str]] = {}
    for row in rewrites:
        if not isinstance(row, dict):
            raise AssetRegistryError(f"asset usage manifest has invalid rewrite rows: {manifest_path}")
        reference_path = str(row.get("reference_path") or "").strip()
        rendered_value = str(row.get("rendered_value") or "").strip()
        if not reference_path or not rendered_value:
            raise AssetRegistryError(f"asset usage manifest has incomplete rewrite rows: {manifest_path}")
        rendered_by_reference.setdefault(reference_path, set()).add(rendered_value)

    raw_html_paths: set[str] = set()
    for reference_path, rendered_values in sorted(rendered_by_reference.items()):
        reference = _bundle_file(
            bundle_root,
            reference_path,
            label="raw HTML asset reference",
        )
        html_values = set(raw_html_asset_values(reference.read_text(encoding="utf-8")))
        raw_html_paths.update(rendered_values & html_values)

    html_out_dir.mkdir(parents=True, exist_ok=True)
    if html_out_dir.is_symlink() or not html_out_dir.is_dir():
        raise AssetRegistryError(f"HTML output is not a safe directory: {html_out_dir}")
    html_root = html_out_dir.resolve(strict=True)
    copied = 0
    for raw_value in sorted(raw_html_paths):
        source = _bundle_file(bundle_root, raw_value, label="raw HTML asset")
        copy_regular_file_no_symlinks(
            source,
            html_root / raw_value,
            source_root=bundle_root,
            destination_root=html_root,
            label="raw HTML asset",
        )
        copied += 1
    if copied:
        printer(f"[build] Copied {copied} raw-HTML asset(s) into html dir")


def build_target(
    cfg: dict,
    *,
    target_model: str | None,
    target_region: str | None,
    target_lang: str | None,
    requested_formats: list[str],
    pdf_mode: str,
    build_cfg: dict,
    tools_cfg: dict,
    no_open: bool,
    source_mode: str,
    data_root: str | None,
    page_selector: str | None = None,
    output_root: Path | None = None,
    output_base_root: Path | None = None,
    write_wrapper_index: bool = True,
    draft_placeholders: bool = False,
    default_docs_build_dir: Path,
    resolve_cfg_languages: Callable[[dict], list[str]],
    build_root_for_target: Callable[..., Path],
    ensure_target_identity: Callable[..., None],
    prepare_manual_bundle: Callable[..., Any],
    render_build_template: Callable[..., str],
    resolve_output_path: Callable[[Path, str], Path],
    sphinx_build: Callable[..., None],
    patch_fonts: Callable[..., None],
    compile_xelatex: Callable[..., None],
    export_word_from_bundle: Callable[..., Path],
    export_word_from_html: Callable[..., Path],
    export_word_from_latex: Callable[..., Path],
    export_markdown_from_bundle: Callable[..., Path],
    export_pdf_from_docx_via_word: Callable[[Path, Path], Path],
    copy_file: Callable[[Path, Path], None],
    open_file: Callable[[Path], None],
    strip_html_cover_section: Callable[[Path], None],
    write_html_manual_meta: Callable[..., None],
    refresh_model_html_switchers: Callable[..., None],
    printer: Callable[[str], None] = print,
) -> None:
    artifact_plan = resolve_build_artifact_plan(
        build_cfg=build_cfg,
        tools_cfg=tools_cfg,
        target_model=target_model,
        target_region=target_region,
        target_lang=target_lang,
        no_open=no_open,
        output_root=output_root,
        output_base_root=output_base_root,
        default_docs_build_dir=default_docs_build_dir,
        resolve_cfg_languages=resolve_cfg_languages,
        build_root_for_target=build_root_for_target,
        render_build_template=render_build_template,
    )
    # review-asis renders the committed review bundle without touching the
    # data-root, so the Spec_Master identity guard (which would fail for a model
    # absent from that data-root) does not apply.
    if source_mode != "review-asis":
        ensure_target_identity(
            cfg,
            model=target_model,
            region=target_region,
            lang=artifact_plan.primary_lang,
            data_root=data_root,
        )

    bundle = prepare_manual_bundle(
        cfg,
        model=target_model,
        region=target_region,
        lang=target_lang,
        data_root=data_root,
        source_mode=source_mode,
        page_selector=page_selector,
        output_root=artifact_plan.build_root,
        write_wrapper_index=write_wrapper_index,
        draft_placeholders=draft_placeholders,
    )

    html_built = False
    latex_built = False

    def ensure_html(*, minimal_theme: bool) -> None:
        nonlocal html_built
        if html_built:
            return
        sphinx_build(
            "html",
            src_dir=bundle.bundle_dir,
            out_dir=artifact_plan.html_out_dir,
            conf_dir=bundle.bundle_dir,
            model=target_model,
            region=target_region,
            lang=target_lang or artifact_plan.primary_lang,
            minimal_theme=minimal_theme,
        )
        _copy_raw_html_assets_for_html(
            Path(bundle.bundle_dir),
            Path(artifact_plan.html_out_dir),
            printer,
        )
        html_built = True

    def ensure_latex() -> None:
        nonlocal latex_built
        if latex_built:
            return
        sphinx_build(
            "latex",
            src_dir=bundle.bundle_dir,
            out_dir=artifact_plan.latex_out_dir,
            conf_dir=bundle.bundle_dir,
            model=target_model,
            region=target_region,
            lang=target_lang or artifact_plan.primary_lang,
        )
        _copy_attachment_images_for_latex(
            Path(bundle.bundle_dir), Path(artifact_plan.latex_out_dir), printer,
        )
        patch_fonts(artifact_plan.patch_fonts_script, artifact_plan.main_tex, build_dir=artifact_plan.latex_out_dir)
        compile_xelatex(artifact_plan.main_tex, artifact_plan.xelatex_runs, cwd=artifact_plan.latex_out_dir)
        latex_built = True

    if "html" in requested_formats or artifact_plan.word_source == "html":
        ensure_html(minimal_theme=("html" not in requested_formats and artifact_plan.word_source == "html"))

    docx_path = build_word_artifact(
        cfg=cfg,
        target_model=target_model,
        target_region=target_region,
        requested_formats=requested_formats,
        pdf_mode=pdf_mode,
        plan=artifact_plan,
        bundle=bundle,
        resolve_output_path=resolve_output_path,
        ensure_html=ensure_html,
        ensure_latex=ensure_latex,
        export_word_from_bundle=export_word_from_bundle,
        export_word_from_html=export_word_from_html,
        export_word_from_latex=export_word_from_latex,
        open_file=open_file,
        printer=printer,
    )

    build_pdf_artifact(
        cfg=cfg,
        target_model=target_model,
        target_region=target_region,
        requested_formats=requested_formats,
        pdf_mode=pdf_mode,
        plan=artifact_plan,
        bundle=bundle,
        docx_path=docx_path,
        resolve_output_path=resolve_output_path,
        ensure_latex=ensure_latex,
        export_word_from_bundle=export_word_from_bundle,
        export_pdf_from_docx_via_word=export_pdf_from_docx_via_word,
        copy_file=copy_file,
        open_file=open_file,
        printer=printer,
    )

    build_markdown_artifact(
        cfg=cfg,
        target_model=target_model,
        target_region=target_region,
        requested_formats=requested_formats,
        plan=artifact_plan,
        bundle=bundle,
        resolve_output_path=resolve_output_path,
        export_markdown_from_bundle=export_markdown_from_bundle,
        open_file=open_file,
        printer=printer,
    )

    finalize_html_artifact(
        requested_formats=requested_formats,
        html_built=html_built,
        plan=artifact_plan,
        target_model=target_model,
        target_region=target_region,
        target_lang=target_lang,
        bundle_title=bundle.title,
        strip_html_cover_section=strip_html_cover_section,
        write_html_manual_meta=write_html_manual_meta,
        refresh_model_html_switchers=refresh_model_html_switchers,
        open_file=open_file,
        printer=printer,
    )
