from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from tools.script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=3)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Write machine-readable workflow metadata for the OpenClaw control layer.")
    ap.add_argument("--output", required=True, help="Metadata JSON path, relative to the repo root by default.")
    ap.add_argument("--workflow-name", required=True, help="Display name of the GitHub workflow.")
    ap.add_argument("--workflow-file", required=True, help="Workflow file path inside the repository.")
    ap.add_argument("--queue-record-id", default="", help="Optional Feishu queue record id.")
    ap.add_argument("--trigger-source", default="", help="Optional trigger source label.")
    ap.add_argument("--openclaw-dispatch-nonce", default="", help="Optional OpenClaw dispatch nonce.")
    ap.add_argument("--publish-url", default="", help="Optional publish URL returned by the deploy step.")
    ap.add_argument(
        "--artifact-name",
        action="append",
        default=[],
        help="Artifact name expected to be uploaded by this workflow. Repeat to record multiple artifacts.",
    )
    ap.add_argument(
        "--releases-root",
        default="reports/releases",
        help="Release metadata root, relative to the repo root by default.",
    )
    return ap.parse_args()


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_iso_timestamp(raw: object) -> float | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return datetime.fromisoformat(raw).timestamp()
    except ValueError:
        return None


def _publish_meta_sort_key(path: Path) -> tuple[float, str]:
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError):
        return (path.stat().st_mtime, path.as_posix())
    built_at = _parse_iso_timestamp(payload.get("built_at"))
    if built_at is None:
        return (path.stat().st_mtime, path.as_posix())
    return (built_at, path.as_posix())


def latest_publish_metadata(releases_root: Path) -> tuple[Path, dict[str, object]] | None:
    if not releases_root.exists():
        return None
    candidates = list(releases_root.glob("*/*/*/latest/publish_meta.json"))
    if not candidates:
        return None
    candidates.sort(key=_publish_meta_sort_key, reverse=True)
    path = candidates[0]
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    return path, payload


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def repo_relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def build_metadata(
    *,
    workflow_name: str,
    workflow_file: str,
    queue_record_id: str,
    trigger_source: str,
    openclaw_dispatch_nonce: str,
    artifact_names: list[str],
    publish_url: str,
    releases_root: Path,
    env: dict[str, str] | None = None,
) -> dict[str, object]:
    env_map = env or os.environ
    run_id = _clean_text(env_map.get("GITHUB_RUN_ID"))
    run_attempt = _clean_text(env_map.get("GITHUB_RUN_ATTEMPT"))
    run_number = _clean_text(env_map.get("GITHUB_RUN_NUMBER"))
    repository = _clean_text(env_map.get("GITHUB_REPOSITORY"))
    server_url = _clean_text(env_map.get("GITHUB_SERVER_URL")) or "https://github.com"
    ref_name = _clean_text(env_map.get("GITHUB_REF_NAME"))
    run_url = ""
    if repository and run_id:
        run_url = f"{server_url.rstrip('/')}/{repository}/actions/runs/{run_id}"

    metadata: dict[str, object] = {
        "workflow_name": workflow_name,
        "workflow_file": workflow_file,
        "queue_record_id": _clean_text(queue_record_id),
        "trigger_source": _clean_text(trigger_source),
        "openclaw_dispatch_nonce": _clean_text(openclaw_dispatch_nonce),
        "artifact_names": [name.strip() for name in artifact_names if name.strip()],
        "publish_url": _clean_text(publish_url),
        "repository": repository,
        "ref_name": ref_name,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "run_number": run_number,
        "run_url": run_url,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    publish_meta = latest_publish_metadata(releases_root)
    if publish_meta is None:
        return metadata

    publish_meta_path, publish_meta_payload = publish_meta
    metadata["publish_metadata_path"] = repo_relative_or_absolute(publish_meta_path)
    metadata["publish_metadata"] = publish_meta_payload
    document_link_url = publish_meta_payload.get("document_link_url")
    html_index = publish_meta_payload.get("html_index")
    word_output_path = publish_meta_payload.get("word_output_path")
    if isinstance(document_link_url, str) and document_link_url.strip():
        metadata["document_link_url"] = document_link_url.strip()
    if isinstance(html_index, str) and html_index.strip():
        metadata["publish_html_index"] = html_index.strip()
    if isinstance(word_output_path, str) and word_output_path.strip():
        metadata["publish_word_output_path"] = word_output_path.strip()
    return metadata


def write_metadata(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    output_path = resolve_repo_path(args.output)
    releases_root = resolve_repo_path(args.releases_root)
    payload = build_metadata(
        workflow_name=args.workflow_name,
        workflow_file=args.workflow_file,
        queue_record_id=args.queue_record_id,
        trigger_source=args.trigger_source,
        openclaw_dispatch_nonce=args.openclaw_dispatch_nonce,
        artifact_names=args.artifact_name,
        publish_url=args.publish_url,
        releases_root=releases_root,
    )
    written = write_metadata(output_path, payload)
    print(f"[openclaw-run-metadata] {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
