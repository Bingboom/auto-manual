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

from tools.component_specs.app_html import (
    parse_app_add_device_html,
    parse_app_download_html,
    parse_app_inline_control_html,
)
from tools.component_specs.fcc_html import parse_fcc_html
from tools.component_specs.inbox_html import parse_inbox_html
from tools.component_specs.lcd_mode_html import parse_lcd_mode_html
from tools.component_specs.manual_table_html import (
    parse_lcd_icon_html,
    parse_symbol_tables_html,
    parse_troubleshooting_html,
)
from tools.component_specs.model import ComponentSpec
from tools.component_specs.operation_html import parse_operation_components
from tools.component_specs.overview_html import parse_overview_html
from tools.component_specs.overview_instance import resolve_overview_instance
from tools.component_specs.registry import require_valid_component_spec
from tools.component_specs.reference_figure_html import parse_reference_figure_html
from tools.component_specs.warranty_html import parse_warranty_html
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION, html_to_flow_nodes
from tools.manual_ir.web_callouts import decode_callout_payload
from tools.manual_ir.web_specs import load_web_spec_source
from tools.utils.path_utils import repo_root
from tools.web_composite_presentation import (
    WebCompositeContext,
    supports_figure_contract,
    supports_preface_contract,
)
from tools.web_composite_manifest import WebCompositeManifest


_PLACEHOLDER_PREFIX = "AUTOMANUALIRCOMPONENT"


@dataclass(frozen=True)
class ComponentClaim:
    """One semantic owner and the exact contiguous source nodes it consumes."""

    spec: ComponentSpec
    owned_nodes: tuple[Tag, ...]
    asset_tags: tuple[tuple[str, Tag], ...] = ()
    asset_paths: tuple[tuple[str, Path], ...] = ()
    frozen_asset_paths: tuple[tuple[str, Path], ...] = ()
    discard_nodes: tuple[Tag, ...] = ()
    consume_interstitial: bool = False


def _matches_source(source_path: Path, patterns: Sequence[str]) -> bool:
    stem = source_path.stem.casefold()
    return any(fnmatch.fnmatch(stem, str(pattern).casefold()) for pattern in patterns)


def _matches_asset_source(source: str, image_key: str) -> bool:
    normalized = source.replace("\\", "/").casefold()
    key = image_key.replace("\\", "/").casefold()
    return bool(key) and (key in normalized or key.rsplit("/", 1)[-1] in normalized)


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
    for node in claim.discard_nodes:
        inside_current_claim = any(
            node is owner or owner in node.parents for owner in claim.owned_nodes
        )
        if _is_claimed(node, claimed) and not inside_current_claim:
            raise ValueError(
                f"{source_path}: overlapping semantic-only source node for "
                f"{claim.spec.component_id}"
            )
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
    declared_role: str | None = None,
    composite_manifest: WebCompositeManifest | None = None,
) -> tuple[ComponentClaim, ...]:
    """Discover registered families in deterministic ownership order."""

    claims: list[ComponentClaim] = []
    claimed: set[int] = set()

    if declared_role == "lcd_icons" or soup.select_one("table.hb-lcd-icon-table"):
        spec, boundary, images = parse_lcd_icon_html(
            soup,
            source_path=source_path,
            declared_page=declared_role == "lcd_icons",
            language=language,
        )
        claim = ComponentClaim(
            spec=spec,
            owned_nodes=(boundary,),
            asset_tags=tuple(("icons", image) for image in images),
        )
        _claim_nodes(claim, claimed=claimed, source_path=source_path)
        claims.append(claim)

    if (
        declared_role == "troubleshooting"
        or soup.select_one("table.hb-troubleshooting-table")
    ):
        spec, boundary, images = parse_troubleshooting_html(
            soup,
            source_path=source_path,
            declared_page=declared_role == "troubleshooting",
            language=language,
        )
        claim = ComponentClaim(
            spec=spec,
            owned_nodes=(boundary,),
            asset_tags=tuple(("icons", image) for image in images),
        )
        _claim_nodes(claim, claimed=claimed, source_path=source_path)
        claims.append(claim)

    meaning_symbols = contract["meaning_symbols"]
    if isinstance(meaning_symbols, Mapping) and (
        declared_role == "symbols"
        or _matches_source(source_path, meaning_symbols.get("source_patterns", []))
    ):
        parsed_symbol_claims = parse_symbol_tables_html(
            soup,
            source_path=source_path,
            expected_signal_rows=int(meaning_symbols["signal_row_count"]),
            language=language,
        )
        for spec, boundary, images in parsed_symbol_claims:
            claim = ComponentClaim(
                spec=spec,
                owned_nodes=(boundary,),
                asset_tags=tuple(("icons", image) for image in images),
            )
            _claim_nodes(claim, claimed=claimed, source_path=source_path)
            claims.append(claim)

    warranty_config = contract["warranty"]
    if isinstance(warranty_config, Mapping) and _matches_source(
        source_path, warranty_config.get("source_patterns", [])
    ):
        for spec, owned_nodes in parse_warranty_html(
            soup,
            source_path=source_path,
            expected_sections=int(warranty_config["section_count"]),
            expected_years=[str(value) for value in warranty_config["period_years"]],
            language=language,
        ):
            claim = ComponentClaim(spec=spec, owned_nodes=owned_nodes)
            _claim_nodes(claim, claimed=claimed, source_path=source_path)
            claims.append(claim)

    operation_config = contract["operations"]
    if isinstance(operation_config, Mapping) and _matches_source(
        source_path, operation_config.get("source_patterns", [])
    ):
        # The current operation presentation contract describes the approved
        # JE-1000F figure skeleton. Other skeletons retain their operation copy
        # as neutral flow until a matching presentation overlay is declared;
        # forcing this five-panel shape would either reject valid pages or drop
        # copy for panels that do not exist on that product.
        if supports_figure_contract(source_path, dict(contract)):
            for spec, owned_nodes, artwork, discard_nodes in parse_operation_components(
                soup,
                source_path=source_path,
                config=operation_config,
                language=language,
            ):
                claim = ComponentClaim(
                    spec=spec,
                    owned_nodes=owned_nodes,
                    asset_tags=(("artwork", artwork),),
                    discard_nodes=discard_nodes,
                )
                _claim_nodes(claim, claimed=claimed, source_path=source_path)
                claims.append(claim)
        lcd_config = operation_config["lcd_mode_table"]
        lcd_spec, lcd_table, lcd_artwork = parse_lcd_mode_html(
            soup,
            source_path=source_path,
            image_key=str(lcd_config["image_key"]),
            expected_body_rows=int(lcd_config["body_rows"]),
            language=language,
        )
        lcd_claim = ComponentClaim(
            spec=lcd_spec,
            owned_nodes=(lcd_table,),
            asset_tags=(("artwork", lcd_artwork),),
        )
        _claim_nodes(lcd_claim, claimed=claimed, source_path=source_path)
        claims.append(lcd_claim)

    supports_figures = supports_figure_contract(source_path, dict(contract))
    if supports_figures:
        app_download = contract["app_download"]
        if isinstance(app_download, Mapping) and _matches_source(
            source_path, app_download.get("source_patterns", [])
        ):
            spec, owned, asset_tags, asset_paths = parse_app_download_html(
                soup,
                source_path=source_path,
                config=app_download,
                language=language,
                model=model,
                region=region,
            )
            claim = ComponentClaim(
                spec=spec,
                owned_nodes=owned,
                asset_tags=asset_tags,
                asset_paths=asset_paths,
            )
            _claim_nodes(claim, claimed=claimed, source_path=source_path)
            claims.append(claim)

        app_inline = contract["app_inline_controls"]
        if isinstance(app_inline, Mapping) and _matches_source(
            source_path, app_inline.get("source_patterns", [])
        ):
            spec, owned = parse_app_inline_control_html(
                soup,
                source_path=source_path,
                config=app_inline,
                language=language,
            )
            claim = ComponentClaim(spec=spec, owned_nodes=owned)
            _claim_nodes(claim, claimed=claimed, source_path=source_path)
            claims.append(claim)

        reference_config = contract["reference_figures"]
        reference_context = WebCompositeContext(
            composite_manifest,
            model,
            region,
            language,
            ValueError,
        )
        for raw_reference in reference_config.get("figures", []):
            if not isinstance(raw_reference, Mapping) or not _matches_source(
                source_path, raw_reference.get("source_patterns", [])
            ):
                continue
            image_key = str(raw_reference.get("image_key") or "")
            images = [
                image
                for image in soup.find_all("img")
                if _matches_asset_source(str(image.get("src") or ""), image_key)
            ]
            if len(images) != 1:
                raise ValueError(
                    f"{source_path}: reference {raw_reference.get('id')!r} needs one "
                    f"governed image; found {len(images)}"
                )
            image = images[0]
            if raw_reference.get("presentation") == "shared-art-live-labels":
                spec, owned, asset_tags, asset_paths = parse_app_add_device_html(
                    soup,
                    source_path=source_path,
                    config=raw_reference,
                    language=language,
                )
                claim = ComponentClaim(
                    spec=spec,
                    owned_nodes=owned,
                    asset_tags=asset_tags,
                    asset_paths=asset_paths,
                )
            else:
                reference = dict(raw_reference)
                entry = reference_context.resolve_entry(reference, source_path)
                approved_path = None
                if entry is not None and composite_manifest is not None:
                    raw_path = Path(entry.path)
                    approved_path = (
                        raw_path
                        if raw_path.is_absolute()
                        else composite_manifest.source.parent / raw_path
                    )
                spec, owned, asset_tags, frozen_assets = parse_reference_figure_html(
                    soup,
                    image=image,
                    config=reference,
                    source_path=source_path,
                    language=language,
                    composite_locale=reference_context.resolve_locale(
                        reference, source_path
                    ),
                    approved_entry=entry,
                    approved_path=approved_path,
                )
                claim = ComponentClaim(
                    spec=spec,
                    owned_nodes=owned,
                    asset_tags=asset_tags,
                    frozen_asset_paths=frozen_assets,
                )
            _claim_nodes(claim, claimed=claimed, source_path=source_path)
            claims.append(claim)

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
    package_frozen_file: Callable[[Path], str] | None = None,
) -> ComponentSpec:
    bound: dict[str, list[str]] = {}
    for role, image in claim.asset_tags:
        bound.setdefault(role, []).append(package_image(image))
    for role, path in claim.asset_paths:
        bound.setdefault(role, []).append(package_file(path))
    frozen_packager = package_frozen_file or package_file
    for role, path in claim.frozen_asset_paths:
        bound.setdefault(role, []).append(frozen_packager(path))
    expected_counts: dict[str, int] = {}
    for asset in claim.spec.assets:
        expected_counts[asset.role] = expected_counts.get(asset.role, 0) + 1
    if {
        role: (expected_counts.get(role, 0), len(values))
        for role, values in bound.items()
        if expected_counts.get(role, 0) != len(values)
    } or any(role not in bound for role in expected_counts):
        raise ValueError(
            f"{claim.spec.source_ref}: component asset bindings do not match spec"
        )
    offsets: dict[str, int] = {}
    assets = []
    for asset in claim.spec.assets:
        index = offsets.get(asset.role, 0)
        candidates = bound.get(asset.role, [])
        asset_ref = candidates[index] if index < len(candidates) else asset.asset_ref
        offsets[asset.role] = index + 1
        assets.append(replace(asset, asset_ref=asset_ref))
    unused = {
        role: len(values) - offsets.get(role, 0)
        for role, values in bound.items()
        if len(values) != offsets.get(role, 0)
    }
    if unused:
        raise ValueError(
            f"{claim.spec.source_ref}: component asset bindings do not match spec: "
            f"{unused}"
        )
    return require_valid_component_spec(replace(claim.spec, assets=tuple(assets)))


def embed_component_claims(
    soup: BeautifulSoup,
    claims: Sequence[ComponentClaim],
    *,
    package_image: Callable[[Tag], str],
    package_file: Callable[[Path], str],
    package_frozen_file: Callable[[Path], str],
) -> tuple[dict, ...]:
    """Bind final assets, replace claimed tags, and return v2 flow roots."""

    replacements: dict[str, dict] = {}
    for index, claim in enumerate(claims, start=1):
        spec = _rebind_spec_assets(
            claim,
            package_image=package_image,
            package_file=package_file,
            package_frozen_file=package_frozen_file,
        )
        # Package non-semantic carrier images too. The semantic role binding
        # above runs first so the final role points to the exact rendered tag.
        for node in claim.owned_nodes:
            for image in node.select("img[src]"):
                if not str(image.get("src") or "").startswith("assets/ir/"):
                    package_image(image)
        discard_parents: list[Tag] = []
        for node in claim.discard_nodes:
            parent = node.parent
            if not isinstance(parent, Tag):
                raise ValueError(
                    f"{claim.spec.source_ref}: semantic-only source node detached "
                    "before embedding"
                )
            discard_parents.append(parent)
            node.extract()
        for parent in discard_parents:
            if parent.parent is not None and not parent.get_text(" ", strip=True):
                parent.decompose()
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
