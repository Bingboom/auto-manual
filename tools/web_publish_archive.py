"""Opt-in Web Publish archive preparation, success hook and frozen-package retry."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tools.config_loader import load_config_mapping
from tools.utils.path_utils import repo_root
from tools.web_archive_package import digest, package_archive
from tools.web_manual_package import write_json


def archive_settings() -> tuple[Path, dict] | None:
    raw = os.environ.get("AUTO_MANUAL_OSS_ARCHIVE_CONFIG", "")
    if raw == "off":
        return None
    path = Path(raw).expanduser() if raw else Path.home() / ".config/auto-manual/web-archive.json"
    if not path.exists():
        if raw:
            raise ValueError("Configured archive settings file is missing")
        return None
    settings = json.loads(path.read_text(encoding="utf-8"))
    if settings.get('enabled') is not True:
        return None
    return path, settings


def record_status(path: Path, report: dict) -> None:
    try:
        write_json(path, report)
    except OSError:
        print("[oss-archive] cannot save archive report; publication unchanged", file=sys.stderr)


def prepare_web_archive(
    *, config_path: Path, model: str, region: str, version: str, lang: str | None,
    data_root: str | None, source_repo: Path, staged_md: Path, git_ref: str = "",
) -> None:
    """Freeze an archive package while the review worktree still exists.

    Errors are recorded separately. An optional archive must not make the
    existing Web Publish build or its later queue writeback fail.
    """
    report_path = staged_md.parent.parent / "archive-preparation.json"
    try:
        configured = archive_settings()
        if configured is None:
            return
        _, settings = configured
        cfg = load_config_mapping(config_path)
        languages = [lang] if lang else cfg.get('build', {}).get('languages', [])
        if not languages:
            raise ValueError("Archive needs declared languages")
        with tempfile.TemporaryDirectory(prefix="web-archive-") as temporary:
            base = Path(temporary)
            cmd = [sys.executable, "-m", "tools.build_web_packages", "--config", str(config_path),
                   "--model", model, "--region", region, "--version", version,
                   "--source", "review-asis", "--languages", *languages,
                   "--work-dir", str(base / "work"), "--output-dir", str(base / "output"),
                   "--node", settings.get('node', 'node')]
            if data_root:
                cmd += ['--data-root', data_root]
            if settings.get('browser'):
                cmd += ['--browser', settings['browser']]
            environment = dict(os.environ)
            if settings.get('node_module_path'):
                environment['NODE_PATH'] = settings['node_module_path']
            subprocess.run(cmd, cwd=source_repo, env=environment, check=True, capture_output=True, timeout=1800)
            output = base / "output" / model / region / version
            source_manifest = output / "release.json"
            source_metadata = json.loads(source_manifest.read_text(encoding="utf-8"))
            source_metadata['review_git_ref'] = git_ref
            write_json(source_manifest, source_metadata)
            packaged = base / "archive"
            release = package_archive(output, packaged)
            destination = staged_md.parent.parent / "archive-package"
            # Web Publish staging owns this freshly created version directory.
            if destination.exists():
                raise ValueError("Archive staging already exists")
            shutil.copytree(packaged, destination)
            report = {"status": "prepared", "model": model, "region": region, "version": version,
                      "release_relative": str(release.relative_to(packaged)),
                      "manifest_sha256": digest(release / "release-manifest.json")}
        record_status(report_path, report)
    except Exception as exc:
        record_status(report_path, {"status": "failed", "error_type": type(exc).__name__})
        print("[oss-archive] package preparation failed; Web Publish continues", file=sys.stderr)


def finish_web_archive(metadata_path: Path, *, staged_md: Path) -> dict | None:
    """Called only after Web Publish metadata is written; never raises into queue."""
    report_path = staged_md.parent.parent / "oss-archive-result.json"
    try:
        configured = archive_settings()
        if configured is None:
            return None
        settings_path, settings = configured
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get('schema_version') != 'auto-manual-web-publish/v1' or metadata.get('workflow_action') != 'Web Publish':
            raise ValueError("Archive requires successful Web Publish metadata")
        prepared = json.loads((staged_md.parent.parent / "archive-preparation.json").read_text(encoding="utf-8"))
        if prepared['status'] != 'prepared':
            raise ValueError("Archive preparation failed; rebuild needed")
        if any(prepared[k] != metadata[k] for k in ('model', 'region', 'version')):
            raise ValueError("Archive target does not match this publication")
        root = staged_md.parent.parent / 'archive-package'
        release = (root / prepared['release_relative']).resolve()
        if not release.is_relative_to(root.resolve()):
            raise ValueError("Invalid prepared release path")
        manifest_path = release / 'release-manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if digest(manifest_path) != prepared['manifest_sha256'] or any(
            manifest[k] != metadata[k] for k in ('model', 'region', 'version')
        ):
            raise ValueError("Frozen archive identity changed")
        frozen_metadata = root / 'web-publish-metadata.json'
        if not frozen_metadata.exists():
            shutil.copy2(metadata_path, frozen_metadata)
        record_status(report_path, {'status': 'uploading'})
        subprocess.run([
            settings['python'], '-m', 'tools.oss_archive_store', '--release', str(release),
            '--settings', str(settings_path.resolve()), '--report', str(report_path.resolve()),
        ], cwd=repo_root(), check=True, capture_output=True, timeout=1800)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get('status') != 'archived':
            raise ValueError("Archive worker did not confirm completion")
    except Exception as exc:
        # Never retain subprocess stderr or SDK payloads containing credentials.
        report = {"status": "failed", "error_type": type(exc).__name__,
                  "publication_status": "unchanged", "retry": "tools.web_publish_archive"}
        record_status(report_path, report)
    print(f"[oss-archive] {report['status']}; report: {report_path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Retry OSS archival of an already frozen Web Publish package")
    parser.add_argument('--metadata', required=True, type=Path)
    parser.add_argument('--staged-md', required=True, type=Path)
    args = parser.parse_args()
    result = finish_web_archive(args.metadata, staged_md=args.staged_md)
    if result is None or result['status'] != 'archived':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
