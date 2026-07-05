from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tools.utils.path_utils import docs_build_dir_of


def is_retryable_cleanup_error(exc: OSError, *, os_name: str) -> bool:
    if getattr(exc, "winerror", None) == 32:
        return True
    if isinstance(exc, PermissionError):
        if os_name == "nt":
            return True
        message = str(exc).lower()
        return "file in use" in message or "resource busy" in message
    return False


def remove_tree_with_retries(
    path: Path,
    *,
    remove_tree: Callable[[Path], None],
    sleep: Callable[[float], None],
    retry_delays: tuple[float, ...],
    is_retryable_cleanup_error: Callable[[OSError], bool],
    printer: Callable[[str], None] = print,
) -> None:
    last_exc: OSError | None = None
    retry_count = len(retry_delays)

    for attempt in range(retry_count + 1):
        try:
            remove_tree(path)
            return
        except FileNotFoundError:
            return
        except OSError as exc:
            if not is_retryable_cleanup_error(exc):
                raise
            last_exc = exc
            if attempt >= retry_count:
                break
            delay = retry_delays[attempt]
            printer(
                "[build] Cleanup blocked by an open handle; "
                f"retrying in {delay:.1f}s ({attempt + 1}/{retry_count})..."
            )
            sleep(delay)

    raise RuntimeError(
        "Could not clean build output: "
        f"{path}. Another program is still using this folder, or Windows has not released the handle yet. "
        "Close any File Explorer, browser, Word, or PDF windows pointing at docs/_build and rerun. "
        "If you only need to rebuild in place, rerun with --no-clean."
    ) from last_exc


def clean_build_targets(
    targets: list[Any],
    *,
    docs_dir: Path,
    preview_name: str | None,
    build_root_for_target: Callable[..., Path],
    cleanup_legacy_rst_artifacts: Callable[..., None],
    remove_tree_with_retries: Callable[[Path], None],
    output_root: Path | None = None,
    printer: Callable[[str], None] = print,
) -> None:
    # A preview writes straight into output_root, which already encodes the
    # (possibly staged) docs_build_dir + model/region/preview/page. Clean exactly
    # that, so a `preview --staging-root` cleans the staged preview dir instead of
    # the repo's default docs/_build preview dir (and never leaves the staged one
    # stale).
    if output_root is not None:
        if output_root.exists():
            printer(f"[build] Cleaning preview output: {output_root}")
            remove_tree_with_retries(output_root)
        return

    actual_docs_build_dir = docs_build_dir_of(docs_dir)

    for target in targets:
        target_build_root = build_root_for_target(
            target.model,
            target.region,
            target.lang,
            docs_build_dir=actual_docs_build_dir,
            preview_name=preview_name,
        )
        if target_build_root.exists():
            printer(f"[build] Cleaning target output: {target_build_root}")
            remove_tree_with_retries(target_build_root)

        if preview_name is None:
            cleanup_legacy_rst_artifacts(
                docs_dir=docs_dir,
                model=target.model,
                region=target.region,
            )


def sphinx_build(
    builder: str,
    *,
    src_dir: Path,
    out_dir: Path,
    conf_dir: Path,
    model: str | None = None,
    region: str | None = None,
    lang: str | None = None,
    minimal_theme: bool = False,
    substitutions: dict[str, str] | None = None,
    should_use_minimal_html_theme: Callable[[Path, bool], bool],
    resolve_sphinx_build_cmd: Callable[[str], list[str]],
    sphinx_tag_args: Callable[..., list[str]],
    with_rst_epilog: Callable[[list[str], dict[str, str] | None], list[str]],
    run: Callable[..., None],
    repo_root: Path,
    printer: Callable[[str], None] = print,
) -> None:
    printer(f"[build] Sphinx -> {builder.upper()}")
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_minimal_theme = should_use_minimal_html_theme(conf_dir, minimal_theme) if builder == "html" else False
    cmd = resolve_sphinx_build_cmd(builder) + sphinx_tag_args(model=model, region=region, lang=lang)
    cmd += [str(src_dir), str(out_dir), "-c", str(conf_dir)]
    if builder == "html" and actual_minimal_theme:
        cmd += [
            "-D",
            "html_theme=alabaster",
        ]
    cmd = with_rst_epilog(cmd, substitutions)
    run(cmd, cwd=repo_root)


def patch_fonts(
    patch_fonts_script: str,
    main_tex: str,
    *,
    build_dir: Path,
    run: Callable[..., None],
    repo_root: Path,
    python_executable: str,
    printer: Callable[[str], None] = print,
) -> None:
    printer("[build] Patch fonts (inject fonts.tex)")
    run(
        [
            python_executable,
            patch_fonts_script,
            "--tex",
            main_tex,
            "--build-dir",
            str(build_dir),
        ],
        cwd=repo_root,
    )


def export_word_from_latex(
    tex_path: Path,
    *,
    resource_dir: Path,
    out_path: Path,
    which: Callable[[str], str | None],
    run: Callable[..., None],
    repo_root: Path,
    printer: Callable[[str], None] = print,
) -> Path:
    pandoc = which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")
    if not tex_path.exists():
        raise RuntimeError(f"LaTeX source not found for Word export: {tex_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    printer("[build] Convert LaTeX -> DOCX")
    run(
        [
            pandoc,
            str(tex_path),
            "--from=latex",
            "--to=docx",
            "--resource-path",
            str(resource_dir),
            "-o",
            str(out_path),
        ],
        cwd=repo_root,
    )
    return out_path


def export_word_from_html(
    html_index: Path,
    *,
    out_path: Path,
    which: Callable[[str], str | None],
    run: Callable[..., None],
    repo_root: Path,
    printer: Callable[[str], None] = print,
) -> Path:
    pandoc = which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")
    if not html_index.exists():
        raise RuntimeError(f"HTML source not found for Word export: {html_index}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    printer("[build] Convert HTML -> DOCX")
    run(
        [
            pandoc,
            str(html_index),
            "--from=html",
            "--to=docx",
            "--resource-path",
            str(html_index.parent),
            "-o",
            str(out_path),
        ],
        cwd=repo_root,
    )
    return out_path


def export_pdf_from_docx_via_word(
    docx_path: Path,
    pdf_path: Path,
    *,
    platform: str,
    run_subprocess: Callable[..., Any],
    repo_root: Path,
) -> Path:
    if not platform.startswith("win"):
        raise RuntimeError("pdf mode 'word' is supported on Windows only")
    if not docx_path.exists():
        raise RuntimeError(f"DOCX source not found for PDF export: {docx_path}")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    docx_literal = str(docx_path).replace("'", "''")
    pdf_literal = str(pdf_path).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$docxPath = '{docx_literal}'
$pdfPath = '{pdf_literal}'
$word = $null
$doc = $null
$wdFormatPDF = 17
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $doc = $word.Documents.Open($docxPath, $false, $true)
    $doc.SaveAs([ref]$pdfPath, [ref]$wdFormatPDF)
}} finally {{
    if ($doc) {{
        $doc.Close([ref]$false)
    }}
    if ($word) {{
        $word.Quit()
    }}
}}
"""
    run_subprocess(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=True,
        cwd=str(repo_root),
    )
    return pdf_path
