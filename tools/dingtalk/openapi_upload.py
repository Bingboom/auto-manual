from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from .workspace import parse_node_id_from_url


DEFAULT_OPENAPI_ORIGIN = "https://api.dingtalk.com"
DEFAULT_UPLOAD_INFO_URL_TEMPLATE = DEFAULT_OPENAPI_ORIGIN + "/v2.0/storage/spaces/files/{parent_dentry_uuid}/uploadInfos/query"
DEFAULT_COMMIT_URL_TEMPLATE = DEFAULT_OPENAPI_ORIGIN + "/v2.0/storage/spaces/files/{parent_dentry_uuid}/commit"
DEFAULT_AUTH_HEADER = "x-acs-dingtalk-access-token"
DEFAULT_STORAGE_DRIVER = "DINGTALK"


@dataclass(frozen=True)
class OpenAPIUploadRequest:
    method: str
    url: str
    headers: dict[str, str]


@dataclass(frozen=True)
class OpenAPIUploadInfo:
    upload_key: str
    parent_dentry_uuid: str
    operator_union_id: str
    file_name: str
    file_size: int
    upload_request: OpenAPIUploadRequest
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class OpenAPICommittedFile:
    dentry_id: str
    dentry_uuid: str
    name: str
    raw_payload: dict[str, Any]

    @property
    def candidate_node_url(self) -> str | None:
        uuid = str(self.dentry_uuid or "").strip()
        if not uuid:
            return None
        return f"https://alidocs.dingtalk.com/i/nodes/{uuid}"


def _required_env(name: str, *, environ: dict[str, str] | os._Environ[str]) -> str:
    value = str(environ.get(name, "")).strip()
    if not value:
        raise RuntimeError(f"Required DingTalk environment variable is not set: {name}")
    return value


def _json_request(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    json_body: dict[str, Any] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    data = None
    current_headers = {str(key): str(value) for key, value in headers.items()}
    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        current_headers.setdefault("content-type", "application/json")
    req = request.Request(url=url, method=method.upper(), data=data, headers=current_headers)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail: Any = raw
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            pass
        raise RuntimeError(
            "DingTalk OpenAPI request failed: "
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
            "DingTalk OpenAPI request failed: "
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
        raise RuntimeError(f"DingTalk OpenAPI response is not valid JSON: {raw}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("DingTalk OpenAPI response is not a JSON object")
    return parsed


def _raw_request(
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout_seconds: float = 120.0,
) -> tuple[int, dict[str, str], str]:
    req = request.Request(
        url=url,
        method=method.upper(),
        data=data,
        headers={str(key): str(value) for key, value in (headers or {}).items()},
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return getattr(resp, "status", 200), {str(k): str(v) for k, v in resp.headers.items()}, raw
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "DingTalk OpenAPI upload request failed: "
            + json.dumps(
                {
                    "status": exc.code,
                    "url": url,
                    "reason": str(exc.reason),
                    "response": raw,
                },
                ensure_ascii=False,
            )
        ) from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "DingTalk OpenAPI upload request failed: "
            + json.dumps(
                {
                    "url": url,
                    "reason": str(exc),
                    "transport_error": exc.__class__.__name__,
                },
                ensure_ascii=False,
            )
        ) from exc


def parse_upload_resource(
    payload: dict[str, Any],
    *,
    prefer_internal_url: bool = False,
) -> OpenAPIUploadRequest:
    header_info = payload.get("headerSignatureInfo")
    if not isinstance(header_info, dict):
        raise RuntimeError("uploadInfos response is missing headerSignatureInfo")
    url_key = "internalResourceUrls" if prefer_internal_url else "resourceUrls"
    url_candidates = header_info.get(url_key)
    if prefer_internal_url and not url_candidates:
        url_candidates = header_info.get("resourceUrls")
    if not isinstance(url_candidates, list) or not url_candidates:
        raise RuntimeError("uploadInfos response is missing usable resourceUrls")
    first_resource = url_candidates[0]
    method = "PUT"
    url = ""
    headers: dict[str, str] = {}
    if isinstance(first_resource, str):
        url = first_resource.strip()
    elif isinstance(first_resource, dict):
        url = str(first_resource.get("url") or first_resource.get("resourceUrl") or "").strip()
        method = str(first_resource.get("method") or "PUT").strip().upper() or "PUT"
        resource_headers = first_resource.get("headers")
        if isinstance(resource_headers, dict):
            headers.update({str(k): str(v) for k, v in resource_headers.items()})
    if not url:
        raise RuntimeError("uploadInfos response did not include a usable upload URL")
    info_headers = header_info.get("headers")
    if isinstance(info_headers, dict):
        headers.update({str(k): str(v) for k, v in info_headers.items()})
    return OpenAPIUploadRequest(method=method, url=url, headers=headers)


def request_upload_info(
    *,
    access_token: str,
    parent_node_id: str,
    operator_union_id: str,
    file_path: Path,
    storage_driver: str = DEFAULT_STORAGE_DRIVER,
    prefer_intranet: bool = False,
    prefer_region: str | None = None,
    endpoint_template: str = DEFAULT_UPLOAD_INFO_URL_TEMPLATE,
    timeout_seconds: float = 30.0,
    prefer_internal_url: bool = False,
) -> OpenAPIUploadInfo:
    if not file_path.exists():
        raise RuntimeError(f"Upload file does not exist: {file_path}")
    url = endpoint_template.format(parent_dentry_uuid=parent_node_id)
    url = parse.urlunparse(
        parse.urlparse(url)._replace(
            query=parse.urlencode({"unionId": operator_union_id})
        )
    )
    option: dict[str, Any] = {
        "storageDriver": storage_driver,
        "preferIntranet": bool(prefer_intranet),
        "preCheckParam": {
            "size": file_path.stat().st_size,
            "name": file_path.name,
        },
    }
    if prefer_region:
        option["preferRegion"] = str(prefer_region).strip()
    payload = _json_request(
        method="POST",
        url=url,
        headers={DEFAULT_AUTH_HEADER: access_token},
        json_body={
            "protocol": "HEADER_SIGNATURE",
            "option": option,
        },
        timeout_seconds=timeout_seconds,
    )
    upload_key = str(payload.get("uploadKey") or "").strip()
    if not upload_key:
        raise RuntimeError("uploadInfos response is missing uploadKey")
    upload_request = parse_upload_resource(payload, prefer_internal_url=prefer_internal_url)
    return OpenAPIUploadInfo(
        upload_key=upload_key,
        parent_dentry_uuid=parent_node_id,
        operator_union_id=operator_union_id,
        file_name=file_path.name,
        file_size=file_path.stat().st_size,
        upload_request=upload_request,
        raw_payload=payload,
    )


def upload_file_with_signed_url(
    *,
    upload_info: OpenAPIUploadInfo,
    file_path: Path,
    timeout_seconds: float = 120.0,
) -> None:
    if not file_path.exists():
        raise RuntimeError(f"Upload file does not exist: {file_path}")
    status, _headers, _body = _raw_request(
        method=upload_info.upload_request.method,
        url=upload_info.upload_request.url,
        headers=upload_info.upload_request.headers,
        data=file_path.read_bytes(),
        timeout_seconds=timeout_seconds,
    )
    if status >= 400:
        raise RuntimeError(f"DingTalk signed upload returned unexpected status: {status}")


def commit_uploaded_file(
    *,
    access_token: str,
    parent_node_id: str,
    operator_union_id: str,
    upload_key: str,
    file_name: str,
    file_size: int,
    convert_to_online_doc: bool = False,
    conflict_strategy: str | None = None,
    endpoint_template: str = DEFAULT_COMMIT_URL_TEMPLATE,
    timeout_seconds: float = 30.0,
) -> OpenAPICommittedFile:
    url = endpoint_template.format(parent_dentry_uuid=parent_node_id)
    url = parse.urlunparse(
        parse.urlparse(url)._replace(
            query=parse.urlencode({"unionId": operator_union_id})
        )
    )
    option: dict[str, Any] = {
        "size": int(file_size),
        "convertToOnlineDoc": bool(convert_to_online_doc),
    }
    if conflict_strategy:
        option["conflictStrategy"] = str(conflict_strategy).strip()
    payload = _json_request(
        method="POST",
        url=url,
        headers={DEFAULT_AUTH_HEADER: access_token},
        json_body={
            "uploadKey": upload_key,
            "name": file_name,
            "option": option,
        },
        timeout_seconds=timeout_seconds,
    )
    dentry = payload.get("dentry")
    if not isinstance(dentry, dict):
        raise RuntimeError("commit response is missing dentry payload")
    dentry_uuid = str(dentry.get("uuid") or "").strip()
    dentry_id = str(dentry.get("id") or "").strip()
    if not dentry_uuid and not dentry_id:
        raise RuntimeError("commit response is missing dentry identifiers")
    return OpenAPICommittedFile(
        dentry_id=dentry_id,
        dentry_uuid=dentry_uuid,
        name=str(dentry.get("name") or file_name).strip(),
        raw_payload=payload,
    )


def upload_file_to_node(
    *,
    access_token: str,
    operator_union_id: str,
    file_path: Path,
    parent_node_url: str,
    storage_driver: str = DEFAULT_STORAGE_DRIVER,
    prefer_intranet: bool = False,
    prefer_region: str | None = None,
    convert_to_online_doc: bool = False,
    conflict_strategy: str | None = None,
    timeout_seconds: float = 30.0,
    upload_timeout_seconds: float = 120.0,
    prefer_internal_url: bool = False,
) -> OpenAPICommittedFile:
    parent_node_id = parse_node_id_from_url(parent_node_url)
    upload_info = request_upload_info(
        access_token=access_token,
        parent_node_id=parent_node_id,
        operator_union_id=operator_union_id,
        file_path=file_path,
        storage_driver=storage_driver,
        prefer_intranet=prefer_intranet,
        prefer_region=prefer_region,
        timeout_seconds=timeout_seconds,
        prefer_internal_url=prefer_internal_url,
    )
    upload_file_with_signed_url(
        upload_info=upload_info,
        file_path=file_path,
        timeout_seconds=upload_timeout_seconds,
    )
    return commit_uploaded_file(
        access_token=access_token,
        parent_node_id=parent_node_id,
        operator_union_id=operator_union_id,
        upload_key=upload_info.upload_key,
        file_name=upload_info.file_name,
        file_size=upload_info.file_size,
        convert_to_online_doc=convert_to_online_doc,
        conflict_strategy=conflict_strategy,
        timeout_seconds=timeout_seconds,
    )


def load_operator_union_id(
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
    env_name: str = "DINGTALK_OPERATOR_UNION_ID",
) -> str:
    current_environ = os.environ if environ is None else environ
    return _required_env(env_name, environ=current_environ)


def load_default_target_node_url(
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
    env_name: str = "DINGTALK_DEFAULT_TARGET_NODE_URL",
) -> str:
    current_environ = os.environ if environ is None else environ
    return _required_env(env_name, environ=current_environ)
