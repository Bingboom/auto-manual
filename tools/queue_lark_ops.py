from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


def run_lark_cli_json(
    *,
    cli_bin: str,
    args: list[str],
    repo_root: Path,
    resolved_cli_command_parts: Callable[[str], list[str]],
    parse_json_payload: Callable[[str], dict[str, Any]],
    format_command: Callable[[list[str]], str],
    command_failure_message: Callable[[list[str], str, str, int], str],
) -> dict[str, Any]:
    import subprocess

    cmd = [*resolved_cli_command_parts(cli_bin), *args]
    print(f"[build-queue] {format_command(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode:
        raise RuntimeError(command_failure_message(cmd, proc.stdout or "", proc.stderr or "", proc.returncode))
    payload = parse_json_payload(proc.stdout or proc.stderr or "")
    code = payload.get("code")
    if code not in (None, 0):
        message = str(payload.get("msg") or payload.get("message") or "Lark CLI API request failed")
        raise RuntimeError(f"Lark CLI API request failed: {message}")
    return payload


def cli_relative_file_arg(*, repo_root: Path, path: Path) -> str:
    resolved = path.resolve(strict=False)
    resolved_repo_root = repo_root.resolve(strict=False)
    try:
        relative = resolved.relative_to(resolved_repo_root)
    except ValueError as exc:
        raise RuntimeError(f"Artifact output must stay under repo root for lark-cli upload: {resolved}") from exc
    if os.name == "nt":
        return ".\\" + str(relative).replace("/", "\\")
    return "./" + relative.as_posix()


def upload_word_to_drive(
    *,
    cli_bin: str,
    word_output_path: Path,
    identity: str,
    repo_root: Path,
    run_lark_cli_json: Callable[..., dict[str, Any]],
    cli_relative_file_arg: Callable[..., str],
) -> tuple[str, str]:
    if not word_output_path.exists():
        raise RuntimeError(f"Artifact output was not created: {word_output_path}")

    upload_payload = run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "drive",
            "+upload",
            "--as",
            identity,
            "--file",
            cli_relative_file_arg(repo_root=repo_root, path=word_output_path),
            "--name",
            word_output_path.name,
        ],
    )
    upload_data = upload_payload.get("data")
    if not isinstance(upload_data, dict):
        raise RuntimeError("Drive upload response is missing data payload")
    file_token = str(upload_data.get("file_token") or "").strip()
    if not file_token:
        raise RuntimeError("Drive upload response is missing file_token")

    meta_payload = run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "drive",
            "metas",
            "batch_query",
            "--as",
            identity,
            "--data",
            json.dumps(
                {
                    "with_url": True,
                    "request_docs": [{"doc_token": file_token, "doc_type": "file"}],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        ],
    )
    meta_data = meta_payload.get("data")
    if not isinstance(meta_data, dict):
        raise RuntimeError("Drive metadata response is missing data payload")
    metas = meta_data.get("metas")
    if not isinstance(metas, list) or not metas or not isinstance(metas[0], dict):
        raise RuntimeError(f"Drive metadata response is missing file url for file_token={file_token}")
    drive_url = str(metas[0].get("url") or "").strip()
    if not drive_url:
        raise RuntimeError(f"Drive metadata response is missing file url for file_token={file_token}")
    return file_token, drive_url


def _first_nested_string(payload: Any, keys: set[str], *, url_only: bool = False) -> str:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).strip().lower() in keys and isinstance(value, str):
                text = value.strip()
                if text and (not url_only or text.startswith(("http://", "https://"))):
                    return text
        for value in payload.values():
            found = _first_nested_string(value, keys, url_only=url_only)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _first_nested_string(item, keys, url_only=url_only)
            if found:
                return found
    return ""


def import_markdown_to_cloud_doc(
    *,
    cli_bin: str,
    markdown_output_path: Path,
    identity: str,
    repo_root: Path,
    run_lark_cli_json: Callable[..., dict[str, Any]],
    cli_relative_file_arg: Callable[..., str],
    doc_name: str | None = None,
) -> tuple[str, str]:
    if not markdown_output_path.exists():
        raise RuntimeError(f"Markdown output was not created: {markdown_output_path}")

    payload = run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "drive",
            "+import",
            "--as",
            identity,
            "--file",
            cli_relative_file_arg(repo_root=repo_root, path=markdown_output_path),
            "--name",
            doc_name or markdown_output_path.stem,
            "--type",
            "docx",
        ],
    )
    url_keys = {"url", "file_url", "doc_url", "document_url", "cloud_doc_url"}
    cloud_doc_url = _first_nested_string(payload, url_keys, url_only=True)
    if not cloud_doc_url:
        raise RuntimeError("Markdown import response is missing cloud document url")
    token_keys = {"token", "doc_token", "document_token", "obj_token", "file_token"}
    cloud_doc_token = _first_nested_string(payload, token_keys)
    return cloud_doc_token, cloud_doc_url


def wiki_node_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Wiki node response is missing data payload")
    node = data.get("node")
    if not isinstance(node, dict):
        raise RuntimeError("Wiki node response is missing node payload")
    return node


def get_wiki_node(
    *,
    cli_bin: str,
    identity: str,
    token: str,
    obj_type: str | None = None,
    run_lark_cli_json: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    params: dict[str, Any] = {"token": token}
    if obj_type:
        params["obj_type"] = obj_type
    payload = run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "wiki",
            "spaces",
            "get_node",
            "--as",
            identity,
            "--params",
            json.dumps(params, ensure_ascii=False, separators=(",", ":")),
        ],
    )
    return wiki_node_from_payload(payload)


def resolve_wiki_destination(
    *,
    cli_bin: str,
    identity: str,
    binding: Any,
    get_wiki_node: Callable[..., dict[str, Any]],
    wiki_destination_factory: Callable[..., Any],
) -> Any:
    if binding.wiki_parent_token:
        node = get_wiki_node(
            cli_bin=cli_bin,
            identity=identity,
            token=binding.wiki_parent_token,
        )
        space_id = str(node.get("space_id") or "").strip()
        parent_wiki_token = binding.wiki_parent_token
    else:
        node = get_wiki_node(
            cli_bin=cli_bin,
            identity=identity,
            token=binding.base_token,
            obj_type="bitable",
        )
        space_id = str(node.get("space_id") or "").strip()
        parent_wiki_token = str(node.get("parent_node_token") or node.get("node_token") or "").strip()
    if not space_id:
        raise RuntimeError("Wiki destination lookup did not return a space_id")
    if not parent_wiki_token:
        raise RuntimeError("Wiki destination lookup did not return a usable parent_wiki_token")
    return wiki_destination_factory(space_id=space_id, parent_wiki_token=parent_wiki_token)


def host_root_from_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"Could not determine tenant host from URL: {url}")
    return f"{parsed.scheme}://{parsed.netloc}"


def wiki_url_from_host_root(host_root: str, wiki_token: str) -> str:
    return f"{host_root.rstrip('/')}/wiki/{wiki_token}"


def move_result_entry_from_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Wiki task response is missing data payload")
    task = data.get("task")
    if not isinstance(task, dict):
        raise RuntimeError("Wiki task response is missing task payload")
    move_result = task.get("move_result")
    if not isinstance(move_result, list) or not move_result or not isinstance(move_result[0], dict):
        raise RuntimeError("Wiki task response is missing move_result payload")
    return move_result[0]


def wait_for_wiki_move_task(
    *,
    cli_bin: str,
    identity: str,
    task_id: str,
    host_root: str,
    run_lark_cli_json: Callable[..., dict[str, Any]],
    move_result_entry_from_task_payload: Callable[[dict[str, Any]], dict[str, Any]],
    wiki_url_from_host_root: Callable[[str, str], str],
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    for _ in range(20):
        payload = run_lark_cli_json(
            cli_bin=cli_bin,
            args=[
                "api",
                "GET",
                f"/open-apis/wiki/v2/tasks/{task_id}",
                "--params",
                json.dumps({"task_type": "move"}, ensure_ascii=False, separators=(",", ":")),
                "--as",
                identity,
            ],
        )
        entry = move_result_entry_from_task_payload(payload)
        status = entry.get("status")
        status_msg = str(entry.get("status_msg") or "").strip()
        if status == 1 or status_msg == "processing":
            sleep(3.0)
            continue
        if status == 0:
            node = entry.get("node")
            if not isinstance(node, dict):
                raise RuntimeError("Wiki task completed without node payload")
            wiki_token = str(node.get("node_token") or "").strip()
            if not wiki_token:
                raise RuntimeError("Wiki task completed without node_token")
            return wiki_url_from_host_root(host_root, wiki_token)
        raise RuntimeError(f"Wiki move task failed: {status_msg or status}")
    raise RuntimeError(f"Wiki move task timed out: {task_id}")


def move_drive_file_to_wiki(
    *,
    cli_bin: str,
    identity: str,
    file_token: str,
    drive_url: str,
    destination: Any,
    run_lark_cli_json: Callable[..., dict[str, Any]],
    host_root_from_url: Callable[[str], str],
    wiki_url_from_host_root: Callable[[str, str], str],
    wait_for_wiki_move_task: Callable[..., str],
    obj_type: str = "file",
) -> str:
    host_root = host_root_from_url(drive_url)
    payload = run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "api",
            "POST",
            f"/open-apis/wiki/v2/spaces/{destination.space_id}/nodes/move_docs_to_wiki",
            "--as",
            identity,
            "--data",
            json.dumps(
                {
                    "parent_wiki_token": destination.parent_wiki_token,
                    "obj_type": obj_type,
                    "obj_token": file_token,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        ],
    )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Wiki move response is missing data payload")
    wiki_token = str(data.get("wiki_token") or "").strip()
    if wiki_token:
        return wiki_url_from_host_root(host_root, wiki_token)
    task_id = str(data.get("task_id") or "").strip()
    if task_id:
        return wait_for_wiki_move_task(
            cli_bin=cli_bin,
            identity=identity,
            task_id=task_id,
            host_root=host_root,
        )
    if data.get("applied") is True:
        raise RuntimeError("Wiki move requires a permission approval flow before the file can be attached to the knowledge base")
    raise RuntimeError("Wiki move response did not include wiki_token or task_id")
