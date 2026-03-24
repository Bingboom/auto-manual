from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Convert a generated review preview site into Vercel Build Output API static output."
    )
    ap.add_argument(
        "--dist-dir",
        default="site/review-preview/dist",
        help="Existing static preview directory, relative to repo root by default.",
    )
    ap.add_argument(
        "--output-root",
        default=".vercel/output",
        help="Vercel build output directory, relative to repo root by default.",
    )
    return ap.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def copy_contents(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def main() -> int:
    args = parse_args()
    dist_dir = resolve_path(args.dist_dir)
    output_root = resolve_path(args.output_root)
    static_root = output_root / "static"

    if not dist_dir.exists():
        raise FileNotFoundError(f"Preview dist directory not found: {dist_dir}")

    if output_root.exists():
        shutil.rmtree(output_root)

    static_root.mkdir(parents=True, exist_ok=True)
    copy_contents(dist_dir, static_root)
    (output_root / "config.json").write_text(
        json.dumps({"version": 3}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
