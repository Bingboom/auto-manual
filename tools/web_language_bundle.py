"""Project a frozen bundle into language sources before any Web rendering."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import fields, replace
from pathlib import Path

from tools.gen_index_bundle import MaterializedBundle, read_included_page_paths
from tools.gen_index_bundle_plan import build_wrapper_index_text
from tools.lang_registry import canonical_language
from tools.language_block_trim import marker_languages, trim_language_blocks
from tools.safe_copy import assert_source_tree_no_symlinks
from tools.web_presentation import should_include_web_page

_LANG = re.compile(r"\\HBApplyLang\{([^{}]+)\}")
_INCLUDE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$", re.MULTILINE)


def _validate_includes(path: Path, *, source: Path, language: str, seen: set[Path]) -> None:
    """Validate transitive includes before writing any derivative files."""
    if path in seen:
        return
    seen.add(path)
    for ref in _INCLUDE.findall(path.read_text(encoding="utf-8")):
        child = (path.parent / ref).resolve(strict=True)
        if not child.is_relative_to(source):
            raise ValueError(f"Include escapes frozen bundle: {child}")
        text = child.read_text(encoding="utf-8")
        declared = {canonical_language(token) for token in _LANG.findall(text)}
        if declared and declared != {language}:
            raise ValueError(f"Included fragment has foreign or unknown language: {child}")
        if set(marker_languages(text)) - {language}:
            raise ValueError(f"Included fragment needs language projection: {child}")
        _validate_includes(child, source=source, language=language, seen=seen)


def _asset_usage_reference(source: Path, raw: object) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Asset usage manifest has an invalid RST reference")
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".rst":
        raise ValueError(f"Asset usage manifest has an unsafe RST reference: {raw!r}")
    try:
        reference = (source / relative).resolve(strict=True)
        reference.relative_to(source)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Asset usage manifest references missing RST: {raw!r}") from exc
    if not reference.is_file():
        raise ValueError(f"Asset usage manifest reference is not a file: {raw!r}")
    return raw


def _load_asset_usage_manifest(source: Path) -> dict | None:
    manifest = source / "asset_usage_manifest.json"
    if not manifest.is_file():
        return None
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid asset usage manifest: {manifest}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid asset usage manifest: {manifest}")

    rewrites = payload.get("rewrites")
    if not isinstance(rewrites, list):
        raise ValueError(f"Asset usage manifest has invalid rewrites: {manifest}")
    for row in rewrites:
        if not isinstance(row, dict):
            raise ValueError(f"Asset usage manifest has an invalid rewrite row: {manifest}")
        _asset_usage_reference(source, row.get("reference_path"))

    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise ValueError(f"Asset usage manifest has invalid assets: {manifest}")
    for row in assets:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("references"), list)
            or not row["references"]
        ):
            raise ValueError(f"Asset usage manifest has an invalid asset row: {manifest}")
        for reference in row["references"]:
            _asset_usage_reference(source, reference)
    return payload


def _project_asset_usage_manifest(
    destination: Path,
    *,
    payload: dict | None,
    keep: set[Path],
) -> None:
    """Keep frozen asset evidence only for RST retained by the projection."""
    if payload is None:
        return
    retained = {path.relative_to(destination).as_posix() for path in keep}
    payload = {
        **payload,
        "rewrites": [
            row for row in payload["rewrites"] if row["reference_path"] in retained
        ],
        "assets": [
            {**row, "references": [ref for ref in row["references"] if ref in retained]}
            for row in payload["assets"]
            if any(ref in retained for ref in row["references"])
        ],
    }

    manifest = destination / "asset_usage_manifest.json"
    manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    if not bundle.index_path.resolve(strict=True).is_relative_to(source):
        raise ValueError("Index escapes frozen bundle")
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
            available = set(marker_languages(text))
            if mixed[path.name]:
                available.add(canonical_language(mixed[path.name]))
            if language not in available:
                raise ValueError(f"Mixed page has no declared block for {language}: {path}")
            owner = canonical_language(mixed[path.name]) if mixed[path.name] else None
            if owner and owner != language and owner not in marker_languages(text):
                # Make the implicit foreign leading block visible to the shared
                # trimmer, which otherwise returns early on in-scope markers.
                text = f"**{owner.upper()} projection boundary**\n\n" + text
            text, _ = trim_language_blocks(text, languages=[language], page_lang=mixed[path.name])
            if set(marker_languages(text)) - {language}:
                raise ValueError(f"Mixed page retains foreign language blocks: {path}")
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
    if len({relative for _, relative, _ in selected}) != len(selected):
        raise ValueError("Projected page paths collide")
    for path, _, _ in selected:
        _validate_includes(path, source=source, language=language, seen=set())
    asset_usage_payload = _load_asset_usage_manifest(source)
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
    _project_asset_usage_manifest(destination, payload=asset_usage_payload, keep=keep)
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


def materialize_web_language_projection(
    bundle: MaterializedBundle,
    *,
    language: str,
    destination: Path,
    write_wrapper_index: bool,
) -> MaterializedBundle:
    """Validate in a fresh directory, then replace the canonical RST bundle."""
    destination = destination.absolute()
    if destination.is_symlink() or destination.parent.is_symlink():
        raise ValueError(f"Web language destination must not use a symbolic link: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or destination.parent.is_symlink():
        raise ValueError(f"Web language destination must not use a symbolic link: {destination}")
    destination = destination.resolve()
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"Web language destination must be a real directory: {destination}")
    wrapper_text = None
    wrapper_temp = None
    if write_wrapper_index:
        wrapper_text = build_wrapper_index_text(
            docs_dir=bundle.wrapper_index_path.parent.resolve(),
            bundle_dir=destination,
        )

    temporary_root = Path(
        tempfile.mkdtemp(prefix=".web-language-projection.", dir=destination.parent)
    )
    candidate = temporary_root / destination.name
    previous = temporary_root / "previous"
    preserve_temporary_root = False
    try:
        projected = split_web_bundle(bundle, language=language, destination=candidate)
        if wrapper_text is not None:
            wrapper_fd, wrapper_name = tempfile.mkstemp(
                prefix=f".{bundle.wrapper_index_path.name}.",
                dir=bundle.wrapper_index_path.parent,
            )
            os.close(wrapper_fd)
            wrapper_temp = Path(wrapper_name)
            wrapper_temp.write_text(wrapper_text, encoding="utf-8")
        if destination.exists():
            destination.rename(previous)
        try:
            candidate.rename(destination)
            if wrapper_temp is not None:
                os.replace(wrapper_temp, bundle.wrapper_index_path)
        except Exception as original_error:
            try:
                if destination.exists():
                    shutil.rmtree(destination)
                if previous.exists():
                    previous.rename(destination)
            except Exception as rollback_error:
                preserve_temporary_root = previous.exists()
                backup = f"; previous bundle preserved at {previous}" if preserve_temporary_root else ""
                raise RuntimeError(
                    f"Web language projection failed and rollback could not restore the destination{backup}"
                ) from rollback_error
            raise original_error

        changes = {}
        for field in fields(projected):
            value = getattr(projected, field.name)
            if isinstance(value, tuple) and value and all(
                isinstance(item, Path) for item in value
            ):
                try:
                    changes[field.name] = tuple(
                        destination / item.relative_to(candidate) for item in value
                    )
                except ValueError:
                    pass
                continue
            if not isinstance(value, Path):
                continue
            try:
                relative = value.relative_to(candidate)
            except ValueError:
                continue
            changes[field.name] = destination / relative
        if previous.exists():
            shutil.rmtree(previous)
        return replace(projected, **changes)
    finally:
        if wrapper_temp is not None:
            wrapper_temp.unlink(missing_ok=True)
        if not preserve_temporary_root:
            shutil.rmtree(temporary_root, ignore_errors=True)
