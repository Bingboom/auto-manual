"""Derive the JS-100I / JP / ja spec-table edition from the released base package.

Run from the repository root:

    python manual_sources/JS-100I/JP/ja/git-20261027-cc8b3421-spec-table/derive_spec_table.py

The released base ``../git-20261026-cc8b3421`` stays immutable. This script
copies its ``source/`` and ``assets/`` trees and ``render.py`` byte-for-byte
(except the base's own ``source/approval.json`` and ``source/differences.md``),
moves the 電気データ table onto the shared spec-table composition, replaces the
table's narrow-screen scroll rule in ``source/presentation.css`` and refreshes
``source_manifest.json``; a second run leaves the tree unchanged. Hand-written
``README.md``, ``source/differences.md`` and (after acceptance)
``source/approval.json`` are not touched. With ``web/ja`` in place it also
writes ``frozen_source_manifest.json`` for ``seal_frozen_web_evidence``.

No copy changes: ``tests/test_js100i_jp_web.py`` proves the rendered visible
copy equals the base edition's.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

PACKAGE = Path(__file__).resolve().parent
BASE = PACKAGE.parent / "git-20261026-cc8b3421"
REPO = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())

CANDIDATE = "review-candidate-no-release-authorization"
APPROVED = "operator-approved-git-only-release"
STATUS = APPROVED
COPIED_ROOTS = ("source", "assets")
COPIED_SCRIPTS = ("render.py",)
SCRIPTS = ("render.py", "derive_spec_table.py")
# The base edition's own acceptance and change record do not carry over.
NOT_COPIED = {"source/approval.json", "source/differences.md"}
SPEC_PAGE = "spec_ja.rst"
TABLE_START = '<h2 id="jp-spec-electrical">電気データ</h2>'
TABLE_END = "</tbody></table></div>"
# (base markup, shared spec-table markup, expected count inside the 電気データ table).
TABLE_EDITS = [
    ('<div class="table-wrapper"><table class="manual-spec-table"><thead>',
     '<figure aria-label="電気データ" class="hb-spec-table-composition">'
     '<table class="manual-spec-table manual-table hb-spec-table">'
     '<colgroup><col class="hb-spec-col-label"/><col/><col/></colgroup><thead>', 1),
    ("<tr><th></th><th>STC<sup>*</sup></th><th>BNPI<sup>*</sup></th></tr>",
     '<tr><th class="hb-spec-label"></th><th class="hb-spec-value">STC<sup>*</sup></th>'
     '<th class="hb-spec-value">BNPI<sup>*</sup></th></tr>', 1),
    ("<tr><th>", '<tr><th class="hb-spec-label" scope="row">', 12),
    ("<td>", '<td class="hb-spec-value">', 10),
    ('<td colspan="2">', '<td class="hb-spec-value" colspan="2">', 7),
    (TABLE_END, "</tbody></table></figure>", 1),
]
CSS_OLD = """/* The three-column 電気データ table scrolls inside its own wrapper on narrow screens. */
#furo-main-content div.table-wrapper { overflow-x: auto; }
"""
CSS_NEW = """/* 電気データ: the STC/BNPI header is bold as printed; the three columns fit narrow screens without scrolling. */
#furo-main-content figure[aria-label="電気データ"] table.hb-spec-table thead .hb-spec-value { font-weight: 700; }
#furo-main-content figure[aria-label="電気データ"] table.hb-spec-table { min-width: 0; }
"""
TABLE_EXCEPTION_REASON = (
    "電気データ STC/BNPI table: three columns with a header row and value cells spanning both conditions; "
    "HB-TABLE-SPEC is a two-column label/value table without header or column spans. It is drawn as the "
    "shared hb-spec-table-composition with the shared hb-spec-* cell classes, like the HB-TABLE-SPEC tables")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def entry(path: Path) -> dict:
    return {"path": path.relative_to(PACKAGE).as_posix(), "size": path.stat().st_size, "sha256": sha256(path)}


def copy_base() -> None:
    for root in COPIED_ROOTS:
        for path in sorted((BASE / root).rglob("*")):
            relative = path.relative_to(BASE).as_posix()
            if path.is_file() and "__pycache__" not in path.parts and relative not in NOT_COPIED:
                target = PACKAGE / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    for name in COPIED_SCRIPTS:
        shutil.copyfile(BASE / name, PACKAGE / name)


def edited_spec_page() -> str:
    """The base spec page with only the 電気データ table moved onto the shared spec-table classes."""
    text = (BASE / "source" / "page" / SPEC_PAGE).read_text(encoding="utf-8")
    if text.count(TABLE_START) != 1:
        raise SystemExit(f"{SPEC_PAGE}: expected the 電気データ heading once")
    start = text.index(TABLE_START)
    end = text.index(TABLE_END, start) + len(TABLE_END)
    table = text[start:end]
    for old, new, count in TABLE_EDITS:
        if table.count(old) != count:
            raise SystemExit(f"{SPEC_PAGE}: expected {old!r} {count}x in the table, found {table.count(old)}")
        table = table.replace(old, new)
    return text[:start] + table + text[end:]


def edited_stylesheet() -> str:
    text = (BASE / "source" / "presentation.css").read_text(encoding="utf-8")
    if text.count(CSS_OLD) != 1:
        raise SystemExit("presentation.css: expected the table-wrapper rule once")
    return text.replace(CSS_OLD, CSS_NEW)


def edit_sources() -> None:
    (PACKAGE / "source" / "page" / SPEC_PAGE).write_text(edited_spec_page(), encoding="utf-8")
    (PACKAGE / "source" / "presentation.css").write_text(edited_stylesheet(), encoding="utf-8")


def manifest() -> None:
    data = read(BASE / "source_manifest.json")
    data["target"]["technical_version"] = PACKAGE.name
    data["source_role"] = ("Git-only Japanese spec-table layout edition of the released "
                           "git-20261026-cc8b3421 package; visible copy unchanged")
    data["publication_eligible"] = STATUS == APPROVED
    data["publication_status"] = STATUS
    data["pending_source_review"] = [] if STATUS == APPROVED else [
        "operator review of the 電気データ table layout before Git-only release"]
    data["derived_from"] = {
        "package": BASE.name,
        "authorization": "operator 2026-10-27 「全部照录，版式都接受，上线提交发布，保留疑点后续纠正」; base release merged as #1611",
        "manifest_sha256": sha256(BASE / "source_manifest.json"),
    }
    data["layout_corrections"] = [{
        "page": f"source/page/{SPEC_PAGE}",
        "block": "電気データ",
        "base": "declared plain table in a scrolling table-wrapper; manual-spec-table only, no frame",
        "corrected": "shared hb-spec-table-composition frame and hb-spec-label / hb-spec-value cells, as the "
                     "HB-TABLE-SPEC tables 基本情報 and 多機能アダプタ; bold STC/BNPI header as printed; "
                     "three columns fit 390px without scrolling",
        "stylesheet": "source/presentation.css: the table-wrapper scroll rule replaced by two geometry/typography rules",
        "instruction": "operator, 2026-10-27: 「这个表格样式不对吧」 on the live page, then 「按新版本包发布」",
    }]
    (exception,) = data["shared_component_exceptions"]
    exception["reason"] = TABLE_EXCEPTION_REASON
    for item in data["component_map"]:
        if item["printed"] == "電気データ STC/BNPI table":
            item["shared"] = ("declared three-column table on the shared hb-spec-table-composition "
                              "(see shared_component_exceptions)")
    for pinned in data["repo_inputs"]:
        pinned["sha256"] = sha256(REPO / pinned["path"])
    files = sorted(
        p for p in PACKAGE.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
        and p.relative_to(PACKAGE).parts[0] in {*SCRIPTS, *COPIED_ROOTS})
    data["inputs"] = [entry(p) for p in files]
    write(PACKAGE / "source_manifest.json", data)


def release_manifest() -> None:
    """Inventory every package file for the Git-only release (seal_frozen_web_evidence)."""
    data = read(PACKAGE / "source_manifest.json")
    frozen = PACKAGE / "frozen_source_manifest.json"
    data["inputs"] = [entry(p) for p in sorted(PACKAGE.rglob("*"))
                      if p.is_file() and "__pycache__" not in p.parts and p != frozen]
    write(frozen, data)


def main() -> None:
    copy_base()
    edit_sources()
    manifest()
    if (PACKAGE / "web" / "ja").is_dir():
        release_manifest()
    print(json.dumps({"package": PACKAGE.name, "inputs": len(read(PACKAGE / "source_manifest.json")["inputs"])}))


if __name__ == "__main__":
    main()
