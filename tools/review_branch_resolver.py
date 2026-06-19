"""Resolve a Feishu cloud-doc to its in-review branch via the Document_link build
table (``文档构建表``).

A target's ``docs/_review/<model>/<region>/`` tree exists only on the review
branch recorded as ``Git_ref`` for that document — NOT on the default branch a
backport runs from. So a `cloud-doc backport` that names an edited cloud-doc must
first map it to that review branch; otherwise the `_review` source is "not found"
on the current checkout. This module is the deterministic resolver:

    cloud-doc URL --(飞书云文档 column)--> build-table record --> Git_ref + Document_ID
    Document_ID ("JE-1000F_US_1.4") --> model / region --> docs/_review/<model>/<region>

It is pure (records are passed in); the live fetch + the worktree run are layered
on top by the CLI. Matching is by the doc TOKEN (the path segment after
``/wiki/`` etc.), so markdown-wrapped or duplicated URLs still match.
"""

from __future__ import annotations

import re
from typing import Any

from tools.document_link_queue import field_value, scalar_text

# The path segment that identifies a Feishu doc (wiki node / docx / base / ...).
_DOC_TOKEN_RE = re.compile(r"/(?:wiki|docx|docs|file|sheets|base)/([A-Za-z0-9]+)")

CLOUD_DOC_FIELDS = ("飞书云文档", "飞书云文档链接", "Feishu_doc", "cloud_doc")
GIT_REF_FIELDS = ("Git_ref",)
DOCUMENT_ID_FIELDS = ("Document_ID",)
REVIEW_STATUS_FIELDS = ("Review_status",)
PR_URL_FIELDS = ("PR_url",)

IN_REVIEW_STATUS = "InReview"


def doc_token(url: str | None) -> str:
    """Extract the Feishu doc token (the id after ``/wiki/`` etc.) from a URL."""
    match = _DOC_TOKEN_RE.search(str(url or ""))
    return match.group(1) if match else ""


def parse_document_id(document_id: str | None) -> tuple[str, str, str] | None:
    """``JE-1000F_US_1.4`` -> ``(model, region, version)``.

    The first ``_``-segment is the model, the last is the version, and everything
    between is the region (so a region like ``pt-BR`` survives). Returns ``None``
    when the id does not have all three parts.
    """
    parts = [part for part in str(document_id or "").split("_") if part != ""]
    if len(parts) < 3:
        return None
    model, version, region = parts[0], parts[-1], "_".join(parts[1:-1])
    if not (model and region and version):
        return None
    return model, region, version


def _record_to_match(fields: dict[str, Any]) -> dict[str, Any] | None:
    git_ref = scalar_text(field_value(fields, *GIT_REF_FIELDS))
    if not git_ref:
        return None
    document_id = scalar_text(field_value(fields, *DOCUMENT_ID_FIELDS))
    parsed = parse_document_id(document_id)
    if parsed is None:
        return None
    model, region, version = parsed
    return {
        "git_ref": git_ref,
        "document_id": document_id,
        "model": model,
        "region": region,
        "version": version,
        "review_dir": f"docs/_review/{model}/{region}",
        "pr_url": scalar_text(field_value(fields, *PR_URL_FIELDS)),
        "review_status": scalar_text(field_value(fields, *REVIEW_STATUS_FIELDS)),
    }


def match_review_branch(cloud_doc_url: str, raw_records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Match the edited cloud-doc to its review branch via the build table.

    Returns a dict ``{git_ref, document_id, model, region, version, review_dir,
    pr_url, review_status}`` or ``None`` when no record references the cloud-doc.
    Raises ``RuntimeError`` when the cloud-doc maps to more than one **distinct**
    ``Git_ref`` (ambiguous — never guess which branch to write).
    """
    token = doc_token(cloud_doc_url)
    if not token:
        return None
    matches: list[dict[str, Any]] = []
    for record in raw_records:
        fields = record.get("fields") or {}
        if not isinstance(fields, dict):
            continue
        if doc_token(scalar_text(field_value(fields, *CLOUD_DOC_FIELDS))) != token:
            continue
        match = _record_to_match(fields)
        if match is not None:
            matches.append(match)
    if not matches:
        return None
    # Prefer active reviews; fall back to all matches if none are InReview.
    preferred = [m for m in matches if m["review_status"] == IN_REVIEW_STATUS] or matches
    refs = sorted({m["git_ref"] for m in preferred})
    if len(refs) > 1:
        raise RuntimeError(f"cloud-doc maps to multiple review branches (ambiguous): {refs}")
    return preferred[0]
