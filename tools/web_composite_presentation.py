"""Bind frozen Web-composite assets to responsive semantic figures."""

from __future__ import annotations

import fnmatch
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from tools.utils.path_utils import PathSegments
from tools.web_composite_manifest import (
    WebCompositeEntry,
    WebCompositeManifest,
    WebCompositeManifestError,
)


def _matches_source(source_path: Path, patterns: list[str]) -> bool:
    stem = source_path.stem.casefold()
    return any(fnmatch.fnmatch(stem, pattern.casefold()) for pattern in patterns)


def supports_figure_contract(source_path: Path, contract: dict[str, Any]) -> bool:
    parts = list(source_path.parts)
    normalized = [part.casefold() for part in parts]
    target: tuple[str, str] | None = None
    for marker in (PathSegments.REVIEW, PathSegments.BUILD):
        try:
            marker_index = normalized.index(marker.casefold())
        except ValueError:
            continue
        if marker_index + 2 < len(parts):
            target = (parts[marker_index + 1], parts[marker_index + 2])
            break
    if target is None:
        return False
    model, region = target
    return any(
        model.casefold() == str(selector["model"]).casefold()
        and region.casefold() == str(selector["region"]).casefold()
        for selector in contract["figure_targets"]
    )


def _fragment_sha256(*values: object) -> str:
    payload = "\n".join(str(value) for value in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_fragment(fragment: Tag, *, image_key: str) -> str:
    normalized = BeautifulSoup(str(fragment), "html.parser")
    for image in normalized.find_all("img"):
        image["src"] = f"asset:{image_key}"
    return str(normalized)


def _composite_stage(soup: BeautifulSoup, artwork_path: str) -> Tag:
    stage = soup.new_tag(
        "div",
        attrs={"class": "hb-composite-stage", "aria-hidden": "true"},
    )
    stage.append(
        soup.new_tag(
            "img",
            attrs={
                "class": "hb-composite-art",
                "src": artwork_path,
                "alt": "",
                "loading": "lazy",
            },
        )
    )
    return stage


@dataclass(frozen=True)
class WebCompositeContext:
    """Target context used by every governed Web figure component."""

    manifest: WebCompositeManifest | None
    model: str | None
    region: str | None
    error_type: type[Exception]

    def _locale(self, component: dict[str, Any], source_path: Path) -> str | None:
        if str(component.get("composite_locale") or "").strip().casefold() == "shared":
            return "shared"
        matches = [
            str(mapping.get("locale") or "").strip()
            for mapping in component.get("composite_locales", [])
            if _matches_source(
                source_path,
                [str(value) for value in mapping.get("source_patterns", [])],
            )
        ]
        matches = [value for value in matches if value]
        if len(matches) > 1:
            raise self.error_type(
                f"{source_path}: Web composite locale mapping is ambiguous: {matches}"
            )
        return matches[0] if matches else None

    def _entry(
        self,
        component: dict[str, Any],
        source_path: Path,
    ) -> WebCompositeEntry | None:
        key = str(component.get("web_replace_key") or "").strip()
        locale = self._locale(component, source_path)
        if not key or not locale or self.manifest is None:
            return None
        try:
            return self.manifest.resolve(
                web_replace_key=key,
                locale=locale,
                model=self.model,
                region=self.region,
            )
        except WebCompositeManifestError as exc:
            raise self.error_type(str(exc)) from exc

    def _append(
        self,
        *,
        soup: BeautifulSoup,
        figure: Tag,
        component: dict[str, Any],
        source_path: Path,
        source_fragment_sha256: str,
    ) -> None:
        key = str(component.get("web_replace_key") or "").strip()
        if key:
            figure["data-web-replace-key"] = key
        figure["data-source-fragment-sha256"] = source_fragment_sha256
        entry = self._entry(component, source_path)
        if entry is not None and entry.source_fragment_sha256 != source_fragment_sha256:
            raise self.error_type(
                f"{source_path}: Web composite source changed for {key!r}; "
                f"expected {entry.source_fragment_sha256}, got {source_fragment_sha256}"
            )
        if entry is not None:
            figure["class"] = [*figure.get("class", []), "hb-has-composite-art"]
            figure.append(_composite_stage(soup, entry.path))

    def append_semantic(
        self,
        *,
        soup: BeautifulSoup,
        figure: Tag,
        semantic: Tag,
        component: dict[str, Any],
        source_path: Path,
        image_key: str,
    ) -> None:
        self._append(
            soup=soup,
            figure=figure,
            component=component,
            source_path=source_path,
            source_fragment_sha256=_fragment_sha256(
                _normalized_fragment(semantic, image_key=image_key)
            ),
        )

    def append_reference(
        self,
        *,
        soup: BeautifulSoup,
        figure: Tag,
        semantic: Tag,
        component: dict[str, Any],
        source_path: Path,
        caption_labels: list[str],
    ) -> None:
        if self._locale(component, source_path) == "shared":
            source_hash = _fragment_sha256(
                str(component["id"]),
                str(component["image_key"]),
                bool(component.get("captions_embedded")),
                int(component.get("capture_following_lines") or 0),
            )
        else:
            source_hash = _fragment_sha256(
                _normalized_fragment(
                    semantic,
                    image_key=str(component["image_key"]),
                ),
                "\n".join(caption_labels),
            )
        self._append(
            soup=soup,
            figure=figure,
            component=component,
            source_path=source_path,
            source_fragment_sha256=source_hash,
        )


__all__ = ("WebCompositeContext", "supports_figure_contract")
