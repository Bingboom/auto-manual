"""Review layer of a workbench review draft (审核稿), and its removal.

A draft written with the ``manual-review-draft`` skill holds the manual copy
plus a review layer, as its markup contract defines
(``references/corpus-and-color-rules.md`` "Markup contract" and
``references/jp-style-mapping.md``): page chrome (toolbar, contents, version
banner, change log), Chinese glosses and review notes, colour marks on reused,
new or updated copy, and hover provenance attributes. A Web candidate keeps
only the manual copy.

``strip_review_layer`` removes that layer in place and reports what it removed.
Pending markers (a parameter still to fill, a review placeholder) leave the
candidate too; the report lists them so the release gate can refuse them.
Copy still awaiting native review (new translations, JP-only inserts) stays in
the candidate and is counted for the same gate.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import re
from typing import Any

from bs4 import Comment, Tag
from bs4.element import AttributeValueList

# Page chrome and review notes: removed with their content.
REVIEW_NODES = (
    "header.preview-toolbar", "aside.toc", ".draft-banner", ".print-note",
    "details.change-log", ".footer-note", "script", "style",
    ".zh-translation", ".jp-review", ".jp-review-source", "nav.manual-locale-nav",
)
# Copy that is not final: removed, and listed for the release gate.
PENDING_NODES = (".jp-parameter", "[data-review-placeholder]")
# Copy awaiting native review: kept, and counted for the release gate.
UNREVIEWED_COPY = {
    "new_translations": ".en-new[data-needs-translation]",
    "draft_inserts": ".jp-draft-insert",
}
# Colour marks over final copy: the mark goes, the copy stays.
COLOUR_MARK = re.compile(
    r"^(?:jp-original|en-new|jp-spec-updated|jp-spec-filled|jp-change|jp-v\d{3}-fix"
    r"|jp-draft-insert|jp-template-value|jp-name-ref|jp-\d{4}-ref|us-difference"
    r"|us-review-figure|jp-typeset-figure)$"
)
# Attributes a Web candidate keeps; everything else is review provenance,
# hover text or inline presentation.
KEPT_ATTRIBUTES = frozenset({
    "id", "class", "src", "alt", "href", "colspan", "rowspan", "scope", "start", "type",
})
_VERSION_ATTRIBUTE = re.compile(r"^data-v\d+")


@dataclass
class ReviewLayerReport:
    removed: Counter = field(default_factory=Counter)
    unmarked: Counter = field(default_factory=Counter)
    dropped_attributes: Counter = field(default_factory=Counter)
    pending: list[dict[str, str]] = field(default_factory=list)
    unreviewed: dict[str, int] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return {
            "removed": dict(sorted(self.removed.items())),
            "unmarked": dict(sorted(self.unmarked.items())),
            "dropped_attributes": dict(sorted(self.dropped_attributes.items())),
            "pending": list(self.pending),
            "unreviewed": dict(self.unreviewed),
        }


def _text(node: Tag) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True))


def _remove_nodes(root: Tag, report: ReviewLayerReport) -> None:
    for selector in PENDING_NODES:
        for node in root.select(selector):
            report.pending.append({"marker": selector, "text": _text(node)})
    for selector in (*PENDING_NODES, *REVIEW_NODES):
        for node in root.select(selector):
            if not node.decomposed:
                report.removed[selector] += 1
                node.decompose()
    for comment in root.find_all(string=lambda value: isinstance(value, Comment)):
        comment.extract()


def _unmark(node: Tag, report: ReviewLayerReport) -> None:
    classes = [str(name) for name in node.get_attribute_list("class") if name]
    marks = [name for name in classes if COLOUR_MARK.match(name)]
    for name in marks:
        report.unmarked[name] += 1
    kept = [name for name in classes if not COLOUR_MARK.match(name)]
    if marks and node.name == "span" and not kept:
        node.unwrap()
        return
    if kept:
        node["class"] = AttributeValueList(kept)
    elif "class" in node.attrs:
        del node["class"]
    for name in list(node.attrs):
        if name.casefold() not in KEPT_ATTRIBUTES:
            report.dropped_attributes[_VERSION_ATTRIBUTE.sub("data-vNNN", name)] += 1
            del node[name]


def strip_review_layer(root: Tag) -> ReviewLayerReport:
    """Remove the review layer under ``root`` in place."""

    report = ReviewLayerReport()
    report.unreviewed = {
        name: len(root.select(selector)) for name, selector in UNREVIEWED_COPY.items()
    }
    _remove_nodes(root, report)
    for node in list(root.find_all(True)):
        _unmark(node, report)
    return report


__all__ = [
    "COLOUR_MARK",
    "PENDING_NODES",
    "REVIEW_NODES",
    "ReviewLayerReport",
    "UNREVIEWED_COPY",
    "strip_review_layer",
]
