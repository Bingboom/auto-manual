"""lark-cli calls and complete table reads for the intelligence loop.

``runner(cli_bin, identity)`` returns ``run(args) -> payload``: one lark-cli call
with ``--as identity`` after the subcommand, its printed JSON object returned,
rate-limited replies retried with bounded backoff. A failure raises
``LarkError`` naming the exit status and any response code, never the command
line, whose arguments hold base tokens and message bodies.

``complete_rows(run, base_token, table_id)`` reads every page of
``base +record-list`` or raises: a changed schema, a repeated or missing record
ID, or an inconsistent total stops the read instead of returning part of a table.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time
from typing import Any, Callable

PAGE_SIZE = 200
RETRIES = 3
MAX_DELAY = 30.0
_LIMITED = re.compile(r"\b429\b|rate[ -]?limit|too many requests", re.IGNORECASE)


class LarkError(RuntimeError):
    """A lark-cli call failed; the message names no argument of the call."""


def command(cli_bin: str) -> list[str]:
    """``cli_bin`` split as a shell would, its program found on PATH (Windows ``.cmd`` shims included)."""
    parts = shlex.split(cli_bin)
    if not parts:
        raise ValueError("lark-cli command must not be empty")
    program = parts[0] if Path(parts[0]).is_absolute() else shutil.which(parts[0]) or parts[0]
    return [program, *parts[1:]]


def payload_of(text: str) -> dict:
    """The JSON object a lark-cli call printed, ignoring notices before or after it."""
    text = (text or "").strip()
    if not text:
        raise LarkError("lark-cli printed nothing")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        try:
            value = json.loads(text[start:end + 1]) if 0 <= start < end else None
        except json.JSONDecodeError:
            value = None
    if not isinstance(value, dict):
        raise LarkError("lark-cli printed no JSON object")
    return value


def _code(payload: dict | None) -> str | None:
    """The response code of a reply, at the top or under ``error`` as lark-cli 1.x prints it; digits only."""
    if not isinstance(payload, dict):
        return None
    error = payload.get("error")
    for value in (payload.get("code"), error.get("code") if isinstance(error, dict) else None):
        text = "" if value is None or isinstance(value, bool) else str(value).strip()
        if text.lstrip("-").isdigit() and text != "0":
            return text
    return None


def _reply(stdout: str, stderr: str) -> dict | None:
    """The JSON object a failed call printed, if any; lark-cli prints its error object to stderr."""
    for text in (stdout, stderr):
        try:
            return payload_of(text)
        except LarkError:
            continue
    return None


def _limited(payload: dict | None, stdout: str, stderr: str) -> bool:
    if payload and any(str(payload.get(key) or "").strip() == "429"
                       for key in ("code", "status", "status_code", "http_status")):
        return True
    return bool(_LIMITED.search(f"{stdout} {stderr}"))


def _delay(attempt: int, payload: dict | None) -> float:
    try:
        retry_after = float((payload or {}).get("retry_after") or 0)
    except (TypeError, ValueError):
        retry_after = 0.0
    return min(MAX_DELAY, max(2.0 ** attempt, retry_after))


def runner(cli_bin: str, identity: str, *, execute=subprocess.run,
           sleep: Callable[[float], None] = time.sleep) -> Callable[[list[str]], dict]:
    """``run(args) -> payload`` over lark-cli as ``identity``; ``execute`` stands in for subprocess in tests."""
    program = command(cli_bin)

    def run(args: list[str]) -> dict:
        call = [*program, *args[:2], *(["--as", identity] if identity else []), *args[2:]]
        for attempt in range(RETRIES + 1):
            done = execute(call, capture_output=True, text=True, encoding="utf-8", check=False)
            stdout, stderr = done.stdout or "", done.stderr or ""
            payload = None
            if done.returncode == 0:
                try:
                    payload = payload_of(stdout or stderr)
                except LarkError:
                    if not _limited(None, stdout, stderr):
                        raise
            if _limited(payload, stdout, stderr) and attempt < RETRIES:
                sleep(_delay(attempt, payload))
                continue
            if done.returncode or payload is None:
                code = _code(_reply(stdout, stderr))
                raise LarkError(f"lark-cli exited with status {done.returncode}"
                                + (f", response code {code}" if code else ""))
            if payload.get("code") not in (None, 0, "0") or payload.get("ok") is False:
                raise LarkError(f"lark-cli request failed with code {_code(payload)}")
            return payload
        raise LarkError("lark-cli stayed rate-limited")

    return run


def _field_name(value: Any) -> str:
    return str(value.get("field_name") or value.get("name") or "") if isinstance(value, dict) else str(value)


def _page(payload: Any, header: list[str]) -> tuple[dict, list[str], list, list]:
    if not isinstance(payload, dict) or payload.get("code", 0) not in (0, "0") or payload.get("ok") is False:
        raise LarkError("table read failed")
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("fields"), list):
        raise LarkError("table response has no field schema")
    names = [_field_name(value) for value in data["fields"]]
    if not names or len(set(names)) != len(names) or not all(names):
        raise LarkError("table field schema is invalid")
    if header and names != header:
        raise LarkError("table field schema changed during pagination")
    page, ids = data.get("data"), data.get("record_id_list")
    if not isinstance(page, list) or not isinstance(ids, list) or len(page) != len(ids) or len(page) > PAGE_SIZE:
        raise LarkError("table page is missing rows or record ids")
    return data, names, page, ids


def _append(rows: list, seen: set[str], names: list[str], page: list, ids: list) -> None:
    for identity, row in zip(ids, page, strict=True):
        if not isinstance(identity, str) or not identity or identity in seen:
            raise LarkError("table repeated or omitted a record id")
        if not isinstance(row, list) or len(row) > len(names):
            raise LarkError("table returned a malformed row")
        seen.add(identity)
        rows.append((identity, dict(zip(names, row, strict=False))))


def _last(data: dict, count: int, offset: int) -> bool:
    total, more = data.get("total"), data.get("has_more")
    if total is not None and (type(total) is not int or total < offset):
        raise LarkError("table total is inconsistent")
    if more is not None and type(more) is not bool:
        raise LarkError("table pagination marker is invalid")
    last = count < PAGE_SIZE or more is False
    if last and (more or (total is not None and offset != total)):
        raise LarkError("table pagination is incomplete")
    return last


def complete_rows(run, base_token: str, table_id: str) -> tuple[list[str], list[tuple[str, dict]]]:
    """``(columns, [(record id, {column: cell})])`` for every row, or LarkError."""
    rows: list[tuple[str, dict]] = []
    header: list[str] = []
    seen: set[str] = set()
    offset, total, revision = 0, None, None
    while True:
        payload = run(["base", "+record-list", "--base-token", base_token, "--table-id", table_id,
                       "--format", "json", "--limit", str(PAGE_SIZE), "--offset", str(offset)])
        data, header, page, ids = _page(payload, header)
        if (total is not None and data.get("total") != total) or (revision is not None and data.get("rev") != revision):
            raise LarkError("table changed during pagination")
        total, revision = data.get("total"), data.get("rev")
        _append(rows, seen, header, page, ids)
        offset += len(page)
        if _last(data, len(page), offset):
            return header, rows
        if offset > 1_000_000:
            raise LarkError("table pagination safety bound exceeded")
