"""Opt-in Sphinx integration for downstream product-intelligence research."""
from __future__ import annotations

import json
from pathlib import Path

from tools.utils.path_utils import PathSegments, repo_root, static_dir_of

KNOWLEDGE_JSON = "product-knowledge.v1.json"
RESEARCH_JSON = "product-intelligence.v1.json"


def clear_research_outputs(app) -> None:
    """Remove only this demo's outputs so a reused directory cannot leak old research."""
    if getattr(app.builder, "format", "") != "html":
        return
    from tools.rtd.product_research import PAGE

    output = Path(app.outdir)
    paths = (output / f"{PAGE}.html",
             static_dir_of(output) / KNOWLEDGE_JSON,
             static_dir_of(output) / RESEARCH_JSON)
    for path in paths:
        path.unlink(missing_ok=True)


def demo_enabled(app) -> bool:
    """Public manuals never build research, regardless of the opt-in flag."""
    if getattr(app.config, "rtd_site_role", "combined") == "manuals":
        return False
    value = getattr(app.config, "rtd_product_intelligence_demo", False)
    if value in (True, "1", "true"):
        return True
    if value in (False, None, "", "0", "false"):
        return False
    raise ValueError("rtd_product_intelligence_demo must be true/false or 1/0")


def research_bundle(app, assets: Path, settings: dict, catalog: list,
                    knowledge_root: Path) -> tuple[dict, dict]:
    """Derive once per build from frozen inputs; never write source records."""
    cached = getattr(app, "_rtd_research_bundle", None)
    if cached is not None:
        return cached
    from tools.product_knowledge import build_product_knowledge
    from tools.rtd.product_intelligence import research_context

    source = Path(app.srcdir)
    manifest_path = source.parent / PathSegments.PUBLISH_MANIFEST_JSON
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {"targets": []}
    knowledge = build_product_knowledge(repo_root(), source, manifest, assets, settings, catalog)
    research = research_context(knowledge, knowledge_root)
    app._rtd_research_bundle = (knowledge, research)
    return knowledge, research


def write_research_exports(app, exception) -> None:
    """Publish versioned consumer artifacts only alongside the opted-in page."""
    if exception is not None or getattr(app.builder, "format", "") != "html" or not demo_enabled(app):
        return
    bundle = getattr(app, "_rtd_research_bundle", None)
    if bundle is None:
        return
    destination = static_dir_of(Path(app.outdir))
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in zip((KNOWLEDGE_JSON, RESEARCH_JSON), bundle, strict=True):
        (destination / name).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8",
        )
