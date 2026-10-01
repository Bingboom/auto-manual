"""Characterization net for ``_validate_composition_data`` (plan CQ-3.2).

Every composition_data page frozen from the target-assembly contracts is
validated as-is and under a deterministic set of mutations (keys removed,
values swapped for wrong types or out-of-range numbers, unknown keys added,
the page moved to the wrong composition).  The issue lists, or the exception
a variant raises, are hashed per
source page and compared with ``idml_composition_data_golden.json``, so any
change to which errors fire, or to their exact wording, fails here.

An intentional validation change regenerates the golden::

    python -m tests.test_idml_composition_data_characterization --update
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Iterator

from tests.test_idml_target_assembly_plan import _manual_ir, _payload
from tools.idml.target_assembly_plan import _validate_composition_data

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CORPUS = FIXTURES / "idml_composition_data_corpus.json"
GOLDEN = FIXTURES / "idml_composition_data_golden.json"

_REPLACEMENTS: tuple[Any, ...] = (None, "x", -1, 0, 99, 1.5, 1e9, True, [], {})


def _paths(value: Any, prefix: tuple = ()) -> Iterator[tuple]:
    if isinstance(value, dict):
        for key in value:
            yield prefix + (key,)
            yield from _paths(value[key], prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value[:3]):
            yield prefix + (index,)
            yield from _paths(item, prefix + (index,))


def _set(root: Any, path: tuple, value: Any) -> Any:
    clone = copy.deepcopy(root)
    target = clone
    for step in path[:-1]:
        target = target[step]
    target[path[-1]] = value
    return clone


def _delete(root: Any, path: tuple) -> Any:
    clone = copy.deepcopy(root)
    target = clone
    for step in path[:-1]:
        target = target[step]
    del target[path[-1]]
    return clone


def variants(page: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield (label, page) pairs: the page itself, then each mutation."""

    yield "as-is", page
    yield "wrong-composition", {**page, "page_role": "body", "composition_type": "body"}
    yield "wrong-composition-type", {**page, "composition_type": "body"}
    data = page["composition_data"]
    for replacement in _REPLACEMENTS[1:]:
        yield f"data={json.dumps(replacement)}", {**page, "composition_data": replacement}
    yield "data:unknown-key", {**page, "composition_data": {**data, "__unknown__": 1}}
    for path in _paths(data):
        label = "/".join(str(step) for step in path)
        if isinstance(path[-1], str):
            yield f"{label}:delete", {**page, "composition_data": _delete(data, path)}
        for replacement in _REPLACEMENTS:
            yield (
                f"{label}={json.dumps(replacement)}",
                {**page, "composition_data": _set(data, path, replacement)},
            )
        node = data
        for step in path:
            node = node[step]
        if isinstance(node, dict):
            yield f"{label}:unknown-key", {**page, "composition_data": _set(data, path, {**node, "__unknown__": 1})}
        if isinstance(node, list) and node:
            yield f"{label}:duplicate-first", {**page, "composition_data": _set(data, path, [node[0], *node])}


def snapshot() -> dict[str, Any]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    reference = {"page_size_pt": corpus["page_size_pt"]}
    ir = _manual_ir(_payload())
    digests: dict[str, str] = {}
    total = 0
    for index, page in enumerate(corpus["pages"]):
        lines = []
        for label, variant in variants(page):
            try:
                outcome: Any = _validate_composition_data([variant], reference, ir)
            except Exception as exc:  # noqa: BLE001 -- a crash is part of the recorded behaviour
                outcome = f"!{type(exc).__name__}: {exc}"
            lines.append(json.dumps([label, outcome], ensure_ascii=False))
            total += 1
        try:
            outcome = _validate_composition_data([page], {}, ir)
        except Exception as exc:  # noqa: BLE001 -- a crash is part of the recorded behaviour
            outcome = f"!{type(exc).__name__}: {exc}"
        lines.append(json.dumps(["no-page-size", outcome], ensure_ascii=False))
        total += 1
        key = f"{index:02d} {page['source_ref']}"
        digests[key] = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]
    return {"variant_count": total, "page_digests": digests}


class CompositionDataCharacterizationTest(unittest.TestCase):
    def test_issue_lists_match_golden(self) -> None:
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
        actual = snapshot()
        self.assertEqual(expected["variant_count"], actual["variant_count"])
        changed = sorted(
            key for key, digest in actual["page_digests"].items()
            if expected["page_digests"].get(key) != digest
        )
        self.assertEqual([], changed, "validation output changed for these corpus pages")


if __name__ == "__main__":
    if "--update" in sys.argv:
        GOLDEN.write_text(json.dumps(snapshot(), indent=1) + "\n", encoding="utf-8")
        print(f"wrote {GOLDEN}")
    else:
        unittest.main()
