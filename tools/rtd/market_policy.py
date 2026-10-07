"""Read a local business-content snapshot for the market and policy primer."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

PAGE = "market/policy"
TEMPLATE = "market_policy.html"
CONTENT_DIR = "market-policy"
_ID = re.compile(r"[a-z][a-z0-9-]*")


def _validate_record(record: dict, ids: set[str]) -> None:
    key = record["id"]
    if not _ID.fullmatch(key) or key in ids:
        raise ValueError("market policy record ids must be unique lower-case ids")
    ids.add(key)
    if record["status"] not in {"verified", "unverified", "demand"}:
        raise ValueError(f"unknown policy verification status: {key}")
    for field in ("title", "country", "region", "timeline", "change", "mechanism",
                  "impact", "reviewed"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"market policy record {key} needs {field}")
    if not isinstance(record.get("boundary", ""), str):
        raise ValueError(f"market policy record {key} needs a text boundary")


def _validate_evidence(record: dict, source: Path) -> None:
    key = record["id"]
    note = record.get("evidence_note", "")
    if not isinstance(note, str):
        raise ValueError(f"market policy record {key} needs a text evidence note")
    recorded_basis = record["status"] != "verified" and bool(note.strip())
    if not record["tags"] or not (record["sources"] or record.get("image") or recorded_basis):
        raise ValueError(f"market policy record {key} needs tags and evidence")
    if image := record.get("image"):
        asset = source.parent / "_assets" / image
        if Path(image).name != image or asset.is_symlink() or not asset.is_file():
            raise ValueError(f"missing or unsafe policy source image: {key}")
    for ref in record["sources"]:
        parts = urlsplit(ref["url"])
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            raise ValueError(f"market policy source must be a public HTTPS URL: {key}")
    if record["status"] == "verified" and not any(
        ref["kind"] == "official" for ref in record["sources"]
    ):
        raise ValueError(f"verified policy record {key} needs an official source")


def market_context(knowledge_root: Path) -> dict:
    """Missing content has an empty state; malformed content fails the build."""
    source = knowledge_root / CONTENT_DIR / "records.json"
    if not source.is_file():
        return {"records": [], "countries": [], "market_tags": [], "reviewed": ""}
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("market policy snapshot needs schema_version 1")
    ids = set()
    for record in data["records"]:
        _validate_record(record, ids)
        _validate_evidence(record, source)
        for link in record.get("knowledge", []):
            if not _ID.fullmatch(link["id"]):
                raise ValueError(f"invalid knowledge anchor: {record['id']}")
    return {
        "records": data["records"], "reviewed": data["reviewed"],
        "countries": sorted({r["country"] for r in data["records"]}),
        "market_tags": list(dict.fromkeys(tag for r in data["records"] for tag in r["tags"])),
    }
