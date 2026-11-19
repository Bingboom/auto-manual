"""Build-entry facade for all-region ManualIR v2 knowledge corpus export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.manual_knowledge import ir_export


def _resolve_repo_path(repo_root: Path, raw: Path) -> Path:
    return raw if raw.is_absolute() else (repo_root / raw).resolve()


def _resolve_optional_path(repo_root: Path, raw: Path | None) -> Path | None:
    return None if raw is None else _resolve_repo_path(repo_root, raw)


def run_ir_export_command(args: argparse.Namespace, *, repo_root: Path) -> None:
    """Dispatch `build.py ir-export` to `tools.manual_knowledge.ir_export.export_ir_knowledge`."""
    root = repo_root.resolve()
    raw_roots = list(getattr(args, "ir_roots", None) or ())
    resolved_roots = [_resolve_repo_path(root, Path(p)) for p in raw_roots]
    summary = ir_export.export_ir_knowledge(
        roots=resolved_roots,
        region=getattr(args, "region", None),
        model=getattr(args, "model", None),
        publication_eligible_only=bool(getattr(args, "publication_eligible_only", False)),
        output_corpus=_resolve_optional_path(root, getattr(args, "output_corpus", None)),
        output_observations=_resolve_optional_path(root, getattr(args, "output_observations", None)),
        previous_observations=_resolve_optional_path(root, getattr(args, "previous_observations", None)),
        repo_root_path=root,
    )
    if bool(getattr(args, "json", False)):
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
        return

    counts = summary["counts"]
    obs = summary["observation_summary"]
    print(
        f"[ir-export] OK: region={summary['region']}, regions={','.join(summary['regions'])}, "
        f"models={counts['models']}, editions={counts['editions']}, sections={counts['sections']}, "
        f"items={obs['items']}, relations={obs['relations']}"
    )


__all__ = ("run_ir_export_command",)
