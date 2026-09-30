"""Single-language release evidence for frozen external MyST manual sources.

This adapter does not claim a phase2 projection. The source manifest binds the
reviewed inputs and each locale's actual Markdown tree to the sealed outputs.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
from typing import Any
from urllib.parse import unquote, urlsplit

from tools.utils.path_utils import PathSegments
from tools.web_language_release_evidence import (
    RECEIPT_FILENAME,
    VerifiedLanguageReleaseEvidence,
    _file_inventory,
    _json_sha256,
    _load_object,
    _required_sha,
    _required_text,
    _safe_relative,
    _sha256,
    _validated_inventory,
    require_publishable_manual_ir,
    verify_release_evidence as verify_projection_evidence,
)

SOURCE_SCHEMA = "auto-manual-frozen-web-source/v1"
RECEIPT_SCHEMA = "auto-manual-frozen-web-language-evidence/v1"
SOURCE_FILENAME = "frozen_source_manifest.json"


def _source(manifest: dict[str, Any], path: Path, language: str) -> tuple[dict, tuple, Path]:
    if manifest.get("schema_version") != SOURCE_SCHEMA:
        raise RuntimeError("unsupported frozen Web source schema")
    target = manifest.get("target")
    if not isinstance(target, dict):
        raise RuntimeError("frozen Web source requires target identity")
    for field in ("model", "region", "technical_version"):
        _required_text(target, field, source=path)
    languages = target.get("languages")
    if (not isinstance(languages, list) or not languages
            or any(not isinstance(item, str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", item) for item in languages)
            or len(set(languages)) != len(languages) or language not in languages):
        raise RuntimeError("frozen Web source language identity mismatch")
    original = manifest.get("original_source")
    if not isinstance(original, dict):
        raise RuntimeError("frozen Web source requires original source identity")
    _required_text(original, "filename", source=path)
    _required_sha(original.get("sha256"), field="original_source.sha256", source=path)
    inputs = _validated_inventory(manifest.get("inputs"), field="inputs", source=path)
    roots = manifest.get("web_roots")
    if not isinstance(roots, dict) or set(roots) != set(languages):
        raise RuntimeError("frozen Web source requires exact locale roots")
    root = _safe_relative(roots[language], field="web_roots", source=path)
    return target, inputs, root


def _locale_inventory(inputs: tuple, root: Path) -> tuple:
    rows = []
    for row in inputs:
        path = Path(row["path"])
        if path.is_relative_to(root):
            rows.append({**row, "path": path.relative_to(root).as_posix()})
    if not rows:
        raise RuntimeError("frozen Web source has no locale Markdown files")
    return tuple(rows)


class _Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.sources.append(dict(attrs).get("src") or "")


def _verify_images(root: Path) -> None:
    for document in root.rglob("*.html"):
        parser = _Images()
        parser.feed(document.read_text(encoding="utf-8"))
        for source in parser.sources:
            url = urlsplit(source)
            relative = Path(unquote(url.path))
            candidate = (document.parent / relative).resolve()
            if (not source or url.scheme or url.netloc or relative.is_absolute()
                    or not candidate.is_relative_to(root.resolve()) or not candidate.is_file()):
                raise RuntimeError(f"frozen Web HTML image is not a packaged file: {source}")


def seal_frozen_web_evidence(*, source_manifest_path: Path, source_root: Path,
                            language: str, markdown_dir: Path, markdown_name: str,
                            html_dir: Path, evidence_dir: Path, git_ref: str) -> Path:
    require_publishable_manual_ir(markdown_dir)
    manifest = _load_object(source_manifest_path, label="frozen Web source")
    target, inputs, root = _source(manifest, source_manifest_path, language)
    actual = _file_inventory(source_root, excluded_roots=(source_manifest_path,))
    if actual != inputs:
        raise RuntimeError("frozen Web source input files differ from manifest")
    markdown_files = _file_inventory(markdown_dir)
    if markdown_files != _locale_inventory(inputs, root):
        raise RuntimeError("frozen Web Markdown differs from designated locale source")
    if markdown_name not in {row["path"] for row in markdown_files}:
        raise RuntimeError("frozen Web Markdown manual is missing")
    html_files = _file_inventory(html_dir)
    _verify_images(html_dir)
    if "index.html" not in {row["path"] for row in html_files} or not git_ref.strip():
        raise RuntimeError("frozen Web evidence requires HTML index and source Git ref")
    payload = {
        "schema_version": RECEIPT_SCHEMA, "model": target["model"],
        "region": target["region"], "language": language,
        "version": target["technical_version"], "git_ref": git_ref.strip(),
        "source_manifest": {"path": SOURCE_FILENAME, "sha256": _sha256(source_manifest_path)},
        "markdown": {"manual": markdown_name, "files": markdown_files, "sha256": _json_sha256(markdown_files)},
        "html": {"files": html_files, "sha256": _json_sha256(html_files)},
    }
    evidence_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source_manifest_path, evidence_dir / SOURCE_FILENAME)
    receipt = evidence_dir / RECEIPT_FILENAME
    receipt.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def verify_release_evidence(receipt_path: Path, **kwargs: Any) -> VerifiedLanguageReleaseEvidence:
    payload = _load_object(receipt_path, label="Web language release evidence")
    if payload.get("schema_version") != RECEIPT_SCHEMA:
        return verify_projection_evidence(receipt_path, **kwargs)
    return _verify_frozen(receipt_path, payload, **kwargs)


def _verify_frozen(receipt_path: Path, payload: dict, *, expected_sha256: str | None,
                   model: str, region: str, language: str, version: str, git_ref: str,
                   markdown_dir: Path, markdown_name: str, html_dir: Path | None,
                   stored: bool = False) -> VerifiedLanguageReleaseEvidence:
    if receipt_path.name != RECEIPT_FILENAME or (not stored and html_dir is None):
        raise RuntimeError("frozen Web evidence requires canonical receipt and fresh HTML")
    require_publishable_manual_ir(markdown_dir)
    digest = _sha256(receipt_path)
    if expected_sha256 is not None and digest != _required_sha(expected_sha256, field="receipt_sha256", source=receipt_path):
        raise RuntimeError("frozen Web evidence SHA-256 mismatch")
    expected = (model, region, language, version.strip(), git_ref.strip())
    actual = tuple(_required_text(payload, key, source=receipt_path) for key in ("model", "region", "language", "version", "git_ref"))
    if not all(expected) or actual != expected:
        raise RuntimeError("frozen Web release identity mismatch")
    evidence_files = _file_inventory(receipt_path.parent)
    if {row["path"] for row in evidence_files} != {RECEIPT_FILENAME, SOURCE_FILENAME}:
        raise RuntimeError("frozen Web evidence directory has unexpected files")
    binding = payload.get("source_manifest")
    if not isinstance(binding, dict) or binding.get("path") != SOURCE_FILENAME:
        raise RuntimeError("frozen Web evidence source manifest path mismatch")
    source_path = receipt_path.parent / SOURCE_FILENAME
    source_sha = _required_sha(binding.get("sha256"), field="source_manifest.sha256", source=receipt_path)
    if _sha256(source_path) != source_sha:
        raise RuntimeError("frozen Web source manifest SHA-256 mismatch")
    target, inputs, root = _source(_load_object(source_path, label="frozen Web source"), source_path, language)
    if (target["model"], target["region"], target["technical_version"]) != (model, region, version):
        raise RuntimeError("frozen Web source target identity mismatch")
    inventories = {}
    for kind in ("markdown", "html"):
        block = payload.get(kind)
        if not isinstance(block, dict):
            raise RuntimeError(f"frozen Web evidence has invalid {kind}")
        inventory = _validated_inventory(block.get("files"), field=kind, source=receipt_path)
        if _json_sha256(inventory) != _required_sha(block.get("sha256"), field=kind, source=receipt_path):
            raise RuntimeError(f"frozen Web {kind} digest mismatch")
        inventories[kind] = inventory
    if payload["markdown"].get("manual") != markdown_name or markdown_name not in {r["path"] for r in inventories["markdown"]}:
        raise RuntimeError("frozen Web Markdown manual identity mismatch")
    if inventories["markdown"] != _locale_inventory(inputs, root):
        raise RuntimeError("frozen Web Markdown detached from source manifest")
    excluded = (receipt_path.parent, markdown_dir / PathSegments.PUBLISH_META_JSON) if stored else ()
    if _file_inventory(markdown_dir, excluded_roots=excluded) != inventories["markdown"]:
        raise RuntimeError("frozen Web Markdown files differ from evidence")
    if "index.html" not in {r["path"] for r in inventories["html"]}:
        raise RuntimeError("frozen Web evidence missing HTML index")
    if html_dir is not None and _file_inventory(html_dir) != inventories["html"]:
        raise RuntimeError("frozen Web HTML files differ from evidence")
    return VerifiedLanguageReleaseEvidence(receipt_path, digest, model, region, language, source_sha)
