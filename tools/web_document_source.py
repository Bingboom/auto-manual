"""One ordered RST read/parse pass into the public whole-document envelope."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import shutil
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from tools.manual_ir import ManualSource, SourcePage, build_manual_ir_from_source, write_manual_ir
from tools.manual_ir.document import content_tree, validate_document
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.web_presentation import load_web_manual_contract


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
                      output_dir: Path, composite_manifest, illustration_manifest: Path | None = None):
    from tools.word_bundle_html import (
        _extract_raw_html_blocks, _publish_rst_fragment_to_html,
        _resolve_fragment_lang, _rewrite_word_friendly_fragment, _resolve_fragment_asset_path,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    languages = tuple(getattr(materialized, "languages", ()))
    target_language = materialized.lang or (languages[0] if len(languages) == 1 else "")
    hashes = {}
    replacements = {}
    illustration_entries = {}
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

    def package_asset(file: Path) -> str:
        digest = file_sha256(file)
        relative = f"assets/ir/{digest}/{file.name}"
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() != file.resolve():
            shutil.copy2(file, target)
        hashes[relative] = digest
        return relative

    source_pages = []
    used_replacements = set()
    for path in page_paths:
        source_bytes = path.read_bytes()
        text = source_bytes.decode("utf-8")
        lang = page_languages.get(path.name) or _resolve_fragment_lang(path, materialized.lang) or target_language
        raw = _extract_raw_html_blocks(text, active_tags=active_tags) if path.name.startswith("safety_") else None
        markup = raw or _publish_rst_fragment_to_html(text, path, active_tags=active_tags)
        markup = _rewrite_word_friendly_fragment(markup, lang=lang)
        soup = BeautifulSoup(markup, "html.parser")
        for image in soup.find_all("img"):
            name = Path(unquote(urlparse(str(image.get("src", ""))).path)).name
            if name in replacements:
                if name in used_replacements:
                    raise ValueError(f"repeated Web illustration source: {name}")
                used_replacements.add(name)
                if replacements[name] is None:
                    image.decompose()
                else:
                    image["src"] = replacements[name].as_uri()
                    image["class"] = [*image.get("class", []), "manual-finished-illustration"]
                    image.attrs.pop("width", None)
                    image.attrs.pop("height", None)
                    image["style"] = "width: 100%; height: auto;"
                    _consume_covered_annotations(soup, illustration_entries[name], image)
        staged = soup
        for image in staged.find_all("img"):
            src = str(image.get("src", ""))
            parsed = urlparse(src)
            resolved = Path(unquote(parsed.path)) if parsed.scheme == "file" else _resolve_fragment_asset_path(src, path)
            if resolved is None or not resolved.is_file():
                raise ValueError(f"{path}: document image is not a packaged local asset: {src}")
            image["src"] = package_asset(resolved)
        source_pages.append(SourcePage(
            page_id=path.name, source_ref=path.name, source_path=str(path), language=lang,
            source_sha256=hashlib.sha256(source_bytes).hexdigest(), blocks=(("document_content", content_tree(str(staged))),),
        ))
    if set(replacements) != used_replacements:
        raise ValueError(f"unused Web illustration bindings: {sorted(set(replacements) - used_replacements)}")
    composites = []
    if composite_manifest:
        for entry in composite_manifest.entries:
            composites.append({**entry.to_payload(), "path": package_asset(composite_manifest.source.parent / entry.path)})
    contract = load_web_manual_contract()
    source = ManualSource(
        model=materialized.model or "unspecified", region=materialized.region or "unspecified",
        language=target_language, source="prepared-document",
        bundle_root=str(getattr(materialized, "bundle_dir", output_dir)),
        bundle_sha256=value_sha256([(p.page_id, p.source_sha256) for p in source_pages]),
        snapshot_sha256=None, layout_params_sha256=value_sha256({"layout": "web"}),
        style_contract_sha256=value_sha256(contract), pages=tuple(source_pages),
        metadata={"projection": "whole-document-content/v1", "title": materialized.title,
                  "declared_languages": list(languages), "asset_sha256": hashes,
                  "web_contract": contract, "composites": composites,
                  "illustration_provenance": provenance,
                  "page_declarations": {path.name: role for path, role in declarations.items()}},
    )
    ir = build_manual_ir_from_source(source)
    validate_document(ir)
    write_manual_ir(ir, output_dir / "manual.ir.json")
    return ir
