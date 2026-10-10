"""图标与素材 tab: the shared Web asset library, listed live from the repository.

A group in design_system/content.yaml reads a registry manifest (the shared
symbol and button manifests), lists a folder, or names files. Every file must
sit in a known asset folder, exist and not carry a hash the symbol manifest has
withdrawn, and a note for a file or key that no longer exists fails, so the
gallery never shows retired art or stale guidance.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from tools.rtd.design_content import DesignSystemError, inline

# Repository folders the page may take art from: `<group>/<file>` in the preview
# markup, the gallery and the published copy.
ASSET_ROOTS = {
    "symbols": "docs/renderers/web/assets/shared/symbols/native-v1",
    "buttons": "docs/renderers/web/assets/shared/buttons",
    "lcd": "docs/renderers/web/assets/shared/lcd",
    "inbox": "docs/templates/word_template/common_assets/in_the_box",
    "marks": "docs/templates/word_template/common_assets/symbols",
    "latex": "docs/renderers/latex/assets",
    "cover": "docs/templates/word_template/common_assets/cover",
}
# Registry manifests: (path, entry path field, semantic key field). Entry paths are
# relative to the manifest; the symbol manifest also lists the withdrawn hashes.
REGISTRIES = {
    "symbols": ("docs/renderers/web/assets/shared/symbols/manifest.json", "path", "key"),
    "buttons": ("docs/renderers/web/assets/shared/buttons/manifest.json", "asset", "semantic_key"),
}
FORMATS = {".svg": "SVG", ".png": "PNG"}
# Tile grounds and the live stylesheet colour each one shows.
GROUNDS = {"paper": "--hb-paper", "surface": "--hb-surface", "dark": "--hb-brand-dark"}

_REF = re.compile(r"([a-z]+)/([A-Za-z0-9][A-Za-z0-9._-]*)")
_ID = re.compile(r"[a-z][a-z0-9-]*")
_COLOR = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_PNG = b"\x89PNG\r\n\x1a\n"


def asset_source(root: Path, group: str, name: str) -> Path:
    """The repository file behind `<group>/<name>`; a missing one is drift."""
    if group not in ASSET_ROOTS:
        raise DesignSystemError(f"unknown asset group {group}")
    source = root / ASSET_ROOTS[group] / name
    if not source.is_file() or source.is_symlink():
        raise DesignSystemError(f"missing asset {group}/{name}")
    return source


def withdrawn_hashes(root: Path) -> frozenset[str]:
    manifest = json.loads((root / REGISTRIES["symbols"][0]).read_text(encoding="utf-8"))
    return frozenset(entry["sha256"] for entry in manifest.get("withdrawn", []))


def check_not_withdrawn(sources: dict[str, Path], withdrawn: frozenset[str]) -> None:
    """Retired bytes stay retired under any name: the page never shows or copies them."""
    for ref, source in sources.items():
        if hashlib.sha256(source.read_bytes()).hexdigest() in withdrawn:
            raise DesignSystemError(f"asset {ref} carries a withdrawn hash")


def _ref(root: Path, source: Path) -> str:
    folder = source.parent.resolve()
    for group, relative in ASSET_ROOTS.items():
        if (root / relative).resolve() == folder:
            asset_source(root, group, source.name)
            return f"{group}/{source.name}"
    raise DesignSystemError(f"{source} is outside the known asset folders")


def _registry_members(root: Path, name: str) -> list[tuple[str, str | None, str | None]]:
    if name not in REGISTRIES:
        raise DesignSystemError(f"unknown asset registry {name}")
    manifest_path, path_field, key_field = REGISTRIES[name]
    manifest = root / manifest_path
    entries = json.loads(manifest.read_text(encoding="utf-8"))["assets"]
    return [(_ref(root, manifest.parent / entry[path_field]), entry[key_field], None) for entry in entries]


def _folder_members(root: Path, folder: str) -> list[tuple[str, str | None, str | None]]:
    if folder not in ASSET_ROOTS:
        raise DesignSystemError(f"unknown asset group {folder}")
    files = sorted(path for path in (root / ASSET_ROOTS[folder]).iterdir() if path.suffix.lower() in FORMATS)
    return [(_ref(root, path), None, None) for path in files]


def _file_members(root: Path, files: list) -> list[tuple[str, str | None, str | None]]:
    members = []
    for entry in files:
        entry = entry if isinstance(entry, dict) else {"file": entry}
        match = _REF.fullmatch(str(entry["file"]))
        if match is None or match.group(2).rsplit(".", 1)[-1].lower() not in {"svg", "png"}:
            raise DesignSystemError(f"asset {entry['file']}: needs <group>/<file>.svg|png")
        asset_source(root, *match.groups())
        members.append((entry["file"], None, entry.get("ground")))
    return members


def _members(group: dict, root: Path) -> list[tuple[str, str | None, str | None]]:
    """(ref, semantic key, ground) for each file the group shows, in order."""
    if "registry" in group:
        members = _registry_members(root, group["registry"])
    elif "folder" in group:
        members = _folder_members(root, group["folder"])
    else:
        members = _file_members(root, group["files"])
    include, exclude = group.get("include", []), group.get("exclude", [])

    def shown(ref: str) -> bool:
        name = ref.split("/", 1)[1]
        return (not include or any(part in name for part in include)) and not any(part in name for part in exclude)

    return [member for member in members if shown(member[0])]


def _source_paths(group: dict) -> list[str]:
    if "registry" in group:
        return [REGISTRIES[group["registry"]][0]]
    if "folder" in group:
        return [ASSET_ROOTS[group["folder"]] + "/"]
    refs = [entry["file"] if isinstance(entry, dict) else entry for entry in group["files"]]
    return sorted({ASSET_ROOTS[ref.split("/", 1)[0]] + "/" for ref in refs})


def _size(count: int) -> str:
    return f"{count / 1024:.1f} KB" if count < 1024 * 1024 else f"{count / 1048576:.1f} MB"


def _has_chunk(data: bytes, kind: bytes) -> bool:
    position = len(_PNG)
    while position + 8 <= len(data):
        chunk = data[position + 4:position + 8]
        if chunk == kind:
            return True
        if chunk == b"IDAT":
            return False
        position += 12 + int.from_bytes(data[position:position + 4], "big")
    return False


def _png_facts(ref: str, data: bytes) -> list[str]:
    if not data.startswith(_PNG) or data[12:16] != b"IHDR":
        raise DesignSystemError(f"asset {ref} is not a PNG file")
    width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    alpha = data[25] in (4, 6) or _has_chunk(data, b"tRNS")
    return [f"{width} × {height} px", "含透明通道" if alpha else "无透明通道"]


def _svg_facts(data: bytes) -> list[str]:
    colors = Counter(color.lower() for color in _COLOR.findall(data.decode("utf-8", "replace")))
    return ["颜色 " + " · ".join(color for color, _ in colors.most_common(3))] if colors else []


def _item(root: Path, member: tuple[str, str | None, str | None], notes: dict, ground: str) -> dict:
    ref, key, item_ground = member
    group, name = ref.split("/", 1)
    source = asset_source(root, group, name)
    data = source.read_bytes()
    suffix = source.suffix.lower()
    facts = [FORMATS[suffix], _size(len(data))]
    facts += _png_facts(ref, data) if suffix == ".png" else _svg_facts(data)
    note = notes.get(name) or (key and (notes.get(key) or notes.get(key.split("/", 1)[0])))
    if (item_ground or ground) not in GROUNDS:
        raise DesignSystemError(f"asset {ref}: ground must be one of {sorted(GROUNDS)}")
    return {"ref": ref, "name": name, "key": key, "note": inline(note) if note else None,
            "facts": facts, "ground": item_ground or ground, "source": source}


def _note_keys(member: tuple[str, str | None, str | None]) -> set[str]:
    ref, key, _ = member
    return {name for name in (ref.split("/", 1)[1], key, key and key.split("/", 1)[0]) if name}


def _group(group: dict, root: Path, notes: dict, matched: set[str]) -> dict:
    members = _members(group, root)
    if not members:
        raise DesignSystemError(f"asset group {group['id']}: lists no files")
    for member in members:
        matched |= _note_keys(member)
    return {
        "id": group["id"], "title": group["title"], "sources": _source_paths(group),
        "paragraphs": [inline(text) for text in group.get("paragraphs", [])],
        "items": [_item(root, member, notes, group.get("ground", "paper")) for member in members],
    }


def asset_gallery(content: dict, root: Path, used_assets: dict[str, Path]) -> dict[str, Any]:
    """The 图标与素材 context; adds every shown file to `used_assets` for publishing.

    `notes` is keyed by file name, semantic key, or the meaning part of a
    semantic key (before the "/"), shared by every variant of that meaning.
    """
    section = content["assets"]
    notes = section.get("notes", {})
    groups, seen, matched = [], set(), set()
    for group in section["groups"]:
        if not _ID.fullmatch(str(group["id"])) or group["id"] in seen:
            raise DesignSystemError(f"asset group {group['id']}: needs a unique id")
        seen.add(group["id"])
        groups.append(_group(group, root, notes, matched))
    stale = set(notes) - matched
    if stale:
        raise DesignSystemError(f"asset notes for {sorted(stale)} match no listed file")
    for group in groups:
        for item in group["items"]:
            used_assets[item["ref"]] = item.pop("source")
    return {
        "intro": [inline(text) for text in section.get("intro", [])],
        "steps": [inline(text) for text in section.get("steps", [])],
        "groups": groups, "count": sum(len(group["items"]) for group in groups),
    }


__all__ = ["ASSET_ROOTS", "REGISTRIES", "asset_gallery", "asset_source", "check_not_withdrawn", "withdrawn_hashes"]
