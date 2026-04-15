from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build a Vercel-ready static site from the latest publish HTML output.")
    ap.add_argument(
        "--releases-root",
        default="reports/releases",
        help="Publish release root, relative to repo root by default.",
    )
    ap.add_argument(
        "--output-dir",
        default="site/publish-latest/dist",
        help="Static site output directory, relative to repo root by default.",
    )
    return ap.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _built_at_sort_key(meta_path: Path) -> tuple[float, str]:
    try:
        payload = read_json(meta_path)
    except (OSError, json.JSONDecodeError):
        return (meta_path.stat().st_mtime, meta_path.as_posix())
    built_at_raw = payload.get("built_at")
    if isinstance(built_at_raw, str):
        try:
            return (datetime.fromisoformat(built_at_raw).timestamp(), meta_path.as_posix())
        except ValueError:
            pass
    return (meta_path.stat().st_mtime, meta_path.as_posix())


def latest_publish_meta(releases_root: Path) -> Path:
    candidates = list(releases_root.glob("*/*/*/latest/publish_meta.json"))
    if not candidates:
        raise FileNotFoundError(f"No publish metadata found under {releases_root}")
    candidates.sort(key=_built_at_sort_key, reverse=True)
    return candidates[0]


def copy_contents(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def build_site(*, releases_root: Path, output_dir: Path) -> Path:
    meta_path = latest_publish_meta(releases_root)
    payload = read_json(meta_path)
    html_dir_value = str(payload.get("html_dir") or "").strip()
    if not html_dir_value:
        raise RuntimeError(f"Publish metadata missing html_dir: {meta_path}")
    html_dir = resolve_path(html_dir_value)
    if not html_dir.exists():
        raise FileNotFoundError(f"Publish HTML directory not found: {html_dir}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_contents(html_dir, output_dir)

    generated_dir = output_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(meta_path, generated_dir / "publish_meta.json")

    if not (output_dir / "index.html").exists():
        raise RuntimeError(f"Latest publish HTML site is missing index.html under {output_dir}")
    return output_dir


def main() -> int:
    args = parse_args()
    releases_root = resolve_path(args.releases_root)
    output_dir = resolve_path(args.output_dir)
    built_dir = build_site(releases_root=releases_root, output_dir=output_dir)
    print(f"[publish-latest] dist={built_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
