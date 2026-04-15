from __future__ import annotations

from pathlib import Path

from .contracts import DingTalkFileReference


def upload_file(*, file_path: Path, file_name: str | None = None) -> DingTalkFileReference:
    raise NotImplementedError(
        "Phase 0 placeholder: implement file upload after the chosen DingTalk storage API is confirmed."
    )


def resolve_share_url(file_ref: DingTalkFileReference) -> str:
    raise NotImplementedError(
        "Phase 0 placeholder: implement link resolution after the storage API confirms durable tenant-visible URLs."
    )
