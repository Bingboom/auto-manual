#!/usr/bin/env python3
"""hello-docs-bridge — STDIO MCP server bridging DingTalk Wukong to the Hello-Docs workspace.

Exposes mature workspace capabilities as MCP tools:

  1. Translation-memory / terminology lookup (Feishu TM-B live base)
       tm_term_lookup, tm_sentence_lookup
  2. Feishu build-queue operations (bounded verbs, same contract as the IM adapters)
       queue_resolve, queue_execute, queue_query, manual_index_query
  3. Spec-data intake (staging-gated writes into the phase2 source tables)
       intake_stage, intake_status, intake_discard, intake_commit (jobs pattern)

Design rules:
  - stdout is the MCP protocol channel; all logging goes to stderr.
  - No third-party dependencies; newline-delimited JSON-RPC per MCP stdio transport.
  - Subprocess timeout stays below Wukong's 60s MCP tool timeout.
  - Credentials never live in the Wukong MCP config: this server sources the
    machine env file(s) itself (default ~/.openclaw/.env, override via
    HELLO_DOCS_BRIDGE_ENV_FILES, colon-separated).
  - queue_execute with action publish is refused unless confirm_publish=true.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from intake_contract import (
    KR_CONTRACT_VERSION,
    KR_STAGING_REQUIRED_FIELDS,
    is_kr_document_key,
    missing_fields,
    structure_identity,
    validate_kr_candidate,
    validate_sibling_structure,
)

BRIDGE_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = str(BRIDGE_DIR.parents[1])
REPO_ROOT = os.environ.get(
    "AUTO_MANUAL_REPO_ROOT",
    os.environ.get("HELLO_DOCS_REPO_ROOT", DEFAULT_REPO_ROOT),
)
REPO_VENV_PYTHON = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
VENV_PYTHON = os.environ.get("AUTO_MANUAL_PYTHON") or (
    REPO_VENV_PYTHON if os.path.isfile(REPO_VENV_PYTHON) else sys.executable
)
TM_SCRIPT = os.path.join(
    ".agents", "skills", "bitable-translation-memory", "scripts",
    "query_live_translation_memory.py",
)
CONTROL_CONFIG = os.environ.get("AUTO_MANUAL_CONTROL_CONFIG", "configs/config.us.yaml")
DEFAULT_ENV_FILES = "~/.openclaw/.env"
SUBPROC_TIMEOUT_SECONDS = 50
STDERR_TAIL_LIMIT = 1200

LARK_CLI = os.environ.get("LARK_CLI") or shutil.which("lark-cli") or "lark-cli"
LARK_CLI_PROFILE = os.environ.get("LARK_CLI_PROFILE", "prod")
LARK_CLI_IDENTITY = os.environ.get("LARK_CLI_IDENTITY", "bot")
BUILD_BASE_TOKEN = "LD3lb4G1ua4GOVs1vxAc9W2enje"
BUILD_TABLE_ID = "tblbnRHjpJeCVTtj"        # 文档构建表
REGION_DICT_TABLE_ID = "tblvBsr8qGPjXWdA"  # 区域法规字典（含 钉钉组合代码）
LANG_DICT_TABLE_ID = "tblVNk16VXXVo5oj"    # 语言字典（含 钉钉语言代码）
INTAKE_STAGING_TABLE_ID = "tblIi0BEufjvGLIU"   # 数据入库表（staging）
SPEC_SOURCE_TABLE_ID = "tblPUFJqt2uGGvTT"      # 规格参数明细（源表）
PLACEHOLDER_SOURCE_TABLE_ID = "tblEhqJVXiyKtnwq"  # 页面占位参数（源表）

SERVER_INFO = {"name": "hello-docs-bridge", "version": "0.8.0"}

_merged_env: dict[str, str] | None = None


def log(message: str) -> None:
    print(f"[hello-docs-bridge] {message}", file=sys.stderr, flush=True)


def merged_env() -> dict[str, str]:
    """Current process env + vars sourced from the machine env file(s).

    File values fill in and override the (minimal) env Wukong launches us with;
    sourcing happens once, lazily, via bash so any valid shell syntax works.
    """
    global _merged_env
    if _merged_env is not None:
        return _merged_env
    env = dict(os.environ)
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + env.get("PATH", "")
    raw_list = os.environ.get("HELLO_DOCS_BRIDGE_ENV_FILES", DEFAULT_ENV_FILES)
    for raw_path in raw_list.split(":"):
        path = os.path.expanduser(raw_path.strip())
        if not path or not os.path.isfile(path):
            continue
        try:
            proc = subprocess.run(
                ["bash", "-c", 'set -a; source "$1" >/dev/null 2>&1; env -0', "_", path],
                capture_output=True, env=env, timeout=10,
            )
            if proc.returncode != 0:
                log(f"env file source failed rc={proc.returncode}: {path}")
                continue
            for chunk in proc.stdout.split(b"\0"):
                if b"=" in chunk:
                    key, _, value = chunk.partition(b"=")
                    try:
                        env[key.decode()] = value.decode()
                    except UnicodeDecodeError:
                        continue
            log(f"sourced env file: {path}")
        except Exception as exc:  # noqa: BLE001 — never let env loading kill the server
            log(f"env file error {path}: {exc}")
    _merged_env = env
    return env


def run_subprocess(argv: list[str], cwd: str | None = None) -> dict:
    """Run a workspace command; return parsed JSON stdout or a structured error."""
    try:
        proc = subprocess.run(
            argv, cwd=cwd or REPO_ROOT, env=merged_env(),
            capture_output=True, text=True, timeout=SUBPROC_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"command timed out after {SUBPROC_TIMEOUT_SECONDS}s",
                "argv": argv}
    except FileNotFoundError as exc:
        return {"ok": False, "error": f"executable not found: {exc}", "argv": argv}
    stderr_tail = (proc.stderr or "")[-STDERR_TAIL_LIMIT:]
    if proc.returncode != 0:
        return {"ok": False, "error": f"exit code {proc.returncode}", "argv": argv,
                "stderr_tail": stderr_tail}
    stdout = (proc.stdout or "").strip()
    try:
        return {"ok": True, "result": json.loads(stdout)}
    except json.JSONDecodeError:
        return {"ok": True, "result_text": stdout, "stderr_tail": stderr_tail}


# ---------------------------------------------------------------- tool layer

def tm_lookup(scope: str, arguments: dict) -> dict:
    query_text = str(arguments.get("query_text", "")).strip()
    target_lang = str(arguments.get("target_lang", "")).strip()
    if not query_text:
        return {"ok": False, "error": "query_text is required"}
    if not target_lang:
        return {"ok": False, "error": "target_lang is required (e.g. ko, ja, fr, zh-TW)"}
    argv = [
        VENV_PYTHON, TM_SCRIPT,
        "--query-text", query_text,
        "--scope", scope,
        "--source-lang", str(arguments.get("source_lang", "en")),
        "--target-lang", target_lang,
        "--limit", str(int(arguments.get("limit", 8))),
        "--format", "json",
    ]
    if arguments.get("no_split"):
        argv.append("--no-split")
    return run_subprocess(argv)


def queue_resolve(arguments: dict) -> dict:
    query_text = str(arguments.get("query_text", "")).strip()
    if not query_text:
        return {"ok": False, "error": "query_text is required"}
    argv = [
        VENV_PYTHON, "build.py", "queue-resolve-action",
        "--config", CONTROL_CONFIG,
        "--query-text", query_text,
        "--json",
    ]
    if arguments.get("confirm_publish"):
        argv.append("--confirm-publish")
    outcome = run_subprocess(argv)
    if outcome.get("ok"):
        _scrub_document_link(outcome, enrich=False, budget=[0])
    return outcome


WORKFLOW_ACTION_ARGS = {
    "start_review": "start-review",
    "build_draft_package": "build-draft-package",
    "publish": "publish",
}


def queue_execute(arguments: dict) -> dict:
    record_id = str(arguments.get("record_id", "")).strip()
    queue_scope = str(arguments.get("queue_scope", "")).strip()
    if not record_id or not queue_scope:
        return {"ok": False,
                "error": "record_id and queue_scope are required; take both from a "
                         "queue_resolve result row"}
    action_name = str(arguments.get("action_name", "")).strip()
    confirm_publish = bool(arguments.get("confirm_publish", False))
    if action_name == "publish" and not confirm_publish:
        return {"ok": False,
                "error": "publish refused: requires explicit operator confirmation. "
                         "Ask the user to say 确认发布, then retry with confirm_publish=true."}
    argv = [
        VENV_PYTHON, "build.py", "queue-execute",
        "--config", CONTROL_CONFIG,
        "--queue-scope", queue_scope,
        "--record-id", record_id,
        "--json",
    ]
    workflow_action = WORKFLOW_ACTION_ARGS.get(action_name, "")
    if workflow_action:
        argv.extend(["--query-workflow-action", workflow_action])
    if confirm_publish:
        argv.append("--confirm-publish")
    if arguments.get("no_wait", True):
        argv.append("--no-wait")
    return run_subprocess(argv)


_URL_RE = None


def _extract_url(text: str) -> str:
    global _URL_RE
    import re
    if _URL_RE is None:
        _URL_RE = re.compile(r"https?://[^\s\)\]]+")
    match = _URL_RE.search(text or "")
    return match.group(0) if match else ""


def _fetch_feishu_doc_link(record_id: str) -> str:
    """Read the build row's 飞书云文档 field (the REAL review-doc link)."""
    got = run_lark_cli([
        "base", "+record-get", "--base-token", BUILD_BASE_TOKEN,
        "--table-id", BUILD_TABLE_ID, "--record-id", record_id,
        "--field-id", "飞书云文档", "--format", "json",
    ])
    if not got.get("ok"):
        return ""
    rows = (got.get("data") or {}).get("data") or []
    if rows and rows[0] and isinstance(rows[0][0], str):
        return _extract_url(rows[0][0])
    return ""


def _scrub_document_link(node, *, enrich: bool, budget: list) -> None:
    """Drop the misleading document_link (it maps to idml_file, not the Feishu
    doc) and, for query results, inject feishu_doc read live from the row."""
    if isinstance(node, dict):
        node.pop("document_link", None)
        record_id = node.get("record_id")
        if (enrich and isinstance(record_id, str) and record_id
                and ("workflow_action" in node or "document_id" in node)):
            inline = _extract_url(str(node.get("feishu_cloud_doc") or ""))
            if inline:
                node["feishu_doc"] = inline
            elif budget[0] > 0:
                budget[0] -= 1
                link = _fetch_feishu_doc_link(record_id)
                if link:
                    node["feishu_doc"] = link
        for value in node.values():
            _scrub_document_link(value, enrich=enrich, budget=budget)
    elif isinstance(node, list):
        for value in node:
            _scrub_document_link(value, enrich=enrich, budget=budget)


def queue_query(arguments: dict) -> dict:
    record_id = str(arguments.get("record_id", "")).strip()
    queue_scope = str(arguments.get("queue_scope", "")).strip()
    if not record_id or not queue_scope:
        return {"ok": False,
                "error": "record_id and queue_scope are required; take both from a "
                         "queue_resolve result row"}
    argv = [
        VENV_PYTHON, "build.py", "queue-query",
        "--config", CONTROL_CONFIG,
        "--queue-scope", queue_scope,
        "--record-id", record_id,
        "--json",
    ]
    fresh_since = str(arguments.get("fresh_since", "")).strip()
    if fresh_since:
        argv.extend(["--fresh-since", fresh_since])
    outcome = run_subprocess(argv)
    if outcome.get("ok"):
        _scrub_document_link(outcome, enrich=True, budget=[3])
    return outcome


def manual_index_query(arguments: dict) -> dict:
    query_text = str(arguments.get("query_text", "")).strip()
    if not query_text:
        return {"ok": False, "error": "query_text is required"}
    argv = [
        VENV_PYTHON, "build.py", "manual-index-query",
        "--config", CONTROL_CONFIG,
        "--query-text", query_text,
        "--limit", str(int(arguments.get("limit", 10))),
        "--json",
    ]
    return run_subprocess(argv)


def lark_cli_argv(args: list[str]) -> list[str]:
    """Pin business-plane calls to the configured prod bot identity."""
    argv = [LARK_CLI, "--profile", LARK_CLI_PROFILE, *args]
    if "--as" not in args:
        argv.extend(["--as", LARK_CLI_IDENTITY])
    return argv


def run_lark_cli(args: list[str], cwd: str | None = None) -> dict:
    """Run lark-cli, parse its JSON output; return {} shape errors as ok:False."""
    outcome = run_subprocess(lark_cli_argv(args), cwd=cwd)
    if not outcome.get("ok"):
        return outcome
    payload = outcome.get("result")
    if isinstance(payload, dict):
        if payload.get("ok") is False:
            return {"ok": False, "error": "lark-cli error",
                    "detail": payload.get("error")}
        return {"ok": True, "data": payload.get("data", {})}
    return {"ok": False, "error": "unexpected lark-cli output",
            "raw": str(outcome.get("result_text", ""))[:400]}


def lark_records_all(table_id: str, max_pages: int = 10,
                     document_key: str | None = None) -> dict:
    """Read all rows of a bitable table via lark-cli columnar record-list.

    document_key filters server-side (avoids the 200-row truncation trap on
    big tables when only one target's rows are needed).
    """
    columns: list[str] = []
    rows: list[list] = []
    record_ids: list[str] = []
    offset = 0
    filter_args: list[str] = []
    if document_key:
        filter_args = ["--filter-json", json.dumps(
            {"logic": "and",
             "conditions": [["document_key", "is", document_key]]})]
    for _ in range(max_pages):
        page = run_lark_cli([
            "base", "+record-list", "--base-token", BUILD_BASE_TOKEN,
            "--table-id", table_id, "--format", "json",
            "--limit", "200", "--offset", str(offset), *filter_args,
        ])
        if not page.get("ok"):
            return page
        data = page["data"]
        columns = data.get("fields") or columns
        page_rows = data.get("data") or []
        rows.extend(page_rows)
        record_ids.extend(data.get("record_id_list") or [])
        if len(page_rows) < 200:
            break
        offset += 200
    return {"ok": True, "columns": columns, "rows": rows, "record_ids": record_ids}


def _cell(columns: list[str], row: list, name: str):
    try:
        value = row[columns.index(name)]
    except (ValueError, IndexError):
        return None
    return value


def _crosswalk(table_id: str, key_col: str, value_col: str) -> dict:
    result = lark_records_all(table_id)
    if not result.get("ok"):
        return {}
    mapping = {}
    for row in result["rows"]:
        key = _cell(result["columns"], row, key_col)
        value = _cell(result["columns"], row, value_col)
        if isinstance(key, str) and isinstance(value, str) and key and value:
            mapping[key.strip()] = value.strip()
    return mapping


def dingtalk_sync_pending(_arguments: dict) -> dict:
    """List build-table rows checked 是否上传钉钉 and not yet synced, with key crosswalks."""
    table = lark_records_all(BUILD_TABLE_ID)
    if not table.get("ok"):
        return table
    region_map = _crosswalk(REGION_DICT_TABLE_ID, "Region", "钉钉组合代码")
    lang_map = _crosswalk(LANG_DICT_TABLE_ID, "缩写", "钉钉语言代码")
    columns = table["columns"]
    pending, failed, synced_count = [], [], 0
    for record_id, row in zip(table["record_ids"], table["rows"]):
        if _cell(columns, row, "是否上传钉钉") is not True:
            continue
        status_cell = _cell(columns, row, "钉钉对接状态")
        status = status_cell.get("name") if isinstance(status_cell, dict) else status_cell
        if status == "已同步":
            synced_count += 1
            continue
        document_id = _cell(columns, row, "Document_ID") or ""
        # Document_ID 可能带版本尾缀（JE-1000F_US_1.5）：从后往前找 Region token 段
        parts = str(document_id).split("_")
        model, region = "", ""
        for i in range(len(parts) - 1, 0, -1):
            if parts[i] in region_map:
                model, region = "_".join(parts[:i]), parts[i]
                break
        combo = region_map.get(region, "")
        lang_raw = _cell(columns, row, "Lang")
        lang_name = lang_raw.get("name") if isinstance(lang_raw, dict) else lang_raw
        entry = {
            "record_id": record_id,
            "document_id": document_id,
            "task_id": _cell(columns, row, "Task_id"),
            "version": (_cell(columns, row, "Version") or {}).get("name")
                       if isinstance(_cell(columns, row, "Version"), dict)
                       else _cell(columns, row, "Version"),
            "lang": lang_name,
            "feishu_doc": _cell(columns, row, "飞书云文档"),
            "dingtalk_target_node": _cell(columns, row, "钉钉上传节点"),
            "existing_dingtalk_link": _cell(columns, row, "Document link_dd"),
            "build_result": str(_cell(columns, row, "构建结果") or "")[:120],
            "dingtalk_key_prefix": f"{model}_{combo}" if model and combo else None,
            "lang_dd": lang_map.get(str(lang_name), None) if lang_name else None,
        }
        (failed if status == "失败" else pending).append(entry)
    return {
        "ok": True,
        "pending": pending,
        "failed_needs_operator": failed,
        "already_synced": synced_count,
        "region_crosswalk": region_map,
        "lang_crosswalk": lang_map,
        "note": "失败行不自动重试——操作员核因后把 钉钉对接状态 改回 待同步 才会重新出现在 pending。",
    }


STATE_DIR = os.path.expanduser(os.environ.get(
    "HELLO_DOCS_BRIDGE_STATE_DIR", "~/.local/state/hello-docs-bridge"
))
EXPORTS_DIR = os.path.join(STATE_DIR, "exports")
VALID_EXPORT_EXT = ("pdf", "docx")
EXPORT_TOOL_BUDGET_SECONDS = 42  # 悟空 MCP 工具 60s 上限内留余量


def _newest_export(ext: str, before: set) -> str | None:
    candidates = [os.path.join(EXPORTS_DIR, f) for f in os.listdir(EXPORTS_DIR)
                  if f.endswith("." + ext) and f not in before]
    return max(candidates, key=os.path.getmtime) if candidates else None


def feishu_doc_export(arguments: dict) -> dict:
    """Export a Feishu cloud doc to a local file for DingTalk import.

    Two-phase: first call starts the export and polls within budget; if the doc
    renders slowly, returns status=processing with ticket/obj_token — call again
    passing them back to resume polling + download.
    """
    import re
    import time
    start = time.monotonic()
    ext = str(arguments.get("file_extension", "pdf")).strip().lower()
    file_name = str(arguments.get("file_name", "")).strip()
    ticket = str(arguments.get("ticket", "")).strip()
    obj_token = str(arguments.get("obj_token", "")).strip()
    if ext not in VALID_EXPORT_EXT:
        return {"ok": False, "error": f"file_extension must be one of {VALID_EXPORT_EXT}"}
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    before = set(os.listdir(EXPORTS_DIR))

    if not ticket:
        url = str(arguments.get("url", "")).strip()
        if not url.startswith("http"):
            return {"ok": False, "error": "url is required (飞书云文档/wiki 链接)"}
        if "/wiki/" in url and not obj_token:
            node = run_lark_cli(["wiki", "+node-get", "--node-token", url])
            if node.get("ok"):
                obj_token = node["data"].get("obj_token", "")
        elif not obj_token:
            path_match = re.search(r"/(?:docx|docs)/([A-Za-z0-9]+)", url)
            obj_token = path_match.group(1) if path_match else ""
        argv = lark_cli_argv([
            "drive", "+export", "--url", url, "--file-extension", ext,
            "--output-dir", ".", "--overwrite",
        ])
        if file_name:
            argv.extend(["--file-name", file_name])
        outcome = run_subprocess(argv, cwd=EXPORTS_DIR)
        payload = outcome.get("result")
        if isinstance(payload, dict) and payload.get("ok"):
            saved = _newest_export(ext, before)
            if saved:
                return {"ok": True, "file_path": saved,
                        "file_name": os.path.basename(saved),
                        "size_bytes": os.path.getsize(saved),
                        "hint": "用钉钉文档导入能力把此本地文件上传到目标节点，成功后取文档链接"}
        stderr = str(outcome.get("stderr_tail", ""))
        ticket_match = re.search(r"export task:\s*(\d+)", stderr)
        if not ticket_match:
            return {"ok": False, "error": "export failed", "detail": payload or outcome}
        ticket = ticket_match.group(1)

    poll_argv = ["drive", "+task_result", "--ticket", ticket,
                 "--scenario", "export"]
    if obj_token:
        poll_argv.extend(["--file-token", obj_token])
    export_file_token = ""
    while time.monotonic() - start < EXPORT_TOOL_BUDGET_SECONDS:
        poll = run_lark_cli(poll_argv)
        data = poll.get("data", {}) if poll.get("ok") else {}
        if data.get("ready") and not data.get("failed"):
            export_file_token = data.get("file_token", "")
            break
        if data.get("failed"):
            return {"ok": False, "error": "export task failed",
                    "detail": data.get("job_error_msg")}
        time.sleep(3)
    if not export_file_token:
        return {"ok": True, "status": "processing", "ticket": ticket,
                "obj_token": obj_token,
                "hint": "导出仍在进行——再次调用 feishu_doc_export 并传回 ticket/obj_token 续传"}
    dl_argv = ["drive", "+export-download", "--file-token", export_file_token,
               "--output-dir", ".", "--overwrite"]
    if file_name:
        dl_argv.extend(["--file-name", file_name])
    download = run_lark_cli(dl_argv, cwd=EXPORTS_DIR)
    if not download.get("ok"):
        return {"ok": False, "error": "download failed", "detail": download}
    saved = _newest_export(ext, before)
    if not saved:
        return {"ok": False, "error": "download reported success but no local file found",
                "download_data": download.get("data")}
    return {"ok": True, "file_path": saved,
            "file_name": os.path.basename(saved),
            "size_bytes": os.path.getsize(saved),
            "hint": "用钉钉文档导入能力把此本地文件上传到目标节点，成功后取文档链接"}


JOBS_DIR = os.path.join(STATE_DIR, "jobs")


def _spawn_job(driver: str, driver_args: list[str]) -> str:
    """Start a detached long-running driver; returns job_id for polling."""
    import uuid
    job_id = uuid.uuid4().hex[:12]
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    log_path = os.path.join(job_dir, "job.log")
    cmd = [VENV_PYTHON, str(BRIDGE_DIR / driver), *driver_args,
           "--job-dir", job_dir]
    job_env = dict(merged_env())
    job_env["FEISHU_PHASE2_IDENTITY"] = LARK_CLI_IDENTITY
    job_env["LARK_CLI_PROFILE"] = LARK_CLI_PROFILE
    job_env["LARK_CLI_IDENTITY"] = LARK_CLI_IDENTITY
    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(cmd, stdout=log_file,
                                stderr=subprocess.STDOUT,
                                start_new_session=True, env=job_env)
    with open(os.path.join(job_dir, "status.json"), "w") as handle:
        json.dump({"status": "running", "pid": proc.pid, "driver": driver}, handle)
    return job_id


def _poll_job(job_id: str) -> dict:
    job_dir = os.path.join(JOBS_DIR, job_id)
    result_path = os.path.join(job_dir, "result.json")
    if os.path.isfile(result_path):
        with open(result_path) as handle:
            return {"ok": True, "job_id": job_id, **json.load(handle)}
    status_path = os.path.join(job_dir, "status.json")
    if not os.path.isfile(status_path):
        return {"ok": False, "error": f"unknown job_id {job_id}"}
    with open(status_path) as handle:
        status = json.load(handle)
    pid = status.get("pid")
    try:
        os.kill(int(pid), 0)
        alive = True
    except (OSError, TypeError, ValueError):
        alive = False
    if alive:
        return {"ok": True, "job_id": job_id, "status": "running",
                "hint": "作业仍在运行（诊断通常 4-6 分钟）——过几分钟带同一个 job_id 再查。"}
    tail = ""
    log_path = os.path.join(job_dir, "job.log")
    if os.path.isfile(log_path):
        with open(log_path, errors="replace") as handle:
            tail = handle.read()[-800:]
    return {"ok": False, "job_id": job_id, "status": "failed",
            "error": "作业进程已退出但没有写结果", "log_tail": tail}


def idml_gate_diff(arguments: dict) -> dict:
    job_id = str(arguments.get("job_id", "")).strip()
    if job_id:
        return _poll_job(job_id)
    model = str(arguments.get("model", "")).strip()
    region = str(arguments.get("region", "")).strip().upper()
    if not model or not region:
        return {"ok": False, "error": "model 和 region 必填（如 JE-1000F / US）"}
    new_id = _spawn_job("gate_diff_driver.py",
                        ["--model", model, "--region", region])
    return {"ok": True, "job_id": new_id, "status": "running",
            "hint": ("诊断已启动（复现构建约 4-6 分钟）。过几分钟用同一工具带 "
                     f"job_id={new_id} 查询结果；结论 verdict=content_only 才可走批准重绑。")}


def idml_gate_rebind(arguments: dict) -> dict:
    job_id = str(arguments.get("job_id", "")).strip()
    if job_id:
        return _poll_job(job_id)
    diff_job_id = str(arguments.get("diff_job_id", "")).strip()
    approved_by = str(arguments.get("approved_by", "")).strip()
    if not diff_job_id or not approved_by:
        return {"ok": False,
                "error": "diff_job_id 与 approved_by 必填——必须先有 content_only 的诊断结论"
                         "且用户在对话中明确说了「批准」。"}
    diff_dir = os.path.join(JOBS_DIR, diff_job_id)
    result_path = os.path.join(diff_dir, "result.json")
    if not os.path.isfile(result_path):
        return {"ok": False, "error": f"诊断作业 {diff_job_id} 无结果——先跑 idml_gate_diff。"}
    with open(result_path) as handle:
        diff_result = json.load(handle)
    if diff_result.get("verdict") != "content_only":
        return {"ok": False,
                "error": f"诊断结论是 {diff_result.get('verdict')!r}，不允许自动重绑："
                         "装配变更/无契约情形需人工排查（把诊断摘要报告给用户）。"}
    driver_args = ["--diff-job-dir", diff_dir, "--approved-by", approved_by]
    note = str(arguments.get("approval_note", "")).strip()
    if note:
        driver_args.extend(["--approval-note", note])
    new_id = _spawn_job("gate_rebind_driver.py", driver_args)
    return {"ok": True, "job_id": new_id, "status": "running",
            "hint": f"重绑已启动（约 1-2 分钟）。带 job_id={new_id} 再查，"
                    "完成后返回 PR 链接（需要用户合并）。"}


VALID_SYNC_STATUS = ("已同步", "失败", "待同步")


def dingtalk_sync_mark(arguments: dict) -> dict:
    """Write back sync status (+ DingTalk link) to a build-table row, with read-back."""
    record_id = str(arguments.get("record_id", "")).strip()
    status = str(arguments.get("status", "")).strip()
    dingtalk_link = str(arguments.get("dingtalk_link", "")).strip()
    if not record_id:
        return {"ok": False, "error": "record_id is required (from dingtalk_sync_pending)"}
    if status not in VALID_SYNC_STATUS:
        return {"ok": False,
                "error": f"status must be one of {VALID_SYNC_STATUS}, got {status!r}"}
    if status == "已同步" and not dingtalk_link:
        return {"ok": False,
                "error": "status=已同步 requires dingtalk_link (钉钉知识库文档链接)"}
    payload: dict = {"钉钉对接状态": status}
    if dingtalk_link:
        payload["Document link_dd"] = dingtalk_link
    write = run_lark_cli([
        "base", "+record-upsert", "--base-token", BUILD_BASE_TOKEN,
        "--table-id", BUILD_TABLE_ID, "--record-id", record_id,
        "--json", json.dumps(payload, ensure_ascii=False),
    ])
    if not write.get("ok"):
        return write
    readback = run_lark_cli([
        "base", "+record-get", "--base-token", BUILD_BASE_TOKEN,
        "--table-id", BUILD_TABLE_ID, "--record-id", record_id,
        "--field-id", "钉钉对接状态", "--field-id", "Document link_dd",
        "--format", "json",
    ])
    return {
        "ok": True,
        "written": payload,
        "readback": readback.get("data") if readback.get("ok") else
                    {"warning": "写入成功但读回失败", "detail": readback.get("error")},
    }


def _norm_cell(value) -> str:
    """select/lookup 的 list 包装、None 统一成纯字符串。"""
    if value is None:
        return ""
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], (str, int, float)):
            return str(value[0]).strip()
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return str(value.get("name", "")).strip()
    return str(value).strip()


def _input_text(value) -> str:
    """Normalize MCP JSON scalar input without turning null into literal 'None'."""
    return "" if value is None else str(value).strip()


def _staging_match_key(columns: list[str], row: list) -> tuple:
    return structure_identity({
        "Page": _cell(columns, row, "Page"),
        "Row_key": _cell(columns, row, "Row_key"),
        "Slot_key": _cell(columns, row, "Slot_key"),
        "Section": _cell(columns, row, "章节"),
        "Line_order": _cell(columns, row, "Line_order"),
    })


def _dataset_structure_rows(dataset: dict, *, section_column: str = "Section") -> list[dict]:
    """Project a live columnar table read into pure structure dictionaries."""
    columns = dataset.get("columns", [])
    return [
        {
            "Page": _cell(columns, row, "Page"),
            "Row_key": _cell(columns, row, "Row_key"),
            "Slot_key": _cell(columns, row, "Slot_key"),
            "Section": _cell(columns, row, section_column),
            "Line_order": _cell(columns, row, "Line_order"),
        }
        for row in dataset.get("rows", [])
    ]


def _sibling_structure(sibling_document_key: str) -> dict:
    """Read the two formal sibling tables used by the intake completeness gate."""
    specs = lark_records_all(SPEC_SOURCE_TABLE_ID, document_key=sibling_document_key)
    if not specs.get("ok"):
        return {"ok": False, "error": "读取姊妹规格参数明细失败", "detail": specs}
    placeholders = lark_records_all(
        PLACEHOLDER_SOURCE_TABLE_ID, document_key=sibling_document_key
    )
    if not placeholders.get("ok"):
        return {"ok": False, "error": "读取姊妹页面占位参数失败", "detail": placeholders}
    references = [
        *_dataset_structure_rows(specs),
        *_dataset_structure_rows(placeholders),
    ]
    if not references:
        return {
            "ok": False,
            "error": f"姊妹目标 {sibling_document_key} 在两张正式源表均无结构行",
        }
    return {
        "ok": True,
        "references": references,
        "spec_rows": len(specs.get("rows", [])),
        "placeholder_rows": len(placeholders.get("rows", [])),
    }


def _kr_staging_violations(document_key: str, columns: list[str], row: list) -> list[dict]:
    """Apply the shared KR contract to one live staging row."""
    return validate_kr_candidate(document_key, {
        field: _cell(columns, row, field)
        for field in (
            "Row_key", "Line_order", "行标签", "手册值", "规格书原值", "Source_lang"
        )
    })


def intake_status(arguments: dict) -> dict:
    """按 document_key（或全表）汇总入库暂存表 + 两张源表现状。只读。"""
    document_key = str(arguments.get("document_key", "")).strip()
    sibling_document_key = str(arguments.get("sibling_document_key", "")).strip()
    staging = lark_records_all(INTAKE_STAGING_TABLE_ID,
                               document_key=document_key or None)
    if not staging.get("ok"):
        return staging
    columns = staging["columns"]
    pending_confirm, confirmed_ready, contract_blocked = [], [], []
    ingested, discarded, failed = 0, [], []
    by_key: dict = {}
    pending_structure_rows: list[dict] = []
    pending_structure_ids: list[str] = []
    for record_id, row in zip(staging["record_ids"], staging["rows"]):
        key = _norm_cell(_cell(columns, row, "document_key"))
        outcome = _norm_cell(_cell(columns, row, "入库结果"))
        entry = {
            "record_id": record_id, "document_key": key,
            "row_key": _norm_cell(_cell(columns, row, "Row_key")),
            "slot_key": _norm_cell(_cell(columns, row, "Slot_key")) or None,
            "line_order": _norm_cell(_cell(columns, row, "Line_order")) or "1",
            "page": _norm_cell(_cell(columns, row, "Page")),
            "section": _norm_cell(_cell(columns, row, "章节")),
            "row_label": _norm_cell(_cell(columns, row, "行标签")),
            "manual_value": _norm_cell(_cell(columns, row, "手册值")),
            "manual_value_ko": _norm_cell(_cell(columns, row, "手册值_ko")),
            "row_label_ko": _norm_cell(_cell(columns, row, "行标签_ko")),
            "source_lang": _norm_cell(_cell(columns, row, "Source_lang")),
            "status": _norm_cell(_cell(columns, row, "状态")),
        }
        bucket = by_key.setdefault(key, {"pending_confirm": 0, "confirmed_ready": 0,
                                         "contract_blocked": 0,
                                         "ingested": 0, "discarded": 0, "failed": 0})
        if not outcome:
            pending_structure_rows.append({
                "Page": _cell(columns, row, "Page"),
                "Row_key": _cell(columns, row, "Row_key"),
                "Slot_key": _cell(columns, row, "Slot_key"),
                "Section": _cell(columns, row, "章节"),
                "Line_order": _cell(columns, row, "Line_order"),
            })
            pending_structure_ids.append(record_id)
        violations = _kr_staging_violations(key, columns, row)
        if outcome.startswith("失败"):
            failed.append({**entry, "入库结果": outcome})
            bucket["failed"] += 1
        elif outcome.startswith("已作废"):
            discarded.append({**entry, "入库结果": outcome})
            bucket["discarded"] += 1
        elif outcome:
            ingested += 1
            bucket["ingested"] += 1
        elif violations:
            contract_blocked.append({**entry, "contract_violations": violations})
            bucket["contract_blocked"] += 1
        elif _cell(columns, row, "确认") is True:
            confirmed_ready.append(entry)
            bucket["confirmed_ready"] += 1
        else:
            pending_confirm.append(entry)
            bucket["pending_confirm"] += 1
    result: dict = {
        "ok": True, "staging_total": len(staging["rows"]),
        "confirmed_ready": confirmed_ready, "pending_confirm": pending_confirm,
        "contract_blocked": contract_blocked,
        "discarded": discarded, "ingest_failed": failed,
        "already_ingested": ingested,
        "by_document_key": by_key,
        "kr_contract": {
            "version": KR_CONTRACT_VERSION,
            "blocked_rows": len(contract_blocked),
            "rule": ("KR 首次入库只要求英文手册值与英文行标签，Source_lang=en；"
                     "韩文列为可选后续本地化层；英文值同时执行单位/DC符号与多行语义校验"),
        },
        "hint": "confirmed_ready 才会被 intake_commit 搬运；pending_confirm 要操作员"
                "在入库表里核值并勾「确认」。",
    }
    if is_kr_document_key(document_key) and sibling_document_key:
        sibling_structure = _sibling_structure(sibling_document_key)
        if sibling_structure.get("ok"):
            structure_preflight = validate_sibling_structure(
                pending_structure_rows,
                sibling_structure["references"],
                require_complete=False,
            )
            for violation in structure_preflight["violations"]:
                index = violation.get("index")
                if isinstance(index, int) and index < len(pending_structure_ids):
                    violation["record_id"] = pending_structure_ids[index]
            result["structure_preflight"] = structure_preflight
            result["coverage_complete"] = structure_preflight["complete"]
        else:
            result["structure_preflight"] = sibling_structure
            result["coverage_complete"] = False
        result["sibling_document_key"] = sibling_document_key
    if document_key:
        for label, table_id in (("spec_rows", SPEC_SOURCE_TABLE_ID),
                                ("placeholder_rows", PLACEHOLDER_SOURCE_TABLE_ID)):
            source = lark_records_all(table_id, document_key=document_key)
            result[f"source_{label}"] = len(source.get("rows", [])) \
                if source.get("ok") else f"读取失败: {source.get('error')}"
    return result


INTAKE_STAGE_FIELDS = ["document_key", "Row_key", "Slot_key", "Line_order", "Page",
                       "章节", "行标签", "行标签_ko", "规格书字段", "规格书原值",
                       "手册值", "手册值_ko", "Source_lang", "备注", "状态"]
INTAKE_STAGE_MAX_ROWS = 80


def intake_stage(arguments: dict) -> dict:
    """Stage structured rows after KR source and sibling-structure preflight."""
    document_key = str(arguments.get("document_key", "")).strip()
    sibling_document_key = str(arguments.get("sibling_document_key", "")).strip()
    rows = arguments.get("rows")
    source_lang = str(arguments.get("source_lang", "en")).strip() or "en"
    if not document_key or "_" not in document_key:
        return {"ok": False,
                "error": "document_key 必填且形如 JE-1000F_AU（规范机型_区域）"}
    if not isinstance(rows, list) or not rows:
        return {"ok": False, "error": "rows 必填：结构化行对象数组"}
    if len(rows) > INTAKE_STAGE_MAX_ROWS:
        return {"ok": False,
                "error": f"单次最多 {INTAKE_STAGE_MAX_ROWS} 行，请分批"}
    existing = lark_records_all(INTAKE_STAGING_TABLE_ID, document_key=document_key)
    if not existing.get("ok"):
        return existing
    is_kr = is_kr_document_key(document_key)
    if is_kr:
        if not sibling_document_key or "_" not in sibling_document_key:
            return {
                "ok": False,
                "error": "KR 暂存必须指定 sibling_document_key，禁止悟空自行猜结构",
                "contract_version": KR_CONTRACT_VERSION,
                "staged": 0,
            }
        if sibling_document_key == document_key:
            return {
                "ok": False,
                "error": "sibling_document_key 不能与目标 document_key 相同",
                "contract_version": KR_CONTRACT_VERSION,
                "staged": 0,
            }
        absent = missing_fields(existing["columns"], KR_STAGING_REQUIRED_FIELDS)
        if absent:
            return {
                "ok": False,
                "error": "KR 暂存合同无法执行：暂存表缺少必需字段",
                "contract_version": KR_CONTRACT_VERSION,
                "missing_fields": absent,
                "staged": 0,
            }
        sibling_structure = _sibling_structure(sibling_document_key)
        if not sibling_structure.get("ok"):
            return {
                **sibling_structure,
                "contract_version": KR_CONTRACT_VERSION,
                "staged": 0,
            }
    else:
        sibling_structure = None
    write_fields = [field for field in INTAKE_STAGE_FIELDS
                    if field in existing["columns"]]
    pending_keys = set()
    before_ids = set(existing["record_ids"])
    for row in existing["rows"]:
        if not _norm_cell(_cell(existing["columns"], row, "入库结果")):
            pending_keys.add(_staging_match_key(existing["columns"], row))
    accepted, invalid, duplicates = [], [], []
    structure_candidates: list[dict] = []
    expected_by_key: dict[tuple, dict] = {}
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            invalid.append({"index": index, "reason": "行必须是对象"})
            continue
        row_key = _input_text(raw.get("Row_key", ""))
        page = _input_text(raw.get("Page", ""))
        manual_value = _input_text(raw.get("手册值", raw.get("manual_value", "")))
        manual_value_ko = _input_text(raw.get(
            "手册值_ko", raw.get("manual_value_ko", "")
        ))
        raw_value = _input_text(raw.get("规格书原值", raw.get("raw_value", "")))
        row_label = _input_text(raw.get("行标签", raw.get("row_label", "")))
        row_label_ko = _input_text(raw.get(
            "行标签_ko", raw.get("row_label_ko", "")
        ))
        row_source_lang = _input_text(raw.get("Source_lang", source_lang)) or source_lang
        if not row_key or not page:
            invalid.append({"index": index, "reason": "Row_key 与 Page 必填"})
            continue
        line_order = raw.get("Line_order", 1)
        try:
            line_order = int(line_order)
        except (TypeError, ValueError):
            invalid.append({"index": index, "reason": "Line_order 必须是整数"})
            continue
        if line_order < 1:
            invalid.append({"index": index, "reason": "Line_order 必须大于等于 1"})
            continue
        if is_kr:
            violations = validate_kr_candidate(document_key, {
                "Row_key": row_key,
                "Line_order": line_order,
                "行标签": row_label,
                "手册值": manual_value,
                "规格书原值": raw_value,
                "Source_lang": row_source_lang,
            })
            if manual_value_ko and "手册值_ko" not in existing["columns"]:
                violations.append({
                    "code": "LOCALIZATION_FIELD_MISSING",
                    "field": "手册值_ko",
                    "message": "提供了韩文值，但暂存表没有手册值_ko字段",
                })
            if row_label_ko and "行标签_ko" not in existing["columns"]:
                violations.append({
                    "code": "LOCALIZATION_FIELD_MISSING",
                    "field": "行标签_ko",
                    "message": "提供了韩文标签，但暂存表没有行标签_ko字段",
                })
            if violations:
                invalid.append({
                    "index": index,
                    "row_key": row_key,
                    "reason": "KR source-first 合同不满足",
                    "contract_violations": violations,
                })
                continue
        elif not manual_value and not raw_value:
            invalid.append({"index": index,
                            "reason": "手册值 与 规格书原值 至少填一个"})
            continue
        slot_key = _input_text(raw.get("Slot_key", ""))
        section = _input_text(raw.get("章节", raw.get("section", "")))
        match_key = structure_identity({
            "Page": page,
            "Row_key": row_key,
            "Slot_key": slot_key,
            "Section": section,
            "Line_order": line_order,
        })
        if match_key in pending_keys:
            duplicates.append({"index": index, "row_key": row_key,
                               "reason": "暂存表已有同键待处理行（未入库），不重复暂存"})
            continue
        pending_keys.add(match_key)
        staged_row = [
            document_key, row_key, slot_key or None, line_order, page,
            section or None,
            row_label or None, row_label_ko or None,
            _input_text(raw.get("规格书字段", raw.get("spec_field", ""))) or None,
            raw_value or None, manual_value or None, manual_value_ko or None,
            row_source_lang,
            _input_text(raw.get("备注", raw.get("note", ""))) or "悟空暂存",
            "⚠️需确认",
        ]
        accepted.append(staged_row)
        staged_fields = dict(zip(INTAKE_STAGE_FIELDS, staged_row))
        structure_candidates.append({
            "Page": staged_fields["Page"],
            "Row_key": staged_fields["Row_key"],
            "Slot_key": staged_fields["Slot_key"],
            "Section": staged_fields["章节"],
            "Line_order": staged_fields["Line_order"],
        })
        expected_by_key[match_key] = {
            field: staged_fields[field] for field in write_fields
        }
    structure_preflight = None
    coverage_preflight = None
    if is_kr and not invalid:
        structure_preflight = validate_sibling_structure(
            structure_candidates,
            sibling_structure["references"],
            require_complete=False,
        )
        if structure_preflight["violations"]:
            invalid.append({
                "reason": "姊妹结构预检失败",
                "structure_violations": structure_preflight["violations"],
            })
        else:
            existing_pending_structure = []
            for existing_row in existing["rows"]:
                if _norm_cell(_cell(existing["columns"], existing_row,
                                    "入库结果")):
                    continue
                existing_pending_structure.append({
                    "Page": _cell(existing["columns"], existing_row, "Page"),
                    "Row_key": _cell(existing["columns"], existing_row, "Row_key"),
                    "Slot_key": _cell(existing["columns"], existing_row, "Slot_key"),
                    "Section": _cell(existing["columns"], existing_row, "章节"),
                    "Line_order": _cell(existing["columns"], existing_row,
                                        "Line_order"),
                })
            coverage_preflight = validate_sibling_structure(
                [*existing_pending_structure, *structure_candidates],
                sibling_structure["references"],
                require_complete=False,
            )
    if is_kr and invalid:
        return {
            "ok": False,
            "error": "KR 暂存批次被原子拒绝：修正英文源或姊妹结构违规后整批重试",
            "contract_version": KR_CONTRACT_VERSION,
            "staged": 0,
            "invalid": invalid,
            "duplicates": duplicates,
            "structure_preflight": structure_preflight,
            "coverage_preflight": coverage_preflight,
        }
    if accepted:
        write = run_lark_cli([
            "base", "+record-batch-create", "--base-token", BUILD_BASE_TOKEN,
            "--table-id", INTAKE_STAGING_TABLE_ID,
            "--json", json.dumps({
                "fields": write_fields,
                "rows": [[dict(zip(INTAKE_STAGE_FIELDS, row))[field]
                          for field in write_fields] for row in accepted],
            },
                                 ensure_ascii=False),
        ])
        if not write.get("ok"):
            return {"ok": False, "error": "暂存写入失败", "detail": write,
                    "invalid": invalid, "duplicates": duplicates}
    after = lark_records_all(INTAKE_STAGING_TABLE_ID, document_key=document_key)
    if not after.get("ok"):
        return {
            "ok": False,
            "error": "暂存写入后读回失败；不能声称暂存成功",
            "detail": after,
            "staged": len(accepted),
            "contract_version": KR_CONTRACT_VERSION if is_kr else None,
        }
    new_rows = [
        (rid, row) for rid, row in zip(after["record_ids"], after["rows"])
        if rid not in before_ids
    ]
    new_ids = [rid for rid, _row in new_rows]
    readback_errors: list[dict] = []
    for record_id, row in new_rows:
        match_key = _staging_match_key(after["columns"], row)
        expected = expected_by_key.get(match_key)
        if expected is None:
            readback_errors.append({"record_id": record_id,
                                    "reason": "出现非本批次的新记录键",
                                    "match_key": match_key})
            continue
        mismatched_fields = []
        for field, expected_value in expected.items():
            actual_value = _norm_cell(_cell(after["columns"], row, field))
            if actual_value != _norm_cell(expected_value):
                mismatched_fields.append({"field": field,
                                          "expected": _norm_cell(expected_value),
                                          "actual": actual_value})
        if _cell(after["columns"], row, "确认") is True:
            mismatched_fields.append({"field": "确认", "expected": False,
                                      "actual": True})
        if _norm_cell(_cell(after["columns"], row, "入库结果")):
            mismatched_fields.append({"field": "入库结果", "expected": "",
                                      "actual": _norm_cell(
                                          _cell(after["columns"], row, "入库结果"))})
        contract_violations = _kr_staging_violations(document_key,
                                                      after["columns"], row)
        if mismatched_fields or contract_violations:
            readback_errors.append({
                "record_id": record_id,
                "match_key": match_key,
                "mismatched_fields": mismatched_fields,
                "contract_violations": contract_violations,
            })
    readback_matches = (len(new_rows) == len(accepted) and not readback_errors)
    return {
        "ok": readback_matches, "document_key": document_key,
        "contract_version": KR_CONTRACT_VERSION if is_kr else None,
        "sibling_document_key": sibling_document_key or None,
        "staged": len(accepted), "staged_record_ids": new_ids,
        "readback_new_rows": len(new_ids),
        "readback_matches_staged": readback_matches,
        "readback_errors": readback_errors,
        "invalid": invalid, "duplicates": duplicates,
        "structure_preflight": structure_preflight,
        "coverage_preflight": coverage_preflight,
        "coverage_complete": coverage_preflight["complete"]
                             if coverage_preflight else None,
        "coverage_missing_rows": coverage_preflight["missing_rows"]
                                 if coverage_preflight else [],
        "next": "请操作员在入库表里核对每行手册值（英文源值——韩文等译文属后续本地化，"
                "只进 *_ko 列，勿填进手册值）并勾「确认」；然后对我说「入库 "
                f"{document_key}」触发 intake_commit（新目标需同时指定姊妹机）。",
    }


def intake_discard(arguments: dict) -> dict:
    """Mark obsolete unconfirmed staging rows as discarded without deleting them."""
    document_key = str(arguments.get("document_key", "")).strip()
    record_ids = arguments.get("record_ids")
    reason = str(arguments.get("reason", "")).strip()
    discarded_by = str(arguments.get("discarded_by", "")).strip()
    if not document_key or not isinstance(record_ids, list) or not record_ids:
        return {"ok": False, "error": "document_key 与非空 record_ids 数组必填"}
    if not arguments.get("confirm_discard"):
        return {
            "ok": False,
            "error": "作废拒绝：只有用户本轮明确要求作废旧暂存，才可传 confirm_discard=true",
        }
    if not reason or not discarded_by:
        return {"ok": False, "error": "reason 与 discarded_by 必填，供审计追溯"}
    wanted = [str(item).strip() for item in record_ids if str(item).strip()]
    if len(wanted) != len(set(wanted)) or len(wanted) > INTAKE_STAGE_MAX_ROWS:
        return {"ok": False, "error": "record_ids 不得重复，单次最多 80 条"}
    staging = lark_records_all(INTAKE_STAGING_TABLE_ID, document_key=document_key)
    if not staging.get("ok"):
        return staging
    rows_by_id = dict(zip(staging["record_ids"], staging["rows"]))
    preflight_errors = []
    for record_id in wanted:
        row = rows_by_id.get(record_id)
        if row is None:
            preflight_errors.append({"record_id": record_id, "reason": "不属于目标或不存在"})
            continue
        if _cell(staging["columns"], row, "确认") is True:
            preflight_errors.append({"record_id": record_id, "reason": "已勾确认，拒绝自动作废"})
        outcome = _norm_cell(_cell(staging["columns"], row, "入库结果"))
        if outcome:
            preflight_errors.append({"record_id": record_id,
                                     "reason": f"已有入库结果: {outcome}"})
    if preflight_errors:
        return {"ok": False, "error": "作废预检失败；本批次零写入",
                "preflight_errors": preflight_errors, "discarded": 0}

    from datetime import date
    marker = f"已作废 {date.today().isoformat()} by {discarded_by}: {reason}"
    written = []
    for record_id in wanted:
        outcome = run_lark_cli([
            "base", "+record-upsert", "--base-token", BUILD_BASE_TOKEN,
            "--table-id", INTAKE_STAGING_TABLE_ID, "--record-id", record_id,
            "--json", json.dumps({"入库结果": marker}, ensure_ascii=False),
        ])
        if not outcome.get("ok"):
            return {"ok": False, "error": "作废写入中断", "written": written,
                    "failed_record_id": record_id, "detail": outcome}
        written.append(record_id)
    after = lark_records_all(INTAKE_STAGING_TABLE_ID, document_key=document_key)
    after_by_id = dict(zip(after.get("record_ids", []), after.get("rows", [])))
    mismatches = []
    for record_id in written:
        actual = _norm_cell(_cell(
            after.get("columns", []), after_by_id.get(record_id, []), "入库结果"
        ))
        if actual != marker:
            mismatches.append({"record_id": record_id, "expected": marker,
                               "actual": actual})
    return {
        "ok": not mismatches,
        "document_key": document_key,
        "discarded": len(written),
        "record_ids": written,
        "readback_ok": not mismatches,
        "readback_mismatches": mismatches,
        "marker": marker,
        "next": "重新调用 intake_stage 暂存修正后的有效行；本工具未删除记录。",
    }


def intake_commit(arguments: dict) -> dict:
    """确认行搬进两张源表（后台作业）：UPDATE 已有行 / 按姊妹机克隆 CREATE。写操作。"""
    job_id = str(arguments.get("job_id", "")).strip()
    if job_id:
        return _poll_job(job_id)
    document_key = str(arguments.get("document_key", "")).strip()
    sibling = str(arguments.get("sibling_document_key", "")).strip()
    approved_by = str(arguments.get("approved_by", "")).strip()
    if not document_key:
        return {"ok": False, "error": "document_key 必填（如 JE-1000F_AU）"}
    if not arguments.get("confirm_ingest"):
        return {"ok": False,
                "error": "入库拒绝：双门之二未过。需要用户在对话中明确说「入库」，"
                         "然后带 confirm_ingest=true 重试（门一是表内勾「确认」）。"}
    if not approved_by:
        return {"ok": False, "error": "approved_by 必填（批准人姓名，写入入库结果追溯）"}
    if sibling and "_" not in sibling:
        return {"ok": False, "error": "sibling_document_key 形如 JE-1000F_EU"}
    if is_kr_document_key(document_key):
        if not sibling:
            return {
                "ok": False,
                "error": "KR 入库必须指定 sibling_document_key，禁止无基线提交",
                "contract_version": KR_CONTRACT_VERSION,
            }
        preflight = intake_status({
            "document_key": document_key,
            "sibling_document_key": sibling,
        })
        if not preflight.get("ok"):
            return {"ok": False, "error": "KR 入库前暂存合同检查失败",
                    "detail": preflight}
        if preflight.get("contract_blocked"):
            return {
                "ok": False,
                "error": "KR 入库被拒绝：暂存表存在 source-first 合同违规行",
                "contract_version": KR_CONTRACT_VERSION,
                "contract_blocked": preflight["contract_blocked"],
            }
        structure_preflight = preflight.get("structure_preflight") or {}
        if structure_preflight.get("violations"):
            return {
                "ok": False,
                "error": "KR 入库被拒绝：暂存行不满足姊妹目标结构",
                "contract_version": KR_CONTRACT_VERSION,
                "structure_violations": structure_preflight["violations"],
            }
        if not preflight.get("coverage_complete"):
            return {
                "ok": False,
                "error": "KR 入库被拒绝：两张源表结构覆盖不完整",
                "contract_version": KR_CONTRACT_VERSION,
                "missing_rows": structure_preflight.get("missing_rows", []),
            }
        if not preflight.get("confirmed_ready"):
            return {
                "ok": False,
                "error": "KR 入库被拒绝：没有已勾确认且通过合同检查的待入库行",
                "contract_version": KR_CONTRACT_VERSION,
            }
    driver_args = ["--document-key", document_key, "--approved-by", approved_by]
    if sibling:
        driver_args += ["--sibling-document-key", sibling]
    new_id = _spawn_job("intake_commit_driver.py", driver_args)
    return {"ok": True, "job_id": new_id, "status": "running",
            "contract_version": KR_CONTRACT_VERSION if
                                is_kr_document_key(document_key) else None,
            "hint": (f"入库作业已启动（含逐行读回 + sync-data + check，约 2-5 分钟）。"
                     f"带 job_id={new_id} 再查；结果含 updated/created/failed/skipped "
                     "明细与暂存表回填。")}


def bridge_info(_arguments: dict) -> dict:
    env_files = [
        os.path.expanduser(p.strip())
        for p in os.environ.get("HELLO_DOCS_BRIDGE_ENV_FILES", DEFAULT_ENV_FILES).split(":")
    ]
    return {
        "ok": True,
        "server_name": SERVER_INFO["name"],
        "server_version": SERVER_INFO["version"],
        "bridge_source_dir": str(BRIDGE_DIR),
        "state_dir": STATE_DIR,
        "repo_root": REPO_ROOT,
        "repo_root_exists": os.path.isdir(REPO_ROOT),
        "venv_python_exists": os.path.isfile(VENV_PYTHON),
        "control_config": CONTROL_CONFIG,
        "lark_cli_profile": LARK_CLI_PROFILE,
        "lark_cli_identity": LARK_CLI_IDENTITY,
        "intake_contract_version": KR_CONTRACT_VERSION,
        "env_files": {p: os.path.isfile(p) for p in env_files},
        "subprocess_timeout_seconds": SUBPROC_TIMEOUT_SECONDS,
    }


LANG_PARAM = {"type": "string",
              "description": "目标语言列，如 ko / ja / fr / es / de / it / zh-TW"}

TOOLS: list[dict] = [
    {
        "name": "tm_term_lookup",
        "description": ("查询权威术语表（Feishu TM Base 的 Terms 表）：输入一个短语/词条，"
                        "返回源语言与目标语言的规范术语对。用于术语一致性质检与翻译校对。只读。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query_text": {"type": "string", "description": "要查询的术语，如 handle、AC output"},
                "target_lang": LANG_PARAM,
                "source_lang": {"type": "string", "description": "源语言列，默认 en（简中→繁中用 zh）"},
                "limit": {"type": "integer", "description": "最多返回条数，默认 8"},
            },
            "required": ["query_text", "target_lang"],
        },
    },
    {
        "name": "tm_sentence_lookup",
        "description": ("查询翻译记忆句对库（Feishu TM Base 的 Translation_Memory 表）：输入整句或段落，"
                        "返回对齐的权威句对。多句输入自动拆分。用于安全警示等固定句式的一致性质检。只读。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query_text": {"type": "string", "description": "要查询的句子或段落"},
                "target_lang": LANG_PARAM,
                "source_lang": {"type": "string", "description": "源语言列，默认 en"},
                "limit": {"type": "integer", "description": "最多返回条数，默认 8"},
                "no_split": {"type": "boolean", "description": "true 时整段作为一个查询单元，不自动拆句"},
            },
            "required": ["query_text", "target_lang"],
        },
    },
    {
        "name": "queue_resolve",
        "description": ("解析飞书构建表：把一句自然语言构建请求（型号/区域/动作）解析成候选队列行，"
                        "返回 record_id、queue_scope、动作与目标信息。只读，不触发任何构建。"
                        "后续 queue_execute / queue_query 的 record_id 和 queue_scope 必须取自本结果。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query_text": {"type": "string",
                               "description": "用户的构建请求原话，如：JE-2000F EU 出 Draft"},
                "confirm_publish": {"type": "boolean",
                                    "description": "仅当用户已明确说'确认发布'时为 true"},
            },
            "required": ["query_text"],
        },
    },
    {
        "name": "queue_execute",
        "description": ("执行一个已解析的构建表行动作（start_review / build_draft_package / publish），"
                        "派发到 GitHub 构建流水线后立即返回（accept-first，不等待构建完成）。"
                        "publish 动作必须 confirm_publish=true，否则拒绝。写操作。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "queue_resolve 结果行的 record_id"},
                "queue_scope": {"type": "string", "description": "queue_resolve 结果行的 queue_scope，原样传回"},
                "action_name": {"type": "string",
                                "enum": ["start_review", "build_draft_package", "publish"],
                                "description": "要执行的动作名"},
                "confirm_publish": {"type": "boolean",
                                    "description": "publish 必须为 true 且用户已明确说'确认发布'"},
                "no_wait": {"type": "boolean", "description": "默认 true：派发后立即返回"},
            },
            "required": ["record_id", "queue_scope"],
        },
    },
    {
        "name": "queue_query",
        "description": ("查询一个构建表行的当前状态：构建结果、版本、进度注记，以及飞书评审文档链接"
                        "（返回中的 feishu_doc 字段，实时读自构建表·飞书云文档列）。"
                        "回答'好了没/链接在哪'必须重新调用本工具，不要凭对话记忆。只读。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "queue_resolve 结果行的 record_id"},
                "queue_scope": {"type": "string", "description": "queue_resolve 结果行的 queue_scope"},
                "fresh_since": {"type": "string", "description": "可选：只接受此时间戳之后刷新的数据"},
            },
            "required": ["record_id", "queue_scope"],
        },
    },
    {
        "name": "manual_index_query",
        "description": ("按型号/区域/关键词查询已构建说明书的索引，返回既有文档的飞书链接。"
                        "用于'给我 XX 的说明书链接'类请求，不触发构建。只读。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query_text": {"type": "string", "description": "查询关键词，如 JE-1000F US"},
                "limit": {"type": "integer", "description": "最多返回条数，默认 10"},
            },
            "required": ["query_text"],
        },
    },
    {
        "name": "dingtalk_sync_pending",
        "description": ("查询飞书构建表中已勾选【是否上传钉钉】且未同步的行（对接钉钉待办清单）。"
                        "返回每行的 Document_ID、飞书文档链接、目标节点、版本语言，以及按字典换算好的"
                        "对接键前缀（Model_组合代码）和语言代码、完整 Region/语言对照表。"
                        "失败行单独列出且不自动重试。只读。"),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "feishu_doc_export",
        "description": ("把飞书云文档（wiki/docx 链接）导出为本地文件（pdf 或 docx），"
                        "供钉钉知识库导入。返回本地文件绝对路径。对接钉钉同步流程第 2.1 步使用。只读。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "飞书云文档链接（构建表·飞书云文档字段的值）"},
                "file_extension": {"type": "string", "enum": ["pdf", "docx"],
                                   "description": "导出格式，默认 pdf（说明书交付口径）"},
                "file_name": {"type": "string",
                              "description": "可选输出文件名（建议用对接键，如 JE-1000F_USCAMX_en-GB_1.1）"},
                "ticket": {"type": "string",
                           "description": "续传用：上次返回 status=processing 时给的 ticket"},
                "obj_token": {"type": "string",
                              "description": "续传用：上次返回的 obj_token，与 ticket 一起传回"},
            },
            "required": [],
        },
    },
    {
        "name": "dingtalk_sync_mark",
        "description": ("同步完成后回写飞书构建表：更新钉钉对接状态（已同步/失败/待同步），"
                        "已同步必须附钉钉知识库文档链接（写入 Document link_dd）。"
                        "写后自动读回验证并返回读回值。写操作。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string",
                              "description": "dingtalk_sync_pending 返回的 record_id"},
                "status": {"type": "string", "enum": ["已同步", "失败", "待同步"],
                           "description": "同步结果状态"},
                "dingtalk_link": {"type": "string",
                                  "description": "钉钉知识库文档链接；status=已同步 时必填"},
            },
            "required": ["record_id", "status"],
        },
    },
    {
        "name": "idml_gate_diff",
        "description": ("Publish 撞同源门（same-source IDML gate）后的自动诊断：后台忠实复现构建"
                        "（镜像 main 代码+评审分支内容+新快照，约 4-6 分钟），把手册 IR 与已批准参考"
                        "版式契约逐页比对。首次调用传 model+region 返回 job_id；之后带 job_id 轮询。"
                        "结论三态：content_only（可批准自动重绑）/ assembly_changed（停，人工排查）/ "
                        "identical|no_contract（门不适用）。只读。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "如 JE-1000F（启动新诊断时必填）"},
                "region": {"type": "string", "description": "如 US（启动新诊断时必填）"},
                "job_id": {"type": "string", "description": "轮询已有诊断作业"},
            },
        },
    },
    {
        "name": "idml_gate_rebind",
        "description": ("操作者批准后的自动契约重绑：基于一个 verdict=content_only 的诊断作业，"
                        "在工程仓执行 rebind --write（写入批准记录）、机械更新测试指纹、跑针对性测试、"
                        "开 auto-manual PR。**必须用户在对话中明确说「批准」才可调用**；装配变更一律拒绝。"
                        "首次调用传 diff_job_id+approved_by 返回 job_id；之后带 job_id 轮询取 PR 链接。写操作。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "diff_job_id": {"type": "string", "description": "content_only 诊断作业的 job_id"},
                "approved_by": {"type": "string", "description": "批准人姓名（写入契约批准记录）"},
                "approval_note": {"type": "string", "description": "可选批准备注"},
                "job_id": {"type": "string", "description": "轮询已有重绑作业"},
            },
        },
    },
    {
        "name": "intake_status",
        "description": ("查询数据入库进度：入库暂存表按 document_key 分组的 待确认/已确认待入库/"
                        "已入库/失败 行清单，以及目标在两张源表（规格参数明细+页面占位参数）的"
                        "现有行数。KR 目标同时返回 source-first 合同违规行，违规行不计入可入库。"
                        "传 sibling_document_key 时还会按 Page+Row_key+Slot_key+Section+Line_order"
                        "核对两张源表覆盖率与错误路由。"
                        "回答'入库到哪一步了/还差什么'用本工具。只读。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_key": {"type": "string",
                                 "description": "可选：只看这个目标（如 JE-1000F_AU）；"
                                                "留空看全部待处理批次"},
                "sibling_document_key": {"type": "string",
                                         "description": "KR 结构审计基线，如 JE-2000E_US"},
            },
        },
    },
    {
        "name": "intake_stage",
        "description": ("把从规格书/聊天里抽取的结构化行写入入库暂存表（数据入库第 1 步）。"
                        "所有行标 ⚠️需确认——操作员必须在表里核值并勾「确认」后才可入库。"
                        "KR 目标执行 source-first 合同：首次入库必须带英文手册值、英文行标签且"
                        "Source_lang=en；手册值_ko/行标签_ko 可留空，后续本地化再补。任一英文"
                        "源字段违规则整批不写。同键待处理行自动去重。"
                        "KR 必须显式指定 sibling_document_key；写前按仓库完整键核对 Page 路由、"
                        "Section、Slot_key 与 Line_order。暂存允许分批，但返回两张源表缺口；"
                        "缺口未清零时 intake_commit 拒绝正式入库。"
                        "只写暂存表，不碰源表。写操作。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_key": {"type": "string",
                                 "description": "目标文档键：规范机型_区域，如 JE-1000F_AU"},
                "sibling_document_key": {"type": "string",
                                         "description": "KR 必填：同产品结构基线，如 JE-2000E_US"},
                "rows": {"type": "array",
                         "description": ("结构化行数组。每行对象字段：Row_key（必填，snake_case，"
                                         "沿用既有词表如 capacity/ac_output/charging_temperature）、"
                                         "Page（必填：specifications 或版块名如 Product overview）、"
                                         "手册值（英文源值，KR首次入库必填）、行标签（英文源标签，"
                                         "KR首次入库必填）、手册值_ko/行标签_ko（可选后续本地化）、"
                                         "规格书原值（原文证据）、"
                                         "Slot_key、Line_order（默认1）、章节、行标签、规格书字段、备注"),
                         "items": {"type": "object"}},
                "source_lang": {"type": "string",
                                "description": "默认 en；JP 目标用 ja（值与标签都用日文）。"
                                               "KR 目标必须 en——韩文绝不进手册值/行标签，"
                                               "只进 *_ko 本地化列（不要从 JP 规则类比外推）"},
            },
            "required": ["document_key", "rows"],
        },
    },
    {
        "name": "intake_discard",
        "description": ("把错误或过期的未确认暂存行标记为已作废，不删除记录、不写正式源表。"
                        "仅接受同一 document_key 下、确认未勾选且入库结果为空的显式 record_ids；"
                        "写后逐行读回。**必须用户本轮明确要求作废旧暂存**，才可传"
                        " confirm_discard=true。写操作。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_key": {"type": "string", "description": "目标文档键"},
                "record_ids": {"type": "array", "items": {"type": "string"},
                               "description": "intake_status 返回的待作废暂存 record_id"},
                "reason": {"type": "string", "description": "作废原因"},
                "discarded_by": {"type": "string", "description": "操作人姓名"},
                "confirm_discard": {"type": "boolean",
                                    "description": "仅当用户本轮明确说作废旧暂存时为 true"},
            },
            "required": ["document_key", "record_ids", "reason", "discarded_by"],
        },
    },
    {
        "name": "intake_commit",
        "description": ("数据入库第 2 步：把暂存表中已勾「确认」且无入库结果的行搬进两张源表"
                        "（后台作业）。KR 首次入库按 source-first 写 Value_source、Row_label_source"
                        "与 Source_lang=en；韩文列有值时才同步写入，不作为首次入库前置条件。"
                        "任一英文源合同或结构预检失败则正式源表零写入。"
                        "已有行→更新；不存在的行→按指定姊妹机克隆新建"
                        "（复用链接字段；Document_key 字典无目标行则拒绝新建）。逐写读回，暂存行"
                        "回填入库结果，收尾自动 sync-data+check。**双门：表内确认 + 用户当轮明确"
                        "说「入库」才可带 confirm_ingest=true**。首次调用返回 job_id，之后带 "
                        "job_id 轮询。写操作。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_key": {"type": "string", "description": "目标文档键，如 JE-1000F_AU"},
                "sibling_document_key": {"type": "string",
                                         "description": ("克隆新建的姊妹机（新目标必填）：同产品他区"
                                                         "给行集（AU→EU），同语言给措辞（JP→JP 姊妹）")},
                "confirm_ingest": {"type": "boolean",
                                   "description": "仅当用户本轮明确说了「入库/确认入库」才为 true"},
                "approved_by": {"type": "string", "description": "批准人姓名（追溯用）"},
                "job_id": {"type": "string", "description": "轮询已有入库作业"},
            },
        },
    },
    {
        "name": "bridge_info",
        "description": "桥自检：返回仓库路径、解释器、配置与 env 文件状态。排障用。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

TOOL_HANDLERS = {
    "tm_term_lookup": lambda args: tm_lookup("term", args),
    "tm_sentence_lookup": lambda args: tm_lookup("sentence", args),
    "queue_resolve": queue_resolve,
    "queue_execute": queue_execute,
    "queue_query": queue_query,
    "manual_index_query": manual_index_query,
    "dingtalk_sync_pending": dingtalk_sync_pending,
    "feishu_doc_export": feishu_doc_export,
    "dingtalk_sync_mark": dingtalk_sync_mark,
    "idml_gate_diff": idml_gate_diff,
    "idml_gate_rebind": idml_gate_rebind,
    "intake_status": intake_status,
    "intake_stage": intake_stage,
    "intake_discard": intake_discard,
    "intake_commit": intake_commit,
    "bridge_info": bridge_info,
}


# ------------------------------------------------------------ protocol layer

def make_response(request_id, result=None, error=None) -> dict:
    message: dict = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    return message


def handle_request(message: dict) -> dict | None:
    method = message.get("method", "")
    request_id = message.get("id")
    is_notification = "id" not in message

    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        client_protocol = (message.get("params") or {}).get("protocolVersion", "2024-11-05")
        return make_response(request_id, {
            "protocolVersion": client_protocol,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "ping":
        return make_response(request_id, {})
    if method == "tools/list":
        return make_response(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return make_response(request_id, error={
                "code": -32602, "message": f"unknown tool: {tool_name}"})
        try:
            outcome = handler(arguments)
        except Exception as exc:  # noqa: BLE001 — tool errors must not kill the server
            log(f"tool {tool_name} crashed: {exc}")
            outcome = {"ok": False, "error": f"internal error: {exc}"}
        return make_response(request_id, {
            "content": [{"type": "text",
                         "text": json.dumps(outcome, ensure_ascii=False, indent=2)}],
            "isError": not outcome.get("ok", False),
        })
    if is_notification:
        return None
    return make_response(request_id, error={"code": -32601, "message": f"method not found: {method}"})


def main() -> None:
    log(f"starting; repo={REPO_ROOT} config={CONTROL_CONFIG}")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            log(f"skipping non-JSON input line ({len(line)} bytes)")
            continue
        response = handle_request(message)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    log("stdin closed; exiting")


if __name__ == "__main__":
    main()
