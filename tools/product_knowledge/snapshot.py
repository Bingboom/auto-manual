"""Read-only, versioned product knowledge from frozen publication inputs.

One record describes one published model/market/language/version.  The existing
matrix still chooses one preferred manual for its overview; this interface never
transfers that manual's figures to another market.  Extraction and placement use
the matrix implementation, while every value retains its own authority.

``settings`` and ``catalog`` are already-loaded frozen inputs.  Every recorded
input names its path, the base that path is relative to (``repository`` or
``web_source``) and what its hash covers: file bytes, or for the catalog parsed
from the Web source's ``index.md`` its canonical JSON.  No wall clock, network,
source-table writes or repository mutations participate in this interface.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath
import re
from typing import Any
from urllib.parse import quote

from tools.manual_knowledge.identity import variant_identity
from tools.rtd import product_matrix as matrix
from tools.rtd.production_evidence import publication_targets
from tools.rtd.system_data import CAPABILITIES_CSV, LANGUAGES_CSV, read_targets
from tools.utils.path_utils import Paths, PathSegments

SCHEMA_VERSION = "product-knowledge/v1"
SETTINGS = "settings.json"
# Registry evidence carries this repository-relative path; downstream checks bind to it.
REGISTRY_PATH = PurePosixPath(PathSegments.DATA, CAPABILITIES_CSV).as_posix()
_SPECS = {
    "capacity_wh": ("wh", "Wh"), "ac_output_w": ("ac", "W"),
    "ac_surge_w": ("surge", "W"), "weight_kg": ("kg", "kg"),
    "cycle_life": ("cycles", "cycles"), "solar_peak_w": ("pv", "W"),
    "ip_rating": ("ip", None), "output_w": ("out", "W"),
}
# What a research rule may require of a manual: figures, not the textual IP rating.
NUMERIC_FACTS = tuple(key for key in _SPECS if key != "ip_rating")


def _digest(value: Any) -> str:
    data = value if isinstance(value, bytes) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _file_hash(path: Path) -> str | None:
    return _digest(path.read_bytes()) if path.is_file() else None


def _relative(base: Path, path: Path) -> str:
    """``path`` below ``base`` in POSIX form, or its bare name outside ``base``."""
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.name


def _input(path: str, base: str, digest: str | None, hash_of: str = "bytes") -> dict:
    return {"path": path, "base": base, "hash_of": hash_of, "sha256": digest}


def _whole(value: Any) -> Any:
    """1024.0 → 1024: the matrix parses figures as floats; consumers read whole numbers."""
    return int(value) if isinstance(value, float) and value.is_integer() else value


def _fact(value: Any, kind: str, evidence: list[dict], *, unit: str | None = None,
          reason: str = "Not stated or not extractable from this published manual") -> dict:
    known = value is not None and value != ""
    return {"value": value if known else None, "unit": unit, "state": "known" if known else "unknown",
            "source_type": kind, "evidence": evidence if known else [], "reason": None if known else reason}


def _evidence(kind: str, path: str, digest: str | None, locator: str, text: str,
              url: str | None = None) -> dict:
    return {"source_type": kind, "path": path, "url": url, "sha256": digest,
            "locator": locator, "quote": text}


def _curated(source: dict, locator: str, entry: Any) -> dict:
    return _evidence("curated_configuration", source["path"], source["sha256"], locator,
                     json.dumps(entry, ensure_ascii=False, sort_keys=True))


def _source_path(srcdir: Path, target: dict) -> Path:
    route, manual = PurePosixPath(target["route"]), PurePosixPath(target["manual"])
    if (route.is_absolute() or manual.is_absolute() or len(manual.parts) != 1
            or ".." in route.parts or "\\" in target["route"] or "\\" in target["manual"]):
        raise ValueError("Unsafe product knowledge publication route")
    path = (srcdir / route / manual).resolve()
    if not path.is_relative_to(srcdir.resolve()):
        raise ValueError("Product knowledge publication escapes the frozen source")
    return path


def _manifest(path: Path) -> tuple[list[dict], dict]:
    """Sorted targets plus the manifest's byte hash and build time, read once."""
    try:
        data = path.read_bytes()
        manifest = json.loads(data)
        targets = publication_targets(manifest)
    except OSError as exc:
        raise ValueError(f"Publication manifest {path.name} is unreadable: {exc.strerror}") from exc
    except ValueError as exc:
        raise ValueError(f"Publication manifest {path.name} is malformed: {exc}") from exc
    ordered = sorted(targets, key=lambda row: tuple(row[key] for key in ("model", "region", "lang", "route")))
    return ordered, {"sha256": _digest(data), "built_at": manifest.get("built_at")}


def _registry(root: Path, warnings: list[str]) -> tuple[list[str], dict, list[dict]]:
    paths = Paths(root)
    capabilities, languages = paths.data_dir / CAPABILITIES_CSV, paths.data_dir / LANGUAGES_CSV
    inputs = [_input(_relative(root, path), "repository", _file_hash(path)) for path in (capabilities, languages)]
    names: list[str] = []
    try:
        with capabilities.open(encoding="utf-8-sig", newline="") as handle:
            names = [name for name in next(csv.reader(handle), []) if name not in ("Document_key", "Project")]
        # Only the switches are read here, so the review-page count is skipped.
        names, rows = read_targets(capabilities, languages, None)
        by_target = {(row["model"], row["region"]): row for row in rows}
        if len(by_target) != len(rows):
            raise ValueError("Duplicate capability registry model/region")
        return names, by_target, inputs
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as exc:
        detail = exc.strerror if isinstance(exc, OSError) else str(exc)
        warnings.append(f"Capability registry unavailable: {type(exc).__name__}: {detail}")
        return names, {}, inputs


def _category(product: dict, target: dict, config: dict, settings: dict,
              curated: dict, manual_evidence: dict) -> dict:
    model, group = target["model"], product["group"]
    navigation = settings.get("navigation") or {}
    evidence = []
    if group is not None:
        if not product["inferred"]:
            entry = next(row for rows in navigation.values() for row in rows
                         if row["id"] == group and model in row.get("models", []))
            evidence.append(_curated(curated["settings"], f"navigation/{group}", entry))
        else:
            evidence.append(_curated(curated["config"], f"assign/{model}", config["assign"][model]))
            if product["basis"]:
                evidence.append({**manual_evidence, "locator": "classification evidence", "quote": product["basis"]})
    return _fact(group, "curated_configuration", evidence,
                 reason="No verified placement for this publication in the product matrix")


def _specifications(product: dict, pairs: list[tuple[str, str]], manual_evidence: dict) -> dict:
    parsed = [(label, value, matrix.read_specs([(label, value)])) for label, value in pairs]
    result = {}
    for key, (matrix_key, unit) in _SPECS.items():
        value = product[matrix_key]
        evidence = [{**manual_evidence, "locator": f"specifications/{label}", "quote": f"{label}: {text}"}
                    for label, text, fields in parsed
                    if value is not None and value != "" and fields[matrix_key] == value]
        result[key] = _fact(_whole(value), "published_manual", evidence, unit=unit)
    return result


def _relations(product: dict, text: str, config: dict, warnings: list[str], manual_evidence: dict,
               curated: dict) -> list[dict]:
    model = product["model"]
    relevant = {**config, "pairings": [entry for entry in config.get("pairings", []) if entry["model"] == model]}
    pairings = matrix.pairings({model: product}, {model: text}, relevant, warnings)
    labels = {label for row in pairings for kind in ("parts", "solar") for label in row[kind]}
    relations = []
    for entry in relevant["pairings"]:
        for kind in ("parts", "solar"):
            for item in entry.get(kind, []):
                label = item if isinstance(item, str) else item["label"]
                match = item if isinstance(item, str) else item.get("match") or item["label"]
                checked_match = re.sub(r"（.*?）", "", match).strip()
                excerpt = matrix.evidence_excerpt(text, checked_match)
                if label in labels and excerpt:
                    kind_of_source = "published_manual" if label == checked_match else "curated_configuration"
                    evidence = [{**manual_evidence, "locator": "named product", "quote": excerpt}]
                    if kind_of_source == "curated_configuration":
                        evidence.insert(0, _curated(curated["config"], f"pairings/{model}/{kind}", item))
                    relations.append({"kind": "named_companion", "label": label, "state": "known",
                                      "source_type": kind_of_source, "evidence": evidence})
    return relations


def _product(srcdir: Path, target: dict, lookups: tuple, config: dict, settings: dict,
             curated: dict, registry: tuple, warnings: list[str]) -> tuple[dict, dict]:
    path = _source_path(srcdir, target)
    data = path.read_bytes() if path.is_file() else None
    if data is None:
        warnings.append(f"{target['model']}: published manual {target['route']}/{target['manual']} is not readable")
    # The one read serves every fact; newlines follow text mode, as on the matrix page.
    markup = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n") if data else ""
    pairs = matrix.spec_pairs(markup)
    product, text = matrix.product_row(target["model"], [target], target, markup, *lookups, config, warnings, pairs)
    source_relative = (PurePosixPath(target["route"]) / target["manual"]).as_posix()
    digest = _digest(data) if data is not None else None
    source = {"route": target["route"], "manual": target["manual"],
              "url": quote(str(PurePosixPath(source_relative).with_suffix(".html")), safe="/") if data is not None else None,
              "sha256": digest, "built_at": target.get("built_at"),
              "git_ref": target.get("git_ref"), "language_scope": target.get("language_scope", "legacy_unspecified")}
    evidence = _evidence("published_manual", source_relative, digest, "", "", source["url"])
    names, registry_rows, registry_inputs = registry
    row = registry_rows.get((target["model"], target["region"]))
    capabilities = {}
    for index, name in enumerate(names):
        value = bool(row["caps"][index]) if row else None
        capabilities[name] = _fact(value, "capability_registry", [
            _evidence("capability_registry", registry_inputs[0]["path"], registry_inputs[0]["sha256"],
                      f"{row['key']}/{name}", f"{name}: {'TRUE' if value else 'FALSE'}")
        ] if row else [], reason="No usable capability registry row for this model and market")
    category = _category(product, target, config, settings, curated, evidence)
    specs = _specifications(product, pairs, evidence)
    identity = variant_identity(model=target["model"], region=target["region"], lang=target["lang"],
                                version=target.get("version"))
    unknowns = [{"field": f"{family}.{key}", "reason": fact["reason"]}
                for family, fields in (("specifications", specs), ("capabilities", capabilities))
                for key, fact in fields.items() if fact["state"] == "unknown"]
    if not names:
        unknowns.append({"field": "capabilities", "reason": "Capability registry columns are unavailable"})
    if category["state"] == "unknown":
        unknowns.append({"field": "category", "reason": category["reason"]})
    if source["language_scope"] != "single":
        unknowns.append({"field": "language", "reason": "Legacy publication does not verify a single-language edition"})
    if identity["publication_version"] is None:
        unknowns.append({"field": "version", "reason": "Publication manifest does not state a version"})
    result = {"id": identity["manual_variant_id"], "model": target["model"], "region": target["region"],
              "language": target["lang"], "version": identity["publication_version"], "name": product["name"],
              "source": source, "category": category, "specifications": specs, "capabilities": capabilities,
              "relations": _relations(product, text, config, warnings, evidence, curated),
              "unknowns": unknowns}
    return result, _input(source_relative, "web_source", digest)


def _edition_warnings(editions: dict[str, list[tuple[str, list[str]]]]) -> list[str]:
    """A message every edition of a model raised appears once; any other names its editions."""
    result = []
    for rows in editions.values():
        raised: dict[str, list[str]] = {}
        for variant, messages in rows:
            for message in messages:
                variants = raised.setdefault(message, [])
                if variant not in variants:
                    variants.append(variant)
        result.extend(message if len(variants) == len(rows) else f"{message} [{', '.join(variants)}]"
                      for message, variants in raised.items())
    return result


def build_product_knowledge(root: Path, srcdir: Path, manifest_path: Path, assets: Path,
                            settings: dict, catalog: list[dict]) -> dict:
    """Build a deterministic v1 snapshot; missing facts remain explicitly unknown.

    ``srcdir`` is the frozen Web source directory (not rendered HTML), and only
    targets of the manifest at ``manifest_path`` are eligible; an unreadable or
    malformed manifest raises ValueError. ``assets`` holds the portal's
    ``product_matrix.json`` and ``settings.json`` (``settings`` is the latter,
    parsed). The caller may serialize this return value unchanged for RTD, an
    Agent, or a separate downstream application.
    """
    targets, manifest = _manifest(manifest_path)
    config = matrix.load_config(assets, settings)
    curated = {name: {"path": _relative(root, assets / file), "sha256": _file_hash(assets / file)}
               for name, file in (("config", matrix.CONFIG), ("settings", SETTINGS))}
    warnings: list[str] = []
    registry = _registry(root, warnings)
    inputs = [*(_input(item["path"], "repository", item["sha256"]) for item in curated.values()),
              _input("index.md", "web_source", _digest(catalog), "parsed_catalog"), *registry[2]]
    lookups = (matrix.catalog_names(catalog), matrix.placements(config))
    products, seen = [], set()
    editions: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    for target in targets:
        raised: list[str] = []
        product, source = _product(srcdir, target, lookups, config, settings, curated, registry, raised)
        if product["id"] in seen:
            raise ValueError(f"Duplicate product knowledge identity: {product['id']}")
        seen.add(product["id"])
        products.append(product)
        inputs.append(source)
        editions[target["model"]].append((product["id"], raised))
    warnings.extend(_edition_warnings(editions))
    vocabulary = {"categories": [entry["id"] for entry in config["lines"] + config["accessories"]],
                  "capabilities": list(registry[0]), "facts": list(NUMERIC_FACTS)}
    result = {"schema_version": SCHEMA_VERSION,
              "snapshot": {"manifest_sha256": manifest["sha256"], "built_at": manifest["built_at"],
                           "inputs": sorted(inputs, key=lambda item: (item["base"], item["path"]))},
              "vocabulary": vocabulary, "products": products, "warnings": warnings}
    return {**result, "content_sha256": _digest(result)}
