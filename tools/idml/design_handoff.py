"""Design handoff package helpers for IDML dual-mode exports."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .flow_idml import FlowOutputs


@dataclass(frozen=True)
class HandoffOutputs:
    root: Path
    production_idml: Path
    production_trace: Path
    production_asset_manifest: Path
    missing_assets_report: Path
    designer_checklist: Path
    layout_feedback: Path


def write_handoff_package(*, root: Path, model: str, region: str, lang: str,
                          data_root: Path, bundle_root: Path,
                          production_idml: Path, flow: FlowOutputs,
                          build_command: list[str]) -> HandoffOutputs:
    handoff_root = flow.markdown.parent.parent
    production_dir = handoff_root / "production"
    production_dir.mkdir(parents=True, exist_ok=True)
    production_copy = production_dir / "manual.production.idml"
    shutil.copyfile(production_idml, production_copy)
    production_manifest = production_dir / "asset_manifest.csv"
    if flow.asset_manifest.is_file():
        shutil.copyfile(flow.asset_manifest, production_manifest)
    else:
        production_manifest.write_text("asset_id,asset_ref,resolved_path,source_ref,kind\n", encoding="utf-8")
    production_trace = production_dir / "source_trace.json"
    production_trace.write_text(
        json.dumps(
            _production_trace(
                root=root,
                model=model,
                region=region,
                lang=lang,
                data_root=data_root,
                bundle_root=bundle_root,
                production_idml=production_copy,
                asset_manifest=production_manifest,
                build_command=build_command,
            ),
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    missing_report = handoff_root / "missing_assets_report.md"
    missing_report.write_text(_missing_assets_report(flow.asset_manifest), encoding="utf-8")
    checklist = handoff_root / "designer_checklist.md"
    checklist.write_text(_designer_checklist(model, region, lang), encoding="utf-8")
    feedback = handoff_root / "layout_feedback.md"
    feedback.write_text(_layout_feedback(model, region, lang), encoding="utf-8")
    return HandoffOutputs(
        root=handoff_root,
        production_idml=production_copy,
        production_trace=production_trace,
        production_asset_manifest=production_manifest,
        missing_assets_report=missing_report,
        designer_checklist=checklist,
        layout_feedback=feedback,
    )


def _production_trace(*, root: Path, model: str, region: str, lang: str,
                      data_root: Path, bundle_root: Path, production_idml: Path,
                      asset_manifest: Path, build_command: list[str]) -> dict:
    return {
        "manual_id": f"{model.replace('-', '')}_{region}_{lang.upper()}",
        "model": model,
        "region": region,
        "language": lang,
        "version": "unknown",
        "source_snapshot": _display_path(root, data_root / "snapshot_manifest.json")
        if (data_root / "snapshot_manifest.json").exists() else _display_path(root, data_root),
        "source_tables": sorted(path.name for path in data_root.glob("*.csv")) if data_root.exists() else [],
        "canonical_md": None,
        "template_commit": _git_sha(root),
        "asset_manifest": _display_path(root, asset_manifest),
        "build_command": build_command,
        "idml_mode": "production",
        "bundle_root": _display_path(root, bundle_root),
        "production_idml": _display_path(root, production_idml),
    }


def _missing_assets_report(manifest_path: Path) -> str:
    missing: list[dict[str, str]] = []
    total = 0
    if manifest_path.is_file():
        with manifest_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                total += 1
                if not (row.get("resolved_path") or "").strip():
                    missing.append(row)
    lines = ["# Missing Assets Report", "", f"- Assets referenced: {total}"]
    if not missing:
        lines.extend(["- Missing assets: 0", "", "No missing assets detected in the flow asset manifest."])
        return "\n".join(lines) + "\n"
    lines.extend(["- Missing assets: " + str(len(missing)), "", "| Asset ID | Reference | Source | Kind |",
                  "|---|---|---|---|"])
    for row in missing:
        lines.append(
            "| {asset_id} | {asset_ref} | {source_ref} | {kind} |".format(
                asset_id=_cell(row.get("asset_id", "")),
                asset_ref=_cell(row.get("asset_ref", "")),
                source_ref=_cell(row.get("source_ref", "")),
                kind=_cell(row.get("kind", "")),
            )
        )
    return "\n".join(lines) + "\n"


def _designer_checklist(model: str, region: str, lang: str) -> str:
    return f"""# Designer Checklist

- Target: `{model}_{region}_{lang}`
- Open `production/manual.production.idml` for visual parity review.
- Open `flow/manual.flow.idml` for continuous-story template styling.
- Use `flow/manual.flow.md` as the readable semantic reference.
- Check `missing_assets_report.md` before relinking or replacing assets.
- Record visual feedback in `layout_feedback.md`.
- Do not treat edited IDML text as the source of truth; route copy fixes back to source tables, templates, review docs, or TM.
"""


def _layout_feedback(model: str, region: str, lang: str) -> str:
    return f"""# Layout Feedback

Target: `{model}_{region}_{lang}`

## Production IDML

- Page / section:
- Issue:
- Suggested renderer or layout parameter change:

## Flow IDML

- Style map / template issue:
- Story editability issue:
- Asset placeholder issue:

## Source Corrections

- Copy or translation issue:
- Source location if known:
"""


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _git_sha(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
