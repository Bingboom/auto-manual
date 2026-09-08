"""Project a frozen bundle into language sources before any Web rendering."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import fields, replace
from pathlib import Path

from tools.gen_index_bundle import MaterializedBundle, read_included_page_paths
from tools.lang_registry import canonical_language
from tools.language_block_trim import trim_language_blocks
from tools.safe_copy import assert_source_tree_no_symlinks
from tools.web_presentation import should_include_web_page

_LANG = re.compile(r"\\HBApplyLang\{([^{}]+)\}")
_INCLUDE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$", re.MULTILINE)


def split_web_bundle(
    bundle: MaterializedBundle, *, language: str, destination: Path,
) -> MaterializedBundle:
    """Keep index order and explicit language identity; never inspect HTML.

    Only generated derivatives are written. Assets were already frozen by the
    shared bundle materializer and retain their bundle-relative paths.
    """
    language = canonical_language(language)
    if not language or language not in bundle.languages:
        raise ValueError(f"Language is outside the frozen bundle: {language!r}")
    source = bundle.bundle_dir.resolve(strict=True)
    destination = destination.resolve()
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError("Language destination must be new and outside the source bundle")
    assert_source_tree_no_symlinks(source, label="Web package bundle")
    paths = read_included_page_paths(bundle.index_path)
    if not paths:
        raise ValueError("Frozen bundle index has no pages")
    mixed = dict(bundle.lang_block_pages)
    selected: list[tuple[Path, Path, str]] = []
    source_hashes = []
    for path in paths:
        path = path.resolve(strict=True)
        if not path.is_relative_to(source):
            raise ValueError(f"Page escapes frozen bundle: {path}")
        if not should_include_web_page(path):
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        relative = path.relative_to(source)
        source_hashes.append({"path": relative.as_posix(), "sha256": hashlib.sha256(raw).hexdigest()})
        if path.name in mixed:
            text, _ = trim_language_blocks(text, languages=[language], page_lang=mixed[path.name])
            text = _LANG.sub(lambda _m: rf"\HBApplyLang{{{language}}}", text)
            relative = relative.with_name(f"{path.stem}_{language}{path.suffix}")
        else:
            declared = {canonical_language(token) for token in _LANG.findall(text)}
            if len(declared) != 1 or None in declared:
                raise ValueError(f"Web page needs one explicit language or lang_blocks: {path}")
            if language not in declared:
                continue
        selected.append((path, relative, text))
    if not selected:
        raise ValueError(f"No Web pages for {language}")
    shutil.copytree(source, destination)
    page_paths = []
    for original, relative, text in selected:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        page_paths.append(target)
    index = destination / bundle.index_path.resolve().relative_to(source)
    index.write_text("\n".join(f".. include:: {p.relative_to(destination).as_posix()}\n" for p in page_paths), encoding="utf-8")
    # Remove unreferenced RST copies from the derivative so a foreign-language
    # source cannot accidentally re-enter its search or an alternate renderer.
    keep = {index.resolve(), *(p.resolve() for p in page_paths)}
    pending = list(page_paths)
    while pending:
        parent = pending.pop()
        for ref in _INCLUDE.findall(parent.read_text(encoding="utf-8")):
            child = (parent.parent / ref).resolve(strict=True)
            if not child.is_relative_to(destination):
                raise ValueError(f"Include escapes derived bundle: {child}")
            if child not in keep:
                keep.add(child)
                pending.append(child)
    for path in destination.rglob("*.rst"):
        if path.resolve() not in keep:
            path.unlink()
    projection = {
        "schema_version": "web-language-bundle/v1", "language": language,
        "model": bundle.model, "region": bundle.region,
        "source_index_sha256": hashlib.sha256(bundle.index_path.read_bytes()).hexdigest(),
        "source_pages": source_hashes,
        "pages": [{"path": p.relative_to(destination).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in page_paths],
    }
    manifest = destination / "bundle_manifest.json"
    manifest.write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changes = {}
    for field in fields(bundle):
        value = getattr(bundle, field.name)
        if isinstance(value, Path) and value.resolve().is_relative_to(source):
            changes[field.name] = destination / value.resolve().relative_to(source)
    changes.update(bundle_dir=destination, page_dir=destination / bundle.page_dir.resolve().relative_to(source),
                   index_path=index, page_paths=tuple(page_paths), lang=language,
                   languages=(language,), lang_block_pages=(), manifest_path=manifest)
    return replace(bundle, **changes)
