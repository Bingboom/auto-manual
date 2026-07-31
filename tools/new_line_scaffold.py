"""Scaffold an existing manual line without crossing the phase2 write gate.

The command has two deliberately separate surfaces:

* the default plan is read-only and resolves the same config/manifest inputs
  as the normal build;
* "--write" materializes only explicitly named config and manifest files,
  refreshes the committed fixture through the existing target-scoped helper,
  and runs the normal "build.py check" gate.

Neither path writes Feishu or "data/phase2". Production source-table writes
remain the separately approved F6 operation described by the scaling plan.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
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


@dataclass(frozen=True)
class ScaffoldWriteResult:
    config: str
    manifest: str
    fixture_refresh: dict[str, Any]
    auto_check: dict[str, Any]

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


def _safe_output_path(raw: str | Path, *, root: Path, label: str) -> Path:
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"{label} must stay inside the repository: {resolved}") from exc

    blocked = (
        root / "data" / "phase2",
        root / "tests" / "fixtures" / "phase2",
        root / "docs" / "_build",
    )
    if any(resolved == candidate or candidate in resolved.parents for candidate in blocked):
        raise RuntimeError(f"{label} is outside the controlled scaffold surface: {resolved}")
    return resolved


def _load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency is required by the repo
        raise RuntimeError("PyYAML is required for new-line --write") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be a YAML mapping: {path}")
    return value


def _write_yaml_mapping(path: Path, value: dict[str, Any]) -> None:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency is required by the repo
        raise RuntimeError("PyYAML is required for new-line --write") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def materialize_scaffold(
    plan: ScaffoldPlan,
    *,
    source_config: Path,
    root: Path,
    output_config: Path,
    output_manifest: Path,
    force: bool = False,
) -> ScaffoldWriteResult:
    """Write an explicit config/manifest pair and nothing else."""

    root = root.resolve()
    source_config = source_config.resolve()
    output_config = _safe_output_path(output_config, root=root, label="--output-config")
    output_manifest = _safe_output_path(output_manifest, root=root, label="--output-manifest")
    if output_config == source_config:
        raise RuntimeError("--output-config must not overwrite --config")
    if output_config == output_manifest:
        raise RuntimeError("--output-config and --output-manifest must be different files")
    existing = [path for path in (output_config, output_manifest) if path.exists()]
    if existing and not force:
        rendered = ", ".join(str(path) for path in existing)
        raise RuntimeError(f"scaffold output already exists; pass --force to replace: {rendered}")

    config = _load_yaml_mapping(source_config, label="source config")
    build = config.setdefault("build", {})
    if not isinstance(build, dict):
        raise RuntimeError("source config build must be a mapping")
    build["default_model"] = plan.target["model"]
    build["default_region"] = plan.target["region"]
    build["targets"] = [{"model": plan.target["model"], "region": plan.target["region"]}]

    extends = config.get("extends")
    if isinstance(extends, str) and extends.strip():
        extends_path = (source_config.parent / extends.strip()).resolve()
        try:
            config["extends"] = os.path.relpath(extends_path, output_config.parent).replace(os.sep, "/")
        except ValueError as exc:
            raise RuntimeError(f"cannot relocate config extends path: {extends_path}") from exc

    paths = config.setdefault("paths", {})
    if not isinstance(paths, dict):
        raise RuntimeError("source config paths must be a mapping")
    paths["page_manifest"] = output_manifest.relative_to(root).as_posix()

    manifest_source = Path(plan.manifest["path"])
    if not manifest_source.is_absolute():
        manifest_source = root / manifest_source
    manifest = _load_yaml_mapping(manifest_source, label="source manifest")
    manifest_id = output_manifest.stem
    if manifest_id.startswith("manual_"):
        manifest["manifest_id"] = manifest_id

    _write_yaml_mapping(output_config, config)
    _write_yaml_mapping(output_manifest, manifest)
    return ScaffoldWriteResult(
        config=output_config.relative_to(root).as_posix(),
        manifest=output_manifest.relative_to(root).as_posix(),
        fixture_refresh={},
        auto_check={},
    )


def _refresh_fixture(
    *,
    root: Path,
    document_key: str,
    source_root: str | Path,
    fixture_root: str | Path,
) -> dict[str, Any]:
    from tools.data_snapshot_fixture_refresh import refresh_fixture_by_document_key

    source = Path(source_root)
    fixture = Path(fixture_root)
    if not source.is_absolute():
        source = root / source
    if not fixture.is_absolute():
        fixture = root / fixture
    result = refresh_fixture_by_document_key(
        source_root=source,
        fixture_root=fixture,
        document_key=document_key,
        write=True,
    )
    if not result.refreshed_files:
        raise RuntimeError(
            f"fixture-refresh found no source rows for {document_key}; "
            "refusing to claim new-line coverage"
        )
    return result.as_dict()


def _auto_check(
    *,
    root: Path,
    config: Path,
    model: str,
    region: str,
    data_root: str | Path,
    staging_root: str | Path | None,
) -> dict[str, Any]:
    data_path = Path(data_root)
    if not data_path.is_absolute():
        data_path = root / data_path
    command = [
        sys.executable,
        str(root / "build.py"),
        "check",
        "--config",
        str(config),
        "--model",
        model,
        "--region",
        region,
        "--source",
        "runtime",
        "--data-root",
        str(data_path),
    ]
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if staging_root is None:
        temporary = tempfile.TemporaryDirectory(prefix="auto-manual-new-line-check-")
        check_staging = Path(temporary.name)
    else:
        check_staging = Path(staging_root)
        if not check_staging.is_absolute():
            check_staging = root / check_staging
    command.extend(["--staging-root", str(check_staging)])
    try:
        completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    finally:
        if temporary is not None:
            temporary.cleanup()
    output = (completed.stdout or "").strip()
    error = (completed.stderr or "").strip()
    if completed.returncode:
        detail = (output or error or "build.py check failed")[-2000:]
        raise RuntimeError(f"new-line auto check failed (exit {completed.returncode}): {detail}")
    return {"status": "passed", "returncode": completed.returncode, "command": command}


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
    if plan.whitelist_diff:
        raise RuntimeError("new-line dry-run found references outside the approved scaffold surface")

    if not getattr(args, "write", False):
        output = getattr(args, "plan_output", None)
        if output:
            output_path = Path(output)
            if not output_path.is_absolute():
                output_path = repo_root / output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(render_plan(plan, as_json=True) + "\n", encoding="utf-8")
        print(render_plan(plan, as_json=bool(getattr(args, "json", False))))
        return

    output_config = getattr(args, "output_config", None)
    output_manifest = getattr(args, "output_manifest", None)
    if not output_config or not output_manifest:
        raise RuntimeError("new-line --write requires --output-config and --output-manifest")

    result = materialize_scaffold(
        plan,
        source_config=config_path,
        root=repo_root,
        output_config=Path(output_config),
        output_manifest=Path(output_manifest),
        force=bool(getattr(args, "force", False)),
    )
    document_key = f"{plan.target['model']}_{plan.target['region']}"
    fixture_result = _refresh_fixture(
        root=repo_root,
        document_key=document_key,
        source_root=getattr(args, "fixture_source_root", "data/phase2"),
        fixture_root=getattr(args, "fixture_root", "tests/fixtures/phase2"),
    )
    check_result = {"status": "skipped", "reason": "--skip-auto-check"}
    if not getattr(args, "skip_auto_check", False):
        generated_config = repo_root / result.config
        check_result = _auto_check(
            root=repo_root,
            config=generated_config,
            model=plan.target["model"],
            region=plan.target["region"],
            data_root=getattr(args, "fixture_root", "tests/fixtures/phase2"),
            staging_root=getattr(args, "staging_root", None),
        )
    result = ScaffoldWriteResult(
        config=result.config,
        manifest=result.manifest,
        fixture_refresh=fixture_result,
        auto_check=check_result,
    )
    report = plan.as_dict()
    report["mode"] = "write"
    report["write"] = result.as_dict()
    output = getattr(args, "plan_output", None)
    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = repo_root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if getattr(args, "json", False):
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_plan(plan, as_json=False))
        print(f"mode=write config={result.config} manifest={result.manifest}")
        print(f"fixture_refresh={fixture_result['document_key']} files={len(fixture_result['refreshed_files'])}")
        print(f"auto_check={check_result['status']}")


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
