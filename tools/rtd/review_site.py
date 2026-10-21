"""Private review-draft site: one 审核稿 list page plus the drafts themselves.

The drafts are business content owned by the private Hello-Docs-Review mirror
under ``docs/review-drafts/<MODEL>/<REGION>/<version>/``; auto-manual never
holds them (it is a public repository). Each version directory is a finished
draft package (HTML, assets, registers) with a ``draft.json`` manifest:

    {"model": "JHP-3600C", "region": "JP", "language": "ja", "version": "v0.69",
     "date": "2026-10-21", "status": "待母语审校", "html": "manual_…_draft.html",
     "milestone": "", "summary": "…", "rd_open": ["…", …]}

The new-translation volume comes from the package's own
``new-translation-summary.json``. The private Read the Docs project builds the
site with ``python -m tools.rtd.review_site docs/review-drafts <output>``; no
live data is read and nothing outside the output directory is written.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from tools.safe_copy import copytree_replace_no_symlinks

ASSETS = Path(__file__).resolve().parents[1] / "rtd_portal_assets"
MANIFEST = "draft.json"
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


def load_draft(directory: Path, drafts_root: Path) -> dict:
    """Read and check one version directory; the directory path must match its manifest."""
    manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    missing = [field for field in _TEXT_FIELDS if not isinstance(manifest.get(field), str) or not manifest[field]]
    if missing:
        raise ValueError(f"{directory / MANIFEST}: missing text fields {missing}")
    version_key(manifest["version"])
    date.fromisoformat(manifest["date"])
    expected = (manifest["model"], manifest["region"], manifest["version"])
    if directory.relative_to(drafts_root).parts != expected:
        raise ValueError(f"{directory}: directory must be <model>/<region>/<version> = {'/'.join(expected)}")
    if not all(_SEGMENT.match(part) for part in expected):
        raise ValueError(f"{directory / MANIFEST}: model, region and version must be plain path segments")
    page = directory / manifest["html"]
    if "/" in manifest["html"] or "\\" in manifest["html"] or page.is_symlink() or not page.is_file():
        raise ValueError(f"{directory / MANIFEST}: html must name a file in the version directory")
    rd_open = manifest.get("rd_open", [])
    if not isinstance(rd_open, list) or not all(isinstance(item, str) and item for item in rd_open):
        raise ValueError(f"{directory / MANIFEST}: rd_open must be a list of non-empty strings")
    volume = None
    if (directory / SUMMARY).is_file():
        summary = json.loads((directory / SUMMARY).read_text(encoding="utf-8"))
        volume = {"units": int(summary["units"]), "words": int(summary["words"])}
    return {
        **{field: manifest[field] for field in _TEXT_FIELDS},
        "milestone": str(manifest.get("milestone") or ""),
        "summary": str(manifest.get("summary") or ""),
        "rd_open": rd_open,
        "volume": volume,
        "url": "/".join(("drafts", *expected, manifest["html"])),
        "source": directory,
    }


def load_drafts(drafts_root: Path) -> list[dict]:
    """One entry per model/region: the newest version first, older kept versions as history."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for manifest in sorted(drafts_root.glob(f"*/*/*/{MANIFEST}")):
        draft = load_draft(manifest.parent, drafts_root)
        groups.setdefault((draft["model"], draft["region"]), []).append(draft)
    lines = []
    for (model, region), versions in sorted(groups.items()):
        versions.sort(key=lambda item: version_key(item["version"]), reverse=True)
        lines.append({"model": model, "region": region, "latest": versions[0], "history": versions[1:]})
    return lines


def render_index(lines: list[dict], *, workbench_url: str = "") -> str:
    env = Environment(loader=FileSystemLoader(str(ASSETS)), autoescape=select_autoescape(("html",)))
    return env.get_template("review_drafts.html").render(lines=lines, workbench_url=workbench_url)


def build(drafts_root: Path, output: Path) -> list[dict]:
    """Write index.html, the shared stylesheets and every kept draft version into ``output``."""
    lines = load_drafts(drafts_root)
    settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
    base = str(settings.get("site_base_url") or "").rstrip("/")
    output.mkdir(parents=True, exist_ok=True)
    static = output / "_static"
    static.mkdir(exist_ok=True)
    for name in STYLESHEETS:
        (static / name).write_bytes((ASSETS / "_static" / name).read_bytes())
    for line in lines:
        for draft in (line["latest"], *line["history"]):
            copytree_replace_no_symlinks(
                draft["source"], output / draft["url"].rsplit("/", 1)[0], destination_root=output,
                label=f"review draft {draft['model']} {draft['region']} {draft['version']}",
            )
    workbench = f"{base}/workspace/deliverables/index.html" if base else ""
    (output / "index.html").write_text(render_index(lines, workbench_url=workbench), encoding="utf-8")
    return lines


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m tools.rtd.review_site <drafts_dir> <output_dir>", file=sys.stderr)
        return 2
    lines = build(Path(argv[0]), Path(argv[1]))
    print(f"review site: {len(lines)} draft line(s), "
          f"{sum(1 + len(line['history']) for line in lines)} version(s) → {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
