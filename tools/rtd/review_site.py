"""Private review-draft site: an overview, one page per draft line, and the drafts themselves.

The drafts are business content owned by the private Hello-Docs-Review mirror
under ``docs/review-drafts/``; auto-manual never holds them (it is a public
repository). Each model/region line is one working draft, edited in place, plus
the milestone versions frozen beside it::

    docs/review-drafts/<MODEL>/<REGION>/          the working draft package
        draft.json                                its manifest (below)
        manual_…_draft.html, assets/, registers
        milestones/<version>/                     a frozen copy; draft.json names the milestone

    {"model": "JHP-3600C", "region": "JP", "language": "ja", "version": "v0.69",
     "date": "2026-10-21", "status": "待母语审校", "html": "manual_…_draft.html",
     "milestone": "", "summary": "…", "tools_sha": "1a2b3c4", "rd_open": ["…", …],
     "issues": "issues.json", "decisions": "decisions.json"}

A working draft records ``tools_sha``, the auto-manual commit it was made with.
``issues`` (optional) names the line's issue register, ``{"schema":
"review-issues/1", "issues": [...]}``: each item has an ``id``, ``title``,
``kind`` (rd, language, compliance, design, content) and ``status`` (open,
confirmed, dropped). An operator's ``adoption`` records what the draft carries;
only the owner's ``resolution`` changes ``status``. With a register, ``rd_open``
is derived from its open rd items (a hand-written ``rd_open`` must equal it).
``decisions`` (optional) names the line's operator-decision list. Working
drafts of one model that disagree on a shared ``topic`` (open in one line,
confirmed in another) produce warnings, not errors.

Intermediate versions live only in that repository's git history. A
``draft.json`` anywhere else (such as a ``<version>/`` copy beside the working
draft) fails the build, so versions cannot pile up as directories. The
new-translation volume comes from each package's ``new-translation-summary.json``.
The site keeps the repository layout, so a draft opens at the same path, and each
line's page is ``<MODEL>/<REGION>.html``. The private Read the Docs project builds
it with ``python -m tools.rtd.review_site docs/review-drafts <output>``; no live
data is read and nothing outside the output directory is written.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath

from jinja2 import Environment, FileSystemLoader, select_autoescape

from tools.rtd.deliverables import region_code, region_labels
from tools.safe_copy import copytree_replace_no_symlinks

ASSETS = Path(__file__).resolve().parents[1] / "rtd_portal_assets"
MANIFEST = "draft.json"
MILESTONES = "milestones"
SUMMARY = "new-translation-summary.json"
STYLESHEETS = ("site-shell.css", "review-drafts.css")
_VERSION = re.compile(r"^v(\d+)\.(\d+)$")
_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_TEXT_FIELDS = ("model", "region", "language", "version", "date", "status", "html")
_TOOLS_SHA = re.compile(r"^[0-9a-f]{7,40}$")
_TOPIC = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_DECISION_ID = re.compile(r"^D\d{2,}$")
ISSUES_SCHEMA = "review-issues/1"
# Issue kinds in display order; rd is the 待研发确认 list, the rest are 其他待确认.
KINDS = {"rd": "研发", "language": "语言审校", "compliance": "合规", "design": "设计", "content": "内容"}
STATUSES = ("open", "confirmed", "dropped")
# The 审核稿总览 link added to every draft page in the output (never to the source).
_HAS_OVERVIEW = re.compile(r"""class=["'](?:[^"']*\s)?to-overview(?:\s[^"']*)?["']""")
_BUTTON_GROUP = re.compile(r"""<div\b[^>]*\bclass=["'](?:[^"']*\s)?(?:controls|toolbar-actions)(?:\s[^"']*)?["'][^>]*>""")
_BODY = re.compile(r"<body\b[^>]*>", re.I)
OVERVIEW_TITLE = "返回审核稿总览，查看全部审核稿"
OVERVIEW_LABEL = "← 审核稿总览"


def version_key(version: str) -> tuple[int, int]:
    match = _VERSION.match(version)
    if match is None:
        raise ValueError(f"draft version must look like v0.69, got {version!r}")
    return int(match.group(1)), int(match.group(2))


def load_draft(directory: Path, drafts_root: Path, *, milestone: bool) -> dict:
    """Read and check one draft package; its path must match its manifest."""
    manifest = _json(directory / MANIFEST)
    expected = _check_manifest(directory, drafts_root, manifest, milestone=milestone)
    _page(directory, manifest)
    issues = _issues(directory, manifest)
    decisions = _decisions(directory, manifest)
    counts = _open_counts(issues)
    return {
        **{field: manifest[field] for field in _TEXT_FIELDS},
        "milestone": str(manifest.get("milestone") or ""),
        "summary": str(manifest.get("summary") or ""),
        "tools_sha": manifest.get("tools_sha") or "",
        "rd_open": _rd_open(directory, manifest, issues),
        "issues": issues or [],
        "registered": issues is not None,
        "open": counts,
        "other_count": None if counts is None else sum(n for kind, n in counts.items() if kind != "rd"),
        "other_open": _other_open(issues),
        "decisions": len(decisions) if decisions is not None else None,
        "decisions_url": "/".join((*expected, manifest["decisions"])) if decisions is not None else "",
        "volume": _volume(directory),
        "url": "/".join((*expected, manifest["html"])),
    }


def _check_manifest(directory: Path, drafts_root: Path, manifest: object, *, milestone: bool) -> tuple[str, ...]:
    """Check the manifest's own fields and location; return the line's path segments."""
    where = directory / MANIFEST
    if not isinstance(manifest, dict):
        raise ValueError(f"{where}: must be a JSON object")
    missing = [field for field in _TEXT_FIELDS if not isinstance(manifest.get(field), str) or not manifest[field]]
    if missing:
        raise ValueError(f"{where}: missing text fields {missing}")
    try:
        version_key(manifest["version"])
        date.fromisoformat(manifest["date"])
    except ValueError as error:
        raise ValueError(f"{where}: {error}") from error
    if not all(_SEGMENT.match(manifest[field]) for field in ("model", "region")):
        raise ValueError(f"{where}: model and region must be plain path segments")
    expected = (manifest["model"], manifest["region"])
    expected += (MILESTONES, manifest["version"]) if milestone else ()
    if directory.relative_to(drafts_root).parts != expected:
        raise ValueError(f"{directory}: directory must be {'/'.join(expected)}")
    if milestone and not manifest.get("milestone"):
        raise ValueError(f"{where}: a frozen milestone must name its milestone")
    tools_sha = manifest.get("tools_sha")
    if (tools_sha is not None or not milestone) and not (isinstance(tools_sha, str) and _TOOLS_SHA.match(tools_sha)):
        raise ValueError(f"{where}: tools_sha must be the auto-manual commit the draft was made with "
                         "(7–40 lowercase hex characters)")
    return expected


def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"{path}: cannot read JSON ({error})") from error


def _page(directory: Path, manifest: dict) -> None:
    page = directory / manifest["html"]
    if "/" in manifest["html"] or "\\" in manifest["html"] or page.is_symlink() or not page.is_file():
        raise ValueError(f"{directory / MANIFEST}: html must name a file in the draft directory")


def _record_file(directory: Path, manifest: dict, key: str) -> Path:
    """The regular file a manifest key names, inside the line directory and reached without symlinks."""
    value = manifest[key]
    relative = PurePosixPath(value) if isinstance(value, str) and value and "\\" not in value else None
    if relative is None or relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"{directory / MANIFEST}: {key} must be a relative path inside the line directory")
    path = directory
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"{directory / MANIFEST}: {key} must not pass through a symbolic link")
    if not path.is_file():
        raise ValueError(f"{directory / MANIFEST}: {key} must name a regular file, not found: {value}")
    return path


def _text(item: dict, key: str) -> bool:
    return isinstance(item.get(key), str) and bool(item[key].strip())


def _iso(value: object) -> bool:
    try:
        date.fromisoformat(str(value))
    except ValueError:
        return False
    return isinstance(value, str)


def _issues(directory: Path, manifest: dict) -> list[dict] | None:
    """The line's issue register (review-issues/1), or None when the manifest declares none."""
    if "issues" not in manifest:
        return None
    path = _record_file(directory, manifest, "issues")
    register = _json(path)
    if not isinstance(register, dict) or register.get("schema") != ISSUES_SCHEMA \
            or not isinstance(register.get("issues"), list):
        raise ValueError(f'{path}: must be {{"schema": "{ISSUES_SCHEMA}", "issues": [...]}}')
    seen: set[str] = set()
    for index, item in enumerate(register["issues"]):
        problem = _issue_problem(item, seen)
        if problem:
            raise ValueError(f"{path}: issues[{index}] {problem}")
        seen.add(item["id"])
    return register["issues"]


def _issue_problem(item: object, seen: set[str]) -> str:
    if not isinstance(item, dict):
        return "must be an object"
    if not _text(item, "id") or item["id"] in seen:
        return "needs a unique non-empty id"
    if not _text(item, "title"):
        return f"{item['id']} needs a title"
    if item.get("kind") not in KINDS:
        return f"{item['id']} kind must be one of {list(KINDS)}"
    if item.get("status") not in STATUSES:
        return f"{item['id']} status must be one of {list(STATUSES)}"
    if "topic" in item and not (isinstance(item["topic"], str) and _TOPIC.match(item["topic"])):
        return f"{item['id']} topic must be a lowercase slug such as solar-input"
    if "question" in item and not isinstance(item["question"], str):
        return f"{item['id']} question must be text"
    if "adoption" in item and not _dated(item["adoption"], ("decision", "by")):
        return f"{item['id']} adoption needs decision, by and an ISO date"
    resolution = item.get("resolution")
    if (resolution is not None or item["status"] != "open") and not _dated(resolution, ("by", "evidence")):
        return f"{item['id']} resolution needs by, an ISO date and evidence (required unless status is open)"
    return ""


def _dated(record: object, keys: tuple[str, ...]) -> bool:
    return isinstance(record, dict) and all(_text(record, key) for key in keys) and _iso(record.get("date"))


def issue_line(item: dict) -> str:
    question = item.get("question") or ""
    return f"{item['id']} {item['title']}：{question}" if question else f"{item['id']} {item['title']}"


def _rd_open(directory: Path, manifest: dict, issues: list[dict] | None) -> list[str]:
    """Open R&D questions: derived from the register when there is one, else draft.json's rd_open."""
    rd_open = manifest.get("rd_open", [])
    if not isinstance(rd_open, list) or not all(isinstance(item, str) and item for item in rd_open):
        raise ValueError(f"{directory / MANIFEST}: rd_open must be a list of non-empty strings")
    if issues is None:
        return rd_open
    derived = [issue_line(item) for item in issues if item["kind"] == "rd" and item["status"] == "open"]
    if "rd_open" in manifest and rd_open != derived:
        raise ValueError(f"{directory / MANIFEST}: rd_open differs from the open rd items of "
                         f"{directory / manifest['issues']}; drop rd_open (it is derived) or make it equal")
    return derived


def _open_counts(issues: list[dict] | None) -> dict[str, int] | None:
    if issues is None:
        return None
    return {kind: sum(item["kind"] == kind and item["status"] == "open" for item in issues) for kind in KINDS}


def _other_open(issues: list[dict] | None) -> list[dict]:
    groups = []
    for kind, label in KINDS.items():
        items = [issue_line(item) for item in issues or () if item["kind"] == kind and item["status"] == "open"]
        if kind != "rd" and items:
            groups.append({"kind": kind, "label": label, "items": items})
    return groups


def _decisions(directory: Path, manifest: dict) -> list[dict] | None:
    """The line's operator decisions, or None when the manifest declares none."""
    if "decisions" not in manifest:
        return None
    path = _record_file(directory, manifest, "decisions")
    decisions = _json(path)
    if not isinstance(decisions, list):
        raise ValueError(f"{path}: must be a JSON list of operator decisions")
    seen: set[str] = set()
    for index, item in enumerate(decisions):
        sound = isinstance(item, dict) and isinstance(item.get("id"), str) and _DECISION_ID.match(item["id"]) \
            and item["id"] not in seen and all(_text(item, key) for key in ("title", "adopted", "status")) \
            and _iso(item.get("date"))
        if not sound:
            raise ValueError(f"{path}: decisions[{index}] needs a unique id like D01, title, adopted, "
                             "status and an ISO date")
        seen.add(item["id"])
    return decisions


def _volume(directory: Path) -> dict | None:
    if not (directory / SUMMARY).is_file():
        return None
    summary = json.loads((directory / SUMMARY).read_text(encoding="utf-8"))
    return {"units": int(summary["units"]), "words": int(summary["words"])}


def load_drafts(drafts_root: Path) -> tuple[list[dict], list[str]]:
    """One entry per model/region (working draft and frozen milestones, newest first), and cross-line warnings."""
    labels = region_labels(ASSETS)
    lines, loaded = [], set()
    for manifest in sorted(drafts_root.glob(f"*/*/{MANIFEST}")):
        frozen = sorted(manifest.parent.glob(f"{MILESTONES}/*/{MANIFEST}"))
        loaded.update((manifest, *frozen))
        current = load_draft(manifest.parent, drafts_root, milestone=False)
        milestones = [load_draft(path.parent, drafts_root, milestone=True) for path in frozen]
        milestones.sort(key=lambda item: version_key(item["version"]), reverse=True)
        model, region = current["model"], current["region"]
        label = labels.get(region_code(region, labels), "")
        lines.append({"model": model, "region": region, "label": f"{label} {region}" if label else region,
                      "page": f"{model}/{region}.html", "current": current, "milestones": milestones,
                      "warnings": []})
    stray = sorted(str(path.relative_to(drafts_root)) for path in set(drafts_root.rglob(MANIFEST)) - loaded)
    if stray:
        raise ValueError(f"draft manifests outside <model>/<region>/ and its {MILESTONES}/<version>/: {stray}; "
                         "edit the working draft in place and leave earlier versions to git history")
    return lines, topic_warnings(lines)


def topic_warnings(lines: list[dict]) -> list[str]:
    """Warn when working drafts of one model hold a shared topic open in one line and confirmed in another.

    Each line has one writer, so a disagreement never blocks the build; it is listed on every affected
    line's page (``warnings``) for the next writer of either line to settle. Dropped items are exempt.
    """
    topics: dict[tuple[str, str], list[tuple[dict, dict]]] = {}
    for line in lines:
        for item in line["current"]["issues"]:
            if item.get("topic") and item["status"] != "dropped":
                topics.setdefault((line["model"], item["topic"]), []).append((line, item))
    warnings = []
    for (model, topic), hits in sorted(topics.items()):
        if len({line["region"] for line, _ in hits}) < 2 or {item["status"] for _, item in hits} != {"open", "confirmed"}:
            continue
        states = "; ".join(f"{line['region']} {item['id']} {item['status']}" for line, item in hits)
        warning = f"{model} topic {topic}: open in one line, confirmed in another ({states})"
        warnings.append(warning)
        for line in {id(line): line for line, _ in hits}.values():
            line["warnings"].append(warning)
    return warnings


def render(template: str, **context) -> str:
    env = Environment(loader=FileSystemLoader(str(ASSETS)), autoescape=select_autoescape(("html",)))
    return env.get_template(template).render(**context)


def build(drafts_root: Path, output: Path) -> tuple[list[dict], list[str]]:
    """Write the overview, one page per line, the shared stylesheets and every draft into ``output``."""
    lines, warnings = load_drafts(drafts_root)
    settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
    base = str(settings.get("site_base_url") or "").rstrip("/")
    workbench = f"{base}/workspace/deliverables/index.html" if base else ""
    output.mkdir(parents=True, exist_ok=True)
    static = output / "_static"
    static.mkdir(exist_ok=True)
    for name in STYLESHEETS:
        (static / name).write_bytes((ASSETS / "_static" / name).read_bytes())
    shell = {"lines": lines, "workbench_url": workbench}
    for line in lines:
        copytree_replace_no_symlinks(
            drafts_root / line["model"] / line["region"], output / line["model"] / line["region"],
            destination_root=output, label=f"review draft {line['model']} {line['region']}",
        )
        for draft in (line["current"], *line["milestones"]):
            add_overview_link(output / draft["url"], output)
        page = render("review_draft_line.html", line=line, root="../", active=line["page"], **shell)
        (output / line["page"]).write_text(page, encoding="utf-8")
    page = render("review_drafts.html", root="", active="index.html", **shell)
    (output / "index.html").write_text(page, encoding="utf-8")
    return lines, warnings


def overview_link(page_html: str, index: str) -> str:
    """``page_html`` with a 审核稿总览 link to ``index``; unchanged when the page already has one.

    The link joins the draft's own toolbar button group (``div.controls`` or ``div.toolbar-actions``)
    as its first child, styled by the draft; without one, a small self-styled bar follows ``<body>``.
    """
    if _HAS_OVERVIEW.search(page_html):
        return page_html
    group = _BUTTON_GROUP.search(page_html)
    if group:
        button = (f'<button type="button" class="to-overview" onclick="location.href=\'{index}\'" '
                  f'title="{OVERVIEW_TITLE}">{OVERVIEW_LABEL}</button>')
        return page_html[:group.end()] + button + page_html[group.end():]
    bar = ('<style>@media print{.to-overview-bar{display:none}}</style>'
           '<nav class="to-overview-bar" style="margin:0;padding:6px 12px;font:13px/1.5 sans-serif">'
           f'<a class="to-overview" href="{index}" title="{OVERVIEW_TITLE}" '
           f'style="color:inherit;text-decoration:none">{OVERVIEW_LABEL}</a></nav>')
    body = _BODY.search(page_html)
    at = body.end() if body else 0
    return page_html[:at] + bar + page_html[at:]


def add_overview_link(page: Path, output: Path) -> None:
    """Add the overview link to one copied draft page; the output root's index.html is its target."""
    index = "../" * (len(page.relative_to(output).parts) - 1) + "index.html"
    original = page.read_bytes().decode("utf-8")
    updated = overview_link(original, index)
    if updated != original:
        page.write_bytes(updated.encode("utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m tools.rtd.review_site <drafts_dir> <output_dir>", file=sys.stderr)
        return 2
    lines, warnings = build(Path(argv[0]), Path(argv[1]))
    for warning in warnings:
        print(f"WARNING {warning}")
    print(f"review site: {len(lines)} draft line(s), "
          f"{sum(len(line['milestones']) for line in lines)} milestone(s) → {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
