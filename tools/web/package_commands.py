"""Build-entry facade and batch sweep helpers for declarative Web packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.web import package_build, package_inventory


def _resolve_repo_path(repo_root: Path, raw: Path) -> Path:
    return raw if raw.is_absolute() else (repo_root / raw).resolve()


def _emit(payload: Mapping[str, Any], text: str, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(text)


def _format_batch_verify_text(report: Mapping[str, Any]) -> str:
    status = "OK" if report["ok"] else "FAILED"
    lines = [
        f"[verify-pins --all-packages] {status}: "
        f"{report['passed_packages']}/{report['total_packages']} ok, "
        f"{report['failed_packages']} failed"
    ]
    for item in report["failures"]:
        lines.append(
            f"  FAIL {item['package_dir']}: "
            f"mismatches={len(item['mismatches'])}, "
            f"missing={len(item['missing'])}, "
            f"traversal={len(item['traversal_errors'])}"
        )
    return "\n".join(lines)


def _format_batch_audit_text(report: Mapping[str, Any]) -> str:
    status = "OK" if report["ok"] else "FAILED"
    lines = [
        f"[audit-styles --all-packages] {status}: "
        f"{report['passed_packages']}/{report['sealed_packages']} sealed packages ok, "
        f"{report['failed_packages']} failed (respect_baseline={report['respect_baseline']})"
    ]
    for item in report["failures"]:
        lines.append(f"  FAIL {item['package_dir']}: {item.get('error') or 'style issues'}")
    return "\n".join(lines)


def run_verify_pins_all(repo_root: Path) -> dict[str, Any]:
    """Verify SHA-256 manifest pins across every package discovered by package_inventory."""
    root = repo_root.resolve()
    inv = package_inventory.collect_inventory(root)
    failures: list[dict[str, Any]] = []
    passed = 0
    for pkg in inv["packages"]:
        rep = package_build.verify_pins(_resolve_repo_path(root, Path(pkg["path"])), repo_root=root)
        if rep["ok"]:
            passed += 1
        else:
            failures.append(
                {
                    "package_dir": pkg["path"],
                    "mismatches": rep.get("mismatches", []),
                    "missing": rep.get("missing", []),
                    "traversal_errors": rep.get("traversal_errors", []),
                    "error": rep.get("error"),
                }
            )
    return {
        "ok": len(failures) == 0,
        "total_packages": inv["total_packages"],
        "passed_packages": passed,
        "failed_packages": len(failures),
        "failures": failures,
    }


def run_audit_styles_all(
    repo_root: Path,
    *,
    lang: str | None = None,
    respect_baseline: bool = False,
) -> dict[str, Any]:
    """Audit sealed Web locales across all sealed packages discovered by package_inventory."""
    root = repo_root.resolve()
    inv = package_inventory.collect_inventory(root)
    sealed_pkgs = [pkg for pkg in inv["packages"] if pkg.get("sealed_locales")]
    failures: list[dict[str, Any]] = []
    passed = 0
    for pkg in sealed_pkgs:
        rep = package_build.audit_styles(
            _resolve_repo_path(root, Path(pkg["path"])),
            lang=lang,
            respect_baseline=respect_baseline,
        )
        if rep["ok"]:
            passed += 1
        else:
            failures.append(
                {
                    "package_dir": pkg["path"],
                    "error": rep.get("error"),
                    "locales": rep.get("locales", []),
                }
            )
    return {
        "ok": len(failures) == 0,
        "respect_baseline": respect_baseline,
        "lang": lang,
        "sealed_packages": len(sealed_pkgs),
        "passed_packages": passed,
        "failed_packages": len(failures),
        "failures": failures,
    }


def _require_single_or_all(
    subcommand: str,
    package_dir: Path | None,
    all_packages: bool,
) -> None:
    if package_dir is not None and all_packages:
        raise RuntimeError(f"web-package {subcommand}: pass either --package-dir or --all-packages, not both")
    if package_dir is None and not all_packages:
        raise RuntimeError(f"web-package {subcommand} requires --package-dir or --all-packages")


def run_web_package_command(args: argparse.Namespace, *, repo_root: Path) -> None:
    """Dispatch `build.py web-package` across inventory, verify-pins, audit-styles, and build."""
    root = repo_root.resolve()
    subcommand = getattr(args, "package_command", None) or "inventory"
    as_json = bool(getattr(args, "json", False))
    package_dir_raw: Path | None = getattr(args, "package_dir", None)
    all_packages = bool(getattr(args, "all_packages", False))

    if subcommand == "inventory":
        report = package_inventory.collect_inventory(root)
        _emit(report, package_inventory.format_inventory_text(report), as_json=as_json)
        return

    if subcommand == "verify-pins":
        _require_single_or_all(subcommand, package_dir_raw, all_packages)
        if all_packages:
            report = run_verify_pins_all(root)
            _emit(report, _format_batch_verify_text(report), as_json=as_json)
            if not report["ok"]:
                raise RuntimeError(
                    f"web-package verify-pins failed on {report['failed_packages']}/{report['total_packages']} packages"
                )
            return
        assert package_dir_raw is not None
        report = package_build.verify_pins(_resolve_repo_path(root, package_dir_raw), repo_root=root)
        _emit(report, package_build.format_verify_text(report), as_json=as_json)
        if not report["ok"]:
            raise RuntimeError(f"web-package verify-pins failed for {report['package_dir']}")
        return

    if subcommand == "audit-styles":
        _require_single_or_all(subcommand, package_dir_raw, all_packages)
        lang = getattr(args, "lang", None)
        respect_baseline = bool(getattr(args, "respect_baseline", False))
        if all_packages:
            report = run_audit_styles_all(root, lang=lang, respect_baseline=respect_baseline)
            _emit(report, _format_batch_audit_text(report), as_json=as_json)
            if not report["ok"]:
                raise RuntimeError(
                    f"web-package audit-styles failed on {report['failed_packages']}/{report['sealed_packages']} sealed packages"
                )
            return
        assert package_dir_raw is not None
        report = package_build.audit_styles(
            _resolve_repo_path(root, package_dir_raw),
            lang=lang,
            respect_baseline=respect_baseline,
        )
        _emit(report, package_build.format_audit_text(report), as_json=as_json)
        if not report["ok"]:
            raise RuntimeError(f"web-package audit-styles failed for {report['package_dir']}")
        return

    if subcommand == "build":
        if all_packages:
            raise RuntimeError("web-package build does not support --all-packages")
        lang = getattr(args, "lang", None)
        output_dir_raw: Path | None = getattr(args, "output_dir", None)
        missing = [
            flag
            for flag, val in (
                ("--package-dir", package_dir_raw),
                ("--lang", lang),
                ("--output-dir", output_dir_raw),
            )
            if not val
        ]
        if missing:
            raise RuntimeError(f"web-package build requires: {', '.join(missing)}")
        assert package_dir_raw is not None and output_dir_raw is not None and lang is not None
        try:
            report = package_build.build_declarative_package(
                _resolve_repo_path(root, package_dir_raw),
                lang=lang,
                output_dir=_resolve_repo_path(root, output_dir_raw),
                repo_root=root,
                skip_pin_check=bool(getattr(args, "skip_pin_check", False)),
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            _emit({"ok": False, "error": str(exc)}, f"[build] FAILED: {exc}", as_json=as_json)
            raise RuntimeError(str(exc)) from exc
        _emit(
            report,
            f"[build] OK: {report['markdown_path']} ({len(report['pages'])} pages)",
            as_json=as_json,
        )
        return

    raise RuntimeError(f"unsupported web-package command: {subcommand!r}")


__all__ = (
    "run_audit_styles_all",
    "run_verify_pins_all",
    "run_web_package_command",
)
