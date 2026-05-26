#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from tools.gen_index_bundle import MaterializedBundle
from tools.word_bundle_common import paths
from tools.word_bundle_docx_images import embed_external_docx_images as _embed_external_docx_images
from tools.word_bundle_docx_pandoc import resolve_pandoc_binary
from tools.word_bundle_docx_styles import (
    enforce_docx_outline_levels as _enforce_docx_outline_levels,
    remap_reference_doc_styles as _remap_reference_doc_styles,
)
from tools.word_bundle_html import build_word_bundle_html


class WordComExportError(RuntimeError):
    """Raised when the Windows Word COM export path fails before producing DOCX."""


def _ps_quote(value: str) -> str:
    return value.replace("'", "''")


def _word_com_timeout_seconds(env: dict[str, str] | None = None) -> float | None:
    raw = (env or os.environ).get("AUTO_MANUAL_WORD_COM_TIMEOUT_SECONDS", "120").strip()
    if raw.lower() in {"", "0", "false", "none", "off"}:
        return None
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise RuntimeError("AUTO_MANUAL_WORD_COM_TIMEOUT_SECONDS must be a positive number, 0, or 'off'") from exc
    if timeout <= 0:
        return None
    return timeout


def _cleanup_timed_out_word_processes(started_at: float) -> None:
    if not sys.platform.startswith("win"):
        return
    cutoff_epoch = max(0, int(started_at) - 5)
    script = f"""
$cutoff = [DateTimeOffset]::FromUnixTimeSeconds({cutoff_epoch}).LocalDateTime
Get-CimInstance Win32_Process |
  Where-Object {{
    $_.Name -eq 'WINWORD.EXE' -and
    $_.CreationDate -ge $cutoff -and
    ($_.CommandLine -match '/Automation|-Embedding')
  }} |
  ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}
"""
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _export_docx_via_pandoc(bundle_html: Path, out_path: Path, reference_doc: Path | None) -> None:
    pandoc = resolve_pandoc_binary(reference_doc)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    resource_path = os.pathsep.join(
        [
            str(bundle_html.parent),
            str(paths.docs_dir),
            str(paths.root),
        ]
    )

    cmd = [
        pandoc,
        str(bundle_html),
        "--from=html",
        "--to=docx",
        "--metadata",
        "title=",
        "--resource-path",
        resource_path,
        "-o",
        str(out_path),
    ]
    if reference_doc is not None:
        cmd += ["--reference-doc", str(reference_doc)]

    subprocess.run(cmd, check=True, cwd=str(paths.root))


def _export_docx_via_word(bundle_html: Path, out_path: Path, reference_doc: Path | None) -> None:
    if not sys.platform.startswith("win"):
        _export_docx_via_pandoc(bundle_html, out_path, reference_doc)
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ref_literal = _ps_quote(str(reference_doc)) if reference_doc else ""
    html_literal = _ps_quote(str(bundle_html))
    out_literal = _ps_quote(str(out_path))

    script = f"""
$ErrorActionPreference = 'Stop'
$referencePath = '{ref_literal}'
$htmlPath = '{html_literal}'
$outPath = '{out_literal}'
$word = $null
$doc = $null
$htmlDoc = $null
$wdAlertsNone = 0
$wdFormatXMLDocument = 12
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = $wdAlertsNone

    if ($referencePath) {{
        Copy-Item -LiteralPath $referencePath -Destination $outPath -Force
        $doc = $word.Documents.Open($outPath)
        $deleteEnd = [Math]::Max(0, $doc.Content.End - 1)
        if ($deleteEnd -gt 0) {{
            $doc.Range(0, $deleteEnd).Delete()
        }}
    }} else {{
        $doc = $word.Documents.Add()
    }}

    $htmlDoc = $word.Documents.Open($htmlPath, $false, $true)
    $doc.Range(0, 0).FormattedText = $htmlDoc.Range().FormattedText

    foreach ($table in @($doc.Tables)) {{
        try {{
            $table.Style = 'Table Grid'
        }} catch {{
        }}
    }}

    if ($referencePath) {{
        $doc.Save()
    }} else {{
        $doc.SaveAs([ref]$outPath, [ref]$wdFormatXMLDocument)
    }}
}} finally {{
    if ($htmlDoc) {{
        $htmlDoc.Close([ref]$false)
    }}
    if ($doc) {{
        $doc.Close([ref]$false)
    }}
    if ($word) {{
        $word.Quit()
    }}
}}
"""
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]
    started_at = time.time()
    timeout = _word_com_timeout_seconds()
    try:
        subprocess.run(
            cmd,
            check=True,
            cwd=str(paths.root),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        _cleanup_timed_out_word_processes(started_at)
        raise WordComExportError(f"Word COM export timed out after {timeout:g}s") from exc
    except (OSError, subprocess.CalledProcessError) as exc:
        raise WordComExportError(f"Word COM export failed: {exc}") from exc


def _docx_is_valid(docx_path: Path) -> bool:
    return docx_path.exists() and zipfile.is_zipfile(docx_path)


def export_word_from_bundle(
    cfg: dict,
    model: str | None,
    region: str | None,
    word_output: str,
    *,
    materialized_bundle: MaterializedBundle | None = None,
    output_dir: Path | None = None,
) -> Path:
    bundle_output_dir = output_dir
    bundle_html, reference_doc, page_metas = build_word_bundle_html(
        cfg,
        model,
        region,
        materialized_bundle=materialized_bundle,
        output_dir=bundle_output_dir,
    )

    out_path = Path(word_output)
    if not out_path.is_absolute():
        out_root = bundle_output_dir or (paths.docs_build_dir / "word")
        out_path = out_root / out_path

    try:
        _export_docx_via_word(bundle_html, out_path, reference_doc)
    except WordComExportError as exc:
        print(f"[word_bundle_docx] {exc}; retrying with pandoc: {out_path}")
        _export_docx_via_pandoc(bundle_html, out_path, reference_doc)
    if not _docx_is_valid(out_path):
        print(f"[word_bundle_docx] Word COM produced an invalid DOCX, retrying with pandoc: {out_path}")
        _export_docx_via_pandoc(bundle_html, out_path, reference_doc)
    _embed_external_docx_images(out_path)
    _remap_reference_doc_styles(out_path, page_metas)
    _enforce_docx_outline_levels(out_path)
    return out_path
