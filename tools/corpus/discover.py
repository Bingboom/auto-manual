"""Discover and pair multilingual manual.ir.json (manual-ir/v2) bundles."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from tools import lang_registry
from tools.manual_copy_source import TM_LANGUAGE_FIELDS

SUPPORTED_IR_SCHEMA_VERSION = "manual-ir/v2"


@dataclass(frozen=True)
class DiscoveredIR:
    """Metadata and pages loaded from a committed manual.ir.json bundle."""

    path: Path
    rel_path: str
    model: str
    region: str
    language: str
    package_dir: Path
    publication_eligible: bool | None
    content_sha256: str
    file_sha256: str
    pages: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class IRPair:
    """An aligned (anchor, target) manual.ir.json pair for the same model and region."""

    model: str
    region: str
    anchor: DiscoveredIR
    target: DiscoveredIR
    pairing_mode: str


@dataclass(frozen=True)
class PackageAbstention:
    """Record explaining why a target manual.ir.json could not be paired."""

    model: str
    region: str
    target_path: str
    target_language: str
    reason: str
    candidate_anchors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "region": self.region,
            "target_path": self.target_path,
            "target_language": self.target_language,
            "reason": self.reason,
            "candidate_anchors": list(self.candidate_anchors),
        }


def default_anchor_lang() -> str:
    """Return the canonical English anchor language code without literal tables."""

    return TM_LANGUAGE_FIELDS.get("en", "en")


def normalize_lang_key(lang: str) -> str:
    """Canonicalize a language code via lang_registry when registered."""

    raw = (lang or "").strip().replace("_", "-")
    canonical = lang_registry.canonical_language(raw)
    if canonical:
        return canonical.casefold()
    return raw.casefold()


def default_scan_roots(repo_root: Path) -> tuple[Path, ...]:
    """Return default committed manual_sources roots present under repo_root."""

    candidates = (repo_root / "manual_sources", repo_root / "data" / "manual_sources")
    return tuple(path for path in candidates if path.is_dir())


def _package_dir_for_ir(ir_path: Path) -> Path:
    if ir_path.parent.parent.name == "web":
        return ir_path.parent.parent.parent
    return ir_path.parent


def _display_rel(path: Path, *, repo_root: Path) -> str:
    resolved = path.resolve()
    root_resolved = repo_root.resolve()
    if resolved.is_relative_to(root_resolved):
        return resolved.relative_to(root_resolved).as_posix()
    return resolved.as_posix()


def load_discovered_ir(path: Path, *, repo_root: Path) -> tuple[DiscoveredIR | None, dict[str, str] | None]:
    """Load a single manual.ir.json file, returning (DiscoveredIR, skipped_info)."""

    rel = _display_rel(path, repo_root=repo_root)
    try:
        raw_bytes = path.read_bytes()
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, {"path": rel, "reason": f"read_or_json_error: {exc}"}
    if not isinstance(payload, dict):
        return None, {"path": rel, "reason": "invalid_root_type"}
    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version != SUPPORTED_IR_SCHEMA_VERSION:
        return None, {"path": rel, "reason": f"unsupported_schema: {schema_version}"}

    model = str(payload.get("model") or "").strip()
    region = str(payload.get("region") or "").strip()
    language = str(payload.get("language") or "").strip()
    pages_raw = payload.get("pages")
    if not model or not region or not language or not isinstance(pages_raw, list):
        return None, {"path": rel, "reason": "missing_model_region_language_or_pages"}

    metadata = payload.get("metadata")
    pub_raw = metadata.get("publication_eligible") if isinstance(metadata, dict) else None
    pub = pub_raw if isinstance(pub_raw, bool) else None
    pages = tuple(item for item in pages_raw if isinstance(item, dict))
    return (
        DiscoveredIR(
            path=path.resolve(),
            rel_path=rel,
            model=model,
            region=region,
            language=language,
            package_dir=_package_dir_for_ir(path.resolve()),
            publication_eligible=pub,
            content_sha256=str(payload.get("content_sha256") or ""),
            file_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            pages=pages,
        ),
        None,
    )


def _matches_filter(ir: DiscoveredIR, *, model: str | None, region: str | None) -> bool:
    if model and ir.model.casefold() != model.strip().casefold():
        return False
    if region and ir.region.casefold() != region.strip().casefold():
        return False
    return True


def _select_unique_anchor(
    anchors: list[DiscoveredIR],
) -> tuple[DiscoveredIR | None, str, tuple[str, ...]]:
    if not anchors:
        return None, "no_anchor_in_model_region", ()
    approved = [item for item in anchors if item.publication_eligible is True]
    pool = approved if approved else anchors
    by_digest: dict[str, DiscoveredIR] = {}
    for item in sorted(pool, key=lambda candidate: candidate.rel_path):
        digest = item.content_sha256 or item.file_sha256
        by_digest.setdefault(digest, item)
    if len(by_digest) == 1:
        return next(iter(by_digest.values())), "split_package_unique_anchor", ()
    candidates = tuple(sorted(item.rel_path for item in pool))
    return None, "ambiguous_anchor_candidates", candidates


def _pair_orphans_in_group(
    *,
    model: str,
    region: str,
    orphans: list[DiscoveredIR],
    anchors: list[DiscoveredIR],
    explicit_anchors: list[DiscoveredIR],
) -> tuple[list[IRPair], list[PackageAbstention]]:
    if not orphans:
        return [], []
    if explicit_anchors:
        if len(explicit_anchors) == 1:
            chosen = explicit_anchors[0]
            return (
                [
                    IRPair(
                        model=model,
                        region=region,
                        anchor=chosen,
                        target=target,
                        pairing_mode="explicit_anchor_ir",
                    )
                    for target in orphans
                ],
                [],
            )
        candidates = tuple(sorted(item.rel_path for item in explicit_anchors))
        return (
            [],
            [
                PackageAbstention(
                    model=model,
                    region=region,
                    target_path=target.rel_path,
                    target_language=target.language,
                    reason="ambiguous_explicit_anchors",
                    candidate_anchors=candidates,
                )
                for target in orphans
            ],
        )

    selected, reason, candidates = _select_unique_anchor(anchors)
    if selected is not None:
        return (
            [
                IRPair(
                    model=model,
                    region=region,
                    anchor=selected,
                    target=target,
                    pairing_mode=reason,
                )
                for target in orphans
            ],
            [],
        )
    return (
        [],
        [
            PackageAbstention(
                model=model,
                region=region,
                target_path=target.rel_path,
                target_language=target.language,
                reason=reason,
                candidate_anchors=candidates,
            )
            for target in orphans
        ],
    )


def _load_explicit_anchors(
    anchor_ir_paths: Sequence[Path],
    *,
    repo_root: Path,
    model: str | None,
    region: str | None,
) -> tuple[dict[tuple[str, str], list[DiscoveredIR]], list[dict[str, str]]]:
    explicit_by_mr: dict[tuple[str, str], list[DiscoveredIR]] = defaultdict(list)
    skipped: list[dict[str, str]] = []
    for path in anchor_ir_paths:
        ir, err = load_discovered_ir(path, repo_root=repo_root)
        if err is not None:
            skipped.append(err)
            continue
        if ir is not None and _matches_filter(ir, model=model, region=region):
            explicit_by_mr[(ir.model, ir.region)].append(ir)
    return explicit_by_mr, skipped


def _collect_ir_files(
    *,
    repo_root: Path,
    scan_roots: Sequence[Path],
    model: str | None,
    region: str | None,
) -> tuple[list[DiscoveredIR], list[dict[str, str]]]:
    ir_paths: list[Path] = []
    for scan_root in scan_roots:
        if scan_root.is_file() and scan_root.name == "manual.ir.json":
            ir_paths.append(scan_root)
        elif scan_root.is_dir():
            ir_paths.extend(sorted(scan_root.rglob("manual.ir.json")))

    discovered: list[DiscoveredIR] = []
    skipped: list[dict[str, str]] = []
    seen_paths: set[Path] = set()
    for path in sorted(ir_paths):
        resolved = path.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        ir, err = load_discovered_ir(resolved, repo_root=repo_root)
        if err is not None:
            skipped.append(err)
            continue
        if ir is not None and _matches_filter(ir, model=model, region=region):
            discovered.append(ir)
    return discovered, skipped


def _pair_model_region_group(
    *,
    ir_model: str,
    ir_region: str,
    group: list[DiscoveredIR],
    anchor_key: str,
    explicit_anchors: list[DiscoveredIR],
) -> tuple[list[IRPair], list[PackageAbstention]]:
    by_pkg: dict[Path, list[DiscoveredIR]] = defaultdict(list)
    all_anchors: list[DiscoveredIR] = []
    for ir in group:
        by_pkg[ir.package_dir].append(ir)
        if normalize_lang_key(ir.language) == anchor_key:
            all_anchors.append(ir)

    pairs: list[IRPair] = []
    orphans: list[DiscoveredIR] = []
    for _pkg_dir, pkg_items in sorted(by_pkg.items(), key=lambda kv: str(kv[0])):
        pkg_anchors = [i for i in pkg_items if normalize_lang_key(i.language) == anchor_key]
        pkg_targets = [i for i in pkg_items if normalize_lang_key(i.language) != anchor_key]
        if len(pkg_anchors) == 1:
            for target in pkg_targets:
                pairs.append(
                    IRPair(
                        model=ir_model,
                        region=ir_region,
                        anchor=pkg_anchors[0],
                        target=target,
                        pairing_mode="same_package",
                    )
                )
        else:
            orphans.extend(pkg_targets)

    orphan_pairs, orphan_abstentions = _pair_orphans_in_group(
        model=ir_model,
        region=ir_region,
        orphans=orphans,
        anchors=all_anchors,
        explicit_anchors=explicit_anchors,
    )
    pairs.extend(orphan_pairs)
    return pairs, orphan_abstentions


def discover_ir_pairs(
    *,
    repo_root: Path,
    roots: Sequence[Path] = (),
    model: str | None = None,
    region: str | None = None,
    anchor_lang: str | None = None,
    explicit_anchor_irs: Sequence[Path] = (),
) -> tuple[list[DiscoveredIR], list[IRPair], list[PackageAbstention], list[dict[str, str]]]:
    """Discover manual.ir.json files and pair target locales with anchor English IRs."""

    anchor_key = normalize_lang_key(anchor_lang or default_anchor_lang())
    scan_roots = tuple(roots) if roots else default_scan_roots(repo_root)
    discovered, skipped = _collect_ir_files(
        repo_root=repo_root, scan_roots=scan_roots, model=model, region=region
    )
    explicit_by_mr, explicit_skipped = _load_explicit_anchors(
        explicit_anchor_irs, repo_root=repo_root, model=model, region=region
    )
    skipped.extend(explicit_skipped)

    by_mr: dict[tuple[str, str], list[DiscoveredIR]] = defaultdict(list)
    for ir in discovered:
        by_mr[(ir.model, ir.region)].append(ir)

    pairs: list[IRPair] = []
    abstentions: list[PackageAbstention] = []
    for (ir_model, ir_region), group in sorted(by_mr.items()):
        group_pairs, group_abstentions = _pair_model_region_group(
            ir_model=ir_model,
            ir_region=ir_region,
            group=group,
            anchor_key=anchor_key,
            explicit_anchors=explicit_by_mr.get((ir_model, ir_region), []),
        )
        pairs.extend(group_pairs)
        abstentions.extend(group_abstentions)

    return discovered, pairs, abstentions, skipped
