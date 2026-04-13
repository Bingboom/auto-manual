#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


HOTSPOT_LINE_THRESHOLDS: dict[str, int] = {
    "build.py": 750,
    "tools/build_docs.py": 860,
    "tools/process_build_queue.py": 650,
    "tools/validate_spec_master_runtime.py": 880,
    "tools/check_docs_generated.py": 880,
    "tools/word_bundle_docx.py": 740,
    "tools/process_docs/build_review_preview_targets.py": 430,
    "tools/queue_lark_ops.py": 360,
}


@dataclass(frozen=True)
class GuardrailFailure:
    path: str
    actual_lines: int
    max_lines: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Low-noise maintainability guardrails for known hotspot files."
    )
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root to inspect.",
    )
    return parser.parse_args(argv)


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def collect_hotspot_failures(
    repo_root: Path,
    *,
    thresholds: dict[str, int] | None = None,
) -> list[GuardrailFailure]:
    active_thresholds = thresholds or HOTSPOT_LINE_THRESHOLDS
    failures: list[GuardrailFailure] = []

    for relative_path, max_lines in active_thresholds.items():
        path = repo_root / relative_path
        if not path.exists():
            raise RuntimeError(f"Guardrail target does not exist: {relative_path}")

        actual_lines = _count_lines(path)
        if actual_lines > max_lines:
            failures.append(
                GuardrailFailure(
                    path=relative_path,
                    actual_lines=actual_lines,
                    max_lines=max_lines,
                )
            )

    return failures


def _render_failure(failure: GuardrailFailure) -> str:
    over_by = failure.actual_lines - failure.max_lines
    return (
        f"[maintainability] {failure.path} has grown to {failure.actual_lines} lines "
        f"(limit {failure.max_lines}, +{over_by})."
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    failures = collect_hotspot_failures(args.repo_root.resolve())
    if failures:
        print("[maintainability] Guardrail failures detected:")
        for failure in failures:
            print(_render_failure(failure))
        return 1

    print(
        f"[maintainability] Guardrails OK for {len(HOTSPOT_LINE_THRESHOLDS)} hotspot files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
