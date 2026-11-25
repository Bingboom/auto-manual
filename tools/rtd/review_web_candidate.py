"""Web candidates on the private review site, built from the working draft at site build.

A line opts in with ``draft.json`` ``"web_candidate": true``. ``build_candidate``
converts the working draft (``tools.web.review_draft_web``), builds the
candidate with strict Sphinx into ``<MODEL>/<REGION>/web/`` of the site output
and keeps the conversion report beside it; nothing generated is committed, so
every push of a new draft version refreshes the candidate. A failure becomes
the line's error, shown on its page; the rest of the site still builds.

``changes_summary`` reads the line's ``web-changes.json``, written with each
version by ``python -m tools.web.review_draft_web changes <line> --write``.
It is current only while its head version is the working draft's version.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from tools.utils.path_utils import repo_root
from tools.web.review_draft_changes import CHANGES_JSON, SCHEMA as CHANGES_SCHEMA
from tools.web.review_draft_web import REPORT_JSON, convert, markdown_filename

CANDIDATE_DIR = "web"
CHANGES_PAGE = "web-changes.html"


def candidate_page(manifest: dict[str, Any]) -> str:
    """Path of the candidate's page inside the line directory."""

    name = markdown_filename(str(manifest["model"]), str(manifest["region"]), str(manifest["language"]))
    return f"{CANDIDATE_DIR}/{name.removesuffix('.md')}.html"


def changes_summary(directory: Path, manifest: dict[str, Any], expected: tuple[str, ...]) -> dict[str, Any] | None:
    """The line's recorded Web changes, or None when it has none."""

    path = directory / CHANGES_JSON
    if not path.is_file() or path.is_symlink():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or record.get("schema") != CHANGES_SCHEMA:
        raise ValueError(f'{path}: must be a "{CHANGES_SCHEMA}" record')
    return {
        "base_version": str(record["base"]["version"]),
        "head_version": str(record["head"]["version"]),
        "current": record["head"]["version"] == manifest["version"],
        "counts": dict(record["counts"]),
        "pages": list(record["pages"]),
        "url": "/".join((*expected, CHANGES_PAGE)),
    }


def _sphinx(source: Path, target: Path, doctrees: Path) -> None:
    subprocess.run(
        [sys.executable, "-m", "sphinx", "-n", "-W", "--keep-going", "-q", "-b", "html",
         "-d", str(doctrees), str(source), str(target)],
        cwd=repo_root(), check=True, capture_output=True, text=True,
    )


def build_candidate(line: Path, target_line: Path, draft: dict[str, Any]) -> dict[str, Any]:
    """Convert and build one line's candidate into ``target_line/web``; report blockers or the error."""

    target = target_line / CANDIDATE_DIR
    if target.exists():
        shutil.rmtree(target)  # a copied, committed preview never outlives the built one
    title = str(draft.get("web_title") or f"{draft['model']} {draft['region']}")
    with tempfile.TemporaryDirectory() as scratch:
        package = Path(scratch) / "candidate"
        try:
            report = convert(line, package, title=title)
            _sphinx(package, target, Path(scratch) / "doctrees")
        except subprocess.CalledProcessError as exc:
            tail = (exc.stderr or exc.stdout or "").strip().splitlines()[-1:] or ["Sphinx failed"]
            return {"error": tail[0][:300], "blockers": None}
        except (ValueError, KeyError, OSError) as exc:
            return {"error": str(exc)[:300], "blockers": None}
        shutil.copy2(package / REPORT_JSON, target / REPORT_JSON)
    return {"error": "", "blockers": len(report["release_blockers"]),
            "components": sum(report["component_inventory"].values())}


__all__ = ["CANDIDATE_DIR", "CHANGES_PAGE", "build_candidate", "candidate_page", "changes_summary"]
