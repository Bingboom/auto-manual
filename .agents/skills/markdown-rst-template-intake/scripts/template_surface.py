from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]

FAMILY_INFO = {
    "us-merged": {
        "config": "config.us.yaml",
        "region": "US",
        "manifest": "docs/manifests/manual_us.yaml",
        "template_dirs": [
            "docs/templates/page_us-en",
            "docs/templates/page_us-fr",
            "docs/templates/page_us-es",
        ],
        "recipe_dirs": [
            "docs/templates/recipes/us-en",
            "docs/templates/recipes/us-fr",
            "docs/templates/recipes/us-es",
        ],
        "structure_owner": "docs/templates/page_us-en",
        "notes": [
            "Use page_us-en as the structure owner for shared US changes.",
            "Keep page_us-fr and page_us-es aligned when headings, order, includes, gates, or placeholder layout change.",
        ],
    },
    "us-en": {
        "config": "config.us-en.yaml",
        "region": "US",
        "manifest": "docs/manifests/manual_us-single-en.yaml",
        "template_dirs": ["docs/templates/page_us-en"],
        "recipe_dirs": ["docs/templates/recipes/us-en"],
        "structure_owner": "docs/templates/page_us-en",
        "notes": [],
    },
    "eu-en": {
        "config": "config.eu-en.yaml",
        "region": "US",
        "manifest": "docs/manifests/manual_eu-en.yaml",
        "template_dirs": ["docs/templates/page_eu-en"],
        "recipe_dirs": ["docs/templates/recipes/eu-en"],
        "structure_owner": "docs/templates/page_eu-en",
        "notes": [
            "This family is intended for the HomePower 2000 Plus single-language English workflow.",
            "The current live phase2 rows resolve through JE-2000E / US data for JHP-2000A.",
            "Keep spec and symbols pages data-driven under data/phase2 for this family.",
        ],
    },
    "us-fr": {
        "config": "config.us-fr.yaml",
        "region": "US",
        "manifest": "docs/manifests/manual_us-single-fr.yaml",
        "template_dirs": ["docs/templates/page_us-fr"],
        "recipe_dirs": ["docs/templates/recipes/us-fr"],
        "structure_owner": "docs/templates/page_us-fr",
        "notes": [
            "For 03_product_overview and 12_app_setup, the shared placeholder mapping currently lives under docs/templates/recipes/us-en.",
        ],
    },
    "us-es": {
        "config": "config.us-es.yaml",
        "region": "US",
        "manifest": "docs/manifests/manual_us-single-es.yaml",
        "template_dirs": ["docs/templates/page_us-es"],
        "recipe_dirs": ["docs/templates/recipes/us-es"],
        "structure_owner": "docs/templates/page_us-es",
        "notes": [
            "For 03_product_overview and 12_app_setup, the shared placeholder mapping currently lives under docs/templates/recipes/us-en.",
        ],
    },
    "jp": {
        "config": "config.ja.yaml",
        "region": "JP",
        "manifest": "docs/manifests/manual_jp.yaml",
        "template_dirs": ["docs/templates/page_jp"],
        "recipe_dirs": ["docs/templates/recipes/jp"],
        "structure_owner": "docs/templates/page_jp",
        "notes": [],
    },
    "zh": {
        "config": "config.zh.yaml",
        "region": "CN",
        "manifest": "docs/manifests/manual_zh.yaml",
        "template_dirs": ["docs/templates/page_zh"],
        "recipe_dirs": ["docs/templates/recipes/zh"],
        "structure_owner": "docs/templates/page_zh",
        "notes": [],
    },
}

RECIPE_BACKED_PAGES = {
    "03_product_overview",
    "05_operation_guide",
    "12_app_setup",
}

CSV_BACKED_PAGES = {
    "spec": [
        "data/phase2/Spec_Master.csv",
        "data/phase2/Spec_Footnotes.csv",
        "data/phase2/Spec_Notes.csv",
    ],
    "symbols": ["data/phase2/symbols_blocks.csv"],
}

ALIASES = {
    "cover": "00_preface",
    "introduction": "00_preface",
    "preface": "00_preface",
    "safety": "safety",
    "symbols": "symbols",
    "meaning_of_symbols": "01_meaning_of_symbols",
    "whats_in_the_box": "02_whats_in_the_box",
    "in_the_box": "02_whats_in_the_box",
    "product_overview": "03_product_overview",
    "lcd": "04_lcd_display",
    "lcd_display": "04_lcd_display",
    "operation_guide": "05_operation_guide",
    "ups": "06_ups_mode",
    "ups_mode": "06_ups_mode",
    "charging": "charging",
    "charging_methods": "08_charging_methods",
    "storage": "09_storage_and_maintenance",
    "storage_and_maintenance": "09_storage_and_maintenance",
    "maintenance": "09_storage_and_maintenance",
    "troubleshooting": "10_troubleshooting",
    "spec": "spec",
    "specs": "spec",
    "warranty": "11_warranty",
    "app": "12_app_setup",
    "app_setup": "12_app_setup",
}


def normalize_page(raw_value: str) -> str:
    cleaned = raw_value.strip().lower()
    cleaned = cleaned.replace(".rst", "").replace(".yaml", "")
    cleaned = cleaned.replace("_placeholder", "")
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = cleaned.strip("_")
    return ALIASES.get(cleaned, cleaned)


def file_for_dir(template_dir: str, family: str, page_key: str) -> str | None:
    root = Path(template_dir)

    if page_key == "00_preface":
        filename = "cover_jp.rst" if family == "jp" else "00_preface.rst"
    elif page_key == "safety":
        if family == "jp":
            filename = "safety_ja.rst"
        elif family == "zh":
            filename = "safety_zh.rst"
        elif family in {"us-en", "eu-en"}:
            filename = "safety_en.rst"
        elif family == "us-fr":
            filename = "safety_fr.rst"
        elif family == "us-es":
            filename = "safety_es.rst"
        else:
            return None
    elif page_key in RECIPE_BACKED_PAGES or page_key == "04_lcd_display":
        suffix = "_placeholder.rst" if page_key != "04_lcd_display" else "_placeholder.rst"
        filename = f"{page_key}{suffix}"
    elif page_key in {
        "01_meaning_of_symbols",
        "02_whats_in_the_box",
        "06_ups_mode",
        "charging",
        "08_charging_methods",
        "09_storage_and_maintenance",
        "10_troubleshooting",
        "11_warranty",
    }:
        filename = f"{page_key}.rst"
    else:
        return None

    return str((root / filename).as_posix())


def recipe_paths(family: str, page_key: str) -> list[str]:
    if page_key not in RECIPE_BACKED_PAGES:
        return []

    if family == "us-merged":
        if page_key in {"03_product_overview", "12_app_setup"}:
            return [f"docs/templates/recipes/us-en/{page_key}.yaml"]
        return [
            "docs/templates/recipes/us-en/05_operation_guide.yaml",
            "docs/templates/recipes/us-fr/05_operation_guide.yaml",
            "docs/templates/recipes/us-es/05_operation_guide.yaml",
        ]

    if family in {"us-fr", "us-es"} and page_key in {"03_product_overview", "12_app_setup"}:
        return [f"docs/templates/recipes/us-en/{page_key}.yaml"]

    if family in {"us-fr", "us-es"} and page_key == "05_operation_guide":
        return [f"docs/templates/recipes/{family}/05_operation_guide.yaml"]

    recipe_family = "jp" if family == "jp" else family
    return [f"docs/templates/recipes/{recipe_family}/{page_key}.yaml"]


def preview_page_stem(page_key: str, family: str) -> str | None:
    if page_key in RECIPE_BACKED_PAGES:
        return f"{page_key}_placeholder"
    if page_key == "04_lcd_display":
        return "04_lcd_display_placeholder"
    if page_key == "00_preface":
        return "cover_jp" if family == "jp" else "00_preface"
    if page_key == "safety":
        if family == "jp":
            return "safety_ja"
        if family == "zh":
            return "safety_zh"
        if family in {"us-en", "eu-en"}:
            return "safety_en"
        if family == "us-fr":
            return "safety_fr"
        if family == "us-es":
            return "safety_es"
    if page_key in {
        "01_meaning_of_symbols",
        "02_whats_in_the_box",
        "06_ups_mode",
        "charging",
        "08_charging_methods",
        "09_storage_and_maintenance",
        "10_troubleshooting",
        "11_warranty",
    }:
        return page_key
    return None


def existing_paths(paths: list[str]) -> list[str]:
    result = []
    for path in paths:
        if (REPO_ROOT / path).exists():
            result.append(path)
    return result


def family_lang_members(family: str) -> list[str]:
    if family == "us-merged":
        return ["us-en", "us-fr", "us-es"]
    return [family]


def build_page_surface(family: str, page_key: str) -> dict[str, object]:
    if page_key == "spec":
        return {
            "page_key": page_key,
            "kind": "csv_generated",
            "sources": CSV_BACKED_PAGES["spec"],
            "notes": [
                "Do not hand-author spec RST.",
                "Edit Spec_Master.csv, Spec_Footnotes.csv, or Spec_Notes.csv instead.",
            ],
        }

    lookup_key = page_key
    if page_key == "symbols" and family != "jp":
        return {
            "page_key": page_key,
            "kind": "csv_generated",
            "sources": CSV_BACKED_PAGES["symbols"],
            "notes": [
                "Do not hand-author symbols RST for this family.",
                "Edit symbols_blocks.csv instead.",
            ],
        }
    if page_key == "symbols" and family == "jp":
        lookup_key = "01_meaning_of_symbols"

    member_families = family_lang_members(family)
    template_files: list[str] = []
    for member in member_families:
        for template_dir in FAMILY_INFO[member]["template_dirs"]:
            candidate = file_for_dir(template_dir, member, lookup_key)
            if candidate:
                template_files.append(candidate)
    template_files = existing_paths(template_files)

    notes = []
    kind = "direct_template"
    if lookup_key in RECIPE_BACKED_PAGES:
        kind = "recipe_backed_placeholder"
        notes.append("Keep placeholder tokens intentional and sync recipe ownership if mappings change.")
        if family == "eu-en":
            notes.append(
                "If the rendered copy must stay family-specific, keep contract-required placeholders in an RST comment and write the visible body literally."
            )
    elif lookup_key == "04_lcd_display":
        notes.append("This page has placeholder text but no dedicated recipe file in the current repo.")
    elif lookup_key == "01_meaning_of_symbols" and family == "jp":
        notes.append("JP keeps detailed symbols content in this template page instead of data/phase2/symbols_blocks.csv.")

    surface = {
        "page_key": page_key,
        "kind": kind,
        "template_files": template_files,
        "recipe_files": existing_paths(recipe_paths(family, lookup_key)),
        "contract_files": existing_paths([f"docs/templates/contracts/{lookup_key}.yaml"])
        if lookup_key in RECIPE_BACKED_PAGES
        else [],
        "notes": notes,
    }
    return surface


def build_summary(family: str, model: str | None, page_key: str | None) -> dict[str, object]:
    info = FAMILY_INFO[family]
    model_value = model or "<MODEL>"
    region = info["region"]
    summary: dict[str, object] = {
        "family": family,
        "config": info["config"],
        "region": region,
        "manifest": info["manifest"],
        "template_dirs": info["template_dirs"],
        "recipe_dirs": info["recipe_dirs"],
        "structure_owner": info["structure_owner"],
        "check_command": f"python build.py check --config {info['config']} --model {model_value} --region {region}",
        "notes": list(info["notes"]),
    }

    if page_key:
        surface = build_page_surface(family, page_key)
        summary["page"] = surface
        preview_stem = preview_page_stem(page_key, family)
        if preview_stem:
            summary["preview_command"] = (
                f"python build.py preview --config {info['config']} --model {model_value} "
                f"--region {region} --page {preview_stem}"
            )
    else:
        summary["page_groups"] = {
            "recipe_backed": sorted(RECIPE_BACKED_PAGES),
            "template_only": [
                "00_preface",
                "safety",
                "01_meaning_of_symbols",
                "02_whats_in_the_box",
                "04_lcd_display",
                "06_ups_mode",
                "charging",
                "08_charging_methods",
                "09_storage_and_maintenance",
                "10_troubleshooting",
                "11_warranty",
            ],
            "csv_generated": ["spec", "symbols"],
        }
    return summary


def render_text(summary: dict[str, object]) -> str:
    lines = [
        f"Family: {summary['family']}",
        f"Config: {summary['config']}",
        f"Region: {summary['region']}",
        f"Manifest: {summary['manifest']}",
        f"Structure owner: {summary['structure_owner']}",
    ]

    if "notes" in summary and summary["notes"]:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in summary["notes"])

    if "page" in summary:
        page = summary["page"]
        lines.append(f"Page: {page['page_key']}")
        lines.append(f"Kind: {page['kind']}")
        if page.get("template_files"):
            lines.append("Template files:")
            lines.extend(f"- {path}" for path in page["template_files"])
        if page.get("recipe_files"):
            lines.append("Recipe files:")
            lines.extend(f"- {path}" for path in page["recipe_files"])
        if page.get("contract_files"):
            lines.append("Contract files:")
            lines.extend(f"- {path}" for path in page["contract_files"])
        if page.get("sources"):
            lines.append("Source files:")
            lines.extend(f"- {path}" for path in page["sources"])
        if page.get("notes"):
            lines.append("Page notes:")
            lines.extend(f"- {note}" for note in page["notes"])
        if "preview_command" in summary:
            lines.append(f"Preview command: {summary['preview_command']}")
    else:
        page_groups = summary["page_groups"]
        lines.append("Recipe-backed pages:")
        lines.extend(f"- {page}" for page in page_groups["recipe_backed"])
        lines.append("Template-only pages:")
        lines.extend(f"- {page}" for page in page_groups["template_only"])
        lines.append("CSV-generated pages:")
        lines.extend(f"- {page}" for page in page_groups["csv_generated"])

    lines.append(f"Check command: {summary['check_command']}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show repo-specific template, recipe, and validation surfaces for Markdown manual intake."
    )
    parser.add_argument(
        "--family",
        required=True,
        choices=sorted(FAMILY_INFO.keys()),
        help="Target template family.",
    )
    parser.add_argument(
        "--page",
        help="Optional page or section key such as 05_operation_guide, product overview, safety, or spec.",
    )
    parser.add_argument(
        "--model",
        help="Optional model used only to render example validation commands.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    page_key = normalize_page(args.page) if args.page else None
    summary = build_summary(args.family, args.model, page_key)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=True))
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
