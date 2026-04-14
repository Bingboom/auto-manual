from __future__ import annotations

import json
import mimetypes
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from .workspace import normalize_node_url, parse_node_id_from_url


ALIDOCS_ORIGIN = "https://alidocs.dingtalk.com"
DEFAULT_BX_VERSION = "2.5.36"
DEFAULT_SESSION_REGISTRY_ROOT = Path.home() / ".auto-manual" / "dingtalk-sessions"


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


def _required_env(name: str, *, environ: dict[str, str] | os._Environ[str]) -> str:
    value = str(environ.get(name, "")).strip()
    if not value:
        raise RuntimeError(f"Required AliDocs session environment variable is not set: {name}")
    return value


def load_session_config(
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
    a_token_env: str = "DINGTALK_DOCS_A_TOKEN",
    xsrf_token_env: str = "DINGTALK_DOCS_XSRF_TOKEN",
    cookie_env: str = "DINGTALK_DOCS_COOKIE",
    bx_version_env: str = "DINGTALK_DOCS_BX_V",
) -> AliDocsSessionConfig:
    current_environ = os.environ if environ is None else environ
    return AliDocsSessionConfig(
        a_token=_required_env(a_token_env, environ=current_environ),
        xsrf_token=_required_env(xsrf_token_env, environ=current_environ),
        cookie=_required_env(cookie_env, environ=current_environ),
        bx_version=str(current_environ.get(bx_version_env, DEFAULT_BX_VERSION)).strip() or DEFAULT_BX_VERSION,
    )


def load_session_config_from_env() -> AliDocsSessionConfig:
    return load_session_config()


def _session_registry_root(
    *,
    environ: dict[str, str] | os._Environ[str],
    registry_root_env: str,
) -> Path:
    root_value = str(environ.get(registry_root_env, "")).strip()
    if root_value:
        return Path(root_value).expanduser()
    return DEFAULT_SESSION_REGISTRY_ROOT


def _read_session_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Failed to read AliDocs session file: {path}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"AliDocs session file is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"AliDocs session file must contain a JSON object: {path}")
    return payload


def _payload_text(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(payload.get(key, "") or "").strip()
        if value:
            return value
    return ""


def load_session_config_for_operator_union_id(
    *,
    operator_union_id: str,
    environ: dict[str, str] | os._Environ[str] | None = None,
    a_token_env: str = "DINGTALK_DOCS_A_TOKEN",
    xsrf_token_env: str = "DINGTALK_DOCS_XSRF_TOKEN",
    cookie_env: str = "DINGTALK_DOCS_COOKIE",
    bx_version_env: str = "DINGTALK_DOCS_BX_V",
    registry_root_env: str = "AUTO_MANUAL_DINGTALK_SESSION_ROOT",
) -> AliDocsSessionConfig:
    current_environ = os.environ if environ is None else environ
    normalized_operator_union_id = str(operator_union_id or "").strip()
    if not normalized_operator_union_id:
        return load_session_config(
            environ=current_environ,
            a_token_env=a_token_env,
            xsrf_token_env=xsrf_token_env,
            cookie_env=cookie_env,
            bx_version_env=bx_version_env,
        )

    session_path = _session_registry_root(
        environ=current_environ,
        registry_root_env=registry_root_env,
    ) / f"{normalized_operator_union_id}.json"
    if session_path.exists():
        payload = _read_session_payload(session_path)
        a_token = _payload_text(payload, "a_token", "aToken", a_token_env)
        xsrf_token = _payload_text(payload, "xsrf_token", "xsrfToken", "x_xsrf_token", xsrf_token_env)
        cookie = _payload_text(payload, "cookie", cookie_env)
        bx_version = _payload_text(payload, "bx_version", "bxVersion", bx_version_env) or DEFAULT_BX_VERSION
        missing: list[str] = []
        if not a_token:
            missing.append("a_token")
        if not xsrf_token:
            missing.append("xsrf_token")
        if not cookie:
            missing.append("cookie")
        if missing:
            raise RuntimeError(
                "AliDocs session file is missing required keys for "
                f"operator_union_id={normalized_operator_union_id}: {', '.join(missing)} ({session_path})"
            )
        return AliDocsSessionConfig(
            a_token=a_token,
            xsrf_token=xsrf_token,
            cookie=cookie,
            bx_version=bx_version,
        )

    try:
        return load_session_config(
            environ=current_environ,
            a_token_env=a_token_env,
            xsrf_token_env=xsrf_token_env,
            cookie_env=cookie_env,
            bx_version_env=bx_version_env,
        )
    except RuntimeError as exc:
        raise RuntimeError(
            "No AliDocs session found for "
            f"operator_union_id={normalized_operator_union_id}. Expected session file {session_path} "
            f"or environment variables {a_token_env}, {xsrf_token_env}, {cookie_env}."
        ) from exc


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
    normalized_parent_node_url = normalize_node_url(parent_node_url)
    parent_dentry_uuid = parse_node_id_from_url(normalized_parent_node_url)
    ticket = request_upload_ticket(
        session=session,
        parent_dentry_uuid=parent_dentry_uuid,
        file_path=file_path,
        referer_url=normalized_parent_node_url,
    )
    upload_file_to_oss(ticket=ticket, file_path=file_path)
    return commit_uploaded_file(session=session, ticket=ticket, referer_url=normalized_parent_node_url)
