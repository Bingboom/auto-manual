"""Build-entry facade and batch sweep helpers for ManualIR v2 QC and provenance."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from tools.corpus.discover import discover_ir_pairs
from tools.web import ir_qc


def _resolve_repo_path(repo_root: Path, raw: Path) -> Path:
    return raw if raw.is_absolute() else (repo_root / raw).resolve()


def _resolve_optional_path(repo_root: Path, raw: Path | None) -> Path | None:
    return None if raw is None else _resolve_repo_path(repo_root, raw)


def _write_json_report(output_path: Path, payload: Mapping[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _emit(payload: Mapping[str, Any], text: str, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(text)


def _audit_threshold_error(
    *,
    errors: int,
    warnings: int,
    strict: bool,
    max_warnings: int | None,
) -> str | None:
    if errors > 0:
        return f"ir-qc audit found {errors} error(s)"
    if strict and warnings > 0:
        return f"ir-qc audit strict mode failed with {warnings} warning(s)"
    if max_warnings is not None and warnings > max_warnings:
        return f"ir-qc audit warnings ({warnings}) exceeded --max-warnings={max_warnings}"
    return None


def _require_single_or_all(subcommand: str, ir_path: Path | None, all_ir: bool) -> None:
    if ir_path is not None and all_ir:
        raise RuntimeError(f"ir-qc {subcommand}: pass either --ir or --all-ir, not both")
    if ir_path is None and not all_ir:
        raise RuntimeError(f"ir-qc {subcommand} requires --ir or --all-ir")


def run_ir_qc_audit_all(
    repo_root: Path,
    *,
    model: str | None = None,
    region: str | None = None,
    terms_path: Path | None = None,
    verify_assets: bool = True,
) -> dict[str, Any]:
    """Run `ir_qc.audit_manual_ir` across all discovered manual.ir.json bundles."""
    root = repo_root.resolve()
    discovered, pairs, _abstentions, _skipped = discover_ir_pairs(
        repo_root=root,
        model=model,
        region=region,
    )
    anchor_by_target: dict[Path, Path] = {
        pair.target.path.resolve(): pair.anchor.path.resolve() for pair in pairs
    }

    clean_bundles = 0
    warning_only_bundles = 0
    error_bundles = 0
    total_errors = 0
    total_warnings = 0
    error_types: Counter[str] = Counter()
    warning_types: Counter[str] = Counter()
    flagged_bundles: list[dict[str, Any]] = []

    for item in discovered:
        anchor_path = anchor_by_target.get(item.path.resolve())
        report = ir_qc.audit_manual_ir(
            item.path,
            anchor_ir_path=anchor_path,
            terms_path=terms_path,
            verify_assets=verify_assets,
        )
        summary = report["summary"]
        err_count = int(summary["errors"])
        warn_count = int(summary["warnings"])
        total_errors += err_count
        total_warnings += warn_count
        for finding in report["findings"]:
            sev = str(finding.get("severity") or "")
            rule = str(finding.get("type") or finding.get("rule_id") or "unknown")
            if sev == "error":
                error_types[rule] += 1
            elif sev == "warning":
                warning_types[rule] += 1
        if err_count > 0:
            error_bundles += 1
        elif warn_count > 0:
            warning_only_bundles += 1
        else:
            clean_bundles += 1
        if err_count > 0 or warn_count > 0:
            flagged_bundles.append(
                {
                    "ir_path": item.rel_path,
                    "anchor_ir_path": (
                        anchor_path.relative_to(root).as_posix()
                        if anchor_path is not None and anchor_path.is_relative_to(root)
                        else (str(anchor_path) if anchor_path is not None else None)
                    ),
                    "model": item.model,
                    "region": item.region,
                    "language": item.language,
                    "summary": summary,
                    "findings": report["findings"],
                }
            )

    return {
        "schema_version": ir_qc.AUDIT_SCHEMA_VERSION,
        "total_bundles": len(discovered),
        "paired_targets": len(pairs),
        "clean_bundles": clean_bundles,
        "warning_only_bundles": warning_only_bundles,
        "error_bundles": error_bundles,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "error_types": dict(sorted(error_types.items())),
        "warning_types": dict(sorted(warning_types.items())),
        "flagged_bundles": flagged_bundles,
    }


def run_ir_qc_provenance_all(
    repo_root: Path,
    *,
    model: str | None = None,
    region: str | None = None,
    asset_registry_csv: Path | None = None,
    tm_json_path: Path | None = None,
) -> dict[str, Any]:
    """Run `ir_qc.build_ir_provenance` across all discovered manual.ir.json bundles."""
    root = repo_root.resolve()
    discovered, pairs, _abstentions, _skipped = discover_ir_pairs(
        repo_root=root,
        model=model,
        region=region,
    )
    anchor_by_target: dict[Path, Path] = {
        pair.target.path.resolve(): pair.anchor.path.resolve() for pair in pairs
    }

    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for item in discovered:
        anchor_path = anchor_by_target.get(item.path.resolve())
        try:
            prov = ir_qc.build_ir_provenance(
                item.path,
                anchor_ir_path=anchor_path,
                asset_registry_csv=asset_registry_csv,
                tm_json_path=tm_json_path,
            )
            items.append(
                {
                    "ir_path": item.rel_path,
                    "model": item.model,
                    "region": item.region,
                    "language": item.language,
                    "visual_assets_status": prov["visual_assets"]["status"],
                    "tm_status": prov["tm_attribution"]["status"],
                    "component_block_count": prov["components"]["component_block_count"],
                }
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append({"ir_path": item.rel_path, "error": str(exc)})

    return {
        "schema_version": ir_qc.PROVENANCE_SCHEMA_VERSION,
        "total_bundles": len(discovered),
        "ok_bundles": len(items),
        "error_bundles": len(errors),
        "errors": errors,
        "items": items,
    }


def _format_batch_audit_text(report: Mapping[str, Any]) -> str:
    status = "OK" if report["total_errors"] == 0 else "FAILED"
    lines = [
        f"[ir-qc audit --all-ir] {status}: "
        f"bundles={report['total_bundles']} (paired={report['paired_targets']}), "
        f"clean={report['clean_bundles']}, warn_only={report['warning_only_bundles']}, "
        f"error_bundles={report['error_bundles']}, "
        f"errors={report['total_errors']}, warnings={report['total_warnings']}"
    ]
    if report["warning_types"]:
        lines.append(f"  warning_types={report['warning_types']}")
    if report["error_types"]:
        lines.append(f"  error_types={report['error_types']}")
    return "\n".join(lines)


def _format_batch_provenance_text(report: Mapping[str, Any]) -> str:
    status = "OK" if report["error_bundles"] == 0 else "FAILED"
    lines = [
        f"[ir-qc provenance --all-ir] {status}: "
        f"{report['ok_bundles']}/{report['total_bundles']} ok, "
        f"errors={report['error_bundles']}"
    ]
    for err in report["errors"]:
        lines.append(f"  ERROR {err['ir_path']}: {err['error']}")
    return "\n".join(lines)


def run_ir_qc_command(args: argparse.Namespace, *, repo_root: Path) -> None:
    """Dispatch `build.py ir-qc` across single-bundle and `--all-ir` modes."""
    root = repo_root.resolve()
    subcommand = getattr(args, "ir_command", None) or "audit"
    ir_path_raw: Path | None = getattr(args, "ir", None)
    all_ir = bool(getattr(args, "all_ir", False))
    _require_single_or_all(subcommand, ir_path_raw, all_ir)

    as_json = bool(getattr(args, "json", False))
    output_path = _resolve_optional_path(root, getattr(args, "output_path", None))
    anchor_ir_path = _resolve_optional_path(root, getattr(args, "anchor_ir", None))
    terms_path = _resolve_optional_path(root, getattr(args, "terms_json", None))
    asset_registry = _resolve_optional_path(root, getattr(args, "asset_registry", None))
    tm_json_path = _resolve_optional_path(root, getattr(args, "tm_json", None))
    verify_assets = not bool(getattr(args, "no_verify_assets", False))
    strict = bool(getattr(args, "strict", False))
    max_warnings: int | None = getattr(args, "max_warnings", None)
    model = getattr(args, "model", None)
    region = getattr(args, "region", None)

    if subcommand == "audit":
        if all_ir:
            report = run_ir_qc_audit_all(
                root,
                model=model,
                region=region,
                terms_path=terms_path,
                verify_assets=verify_assets,
            )
            if output_path is not None:
                _write_json_report(output_path, report)
            _emit(report, _format_batch_audit_text(report), as_json=as_json)
            err_msg = _audit_threshold_error(
                errors=int(report["total_errors"]),
                warnings=int(report["total_warnings"]),
                strict=strict,
                max_warnings=max_warnings,
            )
            if err_msg is not None:
                raise RuntimeError(err_msg)
            return

        assert ir_path_raw is not None
        report = ir_qc.audit_manual_ir(
            _resolve_repo_path(root, ir_path_raw),
            anchor_ir_path=anchor_ir_path,
            terms_path=terms_path,
            verify_assets=verify_assets,
        )
        if output_path is not None:
            _write_json_report(output_path, report)
        summary = report["summary"]
        status = "OK" if int(summary["errors"]) == 0 else "FAILED"
        _emit(
            report,
            f"[ir-qc audit] {status}: {report['ir_path']} "
            f"(errors={summary['errors']}, warnings={summary['warnings']})",
            as_json=as_json,
        )
        err_msg = _audit_threshold_error(
            errors=int(summary["errors"]),
            warnings=int(summary["warnings"]),
            strict=strict,
            max_warnings=max_warnings,
        )
        if err_msg is not None:
            raise RuntimeError(err_msg)
        return

    if subcommand == "provenance":
        if all_ir:
            report = run_ir_qc_provenance_all(
                root,
                model=model,
                region=region,
                asset_registry_csv=asset_registry,
                tm_json_path=tm_json_path,
            )
            if output_path is not None:
                _write_json_report(output_path, report)
            _emit(report, _format_batch_provenance_text(report), as_json=as_json)
            if report["error_bundles"] > 0:
                raise RuntimeError(
                    f"ir-qc provenance failed on {report['error_bundles']}/{report['total_bundles']} bundles"
                )
            return

        assert ir_path_raw is not None
        try:
            report = ir_qc.build_ir_provenance(
                _resolve_repo_path(root, ir_path_raw),
                anchor_ir_path=anchor_ir_path,
                asset_registry_csv=asset_registry,
                tm_json_path=tm_json_path,
                output_path=output_path,
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"ir-qc provenance failed: {exc}") from exc
        _emit(
            report,
            f"[ir-qc provenance] OK: {report['ir_path']} "
            f"(components={report['components']['component_block_count']}, "
            f"visual_assets={report['visual_assets']['status']})",
            as_json=as_json,
        )
        return

    raise RuntimeError(f"unsupported ir-qc command: {subcommand!r}")


__all__ = (
    "run_ir_qc_audit_all",
    "run_ir_qc_command",
    "run_ir_qc_provenance_all",
)
