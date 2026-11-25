"""Convert a workbench review draft (审核稿) into a Web package candidate.

    python -m tools.web.review_draft_web convert DRAFT_DIR --output UNUSED_DIR [--title TITLE] [--release]
    python -m tools.web.review_draft_web gate DRAFT_DIR
    python -m tools.web.review_draft_web changes DRAFT_DIR [--base-dir PREVIOUS_COPY] [--write]

The draft is the only text source (positioning §5.1). ``convert`` strips its
review layer (``review_draft_overlay``), binds every printed block to a
registered shared component (``review_draft_blocks``, ``review_draft_figures``),
writes ``manual.ir.json`` (manual-ir/v2, whole-document-components/v1,
prepared-document), replays it to MyST and writes a conversion report. It
reads no live data and writes nothing outside the unused output directory.

A candidate is never publication-eligible: its IR lists what blocks release in
``pending_source_review``. ``gate`` and ``convert --release`` refuse while
anything blocks: an open issue in the draft's register, a pending marker,
copy awaiting native review, fallback copy, a shared-style issue (including an
undeclared plain table), or a missing 定稿 approval, Web title or release
evidence (typeset full-text compare, parameter cross-check) in ``draft.json``.
Freezing an eligible package under ``manual_sources/``, registering, sealing
and publishing then follow the Git-only release path.

``changes`` compares the working draft's Web copy with its previous version
(``review_draft_changes``); with ``--write`` it records ``web-changes.json``,
which the private review site shows as the version's Web changes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Sequence
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag

from tools.component_specs.registry import load_component_registry, registry_sha256
from tools.component_specs.theme import load_manual_theme, theme_sha256
from tools.manual_ir import (
    ManualSource,
    SourcePage,
    V2_SCHEMA_VERSION,
    build_manual_ir_from_source,
    write_manual_ir,
)
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.document import validate_document
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.whole_document_components import embed_component_claims
from tools.markdown_bundle import _write_myst_sphinx_scaffold
from tools.utils.path_utils import PathSegments
from tools.web.frozen_ai_web import replay_package
from tools.web.prepared_style_audit import audit_prepared_document_styles
from tools.web.presentation import load_web_manual_contract
from tools.web.review_draft_blocks import TABLE_ADAPTERS, DraftChapter
from tools.web.review_draft_changes import CHANGES_JSON, changes_record, write_changes
from tools.web.review_draft_figures import FIGURE_ADAPTERS
from tools.web.review_draft_overlay import ReviewLayerReport, strip_review_layer

DRAFT_MANIFEST = "draft.json"
REPORT_JSON = "review_draft_conversion.json"
REPORT_SCHEMA = "review-draft-web-conversion/v1"
PROJECTION = "whole-document-components/v1"
EVIDENCE_KEYS = ("typeset_compare", "parameter_check")


@dataclass(frozen=True)
class ReviewDraft:
    root: Path
    manifest: dict[str, Any]
    html_path: Path

    @property
    def model(self) -> str:
        return str(self.manifest["model"])

    @property
    def region(self) -> str:
        return str(self.manifest["region"])

    @property
    def language(self) -> str:
        return str(self.manifest["language"])


def markdown_filename(model: str, region: str, language: str) -> str:
    """The candidate's MyST file name; its built page has the same stem."""

    return f"manual_{model.replace('-', '').lower()}_{region.lower()}_{language}.md"


def load_draft(root: Path) -> ReviewDraft:
    root = root.resolve()
    manifest = json.loads((root / DRAFT_MANIFEST).read_text(encoding="utf-8"))
    for key in ("model", "region", "language", "version", "html"):
        if not str(manifest.get(key) or "").strip():
            raise ValueError(f"{root / DRAFT_MANIFEST}: {key} is required")
    html_path = (root / str(manifest["html"])).resolve()
    if not html_path.is_relative_to(root) or not html_path.is_file():
        raise ValueError(f"{root}: draft HTML {manifest['html']!r} is not a file in the package")
    return ReviewDraft(root=root, manifest=manifest, html_path=html_path)


@dataclass
class AssetPackager:
    """Copy each draft image once, by content, into the package."""

    draft_root: Path
    output: Path
    hashes: dict[str, str] = field(default_factory=dict)

    def __call__(self, image: Tag) -> str:
        source = str(image.get("src") or "")
        if source.startswith("assets/ir/"):
            return source
        parsed = urlparse(source)
        file = (self.draft_root / unquote(parsed.path)).resolve()
        if parsed.scheme or parsed.netloc or not file.is_relative_to(self.draft_root) or not file.is_file():
            raise ValueError(f"draft image is not a packaged local asset: {source}")
        digest = file_sha256(file)
        relative = f"assets/ir/{digest}/{file.name}"
        target = self.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(file, target)
        self.hashes[relative] = digest
        image["src"] = relative
        return relative


def _no_file(path: Path) -> str:
    raise ValueError(f"review-draft components bind tagged images only, not {path}")


def chapters_of(draft: ReviewDraft) -> tuple[list[Tag], ReviewLayerReport]:
    soup = BeautifulSoup(draft.html_path.read_text(encoding="utf-8"), "html.parser")
    article = soup.select_one("article#furo-main-content")
    if article is None:
        raise ValueError(f"{draft.html_path}: no manual article (article#furo-main-content)")
    layer = strip_review_layer(article)
    body = article.find("div", recursive=False) or article
    sections = [node for node in body.find_all("section", recursive=False) if node.get("id")]
    if not sections:
        raise ValueError(f"{draft.html_path}: the manual article has no chapter sections")
    return sections, layer


def convert_chapter(draft: ReviewDraft, section: Tag, packager: AssetPackager) -> tuple[SourcePage, DraftChapter]:
    markup = str(section)
    chapter = DraftChapter(
        root=BeautifulSoup(section.decode_contents(), "html.parser"), page_id=str(section["id"]),
        language=draft.language, image_key_prefix=f"{draft.model}/{draft.region}",
    )
    for adapter in (*TABLE_ADAPTERS, *FIGURE_ADAPTERS):
        adapter(chapter)
    for image in chapter.root.find_all("img"):
        packager(image)
    flow = embed_component_claims(
        chapter.root, chapter.claims,
        package_image=packager, package_file=_no_file, package_frozen_file=_no_file,
    )
    page = SourcePage(
        page_id=chapter.page_id, source_ref=f"review-draft/{chapter.page_id}",
        source_path=f"{draft.html_path.name}#{chapter.page_id}", language=draft.language,
        source_sha256=hashlib.sha256(markup.encode("utf-8")).hexdigest(),
        blocks=tuple(("flow", node) for node in flow),
    )
    return page, chapter


def _open_issues(draft: ReviewDraft) -> list[str]:
    name = str(draft.manifest.get("issues") or "")
    if not name:
        return []
    register = json.loads((draft.root / name).read_text(encoding="utf-8"))
    return [f"open issue {item.get('id')} ({item.get('kind')}): {item.get('title')}"
            for item in register.get("issues", []) if item.get("status") == "open"]


def _evidence_blockers(draft: ReviewDraft, html_sha256: str) -> list[str]:
    blockers = []
    approval = draft.manifest.get("approval")
    if not isinstance(approval, dict) or not all(approval.get(k) for k in ("operator", "date", "quote")):
        blockers.append("draft.json records no 定稿 approval (operator, date, quote)")
    elif approval.get("html_sha256") != html_sha256:
        blockers.append("the 定稿 approval does not cover this draft HTML (html_sha256)")
    if not str(draft.manifest.get("web_title") or "").strip():
        blockers.append("draft.json has no web_title")
    evidence = draft.manifest.get("release_evidence") or {}
    for key in EVIDENCE_KEYS:
        path = (draft.root / str(evidence.get(key) or "")).resolve()
        passed = (evidence.get(key) and path.is_relative_to(draft.root) and path.is_file()
                  and json.loads(path.read_text(encoding="utf-8")).get("status") == "pass")
        if not passed:
            blockers.append(f"release evidence {key} is missing or not passed")
    return blockers


def release_blockers(
    draft: ReviewDraft, layer: ReviewLayerReport, chapters: Sequence[DraftChapter], style: dict[str, Any],
) -> list[str]:
    blockers = _open_issues(draft)
    blockers += [f"pending marker {row['marker']}: {row['text'][:80]}" for row in layer.pending]
    blockers += [f"{count} {name.replace('_', ' ')} await native review"
                 for name, count in layer.unreviewed.items() if count]
    blockers += [f"{row['page_id']}: {row['copy']} uses fallback copy ({row['values']})"
                 for chapter in chapters for row in chapter.fallbacks]
    blockers += [f"shared style: {issue}" for issue in style.get("issues", [])]
    return blockers + _evidence_blockers(draft, file_sha256(draft.html_path))


def _source(draft: ReviewDraft, pages: Sequence[SourcePage], metadata: dict[str, Any]) -> ManualSource:
    return ManualSource(
        model=draft.model, region=draft.region, language=draft.language,
        source="prepared-document", bundle_root="review-draft",
        bundle_sha256=value_sha256([(page.page_id, page.source_sha256) for page in pages]),
        snapshot_sha256=None, layout_params_sha256=value_sha256({"layout": "web"}),
        style_contract_sha256=value_sha256(metadata["web_contract"]), pages=tuple(pages),
        metadata=metadata, schema_version=V2_SCHEMA_VERSION,
    )


def _metadata(draft: ReviewDraft, output: Path, pages: Sequence[SourcePage], packager: AssetPackager,
              title: str, filename: str) -> dict[str, Any]:
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    specs = component_specs_in_flow([block for page in pages for _, block in page.blocks])
    return {
        "projection": PROJECTION, "publication_eligible": False, "pending_source_review": [],
        "operator_source_acceptance": draft.manifest.get("approval"),
        "web_source_normalization": "preface-auto-resume/v1",
        "title": title, "markdown_filename": filename, "declared_languages": [draft.language],
        "source_authority": {
            "kind": "review-draft", "model": draft.model, "region": draft.region,
            "version": draft.manifest["version"], "html": draft.html_path.name,
            "html_sha256": file_sha256(draft.html_path), "tools_sha": draft.manifest.get("tools_sha", ""),
        },
        "asset_sha256": dict(sorted(packager.hashes.items())),
        "component_registry": registry, "component_registry_sha256": registry_sha256(registry),
        "manual_theme": theme, "manual_theme_sha256": theme_sha256(theme),
        "web_contract": load_web_manual_contract(model=draft.model, region=draft.region),
        "composites": [], "page_declarations": {},
        "frozen_stylesheet_sha256": file_sha256(output / "_static" / "web_manual.css"),
        "component_inventory": dict(sorted(Counter(spec.component_id for spec in specs).items())),
    }


def convert(draft_root: Path, output: Path, *, title: str | None = None, release: bool = False) -> dict[str, Any]:
    draft = load_draft(draft_root)
    output = output.resolve()
    if output.exists():
        raise ValueError(f"{output}: use an unused output directory")
    title = str(title or draft.manifest.get("web_title") or "").strip()
    if not title:
        raise ValueError("draft.json has no web_title; pass --title")
    sections, layer = chapters_of(draft)
    packager = AssetPackager(draft.root, output)
    converted = [convert_chapter(draft, section, packager) for section in sections]
    pages = [page for page, _ in converted]
    chapters = [chapter for _, chapter in converted]
    filename = markdown_filename(draft.model, draft.region, draft.language)
    _write_myst_sphinx_scaffold(output / filename, title=title, presentation_profile="web")
    with (output / "conf.py").open("a", encoding="utf-8") as stream:
        stream.write("\nlanguage = " + repr(draft.language) + "\n")
    metadata = _metadata(draft, output, pages, packager, title, filename)
    exceptions = [row for chapter in chapters for row in chapter.exceptions]
    style = audit_prepared_document_styles(
        build_manual_ir_from_source(_source(draft, pages, metadata)).to_dict(), exceptions=exceptions)
    blockers = release_blockers(draft, layer, chapters, style)
    if release and blockers:
        raise ValueError("release refused: " + "; ".join(blockers))
    metadata.update(publication_eligible=release, pending_source_review=blockers)
    ir = build_manual_ir_from_source(_source(draft, pages, metadata))
    validate_document(ir)
    write_manual_ir(ir, output / PathSegments.MANUAL_IR_JSON)
    replay_package(output)
    report = {
        "schema_version": REPORT_SCHEMA, "draft": metadata["source_authority"], "title": title,
        "publication_eligible": release, "release_blockers": blockers,
        "component_inventory": metadata["component_inventory"],
        "review_layer": layer.as_json(), "shared_component_exceptions": exceptions,
        "fallback_copy": [row for chapter in chapters for row in chapter.fallbacks],
        "notes": dict(sum((chapter.notes for chapter in chapters), Counter())),
        "shared_style": {key: style.get(key) for key in ("profile", "declared_tables", "issues")},
        "pages": [page.page_id for page in pages],
    }
    (output / REPORT_JSON).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def gate(draft_root: Path) -> list[str]:
    draft = load_draft(draft_root)
    with tempfile.TemporaryDirectory() as scratch:
        report = convert(draft.root, Path(scratch) / "candidate",
                         title=str(draft.manifest.get("web_title") or "untitled"))
    return list(report["release_blockers"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    convert_parser = commands.add_parser("convert", help="write a Web candidate from a review draft")
    convert_parser.add_argument("draft", type=Path)
    convert_parser.add_argument("--output", type=Path, required=True)
    convert_parser.add_argument("--title", help="Web title when draft.json has no web_title")
    convert_parser.add_argument("--release", action="store_true", help="refuse unless nothing blocks release")
    gate_parser = commands.add_parser("gate", help="list what blocks releasing the draft")
    gate_parser.add_argument("draft", type=Path)
    changes_parser = commands.add_parser(
        "changes", help="compare the working draft's Web copy with its previous version")
    changes_parser.add_argument("draft", type=Path)
    changes_parser.add_argument("--base-dir", type=Path, help="a copy of the previous version (default: Git history)")
    changes_parser.add_argument("--write", action="store_true", help=f"write {CHANGES_JSON} beside draft.json")
    args = parser.parse_args(argv)
    if args.command == "changes":
        record = (write_changes if args.write else changes_record)(args.draft.resolve(), base_dir=args.base_dir)
        print(json.dumps({key: record[key] for key in ("base", "head", "counts")}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "gate":
        blockers = gate(args.draft)
        print(json.dumps({"release_blockers": blockers}, ensure_ascii=False, indent=2))
        return 1 if blockers else 0
    report = convert(args.draft, args.output, title=args.title, release=args.release)
    summary = {key: report[key] for key in ("publication_eligible", "component_inventory", "pages")}
    summary["release_blockers"] = len(report["release_blockers"])
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
