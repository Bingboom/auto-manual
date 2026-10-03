from __future__ import annotations

import os
from pathlib import Path
from packaging.version import InvalidVersion, Version
import re
import subprocess

_MIN_REFERENCE_DOC_PANDOC_VERSION = Version("3.9.0.2")
_COMMON_PANDOC_PATHS = (
    "/usr/local/bin/pandoc",
    "/opt/homebrew/bin/pandoc",
)


def pandoc_version(pandoc: str) -> str | None:
    try:
        proc = subprocess.run(
            [pandoc, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    first_line = (proc.stdout or "").splitlines()
    if not first_line:
        return None
    match = re.search(
        r"\bpandoc(?:\.exe)?\s+([0-9]+(?:\.[0-9]+)+)\b",
        first_line[0].strip(),
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def reference_doc_pandoc_support(pandoc: str) -> tuple[bool, str]:
    version_text = pandoc_version(pandoc)
    if version_text is None:
        return False, (
            "Unable to determine pandoc version for reference DOCX export. "
            "Use pandoc 3.9.0.2 or newer."
        )

    try:
        version = Version(version_text)
    except InvalidVersion:
        return False, (
            f"Unable to parse pandoc version '{version_text}' for reference DOCX export. "
            "Use pandoc 3.9.0.2 or newer."
        )

    if version < _MIN_REFERENCE_DOC_PANDOC_VERSION:
        return False, (
            f"pandoc {version_text} is incompatible with this repository's reference DOCX template. "
            "Versions older than 3.9.0.2 can emit an invalid '/word/media/' content-type override "
            "that makes Microsoft Word show an unreadable-content repair prompt. "
            "Use pandoc 3.9.0.2 or newer for reference-doc exports."
        )

    return True, f"pandoc {version_text} supports reference-doc exports"


def discover_pandoc_binaries() -> tuple[str, ...]:
    candidate_names = ("pandoc.exe", "pandoc") if os.name == "nt" else ("pandoc",)
    candidates: list[str] = []
    seen: set[str] = set()

    for directory in os.get_exec_path():
        for name in candidate_names:
            candidate = Path(directory) / name
            if not candidate.is_file():
                continue
            candidate_text = str(candidate)
            if candidate_text in seen:
                continue
            seen.add(candidate_text)
            candidates.append(candidate_text)

    for candidate_text in _COMMON_PANDOC_PATHS:
        candidate = Path(candidate_text)
        if not candidate.is_file() or candidate_text in seen:
            continue
        seen.add(candidate_text)
        candidates.append(candidate_text)

    return tuple(candidates)


def resolve_pandoc_binary(
    reference_doc: Path | None,
    *,
    candidates: tuple[str, ...] | None = None,
) -> str:
    resolved_candidates = candidates if candidates is not None else discover_pandoc_binaries()
    if not resolved_candidates:
        raise RuntimeError("pandoc is required for non-Windows word bundle export")

    if reference_doc is None:
        return resolved_candidates[0]

    supported: list[tuple[Version, str]] = []
    checked_versions: list[str] = []
    first_failure: str | None = None

    for candidate in resolved_candidates:
        version_text = pandoc_version(candidate)
        checked_versions.append(f"{candidate} ({version_text or 'unknown'})")
        ok, detail = reference_doc_pandoc_support(candidate)
        if ok and version_text is not None:
            supported.append((Version(version_text), candidate))
            continue
        if first_failure is None:
            first_failure = detail

    if supported:
        supported.sort(reverse=True)
        return supported[0][1]

    checked = ", ".join(checked_versions)
    if first_failure is not None:
        raise RuntimeError(f"{first_failure} Checked pandoc candidates: {checked}")
    raise RuntimeError(f"No installed pandoc binary supports reference-doc exports. Checked pandoc candidates: {checked}")


def ensure_supported_pandoc_for_reference_doc(pandoc: str, reference_doc: Path | None) -> None:
    if reference_doc is None:
        return

    ok, detail = reference_doc_pandoc_support(pandoc)
    if ok:
        return

    raise RuntimeError(detail)
