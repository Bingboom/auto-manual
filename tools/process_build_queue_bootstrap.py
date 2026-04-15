from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tools.queue_bound_lark_ops import set_repo_root_provider as _set_queue_lark_repo_root_provider
from tools.queue_bound_outputs import set_repo_root_provider as _set_queue_output_repo_root_provider
from tools.queue_bound_records import (
    set_config_loader_provider as _set_queue_record_config_loader_provider,
    set_repo_root_provider as _set_queue_record_repo_root_provider,
    set_resolve_config_path_provider as _set_queue_record_resolve_config_path_provider,
)
from tools.queue_bound_runtime import set_repo_root_provider as _set_queue_runtime_repo_root_provider


def configure_queue_bound_providers(
    *,
    repo_root_provider: Callable[[], Path],
    config_loader_provider: Callable[[], Callable[[Path], dict[str, Any]]],
    resolve_config_path_provider: Callable[[], Callable[..., Path]],
) -> None:
    _set_queue_output_repo_root_provider(lambda: repo_root_provider())
    _set_queue_runtime_repo_root_provider(lambda: repo_root_provider())
    _set_queue_lark_repo_root_provider(lambda: repo_root_provider())
    _set_queue_record_repo_root_provider(lambda: repo_root_provider())
    _set_queue_record_config_loader_provider(lambda: config_loader_provider())
    _set_queue_record_resolve_config_path_provider(lambda: resolve_config_path_provider())
