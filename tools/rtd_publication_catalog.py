"""Group frozen RTD links without treating legacy language slots as translations."""
from __future__ import annotations

from pathlib import Path

from tools.publish_locale_identity import stored_payload
from tools.utils.path_utils import PathSegments


def publication_identity(root: Path, source: Path, *, model: str, region: str) -> dict:
    """Read metadata next to the frozen publish tree, never from a live source."""
    relative = source.relative_to(root.resolve())
    meta_root = root.parent / "sources" / PathSegments.WEB
    metadata = meta_root / relative.parent / PathSegments.PUBLISH_META_JSON
    legacy = {"lang": None, "language_scope": "legacy_unspecified", "version": None, "legacy_default": None}
    if not metadata.exists():
        if len(relative.parts) == 5:
            raise ValueError(f"Locale route needs frozen publication metadata: {relative}")
        return legacy
    if not metadata.resolve().is_relative_to(meta_root.resolve()):
        raise ValueError(f"Unsafe publication metadata: {metadata}")
    try:
        payload = stored_payload(metadata, output_dir=root.parent)
    except RuntimeError as exc:
        raise ValueError(f"Invalid publication metadata identity: {metadata}: {exc}") from exc
    if (payload.get("model"), payload.get("region"), payload.get("route"), payload.get("manual")) != (
        model, region, relative.parent.as_posix(), relative.name
    ):
        raise ValueError(f"Publication metadata identity mismatch: {metadata}")
    scope = payload["language_scope"]
    lang = payload.get("lang")
    if scope == "single" and (not isinstance(lang, str) or not lang.strip()):
        raise ValueError(f"Single-language publication needs a language: {metadata}")
    if scope == "single" and (
        payload["schema_version"] != "auto-manual-web-publish-target/v2"
        or len(relative.parts) != 5 or relative.parts[2] != lang
    ):
        raise ValueError(f"Single-language publication route mismatch: {metadata}")
    default = payload.get("legacy_default")
    return {"lang": lang, "language_scope": scope, "version": payload.get("version"), "legacy_default": default}


def group_publications(records: list[dict], language_labels: dict[str, str]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = {}
    for record in records:
        groups.setdefault((record["model"].casefold(), record["region"].casefold()), []).append(record)
    result = []
    for publications in groups.values():
        defaults = [p for p in publications if p["legacy_default"] is True]
        if len(defaults) > 1:
            raise ValueError("Multiple default publications for one product/market")
        if not defaults and len(publications) != 1:
            raise ValueError("Multiple publications need one explicit default")
        current = defaults[0] if defaults else publications[0]
        if not defaults and current["legacy_default"] is False:
            raise ValueError("Explicit non-default publication cannot become default")
        single = {}
        for publication in publications:
            if publication["language_scope"] != "single":
                continue
            lang = publication["lang"]
            if lang not in language_labels:
                raise ValueError(f"Unknown portal publication language: {lang}")
            if lang in single:
                raise ValueError(f"Duplicate portal publication language: {lang}")
            single[lang] = publication["url"]
        options = []
        if current["language_scope"] != "single":
            options.append({"code": "current", "label": "Current publication", "url": current["url"]})
        options.extend({"code": code, "label": label, "url": single.get(code)} for code, label in language_labels.items())
        card = dict(current)
        card.update(publications=publications, language_options=options)
        result.append(card)
    return result
