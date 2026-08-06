"""Public block/result contract for the lightweight RST extractor."""
from __future__ import annotations

from dataclasses import dataclass, field

Block = tuple[str, str]
EMITTED_COMPONENT_KINDS = (
    "langtag",
    "fcc",
    "inbox",
    "lcdmode",
    "notice",
    "safetyinstruction",
    "safetywarning",
    "warninglead",
    "warnbox",
)
# JSON block payloads must be unescaped inside their values, not their envelope.
JSON_BLOCK_KINDS = frozenset({"component", "data", "semantic", "table"})


@dataclass
class ExtractResult:
    blocks: list[Block] = field(default_factory=list)
    skipped_raw: int = 0
    twocol: bool = False  # page contains a safetytwocol region
