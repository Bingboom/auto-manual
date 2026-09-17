"""``build.py web-sideload``: land an externally converted book without the pipeline.

Some books need to go live before their structured intake (spec extraction,
templating) is done. Sideload is the bypass intake for exactly that case: an
externally converted MyST Markdown source (typically transcribed from a
shipped PDF) is compiled and staged into ``reports/releases/<model>/<region>/<lang>/``
using the *same* staging and metadata functions ``build.py web-release`` uses
(``tools.queue_bound_outputs.stage_web_publish_assets_to_host_repo`` and
``write_web_publish_metadata``), so ``build.py web-assemble`` collects it with
equal standing to a pipeline-built book. It never runs the RST -> Web-profile
pipeline and therefore never produces the per-language projection evidence
that path seals; instead every sideloaded target is written with an explicit
``source_kind: "pdf_sideload"`` marker in its ``publish_meta.json``.

Sideloading has two planes, and only the first is written by a human:

* **Author plane** (``--md-dir``) -- prose plus the semantic component
  directives of ``tools.manual_md_directives`` (``{callout}``,
  ``{spec-table}``, ...). Hand-written component markup is refused here.
* **Staged plane** -- the same document with every directive compiled into
  component markup by ``tools.web_sideload_expand``. This is what gets
  staged, because Read the Docs rebuilds the published source with
  ``-D extensions=myst_parser,tools.rtd_portal`` (``.readthedocs.yaml``),
  which overrides ``conf.py`` and can never load the directive layer.

The operator's ``--md-dir`` is never modified; compilation runs on a copy.

That marker is the *only* thing that exempts a target from the mandatory
language-projection-evidence gate in ``tools.publish_locale_identity`` /
``tools.publish_branch_assembly``. Every ordinary pipeline target (no
``source_kind``, or ``source_kind: "pipeline"``) stays exactly as fail-closed
as before this command existed -- see ``tools.web_language_release_evidence``
for the shared constants and ``tests/test_publish_branch_assembly.py`` for
the negative control proving that.

Landing a sideloaded book always records one automatic debt-ledger entry
("整本未结构化") whose payoff action is the eventual structured intake
(``.agents/skills/spec-sheet-structured-intake/SKILL.md``); once that intake
lands, an ordinary ``build.py web-release`` run for the same
model/region/lang/version-family overwrites this target's
``latest/web/publish_meta.json`` with a real pipeline build, seamlessly
superseding the sideload -- no separate withdrawal step is needed.

See ``code-as-doc/dev/web_publish_pipeline.md`` and
``.agents/skills/pdf-web-sideload/SKILL.md`` for the full operator workflow.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from tools.queue_bound_outputs import (
    publish_release_version_dir_for_target,
    resolve_md_output_path_for_target,
    set_repo_root_provider as _set_queue_output_repo_root_provider,
    stage_web_publish_assets_to_host_repo,
    write_web_publish_metadata,
)
from tools.readthedocs_source import assemble_rtd_source
from tools.utils.path_utils import PathSegments
from tools.web_language_release_evidence import SOURCE_KIND_PDF_SIDELOAD
from tools.web_sideload_expand import (
    expand_sideload_bundle,
    verify_expanded_products,
)
from tools.web_publish import (
    DebtEntry,
    WebReleaseTarget,
    check_batch_for_collisions,
    parse_debt_flag,
    record_debt_entries,
)


DEBT_CATEGORY_UNSTRUCTURED_BOOK = "整本未结构化"
DEBT_PAYOFF_ACTION_UNSTRUCTURED_BOOK = (
    "spec-sheet-structured-intake 正式入库后重新 web-release 覆盖"
)


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


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
            f"cannot resolve local Git HEAD SHA for Web sideload evidence under {repo_root}"
        )
    return sha


def _validate_md_dir_shape(*, md_dir: Path, expected_manual_name: str) -> Path:
    """Confirm ``--md-dir`` is shaped like a staged ``md/`` bundle.

    Only the piece that is otherwise silently wrong -- the manual filename --
    is checked here with a helpful error; the remaining shape (``index.md``
    referencing that filename, ``conf.py``, optional ``assets/``) is already
    enforced with clear errors by ``assemble_rtd_source`` /
    ``discover_manual_sources`` during the strict verification step below, so
    duplicating those checks here would only be able to drift out of sync
    with them.
    """

    if md_dir.is_symlink() or not md_dir.is_dir():
        raise RuntimeError(f"web-sideload --md-dir must be a real directory: {md_dir}")
    manual_path = md_dir / expected_manual_name
    if manual_path.is_file():
        return manual_path
    existing = sorted(path.name for path in md_dir.glob("*.md"))
    raise RuntimeError(
        "web-sideload --md-dir is missing the expected manual file "
        f"{expected_manual_name!r} (derived from --config/--model/--region/--lang's output "
        f"naming template) under {md_dir}; found instead: {existing or '(no .md files)'}"
    )


#: What Read the Docs actually builds the published source with -- see
#: ``.readthedocs.yaml``, which passes this as ``-D extensions=...`` and
#: therefore overrides whatever ``conf.py`` declares.
RTD_EXTENSIONS = "myst_parser,tools.rtd_portal"


def _run_sideload_two_stage_verification(
    *, md_dir: Path, title: str, repo_root: Path
) -> tuple[Path, Path]:
    """Verify the author plane, compile it, then verify the staged plane.

    Unlike ``web_publish._run_strict_web_verification`` -- a throwaway gate
    re-checking a build output ``build.py html`` already produced separately
    -- a sideloaded book has no separate pipeline HTML build to gate against.
    This *is* the staging input, so the returned directories are not cleaned
    up here; the caller stages from them and removes their shared parent
    (``returned_html.parent``) once staging has copied what it needs.

    Stage 1 builds the operator's bundle with ``tools.manual_md_directives``
    loaded, so every semantic directive must parse, and compiles each one into
    its component markup. Stage 2 then rebuilds the *compiled* bundle under
    exactly the extension set Read the Docs uses, which is what proves the
    staged artifact will render there -- the old single-stage gate loaded
    neither the directive layer nor ``tools.rtd_portal``, so it could accept a
    document that RTD cannot build.

    The operator's ``--md-dir`` is never modified: expansion runs against a
    private copy.
    """

    temp_dir = Path(tempfile.mkdtemp(prefix="auto-manual-web-sideload-verify-"))
    try:
        build_root = temp_dir / "source"
        expanded_md_dir = build_root / PathSegments.MD
        shutil.copytree(md_dir, expanded_md_dir)

        # Stage 1: author plane -- lint, strict directive-aware build, compile.
        counts = expand_sideload_bundle(md_dir=expanded_md_dir, repo_root=repo_root)
        verify_expanded_products(md_dir=expanded_md_dir, counts=counts)
        summary = ", ".join(f"{name}x{used}" for name, used in sorted(counts.items()))
        print(
            "[web-sideload]   authored components expanded: "
            + (summary or "(none declared)")
        )

        # Stage 2: staged plane, under the published extension set.
        # Nested under build_root: assemble_rtd_source requires its output_dir
        # to stay inside build_root (see _is_relative_to there); a sibling
        # directory trips that containment check on every real run. Nesting
        # is safe -- discover_manual_sources excludes anything under
        # output_dir from its own source search.
        assembled_dir = build_root / "rtd"
        assemble_rtd_source(build_root=build_root, output_dir=assembled_dir, title=title)
        html_out = temp_dir / "html"
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(repo_root), *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
        )
        proc = subprocess.run(
            [
                sys.executable, "-m", "sphinx", "-W", "-b", "html",
                "-D", f"extensions={RTD_EXTENSIONS}",
                str(assembled_dir), str(html_out),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(
                "strict Web sideload verification failed (sphinx -W -b html, "
                f"extensions={RTD_EXTENSIONS}): {detail[-4000:]}"
            )
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return expanded_md_dir, html_out


def run_web_sideload(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
) -> None:
    """Entry point wired as ``build.py``'s ``web-sideload`` action."""

    config_path = resolve_path_from_root(args.config)
    model = str(getattr(args, "model", None) or "").strip()
    region = str(getattr(args, "region", None) or "").strip()
    lang = str(getattr(args, "lang", None) or "").strip()
    version = str(getattr(args, "version", None) or "").strip()
    raw_md_dir = str(getattr(args, "md_dir", None) or "").strip()
    manual_debt = tuple(parse_debt_flag(raw) for raw in (getattr(args, "debt", None) or ()))
    dry_run = bool(getattr(args, "dry_run", False))

    missing = [
        name
        for name, value in (
            ("--model", model),
            ("--region", region),
            ("--lang", lang),
            ("--version", version),
            ("--md-dir", raw_md_dir),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"web-sideload requires {', '.join(missing)}")

    md_dir = resolve_path_from_root(raw_md_dir)
    target = WebReleaseTarget(model=model, region=region, lang=lang, version=version)

    # a. Reuse the web-release batch collision precheck (a batch of one):
    # fails fast against real production path/route derivation before any
    # verification cost, same as a pipeline release.
    check_batch_for_collisions(config_path=config_path, targets=[target])

    # b. --md-dir must already be named for this exact target: the manual
    # filename must match what the config's output-naming template would
    # produce, so a later pipeline web-release for the same target overwrites
    # this one in place instead of leaving two manuals on disk.
    expected_md_output_path = resolve_md_output_path_for_target(
        config_path=config_path, model=model, region=region, lang=lang
    )
    manual_path = _validate_md_dir_shape(
        md_dir=md_dir, expected_manual_name=expected_md_output_path.name
    )

    if dry_run:
        print(f"[web-sideload] plan: {target.label()}; no staging will happen (--dry-run)")
        print(f"[web-sideload]   md-dir     = {md_dir}")
        print(f"[web-sideload]   manual     = {manual_path.name}")
        print(f"[web-sideload]   source_kind = {SOURCE_KIND_PDF_SIDELOAD}")
        print(
            "[web-sideload]   debt        = 1 automatic "
            f"({DEBT_CATEGORY_UNSTRUCTURED_BOOK}) + {len(manual_debt)} manual entrie(s)"
        )
        return

    _set_queue_output_repo_root_provider(lambda: repo_root)
    git_ref = _current_git_head_sha(repo_root)

    # c. Two-stage local verification straight off the operator-provided
    # source. Neither output is thrown away: the compiled Markdown is what
    # gets staged (the author's directives cannot survive to Read the Docs),
    # and the HTML is the staging HTML input, since there is no separate
    # pipeline build.py html step here.
    expanded_md_dir, html_dir = _run_sideload_two_stage_verification(
        md_dir=md_dir, title=f"{model} {region} {lang}", repo_root=repo_root
    )
    expanded_manual_path = expanded_md_dir / manual_path.name
    try:
        # d. Stage + write metadata with no projection evidence, marked
        # pdf_sideload so the assembler's otherwise-mandatory evidence gate
        # (unchanged for every pipeline target) recognizes the exemption.
        staged_md_output_path, staged_html_dir = stage_web_publish_assets_to_host_repo(
            built_md_output_path=expanded_manual_path,
            built_html_dir=html_dir,
            host_config_path=config_path,
            model=model,
            region=region,
            version=version,
            target_lang=lang,
            source_kind=SOURCE_KIND_PDF_SIDELOAD,
        )
    finally:
        shutil.rmtree(html_dir.parent, ignore_errors=True)

    metadata_path = write_web_publish_metadata(
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        git_ref=git_ref,
        built_at=datetime.now(timezone.utc),
        md_output_path=staged_md_output_path,
        html_dir=staged_html_dir,
        target_lang=lang,
        source_kind=SOURCE_KIND_PDF_SIDELOAD,
    )

    # e. Unconditional debt: sideloading a book is never a substitute for its
    # structured intake, so this entry is recorded regardless of --debt.
    today = _today_iso()
    debt_entries = [
        DebtEntry(
            model=model,
            region=region,
            lang=lang,
            date=today,
            category=DEBT_CATEGORY_UNSTRUCTURED_BOOK,
            location=target.label(),
            payoff_action=DEBT_PAYOFF_ACTION_UNSTRUCTURED_BOOK,
            source="auto",
        )
    ] + [
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
    ]
    record_debt_entries(
        repo_root=repo_root, config_path=config_path, target=target, entries=debt_entries
    )

    print(f"[web-sideload] OK {target.label()} -> {metadata_path}")
    print(f"[web-sideload]   md   = {staged_md_output_path}")
    print(f"[web-sideload]   html = {staged_html_dir}")
    print(f"[web-sideload]   debt = {len(debt_entries)} entrie(s) recorded (1 automatic)")


__all__ = (
    "DEBT_CATEGORY_UNSTRUCTURED_BOOK",
    "DEBT_PAYOFF_ACTION_UNSTRUCTURED_BOOK",
    "run_web_sideload",
)
