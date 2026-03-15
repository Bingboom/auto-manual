#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.config_pages import (
    ConfigPage,
    CoverPdfPage,
    CsvPage,
    PdfInsertPage,
    RstIncludePage,
    parse_config_pages_or_raise,
)
from tools.page_contracts import contract_applies_to, find_contract_for_source, load_page_contracts, required_assets_for_lang  # noqa: E402
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.utils.targets import (
    format_tokenized,
    resolve_build_model as resolve_target_model,
    resolve_build_region as resolve_target_region,
)
from tools.word_bundle_common import (  # noqa: E402
    apply_rst_substitutions,
    derive_word_title,
    ensure_csv_page_rsts,
    fill_product_name_from_spec_master,
    load_rst_substitutions,
    load_word_context,
    pick_vars_map,
    resolve_config_path,
    resolve_reference_doc,
    resolve_spec_master_substitutions,
)

paths = get_paths()

_RST_ASSET_DIRECTIVE_RE = re.compile(
    r"^(\s*(?:[-*]\s+)?(?:-\s+)?\.\.\s+(?:image|figure)::\s+)(\S+)(\s*)$",
    re.MULTILINE,
)
_HTML_SRC_RE = re.compile(r'(\bsrc=")([^"]+)(")', re.IGNORECASE)
_INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$")
_CONTRACT_TOKEN_RE = re.compile(r"\{([a-z_]+)\}")


@dataclass(frozen=True)
class PlannedPage:
    page: ConfigPage
    lang: str | None
    file_name: str


@dataclass(frozen=True)
class MaterializedBundle:
    bundle_dir: Path
    page_dir: Path
    index_path: Path
    conf_path: Path
    conf_base_path: Path
    wrapper_index_path: Path
    page_paths: tuple[Path, ...]
    title: str
    reference_doc: Path | None
    model: str | None
    region: str | None


def _select_planned_pages(planned_pages: list[PlannedPage], page_selector: str | None) -> list[PlannedPage]:
    if not (page_selector or "").strip():
        return planned_pages

    selector = page_selector.strip()
    csv_matches = [planned for planned in planned_pages if isinstance(planned.page, CsvPage) and planned.page.page == selector]
    if csv_matches:
        return csv_matches

    stem_matches = [planned for planned in planned_pages if Path(planned.file_name).stem == selector]
    if not stem_matches:
        raise RuntimeError(f"Page selector did not match any materialized page: {selector}")
    if len(stem_matches) > 1:
        raise RuntimeError(f"Page selector matched multiple materialized pages: {selector}")
    return stem_matches


def load_config(cfg_path: Path) -> dict:
    if not cfg_path.exists():
        raise RuntimeError(f"Config not found: {cfg_path}")

    import yaml  # requires PyYAML

    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def latex_cover_block(file_name: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{empty}}}}]{{{file_name}}}",
        "   \\clearpage",
        "   \\pagenumbering{arabic}",
        "   \\setcounter{page}{1}",
        "",
    ]


def latex_apply_lang(lang: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\HBApplyLang{{{lang}}}",
        "",
    ]


def latex_overview_block(file_name: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{normal}}}}]{{{file_name}}}",
        "",
    ]


def _format_tokenized(
    text: str,
    model: str | None,
    region: str | None,
) -> str:
    return format_tokenized(text, None, model, region)


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    return resolve_target_model(cfg, arg_model)


def resolve_build_region(cfg: dict, arg_region: str | None) -> str | None:
    return resolve_target_region(cfg, arg_region)


def _build_langs(cfg: dict) -> list[str]:
    langs = cfg.get("build", {}).get("languages", ["en"])
    return list(langs)


def _bundle_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def bundle_dir_for_target(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> Path:
    return (
        docs_dir
        / "_build"
        / _bundle_component(model, "_shared")
        / _bundle_component(region, "_default")
        / "rst"
    )


def _legacy_bundle_dir_for_target(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> Path:
    return docs_dir / _bundle_component(model, "_shared") / _bundle_component(region, "_default")


def _legacy_generated_dir_for_target(
    *,
    docs_dir: Path,
    model: str | None,
) -> Path:
    return docs_dir / "generated" / _bundle_component(model, "_shared")


def cleanup_legacy_rst_artifacts(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> None:
    legacy_bundle_dir = _legacy_bundle_dir_for_target(
        docs_dir=docs_dir,
        model=model,
        region=region,
    )
    legacy_generated_dir = _legacy_generated_dir_for_target(
        docs_dir=docs_dir,
        model=model,
    )

    if legacy_bundle_dir.exists():
        shutil.rmtree(legacy_bundle_dir)
        parent = legacy_bundle_dir.parent
        if parent != docs_dir and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

    if legacy_generated_dir.exists():
        shutil.rmtree(legacy_generated_dir)
        parent = legacy_generated_dir.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()


def _resolve_spec_master_csv_path(
    cfg: dict,
    *,
    repo_root: Path,
    model: str | None,
    region: str | None,
) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("spec_master_csv")
    if isinstance(raw, str) and raw.strip():
        return resolve_config_path(repo_root, raw.strip(), model, region)
    return repo_root / "data" / "phase1" / "Spec_Master.csv"


def _resolve_csv_rst_path(
    *,
    source_root: Path,
    page: CsvPage,
    lang: str,
    model: str | None,
    region: str | None,
) -> Path:
    if page.include_dir is None:
        rel = f"{page.page}_{lang}.rst"
    else:
        rel = str(Path(_format_tokenized(page.include_dir, model, region)) / f"{page.page}_{lang}.rst")
    return source_root / rel


def _base_file_name_for_plan(
    page: ConfigPage,
    *,
    lang: str | None,
    model: str | None,
    region: str | None,
) -> str:
    if isinstance(page, CoverPdfPage):
        return "cover.rst"
    if isinstance(page, CsvPage):
        assert lang is not None
        return f"{page.page}_{lang}.rst"
    if isinstance(page, PdfInsertPage):
        assert lang is not None
        pdf_path = _format_tokenized(page.file_map[lang], model, region)
        stem = Path(pdf_path).stem or "pdf_insert"
        return f"{stem}_{lang}.rst"
    if isinstance(page, RstIncludePage):
        rst_path = _format_tokenized(page.file, model, region)
        name = Path(rst_path).name
        return name if name.lower().endswith(".rst") else f"{name}.rst"
    raise RuntimeError(f"Unsupported page type: {type(page).__name__}")


def _ensure_unique_name(file_name: str, seen: set[str], ordinal: int) -> str:
    if file_name not in seen:
        seen.add(file_name)
        return file_name

    prefixed = f"p{ordinal:02d}_{file_name}"
    if prefixed not in seen:
        seen.add(prefixed)
        return prefixed

    seq = 2
    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    while True:
        candidate = f"p{ordinal:02d}_{stem}_{seq}{suffix}"
        if candidate not in seen:
            seen.add(candidate)
            return candidate
        seq += 1


def plan_materialized_pages(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
) -> list[PlannedPage]:
    langs = _build_langs(cfg)
    pages = parse_config_pages_or_raise(
        cfg.get("pages"),
        default_languages=langs,
        error_prefix="config.pages",
    )

    planned: list[PlannedPage] = []
    seen_names: set[str] = set()

    for ordinal, page in enumerate(pages, start=1):
        if isinstance(page, CoverPdfPage):
            base_name = _base_file_name_for_plan(page, lang=None, model=model, region=region)
            planned.append(
                PlannedPage(
                    page=page,
                    lang=None,
                    file_name=_ensure_unique_name(base_name, seen_names, ordinal),
                )
            )
            continue

        if isinstance(page, PdfInsertPage):
            page_langs = list(page.langs) or langs
            for lang in page_langs:
                if lang not in page.file_map:
                    raise RuntimeError(f"pdf_insert.file_map missing lang '{lang}'")
                base_name = _base_file_name_for_plan(page, lang=lang, model=model, region=region)
                planned.append(
                    PlannedPage(
                        page=page,
                        lang=lang,
                        file_name=_ensure_unique_name(base_name, seen_names, ordinal),
                    )
                )
            continue

        if isinstance(page, CsvPage):
            page_langs = list(page.langs) or langs
            if page.include_dir:
                _format_tokenized(page.include_dir, model, region)
            for lang in page_langs:
                base_name = _base_file_name_for_plan(page, lang=lang, model=model, region=region)
                planned.append(
                    PlannedPage(
                        page=page,
                        lang=lang,
                        file_name=_ensure_unique_name(base_name, seen_names, ordinal),
                    )
                )
            continue

        if isinstance(page, RstIncludePage):
            base_name = _base_file_name_for_plan(page, lang=page.lang, model=model, region=region)
            planned.append(
                PlannedPage(
                    page=page,
                    lang=page.lang,
                    file_name=_ensure_unique_name(base_name, seen_names, ordinal),
                )
            )
            continue

        raise RuntimeError(f"Unsupported page type: {type(page).__name__}")

    return planned


def build_index_from_pages(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
) -> str:
    lines: list[str] = []
    for planned in plan_materialized_pages(cfg, model=model, region=region):
        lines.extend([f".. include:: page/{planned.file_name}", ""])
    return "\n".join(lines) + "\n"


def build_wrapper_index_text(
    *,
    docs_dir: Path,
    bundle_dir: Path,
) -> str:
    bundle_rel = bundle_dir.relative_to(docs_dir).as_posix()
    return "\n".join(
        [
            ".. Auto-generated by tools/gen_index_bundle.py. Do not edit directly.",
            "",
            f".. include:: {bundle_rel}/index",
            "",
        ]
    )


def read_included_page_paths(index_path: Path) -> list[Path]:
    out: list[Path] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        match = _INCLUDE_RE.match(line)
        if not match:
            continue
        out.append((index_path.parent / match.group(1)).resolve())
    return out


def _is_external_path(value: str) -> bool:
    token = value.strip()
    if not token:
        return True
    lowered = token.lower()
    return lowered.startswith(("http://", "https://", "data:", "file://", "mailto:", "#")) or Path(token).is_absolute()


def _resolve_rst_asset_path(
    raw_value: str,
    *,
    source_path: Path,
    docs_dir: Path,
    repo_root: Path,
) -> Path | None:
    token = raw_value.strip()
    if not token or _is_external_path(token):
        return None

    raw_path = Path(token)
    probe_paths = [
        source_path.parent / raw_path,
        docs_dir / raw_path,
        repo_root / raw_path,
    ]

    for probe in probe_paths:
        if probe.exists() and probe.is_file():
            return probe.resolve()
    return None


def _bundle_asset_target_path(
    resolved: Path,
    *,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> Path:
    resolved_path = resolved.resolve(strict=False)
    docs_static_dir = (docs_dir / "_static").resolve(strict=False)
    docs_root = docs_dir.resolve(strict=False)
    repo_root_resolved = repo_root.resolve(strict=False)

    try:
        rel = resolved_path.relative_to(docs_static_dir)
        return bundle_dir / "_static" / rel
    except ValueError:
        pass

    try:
        rel = resolved_path.relative_to(docs_root)
        return bundle_dir / "_assets" / rel
    except ValueError:
        pass

    try:
        rel = resolved_path.relative_to(repo_root_resolved)
        return bundle_dir / "_repo_assets" / rel
    except ValueError:
        pass

    return bundle_dir / "_external_assets" / resolved_path.name


def _stage_bundle_asset(
    resolved: Path,
    *,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> Path:
    target = _bundle_asset_target_path(
        resolved,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(resolved, target)
    return target


def _rewrite_single_asset_path(
    raw_value: str,
    *,
    source_path: Path,
    target_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> str:
    token = raw_value.strip()
    if not token or _is_external_path(token):
        return raw_value

    resolved = _resolve_rst_asset_path(
        raw_value,
        source_path=source_path,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    if resolved is None:
        return raw_value

    staged = _stage_bundle_asset(
        resolved,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    return Path(os.path.relpath(staged, start=bundle_dir)).as_posix()


def rewrite_rst_asset_paths(
    text: str,
    *,
    source_path: Path,
    target_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> str:
    def replace_directive(match: re.Match[str]) -> str:
        prefix, raw_value, suffix = match.groups()
        rewritten = _rewrite_single_asset_path(
            raw_value,
            source_path=source_path,
            target_path=target_path,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
        )
        return f"{prefix}{rewritten}{suffix}"

    def replace_html_src(match: re.Match[str]) -> str:
        prefix, raw_value, suffix = match.groups()
        rewritten = _rewrite_single_asset_path(
            raw_value,
            source_path=source_path,
            target_path=target_path,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
        )
        return f"{prefix}{rewritten}{suffix}"

    out = _RST_ASSET_DIRECTIVE_RE.sub(replace_directive, text)
    return _HTML_SRC_RE.sub(replace_html_src, out)


def _prepend_latex_lang(text: str, lang: str | None) -> str:
    body = text if text.endswith("\n") else f"{text}\n"
    if not (lang or "").strip():
        return body
    return "\n".join(latex_apply_lang(lang)) + "\n" + body


def _render_cover_page_rst(title: str, file_name: str) -> str:
    title_html = html.escape(title)
    return "\n".join(
        [
            ".. only:: html",
            "",
            "   .. raw:: html",
            "",
            f"      <section class=\"manual-cover\"><div class=\"cover-title\">{title_html}</div></section>",
            "",
            ".. only:: latex",
            "",
            *("   " + line if line else "" for line in latex_cover_block(file_name)),
            "",
        ]
    )


def _render_pdf_insert_page_rst(file_name: str, lang: str) -> str:
    return "\n".join(
        [
            ".. only:: html",
            "",
            "   .. raw:: html",
            "",
            "      <div class=\"manual-pdf-insert\"></div>",
            "",
            ".. only:: latex",
            "",
            *("   " + line if line else "" for line in (latex_apply_lang(lang) + latex_overview_block(file_name))),
            "",
        ]
    )


def _copytree_replace(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _render_contract_asset_path(
    raw_value: str,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> str:
    values = {
        "model": (model or "").strip(),
        "region": (region or "").strip(),
        "lang": (lang or "").strip(),
    }
    tokens = {match.group(1) for match in _CONTRACT_TOKEN_RE.finditer(raw_value)}
    unknown = sorted(token for token in tokens if token not in values)
    if unknown:
        raise RuntimeError(f"Unsupported contract asset token(s): {', '.join(unknown)}")
    missing = sorted(token for token in tokens if not values[token])
    if missing:
        raise RuntimeError(f"Contract asset path requires value(s) for: {', '.join(missing)}")
    return raw_value.format(**values)


def _resolve_contract_asset_path(
    raw_value: str,
    *,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> Path:
    rendered = _render_contract_asset_path(
        raw_value,
        model=model,
        region=region,
        lang=lang,
    )
    candidate = Path(rendered)
    if candidate.is_absolute():
        return candidate

    docs_candidate = docs_dir / candidate
    if docs_candidate.exists():
        return docs_candidate
    return repo_root / candidate


def _preflight_contract_assets(
    *,
    cfg: dict,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    langs: list[str],
    planned_pages: list[PlannedPage],
) -> None:
    contracts = load_page_contracts(docs_dir / "templates" / "contracts")
    if not contracts:
        return

    seen_sources: set[tuple[str, str | None]] = set()
    for planned in planned_pages:
        page = planned.page
        if not isinstance(page, RstIncludePage):
            continue
        source_key = (page.file, planned.lang or page.lang)
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        source_path = resolve_config_path(docs_dir, page.file, model, region)
        try:
            source_rel = source_path.relative_to(docs_dir).as_posix()
        except ValueError:
            source_rel = source_path.as_posix()
        contract = find_contract_for_source(source_rel, contracts)
        if contract is None:
            continue
        page_langs = [planned.lang or page.lang] if (planned.lang or page.lang) else langs
        for lang in page_langs:
            if not contract_applies_to(contract, lang=lang, model=model, region=region):
                continue
            for asset_path in required_assets_for_lang(contract, lang):
                resolved = _resolve_contract_asset_path(
                    asset_path,
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                    model=model,
                    region=region,
                    lang=lang,
                )
                if resolved.exists():
                    continue
                raise RuntimeError(
                    f"Page contract '{contract.page_id}' is missing required asset "
                    f"for lang '{lang}': {asset_path}"
                )


def _write_bundle_conf_files(
    *,
    cfg: dict,
    docs_dir: Path,
    bundle_dir: Path,
) -> tuple[Path, Path]:
    conf_base_src = docs_dir / "conf_base.py"
    if not conf_base_src.exists():
        raise RuntimeError(f"Missing conf_base.py: {conf_base_src}")

    conf_base_dst = bundle_dir / "conf_base.py"
    shutil.copy2(conf_base_src, conf_base_dst)

    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    main_tex = str(build_cfg.get("main_tex", "manual_demo.tex"))

    conf_text = "\n".join(
        [
            "# Auto-generated by tools/gen_index_bundle.py",
            "# -*- coding: utf-8 -*-",
            "",
            "import sys",
            "from pathlib import Path",
            "",
            "THIS_DIR = Path(__file__).resolve().parent",
            "if str(THIS_DIR) not in sys.path:",
            "    sys.path.insert(0, str(THIS_DIR))",
            "",
            "from conf_base import *  # noqa: F403",
            "",
            "master_doc = 'index'",
            "exclude_patterns = ['_build', 'page/*', 'generated/*', 'generated/**/*']",
            "html_static_path = ['_static']",
            "html_extra_path = ['renderers/latex/assets']",
            f"latex_documents = [('index', '{main_tex}', '', '', 'howto')]",
            "latex_domain_indices = False",
            "",
        ]
    )
    conf_dst = bundle_dir / "conf.py"
    conf_dst.write_text(conf_text, encoding="utf-8")
    return conf_dst, conf_base_dst


def _copy_bundle_support_assets(
    *,
    docs_dir: Path,
    bundle_dir: Path,
) -> None:
    static_src = docs_dir / "_static"
    if static_src.exists():
        _copytree_replace(static_src, bundle_dir / "_static")

    latex_src = docs_dir / "renderers" / "latex"
    if latex_src.exists():
        _copytree_replace(latex_src, bundle_dir / "renderers" / "latex")


def _materialize_planned_page(
    planned: PlannedPage,
    *,
    cfg: dict,
    target_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
    spec_master_csv: Path,
    base_substitutions: dict[str, str],
    base_vars_map: dict[str, str],
    primary_lang: str,
    title: str,
    model: str | None,
    region: str | None,
) -> str:
    page = planned.page

    if isinstance(page, CoverPdfPage):
        return _render_cover_page_rst(title, _format_tokenized(page.file, model, region))

    if isinstance(page, PdfInsertPage):
        if planned.lang is None:
            raise RuntimeError("pdf_insert planned page is missing lang")
        return _render_pdf_insert_page_rst(
            _format_tokenized(page.file_map[planned.lang], model, region),
            planned.lang,
        )

    page_lang = planned.lang or primary_lang
    page_vars = fill_product_name_from_spec_master(
        base_vars_map,
        spec_master_csv=spec_master_csv,
        model=model,
        region=region,
        lang=page_lang,
    )
    page_substitutions = {
        **base_substitutions,
        **resolve_spec_master_substitutions(
            spec_master_csv=spec_master_csv,
            model=model,
            region=region,
            lang=page_lang,
        ),
    }

    if isinstance(page, CsvPage):
        if planned.lang is None:
            raise RuntimeError("csv_page planned page is missing lang")
        source_path = _resolve_csv_rst_path(
            source_root=bundle_dir,
            page=page,
            lang=planned.lang,
            model=model,
            region=region,
        )
    elif isinstance(page, RstIncludePage):
        source_path = resolve_config_path(docs_dir, page.file, model, region)
    else:
        raise RuntimeError(f"Unsupported page type: {type(page).__name__}")

    if not source_path.exists():
        raise RuntimeError(f"Missing source RST for bundle materialization: {source_path}")

    rst_text = source_path.read_text(encoding="utf-8")
    rst_text = apply_rst_substitutions(rst_text, page_substitutions, page_vars)
    rst_text = rewrite_rst_asset_paths(
        rst_text,
        source_path=source_path,
        target_path=target_path,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    return _prepend_latex_lang(rst_text, planned.lang)


def materialize_bundle(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
    *,
    docs_dir: Path | None = None,
    repo_root: Path | None = None,
    ensure_csv_pages: bool = True,
    page_selector: str | None = None,
    bundle_dir_override: Path | None = None,
    write_wrapper_index: bool = True,
) -> MaterializedBundle:
    actual_docs_dir = docs_dir or paths.docs_dir
    actual_root = repo_root or paths.root
    target_model = resolve_build_model(cfg, model)
    target_region = resolve_build_region(cfg, region)
    build_langs = _build_langs(cfg)
    primary_lang = str(build_langs[0]) if build_langs else "en"
    planned_pages = _select_planned_pages(
        plan_materialized_pages(cfg, model=target_model, region=target_region),
        page_selector,
    )
    _preflight_contract_assets(
        cfg=cfg,
        docs_dir=actual_docs_dir,
        repo_root=actual_root,
        model=target_model,
        region=target_region,
        langs=build_langs,
        planned_pages=planned_pages,
    )

    spec_master_csv = _resolve_spec_master_csv_path(
        cfg,
        repo_root=actual_root,
        model=target_model,
        region=target_region,
    )
    base_vars_map = pick_vars_map(target_model, target_region)
    title_vars = fill_product_name_from_spec_master(
        base_vars_map,
        spec_master_csv=spec_master_csv,
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    base_substitutions = load_rst_substitutions(actual_docs_dir / "conf_base.py")
    title_substitutions = {
        **base_substitutions,
        **resolve_spec_master_substitutions(
            spec_master_csv=spec_master_csv,
            model=target_model,
            region=target_region,
            lang=primary_lang,
        ),
    }
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    reference_doc = resolve_reference_doc(build_cfg.get("word_reference_doc"), root=actual_root)
    title = derive_word_title(build_cfg, reference_doc, title_substitutions, title_vars)

    bundle_dir = bundle_dir_override or bundle_dir_for_target(
        docs_dir=actual_docs_dir,
        model=target_model,
        region=target_region,
    )
    generated_dir = bundle_dir / "generated"
    page_dir = bundle_dir / "page"
    index_path = bundle_dir / "index.rst"
    wrapper_index_path = actual_docs_dir / "index.rst"

    if bundle_dir_override is None:
        cleanup_legacy_rst_artifacts(
            docs_dir=actual_docs_dir,
            model=target_model,
            region=target_region,
        )

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)

    if ensure_csv_pages and any(isinstance(item.page, CsvPage) for item in planned_pages):
        builder = load_word_context(
            cfg,
            target_model,
            target_region,
            phase1_output_dir=generated_dir,
        )
        ensure_csv_page_rsts(cfg, builder, target_model, target_region)
    page_dir.mkdir(parents=True, exist_ok=True)
    _copy_bundle_support_assets(docs_dir=actual_docs_dir, bundle_dir=bundle_dir)
    conf_path, conf_base_path = _write_bundle_conf_files(
        cfg=cfg,
        docs_dir=actual_docs_dir,
        bundle_dir=bundle_dir,
    )

    page_paths: list[Path] = []
    for planned in planned_pages:
        target_path = page_dir / planned.file_name
        rendered = _materialize_planned_page(
            planned,
            cfg=cfg,
            target_path=target_path,
            bundle_dir=bundle_dir,
            docs_dir=actual_docs_dir,
            repo_root=actual_root,
            spec_master_csv=spec_master_csv,
            base_substitutions=base_substitutions,
            base_vars_map=base_vars_map,
            primary_lang=primary_lang,
            title=title,
            model=target_model,
            region=target_region,
        )
        target_path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")
        page_paths.append(target_path)

    index_text = build_index_from_pages(cfg, model=target_model, region=target_region)
    index_path.write_text(index_text, encoding="utf-8")
    if write_wrapper_index:
        wrapper_index_path.write_text(
            build_wrapper_index_text(
                docs_dir=actual_docs_dir,
                bundle_dir=bundle_dir,
            ),
            encoding="utf-8",
        )

    return MaterializedBundle(
        bundle_dir=bundle_dir,
        page_dir=page_dir,
        index_path=index_path,
        conf_path=conf_path,
        conf_base_path=conf_base_path,
        wrapper_index_path=wrapper_index_path,
        page_paths=tuple(page_paths),
        title=title,
        reference_doc=reference_doc,
        model=target_model,
        region=target_region,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--model", default=None, help="Optional product model for include/file paths")
    ap.add_argument("--region", default=None, help="Optional region for include/file paths")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    cfg = load_config(cfg_path)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type != "manual_bundle":
        raise RuntimeError(f"gen_index_bundle supports doc_type=manual_bundle only, got: {doc_type}")

    bundle = materialize_bundle(
        cfg,
        model=args.model,
        region=args.region,
    )
    print(f"[gen_index_bundle] Wrote bundle index: {bundle.index_path}")
    print(f"[gen_index_bundle] Wrote wrapper index: {bundle.wrapper_index_path}")


if __name__ == "__main__":
    main()
