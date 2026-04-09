from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DingTalkAccessToken:
    access_token: str
    expires_in_seconds: int
    token_type: str = "app_only"


@dataclass(frozen=True)
class DingTalkRecordReference:
    app_name: str
    table_id: str
    record_id: str


@dataclass(frozen=True)
class DingTalkFileReference:
    file_id: str
    download_url: str | None = None
    share_url: str | None = None


class DingTalkAuthClient(Protocol):
    def get_app_only_token(self) -> DingTalkAccessToken:
        ...


class DingTalkRecordClient(Protocol):
    def list_records(self, *, app_name: str, table_id: str, view_id: str | None = None) -> list[dict[str, Any]]:
        ...

    def get_record(self, ref: DingTalkRecordReference) -> dict[str, Any]:
        ...

    def update_record(self, ref: DingTalkRecordReference, *, fields: dict[str, Any]) -> dict[str, Any]:
        ...


class DingTalkFileClient(Protocol):
    def upload_file(self, *, file_path: str, file_name: str | None = None) -> DingTalkFileReference:
        ...

    def resolve_share_url(self, ref: DingTalkFileReference) -> str:
        ...


class DingTalkWorkspaceClient(Protocol):
    def attach_file(self, *, file_ref: DingTalkFileReference, workspace_id: str, parent_node_id: str) -> str:
        ...
