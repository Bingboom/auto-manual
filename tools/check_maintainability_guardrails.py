#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
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


@dataclass(frozen=True)
class ContentSourceFailure:
    path: str
    line_number: int
    rule: str
    text: str


_BLOCKED_TOOL_IDENTIFIERS: tuple[str, ...] = (
    "LANG" + "_COPY",
    "_" + "LANG" + "_COPY",
    "_" + "SIGNAL" + "_WORDS",
    "_" + "SAFETY" + "_SUBLIST" + "_RULES",
)
_CONFIG_COPY_KEYS = re.compile(
    r"^\s*(?:manual_|output_|bundle_|page_)?(?:title|subtitle|heading|header|language_range)(?:_text|_label|_copy)?\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)
_RECIPE_DEFAULT = re.compile(r"^\s*default\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)


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


def _relative_path(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _iter_lines(path: Path) -> list[tuple[int, str]]:
    return list(
        enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1)
    )


def _strip_yaml_comment(value: str) -> str:
    return value.split("#", 1)[0].strip().strip("'\"")


def _looks_like_visible_copy(value: str) -> bool:
    normalized = _strip_yaml_comment(value)
    if not normalized or normalized in {"[]", "{}", "null", "None"}:
        return False
    if "{{" in normalized or "${" in normalized:
        return False
    if re.fullmatch(r"[\w./:{}\-[\], ]+", normalized) and not re.search(
        r"[A-Za-z]{2,}\s+[A-Za-z]{2,}|[\u4e00-\u9fff]", normalized
    ):
        return False
    return bool(re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}|[\u4e00-\u9fff]", normalized))


def _looks_like_sentence_default(value: str) -> bool:
    normalized = _strip_yaml_comment(value)
    if not normalized or "{{" in normalized:
        return False
    if re.search(r"[\u4e00-\u9fff]", normalized):
        return len(normalized) >= 6
    words = re.findall(r"[A-Za-zÀ-ÿ]{2,}", normalized)
    return len(words) >= 3


def collect_content_source_failures(repo_root: Path) -> list[ContentSourceFailure]:
    failures: list[ContentSourceFailure] = []

    for path in sorted((repo_root / "tools").glob("**/*.py")):
        if path.name == Path(__file__).name:
            continue
        relative = _relative_path(repo_root, path)
        for line_number, line in _iter_lines(path):
            for identifier in _BLOCKED_TOOL_IDENTIFIERS:
                if re.search(rf"^\s*{re.escape(identifier)}\b\s*(?::|=)", line):
                    failures.append(
                        ContentSourceFailure(
                            path=relative,
                            line_number=line_number,
                            rule="python-content-copy-constant",
                            text=identifier,
                        )
                    )

    config_candidates = list(repo_root.glob("config*.yaml"))
    config_candidates.extend((repo_root / "config-bases").glob("*.yaml"))
    for path in sorted(config_candidates):
        if not path.is_file():
            continue
        relative = _relative_path(repo_root, path)
        for line_number, line in _iter_lines(path):
            match = _CONFIG_COPY_KEYS.match(line)
            if match and _looks_like_visible_copy(match.group("value")):
                failures.append(
                    ContentSourceFailure(
                        path=relative,
                        line_number=line_number,
                        rule="yaml-visible-copy",
                        text=line.strip(),
                    )
                )

    recipes_root = repo_root / "docs" / "templates" / "recipes"
    for path in sorted(recipes_root.glob("**/*.yaml")):
        relative = _relative_path(repo_root, path)
        for line_number, line in _iter_lines(path):
            match = _RECIPE_DEFAULT.match(line)
            if match and _looks_like_sentence_default(match.group("value")):
                failures.append(
                    ContentSourceFailure(
                        path=relative,
                        line_number=line_number,
                        rule="recipe-sentence-default",
                        text=line.strip(),
                    )
                )

    return failures


def _render_failure(failure: GuardrailFailure) -> str:
    over_by = failure.actual_lines - failure.max_lines
    return (
        f"[maintainability] {failure.path} has grown to {failure.actual_lines} lines "
        f"(limit {failure.max_lines}, +{over_by})."
    )


def _render_content_failure(failure: ContentSourceFailure) -> str:
    return (
        f"[content-source] {failure.path}:{failure.line_number} violates "
        f"{failure.rule}: {failure.text}"
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    failures = collect_hotspot_failures(repo_root)
    content_failures = collect_content_source_failures(repo_root)
    if failures or content_failures:
        print("[maintainability] Guardrail failures detected:")
        for failure in failures:
            print(_render_failure(failure))
        for failure in content_failures:
            print(_render_content_failure(failure))
        return 1

    print(
        f"[maintainability] Guardrails OK for {len(HOTSPOT_LINE_THRESHOLDS)} hotspot files "
        "and content-source boundary checks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
