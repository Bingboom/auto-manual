"""Compile a sideload bundle's semantic directives into self-contained markup.

``build.py web-sideload`` stages Markdown that Read the Docs rebuilds with
``-D extensions=myst_parser,tools.rtd_portal`` (see ``.readthedocs.yaml``).
That ``-D`` *overrides* whatever ``conf.py`` declares, and
``readthedocs_source.assemble_rtd_source`` strips the bundle's ``conf.py``
outright, so no configuration change can ever put
``tools.manual_md_directives`` on the published build. A staged ``.md`` must
therefore already carry the component markup.

That leaves two authoring planes, and this module is the compiler between
them:

* **Author plane** — prose plus the eight semantic directives
  (``{callout}``, ``{spec-table}``, ...). This is the only plane a human
  writes, and it is the single source of truth for component markup.
* **Staged plane** — the same document with every directive replaced by the
  exact HTML the directive layer emits. Machine-produced, never hand-written.

Expansion runs one throwaway Sphinx HTML build with the real directive
extension loaded and recovers each block's rendered markup from the output.
Nothing here re-implements a component: the directive layer, the emitters and
``web_manual.css`` are untouched, and this module never invents styling. The
web adapter binds classes only (``tools.component_specs.adapters``'
``web_callout_classes``, against ``word_callout_markup``'s inline styles for
the print plane), so class-only output is the correct web form and the shared
stylesheet supplies the look.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from tools.manual_md_directives import DIRECTIVES

#: Sentinel comments wrapped around each compiled block. They exist only
#: inside the throwaway build output and never reach a staged file.
_SENTINEL_PREFIX = "AMX"
_SENTINEL_START = f"<!--{_SENTINEL_PREFIX}:{{docname}}:{{lineno}}:s-->"
_SENTINEL_END = f"<!--{_SENTINEL_PREFIX}:{{docname}}:{{lineno}}:e-->"
_SENTINEL_RE = re.compile(
    rf"<!--{_SENTINEL_PREFIX}:(?P<docname>[^:]*):(?P<lineno>\d+):s-->"
    rf"(?P<html>.*?)"
    rf"<!--{_SENTINEL_PREFIX}:(?P=docname):(?P=lineno):e-->",
    re.S,
)

#: The three fence spellings MyST accepts for a directive block.
_FENCE_CHARS = ("`", "~", ":")
_OPEN_RE = re.compile(
    r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,}|:{3,})\s*\{(?P<name>[A-Za-z0-9_-]+)\}"
)


class SideloadExpansionError(RuntimeError):
    """A sideload bundle cannot be compiled into staged markup."""


# --------------------------------------------------------------------------
# Author-plane lint
# --------------------------------------------------------------------------

#: A class token owned by the component layer. Any prefix match is banned in
#: the author plane; the rule (not a hand-kept list) is what keeps this from
#: drifting as components are added.
_BANNED_CLASS_PREFIXES = ("hb-",)
_BANNED_CLASS_EXACT = {
    "manual-callout-table": "callout",
    "manual-callout-label": "callout",
    "manual-callout-body": "callout",
    "manual-spec-table": "spec-table",
    "manual-spec-label": "spec-table",
    "manual-spec-value": "spec-table",
    "manual-table": "manual-table",
}
#: Which directive owns each ``hb-`` family, so the error can name the fix.
_HB_FAMILY_OWNER = (
    ("hb-spec-", "spec-table"),
    ("hb-troubleshooting-", "troubleshooting"),
    ("hb-lcd-mode-", "lcd-mode"),
    ("hb-lcd-", "lcd-icons"),
    ("hb-symbol-", "symbols"),
    ("hb-auto-resume-", "comparison"),
)
_CLASS_ATTR_RE = re.compile(r"""class\s*=\s*["']([^"']*)["']""", re.I)
_STYLE_ATTR_RE = re.compile(r"""style\s*=\s*["'][^"']*["']""", re.I)


def _owning_directive(token: str) -> str:
    if token in _BANNED_CLASS_EXACT:
        return _BANNED_CLASS_EXACT[token]
    for prefix, owner in _HB_FAMILY_OWNER:
        if token.startswith(prefix):
            return owner
    return "a component"


def lint_author_markdown(text: str, *, label: str) -> list[str]:
    """Reject hand-written component markup in an author-plane document.

    The author plane must hold prose and directives only. Hand-written
    component HTML is the exact defect this lane was rebuilt to remove: it
    renders as an unstyled shell because it cannot reproduce the structure the
    stylesheet keys off (``colgroup``, ``scope``, rowspans, cell classes).
    Inline styles are refused for the same reason -- the web plane is
    class-only by adapter contract, so an inline style is always either a
    hand-written component or a private override of the shared stylesheet.
    """

    problems: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for match in _CLASS_ATTR_RE.finditer(line):
            for token in match.group(1).split():
                banned = token in _BANNED_CLASS_EXACT or any(
                    token.startswith(prefix) for prefix in _BANNED_CLASS_PREFIXES
                )
                if not banned:
                    continue
                owner = _owning_directive(token)
                problems.append(
                    f"{label}:{number}: hand-written component class {token!r}; "
                    f"declare it with the ``{{{owner}}}`` directive instead -- "
                    "component markup has exactly one source "
                    "(tools/manual_md_directives.py)"
                )
        if _STYLE_ATTR_RE.search(line):
            problems.append(
                f"{label}:{number}: inline style attribute; the web plane is "
                "class-only by adapter contract and the shared stylesheet "
                "(docs/renderers/contracts/web_manual.css) owns the look"
            )
    return problems


# --------------------------------------------------------------------------
# Fence scanning
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DirectiveBlock:
    """One directive fence located in an author document."""

    name: str
    start_line: int  # 1-based, the opening fence line
    end_line: int  # 1-based, the closing fence line


def scan_directive_blocks(text: str) -> list[DirectiveBlock]:
    """Locate every *component directive* fence, honouring MyST nesting.

    Only the eight component directives are matched -- a ``{toctree}``, a
    ``{note}`` or a plain code fence is left alone. Closing follows MyST's
    rule that a closer must repeat the opening character at least as many
    times, which is what lets a ``{callout}`` body (parsed as full Markdown)
    contain its own shorter code fence without ending the block early.
    """

    lines = text.splitlines()
    blocks: list[DirectiveBlock] = []
    index = 0
    while index < len(lines):
        match = _OPEN_RE.match(lines[index])
        if not match or match.group("name") not in DIRECTIVES:
            index += 1
            continue
        fence = match.group("fence")
        char, width = fence[0], len(fence)
        closer = re.compile(rf"^\s*{re.escape(char)}{{{width},}}\s*$")
        cursor = index + 1
        while cursor < len(lines) and not closer.match(lines[cursor]):
            cursor += 1
        if cursor >= len(lines):
            raise SideloadExpansionError(
                f"line {index + 1}: unterminated ``{{{match.group('name')}}}`` "
                f"directive -- no closing {char * width!r} fence"
            )
        blocks.append(
            DirectiveBlock(
                name=match.group("name"), start_line=index + 1, end_line=cursor + 1
            )
        )
        index = cursor + 1
    return blocks


# --------------------------------------------------------------------------
# Sphinx extension: wrap each directive in recoverable sentinels
# --------------------------------------------------------------------------


def _wrapped(name: str, base: type) -> type:
    from docutils import nodes

    class _Sentineled(base):  # type: ignore[valid-type, misc]
        def run(self) -> list[Any]:
            docname = str(getattr(self.env, "docname", ""))
            marks = {"docname": docname, "lineno": self.lineno}
            start = nodes.raw("", _SENTINEL_START.format(**marks), format="html")
            end = nodes.raw("", _SENTINEL_END.format(**marks), format="html")
            return [start, *super().run(), end]

    _Sentineled.__name__ = f"Sentineled{base.__name__}"
    _Sentineled.__doc__ = base.__doc__
    return _Sentineled


def setup(app: Any) -> dict[str, Any]:
    """Re-register every component directive with sentinel bracketing.

    Loaded *after* ``tools.manual_md_directives`` so the override takes. The
    wrapped class defers entirely to the original ``run()``; the callout's
    markup is still produced by the HTML writer at departure time, which is
    exactly why the sentinels are recovered from the built page rather than
    from the directive's return value.
    """

    for name, directive in DIRECTIVES.items():
        app.add_directive(name, _wrapped(name, directive), override=True)
    return {
        "version": "1.0",
        "env_version": 1,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


# --------------------------------------------------------------------------
# Expansion driver
# --------------------------------------------------------------------------

_CONF_APPENDIX = """

# --- appended by tools.web_sideload_expand (throwaway expansion build) ---
import sys as _sys
if {repo_root!r} not in _sys.path:
    _sys.path.insert(0, {repo_root!r})
try:
    extensions
except NameError:
    extensions = []
extensions = list(dict.fromkeys([
    *extensions, "myst_parser",
    "tools.manual_md_directives", "tools.web_sideload_expand",
]))
"""


def _markdown_files(md_dir: Path) -> list[Path]:
    return sorted(path for path in md_dir.rglob("*.md") if path.is_file())


def _run_author_build(*, md_dir: Path, repo_root: Path, out_dir: Path) -> Path:
    """Build the author bundle with the directive layer loaded (stage 1)."""

    source = out_dir / "source"
    shutil.copytree(md_dir, source)
    conf = source / "conf.py"
    if not conf.is_file():
        raise SideloadExpansionError(
            f"sideload bundle has no conf.py: {md_dir}"
        )
    with conf.open("a", encoding="utf-8") as handle:
        handle.write(_CONF_APPENDIX.format(repo_root=str(repo_root)))
    html_out = out_dir / "html"
    proc = subprocess.run(
        [sys.executable, "-m", "sphinx", "-W", "-b", "html", str(source), str(html_out)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise SideloadExpansionError(
            "author-mode verification failed (sphinx -W -b html with "
            f"tools.manual_md_directives loaded): {detail[-4000:]}"
        )
    return html_out


def _captured_blocks(html_dir: Path) -> dict[tuple[str, int], str]:
    captured: dict[tuple[str, int], str] = {}
    for page in sorted(html_dir.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        for match in _SENTINEL_RE.finditer(text):
            key = (match.group("docname"), int(match.group("lineno")))
            captured[key] = match.group("html").strip()
    return captured


def _docname(md_path: Path, md_dir: Path) -> str:
    return md_path.relative_to(md_dir).with_suffix("").as_posix()


def _rewrite(text: str, blocks: Iterable[DirectiveBlock], rendered: dict[int, str]) -> str:
    lines = text.splitlines()
    out: list[str] = []
    cursor = 0
    for block in sorted(blocks, key=lambda item: item.start_line):
        out.extend(lines[cursor : block.start_line - 1])
        # A component is one HTML block: keep it on a single line so MyST's
        # CommonMark block rules cannot split it on an interior blank line.
        out.append(rendered[block.start_line].replace("\n", " "))
        cursor = block.end_line
    out.extend(lines[cursor:])
    return "\n".join(out) + "\n"


def expand_sideload_bundle(*, md_dir: Path, repo_root: Path) -> dict[str, int]:
    """Lint the author plane, compile its directives, and rewrite in place.

    Returns a per-directive count of what was expanded, which the caller uses
    for the staged-product existence check.
    """

    problems: list[str] = []
    for path in _markdown_files(md_dir):
        problems.extend(
            lint_author_markdown(
                path.read_text(encoding="utf-8"), label=str(path.relative_to(md_dir))
            )
        )
    if problems:
        raise SideloadExpansionError(
            "author-plane lint failed -- component markup must be declared, "
            "not hand-written:\n  " + "\n  ".join(problems)
        )

    scanned: dict[Path, list[DirectiveBlock]] = {}
    for path in _markdown_files(md_dir):
        try:
            scanned[path] = scan_directive_blocks(path.read_text(encoding="utf-8"))
        except SideloadExpansionError as exc:
            raise SideloadExpansionError(f"{path.relative_to(md_dir)}: {exc}") from exc
    total_scanned = sum(len(items) for items in scanned.values())
    if not total_scanned:
        # A bundle that declares no components needs no compile step; the
        # staged-plane build still verifies the document as a whole.
        return {}

    temp_dir = Path(tempfile.mkdtemp(prefix="auto-manual-web-sideload-expand-"))
    try:
        html_dir = _run_author_build(
            md_dir=md_dir, repo_root=repo_root, out_dir=temp_dir
        )
        captured = _captured_blocks(html_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Fail closed on any disagreement between what the text says and what the
    # parser actually compiled -- a silent mismatch would stage a half
    # expanded document.
    if len(captured) != total_scanned:
        raise SideloadExpansionError(
            f"directive expansion mismatch: scanned {total_scanned} component "
            f"directive fence(s) but the build compiled {len(captured)}; the "
            "bundle may nest directives or use a fence the scanner and MyST "
            "read differently"
        )

    counts: dict[str, int] = {}
    for path, blocks in scanned.items():
        if not blocks:
            continue
        docname = _docname(path, md_dir)
        rendered: dict[int, str] = {}
        for block in blocks:
            key = (docname, block.start_line)
            if key not in captured:
                raise SideloadExpansionError(
                    f"{path.relative_to(md_dir)}:{block.start_line}: the "
                    f"``{{{block.name}}}`` directive produced no markup"
                )
            rendered[block.start_line] = captured[key]
            counts[block.name] = counts.get(block.name, 0) + 1
        path.write_text(
            _rewrite(path.read_text(encoding="utf-8"), blocks, rendered),
            encoding="utf-8",
        )
    return counts


#: Markup each directive must leave behind, used for the staged existence
#: check. Presence only -- never a styling probe, since the web plane carries
#: no inline styles by adapter contract.
_PRODUCT_MARKERS = {
    "callout": "manual-callout-table",
    "spec-table": "hb-spec-table-composition",
    "troubleshooting": "hb-troubleshooting-composition",
    "lcd-icons": "hb-lcd-table-composition",
    "symbols": "hb-symbol-pair-composition",
    "comparison": "hb-auto-resume-composition",
    "manual-table": "manual-table",
    "lcd-mode": "hb-lcd-mode-composition",
}


def verify_expanded_products(*, md_dir: Path, counts: dict[str, int]) -> None:
    """Every directive type used must have left its component marker behind."""

    staged = "\n".join(
        path.read_text(encoding="utf-8") for path in _markdown_files(md_dir)
    )
    missing = [
        f"``{{{name}}}`` used {used}x but no {_PRODUCT_MARKERS[name]!r} in the staged Markdown"
        for name, used in sorted(counts.items())
        if used and _PRODUCT_MARKERS[name] not in staged
    ]
    if missing:
        raise SideloadExpansionError(
            "expanded bundle is missing component markup:\n  " + "\n  ".join(missing)
        )


__all__ = (
    "DirectiveBlock",
    "SideloadExpansionError",
    "expand_sideload_bundle",
    "lint_author_markdown",
    "scan_directive_blocks",
    "setup",
    "verify_expanded_products",
)
