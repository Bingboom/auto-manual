#!/usr/bin/env python3
"""Read-only evidence helpers for review-branch propagation ledgers."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import subprocess


MERGE_PARAMS_SAFE = "merge_params_safe"
NEEDS_HUMAN = "needs_human"

PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")
REVIEW_DUPLICATE_PREFIX_RE = re.compile(r"^p\d+_")
DIRECT_MANIFEST_SOURCE_PREFIXES = (
    "docs/templates/page_",
    "docs/templates/recipes/",
)


@dataclass(frozen=True)
class SafetyResult:
    classification: str
    reason_code: str
    reason: str


@dataclass(frozen=True)
class SourceClassification:
    result: SafetyResult
    review_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewBranchSnapshot:
    branch: str
    branch_head: str | None = None
    manifest_path: str | None = None
    model: str | None = None
    region: str | None = None
    lang: str | None = None
    seed_git_sha: str | None = None
    page_manifest: str | None = None
    page_files: tuple[str, ...] = ()
    error: str | None = None


def _git(args: list[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )


def git_sha(ref: str, cwd: Path | None) -> str | None:
    proc = _git(["rev-parse", "--verify", ref], cwd)
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None


def git_text(ref: str, path: str, cwd: Path | None) -> str | None:
    proc = _git(["show", f"{ref}:{path}"], cwd)
    return proc.stdout if proc.returncode == 0 else None


def fetch_review_branch_refs(remote: str, cwd: Path | None) -> bool:
    """Refresh local remote-tracking refs without changing a review branch."""
    refspec = f"+refs/heads/review/*:refs/remotes/{remote}/review/*"
    return _git(["fetch", "--quiet", "--no-tags", remote, refspec], cwd).returncode == 0


def inspect_review_branch(
    branch: str,
    *,
    remote: str,
    cwd: Path | None,
) -> ReviewBranchSnapshot:
    """Read one review branch's checked-in manifest from its remote ref."""
    ref = f"{remote}/{branch}"
    branch_head = git_sha(ref, cwd)
    if branch_head is None:
        return ReviewBranchSnapshot(branch=branch, error="review_ref_missing")

    tree = _git(["ls-tree", "-r", "--name-only", ref], cwd)
    if tree.returncode != 0:
        return ReviewBranchSnapshot(
            branch=branch,
            branch_head=branch_head,
            error="review_tree_unreadable",
        )
    manifest_paths = tuple(
        path
        for path in tree.stdout.splitlines()
        if path.startswith("docs/_review/") and path.endswith("/manifest.json")
    )
    if not manifest_paths:
        return ReviewBranchSnapshot(
            branch=branch,
            branch_head=branch_head,
            error="review_manifest_missing",
        )
    if len(manifest_paths) != 1:
        return ReviewBranchSnapshot(
            branch=branch,
            branch_head=branch_head,
            error="review_manifest_ambiguous",
        )

    manifest_path = manifest_paths[0]
    raw_manifest = git_text(ref, manifest_path, cwd)
    if raw_manifest is None:
        return ReviewBranchSnapshot(
            branch=branch,
            branch_head=branch_head,
            manifest_path=manifest_path,
            error="review_manifest_unreadable",
        )
    try:
        manifest = json.loads(raw_manifest)
    except json.JSONDecodeError:
        manifest = None
    if not isinstance(manifest, dict):
        return ReviewBranchSnapshot(
            branch=branch,
            branch_head=branch_head,
            manifest_path=manifest_path,
            error="review_manifest_invalid",
        )

    def text_field(name: str) -> str | None:
        value = manifest.get(name)
        return value.strip() if isinstance(value, str) and value.strip() else None

    raw_page_files = manifest.get("page_files")
    page_files = (
        tuple(path for path in raw_page_files if isinstance(path, str) and path.strip())
        if isinstance(raw_page_files, list)
        else ()
    )
    model = text_field("model")
    region = text_field("region")
    seed_git_sha = text_field("git_sha")
    page_manifest = text_field("page_manifest")
    error = None
    if not model or not region or not seed_git_sha or not page_manifest or not page_files:
        error = "review_manifest_incomplete"

    return ReviewBranchSnapshot(
        branch=branch,
        branch_head=branch_head,
        manifest_path=manifest_path,
        model=model,
        region=region,
        lang=text_field("lang"),
        seed_git_sha=seed_git_sha,
        page_manifest=page_manifest,
        page_files=page_files,
        error=error,
    )


def _manifest_string_values(raw_text: str) -> frozenset[str] | None:
    try:
        import yaml
    except ImportError:
        return None
    try:
        payload = yaml.safe_load(raw_text)
    except (ValueError, yaml.YAMLError):
        return None

    values: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str):
            values.add(value.strip())
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return frozenset(values)


def source_affects_review_branch(
    *,
    source_path: str,
    scope_matches: bool,
    snapshot: ReviewBranchSnapshot,
    cwd: Path | None,
) -> bool | None:
    """Resolve source applicability from manifest evidence when available."""
    if snapshot.error:
        return None
    if source_path.startswith("docs/manifests/"):
        return source_path == snapshot.page_manifest
    if not source_path.startswith(DIRECT_MANIFEST_SOURCE_PREFIXES):
        return scope_matches
    if not snapshot.page_manifest or not snapshot.seed_git_sha:
        return None

    referenced_values: set[str] = set()
    found_manifest = False
    for ref in (snapshot.seed_git_sha, "HEAD"):
        manifest_text = git_text(ref, snapshot.page_manifest, cwd)
        if manifest_text is None:
            continue
        values = _manifest_string_values(manifest_text)
        if values is None:
            return None
        found_manifest = True
        referenced_values.update(values)
    if not found_manifest:
        return None
    return source_path.removeprefix("docs/") in referenced_values


def _map_source_to_target_lines(source_lines: list[str], target_lines: list[str]) -> dict[int, int | None]:
    mapping: dict[int, int | None] = {}
    matcher = SequenceMatcher(a=source_lines, b=target_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset
            continue
        if tag == "delete":
            for idx in range(i1, i2):
                mapping[idx] = None
            continue
        if tag == "insert":
            continue
        source_len = i2 - i1
        target_len = j2 - j1
        if target_len <= 0:
            for idx in range(i1, i2):
                mapping[idx] = None
        elif source_len == target_len:
            for offset in range(source_len):
                mapping[i1 + offset] = j1 + offset
        elif source_len == 1:
            mapping[i1] = j1
        else:
            for offset in range(source_len):
                fraction = offset / max(source_len - 1, 1)
                target_offset = round(fraction * max(target_len - 1, 0))
                mapping[i1 + offset] = j1 + target_offset
    return mapping


def _placeholder_values(template_line: str, rendered_line: str) -> tuple[str, ...] | None:
    matches = tuple(PLACEHOLDER_RE.finditer(template_line))
    if not matches:
        return ()
    pattern_parts = [r"\A"]
    last = 0
    for idx, match in enumerate(matches):
        pattern_parts.append(re.escape(template_line[last : match.start()]))
        pattern_parts.append(f"(?P<slot_{idx}>.*?)")
        last = match.end()
    pattern_parts.extend((re.escape(template_line[last:]), r"\Z"))
    rendered_match = re.match("".join(pattern_parts), rendered_line, flags=re.DOTALL)
    if rendered_match is None:
        return None
    return tuple(rendered_match.group(f"slot_{idx}") for idx in range(len(matches)))


def classify_merge_params_change(
    *,
    old_template: str,
    new_template: str,
    review_text: str,
) -> SafetyResult:
    """Prove that changed template lines are safe for current merge_params.

    The proof is intentionally narrow: line structure must be stable, every
    changed line must carry the same placeholders, and the review derivative
    must still match the old line outside placeholder values.
    """
    old_lines = old_template.splitlines()
    new_lines = new_template.splitlines()
    review_lines = review_text.splitlines()
    if old_lines == new_lines:
        return SafetyResult(
            MERGE_PARAMS_SAFE,
            "source_already_at_seed",
            "The branch seed already contains this shared-source content.",
        )
    if len(old_lines) != len(new_lines):
        return SafetyResult(
            NEEDS_HUMAN,
            "template_structure_changed",
            "The shared-source line structure changed, so merge_params cannot be proven safe.",
        )

    changed = tuple(idx for idx, (old, new) in enumerate(zip(old_lines, new_lines)) if old != new)
    mapping = _map_source_to_target_lines(old_lines, review_lines)
    for idx in changed:
        old_slots = tuple(PLACEHOLDER_RE.findall(old_lines[idx]))
        new_slots = tuple(PLACEHOLDER_RE.findall(new_lines[idx]))
        if not old_slots or old_slots != new_slots:
            return SafetyResult(
                NEEDS_HUMAN,
                "non_parameter_change",
                "At least one changed line is not the same parameter-bearing line.",
            )
        review_idx = mapping.get(idx)
        if review_idx is None or review_idx >= len(review_lines):
            return SafetyResult(
                NEEDS_HUMAN,
                "review_line_unmapped",
                "A changed parameter line could not be mapped into the review derivative.",
            )
        if _placeholder_values(old_lines[idx], review_lines[review_idx]) is None:
            return SafetyResult(
                NEEDS_HUMAN,
                "authored_placeholder_line",
                "The reviewer changed text outside a placeholder on a line merge_params would replace.",
            )
    return SafetyResult(
        MERGE_PARAMS_SAFE,
        "placeholder_lines_unedited",
        "All changed lines retain the old template skeleton outside placeholder values.",
    )


def _review_paths_for_source(source_path: str, page_files: tuple[str, ...]) -> tuple[str, ...]:
    source_name = Path(source_path).name
    exact = tuple(path for path in page_files if Path(path).name == source_name)
    if exact:
        return exact
    normalized = tuple(
        path
        for path in page_files
        if REVIEW_DUPLICATE_PREFIX_RE.sub("", Path(path).name, count=1) == source_name
    )
    return normalized if len(normalized) == 1 else ()


def classify_source_for_branch(
    *,
    source_path: str,
    snapshot: ReviewBranchSnapshot,
    remote: str,
    cwd: Path | None,
) -> SourceClassification:
    if snapshot.error:
        return SourceClassification(
            SafetyResult(NEEDS_HUMAN, snapshot.error, "Review-branch metadata is unresolved."),
        )
    if Path(source_path).suffix.lower() != ".rst":
        return SourceClassification(
            SafetyResult(
                NEEDS_HUMAN,
                "non_parameter_source",
                "Only parameter-bearing RST templates can use merge_params.",
            )
        )
    if not snapshot.seed_git_sha:
        return SourceClassification(
            SafetyResult(NEEDS_HUMAN, "seed_git_sha_missing", "The review manifest has no seed git SHA."),
        )

    review_paths = _review_paths_for_source(source_path, snapshot.page_files)
    if not review_paths:
        return SourceClassification(
            SafetyResult(
                NEEDS_HUMAN,
                "review_derivative_unmapped",
                "No unique review derivative can be mapped to this shared-source file.",
            )
        )

    old_template = git_text(snapshot.seed_git_sha, source_path, cwd)
    new_template = git_text("HEAD", source_path, cwd)
    if old_template is None:
        return SourceClassification(
            SafetyResult(
                NEEDS_HUMAN,
                "seed_source_missing",
                "The shared-source file is absent or unreadable at the review seed commit.",
            ),
            review_paths,
        )
    if new_template is None:
        return SourceClassification(
            SafetyResult(
                NEEDS_HUMAN,
                "current_source_missing",
                "The shared-source file is absent or unreadable at HEAD.",
            ),
            review_paths,
        )

    safe_result: SafetyResult | None = None
    for review_path in review_paths:
        review_text = git_text(f"{remote}/{snapshot.branch}", review_path, cwd)
        if review_text is None:
            return SourceClassification(
                SafetyResult(
                    NEEDS_HUMAN,
                    "review_derivative_unreadable",
                    "The mapped review derivative is absent or unreadable.",
                ),
                review_paths,
            )
        result = classify_merge_params_change(
            old_template=old_template,
            new_template=new_template,
            review_text=review_text,
        )
        if result.classification != MERGE_PARAMS_SAFE:
            return SourceClassification(result, review_paths)
        safe_result = result
    assert safe_result is not None
    return SourceClassification(safe_result, review_paths)
