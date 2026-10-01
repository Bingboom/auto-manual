"""Freeze reference-plan issues and exceptions before the CQ-3.2 refactor.

The corpus contains the approved docs contract and the existing reference-plan
fixture, augmented with a flow split. Regenerate only for an intentional change::

    python -m tests.test_reference_layout_plan_characterization --update
"""
from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterator
import unittest

from tests.test_reference_layout_plan import _manual_ir
from tools.idml.reference_layout_plan import validate_approved_reference_plan

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CORPUS = FIXTURES / "reference_layout_plan_corpus.json"
GOLDEN = FIXTURES / "reference_layout_plan_golden.json"
_REPLACEMENTS = (None, "", "x", -1, 0, 1, 99, 1.5, 1e9, True, [], {})


def _paths(value: Any, prefix: tuple = ()) -> Iterator[tuple]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield prefix + (key,)
            yield from _paths(child, prefix + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value[:4]):
            yield prefix + (index,)
            yield from _paths(child, prefix + (index,))


def _mutate(root: Any, path: tuple, value: Any, *, delete: bool = False) -> Any:
    clone = copy.deepcopy(root)
    target = clone
    for step in path[:-1]:
        target = target[step]
    if delete:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return clone


def variants(payload: dict) -> Iterator[tuple[str, Any]]:
    yield "as-is", payload
    for value in _REPLACEMENTS:
        yield f"root={json.dumps(value)}", value
    for path in _paths(payload):
        label = "/".join(map(str, path))
        yield f"{label}:delete", _mutate(payload, path, None, delete=True)
        for value in _REPLACEMENTS:
            yield f"{label}={json.dumps(value)}", _mutate(payload, path, value)
        node = payload
        for step in path:
            node = node[step]
        if isinstance(node, dict):
            yield f"{label}:unknown", _mutate(payload, path, {**node, "__unknown__": 1})
        if isinstance(node, list) and node:
            yield f"{label}:duplicate", _mutate(payload, path, [node[0], *node])
            yield f"{label}:reverse", _mutate(payload, path, list(reversed(node)))
    for tail in ("front", "absent", "tail"):
        yield f"flow-tail={tail}", _mutate(payload, ("pages", 0, "flow_split"), {
            "at_kind": "paragraph", "occurrence": 1, "tail_composition_id": tail,
        })
    yield "forbidden-path", _mutate(payload, ("idml_contract", "forbidden_visible_whole_page_links"), ["../whole.pdf"])
    yield "unknown-source", _mutate(payload, ("pages", 0, "source_ref"), "unknown")


def snapshot() -> dict[str, Any]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    ir = _manual_ir()
    digests = {}
    total = exceptions = 0
    for name, payload in corpus.items():
        lines = []
        cases = ((label, variant, ir) for label, variant in variants(payload))
        extra = (
            ("ir-no-metadata", payload, replace(ir, metadata={})),
            ("ir-unknown-language", payload, replace(ir, language="unknown")),
            ("ir-no-pages", payload, replace(ir, pages=())),
        )
        from itertools import chain

        for label, variant, source_ir in chain(cases, extra):
            try:
                outcome = validate_approved_reference_plan(variant, source_ir)
            except Exception as exc:  # noqa: BLE001 -- exception text is frozen too
                outcome = f"!{type(exc).__name__}: {exc}"
                exceptions += 1
            lines.append(json.dumps([label, outcome], ensure_ascii=False))
            total += 1
        digests[name] = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    return {"variant_count": total, "exception_count": exceptions, "plan_digests": digests}


class ReferenceLayoutPlanCharacterizationTests(unittest.TestCase):
    def test_issue_lists_and_exceptions_match_golden(self) -> None:
        self.assertEqual(json.loads(GOLDEN.read_text(encoding="utf-8")), snapshot())


if __name__ == "__main__":
    if "--update" in sys.argv:
        GOLDEN.write_text(json.dumps(snapshot(), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {GOLDEN}")
    else:
        unittest.main()
