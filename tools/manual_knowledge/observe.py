"""Offline knowledge observation over the sealed EU machine corpus (Phase 2a).

The command reads one deployment (a built site or the served one), refuses it
unless the corpus and manifest match the deployment receipt, and writes
``manual-observations.json`` outside the deployment. Every Knowledge Item keeps
its full variant identity and block-level source. ``knowledge_id`` is content
addressed: inserting or removing other blocks and moving a route keep it, while
a change to the item's own label or text replaces it, so an earlier artifact's
item turns stale exactly when its content changed. Machine output only carries
``extracted`` / ``candidate`` status; review decisions belong to Phase 3.

P2-1 records every callout as a ``warning`` item. Topic classification, the
other carriers (signal-word table rows, safety sections, compliance statements)
and comparison relations arrive with P2-2 and P2-3.
Plan: ``code-as-doc/dev/machine_readable_knowledge_observation.md``.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

from tools.check.docs_capability import CAPABILITIES_CSV, load_capabilities
from tools.manual_knowledge.manifest import MANIFEST, check_freshness, deployment_reader
from tools.utils.path_utils import PathSegments, knowledge_observation_reports_of, repo_root

ARTIFACT = "manual-observations.json"
SCHEMA = "auto-manual-knowledge-observations/v1"
GENERATOR_VERSION = "manual-observations/0.1"
FEATURE_SOURCE = f"{PathSegments.DATA}/{CAPABILITIES_CSV}"
# Line-leading list glyphs only; signs, asterisks and numbering are content.
_BULLETS = re.compile(r"^[ \t]*[•●▪◦‧·][ \t]*", re.MULTILINE)


def normalized(text: str) -> str:
    """Identity text: compatibility width forms, list glyphs and whitespace runs unified."""
    return " ".join(_BULLETS.sub("", unicodedata.normalize("NFKC", text)).split())


def content_sha256(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(normalized(part) for part in parts).encode("utf-8")).hexdigest()


def _context(document: dict, features: dict[str, dict[str, bool]]) -> dict:
    source = document.get("source", {})
    feature = features.get(f"{document['model']}_{document['region']}")
    return {"model": document["model"], "region": document["region"], "language": document["language"],
            "language_status": document["language_status"], "revision": document["revision"],
            "revision_kind": document["revision_kind"], "release_path": source.get("release_path"),
            "authority": source.get("authority"), "feature": dict(feature) if feature is not None else "unknown"}


def _callout_item(document: dict, section: dict, block: dict, context: dict) -> dict:
    severity = block.get("severity", "unknown")
    flags = ["topic_unknown"]  # topic classification arrives with P2-2
    if severity == "unknown":
        flags.append("severity_unknown")
    if document["language"] == "multi":
        flags.append("language_multi")
    return {"category": "warning", "topic": [], "severity": severity, "label": block["label"],
            "text": block["body"], "content_sha256": content_sha256(block["label"], block["body"]),
            "variant_key": document["variant_key"], "manual_variant_id": document["manual_variant_id"],
            "observed_context": dict(context),
            "source": {"section_id": section["id"], "section_title": section["title"],
                       "block_id": block["block_id"], "block_type": block["type"], "item_index": None,
                       "source_ref": block["source_ref"], "html_sha256": document["html_sha256"]},
            "status": "extracted", "review_flags": sorted(flags),
            "method": {"generator": GENERATOR_VERSION, "rules": ["extract.callout"]}}


def _assign_ids(items: list[dict]) -> None:
    seen: Counter[tuple[str, str, str]] = Counter()
    for item in items:
        key = (item["variant_key"], item["category"], item["content_sha256"])
        item["knowledge_id"] = f"kn:{key[0]}:{key[1]}:{key[2][:16]}:{seen[key]}"
        seen[key] += 1


def build_items(corpus: dict, features: dict[str, dict[str, bool]]) -> list[dict]:
    """Knowledge Items in corpus order, each with its content-addressed ``knowledge_id``."""
    items = []
    for document in corpus["documents"]:
        context = _context(document, features)
        for section in document["sections"]:
            items.extend(_callout_item(document, section, block, context)
                         for block in section["blocks"] if block["type"] == "callout")
    _assign_ids(items)
    return items


def summarize(corpus: dict, items: list[dict], relations: list[dict]) -> dict:
    per_variant = {document["variant_key"]: 0 for document in corpus["documents"]}
    per_variant.update(Counter(item["variant_key"] for item in items))
    return {"variants": len(corpus["documents"]), "items": len(items), "items_by_variant": per_variant,
            "items_by_category": dict(Counter(item["category"] for item in items)),
            "items_by_severity": dict(Counter(item["severity"] for item in items)),
            "review_flags": dict(Counter(flag for item in items for flag in item["review_flags"])),
            "unknown_labels": dict(Counter(item["label"] for item in items if item["severity"] == "unknown")),
            "relations": len(relations),
            "images_without_alt": sum(document["coverage"]["images"] - document["coverage"]["images_with_alt"]
                                      for document in corpus["documents"])}


def build_observations(corpus: dict, corpus_bytes: bytes, features: dict[str, dict[str, bool]]) -> dict:
    items = build_items(corpus, features)
    relations: list[dict] = []  # comparison relations arrive with P2-3
    return {"schema": SCHEMA, "generator_version": GENERATOR_VERSION, "region": corpus["region"],
            "source_sha256": corpus["source_sha256"], "published_at": corpus["published_at"],
            "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(), "feature_source": FEATURE_SOURCE,
            "items": items, "relations": relations, "summary": summarize(corpus, items, relations)}


def serialize(observations: dict) -> bytes:
    return (json.dumps(observations, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")


def _relation_fresh(relation: dict, current: set[str], html: dict[str, str]) -> bool:
    # A recorded absence holds only while the variant it was searched in is unchanged.
    return (all(member["knowledge_id"] in current for member in relation["members"])
            and all(html.get(absent["variant_key"]) == absent["html_sha256"]
                    for absent in relation.get("absent_in", [])))


def judge_previous(previous: dict, items: list[dict], corpus: dict) -> dict:
    """Which items and relations of an earlier artifact still describe the current corpus."""
    if previous.get("schema") != SCHEMA:
        raise ValueError("Unsupported knowledge observation artifact")
    current = {item["knowledge_id"] for item in items}
    html = {document["variant_key"]: document["html_sha256"] for document in corpus["documents"]}
    stale_items = sorted(item["knowledge_id"] for item in previous["items"] if item["knowledge_id"] not in current)
    relations = previous.get("relations", [])
    stale_relations = sorted(relation["observation_id"] for relation in relations
                             if not _relation_fresh(relation, current, html))
    return {"items": {"fresh": len(previous["items"]) - len(stale_items), "stale": len(stale_items)},
            "relations": {"fresh": len(relations) - len(stale_relations), "stale": len(stale_relations)},
            "stale_items": stale_items, "stale_relations": stale_relations}


def _write_atomic(destination: Path, data: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)


def main(argv: list[str] | None = None) -> int:
    from tools.rtd.deployment_receipt import RECEIPT

    parser = argparse.ArgumentParser(description="Observe warning knowledge in the sealed EU machine corpus")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--site", type=Path, help="built HTML output directory")
    where.add_argument("--base-url", help="deployed site, e.g. https://ht-doc.readthedocs.io")
    parser.add_argument("--output", type=Path,
                        help=f"file to write (default: reports/knowledge_observations/<source>/{ARTIFACT})")
    parser.add_argument("--previous", type=Path, help="earlier observation artifact to judge against this corpus")
    args = parser.parse_args(argv)
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    read = deployment_reader(site=args.site, base_url=args.base_url)
    report = check_freshness(read, receipt_name=RECEIPT)
    if report["status"] != "fresh":
        print(json.dumps({"status": "refused", "problems": report["problems"], "totals": report["totals"]},
                         ensure_ascii=False, indent=2))
        return 1
    corpus_bytes = read(json.loads(read(MANIFEST))["corpus"]["path"])
    corpus = json.loads(corpus_bytes)
    observations = build_observations(corpus, corpus_bytes, load_capabilities(repo_root() / PathSegments.DATA))
    output = args.output or (knowledge_observation_reports_of(repo_root()) / corpus["source_sha256"][:12] / ARTIFACT)
    _write_atomic(output, serialize(observations))
    summary = {key: value for key, value in observations["summary"].items() if key != "items_by_variant"}
    result: dict = {"status": "written", "path": str(output), "summary": summary}
    if previous is not None:
        result["previous"] = judge_previous(previous, observations["items"], corpus)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
