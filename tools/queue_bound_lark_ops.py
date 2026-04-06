from __future__ import annotations

from pathlib import Path
from typing import Any

_DEFAULT_ROOT = Path(__file__).resolve().parents[1]
_repo_root_provider = lambda: _DEFAULT_ROOT

from tools.phase2_support import parse_json_payload, resolved_cli_command_parts  # noqa: E402
from tools.queue_lark_ops import (  # noqa: E402
    cli_relative_file_arg as _cli_relative_file_arg_impl,
    get_wiki_node as _get_wiki_node_impl,
    run_lark_cli_json as _run_lark_cli_json_impl,
)
from tools.queue_runtime import command_failure_message, format_command  # noqa: E402


def set_repo_root_provider(provider) -> None:
    global _repo_root_provider
    _repo_root_provider = provider


def _repo_root() -> Path:
    return Path(_repo_root_provider())


def run_lark_cli_json(*, cli_bin: str, args: list[str]) -> dict[str, Any]:
    return _run_lark_cli_json_impl(
        cli_bin=cli_bin,
        args=args,
        repo_root=_repo_root(),
        resolved_cli_command_parts=resolved_cli_command_parts,
        parse_json_payload=parse_json_payload,
        format_command=format_command,
        command_failure_message=command_failure_message,
    )


def cli_relative_file_arg(path: Path) -> str:
    return _cli_relative_file_arg_impl(repo_root=_repo_root(), path=path)


def get_wiki_node(
    *,
    cli_bin: str,
    identity: str,
    token: str,
    obj_type: str | None = None,
) -> dict[str, Any]:
    return _get_wiki_node_impl(
        cli_bin=cli_bin,
        identity=identity,
        token=token,
        obj_type=obj_type,
        run_lark_cli_json=run_lark_cli_json,
    )
