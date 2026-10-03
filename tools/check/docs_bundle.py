from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")
INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$")
ASSET_RE = re.compile(r"^\s*(?:[-*]\s+)?(?:-\s+)?\.\.\s+(?:image|figure)::\s+(\S+)\s*$")
HTML_SRC_RE = re.compile(r'\bsrc="([^"]+)"', re.IGNORECASE)


def is_external_reference(value: str) -> bool:
    token = value.strip()
    if not token:
        return True
    lowered = token.lower()
    return lowered.startswith(("http://", "https://", "data:", "file://", "mailto:", "#"))


def resolve_local_reference(
    raw_value: str,
    *,
    rst_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> Path | None:
    token = raw_value.strip()
    if not token or is_external_reference(token):
        return None

    raw_path = Path(token.lstrip("/"))
    probe_paths = [
        rst_path.parent / raw_path,
        bundle_dir / raw_path,
        docs_dir / raw_path,
        repo_root / raw_path,
    ]
    for probe in probe_paths:
        if probe.exists():
            return probe.resolve()
    return None


def collect_placeholder_tokens(text: str) -> set[str]:
    return {match.group(1).strip() for match in PLACEHOLDER_RE.finditer(text) if match.group(1).strip()}


def field_binding_is_used(placeholder: str, used_placeholders: set[str]) -> bool:
    return any(
        candidate in used_placeholders
        for candidate in (
            placeholder,
            f"{placeholder}_BOLD",
            f"{placeholder}_LOWER",
        )
    )


def collect_placeholder_issues(
    *,
    rst_path: Path,
    model: str | None,
    region: str | None,
    issue_cls: type[Any],
) -> list[Any]:
    matches = sorted(set(PLACEHOLDER_RE.findall(rst_path.read_text(encoding="utf-8"))))
    if not matches:
        return []
    return [
        issue_cls(
            code="UNRESOLVED_PLACEHOLDER",
            message=f"Unresolved placeholders: {', '.join(matches)}",
            model=model,
            region=region,
            path=rst_path,
        )
    ]


def collect_reference_issues(
    *,
    rst_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    issue_cls: type[Any],
    resolve_local_reference: Callable[..., Path | None],
) -> list[Any]:
    issues: list[Any] = []
    for line_no, line in enumerate(rst_path.read_text(encoding="utf-8").splitlines(), start=1):
        include_match = INCLUDE_RE.match(line)
        if include_match:
            raw_value = include_match.group(1)
            resolved = resolve_local_reference(
                raw_value,
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                repo_root=repo_root,
            )
            if resolved is None:
                issues.append(
                    issue_cls(
                        code="MISSING_INCLUDE",
                        message=f"Missing include target on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )

        asset_match = ASSET_RE.match(line)
        if asset_match:
            raw_value = asset_match.group(1)
            resolved = resolve_local_reference(
                raw_value,
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                repo_root=repo_root,
            )
            if resolved is None:
                issues.append(
                    issue_cls(
                        code="MISSING_ASSET",
                        message=f"Missing image/figure asset on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )

        for html_match in HTML_SRC_RE.finditer(line):
            raw_value = html_match.group(1)
            resolved = resolve_local_reference(
                raw_value,
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                repo_root=repo_root,
            )
            if resolved is None:
                issues.append(
                    issue_cls(
                        code="MISSING_HTML_SRC",
                        message=f"Missing HTML src asset on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )
    return issues


def collect_bundle_issues(
    *,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    issue_cls: type[Any],
    collect_placeholder_issues: Callable[..., list[Any]],
    collect_reference_issues: Callable[..., list[Any]],
) -> list[Any]:
    issues: list[Any] = []
    index_path = bundle_dir / "index.rst"
    page_dir = bundle_dir / "page"
    if not index_path.exists():
        issues.append(
            issue_cls(
                code="MISSING_BUNDLE_INDEX",
                message=f"Prepared bundle index not found: {index_path}",
                model=model,
                region=region,
                path=index_path,
            )
        )
    if not page_dir.exists():
        issues.append(
            issue_cls(
                code="MISSING_PAGE_DIR",
                message=f"Prepared bundle page directory not found: {page_dir}",
                model=model,
                region=region,
                path=page_dir,
            )
        )
        return issues

    for rst_path in sorted(path for path in bundle_dir.rglob("*.rst") if path.is_file()):
        issues.extend(
            collect_placeholder_issues(
                rst_path=rst_path,
                model=model,
                region=region,
            )
        )
        issues.extend(
            collect_reference_issues(
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                repo_root=repo_root,
                model=model,
                region=region,
            )
        )
    return issues
