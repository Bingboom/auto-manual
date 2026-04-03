#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.process_build_queue import parse_document_key, resolve_config_path_for_task  # noqa: E402
from tools.review_support import review_bundle_exists, review_dir_for_target  # noqa: E402
from tools.sync_data import (  # noqa: E402
    LarkCliSource,
    _cli_bin,
    _cli_command_exists,
    _cli_command_parts,
    _env_value,
    _phase2_identity,
    _provider_name,
    _sync_phase2_cfg,
    load_config,
)
from tools.utils.targets import resolve_output_lang  # noqa: E402

REVIEW_TRIGGER_FIELD = "\u662f\u5426\u8fdb\u5165Review"
REVIEW_STATUS_FIELD = "Review_status"
GIT_REF_FIELD = "Git_ref"
PR_URL_FIELD = "PR_url"
DOCUMENT_ID_FIELD = "Document_ID"
DOCUMENT_KEY_FIELD = "Document_Key"
VERSION_FIELD = "Version"
LANG_FIELD = "Lang"

REVIEW_STATUS_NOT_STARTED = "NotStarted"
REVIEW_STATUS_IN_REVIEW = "InReview"


@dataclass(frozen=True)
class ReviewInitBinding:
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    base_token: str
    table_id: str
    view_id: str | None


@dataclass(frozen=True)
class ReviewStartRecord:
    record_id: str
    document_id: str
    document_key: str
    version: str
    lang: str
    review_status: str
    review_trigger_value: Any
    git_ref: str
    pr_url: str

    @property
    def label(self) -> str:
        return self.document_id or f"{self.document_key}_{self.lang}"


def _review_init_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    phase2_cfg = _sync_phase2_cfg(cfg)
    raw = phase2_cfg.get("review_init", {})
    return raw if isinstance(raw, dict) else {}


def _document_link_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    phase2_cfg = _sync_phase2_cfg(cfg)
    raw = phase2_cfg.get("document_link", {})
    return raw if isinstance(raw, dict) else {}


def _review_init_env_names(cfg: dict[str, Any]) -> tuple[str, str, str | None]:
    phase2_cfg = _sync_phase2_cfg(cfg)
    review_init_cfg = _review_init_cfg(cfg)
    document_link_cfg = _document_link_cfg(cfg)
    base_token_env = str(review_init_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or "").strip()
    document_link_table_id_env = str(document_link_cfg.get("table_id_env") or "").strip()
    document_link_view_id_env = str(document_link_cfg.get("view_id_env") or "").strip() or None
    review_table_id_env = str(review_init_cfg.get("table_id_env") or "").strip()
    review_view_id_env = str(review_init_cfg.get("view_id_env") or "").strip() or None
    table_id_env = document_link_table_id_env or review_table_id_env
    view_id_env = document_link_view_id_env or review_view_id_env
    return base_token_env, table_id_env, view_id_env


def collect_review_start_preflight_errors(cfg: dict[str, Any], *, require_github: bool = True) -> list[str]:
    errors: list[str] = []
    _provider_name(cfg)

    cli_bin = _cli_bin(cfg)
    try:
        command = _cli_command_parts(cli_bin)[0]
    except RuntimeError as exc:
        errors.append(str(exc))
        command = None
    if command and not _cli_command_exists(cli_bin):
        errors.append(f"sync.phase2.cli_bin executable is not available: {command}")

    base_token_env, table_id_env, view_id_env = _review_init_env_names(cfg)
    missing_env_names = [
        env_name
        for env_name in (base_token_env, table_id_env, view_id_env or "")
        if env_name and not str(os.environ.get(env_name, "")).strip()
    ]
    if not base_token_env:
        errors.append("sync.phase2.base_token_env is required")
    if not table_id_env:
        errors.append("sync.phase2.document_link.table_id_env is required because review-init reuses the Document_link binding")
    if missing_env_names:
        errors.append("Required environment variables are not set: " + ", ".join(missing_env_names))

    if require_github:
        for env_name in ("GITHUB_REPOSITORY", "GITHUB_TOKEN"):
            if not str(os.environ.get(env_name, "")).strip():
                errors.append(f"Required environment variable is not set: {env_name}")
    return errors


def resolve_review_init_binding(cfg: dict[str, Any]) -> ReviewInitBinding:
    base_token_env, table_id_env, view_id_env = _review_init_env_names(cfg)
    if not base_token_env:
        raise RuntimeError("sync.phase2.base_token_env is required")
    if not table_id_env:
        raise RuntimeError("sync.phase2.document_link.table_id_env is required because review-init reuses the Document_link binding")
    return ReviewInitBinding(
        base_token_env=base_token_env,
        table_id_env=table_id_env,
        view_id_env=view_id_env,
        base_token=_env_value(base_token_env),
        table_id=_env_value(table_id_env),
        view_id=_env_value(view_id_env) if view_id_env else None,
    )


def _scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        for item in value:
            text = _scalar_text(item)
            if text:
                return text
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, "g")
    return str(value).strip()


def _is_checkbox_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _scalar_text(value).strip().lower()
    return text in {"1", "true", "y", "yes", "checked"}


def normalize_review_status(value: Any) -> str | None:
    text = _scalar_text(value).strip().lower()
    if not text:
        return None
    if text in {"notstarted", "not_started", "not started"}:
        return "notstarted"
    if text in {"inreview", "in_review", "in review"}:
        return "inreview"
    if text in {"readyforpublish", "ready_for_publish", "ready for publish"}:
        return "readyforpublish"
    return text


def parse_review_start_records(raw_records: list[dict[str, Any]]) -> list[ReviewStartRecord]:
    records: list[ReviewStartRecord] = []
    for record in raw_records:
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            raise RuntimeError("Review-init record list is missing record_id")
        fields_raw = record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        records.append(
            ReviewStartRecord(
                record_id=record_id,
                document_id=_scalar_text(fields.get(DOCUMENT_ID_FIELD)),
                document_key=_scalar_text(fields.get(DOCUMENT_KEY_FIELD)),
                version=_scalar_text(fields.get(VERSION_FIELD)),
                lang=_scalar_text(fields.get(LANG_FIELD)).lower(),
                review_status=_scalar_text(fields.get(REVIEW_STATUS_FIELD)),
                review_trigger_value=fields.get(REVIEW_TRIGGER_FIELD),
                git_ref=_scalar_text(fields.get(GIT_REF_FIELD)),
                pr_url=_scalar_text(fields.get(PR_URL_FIELD)),
            )
        )
    return records


def select_pending_review_start_records(
    raw_records: list[dict[str, Any]],
    *,
    record_id: str | None = None,
) -> list[ReviewStartRecord]:
    selected: list[ReviewStartRecord] = []
    for record in parse_review_start_records(raw_records):
        if record_id and record.record_id != record_id:
            continue
        if not _is_checkbox_enabled(record.review_trigger_value):
            continue
        if normalize_review_status(record.review_status) not in {None, "notstarted"}:
            continue
        selected.append(record)
    return selected


def _slug_branch_token(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "review"


def _looks_like_explicit_document_key(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9-]+_[A-Za-z0-9-]+", value.strip()))


def generate_review_branch_name(record: ReviewStartRecord) -> str:
    if record.git_ref.strip():
        return record.git_ref.strip()
    source = record.document_id or f"{record.document_key}_{record.lang}_{record.version}"
    slug = _slug_branch_token(source)[:72]
    return f"codex/review-{slug}"


def _document_key_from_document_id(*, document_id: str, lang: str, version: str) -> str:
    candidate = document_id.strip()
    version_text = version.strip()
    lang_text = lang.strip().lower()
    if version_text and candidate.endswith("_" + version_text):
        candidate = candidate[: -(len(version_text) + 1)]
    if lang_text and candidate.lower().endswith("_" + lang_text):
        candidate = candidate[: -(len(lang_text) + 1)]
    return candidate.strip()


def resolve_target_for_review_start(record: ReviewStartRecord) -> tuple[str, str]:
    candidates: list[str] = []
    if _looks_like_explicit_document_key(record.document_key):
        candidates.append(record.document_key.strip())
    fallback_key = _document_key_from_document_id(
        document_id=record.document_id,
        lang=record.lang,
        version=record.version,
    )
    if fallback_key and fallback_key not in candidates:
        candidates.append(fallback_key)

    errors: list[str] = []
    for candidate in candidates:
        try:
            return parse_document_key(candidate)
        except RuntimeError as exc:
            errors.append(str(exc))

    detail = f"Document_ID={record.document_id!r}, Document_Key={record.document_key!r}, Lang={record.lang!r}"
    if errors:
        raise RuntimeError("Unable to resolve review-start target. " + detail + " | " + " | ".join(errors))
    raise RuntimeError("Unable to resolve review-start target. " + detail)


def build_review_start_success_fields(*, git_ref: str, pr_url: str) -> dict[str, Any]:
    return {
        REVIEW_STATUS_FIELD: [REVIEW_STATUS_IN_REVIEW],
        REVIEW_TRIGGER_FIELD: False,
        GIT_REF_FIELD: git_ref,
        PR_URL_FIELD: pr_url,
    }


def _format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def _run_command(cmd: list[str], *, cwd: Path = ROOT) -> str:
    print(f"[review-start] {_format_command(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode:
        lines = [line.strip() for line in (proc.stderr or proc.stdout or "").splitlines() if line.strip()]
        message = lines[-1] if lines else "command failed"
        raise RuntimeError(f"{message} (exit={proc.returncode}, cmd={_format_command(cmd)})")
    return proc.stdout or ""


def _run_git(args: list[str], *, cwd: Path = ROOT) -> str:
    return _run_command(["git", *args], cwd=cwd)


def _build_py_command(
    worktree: Path,
    *,
    action: str,
    config_path: Path,
    model: str | None = None,
    region: str | None = None,
    data_root: str | None = None,
    source: str | None = None,
) -> list[str]:
    cmd = [
        sys.executable,
        str(worktree / "build.py"),
        action,
        "--config",
        str(config_path),
    ]
    if model:
        cmd += ["--model", model]
    if region:
        cmd += ["--region", region]
    if data_root:
        cmd += ["--data-root", data_root]
    if source:
        cmd += ["--source", source]
    return cmd


def sync_phase2_snapshot_before_review_start(*, config_path: Path, data_root: str | None) -> None:
    _run_command(
        [
            sys.executable,
            str(ROOT / "build.py"),
            "sync-data",
            "--config",
            str(config_path),
            *(["--data-root", data_root] if data_root else []),
        ]
    )


def _review_dir_for_target(config_path: Path, *, model: str, region: str) -> Path:
    cfg = load_config(config_path)
    docs_dir = _resolve_docs_dir_for_config(config_path, cfg)
    output_lang = resolve_output_lang(cfg)
    candidate = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=output_lang)
    if candidate.exists():
        return candidate
    return review_dir_for_target(docs_dir=docs_dir, model=model, region=region)


def _resolve_docs_dir_for_config(config_path: Path, cfg: dict[str, Any]) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        candidate = Path(raw.strip())
        if candidate.is_absolute():
            return candidate
        return (config_path.parent / candidate).resolve()
    return (config_path.parent / "docs").resolve()


def _git_ref_exists(ref_name: str) -> bool:
    proc = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", ref_name],
        cwd=str(ROOT),
        check=False,
    )
    return proc.returncode == 0


def _remote_branch_exists(branch_name: str) -> bool:
    return _git_ref_exists(f"refs/remotes/origin/{branch_name}")


def _worktree_dir_for_branch(branch_name: str) -> Path:
    return ROOT / ".tmp" / "review-start-worktrees" / _slug_branch_token(branch_name)


def _remove_worktree(path: Path) -> None:
    if not path.exists():
        return
    proc = subprocess.run(
        ["git", "worktree", "remove", "--force", str(path)],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0 and path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _prepare_branch_worktree(*, branch_name: str, base_ref: str) -> Path:
    _run_git(["fetch", "origin", "--prune"])
    worktree = _worktree_dir_for_branch(branch_name)
    _remove_worktree(worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    source_ref = f"origin/{branch_name}" if _remote_branch_exists(branch_name) else f"origin/{base_ref}"
    _run_git(["worktree", "add", "--force", str(worktree), source_ref])
    _run_git(["checkout", "-B", branch_name, source_ref], cwd=worktree)
    return worktree


def _configure_git_identity(worktree: Path) -> None:
    _run_git(
        [
            "config",
            "user.name",
            os.environ.get("GIT_AUTHOR_NAME", "github-actions[bot]"),
        ],
        cwd=worktree,
    )
    _run_git(
        [
            "config",
            "user.email",
            os.environ.get("GIT_AUTHOR_EMAIL", "41898282+github-actions[bot]@users.noreply.github.com"),
        ],
        cwd=worktree,
    )


def ensure_review_bundle_on_branch(
    *,
    worktree: Path,
    build_config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
) -> Path:
    worktree_config_path = worktree / build_config_path.name
    cfg = load_config(worktree_config_path)
    docs_dir = _resolve_docs_dir_for_config(worktree_config_path, cfg)
    output_lang = resolve_output_lang(cfg)
    if review_bundle_exists(docs_dir=docs_dir, model=model, region=region, lang=output_lang):
        return _review_dir_for_target(worktree_config_path, model=model, region=region)

    _run_command(
        _build_py_command(
            worktree,
            action="rst",
            config_path=worktree_config_path,
            model=model,
            region=region,
            data_root=data_root,
            source="runtime",
        ),
        cwd=worktree,
    )
    _run_command(
        _build_py_command(
            worktree,
            action="review",
            config_path=worktree_config_path,
            model=model,
            region=region,
        ),
        cwd=worktree,
    )
    review_dir = _review_dir_for_target(worktree_config_path, model=model, region=region)
    if not review_dir.exists():
        raise RuntimeError(f"Review bundle was not created: {review_dir}")
    return review_dir


def _commit_review_bundle_if_changed(*, worktree: Path, review_dir: Path, record: ReviewStartRecord) -> bool:
    review_rel = review_dir.relative_to(worktree).as_posix()
    _run_git(["add", "--", review_rel], cwd=worktree)
    proc = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", review_rel],
        cwd=str(worktree),
        check=False,
    )
    if proc.returncode == 0:
        return False
    if proc.returncode != 1:
        raise RuntimeError(f"Unable to inspect staged review changes for {review_rel}")
    _run_git(
        [
            "commit",
            "-m",
            f"seed review bundle for {record.document_id or record.document_key}",
        ],
        cwd=worktree,
    )
    return True


def _push_branch(*, worktree: Path, branch_name: str) -> None:
    _run_git(["push", "-u", "origin", branch_name], cwd=worktree)


def _github_api_request(*, method: str, path: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib_request.Request(
        "https://api.github.com" + path,
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib_request.urlopen(request) as response:
            raw = response.read().decode("utf-8") or "{}"
            return json.loads(raw)
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"GitHub API {method} {path} failed: {detail or exc}") from exc


def ensure_pull_request_for_branch(
    *,
    repository: str,
    branch_name: str,
    base_ref: str,
    token: str,
    record: ReviewStartRecord,
) -> str:
    owner = repository.split("/", 1)[0]
    query = urllib_parse.urlencode(
        {
            "state": "open",
            "head": f"{owner}:{branch_name}",
            "base": base_ref,
        }
    )
    existing = _github_api_request(
        method="GET",
        path=f"/repos/{repository}/pulls?{query}",
        token=token,
    )
    if isinstance(existing, list) and existing:
        first = existing[0]
        if isinstance(first, dict):
            url = str(first.get("html_url") or "").strip()
            if url:
                return url

    payload = {
        "title": f"Start review for {record.document_id or record.document_key}",
        "head": branch_name,
        "base": base_ref,
        "body": "\n".join(
            [
                "Auto-generated review start branch.",
                "",
                f"- Document_ID: {record.document_id}",
                f"- Document_Key: {record.document_key}",
                f"- Lang: {record.lang}",
                f"- Version: {record.version}",
            ]
        ),
    }
    created = _github_api_request(
        method="POST",
        path=f"/repos/{repository}/pulls",
        token=token,
        payload=payload,
    )
    url = str(created.get("html_url") or "").strip()
    if not url:
        raise RuntimeError("GitHub pull request creation did not return html_url")
    return url


def start_review_for_record(
    *,
    record: ReviewStartRecord,
    sync_config_path: Path,
    snapshot_data_root: str | None,
    base_ref: str,
    repository: str,
    token: str,
) -> tuple[str, str]:
    model, region = resolve_target_for_review_start(record)
    build_config_path = resolve_config_path_for_task(region=region, lang=record.lang)
    branch_name = generate_review_branch_name(record)
    worktree = _prepare_branch_worktree(branch_name=branch_name, base_ref=base_ref)
    try:
        _configure_git_identity(worktree)
        review_dir = ensure_review_bundle_on_branch(
            worktree=worktree,
            build_config_path=build_config_path,
            model=model,
            region=region,
            data_root=snapshot_data_root,
        )
        changed = _commit_review_bundle_if_changed(worktree=worktree, review_dir=review_dir, record=record)
        if changed or not _remote_branch_exists(branch_name):
            _push_branch(worktree=worktree, branch_name=branch_name)
        pr_url = ensure_pull_request_for_branch(
            repository=repository,
            branch_name=branch_name,
            base_ref=base_ref,
            token=token,
            record=record,
        )
        return branch_name, pr_url
    finally:
        _remove_worktree(worktree)


def process_review_start_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None,
    dry_run: bool,
    record_id: str | None = None,
) -> int:
    errors = collect_review_start_preflight_errors(cfg, require_github=not dry_run)
    if errors:
        raise RuntimeError("process-review-start-queue preflight failed:\n- " + "\n- ".join(errors))

    binding = resolve_review_init_binding(cfg)
    source = LarkCliSource(cli_bin=_cli_bin(cfg), identity=_phase2_identity())
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    pending = select_pending_review_start_records(raw_records, record_id=record_id)
    if not pending:
        print("[review-start] No pending review-start tasks found.")
        return 0

    snapshot_data_root = data_root or str((ROOT / ".tmp" / "review-start" / "phase2").resolve())
    if dry_run:
        for record in pending:
            model, region = resolve_target_for_review_start(record)
            build_config_path = resolve_config_path_for_task(region=region, lang=record.lang)
            print(
                "[review-start] DRY-RUN "
                + json.dumps(
                    {
                        "record_id": record.record_id,
                        "label": record.label,
                        "model": model,
                        "region": region,
                        "lang": record.lang,
                        "version": record.version,
                        "git_ref": generate_review_branch_name(record),
                        "config": str(build_config_path),
                        "data_root": snapshot_data_root,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    print("[review-start] Syncing latest phase2 snapshot before starting review branches.")
    sync_phase2_snapshot_before_review_start(config_path=config_path, data_root=snapshot_data_root)

    repository = str(os.environ.get("GITHUB_REPOSITORY", "")).strip()
    token = str(os.environ.get("GITHUB_TOKEN", "")).strip()
    base_ref = str(os.environ.get("REVIEW_START_BASE_REF", "main")).strip() or "main"

    failures: list[str] = []
    processed = 0
    for record in pending:
        try:
            branch_name, pr_url = start_review_for_record(
                record=record,
                sync_config_path=config_path,
                snapshot_data_root=snapshot_data_root,
                base_ref=base_ref,
                repository=repository,
                token=token,
            )
            source.upsert_record(
                base_token=binding.base_token,
                table_id=binding.table_id,
                record_id=record.record_id,
                record=build_review_start_success_fields(git_ref=branch_name, pr_url=pr_url),
            )
            processed += 1
            print(f"[review-start] Updated {record.label}: git_ref={branch_name} pr_url={pr_url}")
        except Exception as exc:
            failures.append(f"{record.label}: {exc}")
            print(f"[review-start] FAILURE {record.label}: {exc}", file=sys.stderr)

    print(f"[review-start] Summary: processed={processed} failed={len(failures)}")
    return 1 if failures else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Consume Review-init rows and seed review branches/PRs.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override phase2 snapshot root for review seeding")
    ap.add_argument("--dry-run", action="store_true", help="List pending rows without creating branches or PRs")
    ap.add_argument("--record-id", default=None, help="Only consume one Review-init record_id")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    cfg = load_config(config_path)
    resolved_data_root = str(
        resolve_phase2_export_root(
            cfg,
            repo_root=ROOT,
            data_root=args.data_root,
        )
    )
    return process_review_start_queue(
        cfg=cfg,
        config_path=config_path,
        data_root=resolved_data_root,
        dry_run=args.dry_run,
        record_id=args.record_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
