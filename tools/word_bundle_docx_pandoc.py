from __future__ import annotations

from pathlib import Path
import re
import subprocess

_KNOWN_BAD_REFERENCE_DOC_PANDOC_VERSIONS = {"3.1.3"}


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


def ensure_supported_pandoc_for_reference_doc(pandoc: str, reference_doc: Path | None) -> None:
    if reference_doc is None:
        return

    version = pandoc_version(pandoc)
    if version not in _KNOWN_BAD_REFERENCE_DOC_PANDOC_VERSIONS:
        return

    raise RuntimeError(
        "pandoc 3.1.3 is incompatible with this repository's reference DOCX template "
        "and can generate Word files that trigger unreadable-content repair prompts. "
        "Use pandoc 3.9.0.2 or newer for reference-doc exports."
    )
