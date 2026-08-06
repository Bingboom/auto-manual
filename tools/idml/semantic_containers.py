"""Projection of RST semantic containers into extractor blocks."""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def append_semantic_container(
    result: Any,
    arg: str,
    body: list[str],
    tags: set[str] | None,
    parse_text: Callable[[str, set[str] | None], Any],
) -> None:
    """Append one supported semantic container, preserving nested metadata."""
    dedent = min(
        (len(line) - len(line.lstrip()) for line in body if line.strip()),
        default=0,
    )
    inner = parse_text("\n".join(line[dedent:] for line in body), tags)
    roles = [role.strip().replace("-", "_") for role in arg.split() if role.strip()]
    semantic_kind = next(
        (
            role
            for role in roles
            if role in {"warranty_lead", "warranty_section"}
        ),
        None,
    )
    if semantic_kind is None:
        result.blocks.extend(inner.blocks)
    else:
        result.blocks.append(("semantic", json.dumps({
            "kind": semantic_kind,
            "roles": roles,
            "blocks": [
                {"kind": kind, "payload": payload}
                for kind, payload in inner.blocks
            ],
        }, ensure_ascii=False)))
    result.skipped_raw += inner.skipped_raw
    result.twocol = result.twocol or inner.twocol
