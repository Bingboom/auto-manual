"""四类资产's curated data (``asset_layers.yaml``): wording, ledger-derived status chips, the regrouped capability
map and the staged path.

- **Wording.** ``umbrella`` (the umbrella term), ``main_line`` (the main-line statement) and ``product_value`` (the
  operator's statement of the product matrix's value, the 产品信息 lead) are each kept once, so a change is one line.
- **Status chips.** A layer's chip is never hand-set: its ``revs`` are execution-ledger rows, read the way 系统建设
  reads them (``system_workspace.ledger_progress``), and the rows' state maps to one portal status word
  (``CHIP_STATUS``). A layer without rows, or whose rows are all deferred, gets no chip. A REV id the ledger lacks
  is an authoring error.
- **Capability map.** ``items`` regroup 系统建设's capability items under the four layers and ``production`` keeps
  whole cards as the 生产 row. Regrouping only moves items: each keeps its own status and evidence; every item of a
  regrouped card is placed exactly once and every card is either regrouped or kept.
- **Staged path.** Positioning §4.2: a stage with ledger rows carries their chip; a stage without one shows only the
  quoted direction and a link, with no status (the portal rule that a planned item cites a ledger row).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from tools.rtd.system_workspace import STATUS_LABELS, Ledger, expand_revs, ledger_progress, status_counts

DATA_NAME = "asset_layers.yaml"
SCHEMA = "hello-docs-asset-layers/v1"
LAYER_IDS = ("product", "content", "media", "language")
# ledger_progress state -> portal status word; "deferred" (every row deferred) shows no chip.
CHIP_STATUS = {"done": "validated", "active": "in_progress", "idle": "planned"}


class LayerDataError(ValueError):
    pass


def _text(data: dict[str, Any], key: str) -> str:
    value = str(data.get(key) or "").strip()
    if not value:
        raise LayerDataError(f"{DATA_NAME}: needs {key}")
    return value


def load_layer_data(assets: Path) -> dict[str, Any]:
    """The validated data file; a malformed one raises LayerDataError."""
    try:
        data = yaml.safe_load((assets / DATA_NAME).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LayerDataError(f"cannot read {DATA_NAME}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise LayerDataError(f"{DATA_NAME}: schema must be {SCHEMA}")
    layers = data.get("layers") or {}
    if set(layers) != set(LAYER_IDS):
        raise LayerDataError(f"{DATA_NAME}: layers must be exactly {LAYER_IDS}")
    try:
        revs = {layer: expand_revs(layers[layer]["revs"]) if layers[layer].get("revs") else [] for layer in LAYER_IDS}
        stages = [{**stage, "revs": expand_revs(stage["revs"]) if stage.get("revs") else []}
                  for stage in (data.get("path") or {}).get("stages") or []]
    except (TypeError, KeyError, ValueError) as exc:
        raise LayerDataError(f"{DATA_NAME}: {exc}") from exc
    for stage in stages:
        if not stage.get("title") or not stage.get("quote"):
            raise LayerDataError(f"{DATA_NAME}: path stage {stage.get('id')} needs a title and a quote")
    return {"umbrella": _text(data, "umbrella"), "main_line": _text(data, "main_line"),
            "product_value": _text(data, "product_value"),
            "source": _text(data, "source"), "revs": revs,
            "items": {layer: list(layers[layer].get("items") or []) for layer in LAYER_IDS},
            "production": list(data.get("production") or []),
            "path": {**(data.get("path") or {}), "stages": stages}}


def _missing(revs: list[str], ledger: Ledger) -> list[str]:
    return [rev for rev in revs if rev not in ledger.statuses]


def chip(revs: list[str], ledger: Ledger | None) -> dict[str, Any] | None:
    """A status chip from ledger rows: the portal word, the rows and their tally; None without rows or ledger."""
    if not revs or ledger is None:
        return None
    if _missing(revs, ledger):
        raise LayerDataError(f"{DATA_NAME}: the ledger has no row {', '.join(_missing(revs, ledger))}")
    progress = ledger_progress(revs, ledger)
    status = CHIP_STATUS.get(progress["state"])
    if status is None:
        return None
    return {"status": status, "status_label": STATUS_LABELS[status], "revs": revs, "tally": progress["tally"]}


def layer_chips(data: dict[str, Any], ledger: Ledger | None) -> dict[str, dict[str, Any] | None]:
    return {layer: chip(data["revs"][layer], ledger) for layer in LAYER_IDS}


def _placed_entries(data: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Each layer's capability entries, in the data file's order; an unknown or twice-placed item is an error."""
    placed: set[str] = set()
    layers: dict[str, list[dict[str, Any]]] = {}
    for layer in LAYER_IDS:
        layers[layer] = []
        for ref in data["items"][layer]:
            card_id, _, item_id = ref.partition(".")
            entries = (by_id.get(card_id) or {}).get("entries") or []
            entry = next((e for e in entries if e.get("id") == item_id), None)
            if entry is None or ref in placed:
                raise LayerDataError(f"{DATA_NAME}: capability item {ref} is unknown or placed twice")
            placed.add(ref)
            layers[layer].append({**entry, "card": card_id})
    return layers


def capability_map(data: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    """系统建设's capability cards regrouped: four layers of items, then the production cards kept whole."""
    by_id = {card["id"]: card for card in cards}
    placed = _placed_entries(data, by_id)
    refs = {f"{entry['card']}.{entry['id']}" for entries in placed.values() for entry in entries}
    regrouped = {ref.partition(".")[0] for ref in refs}
    for card_id in regrouped:
        unplaced = [e["id"] for e in by_id[card_id]["entries"] if f"{card_id}.{e['id']}" not in refs]
        if unplaced:
            raise LayerDataError(f"{DATA_NAME}: {card_id} items {unplaced} are not placed in any layer")
    production = [by_id[card_id] for card_id in data["production"] if card_id in by_id]
    if set(by_id) != regrouped | {card["id"] for card in production} or regrouped & set(data["production"]):
        raise LayerDataError(f"{DATA_NAME}: every capability card must be regrouped or kept whole, not both")
    layers = {layer: {"entries": entries, "counts": status_counts(entries) if entries else [], "anchors": []}
              for layer, entries in placed.items()}
    for card_id in sorted(regrouped):  # an old card id anchors on the layer that holds most of its items
        held = [sum(entry["card"] == card_id for entry in placed[layer]) for layer in LAYER_IDS]
        layers[LAYER_IDS[held.index(max(held))]]["anchors"].append(card_id)
    return {"layers": layers, "production": production}


def path_view(data: dict[str, Any], ledger: Ledger | None, source_url: str) -> dict[str, Any]:
    """The staged path: each stage's chip from its rows, else its quote only."""
    path = data["path"]
    link = f"{source_url}#{path.get('anchor')}" if path.get("anchor") else source_url
    return {"link": link, "boundary": str(path.get("boundary") or ""),
            "stages": [{"id": stage.get("id"), "title": stage["title"], "quote": stage["quote"],
                        "scope": str(stage.get("scope") or ""), "chip": chip(stage["revs"], ledger)}
                       for stage in path["stages"]]}


__all__ = ["CHIP_STATUS", "DATA_NAME", "LAYER_IDS", "LayerDataError", "capability_map", "chip", "layer_chips",
           "load_layer_data", "path_view"]
