"""Prose extraction for the IDML exporter (M4b).

Parses the *prepared bundle* rst pages (docs/_build/<model>/<region>/<lang>/
rst/page/*.rst — variables already substituted, same source the PDF build
consumes) into a flat list of blocks the IDML writer can emit:

    ("h1"|"h2"|"h3"|"body"|"list", text)
    ("image", bundle-relative-path)

Design decisions:
- ``.. only:: latex`` bodies are taken (they carry the component macro
  calls); ``.. only:: not latex / html`` bodies are skipped — same branch
  selection as the PDF build.
- Known raw-latex component macros are *textualized* via their known
  signatures (\\safetywarning{...}, \\HBNoticeBlock{...}{...}{...} etc.) so
  designers get editable text instead of holes. Unknown raw content is
  counted and dropped (reported by the caller).
- This is intentionally a small hand-rolled parser for the bundle's rst
  subset, not docutils: the bundle uses sphinx-only directives (only) and
  raw component calls that docutils would reject or bury.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

Block = tuple[str, str]


@dataclass
class ExtractResult:
    blocks: list[Block] = field(default_factory=list)
    skipped_raw: int = 0
    twocol: bool = False  # page contains a safetytwocol region


# ---------------------------------------------------------------------------
# brace-aware macro argument extraction
# ---------------------------------------------------------------------------

def _read_braced_args(text: str, start: int, count: int) -> tuple[list[str], int]:
    """Read ``count`` {...} groups starting at ``start``; returns (args, end)."""
    args: list[str] = []
    i = start
    for _ in range(count):
        while i < len(text) and text[i] in " \t\n%":
            i += 1
        if i >= len(text) or text[i] != "{":
            break
        depth = 0
        j = i
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        args.append(text[i + 1:j])
        i = j + 1
    return args, i


def _detex(s: str) -> str:
    """Strip the latex-isms our own macros/templates use."""
    # line-continuation comments: an unescaped % swallows the rest of the
    # source line INCLUDING the newline and the next line's indentation
    # (latex semantics), so wrapped macro arguments join seamlessly
    s = re.sub(r"(?<!\\)%[^\n]*\n?", "", s)
    s = s.replace("\\par", "\n").replace("\\textbullet", "•")
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\text(?:sub|super)script\{([^{}]*)\}", r"\1", s)
    s = s.replace("~", " ").replace("\\&", "&").replace("\\%", "%")
    s = re.sub(r"\\[a-zA-Z@]+", " ", s)  # any leftover control words
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"[ \t]+", " ", s).strip()


# ---------------------------------------------------------------------------
# raw latex block -> blocks
# ---------------------------------------------------------------------------

_MACROS: tuple[tuple[str, int, str], ...] = (
    # (macro, arg count, kind)  kind: label1 = arg0 is a heading, rest body
    ("\\safetywarning", 1, "warnbox"),
    ("\\HBWarningLeadBlock", 2, "labelled"),
    ("\\HBDangerBlock", 3, "labelled"),
    ("\\HBNoticeBlock", 4, "noticed"),   # [kind]{label}{p}{s} — optional arg handled below
    ("\\HBNoteBlock", 2, "labelled"),
    ("\\HBTipBlock", 2, "labelled"),
    ("\\HBFccBlock", 2, "bodies"),
    ("\\HBLangTagLine", 2, "langtag"),
    ("\\HBInBoxThree", 6, "inbox"),
    ("\\section", 1, "h1x"),
    ("\\safetysubbar", 1, "h2"),
    ("\\safetylead", 1, "body"),
)


def _extract_raw_latex(body: str, result: ExtractResult) -> None:
    if "safetytwocol" in body:
        result.twocol = True
    i = 0
    consumed_any = False
    while i < len(body):
        nxt = None
        for macro, argc, kind in _MACROS:
            pos = body.find(macro + "{", i)
            # also allow optional [arg] form for HBNoticeBlock
            pos_opt = body.find(macro + "[", i)
            if pos_opt != -1 and (pos == -1 or pos_opt < pos):
                pos = pos_opt
            if pos != -1 and (nxt is None or pos < nxt[0]):
                nxt = (pos, macro, argc, kind)
        if nxt is None:
            break
        pos, macro, argc, kind = nxt
        j = pos + len(macro)
        optional = ""
        if j < len(body) and body[j] == "[":
            k = body.find("]", j)
            optional = body[j + 1:k]
            j = k + 1
        args, j = _read_braced_args(body, j, argc if macro != "\\HBNoticeBlock" else 3)
        args = [_detex(a) for a in args]
        import json as _json
        if kind == "warnbox" and args:
            result.blocks.append(("component", _json.dumps(
                {"kind": "warnbox", "label": "WARNING", "texts": [args[0]]},
                ensure_ascii=False)))
        elif kind == "labelled" and args:
            result.blocks.append(("component", _json.dumps(
                {"kind": "warnbox", "label": args[0],
                 "texts": [a for a in args[1:] if a]}, ensure_ascii=False)))
        elif kind == "noticed" and args:
            result.blocks.append(("component", _json.dumps(
                {"kind": "notice", "label": args[0] or optional.upper() or "NOTICE",
                 "texts": [a for a in args[1:] if a]}, ensure_ascii=False)))
        elif kind == "bodies":
            result.blocks.append(("component", _json.dumps(
                {"kind": "fcc", "texts": [a for a in args if a]}, ensure_ascii=False)))
        elif kind == "langtag" and len(args) == 2:
            result.blocks.append(("h2", f"[{args[0]}] {args[1]}"))
        elif kind == "inbox" and len(args) == 6:
            result.blocks.append(("component", _json.dumps(
                {"kind": "inbox",
                 "items": [{"img": i, "label": l}
                           for i, l in zip(args[0::2], args[1::2])]},
                ensure_ascii=False)))
        elif kind == "h1x" and args:
            result.blocks.append(("h1", args[0]))
        elif kind == "h2" and args:
            result.blocks.append(("h2", args[0]))
        elif kind == "body" and args:
            result.blocks.append(("body", args[0]))
        consumed_any = True
        i = j
    if not consumed_any and body.strip():
        # raw content with no recognizable macro (pure latex plumbing like
        # \HBApplyLang, tabular constructs...) — plumbing is silent, real
        # constructs count as skipped.
        stripped = re.sub(r"\\HBApplyLang\{[^}]*\}", "", body).strip()
        if stripped and not stripped.startswith("\\begin{safetytwocol}") \
                and not stripped.startswith("\\end{safetytwocol}"):
            result.skipped_raw += 1


# ---------------------------------------------------------------------------
# page parser
# ---------------------------------------------------------------------------

_UNDERLINES = {"=": "h1", "-": "h2", "~": "h3", "^": "h3"}


def _only_matches(expr: str, tags: set[str]) -> bool:
    """Evaluate a sphinx ``only::`` expression against active tags.

    Supports the bundle's vocabulary: bare tags, ``and``, and ``not``.
    """
    for clause in expr.split(" and "):
        clause = clause.strip()
        if clause.startswith("not "):
            if clause[4:].strip() in tags:
                return False
        elif clause and clause not in tags:
            return False
    return True


def extract_page(path: Path, tags: set[str] | None = None) -> ExtractResult:
    tags = tags if tags is not None else {"latex"}
    result = ExtractResult()
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    n = len(lines)

    def indented_body(start: int, base_indent: int) -> tuple[list[str], int]:
        out: list[str] = []
        k = start
        while k < n:
            line = lines[k]
            if not line.strip():
                out.append("")
                k += 1
                continue
            ind = len(line) - len(line.lstrip())
            if ind <= base_indent:
                break
            out.append(line)
            k += 1
        while out and not out[-1].strip():
            out.pop()
        return out, k

    while i < n:
        line = lines[i]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        # directives
        m = re.match(r"\.\.\s+(only|raw|image|list-table)::\s*(.*)", stripped)
        if m and indent == 0:
            directive, arg = m.group(1), m.group(2).strip()
            body, i2 = indented_body(i + 1, indent)
            if directive == "raw" and arg == "latex":
                _extract_raw_latex("\n".join(body), result)
            elif directive == "only":
                if _only_matches(arg, tags):
                    # re-parse the body as page content (dedented)
                    dedent = min((len(b) - len(b.lstrip()) for b in body if b.strip()), default=0)
                    sub = "\n".join(b[dedent:] for b in body)
                    inner = _parse_text(sub, tags)
                    result.blocks.extend(inner.blocks)
                    result.skipped_raw += inner.skipped_raw
                    result.twocol = result.twocol or inner.twocol
                # non-matching branches are the PDF-skipped side: drop
            elif directive == "image":
                result.blocks.append(("image", arg))
            elif directive == "list-table":
                result.skipped_raw += 1  # tables are covered by data stories
            i = i2
            continue

        # section titles (underline on the next line)
        if stripped and i + 1 < n:
            under = lines[i + 1].strip()
            if under and len(under) >= max(3, len(stripped) - 2) \
                    and len(set(under)) == 1 and under[0] in _UNDERLINES:
                result.blocks.append((_UNDERLINES[under[0]], stripped))
                i += 2
                continue

        # rst grid tables (+---+ borders) -> ("table", json rows)
        if re.match(r"\+-[-+]*-\+$", stripped):
            import json as _json
            grid = [line.rstrip()]
            k = i + 1
            while k < n and (lines[k].strip().startswith("|") or
                             re.match(r"\+[=+-]+\+$", lines[k].strip())):
                grid.append(lines[k].rstrip())
                k += 1
            rows = _parse_grid_table(grid)
            if rows:
                result.blocks.append(("table", _json.dumps(rows, ensure_ascii=False)))
                i = k
                continue

        # line blocks
        if stripped.startswith("| "):
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            text = "\n".join(b for b in buf if b)
            if text:
                result.blocks.append(("body", text))
            continue

        # bullet lists
        if stripped.startswith("- "):
            item = [stripped[2:]]
            i += 1
            while i < n and lines[i].strip() and not lines[i].strip().startswith("- ") \
                    and (len(lines[i]) - len(lines[i].lstrip())) >= 2:
                item.append(lines[i].strip())
                i += 1
            result.blocks.append(("list", "• " + " ".join(item)))
            continue

        # plain paragraph
        if stripped and not stripped.startswith(".."):
            para = [stripped]
            i += 1
            while i < n and lines[i].strip() and not lines[i].strip().startswith(("|", "- ", "..")):
                nxt_line = lines[i].strip()
                if i + 1 < n:
                    under = lines[i + 1].strip()
                    if under and len(set(under)) == 1 and under[0] in _UNDERLINES:
                        break
                para.append(nxt_line)
                i += 1
            result.blocks.append(("body", " ".join(para)))
            continue

        i += 1
    result.blocks = [(k, t.replace("\\*", "*")) for k, t in result.blocks if t.strip()]
    return result


def _parse_text(text: str, tags: set[str] | None = None) -> ExtractResult:
    """Parse a dedented rst fragment (used for matching only:: bodies)."""
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(suffix=".rst")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        return extract_page(Path(tmp), tags)
    finally:
        os.unlink(tmp)


def bundle_page_order(bundle_root: Path) -> list[Path]:
    """Page files in reading order, from the bundle index toctree/includes."""
    index = bundle_root / "index.rst"
    order: list[Path] = []
    if index.exists():
        for m in re.finditer(r"\.\.\s+include::\s+(page/\S+)", index.read_text(encoding="utf-8")):
            p = bundle_root / m.group(1)
            if p.exists():
                order.append(p)
    return order

def _parse_grid_table(grid: list[str]) -> list[list[str]]:
    """Parse an rst grid table block into row cell-text lists."""
    border = grid[0]
    cols = [m.start() for m in re.finditer(r"\+", border)]
    if len(cols) < 2:
        return []
    rows: list[list[str]] = []
    current: list[list[str]] | None = None
    for line in grid:
        stripped = line.strip()
        if re.match(r"\+[=+-]+\+$", stripped):
            if current is not None:
                rows.append([" ".join(part for part in cell if part).strip()
                             for cell in current])
            current = None
            continue
        if not stripped.startswith("|"):
            continue
        if current is None:
            current = [[] for _ in range(len(cols) - 1)]
        for ci in range(len(cols) - 1):
            a, b = cols[ci] + 1, cols[ci + 1]
            seg = line[a:b].strip() if a < len(line) else ""
            current[ci].append(seg)
    return [r for r in rows if any(r)]
