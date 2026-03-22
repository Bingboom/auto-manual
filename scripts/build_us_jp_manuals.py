#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALID_FORMATS = ("html", "word", "pdf")
DEFAULT_LANGUAGES = ("en", "es", "fr", "ja")


@dataclass(frozen=True)
class MatrixTarget:
    language: str
    region: str
    config: str
    include_lang_in_output_path: bool
    word_template: str
    pdf_template: str

    @property
    def label(self) -> str:
        return f"{self.region}/{self.language}"


@dataclass(frozen=True)
class PlannedCommand:
    target: MatrixTarget
    action: str
    command: list[str]

    @property
    def label(self) -> str:
        return f"[{self.target.label}] {self.action}"


TARGETS: dict[str, MatrixTarget] = {
    "en": MatrixTarget(
        language="en",
        region="US",
        config="config.us-en.yaml",
        include_lang_in_output_path=True,
        word_template="manual_{model_slug}_{region_slug}_{lang_slug}.docx",
        pdf_template="manual_{model_slug}_{region_slug}_{lang_slug}.pdf",
    ),
    "es": MatrixTarget(
        language="es",
        region="US",
        config="config.us-es.yaml",
        include_lang_in_output_path=True,
        word_template="manual_{model_slug}_{region_slug}_{lang_slug}.docx",
        pdf_template="manual_{model_slug}_{region_slug}_{lang_slug}.pdf",
    ),
    "fr": MatrixTarget(
        language="fr",
        region="US",
        config="config.us-fr.yaml",
        include_lang_in_output_path=True,
        word_template="manual_{model_slug}_{region_slug}_{lang_slug}.docx",
        pdf_template="manual_{model_slug}_{region_slug}_{lang_slug}.pdf",
    ),
    "ja": MatrixTarget(
        language="ja",
        region="JP",
        config="config.ja.yaml",
        include_lang_in_output_path=False,
        word_template="manual_{model_slug}_{region_slug}.docx",
        pdf_template="manual_{model_slug}_{region_slug}.pdf",
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Build the US (en/es/fr) and JP (ja) manual set in one command.",
    )
    ap.add_argument("--model", required=True, help="Explicit model to build, for example JE-1000F")
    ap.add_argument(
        "--languages",
        nargs="+",
        default=["en,es,fr,ja"],
        help="Subset of en, es, fr, ja, or 'all'. Accepts comma-separated or space-separated values.",
    )
    ap.add_argument(
        "--formats",
        nargs="+",
        default=["html,word,pdf"],
        help="Subset of html, word, pdf, or 'all'. Accepts comma-separated or space-separated values.",
    )
    ap.add_argument(
        "--source",
        choices=("auto", "runtime", "review"),
        default="auto",
        help="Build source mode forwarded to build.py",
    )
    ap.add_argument("--pdf-mode", choices=("latex", "word"), default=None, help="Override PDF backend")
    ap.add_argument("--check-first", action="store_true", help="Run build.py check before exporting each target")
    ap.add_argument("--open", action="store_true", help="Forward --open to build.py")
    ap.add_argument("--open-html", action="store_true", help="Open generated HTML index pages after the batch finishes")
    ap.add_argument("--no-clean", action="store_true", help="Forward --no-clean to build.py")
    ap.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
    ap.add_argument(
        "--python-exe",
        default=sys.executable,
        help="Python executable used to invoke build.py (default: current interpreter)",
    )
    return ap.parse_args(argv)


def _split_csv_values(raw: str | list[str]) -> list[str]:
    sources = [raw] if isinstance(raw, str) else list(raw)
    items: list[str] = []
    for source in sources:
        for chunk in str(source).split(","):
            value = chunk.strip().lower()
            if value:
                items.append(value)
    return items


def resolve_languages(raw: str | list[str]) -> list[MatrixTarget]:
    values = _split_csv_values(raw)
    if values == ["all"]:
        values = list(DEFAULT_LANGUAGES)
    if not values:
        raise RuntimeError("No languages were provided. Use en, es, fr, ja, or all.")

    seen: set[str] = set()
    targets: list[MatrixTarget] = []
    for value in values:
        if value not in TARGETS:
            raise RuntimeError(f"Unsupported language '{value}'. Supported values: en, es, fr, ja.")
        if value in seen:
            continue
        seen.add(value)
        targets.append(TARGETS[value])
    return targets


def resolve_formats(raw: str | list[str]) -> list[str]:
    values = _split_csv_values(raw)
    if values == ["all"]:
        values = list(VALID_FORMATS)
    if not values:
        raise RuntimeError("No formats were provided. Use html, word, pdf, or all.")

    seen: set[str] = set()
    formats: list[str] = []
    for value in values:
        if value not in VALID_FORMATS:
            raise RuntimeError(f"Unsupported format '{value}'. Supported values: html, word, pdf.")
        if value in seen:
            continue
        seen.add(value)
        formats.append(value)
    return formats


def planned_build_actions(formats: list[str]) -> list[str]:
    if set(formats) == set(VALID_FORMATS):
        return ["all"]
    return list(formats)


def validate_open_options(*, formats: list[str], open_html: bool) -> None:
    if open_html and "html" not in formats:
        raise RuntimeError("--open-html requires html in --formats.")


def build_py_command(
    *,
    python_exe: str,
    action: str,
    model: str,
    target: MatrixTarget,
    source: str,
    pdf_mode: str | None,
    open_outputs: bool,
    no_clean: bool,
) -> list[str]:
    cmd = [
        python_exe,
        str(ROOT / "build.py"),
        action,
        "--config",
        target.config,
        "--model",
        model,
        "--region",
        target.region,
    ]
    if action in {"rst", "html", "word", "pdf", "all", "check"}:
        cmd += ["--source", source]
    if pdf_mode and action in {"pdf", "all"}:
        cmd += ["--pdf-mode", pdf_mode]
    if open_outputs:
        cmd.append("--open")
    if no_clean:
        cmd.append("--no-clean")
    return cmd


def build_plan(args: argparse.Namespace) -> list[PlannedCommand]:
    targets = resolve_languages(args.languages)
    formats = resolve_formats(args.formats)
    actions = planned_build_actions(formats)
    plan: list[PlannedCommand] = []

    for target in targets:
        if args.check_first:
            plan.append(
                PlannedCommand(
                    target=target,
                    action="check",
                    command=build_py_command(
                        python_exe=args.python_exe,
                        action="check",
                        model=args.model,
                        target=target,
                        source=args.source,
                        pdf_mode=args.pdf_mode,
                        open_outputs=args.open,
                        no_clean=args.no_clean,
                    ),
                )
            )

        keep_outputs = args.no_clean or args.check_first
        for index, action in enumerate(actions):
            plan.append(
                PlannedCommand(
                    target=target,
                    action=action,
                    command=build_py_command(
                        python_exe=args.python_exe,
                        action=action,
                        model=args.model,
                        target=target,
                        source=args.source,
                        pdf_mode=args.pdf_mode,
                        open_outputs=args.open,
                        no_clean=keep_outputs or index > 0,
                    ),
                )
            )
    return plan


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def output_root_for_target(model: str, target: MatrixTarget) -> Path:
    root = ROOT / "docs" / "_build" / model / target.region
    if target.include_lang_in_output_path:
        return root / target.language
    return root


def render_output_name(template: str, *, model: str, region: str, language: str) -> str:
    return (
        template.replace("{model_slug}", _slugify(model))
        .replace("{region_slug}", _slugify(region))
        .replace("{lang_slug}", _slugify(language))
    )


def expected_artifacts(model: str, target: MatrixTarget, formats: list[str]) -> list[Path]:
    root = output_root_for_target(model, target)
    artifacts: list[Path] = []
    if "html" in formats:
        artifacts.append(root / "html" / "index.html")
    if "word" in formats:
        artifacts.append(
            root
            / "word"
            / render_output_name(
                target.word_template,
                model=model,
                region=target.region,
                language=target.language,
            )
        )
    if "pdf" in formats:
        artifacts.append(
            root
            / "pdf"
            / render_output_name(
                target.pdf_template,
                model=model,
                region=target.region,
                language=target.language,
            )
        )
    return artifacts


def format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def run_plan(plan: list[PlannedCommand], *, dry_run: bool) -> None:
    for item in plan:
        print()
        print(f"==> {item.label}")
        print(f"    {format_command(item.command)}")
        if dry_run:
            continue
        subprocess.run(item.command, cwd=str(ROOT), check=True)


def open_path(path: Path, *, dry_run: bool) -> None:
    print(f"[open] {path}")
    if dry_run:
        return
    if sys.platform.startswith("win"):
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def open_generated_html(model: str, *, targets: list[MatrixTarget], dry_run: bool) -> None:
    html_indexes = [path for target in targets for path in expected_artifacts(model, target, ["html"])]

    print()
    print("Open HTML:")
    for html_index in html_indexes:
        if dry_run or html_index.exists():
            open_path(html_index, dry_run=dry_run)


def print_artifact_summary(model: str, *, targets: list[MatrixTarget], formats: list[str], dry_run: bool) -> None:
    heading = "Expected outputs" if dry_run else "Artifacts"
    print()
    print(f"{heading}:")
    for target in targets:
        for artifact in expected_artifacts(model, target, formats):
            if dry_run or artifact.exists():
                print(f" - {artifact}")


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        targets = resolve_languages(args.languages)
        formats = resolve_formats(args.formats)
        validate_open_options(formats=formats, open_html=args.open_html)
        plan = build_plan(args)
        run_plan(plan, dry_run=args.dry_run)
        print_artifact_summary(args.model, targets=targets, formats=formats, dry_run=args.dry_run)
        if args.open_html:
            open_generated_html(args.model, targets=targets, dry_run=args.dry_run)
        return 0
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    except RuntimeError as exc:
        print(f"[build_us_jp_manuals] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
