#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.config_pages import RstIncludePage, parse_config_pages_or_raise  # noqa: E402
from tools.build_docs import (  # noqa: E402
    BuildTarget,
    load_config,
    resolve_build_targets,
    resolve_product_name_for_build,
)
from tools.gen_index_bundle import bundle_dir_for_target  # noqa: E402
from tools.page_contracts import (  # noqa: E402
    find_contract_for_source,
    load_page_contracts,
    required_placeholders_for_lang,
)
from tools.utils.spec_master import resolve_template_substitutions_from_spec_master  # noqa: E402
from tools.word_bundle_common import resolve_config_path  # noqa: E402

PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")
INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$")
ASSET_RE = re.compile(r"^\s*(?:[-*]\s+)?(?:-\s+)?\.\.\s+(?:image|figure)::\s+(\S+)\s*$")
HTML_SRC_RE = re.compile(r'\bsrc="([^"]+)"', re.IGNORECASE)


@dataclass(frozen=True)
class CheckIssue:
    code: str
    message: str
    model: str | None
    region: str | None
    path: Path | None = None
    lang: str | None = None


def resolve_docs_dir(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / "docs"


def _repo_relative(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _build_langs(cfg: dict) -> list[str]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = build_cfg.get("languages", ["en"])
    return [str(item).strip() for item in langs if str(item).strip()] or ["en"]


def resolve_spec_master_csv_path(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("spec_master_csv")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / "data" / "phase1" / "Spec_Master.csv"


def resolve_contracts_dir(*, docs_dir: Path) -> Path:
    return docs_dir / "templates" / "contracts"


def _is_external_reference(value: str) -> bool:
    token = value.strip()
    if not token:
        return True
    lowered = token.lower()
    return lowered.startswith(("http://", "https://", "data:", "file://", "mailto:", "#"))


def _resolve_local_reference(raw_value: str, *, rst_path: Path, bundle_dir: Path) -> Path | None:
    token = raw_value.strip()
    if not token or _is_external_reference(token):
        return None

    raw_path = Path(token.lstrip("/"))
    probe_paths = [
        rst_path.parent / raw_path,
        bundle_dir / raw_path,
        ROOT / raw_path,
    ]
    for probe in probe_paths:
        if probe.exists():
            return probe.resolve()
    return None


def collect_placeholder_issues(
    *,
    rst_path: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    matches = sorted(set(PLACEHOLDER_RE.findall(rst_path.read_text(encoding="utf-8"))))
    if not matches:
        return []
    return [
        CheckIssue(
            code="UNRESOLVED_PLACEHOLDER",
            message=f"Unresolved placeholders: {', '.join(matches)}",
            model=model,
            region=region,
            path=rst_path,
        )
    ]


def collect_reference_issues(
    *,
    rst_path: Path,
    bundle_dir: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    for line_no, line in enumerate(rst_path.read_text(encoding="utf-8").splitlines(), start=1):
        include_match = INCLUDE_RE.match(line)
        if include_match:
            raw_value = include_match.group(1)
            resolved = _resolve_local_reference(raw_value, rst_path=rst_path, bundle_dir=bundle_dir)
            if resolved is None:
                issues.append(
                    CheckIssue(
                        code="MISSING_INCLUDE",
                        message=f"Missing include target on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )

        asset_match = ASSET_RE.match(line)
        if asset_match:
            raw_value = asset_match.group(1)
            resolved = _resolve_local_reference(raw_value, rst_path=rst_path, bundle_dir=bundle_dir)
            if resolved is None:
                issues.append(
                    CheckIssue(
                        code="MISSING_ASSET",
                        message=f"Missing image/figure asset on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )

        for html_match in HTML_SRC_RE.finditer(line):
            raw_value = html_match.group(1)
            resolved = _resolve_local_reference(raw_value, rst_path=rst_path, bundle_dir=bundle_dir)
            if resolved is None:
                issues.append(
                    CheckIssue(
                        code="MISSING_HTML_SRC",
                        message=f"Missing HTML src asset on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )
    return issues


def collect_target_identity_issues(cfg: dict, *, target: BuildTarget, langs: list[str]) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    spec_master_csv = resolve_spec_master_csv_path(cfg)
    for lang in langs:
        product_name = resolve_product_name_for_build(
            cfg,
            model=target.model,
            region=target.region,
            lang=lang,
        )
        substitutions = resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model=target.model,
            region=target.region,
            lang=lang,
        )
        if not (product_name or "").strip():
            issues.append(
                CheckIssue(
                    code="MISSING_PRODUCT_NAME",
                    message="Failed to resolve Product Name from Spec_Master.csv",
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            )
        if not (substitutions.get("MODEL_NO") or "").strip():
            issues.append(
                CheckIssue(
                    code="MISSING_MODEL_NO",
                    message="Failed to resolve MODEL_NO from Spec_Master.csv",
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            )
    return issues


def collect_bundle_issues(*, bundle_dir: Path, model: str | None, region: str | None) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    index_path = bundle_dir / "index.rst"
    page_dir = bundle_dir / "page"
    if not index_path.exists():
        issues.append(
            CheckIssue(
                code="MISSING_BUNDLE_INDEX",
                message=f"Prepared bundle index not found: {index_path}",
                model=model,
                region=region,
                path=index_path,
            )
        )
    if not page_dir.exists():
        issues.append(
            CheckIssue(
                code="MISSING_PAGE_DIR",
                message=f"Prepared bundle page directory not found: {page_dir}",
                model=model,
                region=region,
                path=page_dir,
            )
        )
        return issues

    for rst_path in sorted(path for path in bundle_dir.rglob("*.rst") if path.is_file()):
        issues.extend(
            collect_placeholder_issues(
                rst_path=rst_path,
                model=model,
                region=region,
            )
        )
        issues.extend(
            collect_reference_issues(
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                model=model,
                region=region,
            )
        )
    return issues


def collect_page_contract_issues(
    cfg: dict,
    *,
    docs_dir: Path,
    target: BuildTarget,
    langs: list[str],
) -> list[CheckIssue]:
    contracts = load_page_contracts(resolve_contracts_dir(docs_dir=docs_dir))
    if not contracts:
        return []

    pages_raw = cfg.get("pages")
    if not isinstance(pages_raw, list) or not pages_raw:
        return []

    pages = parse_config_pages_or_raise(
        pages_raw,
        default_languages=langs,
        error_prefix="config.pages",
    )
    spec_master_csv = resolve_spec_master_csv_path(cfg)
    substitutions_by_lang: dict[str, dict[str, str]] = {}
    issues: list[CheckIssue] = []

    for page in pages:
        if not isinstance(page, RstIncludePage):
            continue
        source_path = resolve_config_path(docs_dir, page.file, target.model, target.region)
        try:
            source_rel = source_path.relative_to(docs_dir).as_posix()
        except ValueError:
            source_rel = source_path.as_posix()

        contract = find_contract_for_source(source_rel, contracts)
        if contract is None:
            continue

        page_langs = [page.lang] if page.lang else langs
        for lang in page_langs:
            required = required_placeholders_for_lang(contract, lang)
            if not required:
                continue

            substitutions = substitutions_by_lang.get(lang)
            if substitutions is None:
                substitutions = resolve_template_substitutions_from_spec_master(
                    spec_master_csv,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
                substitutions_by_lang[lang] = substitutions

            missing = [key for key in required if not (substitutions.get(key) or "").strip()]
            if missing:
                issues.append(
                    CheckIssue(
                        code="CONTRACT_MISSING_PLACEHOLDERS",
                        message=(
                            f"Page contract '{contract.page_id}' is missing required placeholders "
                            f"for lang '{lang}': {', '.join(missing)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=source_path,
                        lang=lang,
                    )
                )
    return issues


def collect_check_issues(
    *,
    cfg_path: Path,
    model: str | None,
    region: str | None,
    all_targets: bool,
) -> list[CheckIssue]:
    cfg = load_config(cfg_path)
    docs_dir = resolve_docs_dir(cfg)
    langs = _build_langs(cfg)
    targets = resolve_build_targets(
        cfg,
        arg_model=model,
        arg_region=region,
        all_targets=all_targets,
    )

    issues: list[CheckIssue] = []
    for target in targets:
        target_langs = [target.lang] if (target.lang or "").strip() else langs
        bundle_dir = bundle_dir_for_target(
            docs_dir=docs_dir,
            model=target.model,
            region=target.region,
            lang=target.lang,
        )
        issues.extend(collect_target_identity_issues(cfg, target=target, langs=target_langs))
        issues.extend(
            collect_page_contract_issues(
                cfg,
                docs_dir=docs_dir,
                target=target,
                langs=target_langs,
            )
        )
        issues.extend(
            collect_bundle_issues(
                bundle_dir=bundle_dir,
                model=target.model,
                region=target.region,
            )
        )
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run lightweight quality checks against prepared manual bundles.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
    ap.add_argument("--all-targets", action="store_true", help="Use build.targets from config")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path

    try:
        issues = collect_check_issues(
            cfg_path=cfg_path,
            model=args.model,
            region=args.region,
            all_targets=args.all_targets,
        )
    except RuntimeError as exc:
        print(f"[check] ERROR: {exc}", file=sys.stderr)
        return 1

    if issues:
        for issue in issues:
            target_bits = [bit for bit in (issue.model, issue.region) if bit]
            target_text = "/".join(target_bits) if target_bits else "_shared/_default"
            lang_text = f" lang={issue.lang}" if issue.lang else ""
            path_text = f" path={_repo_relative(issue.path)}" if issue.path else ""
            print(f"[check] {issue.code} target={target_text}{lang_text}{path_text}: {issue.message}")
        print(f"[check] FAILED with {len(issues)} issue(s)", file=sys.stderr)
        return 1

    print("[check] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
