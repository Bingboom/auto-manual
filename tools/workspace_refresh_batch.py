#!/usr/bin/env python3
"""Wrap an already approved local production/TM batch with one frozen-data refresh."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.workspace_refresh import refresh
from tools.workspace_refresh_publish import submit
from tools.workspace_refresh_trigger import REQUEST_ENV
from tools.utils.path_utils import repo_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("deliverables", "corpus"))
    parser.add_argument("--cli-bin", default="lark-cli --profile prod")
    parser.add_argument("--as", dest="identity", default="bot")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("supply the existing approved batch command after --")
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="workspace-batch-") as tmp:
        request = Path(tmp) / "request.json"
        env = dict(os.environ, **{REQUEST_ENV: str(request)})
        result = subprocess.run(command, cwd=root, env=env, check=False)
        if result.returncode or not request.exists():
            return result.returncode
        evidence = json.loads(request.read_text())
        if evidence.get("kind") != args.kind or not evidence.get("source_completed"):
            raise ValueError("batch completion evidence does not match requested source")
        report = refresh(args.kind, root=root, log=root / ".tmp/workspace-refresh/result.json",
                         cli_bin=args.cli_bin, identity=args.identity)
        print(submit(root, args.kind))
        return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
