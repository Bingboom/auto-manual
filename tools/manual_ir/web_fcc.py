"""Prepared FCC source and its semantic public-IR projection contract."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from tools.component_specs.fcc import fcc_component_spec, fcc_semantic_projection
from tools.component_specs.fcc_html import parse_fcc_html
from tools.component_specs.model import ComponentSpec
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles
from tools.manual_ir import ManualIR, ManualIRValidationError, validate_manual_ir
from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.source import ManualSource
from tools.manual_ir.web_source import make_web_source


def load_web_fcc_source(
    html: str, *, source_path: Path, config: Mapping[str, Any],
    language: str | None = None, model: str | None = None, region: str | None = None,
) -> ManualSource:
    parsed = parse_fcc_html(
        BeautifulSoup(html, "html.parser"), source_path=source_path, config=config,
        language=language, error_type=ValueError,
    )
    registry = load_component_registry()
    payload = {
        "component_spec": parsed.spec.to_dict(),
        "mark_binding": {"asset_ref": parsed.spec.assets[0].asset_ref, "src": config["mark_path"]},
    }
    return make_web_source(
        html, source_path=source_path, blocks=(("web_fcc", payload),), projection="web-fcc",
        language=parsed.spec.language, model=model, region=region,
        style_contract_sha256=value_sha256({
            "registry": registry, "theme": load_manual_theme(component_registry=registry),
            "fcc_source_config": dict(config),
        }),
    )


def decode_fcc_ir(ir: ManualIR) -> tuple[ComponentSpec, str]:
    """Replay requires semantic data and a bound mark, never source HTML/config."""
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if (ir.metadata.get("projection") != "web-fcc" or len(ir.pages) != 1
            or len(ir.pages[0].blocks) != 1):
        raise ValueError("expected a single-block web-fcc projection")
    page = ir.pages[0]
    block = page.blocks[0]
    payload = block.payload
    if (block.kind != "web_fcc" or not isinstance(payload, dict)
            or set(payload) != {"component_spec", "mark_binding"}
            or not isinstance(payload["component_spec"], dict)):
        raise ValueError(f"{block.source_ref}: incomplete Web FCC payload")
    spec = require_component_theme_roles(require_valid_component_spec(
        ComponentSpec.from_dict(payload["component_spec"]),
    ))
    projection = fcc_semantic_projection(spec)
    canonical = fcc_component_spec(
        accessibility_label=projection["accessibility_label"],
        opening_copy=projection["opening_copy"], left_blocks=projection["left_blocks"],
        right_blocks=projection["right_blocks"], source_ref=Path(page.source_ref).as_posix(),
        language=page.language, mark_asset_ref=projection["mark_asset_ref"], metadata=spec.metadata,
    )
    if value_sha256(canonical.to_dict()) != value_sha256(payload["component_spec"]):
        raise ValueError(f"{block.source_ref}: noncanonical FCC semantics or source identity")
    binding = payload["mark_binding"]
    if (not isinstance(binding, dict) or set(binding) != {"asset_ref", "src"}
            or binding["asset_ref"] != projection["mark_asset_ref"]
            or not isinstance(binding["src"], str) or not binding["src"].strip()):
        raise ValueError(f"{block.source_ref}: FCC mark binding does not match its semantic asset")
    return spec, binding["src"]
