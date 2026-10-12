"""Frozen workspace data: complete reads, atomic writes and content identities."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from tools.utils.path_utils import PathSegments

NAMES = {"deliverables": "deliverables_snapshot.json", "corpus": "system_workspace_corpus.json"}


def data_dir(root: Path) -> Path:
    return root / PathSegments.DOCS / PathSegments.KNOWLEDGE / PathSegments.WORKSPACE_DATA


def snapshot_path(assets: Path, name: str) -> Path:
    """Business-owned frozen data overrides the migration baseline, even if malformed."""
    root = assets.parent.parent
    candidate = data_dir(root) / name
    return candidate if candidate.exists() else assets / name


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def content_digest(snapshot: dict) -> str:
    return digest({key: value for key, value in snapshot.items()
                   if key not in {"exported_at", "refresh", "history"}})


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Reopen the candidate before replacing the last good file.
        if json.loads(Path(temporary).read_text(encoding="utf-8")) != value:
            raise ValueError("candidate readback mismatch")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _page(payload, header):
    if not isinstance(payload, dict) or (payload.get("code", 0) not in (0, "0") or payload.get("ok") is False):
        raise RuntimeError("source read failed")
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("fields"), list):
        raise RuntimeError("source response missing field schema")
    names = [_field_name(v) for v in data["fields"]]
    if not names or len(set(names)) != len(names) or not all(names):
        raise RuntimeError("source field schema invalid")
    if header and names != header:
        raise RuntimeError("source field schema changed during pagination")
    page, ids = data.get("data"), data.get("record_id_list")
    if not isinstance(page, list) or not isinstance(ids, list):
        raise RuntimeError("source page missing rows or record identities")
    if len(page) != len(ids) or len(page) > 200:
        raise RuntimeError("source page missing rows or record identities")
    return data, names, page, ids


def _field_name(value):
    return str(value.get("field_name") or value.get("name") or "") if isinstance(value, dict) else str(value)


def _append_rows(rows, seen, names, page, ids):
    for identity, row in zip(ids, page, strict=True):
        if not isinstance(identity, str) or not identity or identity in seen:
            raise RuntimeError("source repeated or missing record identity")
        if not isinstance(row, list) or len(row) > len(names):
            raise RuntimeError("source malformed row")
        seen.add(identity)
        rows.append((identity, dict(zip(names, row, strict=False))))


def _last_page(data, count, offset):
    total, more = data.get("total"), data.get("has_more")
    if total is not None and (type(total) is not int or total < offset):
        raise RuntimeError("source total inconsistent")
    if more is not None and type(more) is not bool:
        raise RuntimeError("source pagination marker invalid")
    last = count < 200 or more is False
    if last and (more or (total is not None and offset != total)):
        raise RuntimeError("source pagination incomplete")
    return last


def complete_rows(run, base_token: str, table_id: str) -> tuple[list[str], list[tuple[str, dict]]]:
    """Read the documented offset-paged CLI grid, rejecting partial/malformed pages."""
    rows: list[tuple[str, dict]] = []
    header: list[str] = []
    seen: set[str] = set()
    offset, initial_total, initial_revision = 0, None, None
    while True:
        payload = run(["base", "+record-list", "--base-token", base_token, "--table-id", table_id,
                       "--format", "json", "--limit", "200", "--offset", str(offset)])
        data, header, page, ids = _page(payload, header)
        if initial_total is not None and data.get("total") != initial_total:
            raise RuntimeError("source total changed during pagination")
        if initial_revision is not None and data.get("rev") != initial_revision:
            raise RuntimeError("source revision changed during pagination")
        initial_total, initial_revision = data.get("total"), data.get("rev")
        _append_rows(rows, seen, header, page, ids)
        offset += len(page)
        if _last_page(data, len(page), offset):
            return header, rows
        if offset > 1_000_000:
            raise RuntimeError("source pagination safety bound exceeded")


def _delivery_losses(candidate: dict, previous: dict) -> list[str]:
    from tools.rtd.deliverables import version_key

    def slots(snapshot):
        return {(row["key"], row["lang"], fmt): value for row in snapshot["documents"]
                for fmt, value in row["formats"].items()}
    before, after = slots(previous), slots(candidate)
    missing = before.keys() - after.keys()
    regressed = [key for key in before.keys() & after.keys()
                 if version_key(after[key]["version"]) < version_key(before[key]["version"])]
    problems = []
    if missing:
        problems.append(f"candidate drops {len(missing)} existing delivery identities; review source before retry")
    if regressed:
        problems.append(f"candidate regresses {len(regressed)} delivery versions; review source before retry")
    return problems


def loss_problems(candidate: dict, previous: dict | None) -> list[str]:
    if not previous:
        return []
    if "documents" in candidate:
        return _delivery_losses(candidate, previous)
    problems = []
    for kind in ("sentence_pairs", "terms"):
        before, after = previous[kind]["total"], candidate[kind]["total"]
        if after < before:
            problems.append(f"{kind} decreased from {before} to {after}; review source before retry")
        for lang, count in previous[kind]["by_language"].items():
            if candidate[kind]["by_language"].get(lang, 0) < count:
                problems.append(f"{kind} language coverage decreased: {lang}")
    return problems


def save_snapshot(path: Path, candidate: dict, *, previous: dict | None, validate,
                  source: dict, execution: str = "") -> dict:
    problems = validate(candidate) + loss_problems(candidate, previous)
    if previous and previous.get("refresh", {}).get("source") not in (None, source):
        problems.append("source identity differs from last valid snapshot")
    if problems:
        raise ValueError("; ".join(problems))
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    identity = content_digest(candidate)
    changed = previous is None or content_digest(previous) != identity
    result = {"status": "changed" if changed else "unchanged", "checked_at": now,
              "content_sha256": identity, "source": source, "execution": execution}
    if changed:
        candidate = {**candidate, "refresh": result}
        atomic_json(path, candidate)
    return result
