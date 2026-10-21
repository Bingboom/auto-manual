"""Opt-in Sphinx integration for external intelligence and its optional product lens.

Events and their decision digest come from the business knowledge snapshot and
never wait on product data: a missing or broken product input only marks the
lens unavailable. A malformed events file skips this page, with a warning, and
no other page. Public manuals never build any of it.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from tools.utils.path_utils import PathSegments, repo_root, static_dir_of

EVENTS_JSON = "external-intel.v1.json"
DIGEST_JSON = "external-intel-digest.v1.json"
DIGEST_TEXT = "external-intel-digest.v1.md"
KNOWLEDGE_JSON = "product-knowledge.v1.json"
LENS_JSON = "product-intelligence.v1.json"
OUTPUTS = (EVENTS_JSON, DIGEST_JSON, DIGEST_TEXT, KNOWLEDGE_JSON, LENS_JSON)
_TRUE, _FALSE = {"1", "true", "yes", "on"}, {"", "0", "false", "no", "off"}


def parse_flag(value: object) -> bool:
    """A boolean, 1/0 or a true/false, yes/no, on/off spelling in any case; anything else raises."""
    if isinstance(value, bool) or value is None:
        return bool(value)
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in _TRUE | _FALSE:
        return value.strip().lower() in _TRUE
    raise ValueError(f"rtd_product_intelligence_demo must be true/false, 1/0, yes/no or on/off, got {value!r}")


def validate_flag(app, config) -> None:
    """Reject a misspelt flag once, at configuration time, whatever the site role."""
    from sphinx.errors import ConfigError

    try:
        parse_flag(config.rtd_product_intelligence_demo)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def demo_enabled(app) -> bool:
    """Public manuals never build research, regardless of the opt-in flag."""
    if getattr(app.config, "rtd_site_role", "combined") == "manuals":
        return False
    return parse_flag(getattr(app.config, "rtd_product_intelligence_demo", False))


def research_available(app) -> bool:
    """Whether this build has the research page; links to it follow this, not the flag."""
    return getattr(app, "_rtd_research", None) is not None


def clear_research_outputs(app) -> None:
    """Remove only this demo's outputs so a reused directory cannot leak old research."""
    if getattr(app.builder, "format", "") != "html":
        return
    from tools.rtd.product_research import PAGE

    output = Path(app.outdir)
    for path in (output / f"{PAGE}.html", *(static_dir_of(output) / name for name in OUTPUTS)):
        path.unlink(missing_ok=True)


def _lens_problem(exc: Exception) -> str:
    """Page text for an unusable product input; local file paths stay in the build log."""
    if isinstance(exc, OSError):
        return f"产品知识快照不可用：读取冻结发布资料失败（{exc.strerror}）。"
    if isinstance(exc, (ValueError, csv.Error)):
        return f"产品知识快照不可用：{exc}"
    return f"产品知识快照不可用：发布资料结构异常（{type(exc).__name__}）。"


def _product_lens(app, assets: Path, settings: dict, catalog: list, intel: dict, logger) -> tuple:
    from tools.product_knowledge import build_product_knowledge
    from tools.rtd.product_intelligence import product_lens_context

    source = Path(app.srcdir)
    try:
        knowledge = build_product_knowledge(repo_root(), source, source.parent / PathSegments.PUBLISH_MANIFEST_JSON,
                                            assets, settings, catalog)
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as exc:
        logger.warning("External intelligence product lens unavailable: %s", exc)
        return None, None, _lens_problem(exc)
    lens = product_lens_context(knowledge, intel)
    for entry in lens["lenses"]:
        for problem in entry["problems"]:
            logger.warning("External intelligence event %s product lens: %s", entry["event_id"], problem)
    return knowledge, lens, ""


def build_research(app, assets: Path, settings: dict, catalog: list, knowledge_root: Path,
                   base_url: str) -> dict | None:
    """Events first; the product lens only for events that ask for one, and only if its inputs read."""
    from sphinx.util import logging as sphinx_logging
    from tools.rtd.decision_digest import decision_digest
    from tools.rtd.intelligence_events import load_events
    from tools.rtd.product_research import PAGE

    logger = sphinx_logging.getLogger(__name__)
    try:
        intel = load_events(knowledge_root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        logger.warning("External intelligence page skipped: %s", exc)
        return None
    knowledge = lens = None
    problem = ""
    if any(event["product_lens"] is not None for event in intel["events"]):
        knowledge, lens, problem = _product_lens(app, assets, settings, catalog, intel, logger)
    return {"intel": intel, "digest": decision_digest(intel, page=PAGE, base_url=base_url),
            "knowledge": knowledge, "lens": lens, "lens_problem": problem}


def research_page(research: dict) -> dict:
    """The page context, with downloads for exactly the exports this build writes."""
    from tools.rtd.product_research import research_page_context

    items = [("外部事件 JSON", EVENTS_JSON), ("决策摘要 JSON", DIGEST_JSON), ("决策摘要文本（Markdown）", DIGEST_TEXT)]
    if research["lens"] is not None:
        items += [("附录 · 产品知识 JSON", KNOWLEDGE_JSON), ("附录 · 产品关联 JSON", LENS_JSON)]
    return research_page_context(
        research["intel"], lens=research["lens"], knowledge=research["knowledge"],
        lens_problem=research["lens_problem"],
        downloads=tuple((label, f"{PathSegments.STATIC}/{name}") for label, name in items),
    )


def write_research_exports(app, exception) -> None:
    """Publish versioned consumer artifacts only alongside the page that offers them."""
    research = getattr(app, "_rtd_research", None)
    if exception is not None or getattr(app.builder, "format", "") != "html" or research is None:
        return
    destination = static_dir_of(Path(app.outdir))
    destination.mkdir(parents=True, exist_ok=True)
    payloads = {EVENTS_JSON: research["intel"], DIGEST_JSON: research["digest"],
                KNOWLEDGE_JSON: research["knowledge"], LENS_JSON: research["lens"]}
    for name, payload in payloads.items():
        if payload is not None:
            (destination / name).write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8",
            )
    (destination / DIGEST_TEXT).write_text(research["digest"]["text"], encoding="utf-8")
