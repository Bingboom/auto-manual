"""Typed contracts shared by the design-master intake pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AssetIntakeError(RuntimeError):
    """Base error for a fail-closed asset-intake run."""


class RecipeValidationError(AssetIntakeError):
    """Raised when a recipe is ambiguous or unsafe."""


class SourceValidationError(AssetIntakeError):
    """Raised when source bytes do not match the recipe contract."""


class ArtifactValidationError(AssetIntakeError):
    """Raised when a generated artifact fails its declared gate."""


Bbox = tuple[float, float, float, float]


@dataclass(frozen=True)
class GateSpec:
    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CoordinateContract:
    page_numbering: str
    bbox_units: str
    bbox_origin: str
    bbox_space: str


@dataclass(frozen=True)
class PdfSaveSpec:
    garbage: int
    clean: bool
    deflate: bool
    no_new_id: bool


@dataclass(frozen=True)
class NormalizationSpec:
    engine: str
    validated_version: str
    validated_mupdf_version: str
    pdf_save: PdfSaveSpec
    forbidden_pdf_markers: tuple[str, ...]
    max_render_pixels: int


@dataclass(frozen=True)
class SourceSpec:
    source_key: str
    expected_sha256: str
    expected_page_count: int


@dataclass(frozen=True)
class PageRange:
    first: int
    last: int

    @property
    def values(self) -> tuple[int, ...]:
        return tuple(range(self.first, self.last + 1))


@dataclass(frozen=True)
class ArchivePdfSpec:
    path_pattern: str


@dataclass(frozen=True)
class ArchivePreviewSpec:
    path_pattern: str
    default_scale: float
    page_scale: tuple[tuple[int, float], ...]

    def scale_for(self, page: int) -> float:
        return dict(self.page_scale).get(page, self.default_scale)


@dataclass(frozen=True)
class ArchiveSpec:
    pages: PageRange
    pdf: ArchivePdfSpec
    previews: ArchivePreviewSpec | None


@dataclass(frozen=True)
class PageCatalogEntry:
    page: int
    page_key: str
    role: str
    locale: str
    build_eligible: bool
    gate: GateSpec
    risk_tags: tuple[str, ...]


@dataclass(frozen=True)
class TransformSpec:
    op: str
    bbox_pt: Bbox | None = None
    images: str | None = None
    graphics: str | None = None
    fill: None = None

    def as_manifest(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"op": self.op}
        if self.bbox_pt is not None:
            payload["bbox_pt"] = list(self.bbox_pt)
        if self.images is not None:
            payload["images"] = self.images
        if self.graphics is not None:
            payload["graphics"] = self.graphics
        if self.op == "redact_text":
            payload["fill"] = self.fill
        return payload


@dataclass(frozen=True)
class OutputSpec:
    format: str
    path: str
    scale: float | None
    expected_sha256: str | None

    def as_manifest(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"format": self.format, "path": self.path}
        if self.scale is not None:
            payload["scale"] = self.scale
        if self.expected_sha256 is not None:
            payload["expected_sha256"] = self.expected_sha256
        return payload


@dataclass(frozen=True)
class ScopeSpec:
    models: tuple[str, ...]
    regions: tuple[str, ...]
    locales: tuple[str, ...]


@dataclass(frozen=True)
class AssetSpec:
    asset_key: str
    page: int
    build_eligible: bool
    scope: ScopeSpec
    text_policy: str
    visual_review_required: bool
    transforms: tuple[TransformSpec, ...]
    outputs: tuple[OutputSpec, ...]
    gate: GateSpec
    risk_tags: tuple[str, ...]

    @property
    def crop_bbox(self) -> Bbox:
        bbox = self.transforms[0].bbox_pt
        if bbox is None:  # Kept defensive; recipe validation guarantees it.
            raise RecipeValidationError(f"asset {self.asset_key!r} has no crop bbox")
        return bbox


@dataclass(frozen=True)
class IntakeRecipe:
    schema_version: int
    coordinate_contract: CoordinateContract
    normalization: NormalizationSpec
    source: SourceSpec
    archive: ArchiveSpec
    page_catalog: tuple[PageCatalogEntry, ...]
    assets: tuple[AssetSpec, ...]
    canonical_bytes: bytes


@dataclass(frozen=True)
class SourceInspection:
    sha256: str
    page_count: int
    page_rects: tuple[Bbox, ...]
    ai_private_data_count: int
    ai_metadata_count: int
    piece_info_count: int


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    format: str
    kind: str
    sha256: str
    byte_size: int
    source_page: int
    repo_path: str | None = None
    asset_key: str | None = None
    expected_sha256: str | None = None
    gate_status: str = "archive"
    build_eligible: bool = False
    visual_review_required: bool = False
    text_policy: str | None = None

    def as_manifest(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "byte_size": self.byte_size,
            "build_eligible": self.build_eligible,
            "format": self.format,
            "gate_status": self.gate_status,
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "source_page": self.source_page,
            "visual_review_required": self.visual_review_required,
        }
        if self.asset_key is not None:
            payload["asset_key"] = self.asset_key
        if self.repo_path is not None:
            payload["repo_path"] = self.repo_path
        if self.text_policy is not None:
            payload["text_policy"] = self.text_policy
        if self.expected_sha256 is not None:
            payload["expected_sha256"] = self.expected_sha256
        return payload


@dataclass(frozen=True)
class IntakeResult:
    output_root: Path
    manifest_path: Path
    artifacts_csv_path: Path
    package_path: Path
    artifacts: tuple[ArtifactRecord, ...]
