"""Raw-LaTeX macro decoding for the IDML prose extractor.

Owns the ``\\HB*`` component-macro vocabulary (``_MACROS``) and its
brace-aware decoder. Split out of ``tools/idml_rst_extract.py`` as a pure
ownership move: the RST-side parser stays in the host and calls
``_extract_raw_latex`` exactly as before. Extending the vocabulary means a
``_MACROS`` row plus a renderer registration — parity with the component
registry is pinned by ``tests/test_idml_components.py``.
"""
from __future__ import annotations

import json
import re

try:
    from tools.component_specs.adapters import idml_notice_payload_from_legacy
    from tools.idml.data_components import is_data_plumbing, parse_data_component
    from tools.idml.extract_contract import ExtractResult
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from component_specs.adapters import idml_notice_payload_from_legacy  # type: ignore
    from idml.data_components import is_data_plumbing, parse_data_component  # type: ignore
    from idml.extract_contract import ExtractResult  # type: ignore

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
    ("\\safetywarning", 1, "safetywarning"),
    ("\\HBSafetyInstruction", 1, "safetyinstruction"),
    ("\\HBWarningLeadBlock", 2, "warninglead"),
    ("\\HBDangerBlock", 3, "labelled"),
    ("\\HBNoticeBlock", 4, "noticed"),   # [kind]{label}{p}{s} — optional arg handled below
    ("\\HBNoteBlock", 2, "note"),
    ("\\HBTipBlock", 2, "tip"),
    ("\\HBCautionBlock", 2, "caution"),
    ("\\HBFccBlock", 2, "bodies"),
    ("\\HBLangTagLine", 2, "langtag"),
    ("\\HBInBoxThree", 6, "inbox"),
    ("\\section", 1, "h1x"),
    ("\\safetysubbar", 1, "h2"),
    ("\\safetylead", 1, "safetylead"),
    # JE-2000E-era page macros
    ("\\HBPageBreak", 1, "pagebreak"),
    ("\\HBAppStep", 2, "h2num"),
    ("\\HBAppBody", 1, "body"),
    ("\\HBAppAsset", 3, "image1"),
    ("\\HBAppNotice", 2, "note"),
)


def _extract_boxed_intro(body: str) -> list[tuple[str, str]] | None:
    """Decode a plain title bar plus paragraphs, never an arbitrary TeX box.

    Match the entire block before emitting anything. In particular, options
    such as ``title``/``overlay`` and unknown inline commands can carry content
    and must stay visible to the skipped-raw diagnostic.
    """
    plain = r"(?:\\[%&#_{}]|[^\\{}%$&#_^~])+"
    match = re.fullmatch(
        r"\s*\\par\s*\\noindent\s*\\begin\{tcolorbox\}\[(?P<options>[^\[\]]*)\]"
        r"\s*\{\\color\{white\}\\bfseries\s+(?P<title>" + plain + r")\}"
        r"\s*\\end\{tcolorbox\}(?P<body>.*)",
        body, re.DOTALL,
    )
    if match is None:
        return None
    layout_keys = {
        "colback", "colframe", "arc", "boxrule", "boxsep", "left", "right",
        "top", "bottom", "width", "before skip", "after skip",
    }
    for option in match["options"].split(","):
        key, separator, value = option.strip().partition("=")
        if not separator or key.strip() not in layout_keys or not re.fullmatch(
            r"[\w. +\-]+|(?:[\d.]+)?\\textwidth", value.strip(),
        ):
            return None
    paragraphs = re.split(r"\\par\s*\\noindent\s*", match["body"])
    if paragraphs[0].strip() or len(paragraphs) < 2:
        return None
    texts = [match["title"], *paragraphs[1:]]
    if any(not text.strip() or not re.fullmatch(plain, text) for text in texts):
        return None
    texts = [re.sub(r"\\([%&#_{}])", r"\1", text).strip() for text in texts]
    return [("h2", texts[0]), *(("body", text) for text in texts[1:])]


def _extract_raw_latex(body: str, result: ExtractResult) -> None:
    stripped_body = body.strip()
    if r"\begin{tcolorbox}" in body:
        intro = _extract_boxed_intro(body)
        if intro is not None:
            result.blocks.extend(intro)
        else:
            result.skipped_raw += 1
        return
    data_payload = parse_data_component(body)
    if data_payload is not None:
        result.blocks.append(("data", json.dumps(data_payload, ensure_ascii=False)))
        return
    if stripped_body == r"\begin{safetytwocol}":
        result.twocol = True
        result.blocks.append(("layout", "twocol_start"))
        return
    if stripped_body == r"\end{safetytwocol}":
        result.blocks.append(("layout", "twocol_end"))
        return
    if stripped_body in {
        r"\begin{safetysinglecol}",
        r"\end{safetysinglecol}",
    }:
        # IDML prose is single-column by default. These LaTeX-only wrappers
        # carry no content or geometry into the IDML adapter.
        return
    if "safetytwocol" in body:
        result.twocol = True
    # HBLcdModeTable environment: structured mode/action/description groups
    mt = re.search(r"\\begin\{HBLcdModeTable\}", body)
    if mt:
        import json as _json
        j = mt.end()
        img_args, j = _read_braced_args(body, j, 1)
        groups = []
        for macro in ("\\HBLcdModeFirstGroup", "\\HBLcdModeSecondGroup"):
            pos = body.find(macro + "{", j)
            if pos == -1:
                continue
            args, _ = _read_braced_args(body, pos + len(macro), 7)
            args = [_detex(a) for a in args]
            if len(args) == 7:
                groups.append({"state": args[0],
                               "actions": [[args[1], args[2]],
                                           [args[3], args[4]],
                                           [args[5], args[6]]]})
        if groups:
            result.blocks.append(("component", _json.dumps(
                {"kind": "lcdmode",
                 "img": img_args[0] if img_args else "",
                 "groups": groups}, ensure_ascii=False)))
            return

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
            if k == -1:
                # truncated/malformed optional arg (no closing ]): skip this
                # macro occurrence so the scan makes forward progress. Without
                # this, k=-1 -> j=0 -> _read_braced_args returns 0 -> i=0 and
                # the loop re-finds the same macro forever (hang).
                i = j
                continue
            optional = body[j + 1:k]
            j = k + 1
        args, j = _read_braced_args(body, j, argc if macro != "\\HBNoticeBlock" else 3)
        args = [_detex(a) for a in args]
        import json as _json
        if kind == "safetywarning" and args:
            payload = {"kind": "safetywarning", "texts": [args[0]]}
            if optional.strip():
                payload["label"] = _detex(optional)
            result.blocks.append(("component", _json.dumps(
                payload,
                ensure_ascii=False)))
        elif kind == "safetyinstruction" and args:
            result.blocks.append(("component", _json.dumps(
                {"kind": "safetyinstruction", "texts": [args[0]]},
                ensure_ascii=False)))
        elif kind == "warninglead" and args:
            result.blocks.append(("component", _json.dumps(
                {"kind": "warninglead", "label": args[0],
                 "texts": [a for a in args[1:] if a]}, ensure_ascii=False)))
        elif kind == "labelled" and args:
            result.blocks.append(("component", _json.dumps(
                {"kind": "warnbox", "label": args[0],
                 "texts": [a for a in args[1:] if a]}, ensure_ascii=False)))
        elif kind == "noticed" and args:
            label = args[0].strip()
            if not label:
                raise ValueError("notice label is required from source RST")
            result.blocks.append(("component", _json.dumps(
                idml_notice_payload_from_legacy(
                    {"kind": "notice", "label": label,
                     "variant": optional or "notice",
                     "texts": [a for a in args[1:] if a]},
                    source_ref="rst:raw-latex:HBNoticeBlock",
                ), ensure_ascii=False)))
        elif kind in {"note", "tip", "caution"} and args:
            result.blocks.append(("component", _json.dumps(
                idml_notice_payload_from_legacy(
                    {"kind": "notice", "label": args[0], "variant": kind,
                     "texts": [a for a in args[1:] if a]},
                    source_ref=f"rst:raw-latex:{macro[1:]}",
                ), ensure_ascii=False)))
        elif kind == "bodies":
            result.blocks.append(("component", _json.dumps(
                {"kind": "fcc", "texts": [a for a in args if a]}, ensure_ascii=False)))
        elif kind == "langtag" and len(args) == 2:
            result.blocks.append(("component", _json.dumps(
                {"kind": "langtag", "lang": args[0], "texts": [args[1]]},
                ensure_ascii=False)))
        elif kind == "inbox" and len(args) == 6:
            items = [{"img": args[i], "label": args[i + 1]} for i in range(0, 6, 2)]
            result.blocks.append(("component", _json.dumps({"kind": "inbox", "items": items}, ensure_ascii=False)))
        elif kind == "h1x" and args:
            result.blocks.append(("h1", args[0]))
        elif kind == "h2" and args:
            result.blocks.append(("h2", args[0]))
        elif kind == "h2num" and len(args) == 2:
            result.blocks.append(("h2", f"{args[0]} {args[1]}".strip()))
        elif kind == "image1" and args:
            result.blocks.append(("image", args[0]))
        elif kind in {"body", "safetylead"} and args:
            result.blocks.append((kind, args[0]))
        elif kind == "pagebreak" and consumed_any:
            result.blocks.append(("layout", "page_break"))
        consumed_any = True
        i = j
    if not consumed_any and body.strip():
        # raw content with no recognizable macro (pure latex plumbing like
        # \HBApplyLang, tabular constructs...) — plumbing is silent, real
        # constructs count as skipped.
        stripped = re.sub(r"\\HBApplyLang\{[^}]*\}", "", body).strip()
        if stripped and not is_data_plumbing(stripped) \
                and not stripped.startswith("\\begin{safetytwocol}") \
                and not stripped.startswith("\\end{safetytwocol}"):
            result.skipped_raw += 1
