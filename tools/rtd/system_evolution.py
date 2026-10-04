"""Read the public evolution story and ongoing work from the architecture history."""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urlsplit

import yaml

START = "<!-- system-evolution:start -->"
END = "<!-- system-evolution:end -->"
SCHEMA = "system-evolution/v1"
STATUS_LABELS = {"recorded": "已完成", "ongoing": "持续开展",
                 "in_progress": "建设中", "planned": "未来方向"}


class EvolutionError(ValueError):
    """The single-source story cannot be safely displayed."""


def _text(row: dict, field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvolutionError(f"{field} must be non-empty text")
    return value


def _texts(row: dict, field: str) -> list[str]:
    values = row.get(field)
    if not isinstance(values, list) or len(values) < 2:
        raise EvolutionError(f"{field} needs at least two text steps")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise EvolutionError(f"{field} must contain non-empty text")
    return values


def _file_ref(ref: str) -> tuple[str, str]:
    if not isinstance(ref, str):
        raise EvolutionError("history authority must be a file reference")
    kind, repo, path = ref.split(":", 2)
    parts = urlsplit(path)
    if (kind != "file" or not path or parts.scheme or parts.netloc or parts.query or parts.fragment
            or path.startswith("/") or ".." in PurePosixPath(path).parts or "\\" in path):
        raise EvolutionError("file evidence must be a relative repository path")
    return repo, path


def _evidence(ref: object, repositories: dict[str, str]) -> dict[str, str]:
    if not isinstance(ref, str):
        raise EvolutionError("evidence must be a file: or pr: reference")
    if match := re.fullmatch(r"pr:([a-z-]+)#([1-9][0-9]*)", ref):
        repo, number = match.groups()
        path, label = f"pull/{number}", f"#{number}"
    else:
        try:
            repo, relative = _file_ref(ref)
        except ValueError as exc:
            raise EvolutionError("evidence must be a file: or pr: reference") from exc
        path, label = f"blob/main/{quote(relative, safe='/')}", PurePosixPath(relative).name
    if repo not in repositories:
        raise EvolutionError(f"unknown evidence repository: {repo}")
    return {"href": f"{repositories[repo].rstrip('/')}/{path}", "label": label, "title": ref}


def _stage(row: object, repositories: dict[str, str]) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise EvolutionError("stage must be a mapping")
    stage = {key: _text(row, key) for key in
             ("id", "period", "status", "title", "metaphor", "summary", "detail", "invariant")}
    if not re.fullmatch(r"[a-z][a-z0-9_]*", stage["id"]):
        raise EvolutionError("stage id must be lower_snake_case")
    if stage["status"] not in STATUS_LABELS:
        raise EvolutionError(f"unknown stage status: {stage['status']}")
    refs = row.get("evidence")
    if not isinstance(refs, list) or not refs:
        raise EvolutionError("every stage needs evidence")
    span = _span(row)
    return {**stage, "status_label": STATUS_LABELS[stage["status"]], "flow": _texts(row, "flow"),
            "evidence": [_evidence(ref, repositories) for ref in refs], **span}


_MONTH = re.compile(r"(20[0-9]{2})-(0[1-9]|1[0-2])")


def _month(value: object, field: str) -> int:
    if not isinstance(value, str) or not _MONTH.fullmatch(value):
        raise EvolutionError(f"{field} must be YYYY-MM")
    year, month = map(int, value.split("-"))
    return year * 12 + month - 1


def _span(row: dict) -> dict:
    """Optional month range for the overview chart; open end means still running."""
    if "start" not in row:
        return {}
    start = _month(row["start"], "start")
    end = _month(row["end"], "end") if row.get("end") is not None else None
    if end is not None and end < start:
        raise EvolutionError("end must not precede start")
    return {"start": start, "end": end}


def _chapters(rows: object, stages: list[dict]) -> list[dict]:
    """Group stages by the question each answered; every stage belongs to exactly one chapter."""
    if rows is None:
        return []
    if not isinstance(rows, list) or not rows:
        raise EvolutionError("chapters must be a non-empty list")
    by_id = {stage["id"]: stage for stage in stages}
    chapters, seen = [], []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("stages"), list) or not row["stages"]:
            raise EvolutionError("chapter needs stages")
        if any(stage_id not in by_id for stage_id in row["stages"]):
            raise EvolutionError("chapter names an unknown stage")
        seen += row["stages"]
        chapters.append({"title": _text(row, "title"), "question": _text(row, "question"),
                         "stages": [by_id[stage_id] for stage_id in row["stages"]]})
    if sorted(seen) != sorted(by_id):
        raise EvolutionError("chapters must place every stage exactly once")
    return chapters


def _now(rows: object) -> list[dict]:
    """Optional one-line state per delivery chain, shown before the history."""
    if not isinstance(rows, list):
        raise EvolutionError("now must be a list")
    now = [{"label": _text(row, "label"), "state": _text(row, "state"), "status": _text(row, "status")}
           for row in rows]
    if any(row["status"] not in STATUS_LABELS for row in now):
        raise EvolutionError("unknown now status")
    return now


def _timeline(entries: list[dict], updated: dt.date) -> dict | None:
    """Month axis shared by every bar; positions are percentages of one scale."""
    spans = [entry for entry in entries if "start" in entry]
    if not spans:
        return None
    today = updated.year * 12 + updated.month - 1
    first = min(entry["start"] for entry in spans)
    last = max([today + 2] + [entry["end"] or entry["start"] for entry in spans]) + 1
    width = last - first

    def pct(month: int) -> float:
        return round((month - first) * 100 / width, 3)

    for entry in spans:
        end = entry["end"] if entry["end"] is not None else max(today, entry["start"])
        entry["bar"] = {"left": pct(entry["start"]), "width": max(pct(end + 1) - pct(entry["start"]), 1.5),
                        "open": entry["end"] is None}
    ticks = [{"left": pct(month), "label": f"{month % 12 + 1} 月" if month % 12 else f"{month // 12} 年"}
             for month in range(first, last) if month != today]
    return {"ticks": ticks, "today": pct(today) + round(100 / width * (updated.day - 1) / 31, 3),
            "today_label": updated.isoformat()}


def _story(text: str, repositories: dict[str, str]) -> dict[str, Any]:
    if text.count(START) != 1 or text.count(END) != 1:
        raise EvolutionError("history needs exactly one marked summary")
    if text.index(START) > text.index(END):
        raise EvolutionError("summary markers are out of order")
    block = text.split(START, 1)[1].split(END, 1)[0].strip()
    if not block.startswith("```yaml\n") or not block.endswith("\n```"):
        raise EvolutionError("summary must be a YAML fence")
    data = yaml.safe_load(block[len("```yaml\n"):-len("\n```")])
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise EvolutionError(f"summary schema must be {SCHEMA}")
    updated = data.get("updated_on")
    if type(updated) is not dt.date or f"Updated: {updated.isoformat()}" not in text:
        raise EvolutionError("summary date must match the history Updated date")
    rows = data.get("stages")
    if not isinstance(rows, list) or not rows:
        raise EvolutionError("summary needs stages")
    stages = [_stage(row, repositories) for row in rows]
    crosscutting_rows = data.get("crosscutting", [])
    if not isinstance(crosscutting_rows, list):
        raise EvolutionError("crosscutting must be a list")
    crosscutting = [_stage(row, repositories) for row in crosscutting_rows]
    entries = stages + crosscutting
    if len({entry["id"] for entry in entries}) != len(entries):
        raise EvolutionError("duplicate stage or crosscutting id")
    chapters = _chapters(data.get("chapters"), stages)
    timeline = _timeline(entries, updated)
    now = _now(data.get("now", []))
    feedback = data.get("feedback")
    if not isinstance(feedback, dict):
        raise EvolutionError("summary needs a feedback direction")
    return {"title": _text(data, "title"), "intro": _text(data, "intro"),
            "updated_on": updated.isoformat(), "stages": stages, "crosscutting": crosscutting,
            "chapters": chapters, "timeline": timeline, "now": now,
            "feedback": {"title": _text(feedback, "title"), "note": _text(feedback, "note"),
                         "steps": _texts(feedback, "steps")}}


def evolution_view(*, root: Path, domain: dict | None,
                   repositories: dict[str, str]) -> dict[str, Any] | None:
    """Optional domain; bad/missing input yields an explicit fallback, never invented history."""
    if domain is None:
        return None
    fallback = {"problem": domain["fallback"], "problems": [], "stages": []}
    try:
        repo, relative = _file_ref(domain["authority"])
        if repo != "auto-manual":
            raise EvolutionError("history authority must be on the engineering plane")
        source = (root / relative).resolve()
        if not source.is_relative_to(root.resolve()):
            raise EvolutionError("history authority escapes the checkout")
        story = _story(source.read_text(encoding="utf-8"), repositories)
        return {**story, "source": _evidence(domain["authority"], repositories), "problems": []}
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        return {**fallback, "problems": [str(exc)]}
