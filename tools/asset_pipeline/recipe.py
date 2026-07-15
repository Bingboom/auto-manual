"""Strict JSON loader for deterministic design-master extraction recipes."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path, PurePosixPath
from typing import Any

from tools.asset_pipeline.models import (
    ArchivePdfSpec,
    ArchivePreviewSpec,
    ArchiveSpec,
    AssetSpec,
    Bbox,
    CoordinateContract,
    GateSpec,
    IntakeRecipe,
    NormalizationSpec,
    OutputSpec,
    PageCatalogEntry,
    PageRange,
    PdfSaveSpec,
    RecipeValidationError,
    ScopeSpec,
    SourceSpec,
    TransformSpec,
)

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SOURCE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
LOCALE_RE = re.compile(r"^(?:[a-z]{2,3}(?:-[A-Z]{2})?|mul|und)$")
ALLOWED_OUTPUT_FORMATS = frozenset({"pdf", "png"})
ALLOWED_GRAPHICS_MODES = frozenset({"preserve", "remove_if_touched"})
SENSITIVE_TOKENS = frozenset(
    {
        "app",
        "app-ui",
        "barcode",
        "localized-text",
        "localized-ui",
        "qr",
        "screenshot",
        "url",
    }
)
PAGE_PATTERN_TOKEN = "{page:04d}"
COORDINATE_CONTRACT = {
    "page_numbering": "pdf-1-based",
    "bbox_units": "pt",
    "bbox_origin": "top-left",
    "bbox_space": "source-page",
}
PDF_SAVE_CONTRACT = {
    "garbage": 4,
    "clean": True,
    "deflate": True,
    "no_new_id": True,
}
FORBIDDEN_PDF_MARKERS = ("AIPrivateData", "PieceInfo", "AIMetaData")
TEXT_POLICIES = frozenset(
    {"textless", "numeric-only", "fixed-product-markings", "localized-full-page"}
)


def _fail(location: str, message: str) -> RecipeValidationError:
    return RecipeValidationError(f"{location}: {message}")


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RecipeValidationError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _mapping(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _fail(location, "must be an object")
    return value


def _list(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise _fail(location, "must be an array")
    return value


def _keys(
    value: dict[str, Any],
    *,
    location: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    missing = sorted(required - value.keys())
    unknown = sorted(value.keys() - required - optional)
    if missing:
        raise _fail(location, f"missing field(s): {', '.join(missing)}")
    if unknown:
        raise _fail(location, f"unknown field(s): {', '.join(unknown)}")


def _string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _fail(location, "must be a non-empty string")
    return value.strip()


def _integer(value: Any, location: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise _fail(location, f"must be an integer >= {minimum}")
    return value


def _number(value: Any, location: str, *, maximum: float = 16.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _fail(location, "must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result <= 0 or result > maximum:
        raise _fail(location, f"must be > 0 and <= {maximum:g}")
    return result


def _sha256(value: Any, location: str) -> str:
    digest = _string(value, location)
    if not SHA256_RE.fullmatch(digest):
        raise _fail(location, "must be a complete 64-character SHA-256 digest")
    if digest != digest.lower():
        raise _fail(location, "must use lowercase hexadecimal")
    return digest


def _safe_path(value: Any, location: str, *, suffix: str | None = None) -> str:
    raw = _string(value, location)
    if "\\" in raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise _fail(location, "must be a POSIX path relative to the package root")
    if not SAFE_PATH_RE.fullmatch(raw):
        raise _fail(location, "contains characters outside the v1 path contract")
    path = PurePosixPath(raw)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise _fail(location, "contains an unsafe path segment")
    if suffix and path.suffix.lower() != f".{suffix}":
        raise _fail(location, f"must end in .{suffix}")
    return path.as_posix()


def _path_pattern(value: Any, location: str, *, suffix: str) -> str:
    raw = _string(value, location)
    if raw.count(PAGE_PATTERN_TOKEN) != 1 or "{" in raw.replace(PAGE_PATTERN_TOKEN, ""):
        raise _fail(location, f"must contain exactly one literal {PAGE_PATTERN_TOKEN!r}")
    _safe_path(raw.replace(PAGE_PATTERN_TOKEN, "0001"), location, suffix=suffix)
    if not raw.startswith("archive/"):
        raise _fail(location, "archive output patterns must start with 'archive/'")
    return raw


def _bbox(value: Any, location: str) -> Bbox:
    items = _list(value, location)
    if len(items) != 4:
        raise _fail(location, "must contain exactly [x0, y0, x1, y1]")
    coords: list[float] = []
    for index, item in enumerate(items):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise _fail(f"{location}[{index}]", "must be a finite number")
        coordinate = float(item)
        if not math.isfinite(coordinate):
            raise _fail(f"{location}[{index}]", "must be a finite number")
        if coordinate < 0 or coordinate > 100_000:
            raise _fail(f"{location}[{index}]", "must be between 0 and 100000 pt")
        coords.append(coordinate)
    x0, y0, x1, y1 = coords
    if x1 <= x0 or y1 <= y0:
        raise _fail(location, "must satisfy x1 > x0 and y1 > y0")
    return x0, y0, x1, y1


def _string_tuple(value: Any, location: str) -> tuple[str, ...]:
    result = tuple(_string(item, f"{location}[{index}]") for index, item in enumerate(_list(value, location)))
    if len(set(result)) != len(result):
        raise _fail(location, "must not contain duplicates")
    return result


def _gate(value: Any, location: str, *, allowed: set[str]) -> GateSpec:
    data = _mapping(value, location)
    _keys(data, location=location, required={"status", "reasons"})
    status = _string(data["status"], f"{location}.status")
    if status not in allowed:
        raise _fail(f"{location}.status", f"must be one of: {', '.join(sorted(allowed))}")
    reasons = _string_tuple(data["reasons"], f"{location}.reasons")
    if status == "quarantine" and not reasons:
        raise _fail(location, "quarantine requires at least one reason")
    return GateSpec(status=status, reasons=reasons)


def _is_sensitive(*values: str, risk_tags: tuple[str, ...]) -> bool:
    normalized = {tag.lower() for tag in risk_tags}
    for value in values:
        lowered = value.lower()
        normalized.add(lowered)
        normalized.update(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    return bool(normalized & SENSITIVE_TOKENS)


def _source(value: Any) -> SourceSpec:
    data = _mapping(value, "source")
    _keys(
        data,
        location="source",
        required={"source_key", "expected_sha256", "expected_page_count"},
    )
    source_key = _string(data["source_key"], "source.source_key")
    if not SOURCE_KEY_RE.fullmatch(source_key) or ".." in PurePosixPath(source_key).parts:
        raise _fail("source.source_key", "must be a stable relative key")
    return SourceSpec(
        source_key=source_key,
        expected_sha256=_sha256(data["expected_sha256"], "source.expected_sha256"),
        expected_page_count=_integer(data["expected_page_count"], "source.expected_page_count"),
    )


def _coordinate_contract(value: Any) -> CoordinateContract:
    data = _mapping(value, "coordinate_contract")
    _keys(data, location="coordinate_contract", required=set(COORDINATE_CONTRACT))
    for field, expected in COORDINATE_CONTRACT.items():
        if data[field] != expected:
            raise _fail(f"coordinate_contract.{field}", f"must be {expected!r}")
    return CoordinateContract(**COORDINATE_CONTRACT)


def _normalization(value: Any) -> NormalizationSpec:
    data = _mapping(value, "normalization")
    _keys(
        data,
        location="normalization",
        required={
            "engine",
            "validated_version",
            "validated_mupdf_version",
            "pdf_save",
            "forbidden_pdf_markers",
            "max_render_pixels",
        },
    )
    if data["engine"] != "pymupdf":
        raise _fail("normalization.engine", "must be 'pymupdf'")
    if data["validated_version"] != "1.28.0":
        raise _fail("normalization.validated_version", "must be '1.28.0'")
    if data["validated_mupdf_version"] != "1.29.0":
        raise _fail("normalization.validated_mupdf_version", "must be '1.29.0'")
    save_data = _mapping(data["pdf_save"], "normalization.pdf_save")
    _keys(save_data, location="normalization.pdf_save", required=set(PDF_SAVE_CONTRACT))
    for field, expected in PDF_SAVE_CONTRACT.items():
        if save_data[field] != expected or type(save_data[field]) is not type(expected):
            raise _fail(f"normalization.pdf_save.{field}", f"must be {expected!r}")
    markers = _string_tuple(data["forbidden_pdf_markers"], "normalization.forbidden_pdf_markers")
    if markers != FORBIDDEN_PDF_MARKERS:
        raise _fail(
            "normalization.forbidden_pdf_markers",
            f"must be exactly {list(FORBIDDEN_PDF_MARKERS)!r}",
        )
    max_render_pixels = _integer(
        data["max_render_pixels"], "normalization.max_render_pixels"
    )
    if max_render_pixels > 100_000_000:
        raise _fail("normalization.max_render_pixels", "must be <= 100000000")
    return NormalizationSpec(
        engine="pymupdf",
        validated_version="1.28.0",
        validated_mupdf_version="1.29.0",
        pdf_save=PdfSaveSpec(**PDF_SAVE_CONTRACT),
        forbidden_pdf_markers=markers,
        max_render_pixels=max_render_pixels,
    )


def _archive(value: Any, *, source: SourceSpec) -> ArchiveSpec:
    data = _mapping(value, "archive")
    _keys(data, location="archive", required={"pages", "pdf", "previews"})
    pages_data = _mapping(data["pages"], "archive.pages")
    _keys(pages_data, location="archive.pages", required={"first", "last"})
    pages = PageRange(
        first=_integer(pages_data["first"], "archive.pages.first"),
        last=_integer(pages_data["last"], "archive.pages.last"),
    )
    if pages.first != 1 or pages.last != source.expected_page_count:
        raise _fail(
            "archive.pages",
            "must cover every source page exactly once from 1 through expected_page_count",
        )
    pdf_data = _mapping(data["pdf"], "archive.pdf")
    _keys(pdf_data, location="archive.pdf", required={"path_pattern"})
    pdf = ArchivePdfSpec(
        path_pattern=_path_pattern(pdf_data["path_pattern"], "archive.pdf.path_pattern", suffix="pdf")
    )
    preview_data = _mapping(data["previews"], "archive.previews")
    _keys(
        preview_data,
        location="archive.previews",
        required={"path_pattern", "default_scale", "page_scale"},
    )
    raw_page_scale = _mapping(preview_data["page_scale"], "archive.previews.page_scale")
    page_scales: list[tuple[int, float]] = []
    for raw_page, raw_scale in raw_page_scale.items():
        if not isinstance(raw_page, str) or not raw_page.isdigit():
            raise _fail("archive.previews.page_scale", "page keys must be decimal strings")
        page = _integer(int(raw_page), f"archive.previews.page_scale.{raw_page}")
        if page not in pages.values:
            raise _fail(f"archive.previews.page_scale.{raw_page}", "page is outside archive range")
        page_scales.append(
            (page, _number(raw_scale, f"archive.previews.page_scale.{raw_page}", maximum=4))
        )
    previews = ArchivePreviewSpec(
        path_pattern=_path_pattern(
            preview_data["path_pattern"], "archive.previews.path_pattern", suffix="png"
        ),
        default_scale=_number(
            preview_data["default_scale"], "archive.previews.default_scale", maximum=4
        ),
        page_scale=tuple(sorted(page_scales)),
    )
    return ArchiveSpec(pages=pages, pdf=pdf, previews=previews)


def _catalog(value: Any, *, archive: ArchiveSpec) -> tuple[PageCatalogEntry, ...]:
    rows: list[PageCatalogEntry] = []
    for index, raw in enumerate(_list(value, "page_catalog")):
        location = f"page_catalog[{index}]"
        data = _mapping(raw, location)
        _keys(
            data,
            location=location,
            required={"page", "page_key", "role", "locale", "build_eligible", "gate", "risk_tags"},
        )
        page = _integer(data["page"], f"{location}.page")
        page_key = _string(data["page_key"], f"{location}.page_key")
        role = _string(data["role"], f"{location}.role")
        locale = _string(data["locale"], f"{location}.locale")
        if not LOCALE_RE.fullmatch(locale):
            raise _fail(f"{location}.locale", "does not match the v1 locale contract")
        build_eligible = data["build_eligible"]
        if build_eligible is not False:
            raise _fail(f"{location}.build_eligible", "archive pages must be explicitly false")
        risk_tags = _string_tuple(data["risk_tags"], f"{location}.risk_tags")
        gate = _gate(data["gate"], f"{location}.gate", allowed={"archive", "quarantine"})
        if _is_sensitive(page_key, role, risk_tags=risk_tags) and gate.status != "quarantine":
            raise _fail(f"{location}.gate", "App/QR/URL/localized UI content must be quarantined")
        rows.append(
            PageCatalogEntry(page, page_key, role, locale, build_eligible, gate, risk_tags)
        )
    expected_pages = archive.pages.values
    actual_pages = tuple(sorted(row.page for row in rows))
    if actual_pages != expected_pages:
        raise _fail("page_catalog", "must cover each archive page exactly once")
    page_keys = [row.page_key for row in rows]
    if len(set(page_keys)) != len(page_keys):
        raise _fail("page_catalog", "page_key values must be unique")
    overview_pages = {row.page for row in rows if row.role == "engineering_overview"}
    if overview_pages and archive.previews is not None:
        explicit_scales = dict(archive.previews.page_scale)
        for page in overview_pages:
            if page not in explicit_scales or explicit_scales[page] >= 1:
                raise _fail(
                    "archive.previews.page_scale",
                    "engineering_overview pages require an explicit scale below 1",
                )
    return tuple(sorted(rows, key=lambda row: row.page))


def _transform(value: Any, location: str) -> TransformSpec:
    data = _mapping(value, location)
    op = _string(data.get("op"), f"{location}.op")
    if op in {"crop", "whiteout"}:
        _keys(data, location=location, required={"op", "bbox_pt"})
        return TransformSpec(op=op, bbox_pt=_bbox(data["bbox_pt"], f"{location}.bbox_pt"))
    if op == "redact_text":
        _keys(data, location=location, required={"op", "images", "graphics", "fill"})
        if data["images"] != "preserve":
            raise _fail(f"{location}.images", "must be 'preserve'")
        if data["graphics"] not in ALLOWED_GRAPHICS_MODES:
            raise _fail(
                f"{location}.graphics",
                f"must be one of: {', '.join(sorted(ALLOWED_GRAPHICS_MODES))}",
            )
        if data["fill"] is not None:
            raise _fail(f"{location}.fill", "must be null")
        return TransformSpec(
            op=op,
            images="preserve",
            graphics=data["graphics"],
            fill=None,
        )
    raise _fail(f"{location}.op", "must be crop, redact_text, or whiteout")


def _output(value: Any, location: str) -> OutputSpec:
    data = _mapping(value, location)
    _keys(
        data,
        location=location,
        required={"format", "path"},
        optional={"scale", "expected_sha256"},
    )
    format_name = _string(data["format"], f"{location}.format").lower()
    if format_name not in ALLOWED_OUTPUT_FORMATS:
        raise _fail(
            f"{location}.format",
            f"must be one of: {', '.join(sorted(ALLOWED_OUTPUT_FORMATS))}",
        )
    scale = None
    if format_name == "png":
        if "scale" not in data:
            raise _fail(f"{location}.scale", "is required for PNG Matrix rendering")
        scale = _number(data["scale"], f"{location}.scale")
    elif "scale" in data:
        raise _fail(f"{location}.scale", "is only valid for PNG outputs")
    expected_sha256 = None
    if "expected_sha256" in data:
        expected_sha256 = _sha256(data["expected_sha256"], f"{location}.expected_sha256")
    return OutputSpec(
        format=format_name,
        path=_safe_path(data["path"], f"{location}.path", suffix=format_name),
        scale=scale,
        expected_sha256=expected_sha256,
    )


def _scope(value: Any, location: str) -> ScopeSpec:
    data = _mapping(value, location)
    _keys(data, location=location, required={"models", "regions", "locales"})
    models = _string_tuple(data["models"], f"{location}.models")
    regions = _string_tuple(data["regions"], f"{location}.regions")
    locales = _string_tuple(data["locales"], f"{location}.locales")
    if not models or not regions or not locales:
        raise _fail(location, "models, regions, and locales must each be non-empty")
    invalid_locales = [locale for locale in locales if not LOCALE_RE.fullmatch(locale)]
    if invalid_locales:
        raise _fail(f"{location}.locales", f"invalid locale(s): {', '.join(invalid_locales)}")
    return ScopeSpec(models=models, regions=regions, locales=locales)


def _assets(value: Any, *, source: SourceSpec) -> tuple[AssetSpec, ...]:
    assets: list[AssetSpec] = []
    output_paths: set[str] = set()
    for index, raw in enumerate(_list(value, "assets")):
        location = f"assets[{index}]"
        data = _mapping(raw, location)
        _keys(
            data,
            location=location,
            required={
                "asset_key",
                "page",
                "build_eligible",
                "scope",
                "text_policy",
                "visual_review_required",
                "transforms",
                "outputs",
                "gate",
                "risk_tags",
            },
        )
        asset_key = _string(data["asset_key"], f"{location}.asset_key")
        if not SOURCE_KEY_RE.fullmatch(asset_key) or ".." in PurePosixPath(asset_key).parts:
            raise _fail(f"{location}.asset_key", "must be a stable relative key")
        page = _integer(data["page"], f"{location}.page")
        if page > source.expected_page_count:
            raise _fail(f"{location}.page", "exceeds source.expected_page_count")
        transforms = tuple(
            _transform(item, f"{location}.transforms[{item_index}]")
            for item_index, item in enumerate(_list(data["transforms"], f"{location}.transforms"))
        )
        if not transforms or transforms[0].op != "crop":
            raise _fail(f"{location}.transforms", "crop must be the first transform")
        if sum(transform.op == "crop" for transform in transforms) != 1:
            raise _fail(f"{location}.transforms", "must contain exactly one crop")
        outputs = tuple(
            _output(item, f"{location}.outputs[{item_index}]")
            for item_index, item in enumerate(_list(data["outputs"], f"{location}.outputs"))
        )
        if not outputs:
            raise _fail(f"{location}.outputs", "must contain at least one output")
        if sum(output.format == "pdf" for output in outputs) > 1:
            raise _fail(f"{location}.outputs", "must contain at most one PDF output")
        for output in outputs:
            if output.path in output_paths:
                raise _fail(f"{location}.outputs", f"duplicate output path: {output.path}")
            output_paths.add(output.path)
        risk_tags = _string_tuple(data["risk_tags"], f"{location}.risk_tags")
        gate = _gate(data["gate"], f"{location}.gate", allowed={"approved", "quarantine"})
        build_eligible = data["build_eligible"]
        visual_review_required = data["visual_review_required"]
        if not isinstance(build_eligible, bool):
            raise _fail(f"{location}.build_eligible", "must be a boolean")
        if not isinstance(visual_review_required, bool):
            raise _fail(f"{location}.visual_review_required", "must be a boolean")
        text_policy = _string(data["text_policy"], f"{location}.text_policy")
        if text_policy not in TEXT_POLICIES:
            raise _fail(
                f"{location}.text_policy",
                f"must be one of: {', '.join(sorted(TEXT_POLICIES))}",
            )
        scope = _scope(data["scope"], f"{location}.scope")
        if _is_sensitive(asset_key, risk_tags=risk_tags) and gate.status != "quarantine":
            raise _fail(f"{location}.gate", "App/QR/URL/localized UI assets must be quarantined")
        if gate.status == "approved":
            if not build_eligible or visual_review_required:
                raise _fail(
                    location,
                    "approved assets require build_eligible=true and visual_review_required=false",
                )
            if any(output.expected_sha256 is None for output in outputs):
                raise _fail(location, "approved assets require expected_sha256 on every output")
        elif build_eligible or not visual_review_required:
            raise _fail(
                location,
                "quarantine assets require build_eligible=false and visual_review_required=true",
            )
        assets.append(
            AssetSpec(
                asset_key=asset_key,
                page=page,
                build_eligible=build_eligible,
                scope=scope,
                text_policy=text_policy,
                visual_review_required=visual_review_required,
                transforms=transforms,
                outputs=outputs,
                gate=gate,
                risk_tags=risk_tags,
            )
        )
    asset_keys = [asset.asset_key for asset in assets]
    if len(set(asset_keys)) != len(asset_keys):
        raise _fail("assets", "asset_key values must be unique")
    return tuple(assets)


def load_recipe(path: Path) -> IntakeRecipe:
    """Load and fully validate one versioned JSON extraction recipe."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_no_duplicates)
    except OSError as exc:
        raise RecipeValidationError(f"cannot read recipe {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RecipeValidationError(f"invalid JSON recipe {path}: {exc}") from exc
    data = _mapping(payload, "recipe")
    _keys(
        data,
        location="recipe",
        required={
            "schema_version",
            "coordinate_contract",
            "normalization",
            "source",
            "archive",
            "page_catalog",
            "assets",
        },
    )
    if data["schema_version"] != 1:
        raise _fail("schema_version", "only version 1 is supported")
    coordinate_contract = _coordinate_contract(data["coordinate_contract"])
    normalization = _normalization(data["normalization"])
    source = _source(data["source"])
    archive = _archive(data["archive"], source=source)
    page_catalog = _catalog(data["page_catalog"], archive=archive)
    assets = _assets(data["assets"], source=source)
    canonical_bytes = (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return IntakeRecipe(
        schema_version=1,
        coordinate_contract=coordinate_contract,
        normalization=normalization,
        source=source,
        archive=archive,
        page_catalog=page_catalog,
        assets=assets,
        canonical_bytes=canonical_bytes,
    )
