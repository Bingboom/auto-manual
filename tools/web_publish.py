"""``build.py web-release``: publish one Web Publish book locally, end to end.

This is the first conveyor-belt command for the manual publishing pipeline: it
runs the same check/md/html Web-profile build the build queue's Web Publish
worker runs (``tools.queue_build_execution.run_web_language_build_steps``),
seals and verifies per-language projection evidence, stages the sealed bundle
under ``reports/releases/<model>/<region>/<lang>/versions/<version>/web/``,
writes ``web_publish_meta.json``, runs a local strict ``sphinx -W`` gate, and
records any accompanying debt to a shared ledger.

Everything that touches the filesystem is delegated to already-tested library
functions (``tools.queue_bound_outputs``, ``tools.queue_bound_runtime``,
``tools.queue_build_execution``, ``tools.web_language_release_evidence``,
``tools.publish_locale_identity``, ``tools.readthedocs_source``); this module
is the local (non-queue, non-worktree) orchestration and CLI-facing surface.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from tools.publish_locale_identity import LANGUAGE_SCOPE_SINGLE, WebPublishTarget
from tools.queue_build_execution import run_web_language_build_steps
from tools.queue_bound_outputs import (
    publish_release_version_dir_for_target,
    resolve_html_output_dir_for_target,
    resolve_md_output_path_for_target,
    set_repo_root_provider as _set_queue_output_repo_root_provider,
    stage_web_publish_assets_to_host_repo,
    write_web_publish_metadata,
)
from tools.queue_bound_runtime import (
    build_py_target_command,
    run_command,
    set_repo_root_provider as _set_queue_runtime_repo_root_provider,
)
from tools.readthedocs_source import assemble_rtd_source
from tools.utils.path_utils import PathSegments, web_debt_ledger_of
from tools.web_language_release_evidence import RECEIPT_FILENAME, require_consistent_captures


DEBT_LEDGER_SCHEMA_VERSION = "auto-manual-web-debt-ledger/v1"
_DEBT_STATUS_OPEN = "open"
_AUTO_DEBT_CATEGORY_BUILD_FAILED = "构建失败"


@dataclass(frozen=True)
class WebReleaseTarget:
    model: str
    region: str
    lang: str
    version: str = ""

    def label(self) -> str:
        return f"{self.model}/{self.region}/{self.lang}@{self.version or '?'}"

    def with_default_version(self, default_version: str) -> "WebReleaseTarget":
        if self.version.strip():
            return self
        return WebReleaseTarget(self.model, self.region, self.lang, default_version.strip())


@dataclass(frozen=True)
class DebtEntry:
    model: str
    region: str
    lang: str
    date: str
    category: str
    location: str
    payoff_action: str
    source: str
    status: str = _DEBT_STATUS_OPEN

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": DEBT_LEDGER_SCHEMA_VERSION,
            "target": {"model": self.model, "region": self.region, "lang": self.lang},
            "date": self.date,
            "category": self.category,
            "location": self.location,
            "payoff_action": self.payoff_action,
            "source": self.source,
            "status": self.status,
        }


@dataclass(frozen=True)
class WebReleaseResult:
    target: WebReleaseTarget
    status: str  # "ok" | "failed"
    md_output_path: Path | None = None
    html_output_dir: Path | None = None
    evidence_path: Path | None = None
    error: str | None = None


def parse_targets_file(path: Path) -> list[WebReleaseTarget]:
    """Parse a batch targets file: one ``MODEL,REGION,LANG[,VERSION]`` per line.

    Blank lines and lines starting with ``#`` are comments.
    """

    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"web-release --targets-file must be a real file: {path}")
    targets: list[WebReleaseTarget] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) not in (3, 4) or any(not part for part in parts[:3]):
            raise RuntimeError(
                f"web-release --targets-file {path}:{line_number}: expected "
                f"MODEL,REGION,LANG[,VERSION], got {raw_line!r}"
            )
        version = parts[3] if len(parts) == 4 else ""
        targets.append(
            WebReleaseTarget(model=parts[0], region=parts[1], lang=parts[2], version=version)
        )
    if not targets:
        raise RuntimeError(f"web-release --targets-file has no target rows: {path}")
    return targets


def parse_debt_flag(raw: str) -> tuple[str, str, str]:
    """Parse one ``--debt "category:location:payoff action"`` entry."""

    parts = raw.split(":", 2)
    if len(parts) != 3 or not parts[0].strip() or not parts[1].strip():
        raise RuntimeError(
            "--debt must be formatted as 'category:location:payoff action', "
            f"got {raw!r}"
        )
    return parts[0].strip(), parts[1].strip(), parts[2].strip()


def _assembly_route_key(*, model: str, region: str, lang: str) -> str:
    """Compute the real Web Publish assembly route key for one target.

    Delegates to :class:`WebPublishTarget.route` (the property
    ``tools.publish_branch_assembly`` actually keys assembly routes on) rather
    than re-deriving the formula, so this precheck tracks the real assembly
    logic even if it changes later. The unused path fields are placeholders;
    ``.route``/``.identity`` only read model/region/lang.
    """

    probe = WebPublishTarget(
        metadata_path=Path("."),
        model=model,
        region=region,
        lang=lang,
        version="0",
        built_at="",
        git_ref="",
        markdown_path=Path("."),
        html_dir=Path("."),
        legacy_default=None,
        language_scope=LANGUAGE_SCOPE_SINGLE,
    )
    return probe.route.as_posix().casefold()


def check_batch_for_collisions(
    *, config_path: Path, targets: Sequence[WebReleaseTarget]
) -> None:
    """Reject the whole batch before any build starts if two targets collide.

    Two independent checks, both against real production path derivation:
    (1) no two targets resolve to the same on-disk build output path
    (``resolve_md_output_path_for_target``); (2) no two targets resolve to the
    same Web Publish assembly route (``WebPublishTarget.route``). Both reduce
    to "no duplicate (model, region, lang)" given the current locale-aware
    build/assembly paths, but are computed from the real helpers rather than
    reimplemented, so a future path-derivation change is still caught here.
    """

    problems: list[str] = []
    build_paths_seen: dict[str, WebReleaseTarget] = {}
    routes_seen: dict[str, WebReleaseTarget] = {}
    for target in targets:
        build_path = resolve_md_output_path_for_target(
            config_path=config_path,
            model=target.model,
            region=target.region,
            lang=target.lang,
        )
        build_path_key = str(build_path.resolve(strict=False)).casefold()
        other = build_paths_seen.get(build_path_key)
        if other is not None:
            problems.append(
                f"{target.label()} and {other.label()} resolve to the same build "
                f"output path: {build_path}"
            )
        else:
            build_paths_seen[build_path_key] = target

        route_key = _assembly_route_key(
            model=target.model, region=target.region, lang=target.lang
        )
        other = routes_seen.get(route_key)
        if other is not None:
            problems.append(
                f"{target.label()} and {other.label()} resolve to the same Web "
                f"Publish assembly route: {route_key}"
            )
        else:
            routes_seen[route_key] = target

    if problems:
        raise RuntimeError(
            "web-release batch collision precheck failed; no build was started:\n"
            + "\n".join(f"  - {problem}" for problem in problems)
        )


def _current_git_head_sha(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    sha = (proc.stdout or "").strip().lower()
    if proc.returncode != 0 or len(sha) != 40:
        raise RuntimeError(
            f"cannot resolve local Git HEAD SHA for Web release evidence under {repo_root}"
        )
    return sha


def _run_strict_web_verification(*, built_md_output_path: Path, title: str) -> None:
    """Rebuild the just-built Web bundle with ``sphinx -W`` (warnings as errors).

    ``build.py html`` does not pass ``-W``, so this is a strictly stronger
    local gate on top of it. Runs entirely in a scratch temp directory outside
    the repo (never under ``docs/_build`` or the release tree) so it never
    leaves scratch files behind or fights ``assemble_rtd_source``'s
    output-inside-build-root containment check against an immutable tree.
    """

    source_md_dir = built_md_output_path.parent
    with tempfile.TemporaryDirectory(prefix="auto-manual-web-release-verify-") as raw_temp_dir:
        temp_dir = Path(raw_temp_dir)
        build_root = temp_dir / "source"
        shutil.copytree(source_md_dir, build_root / PathSegments.MD)
        assembled_dir = temp_dir / "rtd"
        assemble_rtd_source(build_root=build_root, output_dir=assembled_dir, title=title)
        html_out = temp_dir / "html"
        proc = subprocess.run(
            [sys.executable, "-m", "sphinx", "-W", "-b", "html", str(assembled_dir), str(html_out)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(
                f"strict Web verification failed (sphinx -W -b html): {detail[-4000:]}"
            )


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _append_json_array_file(path: Path, new_entries: Sequence[dict[str, Any]]) -> None:
    existing: list[dict[str, Any]] = []
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("entries"), list):
            existing = [item for item in payload["entries"] if isinstance(item, dict)]
    path.parent.mkdir(parents=True, exist_ok=True)
    combined = existing + list(new_entries)
    path.write_text(
        json.dumps(
            {"schema_version": DEBT_LEDGER_SCHEMA_VERSION, "entries": combined},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _append_jsonl_file(path: Path, new_entries: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for entry in new_entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def record_debt_entries(
    *,
    repo_root: Path,
    config_path: Path,
    target: WebReleaseTarget,
    entries: Sequence[DebtEntry],
) -> None:
    """Append ``entries`` to the per-book ledger and the repo-wide total ledger.

    Per-book: ``reports/releases/<model>/<region>/<lang>/versions/<version>/web/debt_ledger.json``
    (a sibling of the sealed ``evidence/`` directory, not inside it --
    ``verify_release_evidence`` asserts that directory contains *exactly*
    ``language_projection_receipt.json`` and ``projection_bundle_manifest.json``,
    so a third file there would break every future evidence read of this
    release). Total: ``reports/web_debt_ledger.jsonl``, one JSON object per
    line, append-only.
    """

    if not entries:
        return
    payloads = [entry.to_dict() for entry in entries]
    version_dir = publish_release_version_dir_for_target(
        config_path=config_path,
        model=target.model,
        region=target.region,
        version=target.version,
        lang=target.lang,
    )
    _append_json_array_file(
        version_dir / PathSegments.WEB / PathSegments.DEBT_LEDGER_JSON, payloads
    )
    _append_jsonl_file(web_debt_ledger_of(repo_root), payloads)


def _release_one_target(
    *,
    repo_root: Path,
    config_path: Path,
    target: WebReleaseTarget,
    data_root: str | None,
    git_ref: str,
    skip_verify: bool,
    manual_debt: Sequence[tuple[str, str, str]],
) -> WebReleaseResult:
    model, region, lang, version = target.model, target.region, target.lang, target.version

    # b. Warm up once so the review-derived generated bundle hash converges;
    # otherwise the *first* build after a fresh review sync can still be
    # settling content between runs, and the captured check/md/html
    # fingerprints below would disagree (require_consistent_captures fails).
    run_command(
        build_py_target_command(
            action="check",
            config_path=config_path,
            model=model,
            region=region,
            lang=lang,
            data_root=data_root,
            source="review",
            no_clean=False,
            presentation_profile="web",
            repo_root=repo_root,
        ),
        cwd=repo_root,
    )

    # c. The real check/md/html Web-profile build, capturing per-step evidence.
    projection_captures = run_web_language_build_steps(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        source_revision_workspace=repo_root,
        run_command=run_command,
        build_py_target_command=build_py_target_command,
        resolve_md_output_path_for_target=resolve_md_output_path_for_target,
    )

    # d. Fail fast on a cross-step drift before any staging/verification cost.
    require_consistent_captures(projection_captures)

    built_md_output_path = resolve_md_output_path_for_target(
        config_path=config_path, model=model, region=region, lang=lang
    )
    built_html_dir = resolve_html_output_dir_for_target(
        config_path=config_path, model=model, region=region, lang=lang
    )

    # f. Local strict verification, run against the just-built raw output
    # (before staging) so a broken bundle never reaches the release tree.
    if not skip_verify:
        _run_strict_web_verification(
            built_md_output_path=built_md_output_path,
            title=f"{model} {region} {lang}",
        )

    # e. Seal projection evidence, stage the sealed bundle, write metadata.
    staged_md_output_path, staged_html_dir = stage_web_publish_assets_to_host_repo(
        built_md_output_path=built_md_output_path,
        built_html_dir=built_html_dir,
        host_config_path=config_path,
        model=model,
        region=region,
        version=version,
        projection_captures=tuple(projection_captures),
        git_ref=git_ref,
        target_lang=lang,
    )
    version_dir = publish_release_version_dir_for_target(
        config_path=config_path, model=model, region=region, version=version, lang=lang
    )
    evidence_path = version_dir / PathSegments.WEB / PathSegments.EVIDENCE / RECEIPT_FILENAME
    write_web_publish_metadata(
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        git_ref=git_ref,
        built_at=datetime.now(timezone.utc),
        md_output_path=staged_md_output_path,
        html_dir=staged_html_dir,
        target_lang=lang,
        language_projection_evidence_path=evidence_path,
    )

    # g. Debt ledger: any manual entries supplied for this run.
    if manual_debt:
        today = _today_iso()
        record_debt_entries(
            repo_root=repo_root,
            config_path=config_path,
            target=target,
            entries=[
                DebtEntry(
                    model=model,
                    region=region,
                    lang=lang,
                    date=today,
                    category=category,
                    location=location,
                    payoff_action=payoff_action,
                    source="manual",
                )
                for category, location, payoff_action in manual_debt
            ],
        )

    return WebReleaseResult(
        target=target,
        status="ok",
        md_output_path=staged_md_output_path,
        html_output_dir=staged_html_dir,
        evidence_path=evidence_path,
    )


def _format_result_line(result: WebReleaseResult) -> str:
    if result.status == "ok":
        return f"OK     {result.target.label()} -> {result.evidence_path}"
    return f"FAILED {result.target.label()}: {result.error}"


def _print_summary(results: Sequence[WebReleaseResult]) -> None:
    ok = sum(1 for result in results if result.status == "ok")
    print("[web-release] summary:")
    for result in results:
        print(f"[web-release]   {_format_result_line(result)}")
    print(f"[web-release] {ok}/{len(results)} target(s) released")


def _resolve_targets(
    args: argparse.Namespace, *, resolve_path_from_root: Callable[[str], Path]
) -> list[WebReleaseTarget]:
    targets_file = str(getattr(args, "targets_file", None) or "").strip()
    if targets_file:
        return parse_targets_file(resolve_path_from_root(targets_file))
    model = str(getattr(args, "model", None) or "").strip()
    region = str(getattr(args, "region", None) or "").strip()
    lang = str(getattr(args, "lang", None) or "").strip()
    if not model or not region or not lang:
        raise RuntimeError(
            "web-release requires --model, --region, and --lang (or --targets-file)"
        )
    return [WebReleaseTarget(model=model, region=region, lang=lang)]


def run_web_release(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
) -> None:
    """Entry point wired as ``build.py``'s ``web-release`` action."""

    config_path = resolve_path_from_root(args.config)
    default_version = str(getattr(args, "version", None) or "").strip()
    manual_debt = tuple(
        parse_debt_flag(raw) for raw in (getattr(args, "debt", None) or ())
    )
    skip_verify = bool(getattr(args, "skip_verify", False))
    dry_run = bool(getattr(args, "dry_run", False))
    data_root = getattr(args, "data_root", None)

    raw_targets = _resolve_targets(args, resolve_path_from_root=resolve_path_from_root)
    targets = [target.with_default_version(default_version) for target in raw_targets]
    missing_version = [target for target in targets if not target.version.strip()]
    if missing_version:
        raise RuntimeError(
            "web-release requires a version for every target: pass --version, or "
            "a 4th column in --targets-file; missing for "
            + ", ".join(f"{t.model}/{t.region}/{t.lang}" for t in missing_version)
        )

    check_batch_for_collisions(config_path=config_path, targets=targets)

    if dry_run:
        print(f"[web-release] plan: {len(targets)} target(s); no build will run (--dry-run)")
        for target in targets:
            print(f"[web-release]   - {target.label()}")
        if manual_debt:
            print(f"[web-release]   {len(manual_debt)} manual debt entrie(s) would be recorded per target")
        return

    _set_queue_output_repo_root_provider(lambda: repo_root)
    _set_queue_runtime_repo_root_provider(lambda: repo_root)
    git_ref = _current_git_head_sha(repo_root)

    results: list[WebReleaseResult] = []
    for target in targets:
        try:
            result = _release_one_target(
                repo_root=repo_root,
                config_path=config_path,
                target=target,
                data_root=data_root,
                git_ref=git_ref,
                skip_verify=skip_verify,
                manual_debt=manual_debt,
            )
        except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
            result = WebReleaseResult(target=target, status="failed", error=str(exc))
            try:
                record_debt_entries(
                    repo_root=repo_root,
                    config_path=config_path,
                    target=target,
                    entries=[
                        DebtEntry(
                            model=target.model,
                            region=target.region,
                            lang=target.lang,
                            date=_today_iso(),
                            category=_AUTO_DEBT_CATEGORY_BUILD_FAILED,
                            location=target.label(),
                            payoff_action=f"re-run web-release once fixed: {str(exc)[:500]}",
                            source="auto",
                        )
                    ],
                )
            except (RuntimeError, OSError):
                pass  # the build failure is the primary signal; don't mask it with a ledger-write failure
        results.append(result)
        print(f"[web-release] {_format_result_line(result)}")

    _print_summary(results)
    failed = [result for result in results if result.status == "failed"]
    if failed:
        raise RuntimeError(
            f"web-release: {len(failed)}/{len(results)} target(s) failed: "
            + "; ".join(result.target.label() for result in failed)
        )


__all__ = (
    "DebtEntry",
    "WebReleaseResult",
    "WebReleaseTarget",
    "check_batch_for_collisions",
    "parse_debt_flag",
    "parse_targets_file",
    "record_debt_entries",
    "run_web_release",
)
