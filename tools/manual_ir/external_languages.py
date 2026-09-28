"""Source-scoped locale identity for frozen external documents, not phase2."""
from __future__ import annotations

import re

from .hashing import value_sha256
from .model import ManualIR, V2_SCHEMA_VERSION


def frozen_language_issues(ir: ManualIR) -> list[str] | None:
    """Keep production registry rules unless this is the explicit frozen adapter.

    The original manifest is carried in the IR and bound to the source bundle
    digest. This permits an approved external locale without claiming that it
    has phase2 columns, print templates or a registered production target.
    """
    if getattr(ir, "source", None) != "frozen-ai-json":
        return None
    manifest = ir.metadata.get("frozen_source_manifest")
    if not isinstance(manifest, dict):
        return ["frozen source language requires its source manifest"]
    target = manifest.get("target", {})
    if not isinstance(target, dict):
        return ["frozen source target must be an object"]
    languages = target.get("languages")
    if (
        ir.schema_version != V2_SCHEMA_VERSION
        or manifest.get("schema_version") != "auto-manual-frozen-web-source/v1"
        or value_sha256(manifest) != ir.bundle_sha256
        or (target.get("model"), target.get("region")) != (ir.model, ir.region)
        or not isinstance(languages, list) or not languages
        or any(not isinstance(code, str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", code)
               for code in languages)
        or len(set(languages)) != len(languages)
        or ir.language not in languages
        or ir.metadata.get("declared_languages") != [ir.language]
        or any(page.language != ir.language for page in ir.pages)
    ):
        return ["frozen source language identity or manifest digest disagrees"]
    return []
