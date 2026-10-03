#!/usr/bin/env python3
"""Refresh frozen workspace inputs without rebuilding manuals or merging changes."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.workspace_snapshot import atomic_json, content_digest, data_dir, digest, NAMES, save_snapshot, snapshot_path
from tools.utils.path_utils import repo_root


def execution_url() -> str:
    repo, run = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", "")
    return f"https://github.com/{repo}/actions/runs/{run}" if repo and run else "local"


def _read_status(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _check_identity(assets: Path, kind: str, source: dict) -> None:
    expected = json.loads((assets / "workspace_refresh_sources.json").read_text())[kind]
    if source["identity_sha256"] != expected:
        raise ValueError("unexpected source identity")


def refresh(kind: str, *, root: Path, log: Path, cli_bin: str, identity: str, run=None) -> dict:
    from tools import rtd_deliverables as delivery
    from tools import rtd_system_workspace as corpus
    from tools.lang_asset_sweep import TM_SENTENCE_TABLE, TM_TERMS_TABLE

    assets = root / "tools" / "rtd_portal_assets"
    path = snapshot_path(assets, NAMES[kind])
    destination = data_dir(root) / NAMES[kind]
    status_path = data_dir(root) / (kind + "-status.json")
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    report = {"schema": "workspace-refresh/v1", "kind": kind, "checked_at": now,
              "execution": execution_url(), "attempt": os.environ.get("GITHUB_RUN_ATTEMPT", now),
              "stage": "source-read", "status": "failed",
              "last_success": "", "resume": f"python tools/workspace_refresh.py refresh {kind}"}
    previous = None
    try:
        if path.exists():
            previous = json.loads(path.read_text(encoding="utf-8"))
            report["last_success"] = previous.get("exported_at", "")
        today = dt.datetime.now(dt.timezone.utc).date()
        reader = run or corpus.lark_runner(cli_bin, identity)
        if kind == "deliverables":
            names = ("FEISHU_PHASE2_BASE_TOKEN", "FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
                     "FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID")
            values = [os.environ.get(name, "") for name in names]
            source = {"identity_sha256": digest(values)}
            validate = delivery.snapshot_problems
            if not all(values):
                raise ValueError("missing source configuration")
            _check_identity(assets, kind, source)
            candidate = delivery.export_snapshot(run=reader, base_token=values[0], build_table=values[1],
                                                 key_table=values[2], today=today)
        else:
            base = os.environ.get("FEISHU_TRANSLATION_MEMORY_BASE_TOKEN", "")
            if not base:
                raise ValueError("missing corpus source configuration")
            source = {"identity_sha256": digest([base, TM_SENTENCE_TABLE, TM_TERMS_TABLE])}
            _check_identity(assets, kind, source)
            contract = corpus.load_contract(assets / corpus.CONTRACT_NAME)
            codes = [lang["code"] for lang in contract["corpus"]["languages"]]
            validate = lambda value: corpus.corpus_problems(value, codes)
            candidate = corpus.corpus_export(contract, run=reader, base_token=base, today=today, previous=previous)
        report["stage"] = "snapshot-validation"
        if previous and validate(previous):
            raise ValueError("invalid previous snapshot")
        result = save_snapshot(destination, candidate, previous=previous, validate=validate,
                               source=source, execution=report["execution"])
        report.update(result, stage="snapshot-validated", last_success=candidate["exported_at"],
                      snapshot_date=(previous or candidate)["exported_at"] if result["status"] == "unchanged" else candidate["exported_at"])
        request_path = os.environ.get("AUTO_MANUAL_WORKSPACE_REFRESH_REQUEST", "")
        if request_path and Path(request_path).is_file():
            report["batch"] = _read_status(Path(request_path))
        # Keep an execution candidate even for no-op reads, so a retry can compare
        # against an open content PR without rewriting the effective snapshot.
        frozen = json.loads(destination.read_text()) if result["status"] == "changed" else previous
        atomic_json(log.parent / (kind + "-candidate.json"), frozen)
        # Unchanged successful reads stay in execution logs, not timestamp-only commits.
        # A previously published failure does need an explicit recovery state.
        # Candidate status is local execution output. Submission suppresses no-op
        # confirmations, but can recover a still-open failure PR on retry.
        atomic_json(status_path, report)
    except Exception as exc:  # noqa: BLE001 - one refresh must preserve completed production
        # Transport exceptions may contain command arguments/tokens. Never persist their text.
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        report["message"] = "刷新失败，沿用上次有效数据；检查本次来源配置、分页与候选校验。"
        if isinstance(previous, dict):
            report["content_sha256"] = content_digest(previous)
        old_status = _read_status(status_path)
        fingerprint = digest({k: report[k] for k in ("kind", "stage", "error_type", "last_success")})
        report["failure_key"] = fingerprint
        if old_status.get("failure_key") != fingerprint:
            try:
                atomic_json(status_path, report)
            except OSError:
                report["state_write_failed"] = True
    atomic_json(log, report)
    print(json.dumps(report, ensure_ascii=False))
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    refresh_parser = commands.add_parser("refresh")
    refresh_parser.add_argument("kind", choices=NAMES)
    refresh_parser.add_argument("--root", type=Path, default=repo_root())
    refresh_parser.add_argument("--log", type=Path, default=Path(".tmp/workspace-refresh/result.json"))
    refresh_parser.add_argument("--cli-bin", default="lark-cli")
    refresh_parser.add_argument("--as", dest="identity", default=os.environ.get("FEISHU_PHASE2_IDENTITY", "bot"))
    args = parser.parse_args(argv)
    report = refresh(args.kind, root=args.root, log=args.log, cli_bin=args.cli_bin, identity=args.identity)
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
