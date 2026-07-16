"""Resolve page-contract asset requirements through one shared contract.

Both ``check`` and bundle materialization use this resolver.  Legacy paths
keep their existing lookup order, while ``asset:<key>`` values are resolved
through the target-bound asset registry and its renderer-safe format policy.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from tools.asset_registry import AssetRegistryError
from tools.asset_usage import AssetTarget, BundleAssetUsage, parse_asset_uri
from tools.build_docs_resolve import render_build_template, slug_token

_CONTRACT_TOKEN_RE = re.compile(r"\{([a-z_]+)\}")


def render_contract_asset_value(
    raw_value: str,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> str:
    """Render contract tokens with the same rules as build output paths."""

    return render_build_template(
        raw_value,
        model=model,
        region=region,
        lang=lang,
        template_token_re=_CONTRACT_TOKEN_RE,
        slug_token=slug_token,
    )


class ContractAssetResolver:
    """Resolve legacy paths and registry URIs for one model/region target."""

    def __init__(
        self,
        *,
        docs_dir: Path,
        repo_root: Path,
        model: str | None,
        region: str | None,
        registry_path: Path | None = None,
        value_renderer: Callable[..., str] | None = None,
    ) -> None:
        self.docs_dir = docs_dir
        self.repo_root = repo_root
        self.model = model
        self.region = region
        self.registry_path = registry_path
        self.value_renderer = value_renderer or render_contract_asset_value
        self._usage: BundleAssetUsage | None = None

    def _registry_usage(self) -> BundleAssetUsage:
        if self._usage is not None:
            return self._usage
        if not (self.model or "").strip() or not (self.region or "").strip():
            raise AssetRegistryError(
                "contract asset URI resolution requires an explicit model and region"
            )
        self._usage = BundleAssetUsage(
            target=AssetTarget(
                model=self.model or "",
                region=self.region or "",
                language=None,
            ),
            repo_root=self.repo_root,
            registry_path=self.registry_path,
        )
        return self._usage

    def resolve(self, raw_value: str, *, lang: str | None) -> Path:
        rendered = self.value_renderer(
            raw_value,
            model=self.model,
            region=self.region,
            lang=lang,
        )
        if parse_asset_uri(rendered) is not None:
            frozen = self._registry_usage().resolve_reference(
                rendered,
                model=self.model,
                region=self.region,
                language=lang,
            )
            if frozen is None:  # pragma: no cover - guarded by parse_asset_uri
                raise AssetRegistryError(f"unresolved contract asset URI: {rendered!r}")
            return frozen.source_path

        candidate = Path(rendered)
        if candidate.is_absolute():
            return candidate
        docs_candidate = self.docs_dir / candidate
        if docs_candidate.exists():
            return docs_candidate
        return self.repo_root / candidate

    def exists(self, raw_value: str, *, lang: str | None) -> bool:
        try:
            return self.resolve(raw_value, lang=lang).is_file()
        except AssetRegistryError:
            return False


__all__ = (
    "ContractAssetResolver",
    "render_contract_asset_value",
)
