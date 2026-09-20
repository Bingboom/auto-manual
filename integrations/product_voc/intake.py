"""Append-only bot adapter with durable replay protection; no general agent tools."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import threading
import time
from pathlib import Path

FIELDS = {"suggestion": "Your suggestion", "model": "Product model",
          "use_case": "Use case", "context": "Manual context"}
LIMITS = {"suggestion": (5, 3000), "model": (1, 100),
          "use_case": (0, 1000), "context": (0, 1500), "website": (0, 0)}
REQUEST_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


class IntakeError(Exception):
    def __init__(self, status: int, code: str):
        self.status, self.code = status, code
        super().__init__(code)


def validate(payload: object) -> tuple[str, dict[str, str]]:
    if not isinstance(payload, dict) or set(payload) != {*LIMITS, "request_id"}:
        raise IntakeError(400, "invalid_fields")
    request_id = payload["request_id"]
    if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
        raise IntakeError(400, "invalid_reference")
    for name, (minimum, maximum) in LIMITS.items():
        value = payload[name]
        if (not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum
                or len(value) > maximum or any(ord(c) < 32 and c not in "\n\t" for c in value)):
            raise IntakeError(400, "invalid_fields")
    # Context is visitor-supplied evidence, not authority to operate on a document.
    fields = {label: payload[key].strip() for key, label in FIELDS.items()}
    fields["Manual context"] += f"\nSubmission: {request_id}"
    return request_id, fields


class BotWriter:
    def __init__(self, *, base: str, table: str, profile: str = "prod"):
        if not re.fullmatch(r"[A-Za-z0-9]+", base) or not re.fullmatch(r"tbl[A-Za-z0-9]+", table):
            raise ValueError("Explicit VOC base and table IDs are required")
        self.args = ["lark-cli", "--profile", profile, "base"]
        self.target = ["--as", "bot", "--base-token", base, "--table-id", table, "--format", "json"]

    def call(self, action: str, *args: str) -> dict:
        result = subprocess.run(
            [*self.args, action, *self.target, *args],
            env={**os.environ, "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
                 "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1"},
            capture_output=True, text=True, timeout=15, check=False,
        )
        if result.returncode:
            raise RuntimeError("Feishu request failed")  # Never return raw CLI output/secrets.
        envelope = json.loads(result.stdout)
        if envelope.get("ok") is not True or envelope.get("identity") != "bot":
            raise RuntimeError("Unverified bot response")
        return envelope["data"]

    def preflight(self) -> None:
        live = self.call("+field-list", "--limit", "200")["fields"]
        actual = {field["name"]: field for field in live}
        if any(actual.get(name, {}).get("type") != "text" for name in FIELDS.values()):
            raise RuntimeError("VOC schema does not match text fields")

    def create(self, fields: dict[str, str]) -> str:
        data = self.call("+record-upsert", "--json", json.dumps(fields, ensure_ascii=False))
        record = data.get("record", {})
        record_id = record.get("record_id") or record.get("id")
        if not isinstance(record_id, str) or not re.fullmatch(r"rec[A-Za-z0-9]+", record_id):
            raise RuntimeError("Missing created record ID")
        return record_id

    def verify(self, record_id: str, fields: dict[str, str]) -> None:
        data = self.call("+record-get", "--record-id", record_id)
        if data.get("record_id_list") != [record_id] or len(data.get("data", [])) != 1:
            raise RuntimeError("Record readback missing")
        actual = dict(zip(data["fields"], data["data"][0]))
        if any((actual.get(name) or "") != value for name, value in fields.items()):
            raise RuntimeError("Record readback mismatch")


class Intake:
    def __init__(self, state: Path, writer: BotWriter):
        state.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(state, check_same_thread=False)
        os.chmod(state, 0o600)
        self.db.execute("CREATE TABLE IF NOT EXISTS submissions (id TEXT PRIMARY KEY, digest TEXT, record_id TEXT, verified INTEGER)")
        self.db.commit()
        self.writer = writer
        self.lock = threading.Lock()
        self.attempts: dict[str, list[float]] = {}

    def rate_limit(self, peer: str) -> None:
        now = time.monotonic()
        self.attempts = {key: [t for t in times if t > now - 600]
                         for key, times in self.attempts.items() if times and times[-1] > now - 600}
        # Store only a short-lived hash in RAM. No address, UA or cookies go to Feishu.
        key = hashlib.sha256(peer.encode()).hexdigest()
        own = self.attempts.setdefault(key, [])
        total = sum(len(times) for times in self.attempts.values())
        if len(own) >= 5 or total >= 100:
            raise IntakeError(429, "rate_limited")
        own.append(now)

    def submit(self, payload: object, peer: str) -> dict:
        if not self.lock.acquire(blocking=False):
            raise IntakeError(429, "busy")
        try:
            self.rate_limit(peer)
            request_id, fields = validate(payload)
            digest = hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()
            prior = self.db.execute("SELECT digest, record_id, verified FROM submissions WHERE id=?", (request_id,)).fetchone()
            if prior and prior[0] != digest:
                raise IntakeError(409, "reference_conflict")
            if prior and prior[2]:
                return {"ok": True, "reference": request_id}
            if prior and not prior[1]:
                # A timeout/crash might have written the record; never blindly create twice.
                raise IntakeError(409, "needs_verification")
            if not prior:
                self.db.execute("INSERT INTO submissions VALUES (?, ?, NULL, 0)", (request_id, digest))
                self.db.commit()
            try:
                record_id = prior[1] if prior else self.writer.create(fields)
                self.db.execute("UPDATE submissions SET record_id=? WHERE id=?", (record_id, request_id))
                self.db.commit()
                time.sleep(0.3)  # Feishu's write-readback visibility can lag.
                self.writer.verify(record_id, fields)
            except Exception as exc:
                raise IntakeError(503, "delivery_unconfirmed") from exc
            self.db.execute("UPDATE submissions SET verified=1 WHERE id=?", (request_id,))
            self.db.commit()
            return {"ok": True, "reference": request_id}
        finally:
            self.lock.release()
