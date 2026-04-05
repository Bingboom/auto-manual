from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class DocumentLinkBinding:
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    wiki_parent_token_env: str | None
    base_token: str
    table_id: str
    view_id: str | None
    wiki_parent_token: str | None


@dataclass(frozen=True)
class QueueRecord:
    record_id: str
    document_id: str
    document_key: str
    version: str
    lang: str
    workflow_action: str = ""
    doc_phase: str = ""
    git_ref: str = ""
    trigger_value: str = ""
    immediate_trigger_value: Any = None
    build_family: str = ""

    @property
    def label(self) -> str:
        return self.document_id or f"{self.document_key}_{self.lang}"


@dataclass(frozen=True)
class WikiDestination:
    space_id: str
    parent_wiki_token: str
