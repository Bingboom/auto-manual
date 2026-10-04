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
    return {**stage, "status_label": STATUS_LABELS[stage["status"]], "flow": _texts(row, "flow"),
            "evidence": [_evidence(ref, repositories) for ref in refs]}


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
    feedback = data.get("feedback")
    if not isinstance(feedback, dict):
        raise EvolutionError("summary needs a feedback direction")
    return {"title": _text(data, "title"), "intro": _text(data, "intro"),
            "updated_on": updated.isoformat(), "stages": stages, "crosscutting": crosscutting,
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
