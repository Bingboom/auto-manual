"""Published workspace version receipt; generated with the page, without network access."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

from tools.utils.path_utils import repo_root

SCHEMA = "hello-docs-system-revision/v1"
RECEIPT_NAME = "system-workspace-revision.json"


def workspace_revision(root: Path) -> dict[str, str]:
    """Use RTD's checkout identity, falling back to Git for local builds."""
    revision = os.environ.get("READTHEDOCS_GIT_COMMIT_HASH", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        try:
            revision = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True, stderr=subprocess.DEVNULL, timeout=5,
            ).strip()
        except (OSError, subprocess.SubprocessError):
            revision = ""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        revision = ""
    return {"schema": SCHEMA, "revision": revision, "short_revision": revision[:8] or "本地预览",
            "built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def page_revision(app) -> dict[str, str]:
    """Cache once so HTML and its JSON receipt have the same build identity."""
    receipt = workspace_revision(repo_root())
    app._system_workspace_revision = receipt
    return receipt


def write_workspace_revision(app, exception) -> None:
    """Publish only a successful rendered page's receipt, never a main-branch claim."""
    receipt = getattr(app, "_system_workspace_revision", None)
    if exception is not None or receipt is None:
        return
    output = Path(app.outdir) / "_static" / RECEIPT_NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False) + "\n", encoding="utf-8")
