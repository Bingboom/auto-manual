"""Plan-only scaffolding for onboarding an existing manual line.

Stage 3 deliberately starts with a read-only plan. This module resolves the
same config and manifest surfaces used by the normal build, but it never
creates files and never talks to Feishu. The later write PR can consume this
stable report without reimplementing target or page resolution.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.config_loader import load_config_mapping
from tools.config_pages import (
    ConfigPage,
    CoverPdfPage,
    CsvPage,
    GeneratedPage,
    PdfInsertPage,
    RstIncludePage,
)
from tools.page_manifest import resolve_config_pages_or_raise
from tools.utils.targets import (
    format_tokenized,
    resolve_build_languages,
    resolve_build_model,
    resolve_build_region,
)


SCHEMA_VERSION = "new-line-scaffold/v1"
WRITE_ROLES = ("config", "manifest", "template-source", "source-table")
BLOCKED_WRITE_ROLES = ("source-table",)


@dataclass(frozen=True)
class PlanReference:
    role: str
    path: str
    status: str
    page: str | None = None


@dataclass(frozen=True)
class ScaffoldPlan:
    schema_version: str
    mode: str
    source_config: str
    config_chain: tuple[str, ...]
    target: dict[str, Any]
    manifest: dict[str, Any]
    references: tuple[PlanReference, ...]
    write_surface: tuple[dict[str, str], ...]
    write_policy: dict[str, Any]
    whitelist_diff: tuple[str, ...]
    validation: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _relative(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _config_chain(config_path: Path) -> tuple[Path, ...]:
    chain: list[Path] = []
    current = config_path.resolve()
    while True:
        if current in chain:
            names = " -> ".join(path.name for path in (*chain, current))
            raise RuntimeError(f"config extends cycle detected: {names}")
        chain.append(current)
        cfg = load_config_mapping(current)
        raw_extends = cfg.get("extends")
        if not isinstance(raw_extends, str) or not raw_extends.strip():
            return tuple(chain)
        current = (current.parent / raw_extends.strip()).resolve()


def _first_target(cfg: dict[str, Any]) -> dict[str, str]:
    build = cfg.get("build")
    if not isinstance(build, dict):
        return {}
    targets = build.get("targets")
    if not isinstance(targets, list):
        return {}
    for raw in targets:
        if not isinstance(raw, dict):
            continue
        model = str(raw.get("model") or "").strip()
        region = str(raw.get("region") or "").strip()
        if model or region:
            return {"model": model, "region": region}
    return {}


def _resolve_target(cfg: dict[str, Any], *, model: str | None, region: str | None) -> tuple[str, str]:
    fallback = _first_target(cfg)
    resolved_model = resolve_build_model(cfg, model) or fallback.get("model", "")
    resolved_region = resolve_build_region(cfg, region) or fallback.get("region", "")
    if not resolved_model or not resolved_region:
        raise RuntimeError("new-line requires a resolvable model and region (pass --model and --region)")
    return resolved_model, resolved_region


def _docs_dir(cfg: dict[str, Any], *, root: Path) -> Path:
    paths = cfg.get("paths")
    raw = paths.get("docs_dir") if isinstance(paths, dict) else None
    path = Path(raw.strip()) if isinstance(raw, str) and raw.strip() else Path("docs")
    return path if path.is_absolute() else root / path


def _source_path(raw: str, *, docs_dir: Path, model: str, region: str) -> Path | None:
    if raw.startswith("asset:"):
        return None
    rendered = format_tokenized(raw, None, model, region)
    path = Path(rendered)
    return path if path.is_absolute() else docs_dir / path


def _page_references(
    pages: list[ConfigPage],
    *,
    docs_dir: Path,
    model: str,
    region: str,
    root: Path,
) -> list[PlanReference]:
    references: list[PlanReference] = []

    def add(role: str, raw: str, page: str | None) -> None:
        source_path = _source_path(raw, docs_dir=docs_dir, model=model, region=region)
        if source_path is None:
            references.append(PlanReference(role="asset-reference", path=raw, status="deferred", page=page))
            return
        references.append(
            PlanReference(
                role=role,
                path=_relative(source_path, root=root),
                status="present" if source_path.exists() else "missing",
                page=page,
            )
        )

    for page in pages:
        if isinstance(page, RstIncludePage):
            add("template-source", page.file, None)
        elif isinstance(page, GeneratedPage):
            add("template-source", page.recipe, page.page)
            add("template-source", page.template, page.page)
        elif isinstance(page, CoverPdfPage):
            add("template-source", page.file, None)
        elif isinstance(page, PdfInsertPage):
            for raw in page.file_map.values():
                add("template-source", raw, None)
        elif isinstance(page, CsvPage):
            references.append(
                PlanReference(
                    role="source-table",
                    path="data/phase2",
                    status="deferred",
                    page=page.page,
                )
            )
    return references


def _manifest_summary(resolved: Any, *, root: Path) -> dict[str, Any]:
    pages = resolved.pages
    counts: dict[str, int] = {}
    for page in pages:
        counts[page.page_type] = counts.get(page.page_type, 0) + 1
    return {
        "path": _relative(resolved.manifest_path, root=root) if resolved.manifest_path else None,
        "manifest_id": resolved.manifest_id,
        "page_count": len(pages),
        "page_type_counts": dict(sorted(counts.items())),
        "pages": [page.page_type for page in pages],
    }


def build_plan(
    config_path: Path,
    *,
    root: Path,
    model: str | None = None,
    region: str | None = None,
) -> ScaffoldPlan:
    root = root.resolve()
    config_path = config_path.resolve()
    cfg = load_config_mapping(config_path)
    resolved_model, resolved_region = _resolve_target(cfg, model=model, region=region)

    languages = resolve_build_languages(cfg)
    if not languages:
        raise RuntimeError("new-line requires build.languages to contain at least one language")

    resolved = resolve_config_pages_or_raise(
        cfg,
        default_languages=languages,
        root=root,
        model=resolved_model,
        region=resolved_region,
        error_prefix="config.pages",
    )
    if resolved.manifest_path is None:
        raise RuntimeError("new-line requires paths.page_manifest so the scaffold has an explicit page source")

    references = _page_references(
        resolved.pages,
        docs_dir=_docs_dir(cfg, root=root),
        model=resolved_model,
        region=resolved_region,
        root=root,
    )
    chain = _config_chain(config_path)
    source_config_rel = _relative(config_path, root=root)
    manifest_rel = _relative(resolved.manifest_path, root=root)
    write_surface = (
        {"role": "config", "path": source_config_rel, "operation": "create-or-update"},
        {"role": "manifest", "path": manifest_rel, "operation": "create-or-update"},
        {
            "role": "template-source",
            "path": _relative(_docs_dir(cfg, root=root), root=root),
            "operation": "copy-or-localize",
        },
        {"role": "source-table", "path": "data/phase2", "operation": "F6-gated"},
    )

    missing = sorted({reference.path for reference in references if reference.status == "missing"})
    outside = sorted(
        {
            reference.path
            for reference in references
            if reference.status != "deferred"
            and (reference.path.startswith("/") or reference.path.startswith("../"))
        }
    )
    unexpected = sorted(set(missing) | set(outside))
    return ScaffoldPlan(
        schema_version=SCHEMA_VERSION,
        mode="dry-run",
        source_config=source_config_rel,
        config_chain=tuple(_relative(path, root=root) for path in chain),
        target={"model": resolved_model, "region": resolved_region, "languages": languages},
        manifest=_manifest_summary(resolved, root=root),
        references=tuple(references),
        write_surface=write_surface,
        write_policy={
            "source_table_write": "blocked",
            "reason": "Stage 3 gate: phase2 source-table writes require a separately approved write PR",
            "allowed_roles": list(WRITE_ROLES),
            "blocked_roles": list(BLOCKED_WRITE_ROLES),
        },
        whitelist_diff=tuple(unexpected),
        validation={
            "status": "passed" if not unexpected else "failed",
            "missing_references": missing,
            "outside_repo_references": outside,
            "page_parse_errors": [],
        },
    )


def render_plan(plan: ScaffoldPlan, *, as_json: bool) -> str:
    if as_json:
        return json.dumps(plan.as_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    validation = plan.validation
    return "\n".join(
        (
            f"schema_version={plan.schema_version}",
            f"mode={plan.mode}",
            f"source_config={plan.source_config}",
            f"target={plan.target['model']}/{plan.target['region']}[{','.join(plan.target['languages'])}]",
            f"manifest={plan.manifest['path']} pages={plan.manifest['page_count']}",
            f"source_table_write={plan.write_policy['source_table_write']}",
            f"whitelist_diff={len(plan.whitelist_diff)}",
            f"validation={validation['status']}",
        )
    )


def run_new_line(args: argparse.Namespace, *, repo_root: Path) -> None:
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    plan = build_plan(
        config_path,
        root=repo_root,
        model=getattr(args, "model", None),
        region=getattr(args, "region", None),
    )
    output = getattr(args, "plan_output", None)
    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = repo_root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_plan(plan, as_json=True) + "\n", encoding="utf-8")
    print(render_plan(plan, as_json=bool(getattr(args, "json", False))))
    if plan.whitelist_diff:
        raise RuntimeError("new-line dry-run found references outside the approved scaffold surface")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a read-only new-line scaffold")
    parser.add_argument("--config", required=True)
    parser.add_argument("--model")
    parser.add_argument("--region")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    run_new_line(args, repo_root=Path(__file__).resolve().parents[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
