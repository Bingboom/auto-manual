#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.script_bootstrap import bootstrap_repo_root

bootstrap_repo_root(__file__, parent_count=2)

from tools.dingtalk.alidocs_session import load_session_config_from_env, upload_file_to_node


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Manual AliDocs browser-session upload helper for Phase 0 DingTalk artifact sink validation.")
    ap.add_argument("--file", required=True, help="Local file path to upload.")
    ap.add_argument("--node-url", required=True, help="Target DingTalk docs node URL.")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    session = load_session_config_from_env()
    file_path = Path(args.file).resolve()
    committed = upload_file_to_node(session=session, file_path=file_path, parent_node_url=args.node_url)
    print(
        json.dumps(
            {
                "name": committed.name,
                "dentry_uuid": committed.dentry_uuid,
                "space_id": committed.space_id,
                "node_url": committed.node_url,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
