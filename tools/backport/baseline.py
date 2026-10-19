"""Per-target render baseline for cloud-doc backport (approach C).

The backport must diff the rendered cloud-doc against a RENDER baseline (the doc as
Feishu stored it at review-start / the last backport), not the RST source — see
``code-as-doc/architecture/Backport_Rendered_Baseline_Design.md``. This module owns
the baseline FILE: where it lives and reading/writing it.

Decisions (夏冰, 2026-06-19):
- **Storage:** on the review branch, under a build-ignored ``.backport/`` dir
  (``docs/_review/<model>/<region>/.backport/<doc-token>.baseline.md``) so it
  persists and travels with the branch/PR. It is ``.md`` outside ``page/``, so the
  RST build / review-preview (which glob ``page/*.rst``) never render it.
- **Cursor advance:** only after a full apply (handled by the caller).
- **Legacy reviews:** seed the current cloud-doc as the baseline.
"""

from __future__ import annotations

from pathlib import Path

BACKPORT_DIRNAME = ".backport"


def safe_doc_token(doc_token: str) -> str:
    """Filesystem-safe baseline filename stem for a cloud-doc token."""
    safe = "".join(ch if (ch.isalnum() or ch in "-_") else "-" for ch in str(doc_token or "").strip())
    return safe[:64].strip("-") or "doc"


def baseline_rel_path(review_dir: str, doc_token: str) -> str:
    """Repo-relative baseline path under the review dir's ``.backport/`` directory."""
    review_dir = str(review_dir or "").strip().strip("/")
    if not review_dir:
        raise ValueError("review_dir is required")
    return f"{review_dir}/{BACKPORT_DIRNAME}/{safe_doc_token(doc_token)}.baseline.md"


def load_baseline(worktree: str | Path, review_dir: str, doc_token: str) -> str | None:
    """Return the stored baseline text, or ``None`` when no baseline exists yet."""
    path = Path(worktree) / baseline_rel_path(review_dir, doc_token)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def store_baseline(worktree: str | Path, review_dir: str, doc_token: str, text: str) -> str:
    """Write the baseline text; return the repo-relative path (for ``git add``)."""
    rel = baseline_rel_path(review_dir, doc_token)
    path = Path(worktree) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return rel
