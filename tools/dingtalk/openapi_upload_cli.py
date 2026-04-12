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
from tools.dingtalk.auth import get_app_only_token
from tools.dingtalk.openapi_upload import (
    DEFAULT_STORAGE_DRIVER,
    load_default_target_node_url,
    load_operator_union_id,
    request_upload_info,
    upload_file_with_signed_url,
    commit_uploaded_file,
)
from tools.dingtalk.workspace import parse_node_id_from_url

bootstrap_repo_root(__file__, parent_count=2)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Manual DingTalk OpenAPI upload smoke CLI for app-token + operator-union-id flows.",
    )
    ap.add_argument("--file", required=True, help="Local file path to upload")
    ap.add_argument("--parent-node-url", default=None, help="DingTalk knowledge node URL; defaults to DINGTALK_DEFAULT_TARGET_NODE_URL")
    ap.add_argument("--operator-union-id", default=None, help="Operator unionId; defaults to DINGTALK_OPERATOR_UNION_ID")
    ap.add_argument("--client-id-env", default="DINGTALK_CLIENT_ID", help="Env name for DingTalk client id")
    ap.add_argument("--client-secret-env", default="DINGTALK_CLIENT_SECRET", help="Env name for DingTalk client secret")
    ap.add_argument("--corp-id-env", default="DINGTALK_CORP_ID", help="Env name for DingTalk corp id")
    ap.add_argument("--storage-driver", default=DEFAULT_STORAGE_DRIVER, help="Storage driver to request from DingTalk")
    ap.add_argument("--prefer-region", default=None, help="Optional region hint forwarded to uploadInfos")
    ap.add_argument("--prefer-intranet", action="store_true", help="Prefer intranet upload URLs when the API supports them")
    ap.add_argument("--prefer-internal-url", action="store_true", help="Use internalResourceUrls when the API returns them")
    ap.add_argument("--convert-to-online-doc", action="store_true", help="Ask DingTalk to convert the uploaded file into an online document at commit time")
    ap.add_argument("--conflict-strategy", default=None, help="Optional commit conflict strategy, for example AUTO_RENAME")
    ap.add_argument("--dry-run", action="store_true", help="Resolve token, operator, target node, and upload ticket without uploading bytes")
    ap.add_argument("--json", action="store_true", help="Emit JSON output")
    ap.add_argument("--timeout-seconds", type=float, default=30.0, help="Timeout for OpenAPI JSON requests")
    ap.add_argument("--upload-timeout-seconds", type=float, default=120.0, help="Timeout for the signed object upload")
    return ap.parse_args(argv)


def _print(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f"[dingtalk-openapi-upload] ERROR: Upload file does not exist: {file_path}", file=sys.stderr)
        return 1

    try:
        access_token = get_app_only_token(
            client_id_env=args.client_id_env,
            client_secret_env=args.client_secret_env,
            corp_id_env=args.corp_id_env,
        )
        parent_node_url = str(args.parent_node_url or "").strip() or load_default_target_node_url()
        operator_union_id = str(args.operator_union_id or "").strip() or load_operator_union_id()
        parent_node_id = parse_node_id_from_url(parent_node_url)
        upload_info = request_upload_info(
            access_token=access_token.access_token,
            parent_node_id=parent_node_id,
            operator_union_id=operator_union_id,
            file_path=file_path,
            storage_driver=args.storage_driver,
            prefer_intranet=args.prefer_intranet,
            prefer_region=args.prefer_region,
            timeout_seconds=args.timeout_seconds,
            prefer_internal_url=args.prefer_internal_url,
        )
        if args.dry_run:
            _print(
                {
                    "mode": "dry-run",
                    "file": str(file_path),
                    "parent_node_url": parent_node_url,
                    "parent_node_id": parent_node_id,
                    "operator_union_id": operator_union_id,
                    "upload_key": upload_info.upload_key,
                    "upload_method": upload_info.upload_request.method,
                    "upload_url": upload_info.upload_request.url,
                    "convert_to_online_doc": args.convert_to_online_doc,
                },
                as_json=args.json,
            )
            return 0
        upload_file_with_signed_url(
            upload_info=upload_info,
            file_path=file_path,
            timeout_seconds=args.upload_timeout_seconds,
        )
        committed = commit_uploaded_file(
            access_token=access_token.access_token,
            parent_node_id=parent_node_id,
            operator_union_id=operator_union_id,
            upload_key=upload_info.upload_key,
            file_name=upload_info.file_name,
            file_size=upload_info.file_size,
            convert_to_online_doc=args.convert_to_online_doc,
            conflict_strategy=args.conflict_strategy,
            timeout_seconds=args.timeout_seconds,
        )
    except RuntimeError as exc:
        print(f"[dingtalk-openapi-upload] ERROR: {exc}", file=sys.stderr)
        return 1

    _print(
        {
            "mode": "upload",
            "file": str(file_path),
            "parent_node_url": parent_node_url,
            "parent_node_id": parent_node_id,
            "operator_union_id": operator_union_id,
            "upload_key": upload_info.upload_key,
            "dentry_id": committed.dentry_id,
            "dentry_uuid": committed.dentry_uuid,
            "candidate_node_url": committed.candidate_node_url,
            "convert_to_online_doc": args.convert_to_online_doc,
        },
        as_json=args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
