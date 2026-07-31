from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

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
    ap.add_argument(
        "--single-target",
        action="store_true",
        help="Keep the legacy behavior: publish only the newest target at the site root.",
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
    candidates = latest_publish_metas(releases_root)
    if not candidates:
        raise FileNotFoundError(f"No publish metadata found under {releases_root}")
    return candidates[0]


def latest_publish_metas(releases_root: Path) -> list[Path]:
    candidates = list(releases_root.glob("*/*/*/latest/publish_meta.json"))
    candidates.sort(key=_built_at_sort_key, reverse=True)
    return candidates


def _target_segment(value: Any, *, field_name: str, meta_path: Path) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise RuntimeError(f"Publish metadata missing {field_name}: {meta_path}")
    segment = "".join(char if char.isalnum() or char in "._-" else "-" for char in raw)
    segment = segment.strip(".-")
    if not segment:
        raise RuntimeError(f"Publish metadata has unusable {field_name}: {meta_path}")
    return segment


def target_site_path(payload: dict[str, Any], *, meta_path: Path) -> Path:
    return Path(
        _target_segment(payload.get("model"), field_name="model", meta_path=meta_path),
        _target_segment(payload.get("region"), field_name="region", meta_path=meta_path),
        _target_segment(payload.get("lang"), field_name="lang", meta_path=meta_path),
    )


def _write_root_index(output_dir: Path, entries: list[tuple[Path, dict[str, Any]]]) -> None:
    links = []
    for target_path, payload in entries:
        label = " / ".join(
            str(payload.get(key) or "").strip()
            for key in ("model", "region", "lang")
        )
        href = (target_path / "index.html").as_posix()
        version = str(payload.get("version") or "").strip()
        suffix = f" (v{version})" if version else ""
        links.append(f'      <li><a href="{html.escape(href)}">{html.escape(label)}{html.escape(suffix)}</a></li>')
    body = "\n".join(links)
    (output_dir / "index.html").write_text(
        "<!doctype html>\n"
        '<html lang="en">\n<head><meta charset="utf-8"><title>Published manuals</title></head>\n'
        "<body>\n<h1>Published manuals</h1>\n<ul>\n"
        f"{body}\n"
        "</ul>\n</body>\n</html>\n",
        encoding="utf-8",
    )


def copy_contents(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def _copy_target_site(*, meta_path: Path, payload: dict[str, Any], target_dir: Path) -> None:
    html_dir_value = str(payload.get("html_dir") or "").strip()
    if not html_dir_value:
        raise RuntimeError(f"Publish metadata missing html_dir: {meta_path}")
    html_dir = resolve_path(html_dir_value)
    if not html_dir.exists():
        raise FileNotFoundError(f"Publish HTML directory not found: {html_dir}")
    copy_contents(html_dir, target_dir)
    generated_dir = target_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(meta_path, generated_dir / "publish_meta.json")
    if not (target_dir / "index.html").exists():
        raise RuntimeError(f"Published HTML site is missing index.html under {target_dir}")


def build_site(*, releases_root: Path, output_dir: Path, multi_target: bool = True) -> Path:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    meta_paths = latest_publish_metas(releases_root)
    if not meta_paths:
        raise FileNotFoundError(f"No publish metadata found under {releases_root}")
    if not multi_target:
        meta_path = meta_paths[0]
        payload = read_json(meta_path)
        _copy_target_site(meta_path=meta_path, payload=payload, target_dir=output_dir)
        return output_dir

    entries: list[tuple[Path, dict[str, Any]]] = []
    seen_targets: set[Path] = set()
    for meta_path in meta_paths:
        payload = read_json(meta_path)
        target_path = target_site_path(payload, meta_path=meta_path)
        if target_path in seen_targets:
            raise RuntimeError(f"Duplicate publish target path {target_path}: {meta_path}")
        seen_targets.add(target_path)
        target_dir = output_dir / target_path
        _copy_target_site(meta_path=meta_path, payload=payload, target_dir=target_dir)
        entries.append((target_path, payload))

    generated_dir = output_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    # Keep the newest metadata at the historical location for callers that
    # only need a single summary, while the per-target copies are authoritative.
    shutil.copy2(meta_paths[0], generated_dir / "publish_meta.json")
    (generated_dir / "publish_targets.json").write_text(
        json.dumps(
            [
                {
                    "model": payload.get("model"),
                    "region": payload.get("region"),
                    "lang": payload.get("lang"),
                    "version": payload.get("version"),
                    "built_at": payload.get("built_at"),
                    "path": target_path.as_posix(),
                }
                for target_path, payload in entries
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_root_index(output_dir, entries)
    return output_dir


def main() -> int:
    args = parse_args()
    releases_root = resolve_path(args.releases_root)
    output_dir = resolve_path(args.output_dir)
    built_dir = build_site(
        releases_root=releases_root,
        output_dir=output_dir,
        multi_target=not args.single_target,
    )
    print(f"[publish-latest] dist={built_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
