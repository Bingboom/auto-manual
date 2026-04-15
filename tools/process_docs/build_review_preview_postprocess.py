from __future__ import annotations

import os
import re
from collections.abc import Callable
from html import escape
from pathlib import Path

from tools.process_docs.build_review_preview_render import display_text
from tools.process_docs.build_review_preview_targets import WorkspaceTarget


_MANUAL_SWITCHER_BLOCK_RE = re.compile(
    r"<!-- HB_MANUAL_SWITCHER_START -->.*?<!-- HB_MANUAL_SWITCHER_END -->\s*",
    re.DOTALL,
)


def rewrite_manual_switcher_links(
    text: str,
    *,
    current_target: WorkspaceTarget,
    current_relative_path: Path,
    all_targets: list[WorkspaceTarget],
    html_root_for_target_func: Callable[[str, WorkspaceTarget], Path],
) -> str:
    match = _MANUAL_SWITCHER_BLOCK_RE.search(text)
    if match is None:
        return text

    current_source_html = html_root_for_target_func(current_target.model, current_target) / current_relative_path
    source_start = current_source_html.parent
    preview_current = (
        Path("manual")
        / current_target.family
        / current_target.model
        / current_target.language
        / current_relative_path
    )
    preview_start = preview_current.parent
    rewritten = match.group(0)

    for target in all_targets:
        if target == current_target:
            continue

        target_source_root = html_root_for_target_func(target.model, target)
        target_page = current_relative_path if (target_source_root / current_relative_path).exists() else Path("index.html")
        source_target = target_source_root / target_page
        preview_target = Path("manual") / target.family / target.model / target.language / target_page

        source_href = Path(os.path.relpath(source_target, start=source_start)).as_posix()
        preview_href = Path(os.path.relpath(preview_target, start=preview_start)).as_posix()
        rewritten = rewritten.replace(f'href="{escape(source_href)}"', f'href="{escape(preview_href)}"')

    return text[: match.start()] + rewritten + text[match.end() :]


def rewrite_manual_tree_for_preview(
    manual_dir: Path,
    *,
    current_target: WorkspaceTarget,
    all_targets: list[WorkspaceTarget],
    rewrite_manual_switcher_links_func: Callable[..., str],
) -> None:
    for html_file in manual_dir.rglob("*.html"):
        try:
            text = html_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        html_file.write_text(
            rewrite_manual_switcher_links_func(
                text,
                current_target=current_target,
                current_relative_path=html_file.relative_to(manual_dir),
                all_targets=all_targets,
            ),
            encoding="utf-8",
        )


def assert_preview_output_contract(
    output_dir: Path,
    workspace: dict[str, object],
    *,
    require_word: bool,
    required_preview_files: tuple[str, ...],
    required_download_csvs: tuple[str, ...],
    required_change_report_files: tuple[str, ...],
) -> None:
    missing: list[str] = []

    for relative_path in required_preview_files:
        if not (output_dir / relative_path).exists():
            missing.append(relative_path)

    defaults = workspace.get("defaults", {})
    if not isinstance(defaults, dict):
        missing.append("generated/workspace.json#defaults")
    else:
        for key in ("manual_url", "change_url"):
            target = defaults.get(key)
            if not isinstance(target, str) or not (output_dir / target).exists():
                missing.append(f"generated/workspace.json#defaults.{key}")

    families = workspace.get("families", [])
    if not isinstance(families, list) or not families:
        missing.append("generated/workspace.json#families")
    else:
        for family_entry in families:
            if not isinstance(family_entry, dict):
                missing.append("generated/workspace.json#families[]")
                continue
            family = display_text(family_entry.get("family"), "")
            if not family:
                missing.append("generated/workspace.json#families[].family")
                continue
            change_index_url = family_entry.get("change_index_url")
            if not isinstance(change_index_url, str) or not (output_dir / change_index_url).exists():
                missing.append(f"changes/{family}/index.html")

            models = family_entry.get("models", [])
            if not isinstance(models, list) or not models:
                missing.append(f"generated/workspace.json#families[{family}]#models")
                continue
            for model_entry in models:
                if not isinstance(model_entry, dict):
                    missing.append(f"generated/workspace.json#families[{family}]#models[]")
                    continue
                model_name = display_text(model_entry.get("model"), "")
                if not model_name:
                    missing.append(f"generated/workspace.json#families[{family}]#models[].model")
                    continue
                change_index_url = model_entry.get("change_index_url")
                if not isinstance(change_index_url, str) or not (output_dir / change_index_url).exists():
                    missing.append(f"changes/{family}/{model_name}/index.html")
                change_workbook = model_entry.get("change_workbook_url")
                if not isinstance(change_workbook, str) or not (output_dir / change_workbook).exists():
                    missing.append(f"downloads/{family}/{model_name}/change-report.xlsx")
                csv_urls = model_entry.get("csv_urls")
                if not isinstance(csv_urls, dict):
                    missing.extend(f"downloads/{family}/{model_name}/{name}" for name in required_download_csvs)
                else:
                    for file_name in required_download_csvs:
                        target = csv_urls.get(file_name)
                        if not isinstance(target, str) or not (output_dir / target).exists():
                            missing.append(f"downloads/{family}/{model_name}/{file_name}")
                report_files = model_entry.get("report_files")
                if not isinstance(report_files, dict):
                    missing.extend(f"changes/{family}/{model_name}/{name}" for name in required_change_report_files)
                else:
                    for file_name in required_change_report_files:
                        target = report_files.get(file_name)
                        if not isinstance(target, str) or not (output_dir / target).exists():
                            missing.append(f"changes/{family}/{model_name}/{file_name}")
                languages = model_entry.get("languages", [])
                if not isinstance(languages, list) or not languages:
                    missing.append(f"generated/workspace.json#families[{family}]#models[{model_name}]#languages")
                    continue
                for language_entry in languages:
                    if not isinstance(language_entry, dict):
                        missing.append(f"generated/workspace.json#families[{family}]#languages[]")
                        continue
                    manual_url = language_entry.get("manual_url")
                    if not isinstance(manual_url, str) or not (output_dir / manual_url).exists():
                        missing.append(
                            f"manual/{family}/{model_name}/{display_text(language_entry.get('lang'), '').lower()}/index.html"
                        )
                    word_url = language_entry.get("word_url")
                    if require_word and (not isinstance(word_url, str) or not (output_dir / word_url).exists()):
                        missing.append(
                            f"downloads/{family}/{model_name}/{display_text(language_entry.get('lang'), '').lower()}/review-manual.docx"
                        )

    if missing:
        raise RuntimeError("Review preview output contract is incomplete: " + ", ".join(sorted(set(missing))))
