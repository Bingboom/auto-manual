#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import glob
import importlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = "config.yaml"
BUILD_ACTIONS = ("rst", "word", "html", "pdf", "all")
ALL_OUTPUT_FORMATS = "html,word,pdf"
REVIEW_TRACKED_ROOT = "docs/_review/JE-1000F"
REVIEW_REPORT_DIR = "reports/version_tracking/JE-1000F"
VALID_PDF_MODES = {"latex", "word"}


@dataclass
class DoctorFinding:
    level: str
    area: str
    message: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Cross-platform build entrypoint for Auto-Manual.",
    )
    ap.add_argument(
        "action",
        choices=("validate", "doctor", *BUILD_ACTIONS, "review", "check", "sync-review", "publish", "clean", "diff-report"),
        help="Action to run",
    )
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="Config YAML path, relative to repo root by default")
    ap.add_argument("--model", default=None, help="Build a single model instead of build.targets")
    ap.add_argument("--region", default=None, help="Build a single region instead of build.targets")
    ap.add_argument(
        "--source",
        choices=("auto", "runtime", "review"),
        default="auto",
        help="Content source for build actions: auto, runtime, or review",
    )
    ap.add_argument("--pdf-mode", choices=("latex", "word"), default=None, help="Override PDF backend")
    ap.add_argument("--open", action="store_true", help="Allow opening generated artifacts after build")
    ap.add_argument("--no-clean", action="store_true", help="Skip cleaning current target outputs before build")
    ap.add_argument(
        "--refresh-review",
        action="store_true",
        help="Refresh an existing review bundle from the runtime template/data output",
    )
    ap.add_argument(
        "--sync-scope",
        choices=("generated", "params"),
        default="params",
        help="For sync-review: generated = spec/safety only; params = generated plus placeholder/cover pages",
    )
    ap.add_argument(
        "--page-file",
        action="append",
        default=[],
        help="For sync-review: extra review page file name to sync from runtime/page",
    )
    ap.add_argument("--tracked-root", default=REVIEW_TRACKED_ROOT, help="Tracked subtree for diff-report")
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref for diff-report")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref for diff-report")
    ap.add_argument(
        "--ignore-initial-adds",
        action="store_true",
        help="Ignore initial all-Added rows when the tracked subtree is first introduced",
    )
    ap.add_argument(
        "--report-dir",
        default=REVIEW_REPORT_DIR,
        help="Output directory for diff-report CSV/HTML",
    )
    return ap.parse_args(argv)


def resolve_path_from_root(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def load_config(config_path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc

    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as exc:
        raise RuntimeError(f"Failed to load config: {config_path}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"Config root must be a mapping: {config_path}")
    return data


def resolve_layout_params_csv(config_path: Path) -> Path:
    cfg = load_config(config_path)
    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        raw = paths_cfg.get("layout_params_csv")
        if isinstance(raw, str) and raw.strip():
            return resolve_path_from_root(raw.strip())
    return ROOT / "data" / "layout_params.csv"


def resolve_docs_dir(config_path: Path) -> Path:
    try:
        cfg = load_config(config_path)
    except RuntimeError:
        return ROOT / "docs"

    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        raw = paths_cfg.get("docs_dir")
        if isinstance(raw, str) and raw.strip():
            return resolve_path_from_root(raw.strip())
    return ROOT / "docs"


def clean_targets_for_config(config_path: Path) -> tuple[Path, Path]:
    docs_dir = resolve_docs_dir(config_path)
    return docs_dir / "_build", docs_dir / "renderers" / "latex" / "params.tex"


def review_root_for_config(config_path: Path) -> Path:
    docs_dir = resolve_docs_dir(config_path)
    return docs_dir / "_review"


def is_legacy_bundle_dir(path: Path) -> bool:
    return path.is_dir() and (path / "index.rst").exists() and (path / "page").is_dir()


def collect_legacy_docs_output_dirs(docs_dir: Path) -> list[Path]:
    if not docs_dir.exists():
        return []

    legacy_dirs: list[Path] = []
    generated_dir = docs_dir / "generated"
    if generated_dir.exists():
        legacy_dirs.append(generated_dir)

    reserved = {"_build", "_static", "renderers", "templates", "__pycache__"}
    for child in docs_dir.iterdir():
        if not child.is_dir() or child.name in reserved or child == generated_dir:
            continue
        if is_legacy_bundle_dir(child):
            legacy_dirs.append(child)
            continue
        subdirs = [item for item in child.iterdir() if item.is_dir()]
        if subdirs and all(is_legacy_bundle_dir(item) for item in subdirs):
            legacy_dirs.append(child)
    return legacy_dirs


def format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def run_checked(cmd: list[str]) -> None:
    print(f"[build.py] {format_command(cmd)}")
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def _append_target_args(cmd: list[str], args: argparse.Namespace) -> list[str]:
    if args.model:
        cmd += ["--model", args.model]
    if args.region:
        cmd += ["--region", args.region]
    if not (args.model or args.region):
        cmd.append("--all-targets")
    return cmd


def build_docs_command(
    args: argparse.Namespace,
    *,
    action_override: str | None = None,
    source_override: str | None = None,
) -> list[str]:
    action = action_override or args.action
    if action not in BUILD_ACTIONS:
        raise RuntimeError(f"Action '{action}' is not a build action")

    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "build_docs.py"),
        "--config",
        str(config_path),
    ]
    _append_target_args(cmd, args)
    cmd += ["--source", source_override or args.source]

    if action == "rst":
        cmd.append("--prepare-only")
    elif action == "all":
        cmd += ["--formats", ALL_OUTPUT_FORMATS]
    else:
        cmd += ["--formats", action]

    if args.pdf_mode:
        cmd += ["--pdf-mode", args.pdf_mode]
    if not args.no_clean:
        cmd.append("--clean")
    if not args.open:
        cmd.append("--no-open")
    return cmd


def review_bundle_command(args: argparse.Namespace) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "review_bundle.py"),
        "--config",
        str(config_path),
    ]
    _append_target_args(cmd, args)
    if args.refresh_review:
        cmd.append("--refresh-existing")
    return cmd


def check_docs_command(args: argparse.Namespace) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "check_docs.py"),
        "--config",
        str(config_path),
    ]
    return _append_target_args(cmd, args)


def sync_review_command(args: argparse.Namespace) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "sync_review.py"),
        "--config",
        str(config_path),
        "--sync-scope",
        args.sync_scope,
    ]
    _append_target_args(cmd, args)
    for page_file in args.page_file:
        cmd += ["--page-file", page_file]
    return cmd


def run_validate(config_path: Path) -> None:
    run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_config.py"),
            "--config",
            str(config_path),
        ]
    )
    run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_layout_params.py"),
            "--csv",
            str(resolve_layout_params_csv(config_path)),
        ]
    )


def _doctor_add(findings: list[DoctorFinding], level: str, area: str, message: str) -> None:
    findings.append(DoctorFinding(level=level, area=area, message=message))


def _doctor_render_finding(finding: DoctorFinding) -> str:
    return f"[doctor] {finding.level:<5} {finding.area}: {finding.message}"


def _doctor_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return False, str(exc)
    return True, ""


def _slug_token(value: str | None) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", "", text)


class _SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render_config_tokenized_value(value: str, model: str | None, region: str | None) -> str:
    context = _SafeFormatDict(
        model=model or "",
        region=region or "",
        model_slug=_slug_token(model),
        region_slug=_slug_token(region),
    )
    try:
        return value.format_map(context)
    except Exception:
        return value


def _is_windows_platform() -> bool:
    return sys.platform.startswith("win")


def _find_xelatex() -> str | None:
    from tools.utils.process_utils import find_exe

    return find_exe(["xelatex"])


def _check_word_com_available() -> tuple[bool, str]:
    if not _is_windows_platform():
        return False, "Word COM check is only available on Windows"

    powershell = shutil.which("powershell")
    if not powershell:
        return False, "powershell not found in PATH"

    script = (
        "$ErrorActionPreference='Stop'; "
        "$word = New-Object -ComObject Word.Application; "
        "$word.Visible = $false; "
        "$word.Quit()"
    )
    try:
        subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            check=True,
            cwd=str(ROOT),
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


def _resolve_doctor_target(cfg: dict, args: argparse.Namespace) -> tuple[str | None, str | None]:
    from tools.utils.targets import resolve_build_model, resolve_build_region

    return resolve_build_model(cfg, args.model), resolve_build_region(cfg, args.region)


def _resolve_doctor_pdf_mode(cfg: dict, cli_pdf_mode: str | None) -> str:
    if cli_pdf_mode and cli_pdf_mode.strip():
        mode = cli_pdf_mode.strip().lower()
    else:
        pdf_cfg_raw = cfg.get("pdf", {})
        pdf_cfg = pdf_cfg_raw if isinstance(pdf_cfg_raw, dict) else {}
        mode = str(pdf_cfg.get("mode", "latex")).strip().lower()
    if mode not in VALID_PDF_MODES:
        raise RuntimeError(f"Unsupported pdf mode: {mode}")
    return mode


def _resolve_reference_doc_status(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
) -> DoctorFinding | None:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    reference_raw = build_cfg.get("word_reference_doc")
    if not isinstance(reference_raw, str) or not reference_raw.strip():
        return None

    rendered = _render_config_tokenized_value(reference_raw.strip(), model, region)
    if any(ch in rendered for ch in "*?["):
        pattern = rendered
        if not Path(pattern).is_absolute():
            pattern = str(ROOT / pattern)
        matches = sorted(glob.glob(pattern))
        if matches:
            return DoctorFinding("OK", "word.reference_doc", f"matched {matches[0]}")
        return DoctorFinding("ERROR", "word.reference_doc", f"no files matched: {rendered}")

    path = Path(rendered)
    if not path.is_absolute():
        path = ROOT / path
    if path.exists():
        return DoctorFinding("OK", "word.reference_doc", f"found {path}")
    return DoctorFinding("ERROR", "word.reference_doc", f"not found: {path}")


def _collect_doctor_findings(args: argparse.Namespace) -> list[DoctorFinding]:
    from tools.validate_config import load_yaml as load_validate_yaml
    from tools.validate_config import validate as validate_cfg
    from tools.validate_layout_params import validate as validate_layout

    findings: list[DoctorFinding] = []
    config_path = resolve_path_from_root(args.config)

    try:
        cfg = load_validate_yaml(config_path)
    except Exception as exc:
        _doctor_add(findings, "ERROR", "config", f"failed to load {config_path}: {exc}")
        return findings

    _doctor_add(findings, "OK", "config", f"loaded {config_path}")

    config_issues = validate_cfg(cfg, strict_files=False)
    config_errors = [issue for issue in config_issues if issue.level == "ERROR"]
    config_warnings = [issue for issue in config_issues if issue.level == "WARN"]
    if not config_issues:
        _doctor_add(findings, "OK", "validate_config", "config structure is valid")
    else:
        for issue in config_warnings:
            _doctor_add(findings, "WARN", "validate_config", issue.msg)
        for issue in config_errors:
            _doctor_add(findings, "ERROR", "validate_config", issue.msg)

    layout_csv = resolve_layout_params_csv(config_path)
    layout_issues = validate_layout(layout_csv)
    layout_errors = [issue for issue in layout_issues if issue.level == "ERROR"]
    if not layout_issues:
        _doctor_add(findings, "OK", "layout_params", f"validated {layout_csv}")
    else:
        for issue in layout_issues:
            level = "ERROR" if issue.level == "ERROR" else "WARN"
            _doctor_add(findings, level, "layout_params", issue.msg)

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
        ok, detail = _doctor_import(module_name)
        if ok:
            _doctor_add(findings, "OK", area, ok_message)
        else:
            _doctor_add(findings, "ERROR", area, f"missing module '{module_name}': {detail}")
    for module_name, area, ok_message in optional_modules:
        ok, detail = _doctor_import(module_name)
        if ok:
            _doctor_add(findings, "OK", area, ok_message)
        else:
            _doctor_add(findings, "WARN", area, f"missing optional module '{module_name}': {detail}")

    model, region = _resolve_doctor_target(cfg, args)
    _doctor_add(
        findings,
        "OK",
        "target",
        f"effective target model='{model or ''}' region='{region or ''}'",
    )

    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    word_source = str(build_cfg.get("word_source", "bundle")).strip().lower()
    _doctor_add(findings, "OK", "word", f"word_source={word_source}")

    reference_doc_status = _resolve_reference_doc_status(cfg, model=model, region=region)
    if reference_doc_status is not None:
        findings.append(reference_doc_status)

    pandoc = shutil.which("pandoc")
    if word_source == "bundle":
        if _is_windows_platform():
            ok, detail = _check_word_com_available()
            _doctor_add(findings, "OK" if ok else "ERROR", "word.runtime", detail)
            if pandoc:
                _doctor_add(findings, "OK", "word.pandoc", f"found {pandoc} (optional for bundle on Windows)")
            else:
                _doctor_add(findings, "WARN", "word.pandoc", "pandoc not found; okay for bundle on Windows, but html/latex export will fail")
        else:
            if pandoc:
                _doctor_add(findings, "OK", "word.pandoc", f"found {pandoc}")
            else:
                _doctor_add(findings, "ERROR", "word.pandoc", "pandoc not found; required for bundle export on non-Windows")
    elif word_source == "html":
        if pandoc:
            _doctor_add(findings, "OK", "word.pandoc", f"found {pandoc}")
        else:
            _doctor_add(findings, "ERROR", "word.pandoc", "pandoc not found; required for word_source=html")
    elif word_source == "latex":
        if pandoc:
            _doctor_add(findings, "OK", "word.pandoc", f"found {pandoc}")
        else:
            _doctor_add(findings, "ERROR", "word.pandoc", "pandoc not found; required for word_source=latex")
        xelatex = _find_xelatex()
        if xelatex:
            _doctor_add(findings, "OK", "word.xelatex", f"found {xelatex}")
        else:
            _doctor_add(findings, "ERROR", "word.xelatex", "xelatex not found; required for word_source=latex")
    else:
        _doctor_add(findings, "ERROR", "word", "build.word_source must be one of bundle/html/latex")

    try:
        pdf_mode = _resolve_doctor_pdf_mode(cfg, args.pdf_mode)
        _doctor_add(findings, "OK", "pdf", f"pdf_mode={pdf_mode}")
    except RuntimeError as exc:
        _doctor_add(findings, "ERROR", "pdf", str(exc))
        return findings

    _build_dir, params_tex = clean_targets_for_config(config_path)
    tools_cfg_raw = cfg.get("tools", {})
    tools_cfg = tools_cfg_raw if isinstance(tools_cfg_raw, dict) else {}
    patch_fonts_script = tools_cfg.get("patch_fonts")

    if pdf_mode == "latex":
        xelatex = _find_xelatex()
        if xelatex:
            _doctor_add(findings, "OK", "pdf.xelatex", f"found {xelatex}")
        else:
            _doctor_add(findings, "ERROR", "pdf.xelatex", "xelatex not found; required for pdf.mode=latex")

        if params_tex.exists():
            _doctor_add(findings, "OK", "pdf.params_tex", f"found {params_tex}")
        else:
            _doctor_add(findings, "ERROR", "pdf.params_tex", f"missing {params_tex}; run python tools/csv_to_tex_params.py")

        if isinstance(patch_fonts_script, str) and patch_fonts_script.strip():
            patch_path = resolve_path_from_root(patch_fonts_script.strip())
            if patch_path.exists():
                _doctor_add(findings, "OK", "pdf.patch_fonts", f"found {patch_path}")
            else:
                _doctor_add(findings, "ERROR", "pdf.patch_fonts", f"missing {patch_path}")
    else:
        if not _is_windows_platform():
            _doctor_add(findings, "ERROR", "pdf.runtime", "pdf.mode=word is only supported on Windows")
        else:
            ok, detail = _check_word_com_available()
            _doctor_add(findings, "OK" if ok else "ERROR", "pdf.runtime", detail)

    return findings


def run_doctor(args: argparse.Namespace) -> None:
    findings = _collect_doctor_findings(args)
    for finding in findings:
        print(_doctor_render_finding(finding))

    errors = sum(1 for finding in findings if finding.level == "ERROR")
    warnings = sum(1 for finding in findings if finding.level == "WARN")
    print(f"[doctor] SUMMARY errors={errors} warnings={warnings}")
    if errors:
        raise RuntimeError(f"doctor found {errors} blocking issue(s)")


def run_diff_report(args: argparse.Namespace) -> None:
    run_diff_report_with_paths(
        args,
        tracked_root=resolve_path_from_root(args.tracked_root),
        report_dir=resolve_path_from_root(args.report_dir),
    )


def run_diff_report_with_paths(
    args: argparse.Namespace,
    *,
    tracked_root: Path,
    report_dir: Path,
) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "diff_report.py"),
        "--tracked-root",
        str(tracked_root),
        "--config",
        str(resolve_path_from_root(args.config)),
        "--from-ref",
        args.from_ref,
        "--to-ref",
        args.to_ref,
        "--output-dir",
        str(report_dir),
    ]
    if args.ignore_initial_adds:
        cmd.append("--ignore-initial-adds")
    run_checked(cmd)


def run_check(args: argparse.Namespace, *, source_override: str = "auto") -> None:
    config_path = resolve_path_from_root(args.config)
    run_validate(config_path)
    run_checked(build_docs_command(args, action_override="rst", source_override=source_override))
    run_checked(check_docs_command(args))


def _publish_target_components(args: argparse.Namespace) -> tuple[str, str, str | None]:
    model = (args.model or "").strip()
    region = (args.region or "").strip()
    if not model or not region:
        raise RuntimeError("publish requires --model and --region so the release target is explicit")
    from tools.utils.targets import resolve_output_lang

    cfg = load_config(resolve_path_from_root(args.config))
    return model, region, resolve_output_lang(cfg)


def _publish_tracked_root(args: argparse.Namespace) -> Path:
    model, region, lang = _publish_target_components(args)
    if args.tracked_root == REVIEW_TRACKED_ROOT:
        base = ROOT / "docs" / "_review" / model / region
        if (lang or "").strip():
            return base / lang
        return base
    return resolve_path_from_root(args.tracked_root)


def _publish_report_dir(args: argparse.Namespace) -> Path:
    model, region, lang = _publish_target_components(args)
    if args.report_dir == REVIEW_REPORT_DIR:
        base = ROOT / "reports" / "version_tracking" / model / region
        if (lang or "").strip():
            return base / lang
        return base
    return resolve_path_from_root(args.report_dir)


def run_publish(args: argparse.Namespace) -> None:
    tracked_root = _publish_tracked_root(args)
    report_dir = _publish_report_dir(args)
    run_check(args, source_override="review")
    run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)
    run_checked(build_docs_command(args, action_override="word", source_override="review"))


def clean_build_artifacts(config_path: Path, *, remove_params_tex: bool = True) -> None:
    build_dir, params_tex = clean_targets_for_config(config_path)
    review_dir = review_root_for_config(config_path)
    docs_dir = resolve_docs_dir(config_path)
    print(f"[build.py] remove {build_dir}")
    shutil.rmtree(build_dir, ignore_errors=True)
    print(f"[build.py] remove {review_dir}")
    shutil.rmtree(review_dir, ignore_errors=True)
    if remove_params_tex:
        print(f"[build.py] remove {params_tex}")
        params_tex.unlink(missing_ok=True)
    for legacy_dir in collect_legacy_docs_output_dirs(docs_dir):
        print(f"[build.py] remove {legacy_dir}")
        shutil.rmtree(legacy_dir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = resolve_path_from_root(args.config)

    try:
        if args.action == "validate":
            run_validate(config_path)
        elif args.action == "doctor":
            run_doctor(args)
        elif args.action == "review":
            run_checked(build_docs_command(args, action_override="rst", source_override="runtime"))
            run_checked(review_bundle_command(args))
        elif args.action == "check":
            run_check(args)
        elif args.action == "sync-review":
            run_checked(build_docs_command(args, action_override="rst", source_override="runtime"))
            run_checked(sync_review_command(args))
        elif args.action == "publish":
            run_publish(args)
        elif args.action == "diff-report":
            run_diff_report(args)
        elif args.action == "clean":
            clean_build_artifacts(config_path)
        else:
            run_checked(build_docs_command(args))
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    except RuntimeError as exc:
        print(f"[build.py] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
