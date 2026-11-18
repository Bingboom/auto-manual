"""Scrub credentials and opaque identifiers out of text bound for a log.

Error text from ``lark-cli`` and the Feishu API can carry base tokens, table /
view / record ids, request ids, log ids and troubleshooting URLs. The cred
health check publishes its probe detail in the job summary of a public
repository, so anything that reaches it goes through :func:`redact_identifiers`
first. The rules are deliberately broad: losing a harmless word is cheaper than
publishing an identifier.
"""

from __future__ import annotations

import re
from typing import Iterable

REDACTED = "<redacted>"

_URL = re.compile(r"(?:https?|wss?|ftp)://\S+|www\.\S+", re.IGNORECASE)
_USERINFO = re.compile(r"\S+:\S+@\S+")
_KEY_VALUE = re.compile(
    r"(?i)\b([a-z_]*(?:token|secret|password|passwd|authorization|cookie|ticket|signature|key))"
    r"[\"']?\s*[=:]\s*"
    r"(?!<redacted>)[\"']?[^\s\"',;&]+"
)
_BEARER = re.compile(r"(?i)\b(bearer|basic)\s+[^\s\"',;]+")
# Feishu object ids: tbl…, vew…, rec…, fld…, plus app/user/chat ids.
_FEISHU_ID = re.compile(r"\b(?:tbl|vew|rec|fld|cli_|ou_|on_|oc_|bas)(?=[A-Za-z0-9_]*[A-Z0-9])[A-Za-z0-9_]{5,}\b")
# Long opaque tokens: 16+ id characters mixing letters and digits.
_OPAQUE = re.compile(r"\b(?=[A-Za-z0-9_\-]*[A-Za-z])(?=[A-Za-z0-9_\-]*\d)[A-Za-z0-9_\-]{16,}\b")
# Environment-variable names (FEISHU_PHASE2_BASE_TOKEN) are diagnostics, not secrets.
_ENV_NAME = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+")
_MIN_KNOWN_LENGTH = 4


def _redact_opaque(match: re.Match[str]) -> str:
    return match.group(0) if _ENV_NAME.fullmatch(match.group(0)) else REDACTED


def redact_identifiers(text: str, known: Iterable[str] = ()) -> str:
    """Return ``text`` with known secret values and identifier-shaped runs replaced."""
    result = text or ""
    for value in sorted({str(item) for item in known if item}, key=len, reverse=True):
        if len(value) >= _MIN_KNOWN_LENGTH:
            result = result.replace(value, REDACTED)
    result = _URL.sub(REDACTED, result)
    result = _USERINFO.sub(REDACTED, result)
    result = _KEY_VALUE.sub(lambda match: f"{match.group(1)}={REDACTED}", result)
    result = _BEARER.sub(lambda match: f"{match.group(1)} {REDACTED}", result)
    result = _FEISHU_ID.sub(REDACTED, result)
    return _OPAQUE.sub(_redact_opaque, result)


__all__ = ("REDACTED", "redact_identifiers")
