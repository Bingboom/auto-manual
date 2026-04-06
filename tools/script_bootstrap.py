from __future__ import annotations

import sys
from pathlib import Path


def bootstrap_repo_root(file_path: str | Path, *, parent_count: int = 1) -> Path:
    repo_root = Path(file_path).resolve().parents[parent_count]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
    return repo_root
