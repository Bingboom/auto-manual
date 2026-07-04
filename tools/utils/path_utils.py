#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    # tools/utils/path_utils.py -> tools/utils -> tools -> repo root
    return Path(__file__).resolve().parents[2]


class PathSegments:
    """Single source of truth for repo-relative path segment literals.

    Every module that builds a repo path should reference these constants
    instead of re-hardcoding the string, so a rename lands in one place.
    """

    DOCS = "docs"
    DATA = "data"
    TOOLS = "tools"
    REPORTS = "reports"
    CONFIGS = "configs"

    BUILD = "_build"
    REVIEW = "_review"
    STATIC = "_static"

    RENDERERS = "renderers"
    TEMPLATES = "templates"
    LATEX = "latex"
    CONTRACTS = "contracts"
    RECIPES = "recipes"
    WORD_TEMPLATE = "word_template"
    COMMON_ASSETS = "common_assets"

    VERSION_TRACKING = "version_tracking"
    RELEASES = "releases"
    CONTENT_QC = "content_qc"
    CLOUD_DOC_BACKPORT = "cloud_doc_backport"
    SOURCE_INTAKE = "source_intake"
    REVISION_LEDGER = "revision_ledger"
    TM_HIT_RATE = "tm_hit_rate"
    PDF_ANNOTATE = "pdf_annotate"
    FLOW_DASHBOARD = "flow_dashboard"

    PARAMS_TEX = "params.tex"
    FONTS_TEX = "fonts.tex"
    LAYOUT_PARAMS_CSV = "layout_params.csv"

    DEFAULT_CONFIG_US = "config.us.yaml"
    DEFAULT_CONFIG_JA = "config.ja.yaml"


# --- suffix helpers -------------------------------------------------------
# These wrap a caller-supplied base directory and never re-anchor at repo
# root, so a site that already resolved a docs_dir / staging root / worktree
# keeps using exactly that base. Use these for dependency-injected call sites;
# use the Paths properties below when the call site starts from repo root.


def docs_build_dir_of(docs_dir: Path) -> Path:
    return docs_dir / PathSegments.BUILD


def review_dir_of(docs_dir: Path) -> Path:
    return docs_dir / PathSegments.REVIEW


def static_dir_of(docs_dir: Path) -> Path:
    return docs_dir / PathSegments.STATIC


def latex_renderer_of(docs_dir: Path) -> Path:
    return docs_dir / PathSegments.RENDERERS / PathSegments.LATEX


def contracts_dir_of(docs_dir: Path) -> Path:
    return docs_dir / PathSegments.TEMPLATES / PathSegments.CONTRACTS


def word_common_assets_of(docs_dir: Path) -> Path:
    return (
        docs_dir
        / PathSegments.TEMPLATES
        / PathSegments.WORD_TEMPLATE
        / PathSegments.COMMON_ASSETS
    )


def version_tracking_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.VERSION_TRACKING


def releases_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.RELEASES


def content_qc_reports_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.CONTENT_QC


def cloud_doc_backport_reports_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.CLOUD_DOC_BACKPORT


def source_intake_reports_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.SOURCE_INTAKE


def revision_ledger_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.REVISION_LEDGER


def tm_hit_rate_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.TM_HIT_RATE


def pdf_annotate_reports_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.PDF_ANNOTATE


def flow_dashboard_reports_of(base_root: Path) -> Path:
    return base_root / PathSegments.REPORTS / PathSegments.FLOW_DASHBOARD


@dataclass(frozen=True)
class Paths:
    root: Path
    # When set, overrides the default ``root / "docs"`` anchor so a
    # config-driven docs_dir threads through every derived path. Defaults to
    # None to keep the existing ``Paths(root=...)`` behavior unchanged.
    _docs_dir: Path | None = None

    @property
    def configs_dir(self) -> Path:
        return self.root / PathSegments.CONFIGS

    @property
    def config_yaml(self) -> Path:
        return self.configs_dir / PathSegments.DEFAULT_CONFIG_US

    def config_file(self, name: str) -> Path:
        return self.configs_dir / name

    @property
    def docs_dir(self) -> Path:
        if self._docs_dir is not None:
            return self._docs_dir
        return self.root / PathSegments.DOCS

    @property
    def docs_build_dir(self) -> Path:
        return docs_build_dir_of(self.docs_dir)

    @property
    def latex_build_dir(self) -> Path:
        return self.docs_build_dir / PathSegments.LATEX

    @property
    def tools_dir(self) -> Path:
        return self.root / PathSegments.TOOLS

    @property
    def latex_renderer_dir(self) -> Path:
        return latex_renderer_of(self.docs_dir)

    @property
    def latex_theme_dir(self) -> Path:
        # Backward-compatible alias; repo now uses docs/renderers/latex.
        return self.latex_renderer_dir

    @property
    def templates_dir(self) -> Path:
        return self.docs_dir / PathSegments.TEMPLATES

    @property
    def data_dir(self) -> Path:
        return self.root / PathSegments.DATA

    @property
    def review_dir(self) -> Path:
        return review_dir_of(self.docs_dir)

    @property
    def static_dir(self) -> Path:
        return static_dir_of(self.docs_dir)

    @property
    def contracts_dir(self) -> Path:
        return contracts_dir_of(self.docs_dir)

    @property
    def recipes_dir(self) -> Path:
        return self.templates_dir / PathSegments.RECIPES

    @property
    def params_tex(self) -> Path:
        return self.latex_renderer_dir / PathSegments.PARAMS_TEX

    @property
    def fonts_tex(self) -> Path:
        return self.latex_renderer_dir / PathSegments.FONTS_TEX

    @property
    def layout_params_csv(self) -> Path:
        # DEFAULT location only. The config override lives in
        # build_paths.resolve_layout_params_csv; do not use this property where
        # the ``paths.layout_params_csv`` config key must win.
        return self.data_dir / PathSegments.LAYOUT_PARAMS_CSV

    @property
    def version_tracking_dir(self) -> Path:
        return version_tracking_of(self.root)

    @property
    def releases_dir(self) -> Path:
        return releases_of(self.root)

    @property
    def content_qc_reports_dir(self) -> Path:
        return content_qc_reports_of(self.root)

    @property
    def cloud_doc_backport_reports_dir(self) -> Path:
        return cloud_doc_backport_reports_of(self.root)

    @property
    def source_intake_reports_dir(self) -> Path:
        return source_intake_reports_of(self.root)

    @property
    def revision_ledger_dir(self) -> Path:
        return revision_ledger_of(self.root)

    @property
    def tm_hit_rate_dir(self) -> Path:
        return tm_hit_rate_of(self.root)

    @property
    def pdf_annotate_reports_dir(self) -> Path:
        return pdf_annotate_reports_of(self.root)

    @property
    def flow_dashboard_reports_dir(self) -> Path:
        return flow_dashboard_reports_of(self.root)

    def safety_rst(self, lang: str) -> Path:
        return self.docs_dir / f"safety_{lang}.rst"

    def main_tex(self, main_tex_name: str) -> Path:
        return self.latex_build_dir / main_tex_name

    def output_pdf(self, pdf_name: str) -> Path:
        return self.latex_build_dir / pdf_name

    def clean_targets(self) -> tuple[Path, Path]:
        # Order matters: callers unpack (build_dir, params_tex) and rmtree the
        # first. Do not reverse.
        return self.docs_build_dir, self.params_tex

    @classmethod
    def from_docs_dir(cls, root: Path, docs_dir: Path) -> "Paths":
        return cls(root=root, _docs_dir=docs_dir)


def get_paths() -> Paths:
    return Paths(root=repo_root())


def paths_for_docs_dir(root: Path, docs_dir: Path) -> Paths:
    """Paths anchored at a caller-resolved docs_dir (e.g. from config).

    The caller resolves the docs_dir (build_paths.resolve_docs_dir owns the
    ``paths.docs_dir`` config lookup); this keeps path_utils free of a
    config_loader dependency and the strict mypy graph minimal.
    """
    return Paths.from_docs_dir(root, docs_dir)
