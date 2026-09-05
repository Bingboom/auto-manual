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
import csv
import hashlib
import html
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

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


def _asset_index(staged_dir: Path) -> dict[str, Path]:
    """Map every staged non-markdown file basename to its path (first wins)."""
    index: dict[str, Path] = {}
    for path in sorted(staged_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() == ".md":
            continue
        relative = path.relative_to(staged_dir)
        if _skipped(relative) or relative.parts[0] == _STATIC_DIRNAME:
            continue
        index.setdefault(path.name, relative)
    return index


_ASCII_ASSET_DIRNAME = "_md_assets"
_EXTENSION_DIRNAME = "_ext"
_EXTENSION_MODULE = "manual_md_directives"
_MD_IMAGE_RE = re.compile(r'(!\[[^\]]*\]\(\s*)([^)"\'\s]+)')
_HTML_IMAGE_RE = re.compile(r'(<img\b[^>]*?\bsrc=["\'])([^"\'>]+)')


def _is_ascii_path(text: str) -> bool:
    return text.isascii()


def _ascii_asset_copy(staged_dir: Path, staged_target: Path) -> Path:
    """Stage an ASCII-named copy of an asset and return its staged-relative path.

    MyST percent-encodes image URIs, and Sphinx then looks for a file literally
    named ``%E9%9D%A2%E6%9D%BF.png``, so a Markdown image whose path contains
    non-ASCII characters never resolves — a legacy backlog with Chinese asset
    names would silently render every such image broken. Give Sphinx an ASCII
    path to chew on; the visible alt text is untouched.
    """
    source = staged_dir / staged_target
    digest = hashlib.sha1(staged_target.as_posix().encode("utf-8")).hexdigest()[:8]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source.stem).strip("-.") or "img"
    destination_relative = Path(_ASCII_ASSET_DIRNAME) / f"{stem}-{digest}{source.suffix.lower()}"
    destination = staged_dir / destination_relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)
    return destination_relative


_REMOTE_DIRNAME = "remote"
_IMAGE_SUFFIXES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}
MAX_REMOTE_IMAGE_BYTES = 25 * 1024 * 1024


def download_remote_images(
    staged_dir: Path, *, timeout: float = 20.0, log=print
) -> tuple[int, list[str]]:
    """Localize http(s) image references so the built site is self-contained.

    Documents exported from a cloud editor reference every image on that
    editor's CDN — the HTE153 export has 57 of 57 on one host — so the site only
    renders while that host is reachable and dies with the link. Fetch each URL
    once into the staged tree and repoint the reference. Failures are reported
    and left as remote URLs rather than silently dropping artwork.
    """
    import urllib.error
    import urllib.request

    remote_dir = staged_dir / _ASCII_ASSET_DIRNAME / _REMOTE_DIRNAME
    cache: dict[str, str] = {}
    failures: list[str] = []
    downloaded = 0

    def fetch(url: str) -> str | None:
        nonlocal downloaded
        if url in cache:
            return cache[url]
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(unquote(url).split("?")[0]).stem).strip("-.")
        stem = (stem or "image")[:40]
        request = urllib.request.Request(url, headers={"User-Agent": "plain-markdown-site/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                declared = int(response.headers.get("Content-Length") or 0)
                if declared > MAX_REMOTE_IMAGE_BYTES:
                    raise ValueError(f"image is {declared} bytes, over the {MAX_REMOTE_IMAGE_BYTES} cap")
                payload = response.read(MAX_REMOTE_IMAGE_BYTES + 1)
                if len(payload) > MAX_REMOTE_IMAGE_BYTES:
                    raise ValueError(f"image exceeds the {MAX_REMOTE_IMAGE_BYTES} byte cap")
                content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip()
        except (urllib.error.URLError, ValueError, OSError, TimeoutError) as exc:
            failures.append(f"{url} ({exc})")
            cache[url] = ""
            return None
        suffix = Path(unquote(url).split("?")[0]).suffix.lower()
        if suffix not in {value for value in _IMAGE_SUFFIXES.values()}:
            suffix = _IMAGE_SUFFIXES.get(content_type, ".png")
        remote_dir.mkdir(parents=True, exist_ok=True)
        target = remote_dir / f"{stem}-{digest}{suffix}"
        target.write_bytes(payload)
        downloaded += 1
        cache[url] = target.relative_to(staged_dir).as_posix()
        return cache[url]

    for markdown_path in sorted(staged_dir.rglob("*.md")):
        relative = markdown_path.relative_to(staged_dir)
        if _skipped(relative):
            continue
        start = relative.parent.as_posix() or "."
        text = markdown_path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            prefix, url = match.group(1), match.group(2)
            if not url.lower().startswith(("http://", "https://")):
                return match.group(0)
            staged = fetch(url)
            if not staged:
                return match.group(0)
            return f"{prefix}{posixpath.relpath(staged, start=start)}"

        rewritten = _MD_IMAGE_RE.sub(replace, text)
        rewritten = _HTML_IMAGE_RE.sub(replace, rewritten)
        if rewritten != text:
            markdown_path.write_text(rewritten, encoding="utf-8")

    if downloaded:
        log(f"[md-site] downloaded {downloaded} remote image(s) into the site")
    for failure in failures:
        log(f"[md-site] warning: could not download {failure}")
    return downloaded, failures


def normalize_image_refs(staged_dir: Path, *, log=print) -> int:
    """Make image references resolvable for legacy and exported Markdown.

    Two fixes, both applied only to the staged copy:

    * A reference that does not resolve is repointed by basename to the staged
      file. Documents carry paths from wherever they used to live — a published
      manual references
      ``../../../_static/manual-assets/<model>/<region>/md/assets/x.png`` — and
      the file is usually right there under another route.
    * A Markdown image whose resolved path contains non-ASCII characters is
      pointed at an ASCII-named staged copy, because MyST/Sphinx cannot resolve
      percent-encoded paths (see ``_ascii_asset_copy``). Raw HTML ``<img>`` is
      left alone: the browser resolves those, and the build copies files
      verbatim.
    """
    index = _asset_index(staged_dir)
    if not index:
        return 0
    rewrites = 0
    for markdown_path in sorted(staged_dir.rglob("*.md")):
        relative = markdown_path.relative_to(staged_dir)
        if _skipped(relative):
            continue
        start = relative.parent.as_posix() or "."
        text = markdown_path.read_text(encoding="utf-8")

        def resolve_target(ref: str) -> Path | None:
            """Staged-relative path for a reference, or None to leave it alone."""
            if "://" in ref or ref.startswith(("data:", "/", "#")):
                return None
            decoded = unquote(ref)
            candidate = (markdown_path.parent / decoded).resolve(strict=False)
            if candidate.is_file():
                try:
                    return candidate.relative_to(staged_dir.resolve(strict=False))
                except ValueError:
                    return None
            return index.get(Path(decoded).name)

        def replace_markdown(match: re.Match[str]) -> str:
            nonlocal rewrites
            prefix, ref = match.group(1), match.group(2)
            target = resolve_target(ref)
            if target is None:
                return match.group(0)
            if not _is_ascii_path(target.as_posix()):
                target = _ascii_asset_copy(staged_dir, target)
            repointed = posixpath.relpath(target.as_posix(), start=start)
            if repointed == ref:
                return match.group(0)
            rewrites += 1
            return f"{prefix}{repointed}"

        def replace_html(match: re.Match[str]) -> str:
            nonlocal rewrites
            prefix, ref = match.group(1), match.group(2)
            if "://" in ref or ref.startswith(("data:", "/", "#")):
                return match.group(0)
            if (markdown_path.parent / unquote(ref)).resolve(strict=False).is_file():
                return match.group(0)
            target = index.get(Path(unquote(ref)).name)
            if target is None:
                return match.group(0)
            rewrites += 1
            return f"{prefix}{posixpath.relpath(target.as_posix(), start=start)}"

        rewritten = _MD_IMAGE_RE.sub(replace_markdown, text)
        rewritten = _HTML_IMAGE_RE.sub(replace_html, rewritten)
        if rewritten != text:
            markdown_path.write_text(rewritten, encoding="utf-8")
    if rewrites:
        log(f"[md-site] repointed {rewrites} image reference(s) to staged files")
    return rewrites


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)")
_CODE_RE = re.compile(r"`([^`]+)`")


def _inline(text: str) -> str:
    """Escape a cell, then re-enable the inline Markdown a table cell may carry."""
    escaped = _esc(text)
    escaped = _CODE_RE.sub(r"<code>\1</code>", escaped)
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    return _ITALIC_RE.sub(r"<em>\1</em>", escaped)


_TABLE_DELIMITER_RE = re.compile(r"^\|[\s:|-]+\|$")
_SUPERSCRIPT_RE = re.compile(r"\^\(([^)]{1,12})\)")
_MD_IMAGE_INLINE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")


def _split_row(line: str) -> list[str]:
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") else body
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", body)]


def _cell_html(text: str) -> str:
    """Inline Markdown a spec cell can carry, rendered as the manual does it."""
    html_text = _inline(text)
    html_text = _SUPERSCRIPT_RE.sub(r'<sup class="hb-spec-reference">\1</sup>', html_text)

    def image(match: re.Match[str]) -> str:
        alt, src = match.group(1), match.group(2)
        return f'<img src="{src}" alt="{alt}"/>'

    return _MD_IMAGE_INLINE_RE.sub(image, html_text)


def _nearest_heading(lines: list[str], index: int) -> str:
    for line in reversed(lines[:index]):
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def _spec_table_html(rows: list[list[str]], *, aria_label: str) -> str:
    """Render label/value rows as the manual's spec-table composition.

    A GFM pipe table cannot express what this table actually is: it forces a
    header row (so a headerless spec block renders an empty grey strip), it
    cannot mark the label column as ``<th>``, and it has no rowspan, so one
    label covering two values loses the join. The stylesheet keys off exactly
    those three things, which is why an untouched pipe table looks nothing like
    the published table. Emit the real structure instead.
    """
    body: list[str] = []
    index = 0
    while index < len(rows):
        label, *values = rows[index]
        span = 1
        while index + span < len(rows) and not rows[index + span][0].strip():
            span += 1
        rowspan = f' rowspan="{span}"' if span > 1 else ""
        value_html = "".join(
            f'<td class="manual-spec-value hb-spec-value">{_cell_html(value)}</td>' for value in values
        )
        body.append(
            f'<tr><th class="manual-spec-label hb-spec-label" scope="row"{rowspan}>'
            f"{_cell_html(label)}</th>{value_html}</tr>"
        )
        for offset in range(1, span):
            merged_values = "".join(
                f'<td class="manual-spec-value hb-spec-value">{_cell_html(value)}</td>'
                for value in rows[index + offset][1:]
            )
            body.append(f"<tr>{merged_values}</tr>")
        index += span

    label_attr = f' aria-label="{_esc(aria_label)}"' if aria_label else ""
    return (
        f'<figure{label_attr} class="hb-spec-table-composition">'
        '<table class="manual-table manual-spec-table hb-spec-table">'
        '<colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup>'
        f'<tbody>{"".join(body)}</tbody></table></figure>'
    )


SIGNAL_WORDS = frozenset(
    {"WARNING", "CAUTION", "NOTE", "TIP", "DANGER", "IMPORTANT", "NOTICE", "ATTENTION"}
)
_MARKUP_STRIP_RE = re.compile(r"^[#*\s]+|[*\s]+$")
_LEADING_NUMBER_RE = re.compile(r"^[①-⑳\d]{1,3}$")
_SUP_RE = re.compile(r"\^([^\^\s][^\^]{0,24})\^")
_SUB_RE = re.compile(r"~([^~\s][^~]{0,24})~")


def _bare(cell: str) -> str:
    """Cell text without heading marks, bold stars or surrounding space."""
    return _MARKUP_STRIP_RE.sub("", cell).strip()


def _is_signal_word(cell: str) -> bool:
    return _bare(cell).upper() in SIGNAL_WORDS


def _callout_html(label: str, body: str) -> str:
    """The manual's callout box: a labelled cell beside the message."""
    return (
        '<table class="manual-callout-table"><tbody><tr>'
        f'<td class="manual-callout-label"><p><strong>{_esc(_bare(label))}</strong></p></td>'
        f'<td class="manual-callout-body"><p>{_cell_html(body)}</p></td>'
        "</tr></tbody></table>"
    )


def _looks_like_data(header: list[str]) -> bool:
    """True when the header row is really the first data row.

    Cloud-editor exports put the delimiter after the first data row when the
    source table had no header, so genuine content lands in ``<thead>`` and
    renders as column headings — an icon, a circled index or an in-table
    section heading sitting in a header slot is the giveaway.
    """
    first = header[0].strip() if header else ""
    if "![" in "".join(header):
        return True
    if first.startswith("#"):
        return True
    return bool(_LEADING_NUMBER_RE.match(_bare(first)))


def _section_split(rows: list[list[str]]) -> list[tuple[str, list[list[str]]]]:
    """Split rows on in-table section headings (``### INPUT PORTS`` style).

    The published manual renders one bordered composition per spec group, so a
    single exported table carrying several ``###`` rows has to become several
    compositions rather than one long grid.
    """
    groups: list[tuple[str, list[list[str]]]] = []
    current_title = ""
    current: list[list[str]] = []
    for row in rows:
        first = row[0].strip()
        rest_empty = not any(cell.strip() for cell in row[1:])
        if first.startswith("#") and rest_empty:
            if current:
                groups.append((current_title, current))
            current_title = _bare(first)
            current = []
            continue
        current.append(row)
    if current:
        groups.append((current_title, current))
    return groups


def _is_label_value(rows: list[list[str]]) -> bool:
    """True when the first column reads as labels rather than artwork.

    An icon-and-meaning table is also two headerless columns, but putting the
    icon in a grey ``<th>`` label cell is not what it is; those stay a plain
    manual table.
    """
    firsts = [row[0] for row in rows if row and row[0].strip()]
    if not firsts:
        return False
    images = sum(1 for cell in firsts if cell.lstrip().startswith("!["))
    return images * 2 <= len(firsts)


def _cell_to_markdown(cell: str) -> list[str]:
    """A cell's content as markdown lines, recovering what the export flattened.

    Cloud editors fake a paragraph break inside a cell with ``<br>`` plus literal
    spaces, and a bullet list with ``*   `` — which markdown-it does not parse
    inside a table cell, so it prints as literal asterisks. In a directive body
    these become real blank lines and real list items.
    """
    text = re.sub(r"<br\s*/?>", "\n", cell)
    lines: list[str] = []
    for raw_line in text.split("\n"):
        stripped = raw_line.strip().replace("\xa0", " ").strip()
        if not stripped:
            continue
        bullet = re.match(r"^[*\u2022\u203b]\s+(.*)$", stripped)
        ordered = re.match(r"^(\d+)[.)]\s+(.*)$", stripped)
        if bullet:
            lines += ["", f"- {bullet.group(1).strip()}"]
        elif ordered:
            lines += ["", f"{ordered.group(1)}. {ordered.group(2).strip()}"]
        else:
            lines += ["", stripped]
    while lines and not lines[0]:
        lines.pop(0)
    return lines or [""]


def _fence(name: str, argument: str, body: list[str]) -> list[str]:
    head = f"```{{{name}}} {argument}".rstrip() if argument else f"```{{{name}}}"
    return ["", head, *body, "```", ""]


def _callout_directive(label: str, body: str) -> list[str]:
    return _fence("callout", _bare(label).upper(), _cell_to_markdown(body))


def _spec_directive(rows: list[list[str]], *, label: str) -> list[str]:
    body = [" | ".join(cell.replace("|", "\\|") for cell in row).rstrip() for row in rows]
    return _fence("spec-table", label, body)


def _row_directive(name: str, rows: list[list[str]], *, label: str = "") -> list[str]:
    body = [" | ".join(cell.replace("|", "\\|") for cell in row).rstrip() for row in rows]
    return _fence(name, label, body)


def _pipe_table(header: list[str], rows: list[list[str]], *, hint: str = "") -> list[str]:
    """Keep an unclassified table as a pipe table, with a hint for the operator."""
    width = max([len(header)] + [len(row) for row in rows]) if rows or header else 0
    def line(cells: list[str]) -> str:
        padded = cells + [""] * (width - len(cells))
        return "| " + " | ".join(padded) + " |"
    out = [""]
    if hint:
        out.append(f"<!-- md-site: unclassified table; consider {hint} -->")
    out.append(line(header if any(header) else [""] * width))
    out.append("|" + "|".join([" --- "] * width) + "|")
    out += [line(row) for row in rows]
    out.append("")
    return out


def _has_merge_gap(rows: list[list[str]]) -> bool:
    """True when a later row leaves a cell blank, meaning it merges upward."""
    return any(
        not cell.strip()
        for row in rows[1:]
        for cell in row
    )


def _looks_like_lcd_mode(rows: list[list[str]]) -> bool:
    """Screen art in the first cell, then a state/action/detail matrix."""
    if len(rows) < 2 or len(rows[0]) < 4:
        return False
    if "![" not in rows[0][0]:
        return False
    if any("![" in row[0] for row in rows[1:]):
        return False
    return _has_merge_gap([row[1:] for row in rows])


def _looks_like_lcd_rows(rows: list[list[str]]) -> bool:
    """Index, icon, name, behaviour — the manual's LCD legend."""
    scored = 0
    for row in rows:
        indexed = bool(_LEADING_NUMBER_RE.match(_bare(row[0]))) or not row[0].strip()
        if indexed and "![" in row[1] and "![" not in row[2]:
            scored += 1
    return scored * 2 > len(rows)


def _looks_like_symbol_pairs(rows: list[list[str]]) -> bool:
    """Two side-by-side icon/meaning pairs in one four-column table."""
    scored = sum(1 for row in rows if "![" in row[0] and "![" in row[2])
    return scored * 2 > len(rows)


def _plain_table_html(rows: list[list[str]], *, aria_label: str) -> str:
    """A headerless table with more than two columns: drop the phantom header."""
    body = "".join(
        "<tr>" + "".join(f"<td>{_cell_html(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    label_attr = f' aria-label="{_esc(aria_label)}"' if aria_label else ""
    return f'<table class="manual-table"{label_attr}><tbody>{body}</tbody></table>'


def upgrade_spec_tables(staged_dir: Path, *, log=print) -> int:
    """Rewrite headerless pipe tables into the manual's real table markup.

    Only tables whose header row is entirely empty are touched — those are the
    ones a converter produced for a table that never had a header, and the only
    ones that render the phantom grey strip. Tables with a genuine header are
    left alone: the generic stylesheet already renders those correctly.
    """
    upgraded = 0
    for markdown_path in sorted(staged_dir.rglob("*.md")):
        relative = markdown_path.relative_to(staged_dir)
        if _skipped(relative):
            continue
        lines = markdown_path.read_text(encoding="utf-8").splitlines()
        out: list[str] = []
        index = 0
        changed = False
        while index < len(lines):
            line = lines[index]
            is_table_start = (
                line.strip().startswith("|")
                and index + 1 < len(lines)
                and _TABLE_DELIMITER_RE.match(lines[index + 1].strip())
            )
            if not is_table_start:
                out.append(line)
                index += 1
                continue
            header = _split_row(line)
            cursor = index + 2
            rows: list[list[str]] = []
            while cursor < len(lines) and lines[cursor].strip().startswith("|"):
                row = _split_row(lines[cursor])
                if row and any(cell for cell in row):
                    rows.append(row)
                cursor += 1

            # A two-column table with no body rows whose first cell is a signal
            # word is a callout box that a cloud export flattened into a table.
            if not rows and len(header) == 2 and _is_signal_word(header[0]):
                out.extend(_callout_directive(header[0], header[1]))
                upgraded += 1
                changed = True
                index = cursor
                continue

            header_is_data = _looks_like_data(header)
            if any(cell for cell in header) and not header_is_data:
                # A real header is fine as a pipe table — unless a body cell is
                # blank, which in the source convention means "merge with the
                # cell above". A pipe table has no rowspan, so that blank
                # renders as an empty box; the comparison component can express it.
                if rows and _has_merge_gap(rows):
                    if len(header) == 2:
                        out.extend(_row_directive("comparison", rows, label=" | ".join(header)))
                    else:
                        body = [
                            " | ".join(cell.replace("|", "\\|") for cell in row).rstrip()
                            for row in rows
                        ]
                        out.extend(
                            ["", "```{manual-table}", f":headers: {' | '.join(header)}", "", *body, "```", ""]
                        )
                    upgraded += 1
                    changed = True
                    index = cursor
                    continue
                out.append(line)
                index += 1
                continue
            if header_is_data:
                rows.insert(0, header)
            if not rows:
                out.append(line)
                index += 1
                continue
            aria_label = _nearest_heading(lines, index)
            width = max(len(row) for row in rows)
            rows = [row + [""] * (width - len(row)) for row in rows]
            blocks: list[str] = []
            if width == 4 and _looks_like_lcd_mode(rows):
                blocks += _fence(
                    "lcd-mode", rows[0][0],
                    [" | ".join(cell.replace("|", "\\|") for cell in row[1:]).rstrip() for row in rows],
                )
            elif width == 4 and _looks_like_lcd_rows(rows):
                blocks += _row_directive("lcd-icons", rows, label=aria_label)
            elif width == 4 and _looks_like_symbol_pairs(rows):
                blocks += _row_directive(
                    "symbols", [pair for row in rows for pair in (row[:2], row[2:]) if any(pair)],
                    label=aria_label,
                )
            else:
                for section_title, section_rows in _section_split(rows):
                    if not section_rows:
                        continue
                    label = section_title or aria_label
                    if section_title:
                        blocks += ["", f"### {section_title}"]
                    if width == 2 and _is_label_value(section_rows):
                        blocks += _spec_directive(section_rows, label=label)
                    elif _has_merge_gap(section_rows):
                        # blanks mean row spans, which a pipe table cannot express
                        blocks += _row_directive("manual-table", section_rows, label=label)
                    else:
                        blocks += _pipe_table(
                            [""] * width, section_rows,
                            hint="{lcd-icons}, {symbols}, {troubleshooting} or {comparison}",
                        )
            out += blocks
            upgraded += 1
            changed = True
            index = cursor
        if changed:
            markdown_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    if upgraded:
        log(f"[md-site] upgraded {upgraded} headerless table(s) to manual table markup")
    return upgraded


def normalize_inline_syntax(staged_dir: Path, *, log=print) -> int:
    """Render pandoc-style ``^sup^`` and ``~sub~`` that MyST leaves as literals.

    Exported manuals carry footnote markers as ``Bypass Mode^①^`` and units as
    ``V~oc~``. MyST enables neither extension, so both print their tildes and
    carets verbatim. Convert to real ``<sup>``/``<sub>`` outside code, where the
    characters must stay untouched.
    """
    converted = 0
    for markdown_path in sorted(staged_dir.rglob("*.md")):
        relative = markdown_path.relative_to(staged_dir)
        if _skipped(relative):
            continue
        out: list[str] = []
        in_fence = False
        changed = False
        for line in markdown_path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                out.append(line)
                continue
            if in_fence or "`" in line:
                out.append(line)
                continue
            rewritten, sup_count = _SUP_RE.subn(r"<sup>\1</sup>", line)
            rewritten, sub_count = _SUB_RE.subn(r"<sub>\1</sub>", rewritten)
            if sup_count or sub_count:
                converted += sup_count + sub_count
                changed = True
            out.append(rewritten)
        if changed:
            markdown_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    if converted:
        log(f"[md-site] converted {converted} superscript/subscript marker(s)")
    return converted


def ensure_page_titles(staged_dir: Path, *, titles: dict[str, str] | None = None, log=print) -> int:
    """Give every staged page a level-1 heading so the sidebar can link it.

    Sphinx refuses to link a toctree entry with no title, which drops legacy
    documents that simply start with body text. Prepend the manifest title (or
    the filename) to the staged copy rather than asking anyone to edit hundreds
    of originals.
    """
    titles = titles or {}
    added = 0
    for markdown_path in sorted(staged_dir.rglob("*.md")):
        relative = markdown_path.relative_to(staged_dir)
        if _skipped(relative) or relative.as_posix() == f"{_ROOT_DOC}.md":
            continue
        text = markdown_path.read_text(encoding="utf-8")
        if any(line.strip().startswith("# ") for line in text.splitlines()):
            continue
        heading = titles.get(relative.as_posix()) or markdown_path.stem
        markdown_path.write_text(f"# {heading}\n\n{text.lstrip()}", encoding="utf-8")
        added += 1
    if added:
        log(f"[md-site] added a heading to {added} page(s) that had none")
    return added


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

    # One document needs no landing page in front of it: promote it to the root
    # so the site opens on the content instead of a page holding one link.
    if len(children) == 1 and not index_path.is_file():
        only = staged_dir / children[0]
        only.replace(index_path)
        return []

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


def stage_component_extension(staged_dir: Path) -> bool:
    """Copy the manual-component extension and its typed contract runtime.

    The extension is what turns declared intent (``{callout}``, ``{spec-table}``
    …) into the exact markup the stylesheet expects, so a document converted to
    the intermediate form renders deterministically instead of relying on shape
    heuristics. The staged Sphinx process cannot assume the source checkout is on
    ``sys.path``, so it receives the bounded ComponentSpec package, path helper,
    and registry contract beside the extension. Absent (an incomplete bundle),
    the directives simply are not available and Sphinx reports the unknown
    directive.
    """
    source = _SCRIPT_DIR / f"{_EXTENSION_MODULE}.py"
    component_specs = _SCRIPT_DIR / "component_specs"
    troubleshooting = _SCRIPT_DIR / "web_troubleshooting_component.py"
    lcd = _SCRIPT_DIR / "web_lcd_component.py"
    path_utils = _SCRIPT_DIR / "utils" / "path_utils.py"
    registry = (
        _MAYBE_REPO_ROOT
        / "docs"
        / "renderers"
        / "contracts"
        / "component_registry.yaml"
    )
    theme = registry.with_name("manual_theme.yaml")
    if not all(
        path.is_file()
        for path in (source, troubleshooting, lcd, path_utils, registry, theme, _SCRIPT_DIR / "__init__.py")
    ) or not component_specs.is_dir():
        return False
    target_dir = staged_dir / _EXTENSION_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target_dir / f"{_EXTENSION_MODULE}.py")
    staged_tools = target_dir / "tools"
    staged_tools.mkdir()
    shutil.copyfile(troubleshooting, staged_tools / troubleshooting.name)
    shutil.copyfile(lcd, staged_tools / lcd.name)
    shutil.copyfile(_SCRIPT_DIR / "__init__.py", staged_tools / "__init__.py")
    shutil.copytree(
        component_specs,
        staged_tools / "component_specs",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    staged_utils = staged_tools / "utils"
    staged_utils.mkdir()
    shutil.copyfile(_SCRIPT_DIR / "utils" / "__init__.py", staged_utils / "__init__.py")
    shutil.copyfile(path_utils, staged_utils / "path_utils.py")
    staged_registry = target_dir / "docs" / "renderers" / "contracts"
    staged_registry.mkdir(parents=True)
    shutil.copyfile(registry, staged_registry / registry.name)
    shutil.copyfile(theme, staged_registry / theme.name)
    return True


def write_conf_py(staged_dir: Path, *, title: str, components: bool = True) -> Path:
    conf_path = staged_dir / "conf.py"
    lines = [
        "# Generated by tools.plain_markdown_site. Do not hand-edit generated output.",
        "from pathlib import Path",
        "import shutil",
        "import sys",
        "",
        f"project = {title!r}",
        "html_title = project",
        *STYLE_CONF_LINES,
        'exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "_ext"]',
        "",
    ]
    if components:
        lines += [
            f"sys.path.insert(0, str(Path(__file__).parent / {_EXTENSION_DIRNAME!r}))",
            f"extensions.append({_EXTENSION_MODULE!r})",
        ]
    lines += [
        "",
        "",
        # Sphinx only tracks images it parses into image nodes, so anything
        # referenced from a raw HTML block (every pasted manual component, and
        # every <img> a pipeline-exported manual carries) is never copied.
        # Mirror tools/readthedocs_source.py and copy the files verbatim.
        "def _copy_referenced_files(app, exception):",
        "    if exception:",
        "        return",
        "    srcdir = Path(app.srcdir)",
        "    outdir = Path(app.outdir)",
        "    for path in srcdir.rglob('*'):",
        "        if not path.is_file() or path.suffix.lower() in {'.md', '.py'}:",
        "            continue",
        "        relative = path.relative_to(srcdir)",
        "        if relative.parts[0] in {'_static', '_build'}:",
        "            continue",
        "        target = outdir / relative",
        "        target.parent.mkdir(parents=True, exist_ok=True)",
        "        shutil.copyfile(path, target)",
        "",
        "",
        "def setup(app):",
        "    app.connect('build-finished', _copy_referenced_files)",
        "",
    ]
    conf_path.write_text("\n".join(lines), encoding="utf-8")
    return conf_path


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def _require_sphinx() -> None:
    """Fail with something actionable when the renderer is not installed.

    The default ``python3`` on macOS is 3.9 from the Command Line Tools, which
    cannot even install the pinned Sphinx 8, so the raw CalledProcessError this
    used to raise sent people to the wrong problem.
    """
    import importlib.util

    missing = [name for name in ("sphinx", "myst_parser", "furo") if importlib.util.find_spec(name) is None]
    if not missing:
        return
    raise RuntimeError(
        "missing renderer package(s): "
        + ", ".join(missing)
        + f"\nThis interpreter is {sys.executable} (Python "
        + ".".join(str(part) for part in sys.version_info[:3])
        + ").\nEither run this script with an interpreter that has them "
        "(the repo's .venv/bin/python does), or install into a Python 3.12+:\n"
        '  python3.12 -m pip install "sphinx==8.2.3" "myst-parser==4.0.1" "furo==2025.12.19"'
    )


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
    source: Path | None = None,
    manifest: Path | None = None,
    output_dir: Path | None = None,
    title: str | None = None,
    assets_dir: Path | None = None,
    work_dir: Path | None = None,
    stylesheet: Path | None = None,
    strict: bool = False,
    normalize_images: bool = True,
    upgrade_tables: bool = True,
    download_images: bool = False,
    intermediate_dir: Path | None = None,
    log=print,
) -> MarkdownSite:
    if (source is None) == (manifest is None):
        raise RuntimeError("pass exactly one of source= or manifest=")
    output_dir = output_dir.expanduser() if output_dir is not None else None
    if output_dir is not None:
        _guard_output_dir(output_dir)

    entries: list[ManifestEntry] = []
    if manifest is not None:
        manifest = manifest.expanduser()
        if not manifest.is_file():
            raise RuntimeError(f"manifest not found: {manifest}")
        entries = read_manifest(manifest)
        resolved_title = (title or manifest.stem).strip() or "Markdown Site"
    else:
        assert source is not None
        source = source.expanduser()
        if not source.exists():
            raise RuntimeError(f"source not found: {source}")
        resolved_title = (title or source.stem if source.is_file() else title or source.name).strip()
        resolved_title = resolved_title or "Markdown Site"

    with tempfile.TemporaryDirectory() as tmp:
        staged_dir = (work_dir.expanduser() if work_dir else Path(tmp) / "source")
        if staged_dir.exists() and work_dir is not None:
            shutil.rmtree(staged_dir)
        staged_dir.mkdir(parents=True, exist_ok=True)

        manifest_routes: list[Path] | None = None
        route_titles: dict[str, str] = {}
        if entries:
            manifest_routes = stage_manifest(entries, staged_dir, title=resolved_title)
            route_titles = {
                route.as_posix(): entry.title
                for entry, route in zip(entries, manifest_routes, strict=True)
            }
        elif source is not None and source.is_file():
            shutil.copyfile(source, staged_dir / f"{_ROOT_DOC}.md")
            if assets_dir is not None:
                assets_source = assets_dir.expanduser()
                if not assets_source.is_dir():
                    raise RuntimeError(f"assets directory not found: {assets_source}")
                shutil.copytree(assets_source, staged_dir / assets_source.name, dirs_exist_ok=True)
        else:
            assert source is not None
            _copy_tree(source, staged_dir)

        pages = discover_markdown(staged_dir)
        if not pages:
            raise RuntimeError(f"no markdown files found under {manifest or source}")
        if download_images:
            download_remote_images(staged_dir, log=log)
        if normalize_images:
            normalize_image_refs(staged_dir, log=log)
        if upgrade_tables:
            normalize_inline_syntax(staged_dir, log=log)
            upgrade_spec_tables(staged_dir, log=log)
        ensure_page_titles(staged_dir, titles=route_titles, log=log)
        if manifest_routes is None:
            children = _write_root_index(staged_dir, title=resolved_title, pages=pages)
        else:
            children = manifest_routes
        components = stage_component_extension(staged_dir)
        write_conf_py(staged_dir, title=resolved_title, components=components)
        stylesheet_path, origin = resolve_stylesheet(staged_dir, explicit=stylesheet)

        if intermediate_dir is not None:
            destination = intermediate_dir.expanduser()
            _guard_output_dir(destination)
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(
                staged_dir, destination,
                ignore=shutil.ignore_patterns("conf.py", _EXTENSION_DIRNAME, _STATIC_DIRNAME),
            )
            page_count = len(children) + 1
            log(
                f"[md-site] wrote the intermediate form of {page_count} page(s) to {destination}; "
                "review it, then build from it with --source"
            )
            return MarkdownSite(
                source_dir=source if source is not None else manifest,
                output_dir=destination,
                page_count=page_count,
                stylesheet=stylesheet_path,
                stylesheet_origin=origin,
            )

        _require_sphinx()
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
            source_dir=source if source is not None else manifest,
            output_dir=output_dir,
            page_count=page_count,
            stylesheet=stylesheet_path,
            stylesheet_origin=origin,
        )


@dataclass(frozen=True)
class ManifestEntry:
    source: Path
    title: str
    section: str
    order: int


MANIFEST_COLUMNS = ("source", "title", "section", "order")


def read_manifest(manifest_path: Path, *, base_dir: Path | None = None) -> list[ManifestEntry]:
    """Read a batch manifest CSV: ``source`` required, ``title``/``section``/``order`` optional.

    ``source`` is a markdown file path, relative to the manifest's own folder
    unless absolute, so a manifest can travel with the documents it lists.
    Rows whose source is blank or that start with ``#`` are ignored, which keeps
    a hand-maintained inventory easy to comment out.
    """
    base = base_dir or manifest_path.parent
    entries: list[ManifestEntry] = []
    with manifest_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "source" not in {
            (name or "").strip().lower() for name in reader.fieldnames
        }:
            raise RuntimeError(
                f"{manifest_path} needs a header row with a 'source' column "
                f"(optional: {', '.join(MANIFEST_COLUMNS[1:])})"
            )
        for index, raw in enumerate(reader):
            row = {(key or "").strip().lower(): (value or "").strip() for key, value in raw.items()}
            source_text = row.get("source", "")
            if not source_text or source_text.startswith("#"):
                continue
            source = Path(source_text).expanduser()
            if not source.is_absolute():
                source = base / source
            if not source.is_file():
                raise RuntimeError(f"{manifest_path}: source not found: {source}")
            order_text = row.get("order", "")
            try:
                order = int(order_text) if order_text else index
            except ValueError as exc:
                raise RuntimeError(f"{manifest_path}: order must be an integer, got {order_text!r}") from exc
            entries.append(
                ManifestEntry(
                    source=source,
                    title=row.get("title", "") or source.stem,
                    section=row.get("section", ""),
                    order=order,
                )
            )
    if not entries:
        raise RuntimeError(f"{manifest_path} lists no usable sources")
    return sorted(entries, key=lambda entry: (entry.section, entry.order, entry.title))


def _first_heading(markdown_path: Path) -> str:
    for line in markdown_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return markdown_path.stem


def write_manifest_scaffold(source_dir: Path, manifest_path: Path, *, log=print) -> int:
    """Scaffold a batch manifest CSV from an existing folder of Markdown.

    Hand-writing an inventory for a large backlog is the real chore, so derive
    a starting point: title from each document's first ``# `` heading, section
    from its top-level subfolder, order from the alphabetical position inside
    that section. The operator then edits titles/sections/order by hand — the
    CSV is the editable layer, this only fills the blank page.
    """
    source_dir = source_dir.expanduser()
    if not source_dir.is_dir():
        raise RuntimeError(f"--init-manifest needs a folder as --source: {source_dir}")
    manifest_path = manifest_path.expanduser()
    pages = discover_markdown(source_dir)
    if not pages:
        raise RuntimeError(f"no markdown files found under {source_dir}")

    rows: list[tuple[str, str, str, int]] = []
    counters: dict[str, int] = {}
    for page in pages:
        section = page.parts[0] if len(page.parts) > 1 else ""
        counters[section] = counters.get(section, 0) + 1
        source_ref = posixpath.relpath(
            (source_dir / page).resolve(strict=False).as_posix(),
            start=manifest_path.parent.resolve(strict=False).as_posix(),
        )
        rows.append((source_ref, _first_heading(source_dir / page), section, counters[section]))

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(MANIFEST_COLUMNS)
        writer.writerows(rows)
    log(
        f"[md-site] wrote {manifest_path} with {len(rows)} row(s); "
        "edit title/section/order, then rebuild with --manifest"
    )
    return len(rows)


def _slug(text: str) -> str:
    """Filesystem-safe route segment that keeps non-Latin words readable.

    CJK titles and sections must survive: stripping to ASCII collapses them to
    one placeholder, which silently merges different sections into the same
    route. ``\\w`` under re.UNICODE keeps letters/digits from any script.
    """
    slug = re.sub(r"\s+", "-", text.strip())
    slug = re.sub(r"[^\w.-]+", "-", slug, flags=re.UNICODE)
    slug = re.sub(r"-{2,}", "-", slug).strip("-.")
    return slug.lower() or "page"


def stage_manifest(entries: list[ManifestEntry], staged_dir: Path, *, title: str) -> list[Path]:
    """Copy manifest sources into ``staged_dir``, grouped by section, and index them."""
    used: set[str] = set()
    routes: list[tuple[ManifestEntry, Path]] = []
    for entry in entries:
        parent = Path(_slug(entry.section)) if entry.section else Path()
        stem = _slug(entry.title if entry.title != entry.source.stem else entry.source.stem)
        route = parent / f"{stem}.md"
        suffix = 2
        while route.as_posix() in used:
            route = parent / f"{stem}-{suffix}.md"
            suffix += 1
        used.add(route.as_posix())
        destination = staged_dir / route
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(entry.source, destination)
        # Bring each document's sibling folders (images and the like) along.
        for sibling in sorted(entry.source.parent.iterdir()):
            if sibling.is_dir() and not _is_skipped_dir(sibling):
                shutil.copytree(sibling, destination.parent / sibling.name, dirs_exist_ok=True)
        routes.append((entry, route))

    lines = [f"# {title}", ""]
    current_section = None
    for entry, route in routes:
        if entry.section != current_section:
            current_section = entry.section
            if current_section:
                lines += [f"## {current_section}", ""]
        lines.append(f"- [{entry.title}]({route.as_posix()})")
    lines.append("")

    grouped: dict[str, list[Path]] = {}
    for entry, route in routes:
        grouped.setdefault(entry.section, []).append(route)
    for section, section_routes in grouped.items():
        lines += [_TOCTREE_FENCE, ":maxdepth: 2", ":hidden:", ""]
        if section:
            lines.insert(len(lines) - 1, f":caption: {section}")
        lines += [route.with_suffix("").as_posix() for route in section_routes]
        lines += ["```", ""]
    (staged_dir / f"{_ROOT_DOC}.md").write_text("\n".join(lines), encoding="utf-8")
    return [route for _entry, route in routes]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=Path, help="A .md file, or a folder of .md files")
    group.add_argument(
        "--manifest",
        type=Path,
        help=f"Batch CSV inventory with columns: {', '.join(MANIFEST_COLUMNS)} (only 'source' is required)",
    )
    parser.add_argument(
        "--init-manifest",
        default=None,
        type=Path,
        help="Scaffold a manifest CSV from --source and exit (title from first heading, section from subfolder)",
    )
    parser.add_argument("--output-dir", type=Path, help="Where to write the static site")
    parser.add_argument(
        "--to-intermediate",
        default=None,
        type=Path,
        help=(
            "Stage 2 of the pipeline: write the converted intermediate Markdown here "
            "(component directives, assets alongside) instead of building. Review or "
            "correct it, then render it with --source."
        ),
    )
    parser.add_argument("--title", default=None, help="Site title (default: source name)")
    parser.add_argument("--assets", default=None, type=Path, help="Single-file mode: folder of images to copy alongside")
    parser.add_argument("--work-dir", default=None, type=Path, help="Keep the staged Sphinx source here (for debugging)")
    parser.add_argument("--stylesheet", default=None, type=Path, help="Override the manual stylesheet")
    parser.add_argument("--strict", action="store_true", help="Treat Sphinx warnings as errors")
    parser.add_argument(
        "--keep-image-refs",
        action="store_true",
        help="Do not repoint image references that fail to resolve in the staged tree",
    )
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="Fetch http(s) image references into the site so it is self-contained (network access)",
    )
    parser.add_argument(
        "--keep-tables",
        action="store_true",
        help="Do not upgrade headerless pipe tables to the manual's table markup",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.init_manifest is not None:
        if args.source is None:
            raise RuntimeError("--init-manifest requires --source <folder>")
        write_manifest_scaffold(args.source, args.init_manifest)
        return 0
    if args.output_dir is None and args.to_intermediate is None:
        raise RuntimeError(
            "pass --output-dir to build a site, or --to-intermediate to write the converted Markdown"
        )
    render_markdown_site(
        source=args.source,
        manifest=args.manifest,
        output_dir=args.output_dir,
        normalize_images=not args.keep_image_refs,
        upgrade_tables=not args.keep_tables,
        download_images=args.download_images,
        intermediate_dir=args.to_intermediate,
        title=args.title,
        assets_dir=args.assets,
        work_dir=args.work_dir,
        stylesheet=args.stylesheet,
        strict=args.strict,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
