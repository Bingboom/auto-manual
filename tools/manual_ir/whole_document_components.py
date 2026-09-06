"""Extract registered components into ordered whole-document flow.

The existing scoped HTML parsers remain the source adapters. This module owns
their whole-document claim ordering, overlap checks, packaged-asset binding and
placeholder replacement; it does not introduce a second semantic scraper.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import fnmatch
from pathlib import Path
from typing import Callable, Mapping, Sequence

from bs4 import BeautifulSoup, Comment, Tag

from tools.component_specs.fcc_html import parse_fcc_html
from tools.component_specs.inbox_html import parse_inbox_html
from tools.component_specs.model import ComponentAsset, ComponentSpec
from tools.component_specs.overview_html import parse_overview_html
from tools.component_specs.overview_instance import resolve_overview_instance
from tools.component_specs.registry import require_valid_component_spec
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION, html_to_flow_nodes
from tools.manual_ir.web_callouts import decode_callout_payload
from tools.manual_ir.web_specs import load_web_spec_source
from tools.utils.path_utils import repo_root
from tools.web_composite_presentation import (
    supports_figure_contract,
    supports_preface_contract,
)


_PLACEHOLDER_PREFIX = "AUTOMANUALIRCOMPONENT"


@dataclass(frozen=True)
class ComponentClaim:
    """One semantic owner and the exact contiguous source nodes it consumes."""

    spec: ComponentSpec
    owned_nodes: tuple[Tag, ...]
    asset_tags: tuple[tuple[str, Tag], ...] = ()
    asset_paths: tuple[tuple[str, Path], ...] = ()
    consume_interstitial: bool = False


def _matches_source(source_path: Path, patterns: Sequence[str]) -> bool:
    stem = source_path.stem.casefold()
    return any(fnmatch.fnmatch(stem, str(pattern).casefold()) for pattern in patterns)


def _is_claimed(node: Tag, claimed: set[int]) -> bool:
    return any(id(candidate) in claimed for candidate in (node, *node.parents))


def _claim_nodes(
    claim: ComponentClaim,
    *,
    claimed: set[int],
    source_path: Path,
) -> None:
    if not claim.owned_nodes:
        raise ValueError(f"{source_path}: component claim cannot be empty")
    positions = []
    parent = claim.owned_nodes[0].parent
    if parent is None or any(node.parent is not parent for node in claim.owned_nodes):
        raise ValueError(
            f"{source_path}: component {claim.spec.component_id} claim must share one parent"
        )
    tag_siblings = [child for child in parent.children if isinstance(child, Tag)]
    for node in claim.owned_nodes:
        if _is_claimed(node, claimed):
            raise ValueError(
                f"{source_path}: overlapping component claim for {claim.spec.component_id}"
            )
        positions.append(tag_siblings.index(node))
    if positions != list(range(positions[0], positions[0] + len(positions))):
        raise ValueError(
            f"{source_path}: component {claim.spec.component_id} claim is not contiguous"
        )
    for node in claim.owned_nodes:
        claimed.add(id(node))
        claimed.update(id(descendant) for descendant in node.find_all(True))


def discover_registered_components(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: Mapping[str, object],
    model: str,
    region: str,
    language: str,
) -> tuple[ComponentClaim, ...]:
    """Discover the five registered families in deterministic ownership order."""

    claims: list[ComponentClaim] = []
    claimed: set[int] = set()

    overview_config = contract["product_overview"]
    if (
        isinstance(overview_config, Mapping)
        and _matches_source(source_path, overview_config.get("source_patterns", []))
        and supports_figure_contract(source_path, dict(contract))
    ):
        instance = resolve_overview_instance(model=model, region=region)
        parsed = parse_overview_html(
            soup,
            source_path=source_path,
            instance=instance,
            error_type=ValueError,
            language=language,
        )
        claim = ComponentClaim(
            spec=parsed.spec,
            owned_nodes=tuple(view.section for view in parsed.views),
            asset_tags=tuple(
                (asset.role, view.image)
                for asset, view in zip(parsed.spec.assets, parsed.views, strict=True)
            ),
            consume_interstitial=True,
        )
        _claim_nodes(claim, claimed=claimed, source_path=source_path)
        claims.append(claim)

    fcc_config = contract["fcc"]
    if (
        isinstance(fcc_config, Mapping)
        and _matches_source(source_path, fcc_config.get("source_patterns", []))
        and supports_preface_contract(source_path, dict(contract))
    ):
        parsed = parse_fcc_html(
            soup,
            source_path=source_path,
            config=fcc_config,
            error_type=ValueError,
            language=language,
        )
        mark_path = Path(str(fcc_config["mark_path"]))
        if not mark_path.is_absolute():
            mark_path = repo_root() / mark_path
        claim = ComponentClaim(
            spec=parsed.spec,
            owned_nodes=parsed.consumed_nodes,
            asset_paths=((parsed.spec.assets[0].role, mark_path),),
            consume_interstitial=True,
        )
        _claim_nodes(claim, claimed=claimed, source_path=source_path)
        claims.append(claim)

    inbox_config = contract["in_the_box"]
    semantic_inbox = isinstance(inbox_config, Mapping) and _matches_source(
        source_path, inbox_config.get("semantic_source_patterns", [])
    )
    legacy_inbox = (
        isinstance(inbox_config, Mapping)
        and _matches_source(source_path, inbox_config.get("source_patterns", []))
        and (
            supports_preface_contract(source_path, dict(contract))
            or supports_figure_contract(source_path, dict(contract))
        )
    )
    if semantic_inbox or legacy_inbox:
        parsed = parse_inbox_html(
            soup,
            source_path=source_path,
            language=language,
            error_type=ValueError,
        )
        images = parsed.inbox_table.select("img[src]")
        claim = ComponentClaim(
            spec=parsed.spec,
            owned_nodes=(parsed.inbox_table, parsed.tip_table),
            asset_tags=tuple(
                (asset.role, image)
                for asset, image in zip(parsed.spec.assets, images, strict=True)
            ),
        )
        _claim_nodes(claim, claimed=claimed, source_path=source_path)
        claims.append(claim)

    specification_index = 0
    for heading in list(soup.select("h2.hb-spec-section")):
        if _is_claimed(heading, claimed):
            continue
        table = heading.find_next_sibling()
        if not isinstance(table, Tag) or _is_claimed(table, claimed):
            raise ValueError(
                f"{source_path}: declared specification has no unclaimed adjacent table"
            )
        specification_index += 1
        source = load_web_spec_source(
            str(heading) + str(table),
            source_path=source_path,
            language=language,
            model=model,
            region=region,
        )
        if source is None or len(source.pages[0].blocks) != 1:
            raise ValueError(f"{source_path}: specification projection is ambiguous")
        payload = source.pages[0].blocks[0][1]
        spec = require_valid_component_spec(
            ComponentSpec.from_dict(payload["component_spec"])
        )
        spec = require_valid_component_spec(
            replace(
                spec,
                source_ref=f"{source_path}#specification-{specification_index}",
            )
        )
        claim = ComponentClaim(spec=spec, owned_nodes=(heading, table))
        _claim_nodes(claim, claimed=claimed, source_path=source_path)
        claims.append(claim)

    callout_index = 0
    for table in list(soup.select("table.manual-callout-table")):
        if _is_claimed(table, claimed):
            continue
        callout_index += 1
        source_ref = f"{source_path}#callout-{callout_index}"
        payload = decode_callout_payload(str(table), source_ref=source_ref)
        spec = require_valid_component_spec(
            ComponentSpec.from_dict(payload["component_spec"])
        )
        claim = ComponentClaim(spec=spec, owned_nodes=(table,))
        _claim_nodes(claim, claimed=claimed, source_path=source_path)
        claims.append(claim)

    return tuple(claims)


def _rebind_spec_assets(
    claim: ComponentClaim,
    *,
    package_image: Callable[[Tag], str],
    package_file: Callable[[Path], str],
) -> ComponentSpec:
    bound: dict[str, str] = {}
    for role, image in claim.asset_tags:
        bound[role] = package_image(image)
    for role, path in claim.asset_paths:
        bound[role] = package_file(path)
    assets = tuple(
        replace(asset, asset_ref=bound.get(asset.role, asset.asset_ref))
        for asset in claim.spec.assets
    )
    return require_valid_component_spec(replace(claim.spec, assets=assets))


def embed_component_claims(
    soup: BeautifulSoup,
    claims: Sequence[ComponentClaim],
    *,
    package_image: Callable[[Tag], str],
    package_file: Callable[[Path], str],
) -> tuple[dict, ...]:
    """Bind final assets, replace claimed tags, and return v2 flow roots."""

    replacements: dict[str, dict] = {}
    for index, claim in enumerate(claims, start=1):
        spec = _rebind_spec_assets(
            claim,
            package_image=package_image,
            package_file=package_file,
        )
        # Package non-semantic carrier images too. The semantic role binding
        # above runs first so the final role points to the exact rendered tag.
        for node in claim.owned_nodes:
            for image in node.select("img[src]"):
                if not str(image.get("src") or "").startswith("assets/ir/"):
                    package_image(image)
        carrier_nodes: list[object]
        if claim.consume_interstitial:
            parent = claim.owned_nodes[0].parent
            if parent is None or claim.owned_nodes[-1].parent is not parent:
                raise ValueError(
                    f"{claim.spec.source_ref}: component claim detached before embedding"
                )
            siblings = list(parent.children)
            first_index = siblings.index(claim.owned_nodes[0])
            last_index = siblings.index(claim.owned_nodes[-1])
            carrier_nodes = siblings[first_index : last_index + 1]
        else:
            carrier_nodes = list(claim.owned_nodes)
        carrier = html_to_flow_nodes("".join(str(node) for node in carrier_nodes))
        token = f"{_PLACEHOLDER_PREFIX}{index:04d}"
        replacements[token] = component_flow_node(spec, carrier_flow=carrier)
        claim.owned_nodes[0].replace_with(Comment(token))
        for node in carrier_nodes[1:]:
            if claim.consume_interstitial or isinstance(node, Tag):
                node.extract()

    roots = [dict(node) for node in html_to_flow_nodes(str(soup))]
    seen: set[str] = set()

    def substitute(node: dict) -> dict:
        if node.get("kind") == "comment" and node.get("text") in replacements:
            token = str(node["text"])
            if token in seen:
                raise ValueError(f"duplicate component placeholder: {token}")
            seen.add(token)
            return replacements[token]
        if "children" in node:
            node["children"] = [substitute(dict(child)) for child in node["children"]]
        return node

    result = []
    for root in roots:
        root = substitute(root)
        root["schema_version"] = FLOW_V2_SCHEMA_VERSION
        result.append(root)
    missing = set(replacements) - seen
    if missing:
        raise ValueError(f"missing component placeholder(s): {sorted(missing)}")
    return tuple(result)


__all__ = [
    "ComponentClaim",
    "discover_registered_components",
    "embed_component_claims",
]
