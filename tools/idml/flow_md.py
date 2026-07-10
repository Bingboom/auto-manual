"""Semantic Markdown artifacts for flow-idml handoff mode."""
from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.idml import export_paths
    from tools.idml import loaders as _loaders
    from tools.idml_rst_extract import bundle_page_order, extract_page
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from idml import export_paths  # type: ignore
    from idml import loaders as _loaders  # type: ignore
    from idml_rst_extract import bundle_page_order, extract_page  # type: ignore


@dataclass(frozen=True)
class FlowArtifacts:
    markdown: Path
    source_trace: Path
    asset_manifest: Path
    conversion_notes: Path


def write_flow_artifacts(*, root: Path, model: str, region: str, lang: str,
                         data_root: Path, bundle_root: Path,
                         build_command: list[str] | None = None) -> FlowArtifacts:
    out_dir = export_paths.flow_output_dir(root, model, region, lang, bundle_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    writer = _FlowMarkdownWriter(
        root=root,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        bundle_root=bundle_root,
        out_dir=out_dir,
        build_command=build_command or [],
    )
    return writer.write()


class _FlowMarkdownWriter:
    def __init__(self, *, root: Path, model: str, region: str, lang: str,
                 data_root: Path, bundle_root: Path, out_dir: Path,
                 build_command: list[str]) -> None:
        self.root = root
        self.model = model
        self.region = region
        self.lang = lang
        self.data_root = data_root
        self.bundle_root = bundle_root
        self.out_dir = out_dir
        self.build_command = build_command
        self.assets: dict[tuple[str, str], dict[str, str]] = {}
        self.component_counts: dict[str, int] = {}
        self.skipped_raw = 0
        self.pages: list[Path] = []
        self.notes: list[str] = []

    @property
    def manual_id(self) -> str:
        return f"{self.model.replace('-', '')}_{self.region}_{self.lang.upper()}"

    def write(self) -> FlowArtifacts:
        md_path = self.out_dir / "manual.flow.md"
        trace_path = self.out_dir / "manual.flow.source_trace.json"
        manifest_path = self.out_dir / "manual.flow.asset_manifest.csv"
        notes_path = self.out_dir / "flow_conversion_notes.md"
        markdown = self._markdown()
        md_path.write_text(markdown, encoding="utf-8")
        self._write_manifest(manifest_path)
        self._write_trace(trace_path, md_path, manifest_path)
        self._write_notes(notes_path)
        return FlowArtifacts(md_path, trace_path, manifest_path, notes_path)

    def _markdown(self) -> str:
        lines = self._front_matter()
        tags = {
            "latex",
            f"region_{self.region.lower()}",
            f"lang_{self.lang.lower()}",
            "model_" + self.model.lower().replace("-", "_"),
        }
        self.pages = bundle_page_order(self.bundle_root) if self.bundle_root.is_dir() else []
        if not self.pages:
            self.notes.append(f"No prepared RST bundle was found at {self.bundle_root}.")
        for page in self.pages:
            data_lines = self._data_page(page, self._source_ref(page, 0))
            if data_lines is not None:
                lines.extend(["", f"<!-- source_ref: {self._source_ref(page, 0)} -->", *data_lines])
                continue
            result = extract_page(page, tags)
            self.skipped_raw += result.skipped_raw
            if result.skipped_raw:
                self.notes.append(f"{page.name}: skipped {result.skipped_raw} raw latex block(s).")
            for index, (kind, text) in enumerate(result.blocks, start=1):
                source_ref = self._source_ref(page, index)
                rendered = self._render_block(kind, text, source_ref)
                if rendered:
                    lines.extend(["", f"<!-- source_ref: {source_ref} -->", *rendered])
        lines.append("")
        return "\n".join(lines)

    def _front_matter(self) -> list[str]:
        return [
            "---",
            f"manual_id: {self.manual_id}",
            f"model: {self.model}",
            f"region: {self.region}",
            f"language: {self.lang}",
            "version: unknown",
            f"source_snapshot: {self._source_snapshot()}",
            f"build_commit: {self._git_sha()}",
            "idml_mode: flow",
            "---",
        ]

    def _render_block(self, kind: str, text: str, source_ref: str) -> list[str]:
        if kind == "h1":
            return [f"# {text}"]
        if kind == "h2":
            return [f"## {text}"]
        if kind == "h3":
            return [f"### {text}"]
        if kind == "body":
            return self._paragraph_lines(text)
        if kind == "list":
            item = text[1:].strip() if text.startswith("•") else text.strip()
            return [f"- {item}"]
        if kind == "image":
            return self._image(text, source_ref, "image")
        if kind == "table":
            return _markdown_table(json.loads(text))
        if kind == "component":
            return self._component(json.loads(text), source_ref)
        if kind == "layout":
            self.notes.append(f"{source_ref}: layout marker {text!r} omitted from flow-md.")
            return []
        self.notes.append(f"{source_ref}: unsupported block kind {kind!r} omitted.")
        return []

    def _component(self, spec: dict, source_ref: str) -> list[str]:
        kind = str(spec.get("kind") or "component")
        self.component_counts[kind] = self.component_counts.get(kind, 0) + 1
        if kind in {"notice", "warnbox", "warninglead", "safetywarning"}:
            variant = str(spec.get("variant") or spec.get("label") or "warning").lower()
            label = str(spec.get("label") or variant.upper())
            texts = [str(x) for x in spec.get("texts", []) if str(x).strip()]
            lines = [f"::: {variant} source_ref=\"{source_ref}\"", f"**{label}**"]
            for item in texts:
                lines.extend(_list_or_paragraph(item, bool(spec.get("list"))))
            lines.append(":::")
            return lines
        if kind == "fcc":
            lines = [f"::: fcc source_ref=\"{source_ref}\""]
            for item in spec.get("texts", []):
                lines.extend(self._paragraph_lines(str(item)))
            lines.append(":::")
            return lines
        if kind == "inbox":
            rows = [["No.", "Asset", "Label"]]
            for idx, item in enumerate(spec.get("items", []), start=1):
                asset = str(item.get("img", ""))
                label = str(item.get("label", ""))
                self._record_asset(asset, source_ref, "inbox")
                rows.append([str(idx), asset, label])
            return [f"::: inbox source_ref=\"{source_ref}\"", *_markdown_table(rows), ":::"]
        if kind == "lcdmode":
            lines = [f"::: lcdmode source_ref=\"{source_ref}\""]
            image_ref = str(spec.get("img", ""))
            if image_ref:
                lines.extend(self._image(image_ref, source_ref, "lcdmode"))
            rows = [["State", "Action", "Description"]]
            for group in spec.get("groups", []):
                state = str(group.get("state", ""))
                for action, desc in group.get("actions", []):
                    rows.append([state, str(action), str(desc)])
            lines.extend(_markdown_table(rows))
            lines.append(":::")
            return lines
        self.notes.append(f"{source_ref}: component {kind!r} kept as a JSON code block.")
        return ["```json", json.dumps(spec, ensure_ascii=False, indent=2), "```"]

    def _data_page(self, page: Path, source_ref: str) -> list[str] | None:
        name = page.name
        try:
            if name.startswith("spec_"):
                return self._spec_page()
            if name.startswith("lcd_icons_"):
                return self._lcd_page(source_ref)
            if name.startswith("troubleshooting_"):
                return self._trouble_page()
            if name.startswith("symbols_"):
                return self._symbols_page(source_ref)
        except OSError as exc:
            self.notes.append(f"{source_ref}: data fallback failed: {exc}")
            return None
        return None

    def _spec_page(self) -> list[str] | None:
        sections = _loaders.load_spec_sections(self.data_root, self.model, self.region, self.lang)
        if not sections:
            return None
        lines = ["# SPECIFICATIONS"]
        for section in sections:
            lines.extend(["", f"## {section['title']}"])
            rows = [["Item", "Value"], *section["rows"]]
            lines.extend(_markdown_table(rows))
        annotations = _loaders.load_spec_annotations(self.data_root, self.model, self.region, self.lang)
        if annotations:
            lines.extend(["", "## Notes", *annotations])
        self.notes.append("spec data page rendered from phase2 rows for flow-md.")
        return lines

    def _lcd_page(self, source_ref: str) -> list[str] | None:
        rows = _loaders.load_lcd_rows(self.data_root, self.model, self.lang, self.region)
        if not rows:
            return None
        table = [["No.", "Asset", "Name", "Description"]]
        for row in rows:
            asset = str(row.get("figure", ""))
            self._record_asset(asset, source_ref, "lcd")
            table.append([
                str(row.get("no", "")),
                asset,
                str(row.get("name", "")),
                str(row.get("desc", "")),
            ])
        self.notes.append("lcd data page rendered from phase2 rows for flow-md.")
        return ["# LCD DISPLAY", *_markdown_table(table)]

    def _trouble_page(self) -> list[str] | None:
        rows = _loaders.load_trouble_rows(self.data_root, self.model, self.region, self.lang)
        if not rows:
            return None
        self.notes.append("troubleshooting data page rendered from phase2 rows for flow-md.")
        return ["# TROUBLESHOOTING", *_markdown_table([["Error Code", "Corrective Measures"], *rows])]

    def _symbols_page(self, source_ref: str) -> list[str] | None:
        signals, icons = _loaders.load_symbols_rows(self.data_root, self.lang)
        if not (signals or icons):
            return None
        copy = _loaders.symbol_copy(self.lang)
        rows = [[copy["symbol"], copy["meaning"]], *signals]
        for icon in icons:
            asset = str(icon.get("figure", ""))
            self._record_asset(asset, source_ref, "symbols")
            rows.append([asset, str(icon.get("text", ""))])
        self.notes.append("symbols data page rendered from phase2 rows for flow-md.")
        return [f"# {copy['title']}", *_markdown_table(rows)]

    def _paragraph_lines(self, text: str) -> list[str]:
        parts = [part.strip() for part in text.split("\n") if part.strip()]
        return parts or [""]

    def _image(self, ref: str, source_ref: str, kind: str) -> list[str]:
        self._record_asset(ref, source_ref, kind)
        alt = Path(ref).stem.replace("_", " ") or "figure"
        asset_id = _asset_id(ref)
        return [f"![{alt}]({ref})", f"<!-- asset_id: {asset_id} asset_ref: {ref} -->"]

    def _record_asset(self, ref: str, source_ref: str, kind: str) -> None:
        ref = ref.strip()
        if not ref:
            return
        key = (_asset_id(ref), ref)
        self.assets[key] = {
            "asset_id": key[0],
            "asset_ref": ref,
            "resolved_path": _display_path(self.root, self._resolve_asset(ref)),
            "source_ref": source_ref,
            "kind": kind,
        }

    def _resolve_asset(self, ref: str) -> Path | None:
        candidates = [
            self.bundle_root / ref,
            self.bundle_root / "_assets" / Path(ref).name,
            self.bundle_root / "_repo_assets" / Path(ref).name,
            self.data_root / ref,
            self.root / ref,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _source_ref(self, page: Path, index: int) -> str:
        rel = _display_path(self.root, page)
        return f"page={page.stem} source={rel} block={index}"

    def _write_manifest(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["asset_id", "asset_ref", "resolved_path", "source_ref", "kind"],
            )
            writer.writeheader()
            for _, row in sorted(self.assets.items()):
                writer.writerow(row)

    def _write_trace(self, path: Path, md_path: Path, manifest_path: Path) -> None:
        trace = {
            "manual_id": self.manual_id,
            "model": self.model,
            "region": self.region,
            "language": self.lang,
            "version": "unknown",
            "source_snapshot": self._source_snapshot(),
            "source_tables": self._source_tables(),
            "canonical_md": _display_path(self.root, md_path),
            "template_commit": self._git_sha(),
            "asset_manifest": _display_path(self.root, manifest_path),
            "build_command": self.build_command,
            "idml_mode": "flow",
            "bundle_root": _display_path(self.root, self.bundle_root),
            "pages": [_display_path(self.root, page) for page in self.pages],
            "skipped_raw_blocks": self.skipped_raw,
        }
        path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _write_notes(self, path: Path) -> None:
        lines = [
            "# Flow Conversion Notes",
            "",
            f"- Manual: `{self.manual_id}`",
            "- Mode: `flow`",
            f"- Pages parsed: {len(self.pages)}",
            f"- Assets referenced: {len(self.assets)}",
            f"- Skipped raw blocks: {self.skipped_raw}",
            "",
            "## Component Downgrades",
            "",
        ]
        if self.component_counts:
            lines.extend(f"- `{kind}`: {count}" for kind, count in sorted(self.component_counts.items()))
        else:
            lines.append("- None")
        if self.notes:
            lines.extend(["", "## Notes", ""])
            lines.extend(f"- {note}" for note in self.notes)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _source_snapshot(self) -> str:
        manifest = self.data_root / "snapshot_manifest.json"
        return _display_path(self.root, manifest if manifest.exists() else self.data_root)

    def _source_tables(self) -> list[str]:
        if not self.data_root.exists():
            return []
        return sorted(path.name for path in self.data_root.glob("*.csv"))

    def _git_sha(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return "unknown"
        return result.stdout.strip() or "unknown"


def _markdown_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    width = max(len(row) for row in rows)
    padded = [list(row) + [""] * (width - len(row)) for row in rows]
    header, body = padded[0], padded[1:]
    lines = ["| " + " | ".join(_cell(cell) for cell in header) + " |"]
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    lines.extend("| " + " | ".join(_cell(cell) for cell in row) + " |" for row in body)
    return lines


def _list_or_paragraph(text: str, list_like: bool) -> list[str]:
    chunks = [part.strip() for part in text.split("\n") if part.strip()]
    if list_like:
        return [f"- {chunk[2:].strip() if chunk.startswith('- ') else chunk}" for chunk in chunks]
    return chunks


def _cell(value: object) -> str:
    return str(value).replace("\n", "<br>").replace("|", "\\|").strip()


def _asset_id(ref: str) -> str:
    return Path(ref).stem or ref


def _display_path(root: Path, path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
