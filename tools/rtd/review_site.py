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
     "milestone": "", "summary": "…", "rd_open": ["…", …]}

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
from pathlib import Path

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


def version_key(version: str) -> tuple[int, int]:
    match = _VERSION.match(version)
    if match is None:
        raise ValueError(f"draft version must look like v0.69, got {version!r}")
    return int(match.group(1)), int(match.group(2))


def load_draft(directory: Path, drafts_root: Path, *, milestone: bool) -> dict:
    """Read and check one draft package; its path must match its manifest."""
    manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    missing = [field for field in _TEXT_FIELDS if not isinstance(manifest.get(field), str) or not manifest[field]]
    if missing:
        raise ValueError(f"{directory / MANIFEST}: missing text fields {missing}")
    version_key(manifest["version"])
    date.fromisoformat(manifest["date"])
    if not all(_SEGMENT.match(manifest[field]) for field in ("model", "region")):
        raise ValueError(f"{directory / MANIFEST}: model and region must be plain path segments")
    expected = (manifest["model"], manifest["region"])
    expected += (MILESTONES, manifest["version"]) if milestone else ()
    if directory.relative_to(drafts_root).parts != expected:
        raise ValueError(f"{directory}: directory must be {'/'.join(expected)}")
    if milestone and not manifest.get("milestone"):
        raise ValueError(f"{directory / MANIFEST}: a frozen milestone must name its milestone")
    return {
        **{field: manifest[field] for field in _TEXT_FIELDS},
        "milestone": str(manifest.get("milestone") or ""),
        "summary": str(manifest.get("summary") or ""),
        "rd_open": _contents(directory, manifest),
        "volume": _volume(directory),
        "url": "/".join((*expected, manifest["html"])),
    }


def _contents(directory: Path, manifest: dict) -> list[str]:
    """Check the page the manifest names and return its open R&D questions."""
    page = directory / manifest["html"]
    if "/" in manifest["html"] or "\\" in manifest["html"] or page.is_symlink() or not page.is_file():
        raise ValueError(f"{directory / MANIFEST}: html must name a file in the draft directory")
    rd_open = manifest.get("rd_open", [])
    if not isinstance(rd_open, list) or not all(isinstance(item, str) and item for item in rd_open):
        raise ValueError(f"{directory / MANIFEST}: rd_open must be a list of non-empty strings")
    return rd_open


def _volume(directory: Path) -> dict | None:
    if not (directory / SUMMARY).is_file():
        return None
    summary = json.loads((directory / SUMMARY).read_text(encoding="utf-8"))
    return {"units": int(summary["units"]), "words": int(summary["words"])}


def load_drafts(drafts_root: Path) -> list[dict]:
    """One entry per model/region: the working draft and its frozen milestones, newest first."""
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
                      "page": f"{model}/{region}.html", "current": current, "milestones": milestones})
    stray = sorted(str(path.relative_to(drafts_root)) for path in set(drafts_root.rglob(MANIFEST)) - loaded)
    if stray:
        raise ValueError(f"draft manifests outside <model>/<region>/ and its {MILESTONES}/<version>/: {stray}; "
                         "edit the working draft in place and leave earlier versions to git history")
    return lines


def render(template: str, **context) -> str:
    env = Environment(loader=FileSystemLoader(str(ASSETS)), autoescape=select_autoescape(("html",)))
    return env.get_template(template).render(**context)


def build(drafts_root: Path, output: Path) -> list[dict]:
    """Write the overview, one page per line, the shared stylesheets and every draft into ``output``."""
    lines = load_drafts(drafts_root)
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
        page = render("review_draft_line.html", line=line, root="../", active=line["page"], **shell)
        (output / line["page"]).write_text(page, encoding="utf-8")
    page = render("review_drafts.html", root="", active="index.html", **shell)
    (output / "index.html").write_text(page, encoding="utf-8")
    return lines


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m tools.rtd.review_site <drafts_dir> <output_dir>", file=sys.stderr)
        return 2
    lines = build(Path(argv[0]), Path(argv[1]))
    print(f"review site: {len(lines)} draft line(s), "
          f"{sum(len(line['milestones']) for line in lines)} milestone(s) → {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
