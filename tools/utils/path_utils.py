#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    # tools/utils/path_utils.py -> tools/utils -> tools -> repo root
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def config_yaml(self) -> Path:
        return self.root / "config.yaml"

    @property
    def docs_dir(self) -> Path:
        return self.root / "docs"

    @property
    def docs_build_dir(self) -> Path:
        return self.docs_dir / "_build"

    @property
    def latex_build_dir(self) -> Path:
        return self.docs_build_dir / "latex"

    @property
    def tools_dir(self) -> Path:
        return self.root / "tools"

    @property
    def latex_renderer_dir(self) -> Path:
        return self.docs_dir / "renderers" / "latex"

    @property
    def latex_theme_dir(self) -> Path:
        # Backward-compatible alias; repo now uses docs/renderers/latex.
        return self.latex_renderer_dir

    @property
    def templates_dir(self) -> Path:
        return self.docs_dir / "templates"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    def safety_rst(self, lang: str) -> Path:
        return self.docs_dir / f"safety_{lang}.rst"

    def main_tex(self, main_tex_name: str) -> Path:
        return self.latex_build_dir / main_tex_name

    def output_pdf(self, pdf_name: str) -> Path:
        return self.latex_build_dir / pdf_name


def get_paths() -> Paths:
    return Paths(root=repo_root())
