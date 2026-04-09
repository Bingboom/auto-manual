#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.script_bootstrap import bootstrap_repo_root
from tools.dingtalk.auth import request_app_only_token_response

ROOT = bootstrap_repo_root(__file__, parent_count=2)


DEFAULT_TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/{corp_id}/token"
DEFAULT_TOKEN_BODY = {
    "client_id": "{client_id}",
    "client_secret": "{client_secret}",
    "grant_type": "client_credentials",
}
DEFAULT_AUTH_HEADER = "x-acs-dingtalk-access-token"


@dataclass(frozen=True)
class HttpResponse:
    status: int
    url: str
    headers: dict[str, str]
    text: str
    json_payload: Any | None


class _SafeTemplateDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _env_text(name: str) -> str | None:
    value = str(os.environ.get(name, "")).strip()
    return value or None


def _coerce_scalar(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def parse_update_set(items: list[str]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise RuntimeError(f"--update-set must use KEY=VALUE format: {item}")
        key, raw_value = item.split("=", 1)
        field_name = key.strip()
        if not field_name:
            raise RuntimeError(f"--update-set key must not be empty: {item}")
        fields[field_name] = _coerce_scalar(raw_value)
    return fields


def load_json_arg(raw: str | None) -> Any | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    if text.startswith("@"):
        text = Path(text[1:]).read_text(encoding="utf-8")
    return json.loads(text)


def render_template_string(template: str, context: dict[str, Any]) -> str:
    return template.format_map(_SafeTemplateDict({key: "" if value is None else value for key, value in context.items()}))


def render_template_object(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return render_template_string(value, context)
    if isinstance(value, list):
        return [render_template_object(item, context) for item in value]
    if isinstance(value, dict):
        return {str(key): render_template_object(item, context) for key, item in value.items()}
    return value


def merge_url_query(url: str, extra_query: dict[str, Any] | None) -> str:
    if not extra_query:
        return url
    parsed = parse.urlparse(url)
    current_pairs = parse.parse_qsl(parsed.query, keep_blank_values=True)
    extra_pairs: list[tuple[str, str]] = []
    for key, value in extra_query.items():
        if isinstance(value, list):
            for item in value:
                extra_pairs.append((str(key), str(item)))
        else:
            extra_pairs.append((str(key), str(value)))
    query = parse.urlencode([*current_pairs, *extra_pairs], doseq=True)
    return parse.urlunparse(parsed._replace(query=query))


def _json_payload_from_text(raw_text: str) -> Any | None:
    text = (raw_text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_json_path(payload: Any, path: str | None) -> Any:
    if not path:
        return payload
    current = payload
    token = ""
    idx = 0
    while idx < len(path):
        ch = path[idx]
        if ch == ".":
            if token:
                if not isinstance(current, dict):
                    raise RuntimeError(f"Path step '{token}' expected an object")
                try:
                    current = current[token]
                except KeyError as exc:
                    raise RuntimeError(f"JSON path '{path}' is missing object key '{token}'") from exc
                token = ""
            idx += 1
            continue
        if ch == "[":
            if token:
                if not isinstance(current, dict):
                    raise RuntimeError(f"Path step '{token}' expected an object before list index")
                try:
                    current = current[token]
                except KeyError as exc:
                    raise RuntimeError(f"JSON path '{path}' is missing object key '{token}'") from exc
                token = ""
            end_idx = path.find("]", idx)
            if end_idx == -1:
                raise RuntimeError(f"Invalid JSON path index: {path}")
            list_index = int(path[idx + 1 : end_idx])
            if not isinstance(current, list):
                raise RuntimeError(f"Path index [{list_index}] expected a list")
            try:
                current = current[list_index]
            except IndexError as exc:
                raise RuntimeError(f"JSON path '{path}' is missing list index [{list_index}]") from exc
            idx = end_idx + 1
            continue
        token += ch
        idx += 1
    if token:
        if not isinstance(current, dict):
            raise RuntimeError(f"Path step '{token}' expected an object")
        try:
            current = current[token]
        except KeyError as exc:
            raise RuntimeError(f"JSON path '{path}' is missing object key '{token}'") from exc
    return current


def _multipart_body(
    *,
    file_field_name: str,
    file_path: Path,
    extra_fields: dict[str, Any] | None = None,
    filename_field_name: str | None = None,
) -> tuple[bytes, str]:
    boundary = "----codex-dingtalk-" + uuid.uuid4().hex
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks: list[bytes] = []

    def _append_line(text: str) -> None:
        chunks.append(text.encode("utf-8"))

    for key, value in (extra_fields or {}).items():
        if isinstance(value, list):
            values = value
        else:
            values = [value]
        for item in values:
            _append_line(f"--{boundary}\r\n")
            _append_line(f'Content-Disposition: form-data; name="{key}"\r\n\r\n')
            _append_line(f"{item}\r\n")

    if filename_field_name:
        _append_line(f"--{boundary}\r\n")
        _append_line(f'Content-Disposition: form-data; name="{filename_field_name}"\r\n\r\n')
        _append_line(f"{file_path.name}\r\n")

    _append_line(f"--{boundary}\r\n")
    _append_line(
        f'Content-Disposition: form-data; name="{file_field_name}"; filename="{file_path.name}"\r\n'
    )
    _append_line(f"Content-Type: {mime_type}\r\n\r\n")
    chunks.append(file_path.read_bytes())
    _append_line("\r\n")
    _append_line(f"--{boundary}--\r\n")
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def http_request(
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    json_body: Any | None = None,
    multipart: tuple[bytes, str] | None = None,
    timeout_seconds: float = 30.0,
) -> HttpResponse:
    resolved_headers = {str(key): str(value) for key, value in (headers or {}).items()}
    data: bytes | None = None

    if json_body is not None and multipart is not None:
        raise RuntimeError("Only one of json_body or multipart may be set")
    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        resolved_headers.setdefault("Content-Type", "application/json")
    elif multipart is not None:
        data, content_type = multipart
        resolved_headers.setdefault("Content-Type", content_type)

    req = request.Request(
        url=url,
        data=data,
        method=method.upper(),
        headers=resolved_headers,
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return HttpResponse(
                status=getattr(resp, "status", 200),
                url=resp.geturl(),
                headers={str(key): str(value) for key, value in resp.headers.items()},
                text=raw,
                json_payload=_json_payload_from_text(raw),
            )
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "HTTP request failed: "
            + json.dumps(
                {
                    "status": exc.code,
                    "url": url,
                    "reason": str(exc.reason),
                    "response": _json_payload_from_text(raw) or raw,
                },
                ensure_ascii=False,
            )
        ) from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "HTTP request failed: "
            + json.dumps(
                {
                    "url": url,
                    "reason": str(exc),
                    "transport_error": exc.__class__.__name__,
                },
                ensure_ascii=False,
            )
        ) from exc


def print_step(label: str, payload: dict[str, Any]) -> None:
    print(f"[dingtalk-spike] {label}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def token_request_payload(args: argparse.Namespace, context: dict[str, Any]) -> dict[str, Any]:
    raw = load_json_arg(args.token_body_json)
    body = DEFAULT_TOKEN_BODY if raw is None else raw
    rendered = render_template_object(body, context)
    if not isinstance(rendered, dict):
        raise RuntimeError("--token-body-json must resolve to a JSON object")
    return rendered


def build_request_inputs(
    *,
    url_template: str,
    body_json: str | None,
    query_json: str | None,
    headers_json: str | None,
    context: dict[str, Any],
) -> tuple[str, Any | None, dict[str, str]]:
    url = render_template_string(url_template, context)
    query_value = render_template_object(load_json_arg(query_json), context)
    if query_value is not None and not isinstance(query_value, dict):
        raise RuntimeError("query JSON must resolve to a JSON object")
    body_value = render_template_object(load_json_arg(body_json), context)
    headers_value = render_template_object(load_json_arg(headers_json), context) or {}
    if not isinstance(headers_value, dict):
        raise RuntimeError("headers JSON must resolve to a JSON object")
    return merge_url_query(url, query_value), body_value, {str(k): str(v) for k, v in headers_value.items()}


def require_text(value: str | None, *, flag_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError(f"{flag_name} is required")
    return text


def resolve_access_token(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    client_id = require_text(args.client_id or _env_text("DINGTALK_CLIENT_ID"), flag_name="--client-id")
    client_secret = require_text(
        args.client_secret or _env_text("DINGTALK_CLIENT_SECRET"),
        flag_name="--client-secret",
    )
    corp_id = require_text(args.corp_id or _env_text("DINGTALK_CORP_ID"), flag_name="--corp-id")
    context = {
        "client_id": client_id,
        "client_secret": client_secret,
        "corp_id": corp_id,
    }
    token_url = render_template_string(args.token_url, context)
    token_body = token_request_payload(args, context)
    if (
        args.token_url == DEFAULT_TOKEN_URL
        and args.token_body_json is None
        and args.token_path == "access_token"
        and args.token_expiry_path == "expires_in"
    ):
        payload = request_app_only_token_response(
            client_id=client_id,
            client_secret=client_secret,
            corp_id=corp_id,
            token_url_template=args.token_url,
        )
    else:
        response = http_request(
            method="POST",
            url=token_url,
            json_body=token_body,
            timeout_seconds=args.timeout_seconds,
        )
        payload = response.json_payload
        if not isinstance(payload, dict):
            raise RuntimeError("Token response is not a JSON object")
    access_token = str(extract_json_path(payload, args.token_path) or "").strip()
    if not access_token:
        raise RuntimeError(f"Could not resolve access token from path: {args.token_path}")
    expires_in = extract_json_path(payload, args.token_expiry_path)
    print_step(
        "token",
        {
            "url": token_url,
            "expires_in": expires_in,
            "token_path": args.token_path,
        },
    )
    return access_token, payload


def run_list_step(args: argparse.Namespace, *, access_token: str) -> tuple[dict[str, Any], str | None]:
    list_url = require_text(args.list_url or _env_text("DINGTALK_SPIKE_LIST_URL"), flag_name="--list-url")
    context = {
        "access_token": access_token,
        "corp_id": args.corp_id or _env_text("DINGTALK_CORP_ID") or "",
        "record_id": args.record_id or "",
    }
    url, body_value, headers = build_request_inputs(
        url_template=list_url,
        body_json=args.list_body_json,
        query_json=args.list_query_json,
        headers_json=args.list_headers_json,
        context=context,
    )
    headers.setdefault(args.auth_header, access_token)
    response = http_request(
        method=args.list_method,
        url=url,
        headers=headers,
        json_body=body_value,
        timeout_seconds=args.timeout_seconds,
    )
    payload = response.json_payload
    if not isinstance(payload, dict):
        raise RuntimeError("List response is not a JSON object")
    record_id = None
    if args.record_id_path:
        resolved = extract_json_path(payload, args.record_id_path)
        record_id = str(resolved or "").strip() or None
    print_step(
        "list",
        {
            "url": url,
            "status": response.status,
            "record_id": record_id,
            "record_id_path": args.record_id_path,
        },
    )
    return payload, record_id


def build_update_body(args: argparse.Namespace, *, record_id: str, context: dict[str, Any]) -> Any:
    if args.update_body_json:
        return render_template_object(load_json_arg(args.update_body_json), context)

    fields: dict[str, Any] = {}
    fields_json = load_json_arg(args.update_fields_json)
    if fields_json is not None:
        rendered_fields = render_template_object(fields_json, context)
        if not isinstance(rendered_fields, dict):
            raise RuntimeError("--update-fields-json must resolve to a JSON object")
        fields.update(rendered_fields)
    fields.update(render_template_object(parse_update_set(args.update_set), context))
    if not fields:
        raise RuntimeError("Update step requires --update-body-json, --update-fields-json, or at least one --update-set")

    body: dict[str, Any] = {}
    if args.update_record_id_key:
        body[args.update_record_id_key] = record_id
    if args.update_fields_key:
        body[args.update_fields_key] = fields
    else:
        body.update(fields)
    return body


def run_update_step(args: argparse.Namespace, *, access_token: str, record_id: str) -> dict[str, Any]:
    update_url = require_text(args.update_url or _env_text("DINGTALK_SPIKE_UPDATE_URL"), flag_name="--update-url")
    context = {
        "access_token": access_token,
        "corp_id": args.corp_id or _env_text("DINGTALK_CORP_ID") or "",
        "record_id": record_id,
    }
    url, _unused_body_value, headers = build_request_inputs(
        url_template=update_url,
        body_json=None,
        query_json=args.update_query_json,
        headers_json=args.update_headers_json,
        context=context,
    )
    headers.setdefault(args.auth_header, access_token)
    body_value = build_update_body(args, record_id=record_id, context=context)
    response = http_request(
        method=args.update_method,
        url=url,
        headers=headers,
        json_body=body_value,
        timeout_seconds=args.timeout_seconds,
    )
    payload = response.json_payload
    if not isinstance(payload, dict):
        raise RuntimeError("Update response is not a JSON object")
    print_step(
        "update",
        {
            "url": url,
            "status": response.status,
            "record_id": record_id,
        },
    )
    return payload


def run_upload_step(args: argparse.Namespace, *, access_token: str) -> dict[str, Any]:
    upload_url = require_text(args.upload_url or _env_text("DINGTALK_SPIKE_UPLOAD_URL"), flag_name="--upload-url")
    upload_file: Path | None = None
    if args.upload_file:
        upload_file = Path(args.upload_file).resolve()
        if not upload_file.exists():
            raise RuntimeError(f"Upload file does not exist: {upload_file}")
    elif args.upload_body_json is None:
        raise RuntimeError("--upload-file is required unless --upload-body-json is provided")

    context = {
        "access_token": access_token,
        "corp_id": args.corp_id or _env_text("DINGTALK_CORP_ID") or "",
        "file_name": upload_file.name if upload_file is not None else "",
        "file_path": str(upload_file) if upload_file is not None else "",
    }
    url, body_value, headers = build_request_inputs(
        url_template=upload_url,
        body_json=args.upload_body_json,
        query_json=args.upload_query_json,
        headers_json=args.upload_headers_json,
        context=context,
    )
    headers.setdefault(args.auth_header, access_token)

    if body_value is not None:
        response = http_request(
            method=args.upload_method,
            url=url,
            headers=headers,
            json_body=body_value,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        if upload_file is None:
            raise RuntimeError("Multipart upload requires --upload-file")
        form_fields = render_template_object(load_json_arg(args.upload_form_fields_json), context) or {}
        if not isinstance(form_fields, dict):
            raise RuntimeError("--upload-form-fields-json must resolve to a JSON object")
        multipart = _multipart_body(
            file_field_name=args.upload_file_field,
            file_path=upload_file,
            extra_fields=form_fields,
            filename_field_name=args.upload_filename_field,
        )
        response = http_request(
            method=args.upload_method,
            url=url,
            headers=headers,
            multipart=multipart,
            timeout_seconds=args.timeout_seconds,
        )

    payload = response.json_payload
    if not isinstance(payload, dict):
        raise RuntimeError("Upload response is not a JSON object")
    extracted: dict[str, Any] = {
        "url": url,
        "status": response.status,
        "upload_file": str(upload_file) if upload_file is not None else None,
    }
    if args.upload_file_id_path:
        extracted["file_id"] = extract_json_path(payload, args.upload_file_id_path)
    if args.upload_share_url_path:
        extracted["share_url"] = extract_json_path(payload, args.upload_share_url_path)
    print_step("upload", extracted)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Manual DingTalk Phase 0 smoke CLI for token, list, update, and upload checks.")
    ap.add_argument(
        "action",
        choices=("token", "list", "update", "upload", "all"),
        help="Smoke step to run. 'all' runs token -> list -> update -> upload in sequence.",
    )
    ap.add_argument("--client-id", default=None, help="DingTalk Client ID. Defaults to DINGTALK_CLIENT_ID.")
    ap.add_argument("--client-secret", default=None, help="DingTalk Client Secret. Defaults to DINGTALK_CLIENT_SECRET.")
    ap.add_argument("--corp-id", default=None, help="DingTalk Corp ID. Defaults to DINGTALK_CORP_ID.")
    ap.add_argument("--token-url", default=DEFAULT_TOKEN_URL, help="Token endpoint template. Supports {corp_id}.")
    ap.add_argument(
        "--token-body-json",
        default=None,
        help="Optional JSON or @file override for the token request body. String values support template placeholders.",
    )
    ap.add_argument("--token-path", default="access_token", help="JSON path to the access token in the token response.")
    ap.add_argument("--token-expiry-path", default="expires_in", help="JSON path to the expiry field in the token response.")
    ap.add_argument("--auth-header", default=DEFAULT_AUTH_HEADER, help="Header name used for the DingTalk access token.")
    ap.add_argument("--timeout-seconds", type=float, default=30.0, help="Per-request timeout in seconds.")

    ap.add_argument("--list-url", default=None, help="List endpoint URL or template. Defaults to DINGTALK_SPIKE_LIST_URL.")
    ap.add_argument("--list-method", default="GET", help="HTTP method for the list step.")
    ap.add_argument("--list-body-json", default=None, help="Optional JSON or @file body for the list step.")
    ap.add_argument("--list-query-json", default=None, help="Optional JSON or @file query params for the list step.")
    ap.add_argument("--list-headers-json", default=None, help="Optional JSON or @file headers for the list step.")
    ap.add_argument(
        "--record-id-path",
        default=None,
        help="JSON path to the first stable record ID found during the list step, for example items[0].id.",
    )

    ap.add_argument("--record-id", default=None, help="Explicit record ID. If omitted for 'all', uses --record-id-path from list only when explicitly allowed.")
    ap.add_argument(
        "--allow-listed-record-id",
        action="store_true",
        help="Allow 'all' to reuse a record ID discovered from the list response instead of requiring explicit --record-id.",
    )
    ap.add_argument("--update-url", default=None, help="Update endpoint URL or template. Defaults to DINGTALK_SPIKE_UPDATE_URL.")
    ap.add_argument("--update-method", default="POST", help="HTTP method for the update step.")
    ap.add_argument("--update-body-json", default=None, help="Optional JSON or @file body template for the update step.")
    ap.add_argument("--update-query-json", default=None, help="Optional JSON or @file query params for the update step.")
    ap.add_argument("--update-headers-json", default=None, help="Optional JSON or @file headers for the update step.")
    ap.add_argument(
        "--update-fields-json",
        default=None,
        help="Convenience JSON or @file object of fields for the update step when --update-body-json is not provided.",
    )
    ap.add_argument(
        "--update-set",
        action="append",
        default=[],
        help="Convenience field override using KEY=VALUE. VALUE may be JSON such as true, 1, or \"text\".",
    )
    ap.add_argument(
        "--update-record-id-key",
        default="record_id",
        help="When using convenience update mode, body key that receives the record ID. Use an empty string to omit it.",
    )
    ap.add_argument(
        "--update-fields-key",
        default="fields",
        help="When using convenience update mode, body key that receives the updated fields. Use an empty string to merge into the body root.",
    )

    ap.add_argument("--upload-url", default=None, help="Upload endpoint URL or template. Defaults to DINGTALK_SPIKE_UPLOAD_URL.")
    ap.add_argument("--upload-method", default="POST", help="HTTP method for the upload step.")
    ap.add_argument("--upload-body-json", default=None, help="Optional JSON or @file body for non-multipart upload APIs.")
    ap.add_argument("--upload-query-json", default=None, help="Optional JSON or @file query params for the upload step.")
    ap.add_argument("--upload-headers-json", default=None, help="Optional JSON or @file headers for the upload step.")
    ap.add_argument("--upload-file", default=None, help="Local file path for the upload step.")
    ap.add_argument(
        "--upload-form-fields-json",
        default=None,
        help="Optional JSON or @file extra multipart form fields used when --upload-body-json is omitted.",
    )
    ap.add_argument("--upload-file-field", default="file", help="Multipart field name for the uploaded file.")
    ap.add_argument(
        "--upload-filename-field",
        default=None,
        help="Optional multipart field name that should separately receive the file name.",
    )
    ap.add_argument(
        "--upload-file-id-path",
        default=None,
        help="Optional JSON path to the uploaded file ID in the upload response.",
    )
    ap.add_argument(
        "--upload-share-url-path",
        default=None,
        help="Optional JSON path to a share URL in the upload response.",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    access_token, _token_payload = resolve_access_token(args)
    resolved_record_id = args.record_id

    if args.action in ("list", "all"):
        _list_payload, listed_record_id = run_list_step(args, access_token=access_token)
        if not resolved_record_id:
            resolved_record_id = listed_record_id

    if args.action in ("update", "all"):
        if args.action == "all" and not args.record_id and not args.allow_listed_record_id:
            raise RuntimeError(
                "'all' requires explicit --record-id by default. "
                "Use --allow-listed-record-id only when your list call is uniquely filtered to one safe row."
            )
        record_id = require_text(resolved_record_id, flag_name="--record-id or --record-id-path")
        run_update_step(args, access_token=access_token, record_id=record_id)

    if args.action in ("upload", "all"):
        run_upload_step(args, access_token=access_token)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
