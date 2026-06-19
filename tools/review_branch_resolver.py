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
    """``JE-1000F_US_1.4`` / ``JE-1000F_EU_en_0.8`` -> ``(model, region, version)``.

    The first ``_``-segment is the model and the **second is the region** (US / EU
    / JP / CN / pt-BR — always a single segment; the `docs/_review/<model>/<region>`
    tree stops at the region). Any middle segment (e.g. a language ``en``) and the
    trailing version are not part of the review dir. Returns ``None`` when the id
    has fewer than three segments.
    """
    parts = [part for part in str(document_id or "").split("_") if part != ""]
    if len(parts) < 3:
        return None
    model, region, version = parts[0], parts[1], parts[-1]
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


_NAME_DROP_TOKENS = {"manual", "副本", "copy", "draft", "test"}


def _alnum(value: str) -> str:
    return re.sub(r"[^0-9a-z]", "", str(value or "").lower())


def parse_doc_name(name: str) -> tuple[str, str] | None:
    """Extract ``(model, region)`` tokens from a doc NAME like
    ``manual_je1000f_eu_en_0.8 副本`` -> ``("je1000f", "eu")`` (the first two
    meaningful segments). Used to identify the review branch when the cloud-doc
    URL is not registered in the build table (e.g. a 副本/copy of a doc)."""
    tokens = [
        token
        for token in re.split(r"[\s_]+", str(name or "").strip())
        if token and token.lower() not in _NAME_DROP_TOKENS
    ]
    if len(tokens) < 2:
        return None
    return tokens[0], tokens[1]


def _select_match(matches: list[dict[str, Any]], *, label: str) -> dict[str, Any] | None:
    """Prefer InReview; abstain (raise) on more than one distinct ``Git_ref``."""
    if not matches:
        return None
    preferred = [m for m in matches if m["review_status"] == IN_REVIEW_STATUS] or matches
    refs = sorted({m["git_ref"] for m in preferred})
    if len(refs) > 1:
        raise RuntimeError(f"{label} maps to multiple review branches (ambiguous): {refs}")
    return preferred[0]


def _matches_by_token(token: str, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in raw_records:
        fields = record.get("fields") or {}
        if isinstance(fields, dict) and doc_token(scalar_text(field_value(fields, *CLOUD_DOC_FIELDS))) == token:
            match = _record_to_match(fields)
            if match is not None:
                out.append(match)
    return out


def match_review_branch_by_name(name: str, raw_records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Match a doc NAME to its review branch by **model + region** (ignoring
    language/version), for cloud-docs whose URL is not in the build table (a
    副本/copy). Abstains (raises) on more than one distinct ``Git_ref``."""
    parsed = parse_doc_name(name)
    if parsed is None:
        return None
    model_token, region_token = _alnum(parsed[0]), _alnum(parsed[1])
    out: list[dict[str, Any]] = []
    for record in raw_records:
        fields = record.get("fields") or {}
        if not isinstance(fields, dict):
            continue
        match = _record_to_match(fields)
        if match is not None and _alnum(match["model"]) == model_token and _alnum(match["region"]) == region_token:
            out.append(match)
    return _select_match(out, label=f"doc name {name!r}")


def match_review_branch(cloud_doc_url: str, raw_records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Match the edited cloud-doc to its review branch via the build table.

    Tries the cloud-doc URL token (vs the ``飞书云文档`` column) first, then falls
    back to matching the input as a doc NAME (model+region) when the URL is absent
    or unregistered (e.g. a 副本/copy). Returns ``{git_ref, document_id, model,
    region, version, review_dir, pr_url, review_status}`` or ``None``; raises when
    the match is ambiguous (>1 distinct ``Git_ref``).
    """
    token = doc_token(cloud_doc_url)
    if token:
        result = _select_match(_matches_by_token(token, raw_records), label="cloud-doc")
        if result is not None:
            return result
    return match_review_branch_by_name(cloud_doc_url, raw_records)


def list_in_review_branches(raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every distinct **InReview** review branch in the build table (one entry per
    ``Git_ref``) — so a sync step can ensure a worktree exists for each."""
    by_ref: dict[str, dict[str, Any]] = {}
    for record in raw_records:
        fields = record.get("fields") or {}
        if not isinstance(fields, dict):
            continue
        if scalar_text(field_value(fields, *REVIEW_STATUS_FIELDS)) != IN_REVIEW_STATUS:
            continue
        match = _record_to_match(fields)
        if match is not None:
            by_ref.setdefault(match["git_ref"], match)
    return list(by_ref.values())
