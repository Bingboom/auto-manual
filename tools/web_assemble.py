"""``build.py web-assemble``: collate staged Web releases into a publish PR.

This is the second conveyor-belt command for the manual publishing pipeline
(see ``code-as-doc/dev/web_publish_pipeline.md`` section 2.2, steps 4-5). Where
``build.py web-release`` (the first command) stages one sealed book under
``reports/releases/<model>/<region>/<lang>/{versions/<v>/web,latest/web}``,
this command runs the "one wave, one command" collating step: it assembles
every staged, sealed target into the Hello-Docs ``docs/publish/**`` release
candidate, verifies the aggregate Sphinx build strictly, checks that the
candidate's diff against ``main`` touches only ``docs/publish/**``, and -- only
with ``--push`` -- advances the shared ``publish`` branch and opens or updates
the single ``publish -> main`` PR.

Most of this logic already exists as Bash steps in
``.github/workflows/feishu-web-publish-queue.yml`` (the "Prepare publish
branch worktree", "Assemble frozen Web source under docs/publish", "Commit
publish candidate", "Validate publish PR scope", "Push publish candidate
branch", and "Open or update publish PR" steps). This module is a local,
Python, operator-facing mirror of that same transaction -- the same shape
``tools/publish_branch_assembly.py``, ``local-publish-queue-run`` and
``build.py web-release`` already use for taking a CI YAML step and making it
runnable/testable from a checkout.

Two structural differences from the workflow, both required because this
command runs against a *separate* remote repository (``Bingboom/Hello-Docs``)
instead of a worktree of the current one:

* the workflow adds a ``git worktree`` inside the already-checked-out
  Hello-Docs repository; this command instead makes a fresh, isolated
  blobless clone of Hello-Docs (``--filter=blob:none``: the full commit graph
  up front, file contents fetched lazily on checkout) under a scratch
  temporary directory (never the operator's own local Hello-Docs checkout)
  and tears it down when the run ends. The clone is never truncated
  (``--depth``): ``_reconcile_candidate``'s ``merge-base --is-ancestor`` and
  ``_validate_scope``'s three-dot diff are this command's entire safety net,
  and both need the real commit graph to answer correctly -- a shallow
  history can put the boundary commit exactly where ancestry needs to be
  decided.
* the workflow always runs as the ``github-actions[bot]`` identity; this
  command relies on the operator's own ``git config user.*`` and ``gh auth``
  session (consistent with ``AGENTS.md`` section 8.3: identity comes from
  ``git config user.*``, never a hardcoded bot identity).

Every ``git``/``gh``/``sphinx`` call goes through one injectable
``run(argv, cwd)`` seam (default: a thin ``subprocess.run`` wrapper) so tests
can exercise the full transaction without touching a network, a real git
remote, or Sphinx.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from tools.publish_branch_assembly import assemble_web_publish_branch
from tools.utils.path_utils import Paths, PathSegments


DEFAULT_HELLO_DOCS_REPO = "Bingboom/Hello-Docs"
# Matches the assembler's own default: the queue workflow's "Assemble frozen
# Web source under docs/publish" step never passes --title, so the assembler
# falls back to this same string (tools/publish_branch_assembly.py parse_args).
DEFAULT_TITLE = "Auto Manual Library"
BASE_BRANCH = "main"
PUBLISH_BRANCH = "publish"
_DOCS_PUBLISH_PREFIX = f"{PathSegments.DOCS}/{PathSegments.PUBLISH}/"
_GIT_CREDENTIAL_ARGS: tuple[str, ...] = ("-c", "credential.helper=!gh auth git-credential")
_COMMIT_MESSAGE = "chore(publish): refresh web documentation"
_SYNC_BASE_MESSAGE = "chore(publish): sync candidate base"

CommandRunner = Callable[[Sequence[str], Path], "subprocess.CompletedProcess[str]"]


def default_run_command(cmd: Sequence[str], cwd: Path) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        list(cmd),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


@dataclass(frozen=True)
class AssembleReport:
    hello_docs_remote: str
    releases_root: Path
    title: str
    dry_run: bool = False
    manifest_path: Path | None = None
    manifest_sha256: str | None = None
    included_targets: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    changed_path_count: int = 0
    changed_paths: tuple[str, ...] = field(default_factory=tuple)
    committed: bool = False
    commit_sha: str | None = None
    pushed: bool = False
    pr_url: str | None = None


def resolve_hello_docs_remote(value: str | None) -> str:
    """Resolve ``--hello-docs-repo`` to a ``git clone``-able remote.

    Accepts a full git URL (used as-is), a local directory (used for tests --
    never the operator's real Hello-Docs checkout, which is a normal working
    tree the operator edits by hand, not a throwaway clone source), or an
    ``OWNER/REPO`` slug (the common case, resolved to a GitHub HTTPS URL).
    """

    text = (value or "").strip() or DEFAULT_HELLO_DOCS_REPO
    if text.startswith(("http://", "https://", "git@", "ssh://")):
        return text
    local_path = Path(text)
    if local_path.exists():
        return str(local_path)
    return f"https://github.com/{text}.git"


def _git(
    run: CommandRunner,
    cwd: Path,
    *args: str,
    network: bool = False,
    check: bool = True,
) -> "subprocess.CompletedProcess[str]":
    cmd: list[str] = ["git"]
    if network:
        cmd.extend(_GIT_CREDENTIAL_ARGS)
    cmd.extend(args)
    result = run(cmd, cwd)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed (exit={result.returncode}): {detail}")
    return result


def _publish_branch_exists(run: CommandRunner, clone_dir: Path) -> bool:
    result = _git(
        run, clone_dir, "ls-remote", "--exit-code", "--heads", "origin", PUBLISH_BRANCH,
        network=True, check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 2:
        return False
    detail = (result.stderr or result.stdout or "").strip()
    raise RuntimeError(
        f"git ls-remote failed checking for the {PUBLISH_BRANCH} branch (exit={result.returncode}): {detail}"
    )


def _reconcile_candidate(run: CommandRunner, clone_dir: Path, preserved_dir: Path) -> None:
    """Mirror the workflow's "Prepare publish branch worktree" step.

    On the first-ever run there is no ``publish`` branch yet, so the fresh
    ``main`` clone already *is* the candidate base and nothing else is needed.
    Otherwise: check out the existing ``publish`` tip, preserve its
    ``docs/publish`` (it may already carry other staged-but-unmerged targets
    that a naive checkout of ``main`` would drop), record ``main`` as an
    ancestor with a tree-preserving ``-s ours`` merge only when it is not
    already one, reset the working tree to ``main`` (refreshing the tracked
    code/config alongside the release), and restore the preserved
    ``docs/publish`` on top before the assembler runs.
    """

    if not _publish_branch_exists(run, clone_dir):
        return

    _git(
        run, clone_dir, "fetch", "--no-tags", "origin",
        f"{PUBLISH_BRANCH}:refs/remotes/origin/{PUBLISH_BRANCH}", network=True,
    )
    _git(run, clone_dir, "checkout", "--detach", f"refs/remotes/origin/{PUBLISH_BRANCH}")

    docs_publish_dir = Paths(root=clone_dir).docs_publish_dir
    if docs_publish_dir.is_dir():
        preserved_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(docs_publish_dir, preserved_dir, dirs_exist_ok=True)

    is_ancestor = _git(
        run, clone_dir, "merge-base", "--is-ancestor",
        f"refs/remotes/origin/{BASE_BRANCH}", "HEAD", check=False,
    )
    if is_ancestor.returncode not in (0, 1):
        detail = (is_ancestor.stderr or is_ancestor.stdout or "").strip()
        raise RuntimeError(f"git merge-base --is-ancestor failed (exit={is_ancestor.returncode}): {detail}")
    if is_ancestor.returncode != 0:
        _git(
            run, clone_dir, "merge", "--no-edit", "--no-ff", "-s", "ours",
            f"refs/remotes/origin/{BASE_BRANCH}", "-m", _SYNC_BASE_MESSAGE,
        )
    _git(run, clone_dir, "read-tree", "--reset", "-u", f"refs/remotes/origin/{BASE_BRANCH}")

    if preserved_dir.is_dir():
        docs_publish_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(preserved_dir, docs_publish_dir, dirs_exist_ok=True)


def _assemble_candidate(
    clone_dir: Path, releases_root: Path, title: str, *, repo_root: Path
) -> Path:
    """Assemble the staged Web releases into ``clone_dir``'s ``docs/publish``.

    ``repo_root`` must be the real auto-manual checkout (the one
    ``releases_root`` lives under), never ``clone_dir`` -- the throwaway
    Hello-Docs clone is only where the assembled *output* lands.
    ``assemble_web_publish_branch`` uses ``repo_root`` for two things, both of
    which require the real checkout: ``_validate_publish_boundaries`` guards
    against ``output_dir`` swallowing the repo root it is passed, and
    ``discover_web_publish_targets`` -> ``load_web_publish_target`` resolves
    each staged target's repo-relative ``md_output_path``/``html_dir``/
    ``language_projection_evidence_path`` against it before checking they
    stay under ``releases_root``. Passing ``clone_dir`` there always failed
    that containment check, because every real ``publish_meta.json`` stores
    those paths relative to the real repo, not to an unrelated clone.
    """

    return assemble_web_publish_branch(
        repo_root=repo_root,
        releases_root=releases_root,
        output_dir=Paths(root=clone_dir).docs_publish_dir,
        title=title,
    )


def _run_aggregate_strict_verification(run: CommandRunner, clone_dir: Path) -> None:
    """Rebuild the just-assembled aggregate ``docs/publish/web`` with ``sphinx -W``.

    Mirrors ``code-as-doc/dev/web_publish_pipeline.md`` section 2.2 step 4.
    Runs in a scratch temp directory outside the clone so it never leaves
    build artifacts inside the candidate tree that would then fail the
    ``docs/publish`` scope guard.

    The ``-D extensions=myst_parser,tools.rtd_portal`` override must match
    ``.readthedocs.yaml``'s ``docs/publish/web`` build command byte for byte
    (module docstring's "environment" claim, not just the source tree): the
    assembled ``conf.py`` (``tools/readthedocs_source.py::_write_conf_py``)
    only declares ``extensions = ["myst_parser"]`` -- Read the Docs bolts
    ``tools.rtd_portal`` on at build time via this same flag, and production
    build 34602012 crashed with ``ExtensionError: ... Unknown portal
    publication language: ja`` precisely because this local gate ran plain
    MyST (no portal extension, so ``tools.rtd_portal.page_context`` -- and
    the language-table lookup inside it -- never executed) while RTD ran the
    portal-enabled build. Keeping ``-W`` even though RTD's own command omits
    it is a strictly stronger local gate, mirroring the same intentional gap
    already documented on ``web_publish._run_strict_web_verification``.
    """

    web_source_dir = Paths(root=clone_dir).docs_publish_web_dir
    if not web_source_dir.is_dir():
        raise RuntimeError(f"assembled candidate has no Web source to verify: {web_source_dir}")
    with tempfile.TemporaryDirectory(prefix="auto-manual-web-assemble-verify-") as raw_temp_dir:
        html_out = Path(raw_temp_dir) / "html"
        result = run(
            [
                sys.executable, "-m", "sphinx", "-W", "-b", "html",
                "-D", "extensions=myst_parser,tools.rtd_portal",
                str(web_source_dir), str(html_out),
            ],
            clone_dir,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"aggregate strict Web verification failed (sphinx -W -b html): {detail[-4000:]}"
            )


def _commit_candidate(run: CommandRunner, clone_dir: Path) -> str | None:
    """Mirror the workflow's "Commit publish candidate" step.

    Returns the new commit SHA, or ``None`` when the candidate tree already
    matched the index (nothing to commit).
    """

    _git(run, clone_dir, "add", "-A")
    diff = _git(run, clone_dir, "diff", "--cached", "--quiet", check=False)
    if diff.returncode == 0:
        return None
    if diff.returncode != 1:
        detail = (diff.stderr or diff.stdout or "").strip()
        raise RuntimeError(f"git diff --cached --quiet failed (exit={diff.returncode}): {detail}")
    _git(run, clone_dir, "commit", "-m", _COMMIT_MESSAGE)
    return _git(run, clone_dir, "rev-parse", "HEAD").stdout.strip()


def _validate_scope(run: CommandRunner, clone_dir: Path) -> tuple[int, tuple[str, ...]]:
    """Mirror the workflow's "Validate publish PR scope" step.

    A three-dot diff against ``main`` (not a plain two-dot diff) so branch
    history drift on either side cannot smuggle an unexpected path into the
    scope check; this must mirror the workflow's own check rather than
    reinvent it, since that check is the entire safety net for
    ``docs/publish`` being the *only* thing the release PR may touch.
    """

    is_ancestor = _git(
        run, clone_dir, "merge-base", "--is-ancestor",
        f"refs/remotes/origin/{BASE_BRANCH}", "HEAD", check=False,
    )
    if is_ancestor.returncode != 0:
        raise RuntimeError(
            f"{PUBLISH_BRANCH} must contain {BASE_BRANCH} as an ancestor before PR scope validation"
        )
    diff = _git(
        run, clone_dir, "diff", "--name-only", "--no-renames", "-z",
        f"refs/remotes/origin/{BASE_BRANCH}...HEAD",
    )
    paths = tuple(part for part in diff.stdout.split("\0") if part)
    invalid = sorted(path for path in paths if not path.startswith(_DOCS_PUBLISH_PREFIX))
    if invalid:
        raise RuntimeError(
            "web-assemble PR may change only docs/publish/**; found: " + ", ".join(invalid)
        )
    return len(paths), paths


def _push_candidate(run: CommandRunner, clone_dir: Path) -> bool:
    """Mirror the workflow's "Push publish candidate branch" step.

    An ordinary (non-force) push: a non-fast-forward remote fails this call
    (``_git`` raises) instead of silently overwriting another publisher's
    work, matching the "one shared mutable candidate" concurrency contract in
    ``code-as-doc/dev/web_publish_pipeline.md``.
    """

    _git(
        run, clone_dir, "fetch", "--no-tags", "origin",
        f"{PUBLISH_BRANCH}:refs/remotes/origin/{PUBLISH_BRANCH}", network=True, check=False,
    )
    remote_ref = _git(
        run, clone_dir, "rev-parse", "--verify", f"refs/remotes/origin/{PUBLISH_BRANCH}", check=False,
    )
    remote_commit = remote_ref.stdout.strip() if remote_ref.returncode == 0 else None
    local_commit = _git(run, clone_dir, "rev-parse", "HEAD").stdout.strip()
    if remote_commit == local_commit:
        return False
    _git(run, clone_dir, "push", "origin", f"HEAD:refs/heads/{PUBLISH_BRANCH}", network=True)
    return True


def _open_or_update_pr(run: CommandRunner, clone_dir: Path) -> str | None:
    """Mirror the workflow's "Open or update publish PR" step.

    ``gh`` auto-detects the target repository from the clone's ``origin``
    remote, so no ``--repo`` flag is passed here.
    """

    listing = run(
        [
            "gh", "pr", "list",
            "--base", BASE_BRANCH,
            "--head", PUBLISH_BRANCH,
            "--state", "open",
            "--json", "url",
            "--jq", ".[0].url // empty",
        ],
        clone_dir,
    )
    if listing.returncode != 0:
        raise RuntimeError(f"gh pr list failed: {(listing.stderr or listing.stdout or '').strip()}")
    existing = listing.stdout.strip()
    if existing:
        return existing

    body = (
        "Automated Web Publish candidate (Git-only `build.py web-assemble` transaction).\n\n"
        "- Only `docs/publish/**` may differ from `main`; web-assemble refuses to push on any other path.\n"
        "- `review/*` branches are build inputs only and must never be merged into `main`.\n"
        "- Merge this PR after review. The resulting `main` push is the only production trigger for Read the Docs.\n"
    )
    create = run(
        [
            "gh", "pr", "create",
            "--base", BASE_BRANCH,
            "--head", PUBLISH_BRANCH,
            "--title", _COMMIT_MESSAGE,
            "--body", body,
        ],
        clone_dir,
    )
    if create.returncode != 0:
        raise RuntimeError(f"gh pr create failed: {(create.stderr or create.stdout or '').strip()}")
    lines = [line.strip() for line in create.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest_targets(manifest_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    targets = payload.get("targets") if isinstance(payload, dict) else None
    if not isinstance(targets, list):
        return []
    return [item for item in targets if isinstance(item, dict)]


def _resolve_releases_root(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
) -> Path:
    raw = str(getattr(args, "releases_root", None) or "").strip()
    if raw:
        return resolve_path_from_root(raw)
    return Paths(root=repo_root).releases_dir


def _print_report(report: AssembleReport) -> None:
    print(f"[web-assemble] Hello-Docs remote: {report.hello_docs_remote}")
    print(f"[web-assemble] releases root: {report.releases_root}")
    print(f"[web-assemble] title: {report.title}")
    if report.dry_run:
        print("[web-assemble] --dry-run: no clone, assembly, or verification ran")
        return
    print(f"[web-assemble] manifest: {report.manifest_path}")
    if report.manifest_sha256:
        print(f"[web-assemble] manifest sha256: {report.manifest_sha256}")
    print(f"[web-assemble] included targets: {len(report.included_targets)}")
    for target in report.included_targets:
        label = f"{target.get('model')}/{target.get('region')}/{target.get('lang')}"
        print(f"[web-assemble]   - {label} @ {target.get('version')}")
    print(f"[web-assemble] docs/publish diff vs {BASE_BRANCH}: {report.changed_path_count} file(s)")
    if report.committed:
        print(f"[web-assemble] committed candidate: {report.commit_sha}")
    else:
        print("[web-assemble] no new commit was needed (candidate tree already matched)")
    if report.pushed:
        print(f"[web-assemble] pushed {PUBLISH_BRANCH} -> origin")
    elif report.commit_sha is not None:
        print(f"[web-assemble] not pushed (pass --push to update {PUBLISH_BRANCH} and its PR)")
    if report.pr_url:
        print(f"[web-assemble] {PUBLISH_BRANCH} -> {BASE_BRANCH} PR: {report.pr_url}")
    print("[web-assemble] merging the publish PR remains a manual, human step")


def run_web_assemble(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
    run: CommandRunner = default_run_command,
) -> AssembleReport:
    """Entry point wired as ``build.py``'s ``web-assemble`` action."""

    releases_root = _resolve_releases_root(
        args, repo_root=repo_root, resolve_path_from_root=resolve_path_from_root
    )
    title = str(getattr(args, "title", None) or "").strip() or DEFAULT_TITLE
    remote = resolve_hello_docs_remote(str(getattr(args, "hello_docs_repo", None) or ""))
    push = bool(getattr(args, "push", False))
    dry_run = bool(getattr(args, "dry_run", False))

    if dry_run:
        report = AssembleReport(
            hello_docs_remote=remote, releases_root=releases_root, title=title, dry_run=True
        )
        _print_report(report)
        return report

    with tempfile.TemporaryDirectory(prefix="auto-manual-web-assemble-") as raw_tmp_dir:
        tmp_root = Path(raw_tmp_dir)
        clone_dir = tmp_root / "hello-docs"
        preserved_dir = tmp_root / "preserved-docs-publish"

        _git(
            run, tmp_root, "clone", "--filter=blob:none", "--no-tags",
            "--branch", BASE_BRANCH, "--single-branch", remote, str(clone_dir),
            network=True,
        )
        _reconcile_candidate(run, clone_dir, preserved_dir)
        manifest_path = _assemble_candidate(clone_dir, releases_root, title, repo_root=repo_root)
        _run_aggregate_strict_verification(run, clone_dir)
        commit_sha = _commit_candidate(run, clone_dir)
        changed_count, changed_paths = _validate_scope(run, clone_dir)
        included_targets = _read_manifest_targets(manifest_path)
        manifest_sha256 = _sha256_file(manifest_path)

        pushed = False
        pr_url: str | None = None
        if push:
            pushed = _push_candidate(run, clone_dir)
            if changed_count > 0:
                pr_url = _open_or_update_pr(run, clone_dir)
            else:
                print(
                    f"[web-assemble] no {BASE_BRANCH}-relative docs/publish changes; "
                    "skipping PR open/update"
                )

        report = AssembleReport(
            hello_docs_remote=remote,
            releases_root=releases_root,
            title=title,
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            included_targets=tuple(included_targets),
            changed_path_count=changed_count,
            changed_paths=changed_paths,
            committed=commit_sha is not None,
            commit_sha=commit_sha,
            pushed=pushed,
            pr_url=pr_url,
        )
        _print_report(report)
        return report


__all__ = (
    "AssembleReport",
    "CommandRunner",
    "DEFAULT_HELLO_DOCS_REPO",
    "DEFAULT_TITLE",
    "default_run_command",
    "resolve_hello_docs_remote",
    "run_web_assemble",
)
