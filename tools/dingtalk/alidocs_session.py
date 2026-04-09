from __future__ import annotations

import json
import mimetypes
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from .workspace import parse_node_id_from_url


ALIDOCS_ORIGIN = "https://alidocs.dingtalk.com"
DEFAULT_BX_VERSION = "2.5.36"


@dataclass(frozen=True)
class AliDocsSessionConfig:
    a_token: str
    xsrf_token: str
    cookie: str
    bx_version: str = DEFAULT_BX_VERSION
    origin: str = ALIDOCS_ORIGIN


@dataclass(frozen=True)
class AliDocsUploadTicket:
    parent_dentry_uuid: str
    upload_key: str
    object_key: str
    bucket: str
    endpoint: str
    access_key_id: str
    access_key_secret: str
    security_token: str
    file_name: str
    file_size: int


@dataclass(frozen=True)
class AliDocsCommittedFile:
    dentry_uuid: str
    dentry_id: str
    name: str
    parent_dentry_uuid: str
    space_id: str
    raw_payload: dict[str, Any]

    @property
    def node_url(self) -> str:
        return f"{ALIDOCS_ORIGIN}/i/nodes/{self.dentry_uuid}"


def _required_env(name: str) -> str:
    value = str(os.environ.get(name, "")).strip()
    if not value:
        raise RuntimeError(f"Required AliDocs session environment variable is not set: {name}")
    return value


def load_session_config_from_env() -> AliDocsSessionConfig:
    return AliDocsSessionConfig(
        a_token=_required_env("DINGTALK_DOCS_A_TOKEN"),
        xsrf_token=_required_env("DINGTALK_DOCS_XSRF_TOKEN"),
        cookie=_required_env("DINGTALK_DOCS_COOKIE"),
        bx_version=str(os.environ.get("DINGTALK_DOCS_BX_V", DEFAULT_BX_VERSION)).strip() or DEFAULT_BX_VERSION,
    )


def _json_request(
    *,
    method: str,
    url: str,
    session: AliDocsSessionConfig,
    referer_url: str,
    json_body: dict[str, Any] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    data = None
    headers = {
        "accept": "application/json, text/plain, */*",
        "bx-v": session.bx_version,
        "origin": session.origin,
        "referer": referer_url,
        "cookie": session.cookie,
        "x-xsrf-token": session.xsrf_token,
    }
    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        headers["content-type"] = "application/json"
        headers["a-token"] = session.a_token
    req = request.Request(url=url, method=method.upper(), data=data, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail = raw
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            pass
        raise RuntimeError(
            "AliDocs request failed: "
            + json.dumps(
                {
                    "status": exc.code,
                    "url": url,
                    "reason": str(exc.reason),
                    "response": detail,
                },
                ensure_ascii=False,
            )
        ) from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "AliDocs request failed: "
            + json.dumps(
                {
                    "url": url,
                    "reason": str(exc),
                    "transport_error": exc.__class__.__name__,
                },
                ensure_ascii=False,
            )
        ) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"AliDocs response is not valid JSON: {raw}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("AliDocs response is not a JSON object")
    return parsed


def _require_success(payload: dict[str, Any], *, action: str) -> dict[str, Any]:
    if payload.get("isSuccess") is not True:
        raise RuntimeError(f"AliDocs {action} did not succeed: {json.dumps(payload, ensure_ascii=False)}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"AliDocs {action} response is missing data payload")
    return data


def request_upload_ticket(
    *,
    session: AliDocsSessionConfig,
    parent_dentry_uuid: str,
    file_path: Path,
    referer_url: str,
) -> AliDocsUploadTicket:
    payload = _json_request(
        method="POST",
        url=f"{ALIDOCS_ORIGIN}/box/api/v2/file/uploadinfo",
        session=session,
        referer_url=referer_url,
        json_body={
            "uploadType": "STS_SIGNATURE",
            "supportUploadTypes": ["STS_SIGNATURE", "HTTP_TO_CENTER"],
            "parentDentryUuid": parent_dentry_uuid,
            "fileSize": file_path.stat().st_size,
            "name": file_path.name,
            "multipart": True,
        },
    )
    data = _require_success(payload, action="uploadinfo")
    sts_info = data.get("stsSignatureInfo")
    if not isinstance(sts_info, dict):
        raise RuntimeError("AliDocs uploadinfo response is missing stsSignatureInfo")
    return AliDocsUploadTicket(
        parent_dentry_uuid=parent_dentry_uuid,
        upload_key=str(data.get("uploadKey") or "").strip(),
        object_key=str(sts_info.get("objectKey") or "").strip(),
        bucket=str(sts_info.get("bucket") or "").strip(),
        endpoint=str(sts_info.get("endPoint") or "").strip(),
        access_key_id=str(sts_info.get("accessKeyId") or "").strip(),
        access_key_secret=str(sts_info.get("accessKeySecret") or "").strip(),
        security_token=str(sts_info.get("accessToken") or "").strip(),
        file_name=file_path.name,
        file_size=file_path.stat().st_size,
    )


def _load_oss2() -> Any:
    try:
        import oss2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("AliDocs upload requires the optional 'oss2' package. Install it with 'python -m pip install oss2'.") from exc
    return oss2


def upload_file_to_oss(*, ticket: AliDocsUploadTicket, file_path: Path) -> None:
    if not file_path.exists():
        raise RuntimeError(f"Upload file does not exist: {file_path}")
    oss2 = _load_oss2()
    auth = oss2.StsAuth(ticket.access_key_id, ticket.access_key_secret, ticket.security_token)
    endpoint = ticket.endpoint
    if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
        endpoint = "https://" + endpoint
    bucket = oss2.Bucket(auth, endpoint, ticket.bucket)
    headers = {}
    mime_type = mimetypes.guess_type(file_path.name)[0]
    if mime_type:
        headers["Content-Type"] = mime_type
    result = bucket.put_object_from_file(ticket.object_key, str(file_path), headers=headers or None)
    if getattr(result, "status", 200) >= 400:
        raise RuntimeError(f"AliDocs OSS upload failed with status {getattr(result, 'status', 'unknown')}")


def commit_uploaded_file(
    *,
    session: AliDocsSessionConfig,
    ticket: AliDocsUploadTicket,
    referer_url: str,
) -> AliDocsCommittedFile:
    payload = _json_request(
        method="POST",
        url=f"{ALIDOCS_ORIGIN}/box/api/v2/file/commit",
        session=session,
        referer_url=referer_url,
        json_body={
            "parentDentryUuid": ticket.parent_dentry_uuid,
            "uploadKey": ticket.upload_key,
            "fileSize": ticket.file_size,
            "name": ticket.file_name,
            "toPrevDentryUuid": None,
            "toNextDentryUuid": None,
            "batchId": str(uuid.uuid4()),
            "batchUploadType": 1,
            "batchParentDentryUuid": ticket.parent_dentry_uuid,
        },
    )
    data = _require_success(payload, action="commit")
    dentry_uuid = str(data.get("dentryUuid") or "").strip()
    if not dentry_uuid:
        raise RuntimeError("AliDocs commit response is missing dentryUuid")
    return AliDocsCommittedFile(
        dentry_uuid=dentry_uuid,
        dentry_id=str(data.get("dentryId") or "").strip(),
        name=str(data.get("name") or "").strip(),
        parent_dentry_uuid=str(data.get("parentDentryUuid") or "").strip(),
        space_id=str(data.get("spaceId") or "").strip(),
        raw_payload=data,
    )


def upload_file_to_node(
    *,
    session: AliDocsSessionConfig,
    file_path: Path,
    parent_node_url: str,
) -> AliDocsCommittedFile:
    parent_dentry_uuid = parse_node_id_from_url(parent_node_url)
    ticket = request_upload_ticket(
        session=session,
        parent_dentry_uuid=parent_dentry_uuid,
        file_path=file_path,
        referer_url=parent_node_url,
    )
    upload_file_to_oss(ticket=ticket, file_path=file_path)
    return commit_uploaded_file(session=session, ticket=ticket, referer_url=parent_node_url)
