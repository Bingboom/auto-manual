#!/usr/bin/env python3
"""Render ordinary Markdown files as a manual-styled web document site.

This is the *preview / sharing* lane for hand-written Markdown: point it at a
file or a folder of plain ``.md`` and it produces a self-contained static site
that uses the same presentation contract as the published web manual — furo +
``myst_parser`` + the concatenated ``web_manual.css`` — so ordinary prose,
tables and images pick up the manual's typography, paper card, table panels and
figure sizing.

It is deliberately NOT a publishing path. The Read the Docs catalog renders only
``docs/publish/web`` on the business-plane mirror, assembled from queue release
metadata by ``tools/publish_branch_assembly.py``; nothing here can or should
reach it. Component styling (``hb-*`` figures, spec/LCD/troubleshooting
compositions) needs pipeline-generated markup and will not appear for plain
Markdown — you get the manual's prose pages, not its figure pages.

Standalone use: when the repo is not importable (e.g. the exported bundle), the
stylesheet is taken from ``--stylesheet`` or a sibling ``style/web_manual.css``.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
# Running this file directly puts only tools/ on sys.path, so make the repo root
# importable when it is there; the standalone bundle simply has no tools/ sibling.
_MAYBE_REPO_ROOT = _SCRIPT_DIR.parent
if (_MAYBE_REPO_ROOT / "tools").is_dir() and str(_MAYBE_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_MAYBE_REPO_ROOT))

_BUNDLED_STYLESHEET = _SCRIPT_DIR / "style" / "web_manual.css"
_STYLESHEET_NAME = "web_manual.css"
_STATIC_DIRNAME = "_static"
_ROOT_DOC = "index"
_TOCTREE_FENCE = "```{toctree}"
_SKIP_DIRS = frozenset({"__pycache__", "_build", "_static", "node_modules", ".venv", "venv"})


@dataclass(frozen=True)
class MarkdownSite:
    source_dir: Path
    output_dir: Path
    page_count: int
    stylesheet: Path
    stylesheet_origin: str


# --------------------------------------------------------------------------
# discovery + staging
# --------------------------------------------------------------------------
def _is_skipped_dir(path: Path) -> bool:
    return path.name.startswith(".") or path.name in _SKIP_DIRS


def _skipped(relative: Path) -> bool:
    return any(part.startswith(".") or part in _SKIP_DIRS for part in relative.parts[:-1])


def discover_markdown(source_dir: Path) -> list[Path]:
    """Return repo-relative markdown paths under ``source_dir``, sorted."""
    pages: list[Path] = []
    for path in sorted(source_dir.rglob("*.md")):
        if not path.is_file():
            continue
        relative = path.relative_to(source_dir)
        if _skipped(relative):
            continue
        pages.append(relative)
    return pages


def _copy_tree(source_dir: Path, staged_dir: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = set()
        for name in names:
            candidate = Path(directory) / name
            if candidate.is_dir() and _is_skipped_dir(candidate):
                ignored.add(name)
        return ignored

    shutil.copytree(source_dir, staged_dir, ignore=ignore, dirs_exist_ok=True)


def _has_toctree(markdown_path: Path) -> bool:
    return _TOCTREE_FENCE in markdown_path.read_text(encoding="utf-8")


def _toctree_block(pages: list[Path]) -> str:
    entries = [page.with_suffix("").as_posix() for page in pages]
    return "\n".join([_TOCTREE_FENCE, ":maxdepth: 2", ""] + entries + ["```", ""])


def _write_root_index(staged_dir: Path, *, title: str, pages: list[Path]) -> list[Path]:
    """Ensure a root ``index.md`` exists with a toctree of the other pages.

    Returns the page list excluding whatever became the root document, so a
    document is never listed as a child of itself.
    """
    index_path = staged_dir / f"{_ROOT_DOC}.md"
    readme_path = staged_dir / "README.md"

    if not index_path.is_file() and readme_path.is_file():
        shutil.move(str(readme_path), str(index_path))
        pages = [page for page in pages if page.name != "README.md"]

    children = [page for page in pages if page.as_posix() != f"{_ROOT_DOC}.md"]

    if index_path.is_file():
        if children and not _has_toctree(index_path):
            existing = index_path.read_text(encoding="utf-8").rstrip("\n")
            index_path.write_text(existing + "\n\n" + _toctree_block(children), encoding="utf-8")
        return children

    body = [f"# {title}", ""]
    if children:
        body.append(_toctree_block(children))
    index_path.write_text("\n".join(body), encoding="utf-8")
    return children


# --------------------------------------------------------------------------
# style contract
# --------------------------------------------------------------------------
def resolve_stylesheet(staged_dir: Path, *, explicit: Path | None = None) -> tuple[Path, str]:
    """Place ``web_manual.css`` under ``staged_dir/_static`` and say where it came from.

    Preference order: an explicit ``--stylesheet``, then the repo's live
    contract assembler (so in-repo runs always track the contract), then a
    stylesheet bundled next to this script for standalone use.
    """
    static_dir = staged_dir / _STATIC_DIRNAME
    if explicit is not None:
        if not explicit.is_file():
            raise RuntimeError(f"stylesheet not found: {explicit}")
        static_dir.mkdir(parents=True, exist_ok=True)
        destination = static_dir / _STYLESHEET_NAME
        shutil.copyfile(explicit, destination)
        return destination, f"explicit ({explicit})"

    try:
        from tools.web_stylesheets import copy_web_stylesheet
    except ImportError:
        pass
    else:
        return copy_web_stylesheet(staged_dir), "repo contract (tools/web_stylesheets.py)"

    if _BUNDLED_STYLESHEET.is_file():
        static_dir.mkdir(parents=True, exist_ok=True)
        destination = static_dir / _STYLESHEET_NAME
        shutil.copyfile(_BUNDLED_STYLESHEET, destination)
        return destination, f"bundled ({_BUNDLED_STYLESHEET})"

    raise RuntimeError(
        "no stylesheet available: run inside the repo, pass --stylesheet, "
        f"or place one at {_BUNDLED_STYLESHEET}"
    )


# The style-critical knobs are the published web manual's presentation contract
# and must stay identical to the conf.py generated by tools/readthedocs_source.py
# (tests/test_plain_markdown_site.py pins this).
STYLE_CONF_LINES = (
    'extensions = ["myst_parser"]',
    'source_suffix = {".md": "markdown"}',
    f'root_doc = "{_ROOT_DOC}"',
    f'master_doc = "{_ROOT_DOC}"',
    'html_theme = "furo"',
    f'html_static_path = ["{_STATIC_DIRNAME}"]',
    f'html_css_files = ["{_STYLESHEET_NAME}"]',
    "myst_heading_anchors = 3",
    'suppress_warnings = ["myst.header", "toc.not_included"]',
)


def write_conf_py(staged_dir: Path, *, title: str) -> Path:
    conf_path = staged_dir / "conf.py"
    lines = [
        "# Generated by tools.plain_markdown_site. Do not hand-edit generated output.",
        f"project = {title!r}",
        "html_title = project",
        *STYLE_CONF_LINES,
        'exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]',
        "",
    ]
    conf_path.write_text("\n".join(lines), encoding="utf-8")
    return conf_path


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def _sphinx_cmd() -> list[str]:
    try:
        from tools.build_docs_sphinx import resolve_sphinx_build_cmd
        from tools.utils.process_utils import find_exe
    except ImportError:
        sphinx_build = shutil.which("sphinx-build")
        if sphinx_build:
            return [sphinx_build, "-b", "html"]
        return [sys.executable, "-m", "sphinx", "-b", "html"]
    return resolve_sphinx_build_cmd("html", find_exe=find_exe, python_executable=sys.executable)


def _guard_output_dir(output_dir: Path) -> None:
    """Refuse to write into build/release/publish trees owned by the pipeline."""
    try:
        from tools.utils.path_utils import get_paths, releases_of, repo_root
    except ImportError:
        return
    root = repo_root()
    protected = [
        get_paths().docs_build_dir,
        releases_of(root),
        get_paths().docs_dir / "publish",
    ]
    resolved = output_dir.resolve(strict=False)
    for guarded in protected:
        guarded_resolved = guarded.resolve(strict=False)
        if resolved == guarded_resolved or guarded_resolved in resolved.parents:
            raise RuntimeError(
                f"refusing to write into a pipeline-owned tree: {guarded_resolved}. "
                "Pick an output directory outside docs/_build, reports/releases and docs/publish."
            )


def render_markdown_site(
    *,
    source: Path,
    output_dir: Path,
    title: str | None = None,
    assets_dir: Path | None = None,
    work_dir: Path | None = None,
    stylesheet: Path | None = None,
    strict: bool = False,
    log=print,
) -> MarkdownSite:
    source = source.expanduser()
    output_dir = output_dir.expanduser()
    if not source.exists():
        raise RuntimeError(f"source not found: {source}")
    _guard_output_dir(output_dir)

    resolved_title = (title or source.stem if source.is_file() else title or source.name).strip()
    resolved_title = resolved_title or "Markdown Site"

    with tempfile.TemporaryDirectory() as tmp:
        staged_dir = (work_dir.expanduser() if work_dir else Path(tmp) / "source")
        if staged_dir.exists() and work_dir is not None:
            shutil.rmtree(staged_dir)
        staged_dir.mkdir(parents=True, exist_ok=True)

        if source.is_file():
            shutil.copyfile(source, staged_dir / f"{_ROOT_DOC}.md")
            if assets_dir is not None:
                assets_source = assets_dir.expanduser()
                if not assets_source.is_dir():
                    raise RuntimeError(f"assets directory not found: {assets_source}")
                shutil.copytree(assets_source, staged_dir / assets_source.name, dirs_exist_ok=True)
        else:
            _copy_tree(source, staged_dir)

        pages = discover_markdown(staged_dir)
        if not pages:
            raise RuntimeError(f"no markdown files found under {source}")
        children = _write_root_index(staged_dir, title=resolved_title, pages=pages)
        write_conf_py(staged_dir, title=resolved_title)
        stylesheet_path, origin = resolve_stylesheet(staged_dir, explicit=stylesheet)

        cmd = _sphinx_cmd()
        if strict:
            cmd.append("-W")
        cmd += [str(staged_dir), str(output_dir)]
        log(f"[md-site] {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        page_count = len(children) + 1
        log(
            f"[md-site] {page_count} page(s) rendered into {output_dir} "
            f"(style: {origin})"
        )
        return MarkdownSite(
            source_dir=source,
            output_dir=output_dir,
            page_count=page_count,
            stylesheet=stylesheet_path,
            stylesheet_origin=origin,
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, type=Path, help="A .md file, or a folder of .md files")
    parser.add_argument("--output-dir", required=True, type=Path, help="Where to write the static site")
    parser.add_argument("--title", default=None, help="Site title (default: source name)")
    parser.add_argument("--assets", default=None, type=Path, help="Single-file mode: folder of images to copy alongside")
    parser.add_argument("--work-dir", default=None, type=Path, help="Keep the staged Sphinx source here (for debugging)")
    parser.add_argument("--stylesheet", default=None, type=Path, help="Override the manual stylesheet")
    parser.add_argument("--strict", action="store_true", help="Treat Sphinx warnings as errors")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    render_markdown_site(
        source=args.source,
        output_dir=args.output_dir,
        title=args.title,
        assets_dir=args.assets,
        work_dir=args.work_dir,
        stylesheet=args.stylesheet,
        strict=args.strict,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
