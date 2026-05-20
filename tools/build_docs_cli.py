from __future__ import annotations

import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.us.yaml", help="Path to config yaml")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--model", default=None, help="Target product model for spec filtering")
    ap.add_argument("--region", default=None, help="Target region for spec/product-name filtering")
    ap.add_argument("--lang", default=None, help="Optional language selector for multi-language configs")
    ap.add_argument("--all-targets", action="store_true", help="Build all targets declared in build.targets")
    ap.add_argument("--formats", default=None, help="Comma-separated outputs: html,word,pdf,md")
    ap.add_argument("--pdf-mode", default=None, help="PDF backend: latex or word")
    ap.add_argument("--prepare-only", action="store_true", help="Only materialize target rst bundle")
    ap.add_argument("--clean", action="store_true", help="Delete docs/_build before building")
    ap.add_argument("--no-open", action="store_true", help="Do not open outputs after build (override config)")
    ap.add_argument("--page-selector", default=None, help="Only materialize one exact page selector")
    ap.add_argument("--output-root", default=None, help="Override target output root for this build")
    ap.add_argument("--output-base-root", default=None, help="Override docs/_build base root for this build")
    ap.add_argument("--skip-root-index", action="store_true", help="Do not rewrite docs/index.rst")
    ap.add_argument(
        "--source",
        choices=("auto", "review", "runtime"),
        default="auto",
        help="Content source for bundle materialization: auto, runtime, or review",
    )
    return ap.parse_args(argv)
