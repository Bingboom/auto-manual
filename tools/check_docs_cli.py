from __future__ import annotations

import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run lightweight quality checks against prepared manual bundles.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--docs-build-dir", default=None, help="Override prepared docs/_build root")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
    ap.add_argument("--all-targets", action="store_true", help="Use build.targets from config")
    return ap.parse_args(argv)
