from __future__ import annotations

import os
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

from tools.word_bundle_docx_xml import serialize_xml_preserving_namespaces

SOURCE_DATE_EPOCH_ENV = "SOURCE_DATE_EPOCH"

_DCTERMS_NS = "http://purl.org/dc/terms/"
_FILE_URI_RE = re.compile(r"^file://", re.IGNORECASE)


def _source_date_epoch(env: dict[str, str] | None = None) -> int | None:
    raw = (env or os.environ).get(SOURCE_DATE_EPOCH_ENV, "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{SOURCE_DATE_EPOCH_ENV} must be an integer Unix timestamp") from exc
    if value < 0:
        raise RuntimeError(f"{SOURCE_DATE_EPOCH_ENV} must not be negative")
    return value


def _stable_datetime(epoch: int) -> datetime:
    value = datetime.fromtimestamp(epoch, tz=timezone.utc).replace(microsecond=0)
    # ZIP's DOS timestamp range starts in 1980 and stores two-second
    # resolution.  Git release commits are newer, but clamp defensively so the
    # normalizer remains total for synthetic fixtures.
    if value.year < 1980:
        value = datetime(1980, 1, 1, tzinfo=timezone.utc)
    if value.year > 2107:
        value = datetime(2107, 12, 31, 23, 59, 58, tzinfo=timezone.utc)
    return value.replace(second=value.second - (value.second % 2))


def _stable_file_description(value: str) -> str:
    if not _FILE_URI_RE.match(value):
        return value
    parsed = urlparse(value)
    name = Path(unquote(parsed.path)).name
    return name or "embedded-image"


def _normalize_xml(payload: bytes, *, member_name: str, iso_timestamp: str) -> bytes:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return payload

    changed = False
    if member_name == "docProps/core.xml":
        for tag in ("created", "modified"):
            element = root.find(f"{{{_DCTERMS_NS}}}{tag}")
            if element is not None and element.text != iso_timestamp:
                element.text = iso_timestamp
                changed = True

    if member_name.startswith("word/"):
        for element in root.iter():
            description = element.attrib.get("descr")
            if description is None:
                continue
            stable = _stable_file_description(description)
            if stable != description:
                element.attrib["descr"] = stable
                changed = True

    if not changed:
        return payload
    return serialize_xml_preserving_namespaces(root, original_xml=payload)


def _normalized_zip_info(source: zipfile.ZipInfo, *, date_time: tuple[int, int, int, int, int, int]) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(source.filename, date_time=date_time)
    info.compress_type = source.compress_type
    info.comment = source.comment
    info.create_system = source.create_system
    info.create_version = source.create_version
    info.extract_version = source.extract_version
    info.external_attr = source.external_attr
    info.internal_attr = source.internal_attr
    # Extended timestamp/path fields can contain host-local metadata.  None are
    # required by OPC/DOCX, so omit them from the normalized archive.
    info.extra = b""
    return info


def normalize_docx_for_reproducibility(
    docx_path: Path,
    *,
    source_date_epoch: int | None = None,
) -> None:
    """Canonicalize release DOCX metadata and container bytes.

    Ordinary draft builds are left untouched.  Publish establishes
    ``SOURCE_DATE_EPOCH`` from the release Git commit; in that environment the
    function removes absolute build paths, fixes core timestamps, and writes a
    deterministic OPC ZIP so a rebuild can be compared byte-for-byte.
    """

    epoch = source_date_epoch if source_date_epoch is not None else _source_date_epoch()
    if epoch is None:
        return
    stable_time = _stable_datetime(epoch)
    iso_timestamp = datetime.fromtimestamp(epoch, tz=timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    zip_time = (
        stable_time.year,
        stable_time.month,
        stable_time.day,
        stable_time.hour,
        stable_time.minute,
        stable_time.second,
    )

    with zipfile.ZipFile(docx_path, "r") as source:
        entries = [(info, source.read(info.filename)) for info in source.infolist()]
        archive_comment = source.comment

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{docx_path.name}.",
        suffix=".tmp",
        dir=docx_path.parent,
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        with zipfile.ZipFile(temp_path, "w") as output:
            output.comment = archive_comment
            for original_info, payload in entries:
                normalized_payload = (
                    _normalize_xml(
                        payload,
                        member_name=original_info.filename,
                        iso_timestamp=iso_timestamp,
                    )
                    if original_info.filename.endswith(".xml")
                    else payload
                )
                output.writestr(
                    _normalized_zip_info(original_info, date_time=zip_time),
                    normalized_payload,
                )
        temp_path.replace(docx_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
