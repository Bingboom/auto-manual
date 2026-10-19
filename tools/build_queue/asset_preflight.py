"""Advisory asset preflight for queue dispatch.

The publish gate is authoritative because it reads the frozen
``asset_usage_manifest.json`` from the prepared bundle.  Queue dispatch runs
before that bundle exists, so this module deliberately reports an advisory
projection instead of pretending to have release lineage.  It scans the
target's current review/template sources and resolves semantic ``asset:``
references with the same target-bound resolver used by bundle finalization.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from tools.asset_registry import AssetRegistryError
from tools.asset_usage import AssetTarget, BundleAssetUsage
from tools.language_aliases import normalize_language, normalize_region

ASSET_URI_RE = re.compile(r"asset:([A-Za-z0-9][A-Za-z0-9_./-]*)")
SOURCE_SUFFIXES = frozenset({".html", ".md", ".rst"})
LANGUAGE_SUFFIX_RE = re.compile(r"_(?P<lang>[a-z]{2,3}(?:-[a-z]{2,3})?)(?=\.[^.]+$)", re.IGNORECASE)


@dataclass(frozen=True)
class AssetPreflightWarning:
    code: str
    asset_key: str | None
    message: str


@dataclass(frozen=True)
class AssetPreflightReport:
    model: str
    region: str
    language: str | None
    source_files: int
    references: tuple[str, ...]
    resolved: tuple[str, ...]
    warnings: tuple[AssetPreflightWarning, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": "advisory",
            "model": self.model,
            "region": self.region,
            "language": self.language,
            "source_files": self.source_files,
            "references": list(self.references),
            "resolved": list(self.resolved),
            "warnings": [asdict(item) for item in self.warnings],
        }


def _candidate_source_roots(
    repo_root: Path,
    *,
    model: str,
    region: str,
    language: str | None,
    build_family: str,
) -> tuple[Path, ...]:
    roots: list[Path] = []
    review_root = repo_root / "docs" / "_review" / model / region
    if review_root.is_dir():
        roots.append(review_root)

    family = str(build_family or "").strip()
    if not family and language:
        family = f"{region.lower()}-{language.lower()}"
    template_root = repo_root / "docs" / "templates" / f"page_{family}" if family else None
    if template_root is not None and template_root.is_dir():
        roots.append(template_root)
    elif language:
        # Queue rows may carry a logical family such as ``us-merged`` while
        # the page templates remain split into one language directory each.
        fallback_root = repo_root / "docs" / "templates" / f"page_{region.lower()}-{language.lower()}"
        if fallback_root.is_dir():
            roots.append(fallback_root)

    if language:
        shared_root = repo_root / "docs" / "templates" / "page_shared" / language
        if shared_root.is_dir():
            roots.append(shared_root)
    return tuple(dict.fromkeys(roots))


def _source_matches_language(path: Path, *, language: str | None) -> bool:
    """Skip an explicitly different generated-language file in review trees."""

    if language is None:
        return True
    match = LANGUAGE_SUFFIX_RE.search(path.name)
    if match is None:
        return True
    return normalize_language(match.group("lang")) == language


def _collect_references(
    roots: tuple[Path, ...],
    *,
    language: str | None,
) -> tuple[int, dict[str, tuple[Path, ...]]]:
    source_files = 0
    references: dict[str, list[Path]] = {}
    seen_paths: set[Path] = set()
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            if path in seen_paths or not _source_matches_language(path, language=language):
                continue
            seen_paths.add(path)
            source_files += 1
            text = path.read_text(encoding="utf-8", errors="ignore")
            for asset_key in sorted(set(ASSET_URI_RE.findall(text))):
                references.setdefault(asset_key, []).append(path)
    return source_files, {key: tuple(paths) for key, paths in references.items()}


def preflight_asset_lineage(
    *,
    repo_root: Path,
    model: str,
    region: str,
    language: str | None = None,
    build_family: str = "",
) -> AssetPreflightReport:
    """Resolve current target references without changing dispatch semantics."""

    normalized_model = str(model or "").strip()
    normalized_region = normalize_region(region)
    normalized_language = normalize_language(language) if str(language or "").strip() else None
    roots = _candidate_source_roots(
        repo_root,
        model=normalized_model,
        region=normalized_region,
        language=normalized_language,
        build_family=build_family,
    )
    source_files, references = _collect_references(roots, language=normalized_language)
    warnings: list[AssetPreflightWarning] = []
    resolved: list[str] = []

    if not roots:
        warnings.append(
            AssetPreflightWarning(
                "source_snapshot_unavailable",
                None,
                "no review/template source tree was available; formal bundle lineage remains authoritative",
            )
        )

    usage = None
    if normalized_model and normalized_region:
        try:
            usage = BundleAssetUsage(
                target=AssetTarget(
                    model=normalized_model,
                    region=normalized_region,
                    language=normalized_language,
                ),
                repo_root=repo_root,
            )
        except (AssetRegistryError, OSError) as exc:
            warnings.append(AssetPreflightWarning("registry_unavailable", None, str(exc)))

    for asset_key, source_paths in sorted(references.items()):
        if usage is None:
            warnings.append(
                AssetPreflightWarning(
                    "asset_not_checked",
                    asset_key,
                    "target-bound asset resolver was unavailable",
                )
            )
            continue
        try:
            usage.resolve_reference(
                f"asset:{asset_key}",
                model=normalized_model,
                region=normalized_region,
                language=normalized_language,
            )
        except (AssetRegistryError, OSError) as exc:
            source = ", ".join(path.as_posix() for path in source_paths[:2])
            if len(source_paths) > 2:
                source += ", ..."
            warnings.append(
                AssetPreflightWarning(
                    "unresolvable_asset",
                    asset_key,
                    f"{exc} (referenced by {source})",
                )
            )
        else:
            resolved.append(asset_key)

    return AssetPreflightReport(
        model=normalized_model,
        region=normalized_region,
        language=normalized_language,
        source_files=source_files,
        references=tuple(sorted(references)),
        resolved=tuple(sorted(resolved)),
        warnings=tuple(warnings),
    )


__all__ = (
    "AssetPreflightReport",
    "AssetPreflightWarning",
    "preflight_asset_lineage",
)
