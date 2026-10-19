from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def collect_target_identity_issues(
    cfg: dict,
    *,
    target: Any,
    langs: list[str],
    data_root: str | None,
    issue_cls: type[Any],
    resolve_spec_master_csv_path: Callable[..., Path],
    resolve_product_name_for_build: Callable[..., str | None],
    resolve_template_substitutions_from_spec_master: Callable[..., dict[str, str]],
) -> list[Any]:
    issues: list[Any] = []
    spec_master_csv = resolve_spec_master_csv_path(cfg, data_root=data_root)
    for lang in langs:
        product_name = resolve_product_name_for_build(
            cfg,
            model=target.model,
            region=target.region,
            lang=lang,
            data_root=data_root,
        )
        substitutions = resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model=target.model,
            region=target.region,
            lang=lang,
        )
        if not (product_name or "").strip():
            issues.append(
                issue_cls(
                    code="MISSING_PRODUCT_NAME",
                    message="Failed to resolve Product Name from Spec_Master.csv",
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            )
        if not (substitutions.get("MODEL_NO") or "").strip():
            issues.append(
                issue_cls(
                    code="MISSING_MODEL_NO",
                    message="Failed to resolve MODEL_NO from Spec_Master.csv",
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            )
    return issues


def collect_identity_drift_issues(
    cfg: dict,
    *,
    bundle_dir: Path,
    target: Any,
    langs: list[str],
    data_root: str | None,
    issue_cls: type[Any],
    resolve_spec_master_csv_path: Callable[..., Path],
    checks_cfg: Callable[[dict], dict],
    find_identity_drift_matches: Callable[..., list[Any]],
) -> list[Any]:
    spec_master_csv = resolve_spec_master_csv_path(cfg, data_root=data_root)
    checks = checks_cfg(cfg)
    allowlist_raw = checks.get("allowed_foreign_identity_literals", [])
    allowlist = tuple(str(item).strip() for item in allowlist_raw if str(item).strip()) if isinstance(allowlist_raw, list) else ()

    matches = find_identity_drift_matches(
        bundle_dir=bundle_dir,
        spec_master_csv=spec_master_csv,
        model=target.model,
        region=target.region,
        langs=langs,
        allowlist=allowlist,
    )
    issues: list[Any] = []
    for match in matches:
        source_target = "/".join(bit for bit in (match.source_model, match.source_region) if bit) or "_shared/_default"
        issues.append(
            issue_cls(
                code="STALE_IDENTITY_LITERAL",
                message=(
                    f"Found foreign identity literal '{match.literal}' on line {match.line_no} "
                    f"(latest source target: {source_target})"
                ),
                model=target.model,
                region=target.region,
                path=match.path,
            )
        )
    return issues
