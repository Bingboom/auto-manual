"""Dry-run inventory of the Git-tracked production art for the Feishu 04_资产* tables.

The design (code-as-doc/dev/asset_base_inventory.md) keeps the three existing
asset tables: one master per row in 04_资产源文件, one image identity per row in
04_资产定义, and one file per row, carrying the file itself as its attachment,
in 04_资产导出物. This module stages those rows from the working tree only:

* the four production-art folders: shared Web, per-target Web, print (LaTeX)
  and Word common assets;
* the records that already name those files: the shared symbol and button
  manifests, data/asset_registry.csv and the per-target Web illustration
  manifests, plus the extraction recipes and data/asset_sources.csv.

It writes CSV and JSON to an explicit output directory and never calls Feishu;
the live upload is a separate, operator-gated step with record-by-record
read-back. Only a registry row's status approves a file. Keys and values the
dry run had to propose are flagged ``needs_review`` instead of being presented
as facts. Definitions the registry already holds are staged in its exact
spelling, and summary.json previews what the next sync-data would write to
data/asset_registry.csv if the staged definitions were live.

Given ``--live-snapshot`` (lark-cli JSON of the three live tables, saved
read-only beforehand), each row also gets an action against what the Base
already holds; see tools/asset_pipeline/base_reconcile.py.
"""
from __future__ import annotations

import argparse
import collections
from collections.abc import Callable
import csv
import hashlib
import json
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any

from PIL import Image

from tools.asset_pipeline.base_reconcile import (
    GIT_EXPORT_PREFIX,
    LiveIndex,
    LiveRecord,
    SnapshotError,
    load_snapshot,
    reconcile_definitions,
    reconcile_exports,
    reconcile_sources,
    report_duplicates,
)
from tools.asset_registry import (
    APPROVED_STATUS,
    LOCALIZED_LANGUAGE_DIMENSION,
    MISSING_STATUS,
    NEUTRAL_LANGUAGE_DIMENSION,
    QUARANTINED_STATUS,
    TEMPORARY_STATUS,
    REGISTRY_RELATIVE_PATH,
    AssetRecord,
    AssetRegistryError,
    load_registry,
    load_registry_bytes,
    registered_exports,
)
from tools.sync_asset_registry import OWNED_COLUMNS, definition_rows, merge_registry_csv
from tools.utils.path_utils import PathSegments, Paths, latex_renderer_of, repo_root, word_common_assets_of

SCHEMA = "asset-base-inventory/v1"
SHARED = "shared"
ART_SUFFIXES = frozenset({".png", ".svg", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"})
SYMBOLS_MANIFEST_SCHEMA = "auto-manual-shared-web-symbols/v1"
ASSET_SOURCES_CSV = "asset_sources.csv"
ASSET_RECIPES_DIR = "asset_recipes"
ILLUSTRATIONS_GLOB = "*_illustrations.json"
# The staged CSVs are review material, never repository data.
FORBIDDEN_OUTPUT_ROOTS = (PathSegments.DOCS, PathSegments.DATA, "tools")
KEY_PREFIXES = {"web-shared": "web-shared", "web-target": "web", "print": "print", "word": "word"}
REGISTRY_ORIGIN = REGISTRY_RELATIVE_PATH.name
# 04_资产源文件.archive_status for a master registered without its files yet.
SOURCE_TO_VERIFY = "待校验"
PENDING = "pending"
BASE_ORIGIN = "base"
# The registry status behind a gate, in the gate vocabulary 04_资产定义 already uses.
REGISTRY_GATES = {APPROVED_STATUS: "approved", QUARANTINED_STATUS: "quarantine",
                  TEMPORARY_STATUS: "temporary", MISSING_STATUS: "missing"}

# 04_资产源文件 fields first, then review-only columns that are never uploaded.
SOURCE_COLUMNS = (
    "source_key", "source_kind", "source_format", "source_scope_model", "source_scope_region",
    "source_scope_lang", "document_revision", "registry_revision", "page_count", "page_width_mm",
    "page_height_mm", "source_sha256", "archive_status", "notes",
    "source_pointer", "source_name", "registered_in", "needs_review", "action", "live_record_id",
)
# 04_资产定义 fields first, then review-only columns that are never uploaded.
DEFINITION_COLUMNS = (
    "asset_key", "category", "language_dimension", "status", "textless_pending", "model_scope",
    "region_scope", "language_variants", "override_for", "gate_status", "build_eligible",
    "visual_review_required", "source_key", "source_page", "source_crop", "notes",
    "replaces", "git_exports", "key_origin", "registered_in", "needs_review", "action", "live_record_id",
)
# 04_资产导出物 fields, the two proposed new fields (pixel_size, has_alpha), then review-only columns.
EXPORT_COLUMNS = (
    "export_key", "asset_key", "artifact_kind", "format", "repo_path", "size_bytes", "content_sha256",
    "locale", "gate_status", "build_eligible", "visual_review_required", "source_key", "source_page",
    "notes", "pixel_size", "has_alpha",
    "source_crop", "registered_in", "needs_review", "action", "live_record_id", "fill_fields",
)
FINDING_COLUMNS = ("kind", "subject", "detail")

_SVG_VIEWBOX = re.compile(rb'viewBox\s*=\s*["\']\s*[-+\d.eE]+[\s,]+[-+\d.eE]+[\s,]+([\d.eE+]+)[\s,]+([\d.eE+]+)')
_FILENAME_LANGUAGE = re.compile(r"[-_]([a-z]{2,3})$")


class InventoryError(ValueError):
    """An input registry is unreadable or the output location is unsafe."""


@dataclass(frozen=True)
class ArtRoot:
    kind: str
    path: Path


@dataclass(frozen=True)
class ArtFile:
    repo_path: str
    kind: str
    fmt: str
    size_bytes: int
    sha256: str
    pixel_size: str
    has_alpha: str


@dataclass(frozen=True)
class ManifestEntry:
    """One file a shared symbol or button manifest names."""

    key: str
    sha256: str
    registered_in: str
    source_key: str
    note: str


@dataclass(frozen=True)
class IllustrationUse:
    """One per-target Web illustration manifest entry that binds a file."""

    manifest: str
    model: str
    region: str
    language: str
    sha256: str
    source_key: str
    source_sha256: str
    source_name: str
    source_page: str
    source_crop: str
    replaces: tuple[str, ...]


@dataclass(frozen=True)
class RegistryExport:
    """One file a data/asset_registry.csv row names, resolved as asset-check resolves it."""

    record: AssetRecord
    repo_path: str
    digest: str


@dataclass(frozen=True)
class Identity:
    asset_key: str
    origin: str
    registered_in: tuple[str, ...]
    record: AssetRecord | None = None
    manifest: ManifestEntry | None = None
    uses: tuple[IllustrationUse, ...] = ()
    # Other registry rows that name the same file.
    aliases: tuple[str, ...] = ()
    # A registered export with the same bytes, when the row does not list this file.
    copy_of: str = ""
    # The registry or Base status behind the key; empty when nobody has decided yet.
    status: str = ""


@dataclass
class Context:
    repo_root: Path
    roots: tuple[ArtRoot, ...]
    records: tuple[AssetRecord, ...]
    registry_rows: dict[str, dict[str, str]]
    registry_by_path: dict[str, list[RegistryExport]]
    registry_by_sha: dict[str, list[RegistryExport]]
    registry_folders: dict[str, set[str]]
    shared: dict[str, ManifestEntry]
    withdrawn: dict[str, dict[str, str]]
    uses: dict[str, list[IllustrationUse]]
    recipes: dict[str, tuple[str, str, str]]
    masters: list[dict[str, str]]
    master_by_sha: dict[str, str]
    conventions: dict[str, tuple[str, str]]
    # Lower-case region and language codes the registry names, for reading unregistered file paths.
    regions: frozenset[str]
    languages: frozenset[str]
    live: LiveIndex | None = None


@dataclass
class Inventory:
    sources: dict[str, dict[str, Any]] = field(default_factory=dict)
    definitions: dict[str, dict[str, Any]] = field(default_factory=dict)
    exports: list[dict[str, str]] = field(default_factory=list)
    findings: list[dict[str, str]] = field(default_factory=list)

    def find(self, kind: str, subject: str, detail: str) -> None:
        self.findings.append({"kind": kind, "subject": subject, "detail": detail})


def _flag(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def _slug(text: str) -> str:
    return text.strip().lower().replace("_", "-").replace(" ", "-")


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot read {path}: {exc}") from exc


def art_roots(root: Path) -> tuple[ArtRoot, ...]:
    """The production-art folders, most specific first (shared Web sits inside Web)."""
    docs = Paths(root=root).docs_dir
    web_assets = docs / PathSegments.RENDERERS / PathSegments.WEB / PathSegments.ASSETS
    return (
        ArtRoot("web-shared", web_assets / SHARED),
        ArtRoot("web-target", web_assets),
        ArtRoot("print", latex_renderer_of(docs) / PathSegments.ASSETS),
        ArtRoot("word", word_common_assets_of(docs)),
    )


def _listed_files(root: Path, roots: tuple[ArtRoot, ...], *, tracked_only: bool) -> list[Path]:
    if tracked_only:
        names = [_rel(art_root.path, root) for art_root in roots]
        try:
            result = subprocess.run(
                ["git", "-c", "core.quotePath=false", "ls-files", "-z", "--", *names],
                cwd=root, capture_output=True, text=True, check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise InventoryError(f"git ls-files failed in {root}: {exc}") from exc
        candidates = [root / name for name in result.stdout.split("\0") if name]
    else:
        candidates = [path for art_root in roots if art_root.path.is_dir() for path in art_root.path.rglob("*")]
    return sorted({path for path in candidates
                   if path.suffix.lower() in ART_SUFFIXES and path.is_file() and not path.is_symlink()})


def _image_facts(path: Path, data: bytes, fmt: str) -> tuple[str, str]:
    """(pixel size, alpha channel) for raster art; the viewBox size for SVG."""
    if fmt == "svg":
        match = _SVG_VIEWBOX.search(data)
        return (f"{float(match.group(1)):g}x{float(match.group(2)):g}" if match else ""), ""
    if fmt == "pdf":
        return "", ""
    try:
        with Image.open(path) as image:
            alpha = image.mode in {"RGBA", "LA", "PA"} or "transparency" in image.info
            return f"{image.width}x{image.height}", _flag(alpha)
    except (OSError, ValueError):
        return "", ""


def _art_file(path: Path, root: Path, roots: tuple[ArtRoot, ...]) -> ArtFile:
    art_root = next(item for item in roots if path.is_relative_to(item.path))
    data = path.read_bytes()
    fmt = path.suffix.lower().lstrip(".")
    fmt = "jpg" if fmt == "jpeg" else fmt
    pixel_size, has_alpha = _image_facts(path, data, fmt)
    return ArtFile(_rel(path, root), art_root.kind, fmt, len(data), hashlib.sha256(data).hexdigest(),
                   pixel_size, has_alpha)


def _recipe_sources(root: Path) -> dict[str, tuple[str, str, str]]:
    """Recipe stem -> (source_key, expected SHA-256, expected page count)."""
    recipes: dict[str, tuple[str, str, str]] = {}
    for path in sorted((Paths(root=root).data_dir / ASSET_RECIPES_DIR).glob("*.json")):
        if path.name.endswith(".schema.json"):
            continue
        source = (_json(path) or {}).get("source")
        if isinstance(source, dict) and source.get("source_key"):
            recipes[path.stem] = (str(source["source_key"]), str(source.get("expected_sha256") or ""),
                                  str(source.get("expected_page_count") or ""))
    return recipes


def _recipe_key(recipe: Any, recipes: dict[str, tuple[str, str, str]]) -> str:
    return recipes.get(PurePosixPath(str(recipe or "")).stem, ("",))[0]


def _shared_manifests(root: Path, recipes: dict) -> tuple[dict[str, ManifestEntry], dict[str, dict[str, str]]]:
    """repo_path -> entry for the shared symbol and button manifests; withdrawn SHA-256 -> record."""
    shared = art_roots(root)[0].path
    symbols = _json(shared / "symbols" / "manifest.json")
    if symbols.get("schema_version") != SYMBOLS_MANIFEST_SCHEMA:
        raise InventoryError("unsupported shared Web symbol manifest")
    entries: dict[str, ManifestEntry] = {}
    for asset in symbols["assets"]:
        provenance = asset.get("provenance") or {}
        entries[_rel(shared / "symbols" / asset["path"], root)] = ManifestEntry(
            asset["key"], asset["sha256"], "symbols-manifest", _recipe_key(provenance.get("recipe"), recipes),
            f"清单状态：{asset.get('status', '')}" if asset.get("status") else "",
        )
    buttons = _json(shared / "buttons" / "manifest.json")
    button_source = _recipe_key(buttons.get("source_recipe"), recipes)
    for asset in buttons["assets"]:
        entries[_rel(shared / "buttons" / asset["asset"], root)] = ManifestEntry(
            asset["semantic_key"], asset["sha256"], "buttons-manifest", button_source,
            f"文字策略：{asset.get('text_policy', '')}" if asset.get("text_policy") else "",
        )
    withdrawn = {item["sha256"]: {"path": item["path"], "reason": item.get("reason", "")}
                 for item in symbols.get("withdrawn", [])}
    return entries, withdrawn


def _crop(bbox: Any) -> str:
    return " ".join(f"{float(value):g}" for value in bbox) if isinstance(bbox, list) else ""


def _manifest_uses(path: Path, web_root: Path, root: Path, recipes: dict,
                   inventory: Inventory) -> list[tuple[str, IllustrationUse]]:
    data = _json(path)
    top_recipe = data.get("recipe")
    top_sha = str(data.get("source_pdf_sha256") or data.get("source_artwork_sha256")
                  or data.get("source_master_sha256") or "")
    top_name = str(data.get("source_pdf_name") or data.get("source_artwork_name")
                   or data.get("source_master_name") or "")
    uses = []
    for item in data.get("illustrations", []):
        item_path = str(item.get("path") or "")
        if not item_path or ".." in PurePosixPath(item_path).parts:
            inventory.find("illustration-without-path", path.name, f"entry replaces {item.get('replaces')}")
            continue
        uses.append((_rel(web_root / item_path, root), IllustrationUse(
            manifest=path.name, model=str(data.get("model") or ""), region=str(data.get("region") or ""),
            language=str(data.get("language") or ""), sha256=str(item.get("sha256") or ""),
            source_key=_recipe_key(item.get("recipe") or top_recipe, recipes),
            source_sha256=str(item.get("source_master_sha256") or item.get("source_sha256") or top_sha),
            source_name=top_name, source_page=str(item.get("source_page") or ""),
            source_crop=_crop(item.get("bbox_pt")), replaces=tuple(str(x) for x in item.get("replaces", [])),
        )))
    return uses


def _illustration_uses(root: Path, recipes: dict, inventory: Inventory) -> dict[str, list[IllustrationUse]]:
    web_root = Paths(root=root).docs_dir / PathSegments.RENDERERS / PathSegments.WEB
    uses: dict[str, list[IllustrationUse]] = collections.defaultdict(list)
    for manifest in sorted(web_root.glob(ILLUSTRATIONS_GLOB)):
        for repo_path, use in _manifest_uses(manifest, web_root, root, recipes, inventory):
            uses[repo_path].append(use)
    return uses


def _masters(root: Path) -> list[dict[str, str]]:
    path = Paths(root=root).data_dir / ASSET_SOURCES_CSV
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        raise InventoryError(f"cannot read {path}: {exc}") from exc


def key_conventions(records: tuple[AssetRecord, ...], inventory: Inventory) -> dict[str, tuple[str, str]]:
    """Registered Web folder -> (key prefix, separator its file-stem keys use).

    The registry spells per-target keys two ways (web/ja-ad01a/eu/en/inbox-charger,
    web/je1000h/eu/de/charging_ac), consistently within a folder, so a new file
    follows its registered neighbours rather than one global rule.
    """
    prefixes: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    separators: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for record in records:
        if not record.asset_key.startswith("web/") or record.export_root is None:
            continue
        prefix, stem = record.asset_key.rsplit("/", 1)
        folder = record.export_root.as_posix()
        prefixes[folder][prefix] += 1
        separators[folder].update(char for char in "_-" if char in stem)
    conventions = {}
    for folder, counter in sorted(prefixes.items()):
        if len(counter) > 1:
            inventory.find("mixed-key-prefix", folder, "registered keys use " + ", ".join(sorted(counter)))
        separator = separators[folder].most_common(1)[0][0] if separators[folder] else "_"
        conventions[folder] = (counter.most_common(1)[0][0], separator)
    return conventions


def _registry_index(records: tuple[AssetRecord, ...], root: Path) -> tuple[
        dict[str, list[RegistryExport]], dict[str, list[RegistryExport]], dict[str, set[str]]]:
    """Registered exports by path and by digest, and each row's folders (export root and resolved parents)."""
    by_path: dict[str, list[RegistryExport]] = collections.defaultdict(list)
    by_sha: dict[str, list[RegistryExport]] = collections.defaultdict(list)
    folders: dict[str, set[str]] = collections.defaultdict(set)
    for record in records:
        if record.export_root is not None:
            folders[record.asset_key].add(record.export_root.as_posix())
        for path, _fmt, digest in registered_exports(record, repo_root=root):
            item = RegistryExport(record, _rel(path, root), digest.lower())
            by_path[item.repo_path].append(item)
            by_sha[item.digest].append(item)
            folders[record.asset_key].add(PurePosixPath(item.repo_path).parent.as_posix())
    return by_path, by_sha, folders


def _registry_rows(path: Path) -> dict[str, dict[str, str]]:
    """The registry's raw rows by asset_key, in the spelling sync-data compares against."""
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row.get("asset_key") or "").strip(): row for row in csv.DictReader(handle)}


def load_context(root: Path, inventory: Inventory) -> Context:
    recipes = _recipe_sources(root)
    try:
        records = load_registry(root / REGISTRY_RELATIVE_PATH)
        raw_rows = _registry_rows(root / REGISTRY_RELATIVE_PATH)
    except (OSError, AssetRegistryError) as exc:
        raise InventoryError(f"cannot read {REGISTRY_RELATIVE_PATH}: {exc}") from exc
    by_path, by_sha, folders = _registry_index(records, root)
    shared, withdrawn = _shared_manifests(root, recipes)
    masters = _masters(root)
    return Context(
        repo_root=root, roots=art_roots(root), records=records, registry_rows=raw_rows,
        registry_by_path=by_path, registry_by_sha=by_sha, registry_folders=folders,
        shared=shared, withdrawn=withdrawn, uses=_illustration_uses(root, recipes, inventory),
        recipes=recipes, masters=masters,
        master_by_sha={row["sha256"].lower(): row["source_key"] for row in masters if row.get("sha256")},
        conventions=key_conventions(records, inventory),
        regions=frozenset(region.lower() for record in records for region in record.region_scope if region != "ALL"),
        languages=frozenset(language.lower() for record in records for language in record.language_variants),
    )


def derived_web_key(repo_path: str, uses: tuple[IllustrationUse, ...],
                    conventions: dict[str, tuple[str, str]]) -> str:
    """A per-target key in the registry's spelling for this file's folder.

    A folder with registered files lends its prefix and separator. Otherwise the
    registry's majority spelling applies: web/<model without hyphens>/<region>/
    <language>/<file stem>, with "shared" for a file bound by several languages.
    """
    path = PurePosixPath(repo_path)
    prefix, separator = conventions.get(path.parent.as_posix(), ("", "_"))
    if not prefix:
        languages = sorted({use.language.lower() for use in uses if use.language})
        language = languages[0] if len(languages) == 1 else SHARED
        model = _slug(uses[0].model).replace("-", "") if uses else _slug(path.parent.name)
        region = _slug(uses[0].region) if uses else ""
        prefix = "/".join(part for part in ("web", model, region, language if uses else "") if part)
    stem = path.stem.lower().replace(" ", separator).replace("-", separator).replace("_", separator)
    return f"{prefix}/{stem}"


def _folder_key(art: ArtFile, ctx: Context) -> str:
    if art.kind == "web-target":
        return derived_web_key(art.repo_path, (), ctx.conventions)
    art_root = next(item for item in ctx.roots if item.kind == art.kind)
    parts = [_slug(part) for part in PurePosixPath(art.repo_path).relative_to(_rel(art_root.path, ctx.repo_root))
             .with_suffix("").parts]
    if art.kind == "web-shared" and parts and parts[0] == "lcd":
        return "/".join(["lcd", SHARED, *(part.removeprefix("lcd-") for part in parts[1:])])
    return "/".join([KEY_PREFIXES[art.kind], *parts])


def _registry_match(art: ArtFile, ctx: Context, inventory: Inventory) -> tuple[list[RegistryExport], str]:
    """Registry rows naming this file, and the registered file it copies when no row lists it.

    A row names a file by path, exactly as asset-check resolves it. Failing
    that, a file with a registered export's bytes, in a folder that row uses,
    is that export's copy (Word and LaTeX keep byte copies under their own
    names); the copy is reported rather than silently renamed.
    """
    named = ctx.registry_by_path.get(art.repo_path, [])
    for item in named:
        if not art.sha256.startswith(item.digest):
            inventory.find("hash-mismatch", art.repo_path, f"{REGISTRY_ORIGIN} row {item.record.asset_key} declares "
                                                           f"{item.digest[:12]}, file is {art.sha256[:12]}")
    if named:
        return sorted(named, key=lambda item: item.record.asset_key), ""
    folder = PurePosixPath(art.repo_path).parent.as_posix()
    copies = sorted((item for item in ctx.registry_by_sha.get(art.sha256, ())
                     if folder in ctx.registry_folders[item.record.asset_key]),
                    key=lambda item: (item.record.asset_key, item.repo_path))
    if not copies:
        return [], ""
    inventory.find("registry-copy", art.repo_path, f"same bytes as {copies[0].repo_path} "
                                                   f"({copies[0].record.asset_key}); no row lists this file")
    return copies, copies[0].repo_path


def _check_declared_hashes(art: ArtFile, identity: Identity, inventory: Inventory) -> None:
    declared = [(identity.manifest.registered_in, identity.manifest.sha256)] if identity.manifest else []
    declared += [(use.manifest, use.sha256) for use in identity.uses if use.sha256]
    for where, digest in declared:
        if digest.lower() != art.sha256:
            inventory.find("hash-mismatch", art.repo_path, f"{where} declares {digest[:12]}, file is {art.sha256[:12]}")


def resolve_identity(art: ArtFile, ctx: Context, inventory: Inventory) -> Identity:
    """Name a file by the registry that already names it; derive a key only when none does."""
    uses = tuple(sorted(ctx.uses.get(art.repo_path, ()), key=lambda use: use.manifest))
    manifests = tuple(sorted({use.manifest for use in uses}))
    manifest = ctx.shared.get(art.repo_path)
    matches, copy_of = ([], "") if manifest is not None else _registry_match(art, ctx, inventory)
    keys = tuple(dict.fromkeys(item.record.asset_key for item in matches))
    if len(keys) > 1:
        inventory.find("ambiguous-registry", art.repo_path, "several registry rows name this file: " + ", ".join(keys))
    if manifest is not None:
        # The button manifest reuses registry keys (button/power); the registry row then approves.
        record = next((item for item in ctx.records if item.asset_key == manifest.key), None)
        identity = Identity(manifest.key, manifest.registered_in, (manifest.registered_in, *manifests),
                            record=record, manifest=manifest, uses=uses, status=record.status if record else "")
    elif matches:
        identity = Identity(keys[0], REGISTRY_ORIGIN, (REGISTRY_ORIGIN, *manifests), record=matches[0].record,
                            uses=uses, aliases=keys[1:], copy_of=copy_of, status=matches[0].record.status)
    elif uses:
        identity = Identity(derived_web_key(art.repo_path, uses, ctx.conventions), "illustrations", manifests,
                            uses=uses)
    else:
        identity = Identity(_folder_key(art, ctx), "derived", ())
        inventory.find("unregistered-file", art.repo_path,
                       f"no registry or manifest names this file; proposed key {identity.asset_key}")
    _check_declared_hashes(art, identity, inventory)
    return identity


def adopt_live_key(art: ArtFile, identity: Identity, ctx: Context, inventory: Inventory) -> Identity:
    """A key the dry run could only propose yields to the one the Base already uses for this file.

    The Base row for the file names the key; a Base definition with the proposed
    key confirms it. Only a Base definition makes the identity the Base's own, with
    its status deciding the gate; a Base row's key without one stays a proposal.
    A registry row's definition never confirms it: that row approves the files it
    lists, and resolve_identity found this file is not one of them.
    """
    if ctx.live is None or identity.origin not in {"illustrations", "derived"}:
        return identity
    row = ctx.live.git_exports.get(art.repo_path)
    key = (row.text("asset_key") if row is not None else "") or identity.asset_key
    if key != identity.asset_key:
        inventory.find("live-key", art.repo_path,
                       f"the Base uses {key}; the dry run would propose {identity.asset_key}")
    definition = ctx.live.definitions.get(key)
    if definition is None or key in ctx.registry_rows:
        return replace(identity, asset_key=key)
    return replace(identity, asset_key=key, origin=BASE_ORIGIN, registered_in=(BASE_ORIGIN, *identity.registered_in),
                   status=definition.text("status"))


def report_registry_key(art: ArtFile, identity: Identity, ctx: Context, inventory: Inventory) -> None:
    """A proposed key a registry row already uses names another file's asset; the file stays pending."""
    if identity.origin in {"illustrations", "derived"} and identity.asset_key in ctx.registry_rows:
        inventory.find("registry-key-elsewhere", art.repo_path,
                       f"registry row {identity.asset_key} lists other files; its status does not cover this one")


def _gate(identity: Identity) -> str:
    """Only a status someone decided, in the registry or the Base, approves; other files wait."""
    return REGISTRY_GATES.get(identity.status, PENDING) if identity.status else PENDING


def _gate_fields(gate: str) -> dict[str, str]:
    # As the intake does: anything not approved still needs a visual review.
    return {"gate_status": gate, "build_eligible": _flag(gate == "approved"),
            "visual_review_required": _flag(gate != "approved")}


def folder_locale(folder: str, regions: frozenset[str]) -> str:
    """The language a per-target folder name carries: <model>_<region>_<language|shared>[_suffix]."""
    parts = folder.lower().split("_")
    for region, language in zip(parts, parts[1:], strict=False):
        if region in regions and (language == SHARED or re.fullmatch(r"[a-z]{2}", language)):
            return language
    return ""


def _locale(art: ArtFile, identity: Identity, ctx: Context) -> str:
    if art.kind == "web-shared":
        return SHARED
    languages = {use.language.lower() for use in identity.uses if use.language}
    if languages:
        return languages.pop() if len(languages) == 1 else SHARED
    path = PurePosixPath(art.repo_path)
    match = _FILENAME_LANGUAGE.search(path.stem.lower())
    record = identity.record
    if record is None:
        if art.kind != "web-target":
            return ""
        # A proposal only (the export is flagged needs_review): the folder name, else a file-name suffix.
        suffix = match.group(1) if match and match.group(1) in ctx.languages else ""
        return folder_locale(path.parent.name, ctx.regions) or suffix
    if record.language_dimension == NEUTRAL_LANGUAGE_DIMENSION:
        return SHARED
    if len(record.language_variants) == 1:
        return record.language_variants[0]
    return match.group(1) if match and match.group(1) in record.language_variants else ""


def _source_link(identity: Identity, ctx: Context) -> tuple[str, str, str]:
    """(source_key, page, crop) for an export, from its manifest entry or illustration binding."""
    if identity.manifest is not None and identity.manifest.source_key:
        return identity.manifest.source_key, "", ""
    for use in identity.uses:
        key = use.source_key or ctx.master_by_sha.get(use.source_sha256.lower(), "")
        if not key and use.source_sha256:
            key = f"source/unregistered-{use.source_sha256[:12].lower()}"
        if key:
            return key, use.source_page, use.source_crop
    return "", "", ""


def export_row(art: ArtFile, identity: Identity, ctx: Context) -> dict[str, str]:
    gate = _gate(identity)
    withdrawn = ctx.withdrawn.get(art.sha256)
    notes = [identity.manifest.note] if identity.manifest is not None and identity.manifest.note else []
    if withdrawn is not None:
        # Withdrawn from the Web symbol set only; the registry row still decides the gate.
        notes.append(f"网页符号清单已撤回这份位图：{withdrawn['reason']}")
    if identity.copy_of:
        notes.append(f"登记行没有列出这个文件名，字节与 {identity.copy_of} 相同")
    if identity.aliases:
        notes.append("另有登记行指向同一文件：" + "、".join(identity.aliases))
    source_key, page, crop = _source_link(identity, ctx)
    return {
        "export_key": f"{GIT_EXPORT_PREFIX}{art.repo_path}", "asset_key": identity.asset_key, "artifact_kind": art.kind,
        "format": art.fmt, "repo_path": art.repo_path, "size_bytes": str(art.size_bytes),
        "content_sha256": art.sha256, "pixel_size": art.pixel_size, "has_alpha": art.has_alpha,
        # Free-text locale: the web_locale select stays the web-composite gate's (en/fr/es/shared).
        "locale": _locale(art, identity, ctx), **_gate_fields(gate),
        "source_key": source_key, "source_page": page, "source_crop": crop,
        "registered_in": ";".join(identity.registered_in),
        "needs_review": _flag(identity.origin in {"illustrations", "derived"} or gate == PENDING
                              or bool(identity.aliases or identity.copy_of)),
        "notes": "；".join(notes),
    }


def _registry_definition(record: AssetRecord, raw: dict[str, str]) -> dict[str, Any]:
    """A registry row in the registry's own spelling, so sync-data would overlay it unchanged."""
    return {
        "asset_key": record.asset_key, **{field: raw.get(column) or "" for field, column in OWNED_COLUMNS},
        "override_for": raw.get("override_for") or "",
        **_gate_fields(REGISTRY_GATES.get(record.status, PENDING)), "notes": raw.get("备注") or "",
        "key_origin": REGISTRY_ORIGIN, "registered_in": {REGISTRY_ORIGIN}, "needs_review": "FALSE",
        "git_exports": 0, "replaces": set(), "languages": set(),
    }


def _proposed_definition(art: ArtFile, identity: Identity, locale: str) -> dict[str, Any]:
    """A definition no registry holds yet: category, dimension, scope and status are proposals."""
    uses = identity.uses
    first = uses[0] if uses else None
    category = "图标" if identity.manifest is not None or identity.asset_key.startswith("lcd/") else (
        "插图" if uses else "")
    neutral = art.kind != "web-target" or locale == SHARED
    return {
        "asset_key": identity.asset_key, "category": category,
        "language_dimension": NEUTRAL_LANGUAGE_DIMENSION if neutral else LOCALIZED_LANGUAGE_DIMENSION,
        "status": "", "textless_pending": "FALSE",
        "model_scope": first.model if first else "ALL", "region_scope": first.region if first else "ALL",
        "language_variants": "", **_gate_fields(PENDING),
        "notes": "Git 盘点建议的定义；状态待操作者确认",
        "key_origin": identity.origin, "registered_in": set(), "needs_review": "TRUE",
        "git_exports": 0, "replaces": set(), "languages": set(),
    }


def _live_definition(key: str, record: LiveRecord) -> dict[str, Any]:
    """A definition only the Base holds, in the spelling sync-data would write into the registry."""
    owned = definition_rows([{"fields": record.fields}]).get(key, {})
    return {
        "asset_key": key, **{field: owned.get(column, "") for field, column in OWNED_COLUMNS},
        "override_for": record.text("override_for"),
        **_gate_fields(REGISTRY_GATES.get(record.text("status"), PENDING)),
        "source_key": record.text("source_key"), "source_page": record.text("source_page"),
        "source_crop": record.text("source_crop"), "notes": record.text("notes"),
        "key_origin": BASE_ORIGIN, "registered_in": {BASE_ORIGIN}, "needs_review": "FALSE",
        "git_exports": 0, "replaces": set(), "languages": set(),
    }


def _new_definition(art: ArtFile, identity: Identity, export: dict[str, str], ctx: Context) -> dict[str, Any]:
    live = ctx.live.definitions.get(identity.asset_key) if ctx.live is not None else None
    if identity.origin == BASE_ORIGIN and live is not None:
        return _live_definition(identity.asset_key, live)
    return _proposed_definition(art, identity, export["locale"])


def _add_definition(inventory: Inventory, art: ArtFile, identity: Identity, export: dict[str, str],
                    ctx: Context) -> None:
    definition = inventory.definitions.get(identity.asset_key)
    if definition is None:
        definition = inventory.definitions[identity.asset_key] = _new_definition(art, identity, export, ctx)
    definition["git_exports"] += 1
    definition["registered_in"].update(identity.registered_in)
    definition["replaces"].update(name for use in identity.uses for name in use.replaces)
    definition["languages"].update(use.language.lower() for use in identity.uses if use.language)
    if export["locale"] not in ("", SHARED):
        definition["languages"].add(export["locale"])
    if export["source_key"] and not definition.get("source_key"):
        definition.update(source_key=export["source_key"], source_page=export["source_page"],
                          source_crop=export["source_crop"])


def _source_rows(ctx: Context, inventory: Inventory) -> None:
    for row in ctx.masters:
        # data/asset_sources.csv spells the Base's source_sha256 as sha256.
        inventory.sources[row["source_key"]] = {
            **{column: row.get(column, "") for column in SOURCE_COLUMNS if column in row},
            "source_sha256": row.get("sha256", ""), "registered_in": {ASSET_SOURCES_CSV}, "needs_review": "FALSE",
        }
    for stem, (key, digest, pages) in sorted(ctx.recipes.items()):
        if key in inventory.sources:
            inventory.sources[key]["registered_in"].add(f"recipe:{stem}")
        elif digest and digest.lower() in ctx.master_by_sha:
            inventory.find("source-key-alias", key, f"recipe {stem} names master {ctx.master_by_sha[digest.lower()]}")
        else:
            inventory.sources[key] = {"source_key": key, "source_sha256": digest, "page_count": pages,
                                      "registered_in": {f"recipe:{stem}"}, "needs_review": "TRUE",
                                      "notes": "配方引用的母版，data/asset_sources.csv 未登记"}
            inventory.find("unregistered-master", key, f"recipe {stem} names a master asset_sources.csv lacks")


def _illustration_masters(ctx: Context, inventory: Inventory) -> None:
    for use in (use for uses in ctx.uses.values() for use in uses):
        digest = use.source_sha256.lower()
        if use.source_key or not digest or digest in ctx.master_by_sha:
            continue
        key = f"source/unregistered-{digest[:12]}"
        if key not in inventory.sources:
            inventory.sources[key] = {"source_key": key, "source_sha256": digest, "source_name": use.source_name,
                                      "registered_in": set(), "needs_review": "TRUE",
                                      "notes": "插图清单只记了母版哈希，没有配方或登记"}
            inventory.find("unregistered-master", key, f"{use.manifest} names master {use.source_name or digest[:12]}")
        inventory.sources[key]["registered_in"].add(f"illustrations:{use.manifest}")


def _byte_findings(files: list[ArtFile], ctx: Context, inventory: Inventory) -> None:
    by_sha: dict[str, list[str]] = collections.defaultdict(list)
    for art in files:
        by_sha[art.sha256].append(art.repo_path)
        withdrawn = ctx.withdrawn.get(art.sha256)
        if withdrawn is not None and art.repo_path != withdrawn["path"]:
            inventory.find("withdrawn-copy", art.repo_path, f"carries the withdrawn bytes of {withdrawn['path']}")
    for digest, paths in sorted(by_sha.items()):
        if len(paths) > 1:
            inventory.find("duplicate-bytes", digest[:12], f"{len(paths)} copies: " + "; ".join(sorted(paths)))
    for repo_path in sorted(set(ctx.shared) | set(ctx.uses)):
        if not (ctx.repo_root / repo_path).is_file():
            inventory.find("missing-file", repo_path, "a manifest names this file but it is not in the tree")


def _drift(definitions: dict[str, dict[str, Any]]) -> Callable[[str, LiveRecord], list[str]]:
    """The Base-owned columns where a live definition differs from a staged registry definition."""
    def compare(key: str, live: LiveRecord) -> list[str]:
        owned = definition_rows([{"fields": live.fields}]).get(key, {})
        staged = definitions[key]
        return [f"{field}: Base {owned.get(column, '')!r}, registry {staged[field]!r}"
                for field, column in OWNED_COLUMNS if owned.get(column, "") != staged[field]]
    return compare


def _reconcile(inventory: Inventory, ctx: Context) -> None:
    if ctx.live is None:
        return
    registry_keys = {record.asset_key for record in ctx.records}
    reconcile_exports(inventory.exports, ctx.live, inventory.find)
    reconcile_definitions(inventory.definitions, ctx.live, registry_keys, _drift(inventory.definitions),
                          inventory.find)
    reconcile_sources(inventory.sources, ctx.live)
    report_duplicates(ctx.live, inventory.find)


def build_inventory(root: Path, *, tracked_only: bool = True, live: LiveIndex | None = None) -> Inventory:
    """Stage every production-art file, its identity and its master, from the working tree.

    With a live snapshot, keys the Base already uses win over proposals and every
    row gets an action against the live tables.
    """
    inventory = Inventory()
    ctx = load_context(root, inventory)
    ctx.live = live
    files = [_art_file(path, root, ctx.roots) for path in _listed_files(root, ctx.roots, tracked_only=tracked_only)]
    for record in ctx.records:
        raw = ctx.registry_rows.get(record.asset_key, {})
        inventory.definitions[record.asset_key] = _registry_definition(record, raw)
    for art in files:
        identity = adopt_live_key(art, resolve_identity(art, ctx, inventory), ctx, inventory)
        report_registry_key(art, identity, ctx, inventory)
        export = export_row(art, identity, ctx)
        inventory.exports.append(export)
        _add_definition(inventory, art, identity, export, ctx)
    _source_rows(ctx, inventory)
    _illustration_masters(ctx, inventory)
    for source in inventory.sources.values():
        source.setdefault("archive_status", SOURCE_TO_VERIFY)
    _byte_findings(files, ctx, inventory)
    _reconcile(inventory, ctx)
    return inventory


def _flatten(row: dict[str, Any], columns: tuple[str, ...]) -> dict[str, str]:
    flat = {}
    for column in columns:
        value = row.get(column, "")
        flat[column] = ";".join(sorted(value)) if isinstance(value, set) else str(value)
    return flat


def _definition_rows(inventory: Inventory) -> list[dict[str, str]]:
    rows = []
    for key in sorted(inventory.definitions):
        definition = dict(inventory.definitions[key])
        proposed = definition["key_origin"] != REGISTRY_ORIGIN
        if proposed and definition["language_dimension"] != NEUTRAL_LANGUAGE_DIMENSION:
            # The registry separates language variants with commas.
            definition["language_variants"] = ",".join(sorted(definition["languages"] - {SHARED}))
        rows.append(_flatten(definition, DEFINITION_COLUMNS))
    return rows


def _owned_record(row: dict[str, str]) -> dict[str, Any]:
    return {"fields": {"asset_key": row["asset_key"], **{field: row[field] for field, _column in OWNED_COLUMNS}}}


def _merge(existing: str, records: list[dict[str, Any]], source: str) -> tuple[str, Any, str]:
    """sync-data's merge, then its loader check: (merged text, merge stats, "ok" or the loader's error)."""
    text, stats = merge_registry_csv(existing, records)
    try:
        load_registry_bytes(text.encode("utf-8"), source=source)
    except AssetRegistryError as exc:
        return text, stats, str(exc)
    return text, stats, "ok"


def registry_sync_preview(inventory: Inventory, root: Path, live: LiveIndex | None = None) -> dict[str, Any]:
    """What the next sync-data would write to data/asset_registry.csv were the staged definitions live.

    sync-data overlays the Base-owned columns onto the registry's rows, appends a
    row for every Base key the registry lacks, then re-parses the result with the
    registry loader (tools/sync_asset_registry.py). This runs the same steps. With
    a live snapshot it also runs them on the live definitions plus the ones the
    upload would create, which is what the next sync-data after the upload sees.
    """
    existing = (root / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8")
    rows = _definition_rows(inventory)
    registered = [_owned_record(row) for row in rows if row["key_origin"] == REGISTRY_ORIGIN]
    proposed = [_owned_record(row) for row in rows if row["key_origin"] not in {REGISTRY_ORIGIN, BASE_ORIGIN}]
    registered_text, registered_stats, _loader = _merge(existing, registered, "<staged registry definitions>")
    _text, proposed_stats, loader = _merge(existing, registered + proposed, "<staged definitions>")
    preview: dict[str, Any] = {
        "registered_definitions": {"rows": len(registered), "registry_unchanged": registered_text == existing,
                                   "changed_keys": list(registered_stats.updated)},
        "proposed_definitions": {"rows": len(proposed), "would_append": len(proposed_stats.appended),
                                 "without_status": sum(1 for item in proposed if not item["fields"]["status"]),
                                 "registry_loader": loader},
    }
    if live is not None:
        uploads = [_owned_record(row) for row in rows if row.get("action") == "create"]
        records = [{"fields": record.fields} for record in live.definitions.values()] + uploads
        _text, stats, loader = _merge(existing, records, "<Base definitions after the upload>")
        preview["next_sync_after_upload"] = {
            "base_definitions": len(live.definitions), "uploaded_definitions": len(uploads),
            "changed_keys": list(stats.updated), "appended_keys": list(stats.appended), "registry_loader": loader,
        }
    return preview


def _git_commit(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def _actions(rows: Any) -> dict[str, int]:
    return dict(sorted(collections.Counter(row.get("action", "") for row in rows).items()))


def summarize(inventory: Inventory, root: Path, live: LiveIndex | None = None) -> dict[str, Any]:
    exports = inventory.exports
    bytes_by_kind: collections.Counter = collections.Counter()
    for row in exports:
        bytes_by_kind[row["artifact_kind"]] += int(row["size_bytes"])
    definitions = inventory.definitions.values()
    return {
        "schema": SCHEMA, "repo_commit": _git_commit(root),
        "rows": {"asset_sources": len(inventory.sources), "asset_definitions": len(inventory.definitions),
                 "asset_exports": len(exports)},
        "exports_by_kind": dict(sorted(collections.Counter(row["artifact_kind"] for row in exports).items())),
        "exports_by_gate": dict(sorted(collections.Counter(row["gate_status"] for row in exports).items())),
        "bytes_by_kind": dict(sorted(bytes_by_kind.items())),
        "largest_export_bytes": max((int(row["size_bytes"]) for row in exports), default=0),
        "definitions_by_origin": dict(sorted(collections.Counter(row["key_origin"] for row in definitions).items())),
        "definitions_without_git_exports": sum(1 for row in definitions if not row["git_exports"]),
        "needs_review": {
            "asset_sources": sum(1 for row in inventory.sources.values() if row.get("needs_review") == "TRUE"),
            "asset_definitions": sum(1 for row in definitions if row["needs_review"] == "TRUE"),
            "asset_exports": sum(1 for row in exports if row["needs_review"] == "TRUE"),
        },
        "findings": dict(sorted(collections.Counter(item["kind"] for item in inventory.findings).items())),
        "registry_sync_preview": registry_sync_preview(inventory, root, live),
        "live_actions": None if live is None else {
            "asset_sources": _actions(inventory.sources.values()),
            "asset_definitions": _actions(inventory.definitions.values()),
            "asset_exports": _actions(exports),
        },
    }


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    # A BOM keeps Excel and the Feishu importer reading the Chinese columns as UTF-8.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_inventory(inventory: Inventory, summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "asset_sources.csv", SOURCE_COLUMNS,
               [_flatten(inventory.sources[key], SOURCE_COLUMNS) for key in sorted(inventory.sources)])
    _write_csv(output_dir / "asset_definitions.csv", DEFINITION_COLUMNS, _definition_rows(inventory))
    _write_csv(output_dir / "asset_exports.csv", EXPORT_COLUMNS,
               sorted(inventory.exports, key=lambda row: row["repo_path"]))
    _write_csv(output_dir / "findings.csv", FINDING_COLUMNS,
               sorted(inventory.findings, key=lambda row: (row["kind"], row["subject"], row["detail"])))
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_output_dir(output_dir: Path, root: Path) -> None:
    """Refuse repository data folders and non-empty directories."""
    resolved = output_dir.resolve()
    for name in FORBIDDEN_OUTPUT_ROOTS:
        if resolved.is_relative_to((root / name).resolve()):
            raise InventoryError(f"refusing to write staging files inside {name}/: {resolved}")
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise InventoryError(f"output directory must be new or empty: {resolved}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.asset_pipeline.base_inventory",
        description="Stage the Feishu 04_资产* rows for the Git-tracked production art (dry run, no Feishu calls).",
    )
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="new or empty directory outside docs/, data/ and tools/")
    parser.add_argument("--repo-root", type=Path, default=None, help="repository root (default: this checkout)")
    parser.add_argument("--live-snapshot", type=Path, default=None,
                        help="directory of lark-cli record-list JSON for the three live tables, saved read-only")
    args = parser.parse_args(argv)
    root = (args.repo_root or repo_root()).resolve()
    try:
        check_output_dir(args.output_dir, root)
        live = load_snapshot(args.live_snapshot) if args.live_snapshot is not None else None
        inventory = build_inventory(root, live=live)
    except (InventoryError, SnapshotError) as exc:
        print(f"[asset-inventory] ERROR: {exc}", file=sys.stderr)
        return 2
    summary = summarize(inventory, root, live)
    write_inventory(inventory, summary, args.output_dir)
    rows = summary["rows"]
    print(f"[asset-inventory] staged {rows['asset_sources']} sources, {rows['asset_definitions']} definitions, "
          f"{rows['asset_exports']} exports into {args.output_dir}")
    print(f"[asset-inventory] needs review: {summary['needs_review']}; findings: {summary['findings']}")
    if summary["live_actions"] is not None:
        print(f"[asset-inventory] against the live tables: {summary['live_actions']}")
    return 0


__all__ = [
    "InventoryError", "art_roots", "build_inventory", "check_output_dir", "derived_web_key", "export_row",
    "folder_locale", "main", "registry_sync_preview", "resolve_identity", "summarize", "write_inventory",
]


if __name__ == "__main__":
    raise SystemExit(main())
