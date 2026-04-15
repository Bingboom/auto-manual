from __future__ import annotations

import re
from urllib import parse

from .contracts import DingTalkFileReference, DingTalkWorkspaceTarget

_MARKDOWN_LINK_RE = re.compile(r"^\[(?P<label>.*)\]\((?P<target>https?://[^)]+)\)$")


def normalize_node_url(node_url: str) -> str:
    raw = str(node_url or "").strip()
    if not raw:
        raise RuntimeError("Invalid DingTalk workspace URL: ")
    match = _MARKDOWN_LINK_RE.fullmatch(raw)
    if match:
        return match.group("target").strip()
    return raw


def parse_node_id_from_url(node_url: str) -> str:
    normalized_url = normalize_node_url(node_url)
    parsed = parse.urlparse(normalized_url)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"Invalid DingTalk workspace URL: {node_url}")
    segments = [segment for segment in parsed.path.split("/") if segment]
    for index, segment in enumerate(segments):
        if segment == "nodes" and index + 1 < len(segments):
            node_id = segments[index + 1].strip()
            if node_id:
                return node_id
    raise RuntimeError(f"Could not resolve DingTalk workspace node ID from URL: {node_url}")


def workspace_target_from_url(node_url: str) -> DingTalkWorkspaceTarget:
    normalized_url = normalize_node_url(node_url)
    return DingTalkWorkspaceTarget(
        node_id=parse_node_id_from_url(normalized_url),
        source_url=normalized_url,
    )


def attach_file(*, file_ref: DingTalkFileReference, workspace_id: str, parent_node_id: str) -> str:
    raise NotImplementedError(
        "Phase 0 placeholder: implement workspace attach only if the chosen DingTalk doc product supports it."
    )
