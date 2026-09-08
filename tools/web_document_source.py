"""One ordered RST read/parse pass into the public whole-document envelope."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import shutil
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from tools.component_specs.registry import (
    load_component_registry,
    registry_sha256,
)
from tools.component_specs.overview_instance import (
    overview_instance_sha256,
    resolve_overview_instance,
)
from tools.component_specs.theme import load_manual_theme, theme_sha256
from tools.manual_ir import (
    V2_SCHEMA_VERSION,
    ManualSource,
    SourcePage,
    build_manual_ir_from_source,
    write_manual_ir,
)
from tools.manual_ir.document import validate_document
from tools.manual_ir.flow import html_to_flow_nodes
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.whole_document_components import (
    discover_registered_components,
    embed_component_claims,
)
from tools.web_presentation import (
    load_web_manual_contract,
    normalize_web_source_fragment,
)
from tools.utils.path_utils import PathSegments


def _consume_covered_annotations(soup, entry, image):
    """Only consume explicitly bound, unchanged copy already present in art."""
    covered = []
    for binding in entry.get("covered_annotations", []):
        expected = binding["text"]
        if not isinstance(expected, str) or not expected.strip():
            raise ValueError("covered illustration annotation requires nonempty text")
        matches = [node for node in soup.select(binding["selector"])
                   if " ".join(node.get_text(" ", strip=True).split()) == expected]
        if len(matches) != 1 or matches[0].find(["img", "h1", "h2", "h3"]):
            raise ValueError(f"covered illustration annotation changed or ambiguous: {expected}")
        covered.append(expected)
        matches[0].decompose()
    if covered:
        # Preserve the authoritative source copy for accessibility while the
        # visual page uses one finished figure. It also gates stale artwork.
        image["alt"] = "；".join(covered)


def load_web_document(materialized, *, page_paths, declarations, page_languages, active_tags,
                      output_dir: Path, composite_manifest, illustration_manifest: Path | None = None,
                      page_slots: dict[str, str] | None = None):
    from tools.word_bundle_html import (
        _extract_raw_html_blocks, _publish_rst_fragment_to_html,
        _resolve_fragment_lang, _rewrite_word_friendly_fragment, _resolve_fragment_asset_path,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    languages = tuple(getattr(materialized, "languages", ()))
    target_language = materialized.lang or (languages[0] if len(languages) == 1 else "")
    hashes = {}
    contract = load_web_manual_contract(
        model=materialized.model,
        region=materialized.region,
    )
    component_registry = load_component_registry()
    manual_theme = load_manual_theme(component_registry=component_registry)
    overview_instance = (
        resolve_overview_instance(
            model=materialized.model,
            region=materialized.region,
        )
        if contract.get("figure_targets")
        else None
    )
    replacements = {}
    illustration_entries = {}
    text_corrections = []
    provenance = None
    if illustration_manifest is not None:
        provenance = json.loads(illustration_manifest.read_text(encoding="utf-8"))
        if provenance.get("schema_version") != "web-illustrations/v1":
            raise ValueError("unsupported Web illustration manifest")
        if (provenance["model"], provenance["region"], provenance["language"]) != (
            materialized.model, materialized.region, target_language
        ):
            raise ValueError("Web illustration manifest does not match document target")
        for entry in provenance["illustrations"]:
            file = (illustration_manifest.parent / entry["path"]).resolve()
            if not file.is_relative_to(illustration_manifest.parent.resolve()) or file_sha256(file) != entry["sha256"]:
                raise ValueError(f"Web illustration changed: {entry['path']}")
            for index, name in enumerate(entry["replaces"]):
                if name in replacements:
                    raise ValueError("ambiguous Web illustration replacement")
                replacements[name] = file if index == 0 else None
                if index == 0:
                    illustration_entries[name] = entry
        text_corrections = list(provenance.get("text_corrections", []))
        for correction in text_corrections:
            if not all(
                isinstance(correction.get(field), str)
                and correction[field].strip()
                for field in ("selector", "expected", "replacement")
            ):
                raise ValueError(
                    "Web illustration text correction requires selector, expected, and replacement"
                )

    def package_asset(file: Path) -> str:
        digest = file_sha256(file)
        relative = f"assets/ir/{digest}/{file.name}"
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() != file.resolve():
            shutil.copy2(file, target)
        hashes[relative] = digest
        return relative

    def package_presentation_asset(file: Path) -> str:
        digest = file_sha256(file)
        relative = f"assets/{file.stem}_{digest[:12]}{file.suffix}"
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() != file.resolve():
            shutil.copy2(file, target)
        hashes[relative] = digest
        return relative

    source_pages = []
    used_replacements = set()
    used_text_corrections = set()

    def apply_illustration_replacement(soup, image, name):
        if name in used_replacements:
            raise ValueError(f"repeated Web illustration source: {name}")
        used_replacements.add(name)
        replacement = replacements[name]
        if replacement is None:
            image.decompose()
            return
        entry = illustration_entries[name]
        image["src"] = replacement.as_uri()
        image["class"] = [*image.get("class", []), "manual-finished-illustration"]
        image["data-web-finished-panel-path"] = entry["path"]
        image["data-web-finished-panel-sha256"] = entry["sha256"]
        if entry.get("reference_id"):
            image["data-reference-id"] = str(entry["reference_id"])
        image.attrs.pop("width", None)
        image.attrs.pop("height", None)
        image["style"] = "width: 100%; height: auto;"
        _consume_covered_annotations(soup, entry, image)

    for path in page_paths:
        source_bytes = path.read_bytes()
        text = source_bytes.decode("utf-8")
        lang = page_languages.get(path.name) or _resolve_fragment_lang(path, materialized.lang) or target_language
        raw = _extract_raw_html_blocks(text, active_tags=active_tags) if path.name.startswith("safety_") else None
        markup = raw or _publish_rst_fragment_to_html(text, path, active_tags=active_tags)
        markup = _rewrite_word_friendly_fragment(markup, lang=lang)
        early_soup = BeautifulSoup(markup, "html.parser")
        for image in early_soup.find_all("img"):
            name = Path(unquote(urlparse(str(image.get("src", ""))).path)).name
            if (
                name in illustration_entries
                and illustration_entries[name].get("consume_before_presentation")
            ):
                apply_illustration_replacement(early_soup, image, name)
        markup = str(early_soup)
        markup = normalize_web_source_fragment(
            markup,
            source_path=path,
            contract=contract,
            model=materialized.model,
            region=materialized.region,
        )
        soup = BeautifulSoup(markup, "html.parser")
        for index, correction in enumerate(text_corrections):
            if index in used_text_corrections:
                continue
            expected = " ".join(correction["expected"].split())
            matches = [
                node
                for node in soup.select(correction["selector"])
                if " ".join(node.get_text(" ", strip=True).split()) == expected
            ]
            if len(matches) > 1:
                raise ValueError(
                    f"ambiguous Web illustration text correction: {correction['expected']}"
                )
            if matches:
                node = matches[0]
                if node.string is None:
                    raise ValueError(
                        f"Web illustration text correction is not a text-only node: {correction['expected']}"
                    )
                node.string.replace_with(correction["replacement"])
                used_text_corrections.add(index)
        claims = discover_registered_components(
            soup,
            source_path=path,
            contract=contract,
            model=materialized.model or "unspecified",
            region=materialized.region or "unspecified",
            language=lang or "und",
            declared_role=(
                declarations.get(path.resolve())
                or declarations.get(path)
                or None
            ),
            composite_manifest=composite_manifest,
            overview_instance=overview_instance,
        )
        for image in soup.find_all("img"):
            name = Path(unquote(urlparse(str(image.get("src", ""))).path)).name
            if name in replacements:
                apply_illustration_replacement(soup, image, name)
        def package_image(image) -> str:
            src = str(image.get("src", ""))
            if src.startswith("assets/ir/"):
                return src
            parsed = urlparse(src)
            resolved = (
                Path(unquote(parsed.path))
                if parsed.scheme == "file"
                else _resolve_fragment_asset_path(src, path)
            )
            if resolved is None or not resolved.is_file():
                raise ValueError(
                    f"{path}: document image is not a packaged local asset: {src}"
                )
            packaged = package_asset(resolved)
            image["src"] = packaged
            return packaged

        staged = soup
        for image in staged.find_all("img"):
            package_image(image)
        flow_nodes = embed_component_claims(
            staged,
            claims,
            package_image=package_image,
            package_file=package_presentation_asset,
            package_frozen_file=package_asset,
        )
        source_pages.append(SourcePage(
            page_id=path.name, source_ref=path.name, source_path=str(path), language=lang,
            source_sha256=hashlib.sha256(source_bytes).hexdigest(),
            blocks=tuple(("flow", node) for node in flow_nodes),
        ))
    if set(replacements) != used_replacements:
        raise ValueError(f"unused Web illustration bindings: {sorted(set(replacements) - used_replacements)}")
    if len(used_text_corrections) != len(text_corrections):
        unused = [
            correction["expected"]
            for index, correction in enumerate(text_corrections)
            if index not in used_text_corrections
        ]
        raise ValueError(f"unused Web illustration text corrections: {unused}")
    composites = []
    if composite_manifest:
        for entry in composite_manifest.entries:
            composites.append({**entry.to_payload(), "path": package_asset(composite_manifest.source.parent / entry.path)})
    metadata = {"projection": "whole-document-components/v1",
                "web_source_normalization": "preface-auto-resume/v1",
                "title": materialized.title,
                "declared_languages": list(languages), "asset_sha256": hashes,
                "component_registry": component_registry,
                "component_registry_sha256": registry_sha256(component_registry),
                "manual_theme": manual_theme,
                "manual_theme_sha256": theme_sha256(manual_theme),
                "web_contract": contract, "composites": composites,
                "illustration_provenance": provenance,
                "page_declarations": {path.name: role for path, role in declarations.items()},
                "page_slots": {
                    path.name: str((page_slots or {}).get(path.name) or "")
                    for path in page_paths
                    if (page_slots or {}).get(path.name)
                }}
    if overview_instance is not None:
        metadata["overview_instance"] = overview_instance
        metadata["overview_instance_sha256"] = overview_instance_sha256(
            overview_instance
        )
    source = ManualSource(
        model=materialized.model or "unspecified", region=materialized.region or "unspecified",
        language=target_language, source="prepared-document",
        bundle_root=str(getattr(materialized, "bundle_dir", output_dir)),
        bundle_sha256=value_sha256([(p.page_id, p.source_sha256) for p in source_pages]),
        snapshot_sha256=None, layout_params_sha256=value_sha256({"layout": "web"}),
        style_contract_sha256=value_sha256(contract), pages=tuple(source_pages),
        metadata=metadata,
        schema_version=V2_SCHEMA_VERSION,
    )
    ir = build_manual_ir_from_source(source)
    validate_document(ir)
    write_manual_ir(ir, output_dir / PathSegments.MANUAL_IR_JSON)
    return ir
