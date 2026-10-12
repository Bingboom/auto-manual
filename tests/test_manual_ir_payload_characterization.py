"""Freeze CQ-3.2 payload validation using existing v1 and frozen-v2 fixtures.

The corpus comes from ManualIRReadContractTests' idml_bundle and
WebDocumentIRTests.build, with its existing target/Overview binding variant.
Regenerate only for an intentional behavior change::

    python -m tests.test_manual_ir_payload_characterization --update
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterator
import unittest

from tools.manual_ir.validate import _payload_issues

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CORPUS = FIXTURES / "manual_ir_payload_corpus.json"
GOLDEN = FIXTURES / "manual_ir_payload_golden.json"
_REPLACEMENTS = (None, "", "x", -1, 0, 1, 99, 1.5, True, [], {})


def _paths(value: Any, prefix: tuple = ()) -> Iterator[tuple]:
    # Component and flow validators own their nested schemas. Here the target
    # is the envelope plus the payload validator's dispatch to those owners.
    if prefix and (prefix[-1] == "payload" or (prefix[0] == "metadata" and len(prefix) == 2)):
        return
    if isinstance(value, dict):
        for key, child in value.items():
            yield prefix + (key,)
            yield from _paths(child, prefix + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value[:3]):
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


def variants(raw: dict) -> Iterator[tuple[str, Any]]:
    yield "as-is", raw
    for value in _REPLACEMENTS:
        yield f"root={json.dumps(value)}", value
    for path in _paths(raw):
        label = "/".join(map(str, path))
        yield f"{label}:delete", _mutate(raw, path, None, delete=True)
        for value in _REPLACEMENTS:
            yield f"{label}={json.dumps(value)}", _mutate(raw, path, value)
        node = raw
        for step in path:
            node = node[step]
        if isinstance(node, dict):
            yield f"{label}:unknown", _mutate(raw, path, {**node, "__unknown__": 1})
        if isinstance(node, list) and node:
            yield f"{label}:duplicate", _mutate(raw, path, [node[0], *node])
            yield f"{label}:reverse", _mutate(raw, path, list(reversed(node)))
    for kind in ("document_content", "flow"):
        yield f"block-kind={kind}", _mutate(raw, ("pages", 0, "blocks", 0, "kind"), kind)
    metadata = raw["metadata"]
    for key in ("component_registry", "manual_theme", "overview_instance"):
        missing = copy.deepcopy(metadata)
        missing.pop(key, None)
        missing.pop(key + "_sha256", None)
        yield f"{key}:missing-pair", _mutate(raw, ("metadata",), missing)
    if "web_contract" in metadata:
        for key in ("figure_targets", "product_overview"):
            for value in _REPLACEMENTS:
                yield f"web-{key}={json.dumps(value)}", _mutate(raw, ("metadata", "web_contract", key), value)
    if "overview_instance" in metadata:
        yield "overview-target-mismatch", _mutate(raw, ("metadata", "overview_instance", "target"), {"model": "OTHER", "region": "JP"})
    if "manual_theme" in metadata:
        roles = metadata["manual_theme"]["roles"]
        role = next(iter(roles))
        renderer = next(iter(roles[role]["bindings"]))
        yield "theme-unhashable-kind", _mutate(raw, ("metadata", "manual_theme", "roles", role, "bindings", renderer, "kind"), [])


def snapshot() -> dict[str, Any]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    digests = {}
    total = exceptions = 0
    for name, raw in corpus.items():
        lines = []
        for label, variant in variants(raw):
            for zero_skipped in (False, True):
                try:
                    outcome = _payload_issues(variant, require_zero_skipped_raw=zero_skipped)
                except Exception as exc:  # noqa: BLE001 -- exceptions are frozen behavior
                    outcome = f"!{type(exc).__name__}: {exc}"
                    exceptions += 1
                lines.append(json.dumps([label, zero_skipped, outcome], ensure_ascii=False))
                total += 1
        digests[name] = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    return {"variant_count": total, "exception_count": exceptions, "payload_digests": digests}


class ManualIRPayloadCharacterizationTests(unittest.TestCase):
    def test_issue_lists_and_exceptions_match_golden(self) -> None:
        self.assertEqual(json.loads(GOLDEN.read_text(encoding="utf-8")), snapshot())


if __name__ == "__main__":
    if "--update" in sys.argv:
        GOLDEN.write_text(json.dumps(snapshot(), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {GOLDEN}")
    else:
        unittest.main()
