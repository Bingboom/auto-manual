from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import Any
from urllib import error, request

from .contracts import DingTalkAccessToken


DEFAULT_TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/{corp_id}/token"


def _required_env(name: str) -> str:
    value = str(os.environ.get(name, "")).strip()
    if not value:
        raise RuntimeError(f"Required DingTalk environment variable is not set: {name}")
    return value


def _http_json_request(*, method: str, url: str, json_body: dict[str, Any], timeout_seconds: float = 30.0) -> dict[str, Any]:
    payload = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url=url,
        method=method.upper(),
        data=payload,
        headers={"Content-Type": "application/json"},
    )
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
            "DingTalk token request failed: "
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
            "DingTalk token request failed: "
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
        raise RuntimeError(f"DingTalk token response is not valid JSON: {raw}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("DingTalk token response is not a JSON object")
    return parsed


def _curl_binary() -> str | None:
    return shutil.which("curl.exe") or shutil.which("curl")


def _curl_json_request(*, method: str, url: str, json_body: dict[str, Any], timeout_seconds: float = 30.0) -> dict[str, Any]:
    curl_bin = _curl_binary()
    if not curl_bin:
        raise RuntimeError("curl is not available on PATH")
    payload = json.dumps(json_body, ensure_ascii=False)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", suffix=".json", delete=False) as payload_file:
        payload_file.write(payload)
        payload_path = payload_file.name
    with tempfile.NamedTemporaryFile("w+b", suffix=".json", delete=False) as body_file:
        body_path = body_file.name
    try:
        proc = subprocess.run(
            [
                curl_bin,
                "-sS",
                "-o",
                body_path,
                "-w",
                "%{http_code}",
                "-X",
                method.upper(),
                url,
                "-H",
                "Content-Type: application/json",
                "--data-binary",
                "@" + payload_path,
                "--max-time",
                str(int(timeout_seconds)),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if proc.returncode:
            raise RuntimeError(
                "DingTalk token request failed: "
                + json.dumps(
                    {
                        "url": url,
                        "reason": (proc.stderr or proc.stdout or "").strip(),
                        "transport_error": "curl",
                    },
                    ensure_ascii=False,
                )
            )
        status_text = str(proc.stdout or "").strip()
        try:
            status = int(status_text)
        except ValueError as exc:
            raise RuntimeError(f"DingTalk token request returned an invalid curl status: {status_text}") from exc
        raw = open(body_path, "r", encoding="utf-8", errors="replace").read()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"DingTalk token response is not valid JSON: {raw}") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("DingTalk token response is not a JSON object")
        if status >= 400:
            raise RuntimeError(
                "DingTalk token request failed: "
                + json.dumps(
                    {
                        "status": status,
                        "url": url,
                        "response": parsed,
                    },
                    ensure_ascii=False,
                )
            )
        return parsed
    finally:
        for temp_path in (payload_path, body_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def request_app_only_token_response(
    *,
    client_id: str,
    client_secret: str,
    corp_id: str,
    token_url_template: str = DEFAULT_TOKEN_URL,
) -> dict[str, Any]:
    token_url = token_url_template.format(corp_id=corp_id)
    request_body = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    if token_url_template == DEFAULT_TOKEN_URL and _curl_binary():
        return _curl_json_request(method="POST", url=token_url, json_body=request_body)
    return _http_json_request(method="POST", url=token_url, json_body=request_body)


def get_app_only_token(*, client_id_env: str, client_secret_env: str, corp_id_env: str | None = None) -> DingTalkAccessToken:
    client_id = _required_env(client_id_env)
    client_secret = _required_env(client_secret_env)
    corp_id = _required_env(corp_id_env or "DINGTALK_CORP_ID")
    token_url_template = str(os.environ.get("DINGTALK_TOKEN_URL", DEFAULT_TOKEN_URL)).strip() or DEFAULT_TOKEN_URL
    response = request_app_only_token_response(
        client_id=client_id,
        client_secret=client_secret,
        corp_id=corp_id,
        token_url_template=token_url_template,
    )
    access_token = str(response.get("access_token") or "").strip()
    if not access_token:
        raise RuntimeError("DingTalk token response is missing access_token")
    expires_in_raw = response.get("expires_in", 0)
    try:
        expires_in_seconds = int(expires_in_raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"DingTalk token response has invalid expires_in: {expires_in_raw}") from exc
    return DingTalkAccessToken(access_token=access_token, expires_in_seconds=expires_in_seconds)
