#!/usr/bin/env python3

from __future__ import annotations

import argparse
import posixpath
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
_FILE_URI_RE = re.compile(r"file:///[^\s\"')<>]+")
_HTML_IMG_SRC_RE = re.compile(r"(<img\b[^>]*?\bsrc=)([\"'])([^\"']+)(\2)", re.IGNORECASE)

# Same-source print web edition: tools/render_web_edition.py writes a
# per-target ``webedition/`` dir (body.html + assets/ + manifest.json) beside
# the generated ``md/`` manual, by rasterizing the committed layout-contract
# PDF. When present it becomes the primary catalog entry; when absent the
# catalog is byte-identical to the HTML-only assembly.
_WEB_EDITION_DIRNAME = "webedition"
_WEB_EDITION_DOC = "print_edition"
_WEB_EDITION_STATIC = "web-edition"
# The fragment references page rasters and the downloadable PDF as ``assets/``;
# rewrite both src= (images) and href= (the PDF link) to the _static location.
_WEB_EDITION_SRC_RE = re.compile(r'(\b(?:src|href)=")assets/')


@dataclass(frozen=True)
class RtdManual:
    source_dir: Path
    destination_dir: Path
    label: str
    toctree_ref: str
    web_edition_ref: str | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble generated MyST manuals into one RTD source tree.")
    parser.add_argument("--build-root", default=Path("docs/_build"), type=Path)
    parser.add_argument("--output-dir", default=None, type=Path)
    parser.add_argument("--title", default="Auto Manual Library")
    return parser.parse_args(argv)


def _resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def _first_heading(index_path: Path) -> str:
    for line in index_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text.startswith("# "):
            return text[2:].strip()
    return index_path.parent.name


def _manual_label(source_dir: Path, build_root: Path) -> str:
    relative = source_dir.resolve(strict=False).relative_to(build_root.resolve(strict=False))
    context = " / ".join(part for part in relative.parts if part != "md")
    title = _first_heading(source_dir / "index.md")
    return f"{context} - {title}" if context else title


def _local_path_from_file_uri(raw_uri: str) -> Path:
    parsed = urlparse(raw_uri)
    path_text = unquote(parsed.path)
    if re.match(r"^/[A-Za-z]:", path_text):
        path_text = path_text[1:]
    return Path(path_text).resolve(strict=False)


def discover_manual_sources(*, build_root: Path, output_dir: Path) -> list[Path]:
    sources: list[Path] = []
    for index_path in sorted(build_root.glob("**/md/index.md")):
        source_dir = index_path.parent
        if _is_relative_to(source_dir, output_dir):
            continue
        if (source_dir / "conf.py").exists():
            sources.append(source_dir)
    return sources


def _rewrite_markdown_file_uris(*, source_dir: Path, destination_dir: Path) -> None:
    source_dir = source_dir.resolve(strict=False)
    destination_dir = destination_dir.resolve(strict=False)
    for markdown_path in destination_dir.rglob("*.md"):
        source_markdown_dir = source_dir / markdown_path.parent.relative_to(destination_dir)
        base_dirs = (
            source_markdown_dir.resolve(strict=False),
            markdown_path.parent.resolve(strict=False),
        )
        text = markdown_path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            raw_uri = match.group(0)
            local_path = _local_path_from_file_uri(raw_uri)
            for base_dir in base_dirs:
                try:
                    return local_path.relative_to(base_dir).as_posix()
                except ValueError:
                    continue
            return raw_uri

        rewritten = _FILE_URI_RE.sub(replace, text)
        if rewritten != text:
            markdown_path.write_text(rewritten, encoding="utf-8")


def _copy_manual_assets_to_static(*, output_dir: Path, destination_dir: Path, manual_relative: Path) -> None:
    static_root = output_dir / "_static" / "manual-assets" / manual_relative
    for assets_dir in destination_dir.glob("**/assets"):
        assets_relative = assets_dir.relative_to(destination_dir)
        target_dir = static_root / assets_relative
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(assets_dir, target_dir)


def _static_src_for_manual_asset(
    *,
    src: str,
    markdown_path: Path,
    output_dir: Path,
    destination_dir: Path,
    manual_relative: Path,
) -> str:
    parsed = urlparse(src)
    if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
        return src

    local_asset = (markdown_path.parent / unquote(parsed.path)).resolve(strict=False)
    if not _is_relative_to(local_asset, destination_dir):
        return src

    asset_relative = local_asset.relative_to(destination_dir.resolve(strict=False))
    if "assets" not in asset_relative.parts:
        return src

    static_asset = Path("_static") / "manual-assets" / manual_relative / asset_relative
    markdown_parent = markdown_path.parent.relative_to(output_dir).as_posix()
    rewritten = posixpath.relpath(static_asset.as_posix(), start=markdown_parent or ".")
    if parsed.query:
        rewritten = f"{rewritten}?{parsed.query}"
    if parsed.fragment:
        rewritten = f"{rewritten}#{parsed.fragment}"
    return rewritten


def _rewrite_markdown_asset_sources(*, output_dir: Path, destination_dir: Path, manual_relative: Path) -> None:
    for markdown_path in destination_dir.rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            prefix, quote, src, _ = match.groups()
            rewritten_src = _static_src_for_manual_asset(
                src=src,
                markdown_path=markdown_path,
                output_dir=output_dir,
                destination_dir=destination_dir,
                manual_relative=manual_relative,
            )
            return f"{prefix}{quote}{rewritten_src}{quote}"

        rewritten = _HTML_IMG_SRC_RE.sub(replace, text)
        if rewritten != text:
            markdown_path.write_text(rewritten, encoding="utf-8")


def _write_conf_py(*, output_dir: Path, title: str) -> None:
    output_dir.joinpath("conf.py").write_text(
        "\n".join(
            [
                "# Generated by tools.readthedocs_source. Do not hand-edit generated output.",
                "from pathlib import Path",
                "import shutil",
                "",
                f"project = {title!r}",
                "html_title = project",
                'extensions = ["myst_parser"]',
                'source_suffix = {".md": "markdown"}',
                'root_doc = "index"',
                'master_doc = "index"',
                'html_theme = "furo"',
                'html_static_path = ["_static"]',
                'exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]',
                "myst_heading_anchors = 3",
                'suppress_warnings = ["myst.header", "toc.not_included"]',
                "",
                "",
                "def _copy_manual_assets(app, exception):",
                "    if exception:",
                "        return",
                "    srcdir = Path(app.srcdir)",
                "    outdir = Path(app.outdir)",
                "    for assets_dir in srcdir.glob('**/assets'):",
                "        relative = assets_dir.relative_to(srcdir)",
                "        if '_build' in relative.parts or '_static' in relative.parts:",
                "            continue",
                "        target_dir = outdir / relative",
                "        if target_dir.exists():",
                "            shutil.rmtree(target_dir)",
                "        shutil.copytree(assets_dir, target_dir)",
                "",
                "",
                "def setup(app):",
                "    app.connect('build-finished', _copy_manual_assets)",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _graft_web_edition(
    *,
    source_dir: Path,
    output_dir: Path,
    destination_dir: Path,
    manual_relative: Path,
) -> str | None:
    """Graft a pre-rendered ``webedition/`` into the assembled tree.

    Reads ``<target>/webedition/{body.html,manifest.json,assets/}`` beside the
    ``md/`` manual, copies its assets under ``_static/web-edition/<target>/``,
    rewrites the fragment's ``assets/`` refs to that stable location, and writes
    an orphan ``indesign_web.md`` viewer page. Returns the viewer's toctree ref,
    or None when no web edition was rendered for this target.
    """
    web_dir = source_dir.parent / _WEB_EDITION_DIRNAME
    body_path = web_dir / "body.html"
    if not body_path.is_file():
        return None

    target_relative = manual_relative.parent  # <model>/<region>
    static_root = output_dir / "_static" / _WEB_EDITION_STATIC / target_relative
    assets_src = web_dir / "assets"
    if assets_src.is_dir():
        assets_dst = static_root / "assets"
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        assets_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(assets_src, assets_dst)

    static_rel = (Path("_static") / _WEB_EDITION_STATIC / target_relative).as_posix()
    viewer_parent = manual_relative.as_posix()
    prefix = posixpath.relpath(static_rel, start=viewer_parent)
    body = body_path.read_text(encoding="utf-8")
    body = _WEB_EDITION_SRC_RE.sub(rf'\1{prefix}/assets/', body)

    page_path = destination_dir / f"{_WEB_EDITION_DOC}.md"
    if page_path.exists():
        print(f"[rtd] warning: {page_path} already exists; skipping web edition graft")
        return None
    page_path.write_text("```{raw} html\n" + body + "\n```\n", encoding="utf-8")
    return (manual_relative / _WEB_EDITION_DOC).as_posix()


def _write_index_md(*, output_dir: Path, title: str, manuals: list[RtdManual]) -> None:
    lines = [f"# {title}", ""]
    for manual in manuals:
        if manual.web_edition_ref:
            lines.append(
                f"- **[{manual.label} — print edition]({manual.web_edition_ref}.md)**"
                " — print-layout pages, same source as the formal delivery"
            )
            lines.append(f"  - [{manual.label} — HTML edition]({manual.toctree_ref}.md)")
        else:
            lines.append(f"- [{manual.label}]({manual.toctree_ref}.md)")
    lines.append("")
    output_dir.joinpath("index.md").write_text("\n".join(lines), encoding="utf-8")


def assemble_rtd_source(*, build_root: Path, output_dir: Path, title: str) -> list[RtdManual]:
    build_root = build_root.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    if not _is_relative_to(output_dir, build_root):
        raise RuntimeError(f"RTD source output must stay under build root: {output_dir}")

    source_dirs = discover_manual_sources(build_root=build_root, output_dir=output_dir)
    if not source_dirs:
        raise RuntimeError(f"No generated Markdown manual sources found under {build_root}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir.joinpath("_static", "manual-assets").mkdir(parents=True, exist_ok=True)

    manuals: list[RtdManual] = []
    for source_dir in source_dirs:
        relative = source_dir.resolve(strict=False).relative_to(build_root)
        destination_dir = output_dir / relative
        shutil.copytree(source_dir, destination_dir, ignore=shutil.ignore_patterns("conf.py", "_build"))
        _rewrite_markdown_file_uris(source_dir=source_dir, destination_dir=destination_dir)
        _copy_manual_assets_to_static(output_dir=output_dir, destination_dir=destination_dir, manual_relative=relative)
        _rewrite_markdown_asset_sources(output_dir=output_dir, destination_dir=destination_dir, manual_relative=relative)
        web_edition_ref = _graft_web_edition(
            source_dir=source_dir,
            output_dir=output_dir,
            destination_dir=destination_dir,
            manual_relative=relative,
        )
        manuals.append(
            RtdManual(
                source_dir=source_dir,
                destination_dir=destination_dir,
                label=_manual_label(source_dir, build_root),
                toctree_ref=(relative / "index").as_posix(),
                web_edition_ref=web_edition_ref,
            )
        )

    _write_conf_py(output_dir=output_dir, title=title)
    _write_index_md(output_dir=output_dir, title=title, manuals=manuals)
    return manuals


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    build_root = _resolve_repo_path(args.build_root)
    output_dir = _resolve_repo_path(args.output_dir) if args.output_dir else build_root / "rtd"
    manuals = assemble_rtd_source(build_root=build_root, output_dir=output_dir, title=args.title)
    web_editions = sum(1 for manual in manuals if manual.web_edition_ref)
    print(f"[rtd] Assembled {len(manuals)} manual(s) into {output_dir} ({web_editions} print web edition(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
