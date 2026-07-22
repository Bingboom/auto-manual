#!/usr/bin/env python3
"""Render the InDesign same-source IR into a print-layout web edition.

Consumes the *same* ``manual-ir/v1`` that feeds the IDML export
(``build_same_source_ir``), so the web edition and the InDesign delivery share
one content source. Writes a self-contained ``webedition/`` directory
(body.html + assets/ + manifest.json) that ``tools/readthedocs_source.py`` then
grafts into the RTD catalog as the primary entry.

Best-effort by design: if the IR cannot be built (edge-case content, missing
assets), it warns and exits 0 without writing, so the RTD HTML build stays
green and the catalog simply keeps the HTML-only entry.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.idml.web_edition import render_web_edition  # noqa: E402
from tools.manual_ir import build_manual_ir  # noqa: E402
from tools.utils.path_utils import repo_root  # noqa: E402


def _primary_lang(config_path: Path, override: str | None) -> str:
    if override:
        return override
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    languages = (cfg.get("build") or {}).get("languages") or []
    if not languages:
        raise RuntimeError(f"no build.languages in {config_path}; pass --lang")
    return str(languages[0])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--lang", default=None, help="Primary language (default: build.languages[0])")
    parser.add_argument("--bundle-root", required=True, type=Path, help="Prepared rst bundle root")
    parser.add_argument("--data-root", required=True, type=Path, help="phase2 snapshot for attachment resolution")
    parser.add_argument("--out", required=True, type=Path, help="Output webedition/ directory")
    parser.add_argument("--title", default=None, help="Manual title (default: derived from IR metadata)")
    parser.add_argument("--version", default=None, help="Provenance version label shown in the toolbar")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail (exit 1) instead of skipping when the IR cannot be built",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = repo_root()
    config_path = args.config if args.config.is_absolute() else root / args.config
    lang = _primary_lang(config_path, args.lang)

    # The web edition is a presentation of the same IR the IDML export uses,
    # but not the pixel-authoritative delivery, so it uses build_manual_ir
    # (the projection build_same_source_ir wraps) without the production gates
    # (zero-skipped-raw, semantic-row, asset-enforcement) that are meant for
    # the InDesign artifact. Skipped raw blocks are LaTeX layout directives
    # (e.g. page breaks) with no reader content; the count is recorded in the
    # manifest for transparency.
    try:
        ir = build_manual_ir(
            root=root,
            bundle_root=args.bundle_root,
            model=args.model,
            region=args.region,
            lang=lang,
            source="prepared-bundle",
            data_root=args.data_root,
        )
    except Exception as exc:  # noqa: BLE001 - best-effort by contract
        message = f"[web-edition] skipped {args.model}/{args.region}: {exc}"
        if args.strict:
            print(message, file=sys.stderr)
            return 1
        print(message)
        return 0

    title = args.title or _resolve_title(args.bundle_root, ir, args.model, args.region)
    provenance = {"source": "same-source IR"}
    if args.version:
        provenance["version"] = args.version

    render_web_edition(
        ir,
        bundle_root=args.bundle_root,
        data_root=args.data_root,
        out_dir=args.out,
        title=title,
        provenance=provenance,
    )
    return 0


def _resolve_title(bundle_root: Path, ir, model: str, region: str) -> str:
    # The generated md manual's first heading is the authoritative manual
    # title and is what the RTD catalog entry uses, so match it.
    index_md = bundle_root.parent / "md" / "index.md"
    if index_md.is_file():
        for line in index_md.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    meta = getattr(ir, "metadata", None) or {}
    for key in ("product_name", "manual_title", "title"):
        value = meta.get(key) if isinstance(meta, dict) else None
        if value:
            return str(value)
    return f"{model} / {region}"


if __name__ == "__main__":
    raise SystemExit(main())
