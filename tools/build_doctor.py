from __future__ import annotations

import argparse
import glob
import importlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


class SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def doctor_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return False, str(exc)
    return True, ""


def render_finding(finding: Any) -> str:
    return f"[doctor] {finding.level:<5} {finding.area}: {finding.message}"


def slug_token(value: str | None) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", "", text)


def render_config_tokenized_value(value: str, model: str | None, region: str | None) -> str:
    context = SafeFormatDict(
        model=model or "",
        region=region or "",
        model_slug=slug_token(model),
        region_slug=slug_token(region),
    )
    try:
        return value.format_map(context)
    except Exception:
        return value


def is_windows_platform(platform: str | None = None) -> bool:
    current_platform = sys.platform if platform is None else platform
    return current_platform.startswith("win")


def find_xelatex(*, find_exe: Callable[[list[str]], str | None]) -> str | None:
    return find_exe(["xelatex"])


def check_word_com_available(
    *,
    repo_root: Path,
    is_windows_platform: Callable[[], bool],
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., Any] = subprocess.run,
) -> tuple[bool, str]:
    if not is_windows_platform():
        return False, "Word COM check is only available on Windows"

    powershell = which("powershell")
    if not powershell:
        return False, "powershell not found in PATH"

    script = (
        "$ErrorActionPreference='Stop'; "
        "$word = New-Object -ComObject Word.Application; "
        "$word.Visible = $false; "
        "$word.Quit()"
    )
    try:
        run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            check=True,
            cwd=str(repo_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=20,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return False, "timed out while creating Word COM object"
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or "unable to create Word COM object"
        return False, detail
    return True, "Microsoft Word COM automation is available"


def resolve_doctor_target(
    cfg: dict,
    args: argparse.Namespace,
    *,
    resolve_build_model: Callable[[dict, str | None], str | None],
    resolve_build_region: Callable[[dict, str | None], str | None],
) -> tuple[str | None, str | None]:
    return resolve_build_model(cfg, args.model), resolve_build_region(cfg, args.region)


def resolve_doctor_pdf_mode(cfg: dict, cli_pdf_mode: str | None, *, valid_pdf_modes: set[str]) -> str:
    if cli_pdf_mode and cli_pdf_mode.strip():
        mode = cli_pdf_mode.strip().lower()
    else:
        pdf_cfg_raw = cfg.get("pdf", {})
        pdf_cfg = pdf_cfg_raw if isinstance(pdf_cfg_raw, dict) else {}
        mode = str(pdf_cfg.get("mode", "latex")).strip().lower()
    if mode not in valid_pdf_modes:
        raise RuntimeError(f"Unsupported pdf mode: {mode}")
    return mode


def resolve_reference_doc_status(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    repo_root: Path,
    finding_cls: type[Any],
    render_config_tokenized_value: Callable[[str, str | None, str | None], str],
    glob_matches: Callable[[str], list[str]] = glob.glob,
) -> Any | None:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    reference_raw = build_cfg.get("word_reference_doc")
    if not isinstance(reference_raw, str) or not reference_raw.strip():
        return None

    rendered = render_config_tokenized_value(reference_raw.strip(), model, region)
    if any(ch in rendered for ch in "*?["):
        pattern = rendered
        if not Path(pattern).is_absolute():
            pattern = str(repo_root / pattern)
        matches = sorted(glob_matches(pattern))
        if matches:
            return finding_cls("OK", "word.reference_doc", f"matched {matches[0]}")
        return finding_cls("ERROR", "word.reference_doc", f"no files matched: {rendered}")

    path = Path(rendered)
    if not path.is_absolute():
        path = repo_root / path
    if path.exists():
        return finding_cls("OK", "word.reference_doc", f"found {path}")
    return finding_cls("ERROR", "word.reference_doc", f"not found: {path}")


def collect_doctor_findings(
    args: argparse.Namespace,
    *,
    finding_cls: type[Any],
    resolve_path_from_root: Callable[[str], Path],
    load_validate_yaml: Callable[[Path], dict],
    validate_cfg: Callable[..., list[Any]],
    validate_layout: Callable[[Path], list[Any]],
    resolve_layout_params_csv: Callable[[Path], Path],
    doctor_add: Callable[[list[Any], str, str, str], None],
    doctor_import: Callable[[str], tuple[bool, str]],
    resolve_doctor_target: Callable[[dict, argparse.Namespace], tuple[str | None, str | None]],
    resolve_reference_doc_status: Callable[..., Any | None],
    is_windows_platform: Callable[[], bool],
    check_word_com_available: Callable[[], tuple[bool, str]],
    find_xelatex: Callable[[], str | None],
    resolve_doctor_pdf_mode: Callable[[dict, str | None], str],
    clean_targets_for_config: Callable[[Path], tuple[Path, Path]],
    which: Callable[[str], str | None] = shutil.which,
) -> list[Any]:
    findings: list[Any] = []
    config_path = resolve_path_from_root(args.config)

    try:
        cfg = load_validate_yaml(config_path)
    except Exception as exc:
        doctor_add(findings, "ERROR", "config", f"failed to load {config_path}: {exc}")
        return findings

    doctor_add(findings, "OK", "config", f"loaded {config_path}")

    config_issues = validate_cfg(cfg, strict_files=False)
    if not config_issues:
        doctor_add(findings, "OK", "validate_config", "config structure is valid")
    else:
        for issue in config_issues:
            level = "ERROR" if issue.level == "ERROR" else "WARN"
            doctor_add(findings, level, "validate_config", issue.msg)

    layout_csv = resolve_layout_params_csv(config_path)
    layout_issues = validate_layout(layout_csv)
    if not layout_issues:
        doctor_add(findings, "OK", "layout_params", f"validated {layout_csv}")
    else:
        for issue in layout_issues:
            level = "ERROR" if issue.level == "ERROR" else "WARN"
            doctor_add(findings, level, "layout_params", issue.msg)

    required_modules = [
        ("yaml", "python", "PyYAML available"),
        ("sphinx", "python", "Sphinx available"),
        ("docutils", "python", "docutils available"),
    ]
    optional_modules = [
        ("furo", "python.optional", "furo theme available"),
        ("PIL", "python.optional", "Pillow available"),
        ("numpy", "python.optional", "numpy available"),
    ]
    for module_name, area, ok_message in required_modules:
        ok, detail = doctor_import(module_name)
        if ok:
            doctor_add(findings, "OK", area, ok_message)
        else:
            doctor_add(findings, "ERROR", area, f"missing module '{module_name}': {detail}")
    for module_name, area, ok_message in optional_modules:
        ok, detail = doctor_import(module_name)
        if ok:
            doctor_add(findings, "OK", area, ok_message)
        else:
            doctor_add(findings, "WARN", area, f"missing optional module '{module_name}': {detail}")

    model, region = resolve_doctor_target(cfg, args)
    doctor_add(findings, "OK", "target", f"effective target model='{model or ''}' region='{region or ''}'")

    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    word_source = str(build_cfg.get("word_source", "bundle")).strip().lower()
    doctor_add(findings, "OK", "word", f"word_source={word_source}")

    reference_doc_status = resolve_reference_doc_status(cfg, model=model, region=region)
    if reference_doc_status is not None:
        findings.append(reference_doc_status)

    pandoc = which("pandoc")
    if word_source == "bundle":
        if is_windows_platform():
            ok, detail = check_word_com_available()
            doctor_add(findings, "OK" if ok else "ERROR", "word.runtime", detail)
            if pandoc:
                doctor_add(findings, "OK", "word.pandoc", f"found {pandoc} (optional for bundle on Windows)")
            else:
                doctor_add(findings, "WARN", "word.pandoc", "pandoc not found; okay for bundle on Windows, but html/latex export will fail")
        else:
            if pandoc:
                doctor_add(findings, "OK", "word.pandoc", f"found {pandoc}")
            else:
                doctor_add(findings, "ERROR", "word.pandoc", "pandoc not found; required for bundle export on non-Windows")
    elif word_source == "html":
        if pandoc:
            doctor_add(findings, "OK", "word.pandoc", f"found {pandoc}")
        else:
            doctor_add(findings, "ERROR", "word.pandoc", "pandoc not found; required for word_source=html")
    elif word_source == "latex":
        if pandoc:
            doctor_add(findings, "OK", "word.pandoc", f"found {pandoc}")
        else:
            doctor_add(findings, "ERROR", "word.pandoc", "pandoc not found; required for word_source=latex")
        xelatex = find_xelatex()
        if xelatex:
            doctor_add(findings, "OK", "word.xelatex", f"found {xelatex}")
        else:
            doctor_add(findings, "ERROR", "word.xelatex", "xelatex not found; required for word_source=latex")
    else:
        doctor_add(findings, "ERROR", "word", "build.word_source must be one of bundle/html/latex")

    try:
        pdf_mode = resolve_doctor_pdf_mode(cfg, args.pdf_mode)
        doctor_add(findings, "OK", "pdf", f"pdf_mode={pdf_mode}")
    except RuntimeError as exc:
        doctor_add(findings, "ERROR", "pdf", str(exc))
        return findings

    _build_dir, params_tex = clean_targets_for_config(config_path)
    tools_cfg_raw = cfg.get("tools", {})
    tools_cfg = tools_cfg_raw if isinstance(tools_cfg_raw, dict) else {}
    patch_fonts_script = tools_cfg.get("patch_fonts")

    if pdf_mode == "latex":
        xelatex = find_xelatex()
        if xelatex:
            doctor_add(findings, "OK", "pdf.xelatex", f"found {xelatex}")
        else:
            doctor_add(findings, "ERROR", "pdf.xelatex", "xelatex not found; required for pdf.mode=latex")

        if params_tex.exists():
            doctor_add(findings, "OK", "pdf.params_tex", f"found {params_tex}")
        else:
            doctor_add(findings, "ERROR", "pdf.params_tex", f"missing {params_tex}; run python tools/csv_to_tex_params.py")

        if isinstance(patch_fonts_script, str) and patch_fonts_script.strip():
            patch_path = resolve_path_from_root(patch_fonts_script.strip())
            if patch_path.exists():
                doctor_add(findings, "OK", "pdf.patch_fonts", f"found {patch_path}")
            else:
                doctor_add(findings, "ERROR", "pdf.patch_fonts", f"missing {patch_path}")
    else:
        if not is_windows_platform():
            doctor_add(findings, "ERROR", "pdf.runtime", "pdf.mode=word is only supported on Windows")
        else:
            ok, detail = check_word_com_available()
            doctor_add(findings, "OK" if ok else "ERROR", "pdf.runtime", detail)

    return findings


def run_doctor(
    args: argparse.Namespace,
    *,
    collect_doctor_findings: Callable[[argparse.Namespace], list[Any]],
    render_finding: Callable[[Any], str],
    printer: Callable[[str], None] = print,
) -> None:
    findings = collect_doctor_findings(args)
    for finding in findings:
        printer(render_finding(finding))

    errors = sum(1 for finding in findings if finding.level == "ERROR")
    warnings = sum(1 for finding in findings if finding.level == "WARN")
    printer(f"[doctor] SUMMARY errors={errors} warnings={warnings}")
    if errors:
        raise RuntimeError(f"doctor found {errors} blocking issue(s)")
