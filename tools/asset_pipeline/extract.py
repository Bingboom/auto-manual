"""PyMuPDF-backed extraction primitives for design-master intake."""

from __future__ import annotations

import hashlib
import importlib
import math
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

from tools.asset_pipeline.leaders import (
    find_leader_geometries,
    suppress_leader_strokes,
)
from tools.asset_pipeline.models import (
    ArtifactRecord,
    ArtifactValidationError,
    AssetSpec,
    Bbox,
    IntakeRecipe,
    SourceInspection,
    SourceValidationError,
)

PDF_PRIVATE_MARKERS = (b"AIPrivateData", b"PieceInfo", b"AIMetaData")
SAVE_OPTIONS = {
    "garbage": 4,
    "clean": True,
    "deflate": True,
    "no_new_id": True,
}


def _fitz() -> Any:
    for module_name in ("pymupdf", "fitz"):
        try:
            return importlib.import_module(module_name)
        except ImportError:
            continue
    raise AssetValidationDependencyError(
        "PyMuPDF is required for asset intake; install the repository dependencies"
    )


class AssetValidationDependencyError(ArtifactValidationError):
    """Raised when the declared PDF runtime is unavailable."""


def pymupdf_versions() -> tuple[str, str]:
    """Return binding and MuPDF versions used for render-sensitive bytes."""

    fitz = _fitz()
    version = getattr(fitz, "version", None)
    if isinstance(version, tuple) and len(version) >= 2:
        return str(version[0]), str(version[1])
    binding_version = getattr(fitz, "VersionBind", None)
    mupdf_version = getattr(fitz, "VersionFitz", None)
    if binding_version and mupdf_version:
        return str(binding_version), str(mupdf_version)
    raise AssetValidationDependencyError("cannot determine active PyMuPDF / MuPDF versions")


def pymupdf_version() -> str:
    return pymupdf_versions()[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_markers(handle: BinaryIO) -> dict[bytes, int]:
    counts = {marker: 0 for marker in PDF_PRIVATE_MARKERS}
    overlap = max(len(marker) for marker in PDF_PRIVATE_MARKERS) - 1
    tail = b""
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        data = tail + chunk
        for marker in PDF_PRIVATE_MARKERS:
            offset = 0
            while True:
                found = data.find(marker, offset)
                if found < 0:
                    break
                if found + len(marker) > len(tail):
                    counts[marker] += 1
                offset = found + 1
        tail = data[-overlap:]
    return counts


def _count_markers_in_bytes(data: bytes) -> dict[bytes, int]:
    counts = {marker: 0 for marker in PDF_PRIVATE_MARKERS}
    for marker in PDF_PRIVATE_MARKERS:
        offset = 0
        while True:
            found = data.find(marker, offset)
            if found < 0:
                break
            counts[marker] += 1
            offset = found + 1
    return counts


def _logical_pdf_marker_counts(path: Path) -> dict[bytes, int]:
    """Inspect decoded objects/streams so compression cannot hide markers."""

    counts = {marker: 0 for marker in PDF_PRIVATE_MARKERS}
    fitz = _fitz()
    try:
        document = fitz.open(str(path))
    except Exception as exc:
        raise ArtifactValidationError(
            f"cannot inspect PDF private markers in {path}: {exc}"
        ) from exc
    try:
        for xref in range(1, document.xref_length()):
            try:
                object_bytes = document.xref_object(xref, compressed=False).encode(
                    "latin-1", errors="ignore"
                )
                stream_bytes = document.xref_stream(xref) or b""
            except Exception as exc:
                # xref_length() is the highest object number plus one, so a
                # conforming PDF may contain free / never-assigned numbers in
                # that range. PyMuPDF reports those gaps with this exact
                # missing-object error; there are no logical bytes to scan.
                if "cannot find object in xref" in str(exc):
                    continue
                raise ArtifactValidationError(
                    f"cannot inspect PDF object {xref} in {path}: {exc}"
                ) from exc
            for payload in (object_bytes, stream_bytes):
                payload_counts = _count_markers_in_bytes(payload)
                for marker, count in payload_counts.items():
                    counts[marker] += count
    finally:
        document.close()
    return counts


def scan_pdf_private_markers(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as handle:
        physical_counts = _count_markers(handle)
    logical_counts = _logical_pdf_marker_counts(path)
    counts = {
        marker: max(physical_counts[marker], logical_counts[marker])
        for marker in PDF_PRIVATE_MARKERS
    }
    return counts[b"AIPrivateData"], counts[b"AIMetaData"], counts[b"PieceInfo"]


def validate_source(path: Path, recipe: IntakeRecipe) -> SourceInspection:
    """Verify source bytes and PDF structure before creating any output."""

    if not path.is_file():
        raise SourceValidationError(f"source file does not exist: {path}")
    actual_version, actual_mupdf_version = pymupdf_versions()
    if actual_version != recipe.normalization.validated_version:
        raise SourceValidationError(
            "PyMuPDF version mismatch: "
            f"recipe requires {recipe.normalization.validated_version}, got {actual_version}"
        )
    if actual_mupdf_version != recipe.normalization.validated_mupdf_version:
        raise SourceValidationError(
            "MuPDF version mismatch: "
            f"recipe requires {recipe.normalization.validated_mupdf_version}, "
            f"got {actual_mupdf_version}"
        )
    marker_contract = tuple(marker.decode("ascii") for marker in PDF_PRIVATE_MARKERS)
    if marker_contract != recipe.normalization.forbidden_pdf_markers:
        raise SourceValidationError("runtime forbidden PDF markers differ from the recipe contract")
    save_contract = recipe.normalization.pdf_save
    if SAVE_OPTIONS != {
        "garbage": save_contract.garbage,
        "clean": save_contract.clean,
        "deflate": save_contract.deflate,
        "no_new_id": save_contract.no_new_id,
    }:
        raise SourceValidationError("runtime PDF save options differ from the recipe contract")
    actual_sha256 = sha256_file(path)
    if actual_sha256 != recipe.source.expected_sha256:
        raise SourceValidationError(
            "source SHA-256 mismatch: "
            f"expected {recipe.source.expected_sha256}, got {actual_sha256}"
        )
    ai_private_data_count, ai_metadata_count, piece_info_count = scan_pdf_private_markers(path)
    fitz = _fitz()
    try:
        document = fitz.open(str(path))
    except Exception as exc:
        raise SourceValidationError(f"source is not a readable PDF-compatible file: {exc}") from exc
    try:
        if not document.is_pdf or document.needs_pass:
            raise SourceValidationError("source must be an unencrypted PDF-compatible file")
        if document.page_count != recipe.source.expected_page_count:
            raise SourceValidationError(
                "source page-count mismatch: "
                f"expected {recipe.source.expected_page_count}, got {document.page_count}"
            )
        page_rects: list[Bbox] = []
        for index in range(document.page_count):
            page = document.load_page(index)
            if page.rotation != 0:
                raise SourceValidationError(
                    f"source page {index + 1} is rotated; recipe coordinates require rotation 0"
                )
            rect = page.rect
            page_rects.append((float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)))
    finally:
        document.close()
    if path.suffix.lower() == ".ai" and (ai_private_data_count == 0 or piece_info_count == 0):
        raise SourceValidationError(
            "PDF-compatible .ai source is missing AIPrivateData or PieceInfo markers"
        )
    inspection = SourceInspection(
        sha256=actual_sha256,
        page_count=recipe.source.expected_page_count,
        page_rects=tuple(page_rects),
        ai_private_data_count=ai_private_data_count,
        ai_metadata_count=ai_metadata_count,
        piece_info_count=piece_info_count,
    )
    _validate_geometry(recipe, inspection)
    return inspection


def _inside(inner: Bbox, outer: Bbox, *, tolerance: float = 0.01) -> bool:
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] >= outer[1] - tolerance
        and inner[2] <= outer[2] + tolerance
        and inner[3] <= outer[3] + tolerance
    )


def _validate_geometry(recipe: IntakeRecipe, inspection: SourceInspection) -> None:
    for asset in recipe.assets:
        page_rect = inspection.page_rects[asset.page - 1]
        crop = asset.crop_bbox
        if not _inside(crop, page_rect):
            raise SourceValidationError(
                f"asset {asset.asset_key!r} crop is outside source page {asset.page}"
            )
        for transform in asset.transforms[1:]:
            if transform.bbox_pt is not None and not _inside(transform.bbox_pt, crop):
                raise SourceValidationError(
                    f"asset {asset.asset_key!r} {transform.op} bbox is outside its crop"
                )


def _ensure_destination(artifact_root: Path, relative_path: str) -> Path:
    path = artifact_root.joinpath(*PurePosixPath(relative_path).parts)
    if path.exists():
        raise ArtifactValidationError(f"duplicate artifact destination: {relative_path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _save_pdf(document: Any, path: Path) -> None:
    document.save(str(path), **SAVE_OPTIONS)


def _text_span_rects(fitz: Any, page: Any, clip: Any) -> tuple[Any, ...]:
    rects: list[Any] = []
    for block in page.get_text("dict", clip=clip).get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                rects.append(fitz.Rect(span["bbox"]))
    return tuple(rects)


def _prepare_asset_source(
    fitz: Any,
    source_path: Path,
    asset: AssetSpec,
) -> tuple[Any, Any]:
    source = fitz.open(str(source_path))
    page = source.load_page(asset.page - 1)
    crop = fitz.Rect(asset.crop_bbox)
    for transform in asset.transforms[1:]:
        if transform.op in {"redact_text", "redact_text_region"}:
            if transform.op == "redact_text_region":
                if transform.bbox_pt is None:
                    raise ArtifactValidationError(
                        f"asset {asset.asset_key!r} has invalid redact_text_region"
                    )
                redaction_rects = (fitz.Rect(transform.bbox_pt),)
            else:
                redaction_rects = _text_span_rects(fitz, page, crop)
            for rect in redaction_rects:
                page.add_redact_annot(rect, fill=None, cross_out=False)
            graphics = (
                fitz.PDF_REDACT_LINE_ART_NONE
                if transform.graphics == "preserve"
                else fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED
            )
            page.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=graphics,
                text=fitz.PDF_REDACT_TEXT_REMOVE,
            )
        elif transform.op == "drop_leader_strokes":
            # The leaders sit above the artwork and carry a white halo, so a
            # whiteout can only punch a hole. Suppressing their own strokes
            # lets the grille and panel divider underneath render intact.
            leader_kwargs = {}
            if transform.halo_width_pt is not None:
                leader_kwargs["halo_width"] = transform.halo_width_pt
            if transform.line_width_pt is not None:
                leader_kwargs["line_width"] = transform.line_width_pt
            if transform.width_tolerance_pt is not None:
                leader_kwargs["width_tolerance"] = transform.width_tolerance_pt
            leaders = find_leader_geometries(
                fitz, page, tuple(asset.crop_bbox), **leader_kwargs
            )
            suppressed = suppress_leader_strokes(fitz, source, page, leaders)
            if suppressed != len(leaders) * 2:
                raise ArtifactValidationError(
                    f"asset {asset.asset_key!r} expected {len(leaders) * 2} leader "
                    f"strokes, suppressed {suppressed}"
                )
        elif transform.op == "whiteout":
            if transform.bbox_pt is None:
                raise ArtifactValidationError(f"asset {asset.asset_key!r} has invalid whiteout")
            page.draw_rect(
                fitz.Rect(transform.bbox_pt),
                color=None,
                fill=(1, 1, 1),
                overlay=True,
            )
        elif transform.op == "retain_vector_drawings":
            # Applied at output time: the retained groups are replayed into a
            # fresh crop-sized page so every non-selected vector object stays
            # out of the artifact instead of being hidden or painted over.
            continue
        else:
            raise ArtifactValidationError(
                f"asset {asset.asset_key!r} has unsupported transform {transform.op!r}"
            )
    return source, crop


def _translated_point(point: Any, *, dx: float, dy: float) -> Any:
    return type(point)(point.x + dx, point.y + dy)


def _translated_rect(rect: Any, *, dx: float, dy: float) -> Any:
    return type(rect)(rect.x0 + dx, rect.y0 + dy, rect.x1 + dx, rect.y1 + dy)


def _drawing_overlaps_clip(rect: Any, clip: Any) -> bool:
    """Return overlap for ordinary and zero-area vector drawing bounds."""

    return not (
        rect.x1 < clip.x0
        or rect.x0 > clip.x1
        or rect.y1 < clip.y0
        or rect.y0 > clip.y1
    )


def _replay_drawing(
    page: Any,
    drawing: dict[str, Any],
    *,
    dx: float,
    dy: float,
    fill_override: tuple[float, float, float] | None = None,
    suppress_stroke: bool = False,
) -> None:
    shape = page.new_shape()
    for item in drawing["items"]:
        if item[0] == "l":
            shape.draw_line(
                _translated_point(item[1], dx=dx, dy=dy),
                _translated_point(item[2], dx=dx, dy=dy),
            )
        elif item[0] == "c":
            shape.draw_bezier(
                *(
                    _translated_point(point, dx=dx, dy=dy)
                    for point in item[1:5]
                )
            )
        elif item[0] == "re":
            shape.draw_rect(_translated_rect(item[1], dx=dx, dy=dy))
        else:
            raise ArtifactValidationError(
                f"retain_vector_drawings does not support drawing item {item[0]!r}"
            )
    line_cap = drawing.get("lineCap", 0)
    if isinstance(line_cap, (list, tuple)):
        line_cap = line_cap[0] if line_cap else 0
    dashes = drawing.get("dashes")
    if not isinstance(dashes, str) or not dashes.strip():
        dashes = None
    shape.finish(
        width=float(drawing.get("width") or 0),
        color=None if suppress_stroke else drawing.get("color"),
        fill=fill_override if fill_override is not None else drawing.get("fill"),
        lineCap=int(line_cap or 0),
        lineJoin=int(drawing.get("lineJoin") or 0),
        dashes=dashes,
        even_odd=bool(drawing.get("even_odd", False)),
        closePath=bool(drawing.get("closePath", False)),
        fill_opacity=float(drawing.get("fill_opacity", 1) or 1),
        stroke_opacity=float(drawing.get("stroke_opacity", 1) or 1),
    )
    shape.commit(overlay=True)


def _retained_vector_transform(asset: AssetSpec):
    transforms = [
        transform
        for transform in asset.transforms
        if transform.op == "retain_vector_drawings"
    ]
    if len(transforms) > 1:
        raise ArtifactValidationError(
            f"asset {asset.asset_key!r} has more than one retain_vector_drawings transform"
        )
    return transforms[0] if transforms else None


def _save_retained_vector_pdf(
    fitz: Any,
    source: Any,
    asset: AssetSpec,
    clip: Any,
    destination: Path,
) -> None:
    transform = _retained_vector_transform(asset)
    if transform is None:
        raise ArtifactValidationError(
            f"asset {asset.asset_key!r} has no retain_vector_drawings transform"
        )
    page = source.load_page(asset.page - 1)
    drawings = page.get_drawings()
    if transform.drawing_indices[-1] >= len(drawings):
        raise ArtifactValidationError(
            f"asset {asset.asset_key!r} drawing index "
            f"{transform.drawing_indices[-1]} exceeds source drawing count {len(drawings)}"
        )
    overrides = dict(transform.fill_rgb_overrides)
    stroke_suppressed = set(transform.stroke_suppressed_indices)
    output = fitz.open()
    try:
        target = output.new_page(width=clip.width, height=clip.height)
        for index in transform.drawing_indices:
            drawing = drawings[index]
            if not _drawing_overlaps_clip(fitz.Rect(drawing["rect"]), clip):
                raise ArtifactValidationError(
                    f"asset {asset.asset_key!r} retained drawing {index} "
                    "does not intersect the declared crop"
                )
            _replay_drawing(
                target,
                drawing,
                dx=-clip.x0,
                dy=-clip.y0,
                fill_override=overrides.get(index),
                suppress_stroke=index in stroke_suppressed,
            )
        _save_pdf(output, destination)
    finally:
        output.close()


def _save_asset_pdf(
    fitz: Any,
    source: Any,
    asset: AssetSpec,
    clip: Any,
    destination: Path,
) -> None:
    output = fitz.open()
    try:
        target = output.new_page(width=clip.width, height=clip.height)
        target.show_pdf_page(
            target.rect,
            source,
            pno=asset.page - 1,
            clip=clip,
            keep_proportion=False,
        )
        _save_pdf(output, destination)
    finally:
        output.close()


def _artifact_record(
    path: Path,
    *,
    artifact_root: Path,
    format_name: str,
    kind: str,
    source_page: int,
    repo_path: str | None = None,
    asset_key: str | None = None,
    expected_sha256: str | None = None,
    gate_status: str,
    build_eligible: bool = False,
    visual_review_required: bool = False,
    text_policy: str | None = None,
) -> ArtifactRecord:
    digest = sha256_file(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ArtifactValidationError(
            f"artifact SHA-256 mismatch for {repo_path or path.name}: "
            f"expected {expected_sha256}, got {digest}"
        )
    if format_name == "pdf":
        ai_private_data_count, ai_metadata_count, piece_info_count = scan_pdf_private_markers(path)
        if ai_private_data_count or ai_metadata_count or piece_info_count:
            raise ArtifactValidationError(
                f"generated PDF leaked Illustrator private data: {repo_path or path.name}"
            )
    relative_path = path.relative_to(artifact_root.parent).as_posix()
    return ArtifactRecord(
        path=relative_path,
        format=format_name,
        kind=kind,
        sha256=digest,
        byte_size=path.stat().st_size,
        source_page=source_page,
        repo_path=repo_path,
        asset_key=asset_key,
        expected_sha256=expected_sha256,
        gate_status=gate_status,
        build_eligible=build_eligible,
        visual_review_required=visual_review_required,
        text_policy=text_policy,
    )


def _render_png(
    fitz: Any,
    pdf_path: Path,
    destination: Path,
    *,
    scale: float,
    max_render_pixels: int,
) -> None:
    with fitz.open(str(pdf_path)) as document:
        page = document[0]
        width = math.ceil(page.rect.width * scale)
        height = math.ceil(page.rect.height * scale)
        pixels = width * height
        if pixels > max_render_pixels:
            raise ArtifactValidationError(
                f"PNG render exceeds max_render_pixels: {width}x{height}={pixels} "
                f"> {max_render_pixels}"
            )
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            alpha=False,
            annots=False,
        )
        pixmap.save(str(destination))


def _render_source_page_png(
    fitz: Any,
    page: Any,
    destination: Path,
    *,
    clip: Any,
    scale: float,
    max_render_pixels: int,
) -> None:
    width = math.ceil(clip.x1 * scale) - math.floor(clip.x0 * scale)
    height = math.ceil(clip.y1 * scale) - math.floor(clip.y0 * scale)
    pixels = width * height
    if pixels > max_render_pixels:
        raise ArtifactValidationError(
            f"PNG render exceeds max_render_pixels: {width}x{height}={pixels} "
            f"> {max_render_pixels}"
        )
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(scale, scale),
        clip=clip,
        alpha=False,
    )
    pixmap.save(str(destination))


def _archive_artifacts(
    fitz: Any,
    source: Any,
    recipe: IntakeRecipe,
    artifact_root: Path,
) -> list[ArtifactRecord]:
    records: list[ArtifactRecord] = []
    catalog = {entry.page: entry for entry in recipe.page_catalog}
    for page_number in recipe.archive.pages.values:
        source_page = source.load_page(page_number - 1)
        relative_pdf = recipe.archive.pdf.path_pattern.format(page=page_number)
        pdf_path = _ensure_destination(artifact_root, relative_pdf)
        archive_document = fitz.open()
        try:
            target = archive_document.new_page(
                width=source_page.rect.width,
                height=source_page.rect.height,
            )
            target.show_pdf_page(
                target.rect,
                source,
                pno=page_number - 1,
                keep_proportion=False,
                overlay=True,
                clip=source_page.rect,
            )
            _save_pdf(archive_document, pdf_path)
        finally:
            archive_document.close()
        gate_status = catalog[page_number].gate.status
        records.append(
            _artifact_record(
                pdf_path,
                artifact_root=artifact_root,
                format_name="pdf",
                kind="archive_page",
                source_page=page_number,
                gate_status=gate_status,
                visual_review_required=gate_status == "quarantine",
            )
        )
        previews = recipe.archive.previews
        if previews is not None:
            relative_preview = previews.path_pattern.format(page=page_number)
            preview_path = _ensure_destination(artifact_root, relative_preview)
            _render_png(
                fitz,
                pdf_path,
                preview_path,
                scale=previews.scale_for(page_number),
                max_render_pixels=recipe.normalization.max_render_pixels,
            )
            records.append(
                _artifact_record(
                    preview_path,
                    artifact_root=artifact_root,
                    format_name="png",
                    kind="archive_preview",
                    source_page=page_number,
                    gate_status=gate_status,
                    visual_review_required=gate_status == "quarantine",
                )
            )
    return records


def _asset_artifacts(
    fitz: Any,
    source_path: Path,
    recipe: IntakeRecipe,
    artifact_root: Path,
) -> list[ArtifactRecord]:
    records: list[ArtifactRecord] = []
    for asset in recipe.assets:
        source, clip = _prepare_asset_source(fitz, source_path, asset)
        try:
            page = source.load_page(asset.page - 1)
            with tempfile.TemporaryDirectory(prefix="asset-vector-") as temp_dir:
                retained_pdf = None
                if _retained_vector_transform(asset) is not None:
                    retained_pdf = Path(temp_dir) / "retained.pdf"
                    _save_retained_vector_pdf(
                        fitz, source, asset, clip, retained_pdf
                    )
                for output in asset.outputs:
                    destination = _ensure_destination(artifact_root, output.path)
                    if output.format == "pdf":
                        if retained_pdf is not None:
                            shutil.copyfile(retained_pdf, destination)
                        else:
                            _save_asset_pdf(fitz, source, asset, clip, destination)
                    elif output.format == "png":
                        if output.scale is None:
                            raise ArtifactValidationError(
                                f"asset {asset.asset_key!r} PNG has no Matrix scale"
                            )
                        if retained_pdf is not None:
                            _render_png(
                                fitz,
                                retained_pdf,
                                destination,
                                scale=output.scale,
                                max_render_pixels=recipe.normalization.max_render_pixels,
                            )
                        else:
                            _render_source_page_png(
                                fitz,
                                page,
                                destination,
                                clip=clip,
                                scale=output.scale,
                                max_render_pixels=recipe.normalization.max_render_pixels,
                            )
                    else:
                        raise ArtifactValidationError(
                            f"asset {asset.asset_key!r} has unsupported output {output.format!r}"
                        )
                    records.append(
                        _artifact_record(
                            destination,
                            artifact_root=artifact_root,
                            format_name=output.format,
                            kind="asset_export",
                            source_page=asset.page,
                            repo_path=output.path,
                            asset_key=asset.asset_key,
                            expected_sha256=output.expected_sha256,
                            gate_status=asset.gate.status,
                            build_eligible=asset.build_eligible,
                            visual_review_required=asset.visual_review_required,
                            text_policy=asset.text_policy,
                        )
                    )
        finally:
            source.close()
    return records


def extract_artifacts(
    source_path: Path,
    recipe: IntakeRecipe,
    artifact_root: Path,
) -> tuple[ArtifactRecord, ...]:
    """Extract archive pages and recipe crops into an isolated artifact root."""

    fitz = _fitz()
    with fitz.open(str(source_path)) as source:
        records = _archive_artifacts(fitz, source, recipe, artifact_root)
    records.extend(_asset_artifacts(fitz, source_path, recipe, artifact_root))
    return tuple(sorted(records, key=lambda record: record.path))
