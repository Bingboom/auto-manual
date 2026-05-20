from __future__ import annotations

import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.us.yaml", help="Path to config yaml")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--model", default=None, help="Optional product model for include/file paths")
    ap.add_argument("--region", default=None, help="Optional region for include/file paths")
    ap.add_argument("--lang", default=None, help="Optional language selector for multi-language configs")
    return ap.parse_args(argv)
