#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tools.gen_index_bundle import MaterializedBundle
from tools.word_bundle_common import paths
from tools.word_bundle_docx_pandoc import resolve_pandoc_binary
from tools.word_bundle_html import build_word_bundle_html


MYST_COMPATIBLE_WRITER = "commonmark_x+pipe_tables+yaml_metadata_block-fenced_divs-bracketed_spans-attributes"


def resolve_markdown_writer(pandoc_bin: str) -> str:
    proc = subprocess.run(
        [pandoc_bin, "--list-output-formats"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    formats = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    if "myst" in formats:
        return "myst"
    if "commonmark_x" in formats:
        return MYST_COMPATIBLE_WRITER
    if "gfm" in formats:
        return "gfm"
    return "markdown"


def export_markdown_from_bundle(
    cfg: dict,
    model: str | None,
    region: str | None,
    markdown_output: str,
    *,
    materialized_bundle: MaterializedBundle | None = None,
    output_dir: Path | None = None,
) -> Path:
    bundle_output_dir = output_dir
    bundle_html, _reference_doc, _page_metas = build_word_bundle_html(
        cfg,
        model,
        region,
        materialized_bundle=materialized_bundle,
        output_dir=bundle_output_dir,
    )

    out_path = Path(markdown_output)
    if not out_path.is_absolute():
        out_root = bundle_output_dir or (paths.docs_build_dir / "md")
        out_path = out_root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    resource_path = os.pathsep.join(
        [
            str(bundle_html.parent),
            str(paths.docs_dir),
            str(paths.root),
        ]
    )
    pandoc_bin = resolve_pandoc_binary(None)
    markdown_writer = resolve_markdown_writer(pandoc_bin)
    markdown_reader = "html" if markdown_writer == "myst" else "html-native_divs-native_spans"
    subprocess.run(
        [
            pandoc_bin,
            str(bundle_html),
            f"--from={markdown_reader}",
            f"--to={markdown_writer}",
            "--markdown-headings=atx",
            "--wrap=none",
            "--resource-path",
            resource_path,
            "-o",
            str(out_path),
        ],
        check=True,
        cwd=str(paths.root),
    )
    return out_path
