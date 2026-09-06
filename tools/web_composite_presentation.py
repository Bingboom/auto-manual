"""Bind frozen Web-composite assets to responsive semantic figures."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from tools.utils.path_utils import PathSegments
from tools.web_composite_hashing import (
    reference_source_fragment_sha256,
    semantic_source_fragment_sha256,
)
from tools.web_composite_manifest import (
    WebCompositeEntry,
    WebCompositeManifest,
    WebCompositeManifestError,
)


def _matches_source(source_path: Path, patterns: list[str]) -> bool:
    stem = source_path.stem.casefold()
    return any(fnmatch.fnmatch(stem, pattern.casefold()) for pattern in patterns)


def _supports_target_selectors(
    source_path: Path,
    selectors: list[dict[str, Any]],
) -> bool:
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
        for selector in selectors
    )


def supports_figure_contract(source_path: Path, contract: dict[str, Any]) -> bool:
    return _supports_target_selectors(source_path, contract["figure_targets"])


def supports_preface_contract(source_path: Path, contract: dict[str, Any]) -> bool:
    selectors = contract.get("preface", {}).get("targets", [])
    return _supports_target_selectors(source_path, selectors)


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
    language: str | None
    error_type: type[Exception]

    def resolve_locale(
        self, component: dict[str, Any], source_path: Path
    ) -> str | None:
        if str(component.get("composite_locale") or "").strip().casefold() == "shared":
            return "shared"
        mappings = [
            mapping
            for mapping in component.get("composite_locales", [])
            if isinstance(mapping, dict)
        ]
        requested_language = str(self.language or "").strip().casefold()
        if requested_language:
            language_matches = [
                str(mapping.get("locale") or "").strip()
                for mapping in mappings
                if str(mapping.get("locale") or "").strip().casefold()
                == requested_language
            ]
            language_matches = [value for value in language_matches if value]
            if len(language_matches) > 1:
                raise self.error_type(
                    f"{source_path}: Web composite document-language mapping is "
                    f"ambiguous: {language_matches}"
                )
            if language_matches:
                return language_matches[0]
        matches = [
            str(mapping.get("locale") or "").strip()
            for mapping in mappings
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

    def _locale(self, component: dict[str, Any], source_path: Path) -> str | None:
        """Compatibility alias retained until the final legacy-path cut."""

        return self.resolve_locale(component, source_path)

    def resolve_entry(
        self,
        component: dict[str, Any],
        source_path: Path,
    ) -> WebCompositeEntry | None:
        key = str(component.get("web_replace_key") or "").strip()
        locale = self.resolve_locale(component, source_path)
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

    def _entry(
        self, component: dict[str, Any], source_path: Path
    ) -> WebCompositeEntry | None:
        """Compatibility alias retained until the final legacy-path cut."""

        return self.resolve_entry(component, source_path)

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
        entry = self.resolve_entry(component, source_path)
        if entry is not None and entry.source_fragment_sha256 != source_fragment_sha256:
            raise self.error_type(
                f"{source_path}: Web composite source changed for {key!r}; "
                f"expected {entry.source_fragment_sha256}, got {source_fragment_sha256}"
            )
        if entry is not None:
            figure["class"] = [*figure.get("class", []), "hb-has-composite-art"]
            figure["data-web-composite-asset-key"] = entry.asset_key
            figure["data-web-composite-locale"] = entry.locale
            figure["data-web-composite-sha256"] = entry.content_sha256
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
            source_fragment_sha256=semantic_source_fragment_sha256(
                semantic, image_key=image_key
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
        source_hash = reference_source_fragment_sha256(
            component=component,
            semantic=semantic,
            caption_labels=caption_labels,
            composite_locale=self.resolve_locale(component, source_path),
        )
        self._append(
            soup=soup,
            figure=figure,
            component=component,
            source_path=source_path,
            source_fragment_sha256=source_hash,
        )


__all__ = (
    "WebCompositeContext",
    "supports_figure_contract",
    "supports_preface_contract",
)
