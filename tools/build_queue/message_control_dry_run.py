#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

from tools.build_paths import load_config as _load_config  # noqa: E402
from tools.build_queue.message_control_entry import run_main as _run_main_impl  # noqa: E402
from tools.build_queue.message_control_runtime import resolve_message_control as _resolve_message_control  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    return _run_main_impl(
        argv,
        root=ROOT,
        config_loader=_load_config,
        resolve_message_control=_resolve_message_control,
    )


if __name__ == "__main__":
    raise SystemExit(main())
