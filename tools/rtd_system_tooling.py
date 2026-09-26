#!/usr/bin/env python3
"""Skills and hooks inventory for the system workspace page, read from the tree at build time.

Nothing here is hand-listed. Skills come from ``.agents/skills/*/SKILL.md``
(Codex) and ``.claude/skills/*/SKILL.md`` (Claude Code), merged by directory
name. Each copy must be registered where its agent looks it up: Codex skills
in ``AGENTS.md``, Claude skills in ``.claude/skills/README.md``. Hooks come
from ``.claude/settings.json`` and the steps of ``.githooks/pre-push``; a hook
counts as tested when ``tests/test_<script>.py`` exists. The contract only maps
skills to focus lanes (``tooling.skill_lanes``).
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import yaml

from tools.utils.path_utils import (
    PathSegments,
    claude_settings_of,
    claude_skills_of,
    codex_skills_of,
    githooks_of,
)

REGISTRIES = {"Codex": PathSegments.AGENTS_MD, "Claude": ".claude/skills/README.md"}
_SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CLAUDE_HOOK = re.compile(r"\.claude/hooks/([\w.-]+\.py)")
_PRE_PUSH_STEP = re.compile(r'^\s*(?P<exec>exec\s+)?"\$\{python_cmd\}"\s+"\$\{repo_root\}/(?P<script>[\w./-]+\.py)"')
_SENTENCE_END = re.compile(r"\.(?=\s|$)|。")
_ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "vs.", "cf.")


def _first_sentence(text: str) -> str:
    """Up to the first full stop that is not part of an abbreviation such as ``e.g.``."""
    for match in _SENTENCE_END.finditer(text):
        head = text[:match.end()]
        if not head.lower().endswith(_ABBREVIATIONS):
            return head.strip()
    return text.strip()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _purpose(script: Path) -> str:
    """First line of the script's module docstring; empty when it has none."""
    try:
        doc = ast.get_docstring(ast.parse(_read(script))) or ""
    except SyntaxError:
        return ""
    return doc.strip().splitlines()[0] if doc.strip() else ""


def skill_facts(root: Path) -> list[dict[str, Any]]:
    """One entry per skill directory name, merging its Codex and Claude copies."""
    registry = {"Codex": _read(root / PathSegments.AGENTS_MD),
                "Claude": _read(claude_skills_of(root) / PathSegments.README_MD)}
    skills: dict[str, dict[str, Any]] = {}
    for agent, base in (("Codex", codex_skills_of(root)), ("Claude", claude_skills_of(root))):
        for path in sorted(base.glob(f"*/{PathSegments.SKILL_MD}")):
            cell = path.parent.name
            meta = _frontmatter(_read(path))
            entry = skills.setdefault(cell, {"id": cell, "description": "", "agents": [],
                                             "unregistered": [], "problems": []})
            entry["agents"].append(agent)
            description = str(meta.get("description") or "").strip()
            entry["description"] = entry["description"] or description
            # Codex discovers skills by frontmatter name; Claude Code uses the directory
            # name, so a Claude copy may omit name but must not contradict it.
            name = meta.get("name")
            if (agent == "Codex" and name != cell) or (agent == "Claude" and name not in (None, cell)):
                entry["problems"].append(f"{agent} copy needs frontmatter name {cell!r}")
            if not description:
                entry["problems"].append(f"{agent} copy has no frontmatter description")
            if not _SKILL_NAME.fullmatch(cell) and "not lowercase hyphen-case" not in " ".join(entry["problems"]):
                entry["problems"].append("skill name is not lowercase hyphen-case")
            listed = (path.relative_to(root).as_posix() if agent == "Codex" else f"`{cell}`") in registry[agent]
            if not listed:
                entry["unregistered"].append(agent)
    return [skills[name] for name in sorted(skills)]


def hook_facts(root: Path) -> list[dict[str, Any]]:
    """Claude Code hooks from the project settings, then the steps of the git pre-push hook."""
    hooks: list[dict[str, Any]] = []
    try:
        settings = json.loads(_read(claude_settings_of(root)) or "{}")
    except ValueError:
        settings = {}
    configured = settings.get("hooks") if isinstance(settings, dict) else None
    for event, entries in (configured or {}).items():
        for entry in entries if isinstance(entries, list) else []:
            for hook in (entry or {}).get("hooks") or []:
                match = _CLAUDE_HOOK.search(str((hook or {}).get("command") or ""))
                if match:
                    hooks.append({"layer": "Claude Code", "event": str(event),
                                  "matcher": str(entry.get("matcher") or ""), "blocking": False,
                                  "script": f"{PathSegments.CLAUDE_DIR}/{PathSegments.HOOKS}/{match.group(1)}"})
    for line in _read(githooks_of(root) / PathSegments.PRE_PUSH).splitlines():
        match = _PRE_PUSH_STEP.match(line)
        if match:
            hooks.append({"layer": "git", "event": PathSegments.PRE_PUSH, "matcher": "",
                          "blocking": bool(match.group("exec")), "script": match.group("script")})
    for hook in hooks:
        script = root / hook["script"]
        hook["exists"] = script.is_file()
        hook["tested"] = (root / PathSegments.TESTS / f"test_{script.stem}.py").is_file()
        hook["purpose"] = _purpose(script) if hook["exists"] else ""
    return hooks


def tooling_problems(config: object, lane_ids: set[str]) -> list[str]:
    """Authoring errors in the contract's ``tooling`` section."""
    if not isinstance(config, dict):
        return ["tooling must be a mapping"]
    lanes = config.get("skill_lanes", {})
    if not isinstance(lanes, dict):
        return ["tooling.skill_lanes must map focus lane ids to skill lists"]
    problems = [f"tooling.skill_lanes: unknown focus lane {lane!r}" for lane in lanes if lane not in lane_ids]
    for lane, names in lanes.items():
        if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            problems.append(f"tooling.skill_lanes.{lane} must be a list of skill names")
    return problems


def tooling_findings(config: dict[str, Any], skills: list[dict[str, Any]],
                     hooks: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """``(severity, where, message)`` for ``check``: unknown mapped skills are errors, the rest warnings."""
    known = {skill["id"] for skill in skills}
    out: list[tuple[str, str, str]] = []
    for lane, names in (config.get("skill_lanes") or {}).items():
        for name in names:
            if name not in known:
                out.append(("error", f"tooling.skill_lanes.{lane}", f"no skill named {name!r} in the tree"))
    for skill in skills:
        for agent in skill["unregistered"]:
            out.append(("warning", f"skill {skill['id']}", f"{agent} copy is not registered in {REGISTRIES[agent]}"))
        for problem in skill["problems"]:
            out.append(("warning", f"skill {skill['id']}", problem))
    for hook in hooks:
        if not hook["exists"]:
            out.append(("warning", f"hook {hook['script']}", "script is missing"))
        elif not hook["tested"]:
            out.append(("warning", f"hook {hook['script']}", "has no tests/test_<script>.py"))
    return out


def tooling_view(config: dict[str, Any], skills: list[dict[str, Any]], hooks: list[dict[str, Any]],
                 lanes: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Page context: tiles, skills grouped by focus lane (then the rest), and the hook steps."""
    by_id = {skill["id"]: skill for skill in skills}

    def row(skill: dict[str, Any]) -> dict[str, Any]:
        return {"id": skill["id"], "description": skill["description"], "agents": skill["agents"],
                "summary": _first_sentence(skill["description"]),
                "unregistered": skill["unregistered"], "problems": skill["problems"]}

    groups, placed = [], set()
    for lane_id, names in (config.get("skill_lanes") or {}).items():
        lane = lanes.get(lane_id, {})
        placed.update(names)
        groups.append({"title": lane.get("title", lane_id), "horizon": lane.get("horizon", ""),
                       "horizon_label": lane.get("horizon_label", ""),
                       "rows": [row(by_id[name]) for name in names if name in by_id]})
    rest = [row(skill) for skill in skills if skill["id"] not in placed]
    if rest:
        groups.append({"title": "其他技能", "horizon": "", "horizon_label": "", "rows": rest})
    per_agent = {agent: sum(agent in skill["agents"] for skill in skills) for agent in REGISTRIES}
    per_layer: dict[str, int] = {}
    for hook in hooks:
        per_layer[hook["layer"]] = per_layer.get(hook["layer"], 0) + 1
    return {
        "note": str(config.get("note") or ""),
        "tiles": [
            {"label": "技能", "value": str(len(skills)),
             "sub": " · ".join(f"{agent} {count}" for agent, count in per_agent.items())},
            {"label": "未登记的技能", "value": str(sum(1 for skill in skills if skill["unregistered"])), "sub": ""},
            {"label": "钩子步骤", "value": str(len(hooks)),
             "sub": " · ".join(f"{layer} {count}" for layer, count in per_layer.items())},
            {"label": "没有测试的钩子", "value": str(sum(1 for hook in hooks if not hook["tested"])), "sub": ""},
        ],
        "groups": groups,
        "hooks": [{**hook, "mode_label": "拦截" if hook["blocking"] else "提醒",
                   "trigger": f"{hook['event']} · {hook['matcher']}" if hook["matcher"] else hook["event"]}
                  for hook in hooks],
    }
