"""Declarative Web package runner: pin verification, style audit, inventory, and build."""
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any

from tools.gen_index_bundle_models import MaterializedBundle
from tools.manual_ir import read_manual_ir, write_manual_ir
from tools.markdown_bundle import export_markdown_from_bundle
from tools.utils.path_utils import PathSegments
from tools.web.frozen_package_registry import SOURCE_MANIFEST_JSON, input_matches
from tools.web.package_inventory import (
    collect_inventory,
    extract_rst_refs_from_index,
    format_inventory_text,
    read_manifest,
    resolve_target_pair,
)
from tools.web.prepared_style_audit import (
    PREPARED_SOURCE,
    audit_prepared_package_locale,
    load_baseline,
    require_prepared_style_admission,
)
from tools.web.presentation import PRESENTATION_PROFILE_ENV, WEB_PRESENTATION_PROFILE

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _check_pin_group(
    base: Path,
    rows: Any,
    group: str,
    cache: dict[Path, tuple[str, ...]],
) -> tuple[int, list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], str | None]:
    if rows is None:
        return 0, [], [], [], None
    if not isinstance(rows, list):
        return 0, [], [], [], f"{group} must be a list"
    base_resolved = base.resolve()
    mismatches: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    traversal_errors: list[dict[str, str]] = []
    checked = 0
    for row in rows:
        if not isinstance(row, Mapping) or "path" not in row or "sha256" not in row:
            return (
                checked,
                mismatches,
                missing,
                traversal_errors,
                f"{group} entry requires path and sha256",
            )
        checked += 1
        rel_path = str(row["path"])
        expected = str(row["sha256"])
        if Path(rel_path).is_absolute():
            traversal_errors.append({"group": group, "path": rel_path})
            continue
        candidate = (base / rel_path).resolve()
        if not candidate.is_relative_to(base_resolved):
            traversal_errors.append({"group": group, "path": rel_path})
            continue
        if not candidate.is_file():
            missing.append({"group": group, "path": rel_path})
            continue
        if not input_matches(candidate, expected, cache):
            mismatches.append({"group": group, "path": rel_path, "expected": expected})
    return checked, mismatches, missing, traversal_errors, None


def verify_pins(
    package_dir: Path,
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
) -> dict[str, Any]:
    """Verify ``inputs`` and ``repo_inputs`` SHA-256 pins in ``source_manifest.json``."""
    package_dir = package_dir.resolve()
    manifest, error = read_manifest(package_dir / SOURCE_MANIFEST_JSON)
    if manifest is None:
        return {
            "ok": False,
            "package_dir": str(package_dir),
            "checked_inputs": 0,
            "checked_repo_inputs": 0,
            "mismatches": [],
            "missing": [],
            "traversal_errors": [],
            "error": error,
        }
    cache: dict[Path, tuple[str, ...]] = {}
    in_count, in_mis, in_miss, in_trav, in_err = _check_pin_group(
        package_dir, manifest.get("inputs"), "inputs", cache
    )
    repo_count, repo_mis, repo_miss, repo_trav, repo_err = _check_pin_group(
        repo_root.resolve(), manifest.get("repo_inputs"), "repo_inputs", cache
    )
    mismatches = [*in_mis, *repo_mis]
    missing = [*in_miss, *repo_miss]
    traversal_errors = [*in_trav, *repo_trav]
    combined_error = in_err or repo_err
    ok = (
        combined_error is None
        and not mismatches
        and not missing
        and not traversal_errors
    )
    return {
        "ok": ok,
        "package_dir": str(package_dir),
        "checked_inputs": in_count,
        "checked_repo_inputs": repo_count,
        "mismatches": mismatches,
        "missing": missing,
        "traversal_errors": traversal_errors,
        "error": combined_error,
    }


def _discover_audit_targets(
    package_dir: Path,
    lang: str | None,
) -> tuple[list[tuple[str, Path]], str | None]:
    web_root = package_dir / "web"
    if lang is not None:
        locale_dir = web_root / lang
        if not (locale_dir / PathSegments.MANUAL_IR_JSON).is_file():
            return [], f"missing {PathSegments.MANUAL_IR_JSON} for language {lang!r}"
        return [(lang, locale_dir)], None
    if not web_root.is_dir():
        return [], "no web/ directory in package"
    targets = [
        (path.parent.name, path.parent)
        for path in sorted(web_root.glob(f"*/{PathSegments.MANUAL_IR_JSON}"))
        if path.is_file()
    ]
    if not targets:
        return [], f"no sealed web/*/{PathSegments.MANUAL_IR_JSON} locales found"
    return targets, None


def _audit_single_locale(
    package_dir: Path,
    lang: str,
    locale_dir: Path,
    manifest: Mapping[str, Any],
    baseline_hashes: set[str] | None,
) -> dict[str, Any]:
    ir_path = locale_dir / PathSegments.MANUAL_IR_JSON
    try:
        raw = json.loads(ir_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "language": lang,
            "web_root": str(locale_dir),
            "ok": False,
            "baseline": False,
            "applicable": False,
            "issues": [f"unreadable {PathSegments.MANUAL_IR_JSON}: {exc}"],
        }
    if baseline_hashes is not None and raw.get("content_sha256") in baseline_hashes:
        return {
            "language": lang,
            "web_root": str(locale_dir),
            "ok": True,
            "baseline": True,
            "applicable": raw.get("source") == PREPARED_SOURCE,
            "issues": [],
        }
    try:
        report = audit_prepared_package_locale(package_dir, locale_dir, manifest)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "language": lang,
            "web_root": str(locale_dir),
            "ok": False,
            "baseline": False,
            "applicable": True,
            "issues": [str(exc)],
        }
    issues = [str(item) for item in report.get("issues", ())]
    return {
        "language": lang,
        "web_root": str(locale_dir),
        "ok": not issues,
        "baseline": False,
        "applicable": bool(report.get("applicable")),
        "model": report.get("model"),
        "region": report.get("region"),
        "declared_tables": int(report.get("declared_tables", 0)),
        "issues": issues,
    }


def audit_styles(
    package_dir: Path,
    *,
    lang: str | None = None,
    respect_baseline: bool = False,
) -> dict[str, Any]:
    """Audit shared Web styles for sealed ``web/<lang>/manual.ir.json`` locales."""
    package_dir = package_dir.resolve()
    manifest, manifest_error = read_manifest(package_dir / SOURCE_MANIFEST_JSON)
    if manifest is None:
        return {
            "ok": False,
            "package_dir": str(package_dir),
            "respect_baseline": respect_baseline,
            "locales": [],
            "error": manifest_error,
        }
    targets, target_error = _discover_audit_targets(package_dir, lang)
    if target_error is not None:
        return {
            "ok": False,
            "package_dir": str(package_dir),
            "respect_baseline": respect_baseline,
            "locales": [],
            "error": target_error,
        }
    baseline_hashes: set[str] | None = None
    if respect_baseline:
        baseline_hashes = {
            str(row.get("ir_content_sha256") or "")
            for row in load_baseline()["entries"]
        }
    locale_reports = [
        _audit_single_locale(package_dir, loc_lang, loc_dir, manifest, baseline_hashes)
        for loc_lang, loc_dir in targets
    ]
    return {
        "ok": bool(locale_reports) and all(item["ok"] for item in locale_reports),
        "package_dir": str(package_dir),
        "respect_baseline": respect_baseline,
        "locales": locale_reports,
        "error": None,
    }


def _extract_pages_for_lang(value: Any, lang: str) -> list[str] | None:
    if isinstance(value, list) and value:
        return [str(item) for item in value]
    if isinstance(value, Mapping):
        localized = value.get(lang)
        if isinstance(localized, list) and localized:
            return [str(item) for item in localized]
    return None


def _declarative_section(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("declarative_build", "build"):
        section = manifest.get(key)
        if isinstance(section, Mapping):
            return section
    return {}


def _resolve_page_entry(
    raw_entry: str,
    candidate_bases: tuple[Path, ...],
    package_root: Path,
) -> Path:
    if Path(raw_entry).is_absolute():
        raise ValueError(f"declarative page path must be relative: {raw_entry}")
    suffix_variants = (raw_entry,) if Path(raw_entry).suffix else (raw_entry, f"{raw_entry}.rst")
    for base in candidate_bases:
        for variant in suffix_variants:
            candidate = (base / variant).resolve()
            if not candidate.is_relative_to(package_root):
                raise ValueError(f"declarative page path escapes package: {raw_entry}")
            if candidate.is_file():
                return candidate
    raise ValueError(f"declarative page not found: {raw_entry}")


def resolve_declarative_pages(
    package_dir: Path,
    manifest: Mapping[str, Any],
    lang: str,
) -> tuple[Path, ...]:
    """Resolve ordered RST page paths for ``lang`` from manifest or ``index.rst``."""
    package_root = package_dir.resolve()
    section = _declarative_section(manifest)
    entries = (
        _extract_pages_for_lang(section.get("pages"), lang)
        or _extract_pages_for_lang(section.get("page_order"), lang)
        or _extract_pages_for_lang(manifest.get("pages"), lang)
        or _extract_pages_for_lang(manifest.get("page_order"), lang)
    )
    if entries is None:
        index_entries = extract_rst_refs_from_index(package_root / "source" / lang / "index.rst")
        entries = list(index_entries) if index_entries else None
    if not entries:
        raise ValueError(
            f"no declarative pages found for language {lang!r} in {SOURCE_MANIFEST_JSON} or source/{lang}/index.rst"
        )
    bases: list[Path] = []
    source_subdir = section.get("source_dir")
    if isinstance(source_subdir, str) and source_subdir.strip():
        custom_dir = (package_root / source_subdir.strip()).resolve()
        if not custom_dir.is_relative_to(package_root):
            raise ValueError(f"source_dir escapes package: {source_subdir}")
        bases.append(custom_dir)
    bases.extend(
        [
            package_root / "source" / lang,
            package_root / "source" / "page",
            package_root / "source",
            package_root,
        ]
    )
    return tuple(_resolve_page_entry(entry, tuple(bases), package_root) for entry in entries)


def _slug(value: str | None) -> str:
    if not value:
        return ""
    return _SLUG_RE.sub("", value.lower())


def _resolve_build_title(
    manifest: Mapping[str, Any],
    section: Mapping[str, Any],
    model: str | None,
    lang: str,
) -> str:
    identity = manifest.get("document_identity")
    identity_name = identity.get("product_name") if isinstance(identity, Mapping) else None
    for candidate in (
        section.get("title"),
        manifest.get("web_title"),
        manifest.get("title"),
        identity_name,
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return f"{model} ({lang})" if model else f"Manual ({lang})"


def _resolve_markdown_filename(
    manifest: Mapping[str, Any],
    section: Mapping[str, Any],
    model: str | None,
    region: str | None,
    lang: str,
) -> str:
    for candidate in (section.get("markdown_filename"), manifest.get("markdown_filename")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    parts = [p for p in ("manual", _slug(model), _slug(region), _slug(lang)) if p]
    return "_".join(parts) + ".md"


def _attach_source_stylesheet(
    package_dir: Path,
    output_dir: Path,
    manifest: Mapping[str, Any],
    section: Mapping[str, Any],
) -> None:
    sheet_rel = section.get("stylesheet") or manifest.get("source_stylesheet")
    if not isinstance(sheet_rel, str) or not sheet_rel.strip():
        return
    if Path(sheet_rel).is_absolute():
        raise ValueError(f"stylesheet must be package-relative: {sheet_rel}")
    sheet_src = (package_dir / sheet_rel).resolve()
    if not sheet_src.is_relative_to(package_dir.resolve()) or not sheet_src.is_file():
        raise ValueError(f"source stylesheet missing or escapes package: {sheet_rel}")
    style_text = sheet_src.read_text(encoding="utf-8")
    if "</style" in style_text.lower():
        raise ValueError(f"source stylesheet contains HTML: {sheet_rel}")
    static_dir = output_dir / "_static"
    static_dir.mkdir(parents=True, exist_ok=True)
    target = static_dir / sheet_src.name
    shutil.copy2(sheet_src, target)
    ir_path = output_dir / PathSegments.MANUAL_IR_JSON
    if ir_path.is_file():
        ir = read_manual_ir(ir_path)
        sheet_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        metadata = {
            **ir.metadata,
            "source_stylesheet": {"path": f"_static/{sheet_src.name}", "sha256": sheet_sha},
        }
        write_manual_ir(replace(ir, metadata=metadata), ir_path)
    conf_path = output_dir / "conf.py"
    if conf_path.is_file():
        with conf_path.open("a", encoding="utf-8") as stream:
            stream.write(f"\nhtml_css_files.append({sheet_src.name!r})\n")


def build_declarative_package(
    package_dir: Path,
    *,
    lang: str,
    output_dir: Path,
    repo_root: Path = DEFAULT_REPO_ROOT,
    skip_pin_check: bool = False,
) -> dict[str, Any]:
    """Build a declarative Web package into ``output_dir`` and run style admission."""
    package_dir = package_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ValueError(f"output directory already exists: {output_dir}")
    manifest, manifest_error = read_manifest(package_dir / SOURCE_MANIFEST_JSON)
    if manifest is None:
        raise ValueError(manifest_error or f"missing {SOURCE_MANIFEST_JSON}")
    if not skip_pin_check:
        pin_report = verify_pins(package_dir, repo_root=repo_root)
        if not pin_report["ok"]:
            raise ValueError(
                f"pin verification failed for {package_dir}: "
                f"mismatches={len(pin_report['mismatches'])}, "
                f"missing={len(pin_report['missing'])}, "
                f"traversal={len(pin_report['traversal_errors'])}"
            )
    page_paths = resolve_declarative_pages(package_dir, manifest, lang)
    section = _declarative_section(manifest)
    model, region = resolve_target_pair(manifest)
    title = _resolve_build_title(manifest, section, model, lang)
    markdown_filename = _resolve_markdown_filename(manifest, section, model, region, lang)
    source_root = package_dir / "source" / lang
    if not source_root.is_dir():
        source_root = (package_dir / "source") if (package_dir / "source").is_dir() else package_dir
    bundle = MaterializedBundle(
        bundle_dir=source_root,
        page_dir=page_paths[0].parent,
        index_path=source_root / "index.rst",
        conf_path=source_root / "conf.py",
        conf_base_path=source_root / "conf_base.py",
        wrapper_index_path=source_root / "index.rst",
        page_paths=page_paths,
        title=title,
        reference_doc=None,
        model=model,
        region=region,
        lang=lang,
        languages=(lang,),
    )
    cfg: dict[str, Any] = {}
    entry_patterns = section.get("entry_source_patterns")
    if isinstance(entry_patterns, list) and all(isinstance(p, str) for p in entry_patterns):
        cfg["build"] = {"web_entry_source_patterns": list(entry_patterns)}

    previous_profile = os.environ.get(PRESENTATION_PROFILE_ENV)
    os.environ[PRESENTATION_PROFILE_ENV] = WEB_PRESENTATION_PROFILE
    try:
        markdown_path = export_markdown_from_bundle(
            cfg,
            model,
            region,
            str(output_dir / markdown_filename),
            materialized_bundle=bundle,
            output_dir=output_dir,
        )
    finally:
        if previous_profile is None:
            os.environ.pop(PRESENTATION_PROFILE_ENV, None)
        else:
            os.environ[PRESENTATION_PROFILE_ENV] = previous_profile

    _attach_source_stylesheet(package_dir, output_dir, manifest, section)
    conf_path = output_dir / "conf.py"
    if conf_path.is_file():
        with conf_path.open("a", encoding="utf-8") as stream:
            stream.write(f"\nlanguage = {lang!r}\n")
    admission = require_prepared_style_admission(output_dir, manifest)
    return {
        "ok": True,
        "package_dir": str(package_dir),
        "output_dir": str(output_dir),
        "model": model,
        "region": region,
        "language": lang,
        "markdown_path": str(markdown_path),
        "manual_ir_path": str(output_dir / PathSegments.MANUAL_IR_JSON),
        "pages": [p.relative_to(package_dir).as_posix() for p in page_paths],
        "admission": admission,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_verify = subparsers.add_parser("verify-pins", help="Verify manifest SHA-256 pins.")
    p_verify.add_argument("package_dir", type=Path)
    p_verify.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    p_verify.add_argument("--json", action="store_true")

    p_audit = subparsers.add_parser("audit-styles", help="Audit sealed web locales.")
    p_audit.add_argument("package_dir", type=Path)
    p_audit.add_argument("--lang")
    p_audit.add_argument("--respect-baseline", action="store_true")
    p_audit.add_argument("--json", action="store_true")

    p_inv = subparsers.add_parser("inventory", help="Inventory all frozen source packages.")
    p_inv.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    p_inv.add_argument("--json", action="store_true")

    p_build = subparsers.add_parser("build", help="Build a declarative Web package.")
    p_build.add_argument("package_dir", type=Path)
    p_build.add_argument("--lang", required=True)
    p_build.add_argument("--out", required=True, type=Path)
    p_build.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    p_build.add_argument("--skip-pin-check", action="store_true")
    p_build.add_argument("--json", action="store_true")
    return parser


def _emit(payload: Mapping[str, Any], text: str, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(text)


def _format_verify_text(report: Mapping[str, Any]) -> str:
    status = "OK" if report["ok"] else "FAILED"
    return (
        f"[verify-pins] {status}: {report['package_dir']} "
        f"(inputs={report['checked_inputs']}, repo_inputs={report['checked_repo_inputs']}, "
        f"mismatches={len(report['mismatches'])}, missing={len(report['missing'])}, "
        f"traversal={len(report['traversal_errors'])})"
    )


def _format_audit_text(report: Mapping[str, Any]) -> str:
    status = "OK" if report["ok"] else "FAILED"
    lines = [f"[audit-styles] {status}: {report['package_dir']}"]
    for loc in report["locales"]:
        loc_status = "baseline" if loc.get("baseline") else ("ok" if loc["ok"] else "fail")
        lines.append(f"  {loc['language']}: {loc_status} ({len(loc['issues'])} issues)")
    if report.get("error"):
        lines.append(f"  error: {report['error']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "verify-pins":
        report = verify_pins(args.package_dir, repo_root=args.repo_root)
        _emit(report, _format_verify_text(report), as_json=args.json)
        return 0 if report["ok"] else 1
    if args.command == "audit-styles":
        report = audit_styles(
            args.package_dir,
            lang=args.lang,
            respect_baseline=args.respect_baseline,
        )
        _emit(report, _format_audit_text(report), as_json=args.json)
        return 0 if report["ok"] else 1
    if args.command == "inventory":
        report = collect_inventory(args.repo_root.resolve())
        _emit(report, format_inventory_text(report), as_json=args.json)
        return 0
    if args.command == "build":
        try:
            report = build_declarative_package(
                args.package_dir,
                lang=args.lang,
                output_dir=args.out,
                repo_root=args.repo_root,
                skip_pin_check=args.skip_pin_check,
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            error_payload = {"ok": False, "error": str(exc)}
            _emit(error_payload, f"[build] FAILED: {exc}", as_json=args.json)
            return 1
        _emit(
            report,
            f"[build] OK: {report['markdown_path']} ({len(report['pages'])} pages)",
            as_json=args.json,
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
