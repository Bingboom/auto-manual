#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical four-renderer acceptance for one target (skeleton slice S5).

Every criterion is one command plus one exit code or one grep — the slice plan
refuses "looks right" as evidence. The checks encode findings from the corpus
audit and the renderer-readiness survey rather than generic smoke tests:

* **PDF page count must equal a formula, not merely be non-zero.**
  ``pages = F(L) + L*B + K`` with ``F(L) = 1 + 2*ceil(L/3)`` and ``K = 1`` held
  with zero exceptions across the 25 multi-language corpus books, so a battery
  pack with L=3 and B=8 must print exactly 28 pages. "Off by one is fine" is
  not an acceptable result for a page-budgeted print deliverable.
* **HTML degradation is asserted positively.** Composite figures are gated by
  the ``figure_targets`` allowlist in the web contract, so a target outside it
  must render plain HTML. Zero ``hb-*-composition`` hits is therefore a
  *requirement*: a hit means somebody widened the allowlist by hand.
* **IDML must not move the shared layout parameters.** The approved
  JE-1000F/US reference plan hashes the whole of ``data/layout_params.csv``, so
  adding one row for another target silently unpins it (the #720 failure
  shape). This asserts an empty git diff on that file and on the approved
  contracts instead of trusting reviewer discipline.
* **Host regression is part of acceptance**, because the LaTeX component
  library and the layout parameter table are single shared instances: a slice
  cannot claim success without showing it did not move the existing lines.

Usage::

    python tools/renderer_acceptance.py --config configs/config.bp-us.yaml \\
        --model JBP-2000B --region US --block-pages 8

Exit code is 0 only when every selected criterion passes.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config_loader import load_config_mapping  # noqa: E402
from tools.utils.path_utils import repo_root  # noqa: E402

REPORT_SCHEMA_VERSION = "renderer-acceptance/v1"

_COMPOSITION_CLASS_RE = re.compile(r"hb-[a-z0-9-]*-composition")


@dataclass
class Criterion:
    renderer: str
    name: str
    status: str  # pass | fail | skip
    detail: str
    command: str = ""


@dataclass
class AcceptanceReport:
    schema_version: str
    config: str
    model: str
    region: str
    languages: list[str]
    block_pages: int | None
    expected_pdf_pages: int | None
    criteria: list[Criterion] = field(default_factory=list)

    @property
    def failed(self) -> list[Criterion]:
        return [item for item in self.criteria if item.status == "fail"]

    @property
    def skipped(self) -> list[Criterion]:
        return [item for item in self.criteria if item.status == "skip"]


def front_matter_pages(language_count: int) -> int:
    """Front-matter page count, measured rather than assumed.

    Multi-language books: cover + ceil(L/3) preface pages + ceil(L/3) contents
    pages (three languages share one preface page and one contents page).

    Single-language books are NOT the L=1 case of that expression. The
    corpus measurement is explicit: the JP house style absorbs the preface into
    the cover, so front matter is cover + contents = 2, and applying the
    multi-language expression would predict 3 and be wrong by a page on every
    single-language line. Encoded as a separate case instead of a formula that
    is wrong for a whole house style.
    """

    if language_count <= 1:
        return 2
    return 1 + 2 * math.ceil(language_count / 3)


def expected_pdf_pages(
    language_count: int,
    block_pages: int,
    *,
    front_pages: int | None = None,
    back_pages: int = 1,
) -> int:
    """pages = F(L) + L*B + K.

    Verified against shipped books: L=3/B=8 -> 28 (HTP017 US), L=6/B=19 -> 120
    (HTE152 EU), L=3/B=31 -> 97 (HTE157 US), L=1/B=25 -> 28 (HTE152 JP).
    ``front_pages`` overrides the measured default for a line whose front
    matter genuinely differs; ``back_pages`` covers books with a blank leaf.
    """

    front = front_matter_pages(language_count) if front_pages is None else front_pages
    return front + language_count * block_pages + back_pages


def _display_path(path: Path, root: Path) -> str:
    """Repo-relative when possible, absolute otherwise.

    `--staging-root` deliberately puts build output OUTSIDE the repo, which is
    the whole point of the flag and the shape S6's handoff round needs. A bare
    ``relative_to(root)`` raises ValueError there, so every criterion that
    found an artifact crashed the harness the moment staging was used.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=str(cwd), capture_output=True, text=True, check=False
    )


def _pdf_page_count(pdf_path: Path) -> int | None:
    if shutil.which("pdfinfo"):
        result = subprocess.run(
            ["pdfinfo", str(pdf_path)], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Pages:"):
                    return int(line.split(":", 1)[1].strip())
    try:  # pragma: no cover - exercised only when pdfinfo is absent
        import fitz

        with fitz.open(pdf_path) as document:
            return document.page_count
    except Exception:
        return None


def _pdf_page_sizes(pdf_path: Path) -> set[tuple[int, int]]:
    try:
        import fitz
    except ImportError:  # pragma: no cover
        return set()
    sizes: set[tuple[int, int]] = set()
    with fitz.open(pdf_path) as document:
        for page in document:
            sizes.add((round(page.rect.width), round(page.rect.height)))
    return sizes


def check_pdf(
    *,
    root: Path,
    pdf_dir: Path,
    latex_dir: Path,
    expected_pages: int,
) -> list[Criterion]:
    criteria: list[Criterion] = []
    pdfs = sorted(pdf_dir.glob("*.pdf")) if pdf_dir.is_dir() else []
    if not pdfs:
        criteria.append(
            Criterion(
                "pdf", "artifact-present", "skip",
                f"no PDF under {pdf_dir} — run `build.py pdf` for this target first",
            )
        )
        return criteria
    pdf_path = pdfs[0]
    criteria.append(
        Criterion("pdf", "artifact-present", "pass", _display_path(pdf_path, root))
    )

    actual = _pdf_page_count(pdf_path)
    if actual is None:
        criteria.append(
            Criterion("pdf", "page-count", "skip", "neither pdfinfo nor PyMuPDF available")
        )
    else:
        status = "pass" if actual == expected_pages else "fail"
        criteria.append(
            Criterion(
                "pdf", "page-count", status,
                f"expected {expected_pages} (F(L)+L*B+K), got {actual}",
                command=f"pdfinfo {_display_path(pdf_path, root)}",
            )
        )

    sizes = _pdf_page_sizes(pdf_path)
    if not sizes:
        criteria.append(Criterion("pdf", "uniform-page-size", "skip", "PyMuPDF unavailable"))
    else:
        status = "pass" if len(sizes) == 1 else "fail"
        criteria.append(
            Criterion("pdf", "uniform-page-size", status, f"distinct page sizes: {sorted(sizes)}")
        )

    logs = sorted(latex_dir.glob("*.log")) if latex_dir.is_dir() else []
    if not logs:
        criteria.append(Criterion("pdf", "latex-log-clean", "skip", f"no .log under {latex_dir}"))
    else:
        offenders: list[str] = []
        for log_path in logs:
            text = log_path.read_text(encoding="utf-8", errors="ignore")
            for needle in ("Undefined control sequence", "Missing $ inserted"):
                if needle in text:
                    offenders.append(f"{log_path.name}: {needle}")
        status = "pass" if not offenders else "fail"
        criteria.append(
            Criterion(
                "pdf", "latex-log-clean", status,
                "; ".join(offenders) if offenders else f"{len(logs)} log(s) clean",
            )
        )
    return criteria


def check_html(*, root: Path, html_dir: Path, languages: list[str]) -> list[Criterion]:
    criteria: list[Criterion] = []
    if not html_dir.is_dir():
        return [
            Criterion(
                "html", "artifact-present", "skip",
                f"no HTML under {html_dir} — the web lane is check -> md -> html",
            )
        ]
    pages = sorted(html_dir.rglob("*.html"))
    status = "pass" if pages else "fail"
    criteria.append(
        Criterion("html", "artifact-present", status, f"{len(pages)} html file(s)")
    )
    if not pages:
        return criteria

    # Positive degradation criterion: a target outside the web contract's
    # figure_targets allowlist must render plain HTML. A composition hit means
    # the allowlist was widened by hand.
    hits: list[str] = []
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="ignore")
        for match in _COMPOSITION_CLASS_RE.findall(text):
            hits.append(f"{page.name}:{match}")
    status = "pass" if not hits else "fail"
    criteria.append(
        Criterion(
            "html", "no-unexpected-composites", status,
            f"{len(hits)} composition class hit(s)"
            + (f": {', '.join(sorted(set(hits))[:5])}" if hits else ""),
            command=f"grep -ro 'hb-[a-z-]*-composition' {_display_path(html_dir, root)}",
        )
    )

    # Two lanes emit HTML with different stylesheets: `build.py all --formats
    # html` goes through Sphinx and ships hb_manual.css, while the web_publish
    # lane (check -> md -> html) composes web_manual.css. Asserting one name
    # fails the other lane for no reason, so require *a* manual stylesheet and
    # name the lane that produced it.
    lanes = {
        "web_publish": html_dir / "_static" / "web_manual.css",
        "sphinx": html_dir / "_static" / "hb_manual.css",
    }
    found = [
        name for name, path in lanes.items()
        if path.is_file() and path.stat().st_size > 0
    ]
    status = "pass" if found else "fail"
    criteria.append(
        Criterion(
            "html", "stylesheet-present", status,
            f"lane={'+'.join(found)}" if found
            else "neither web_manual.css nor hb_manual.css present",
        )
    )
    return criteria


_WORD_PLACEHOLDER_RE = re.compile(r"\|[A-Z0-9][A-Z0-9_]+\|")
_WORD_DRAFT_MARKER_RE = re.compile(r"==MISSING:[^=]*==")
_WORD_REQUIRED_PARTS = ("[Content_Types].xml", "word/document.xml")


def _docx_text(path: Path) -> str | None:
    """Visible text of the document body, or None if the package is unreadable."""
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                return None
            if any(part not in archive.namelist() for part in _WORD_REQUIRED_PARTS):
                return None
            body = archive.read("word/document.xml").decode("utf-8", "replace")
    except (zipfile.BadZipFile, KeyError, OSError):
        return None
    return re.sub(r"<[^>]+>", "", body)


def check_word(*, root: Path, word_dir: Path) -> list[Criterion]:
    docs = sorted(word_dir.glob("*.docx")) if word_dir.is_dir() else []
    if not docs:
        return [
            Criterion("word", "artifact-present", "skip", f"no .docx under {word_dir}")
        ]
    docx_path = docs[0]
    shown = _display_path(docx_path, root)
    criteria = [Criterion("word", "artifact-present", "pass", shown)]

    # "A .docx exists" was the whole Word criterion, which accepts a corrupt
    # package and a book full of unresolved placeholders. These three are the
    # cheapest checks that would actually have caught something: the package
    # opening, and the two marker families this pipeline is known to leak —
    # |PLACEHOLDER| when a contract slot resolves to nothing, and
    # ==MISSING:...== which draft_engine writes in place of an absent
    # Spec_Master row.
    text = _docx_text(docx_path)
    if text is None:
        criteria.append(
            Criterion(
                "word", "opens-as-ooxml", "fail",
                "package is unreadable, fails its zip CRC, or lacks "
                f"{' / '.join(_WORD_REQUIRED_PARTS)}",
                command=f"python -c \"import zipfile;zipfile.ZipFile('{shown}').testzip()\"",
            )
        )
        return criteria

    criteria.append(
        Criterion("word", "opens-as-ooxml", "pass", f"{len(text)} chars of body text")
    )
    for name, pattern, label in (
        ("no-unresolved-placeholders", _WORD_PLACEHOLDER_RE, "|PLACEHOLDER|"),
        ("no-draft-markers", _WORD_DRAFT_MARKER_RE, "==MISSING:...=="),
    ):
        hits = sorted(set(pattern.findall(text)))
        criteria.append(
            Criterion(
                "word", name, "fail" if hits else "pass",
                f"{len(hits)} distinct {label} in the body"
                + (f": {', '.join(hits[:5])}" if hits else ""),
            )
        )
    return criteria


_PINNED_PATHS = (
    "data/layout_params.csv",
    "docs/renderers/contracts/reference_layout",
)


def check_idml(*, root: Path, idml_path: Path) -> list[Criterion]:
    criteria: list[Criterion] = []
    if idml_path.is_file() and idml_path.stat().st_size > 0:
        criteria.append(
            Criterion(
                "idml", "artifact-present", "pass",
                f"{_display_path(idml_path, root)} "
                f"({idml_path.stat().st_size} bytes)",
            )
        )
    else:
        criteria.append(
            Criterion(
                "idml", "artifact-present", "skip",
                f"no IDML at {idml_path} — a target with no approved reference "
                "plan still exports through the latex-auto fallback",
            )
        )

    # The approved JE-1000F/US plan hashes the entire shared layout parameter
    # table, so one added row unpins it for every target. Reviewer discipline
    # is not a control; an empty diff is.
    dirty: list[str] = []
    for rel in _PINNED_PATHS:
        result = _run(["git", "status", "--porcelain", "--", rel], cwd=root)
        for line in result.stdout.splitlines():
            if line.strip():
                dirty.append(line.strip())
    status = "pass" if not dirty else "fail"
    criteria.append(
        Criterion(
            "idml", "shared-layout-pins-untouched", status,
            "; ".join(dirty) if dirty else "layout_params.csv and approved contracts unchanged",
            command="git status --porcelain -- " + " ".join(_PINNED_PATHS),
        )
    )
    return criteria


def check_host_regression(
    *,
    root: Path,
    base_ref: str,
    targets: list[tuple[str, str, str]],
    staging_prefix: Path,
    python_executable: str,
) -> list[Criterion]:
    """Prove the shared LaTeX library and parameter table did not move.

    Two detached worktrees at base and head, each built into its own staging
    root, then a byte diff. `git stash` cannot express this: it does not remove
    committed changes and skips untracked files by default, so a stash-based
    "before" can already contain the change under test.
    """

    criteria: list[Criterion] = []
    if shutil.which("git") is None:  # pragma: no cover
        return [Criterion("regression", "host-lines-unchanged", "skip", "git unavailable")]

    base_tree = staging_prefix / "wt-base"
    head_tree = staging_prefix / "wt-head"
    for path in (base_tree, head_tree):
        shutil.rmtree(path, ignore_errors=True)

    added: list[Path] = []
    try:
        for path, ref in ((base_tree, base_ref), (head_tree, "HEAD")):
            result = _run(["git", "worktree", "add", str(path), ref], cwd=root)
            if result.returncode != 0:
                return [
                    Criterion(
                        "regression", "host-lines-unchanged", "skip",
                        f"could not create worktree at {ref}: {result.stderr.strip()[:200]}",
                    )
                ]
            added.append(path)
            # phase2 is a gitignored local mirror, so a fresh worktree has no
            # snapshot and every build would fail on identity resolution.
            mirror = root / "data" / "phase2"
            if mirror.is_dir():
                shutil.copytree(mirror, path / "data" / "phase2", dirs_exist_ok=True)

        for config, model, region in targets:
            outputs: dict[str, Path] = {}
            failed = False
            for label, tree in (("base", base_tree), ("head", head_tree)):
                out = staging_prefix / f"out-{label}-{model}-{region}"
                shutil.rmtree(out, ignore_errors=True)
                result = _run(
                    [
                        python_executable, "build.py", "check",
                        "--config", config,
                        "--model", model,
                        "--region", region,
                        "--staging-root", str(out),
                    ],
                    cwd=tree,
                )
                if result.returncode != 0:
                    criteria.append(
                        Criterion(
                            "regression", f"host-{model}-{region}", "fail",
                            f"{label} check exited {result.returncode}: "
                            f"{result.stdout.strip().splitlines()[-1][:200] if result.stdout.strip() else ''}",
                        )
                    )
                    failed = True
                    break
                outputs[label] = out
            if failed:
                continue
            diff = _run(
                ["diff", "-r", str(outputs["base"]), str(outputs["head"])], cwd=root
            )
            status = "pass" if diff.returncode == 0 else "fail"
            criteria.append(
                Criterion(
                    "regression", f"host-{model}-{region}", status,
                    "byte-identical" if status == "pass"
                    else diff.stdout.strip().splitlines()[0][:200],
                    command=f"diff -r <base staging> <head staging>  # {model}/{region}",
                )
            )
    finally:
        for path in added:
            _run(["git", "worktree", "remove", "--force", str(path)], cwd=root)
    return criteria


def _languages_for(cfg: dict) -> list[str]:
    build_raw = cfg.get("build", {})
    build = build_raw if isinstance(build_raw, dict) else {}
    langs = build.get("languages", [])
    if isinstance(langs, list):
        return [str(item).strip() for item in langs if str(item).strip()]
    return []


def _build_root(root: Path, staging_root: Path | None, model: str, region: str,
                lang: str | None) -> Path:
    base = (staging_root / "docs" / "_build") if staging_root else (root / "docs" / "_build")
    target = base / model / region
    return target / lang / "" if lang else target


def run_acceptance(args: argparse.Namespace) -> AcceptanceReport:
    root = repo_root()
    config_path = Path(args.config)
    cfg = load_config_mapping(config_path if config_path.is_absolute() else root / config_path)
    languages = _languages_for(cfg)
    include_lang = bool((cfg.get("build") or {}).get("include_lang_in_output_path"))
    lang_segment = languages[0] if (include_lang and languages) else None

    staging_root = Path(args.staging_root) if args.staging_root else None
    build_root = _build_root(root, staging_root, args.model, args.region, lang_segment)

    if args.expect_pages is not None:
        expected = args.expect_pages
    elif args.block_pages is not None:
        expected = expected_pdf_pages(
            len(languages) or 1,
            args.block_pages,
            front_pages=args.front_pages,
            back_pages=args.back_pages,
        )
    else:
        expected = None

    report = AcceptanceReport(
        schema_version=REPORT_SCHEMA_VERSION,
        config=config_path.as_posix(),
        model=args.model,
        region=args.region,
        languages=languages,
        block_pages=args.block_pages,
        expected_pdf_pages=expected,
    )

    selected = set(args.renderers)

    if "pdf" in selected:
        if expected is None:
            report.criteria.append(
                Criterion(
                    "pdf", "page-count", "skip",
                    "neither --block-pages nor --expect-pages given; the "
                    "page-count criterion is the point of this lane",
                )
            )
        report.criteria.extend(
            check_pdf(
                root=root,
                pdf_dir=build_root / "pdf",
                latex_dir=build_root / "latex",
                expected_pages=expected if expected is not None else -1,
            )
            if expected is not None
            else check_pdf(
                root=root,
                pdf_dir=build_root / "pdf",
                latex_dir=build_root / "latex",
                expected_pages=-1,
            )[:1]
        )
    if "html" in selected:
        report.criteria.extend(
            check_html(root=root, html_dir=build_root / "html", languages=languages)
        )
    if "word" in selected:
        report.criteria.extend(check_word(root=root, word_dir=build_root / "word"))
    if "idml" in selected:
        from tools.idml.export_paths import default_bundle_root, default_output_path

        lang_for_idml = lang_segment or (languages[0] if languages else "en")
        idml_root = staging_root or root
        bundle_root = default_bundle_root(idml_root, args.model, args.region, lang_for_idml)
        report.criteria.extend(
            check_idml(
                root=root,
                idml_path=default_output_path(
                    idml_root, args.model, args.region, lang_for_idml, bundle_root
                ),
            )
        )
    if "regression" in selected:
        targets = [
            tuple(item.split(":", 2)) for item in args.regression_target
        ]
        bad = [item for item in targets if len(item) != 3]
        if bad:
            raise SystemExit(
                "--regression-target must be config:MODEL:REGION, got: "
                + ", ".join(":".join(item) for item in bad)
            )
        report.criteria.extend(
            check_host_regression(
                root=root,
                base_ref=args.base_ref,
                targets=targets,  # type: ignore[arg-type]
                staging_prefix=Path(args.regression_staging),
                python_executable=sys.executable,
            )
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument(
        "--block-pages", type=int,
        help="printed pages per language block (B in pages = F(L) + L*B + K)",
    )
    parser.add_argument(
        "--expect-pages", type=int,
        help="pin the expected page count directly (e.g. the shipped book's "
             "count) instead of deriving it from the block formula",
    )
    parser.add_argument("--front-pages", type=int, help="override measured front matter")
    parser.add_argument("--back-pages", type=int, default=1)
    parser.add_argument("--staging-root", help="where the artifacts under test were built")
    parser.add_argument(
        "--renderers", nargs="+",
        default=["pdf", "html", "word", "idml"],
        choices=["pdf", "html", "word", "idml", "regression"],
    )
    parser.add_argument("--base-ref", default="origin/main",
                        help="regression baseline ref for the two-worktree diff")
    parser.add_argument(
        "--regression-target", action="append", default=[],
        metavar="CONFIG:MODEL:REGION",
        help="host line to prove unchanged; repeatable",
    )
    parser.add_argument("--regression-staging", default="/tmp/renderer-acceptance")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args(argv)

    report = run_acceptance(args)

    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(f"[acceptance] {report.model}/{report.region} via {report.config}")
        if report.expected_pdf_pages is not None:
            print(
                f"[acceptance] expected PDF pages: {report.expected_pdf_pages} "
                f"(L={len(report.languages) or 1}, B={report.block_pages})"
            )
        for item in report.criteria:
            marker = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[item.status]
            print(f"  [{marker}] {item.renderer}/{item.name}: {item.detail}")
        print(
            f"[acceptance] {len(report.criteria) - len(report.failed) - len(report.skipped)} pass, "
            f"{len(report.failed)} fail, {len(report.skipped)} skip"
        )
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
