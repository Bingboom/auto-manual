"""Machine-surface manifest and freshness check for the EU manual corpus.

The manifest is written next to ``manual-knowledge.json`` in the same build and
before the deployment receipt, so the receipt hashes both. Freshness compares a
manifest's recorded hashes with a deployment receipt:

- ``fresh``: the receipt still serves the HTML this surface was extracted from
  and the corpus still carries the same document bytes;
- ``stale``: the published HTML changed since this surface was generated;
- ``failed``: the corpus is missing the document or its bytes differ;
- ``unavailable``: the publication is no longer in the deployment.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import sys

from tools.manual_knowledge.identity import GENERATOR_VERSION

MANIFEST = "machine_surface_manifest.json"
MANIFEST_SCHEMA = "auto-manual-machine-surface-manifest/v1"
STATUSES = ("fresh", "stale", "failed", "unavailable")


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def surface_sha256(document: dict) -> str:
    return hashlib.sha256(canonical(document)).hexdigest()


def _counts(document: dict) -> dict:
    blocks = [block for section in document["sections"] for block in section["blocks"]]
    coverage = document.get("coverage", {})
    return {"sections": len(document["sections"]), "blocks": len(blocks),
            "blocks_by_type": dict(sorted(Counter(b["type"] for b in blocks).items())),
            "callouts_by_severity": dict(sorted(Counter(b.get("severity", "unknown") for b in blocks
                                                        if b["type"] == "callout").items())),
            "images": coverage.get("images", 0),
            "images_without_alt": coverage.get("images", 0) - coverage.get("images_with_alt", 0)}


def build_manifest(corpus: dict, corpus_bytes: bytes, *, artifact: str) -> dict:
    variants = []
    for document in corpus["documents"]:
        source = document.get("source", {})
        variants.append({
            "variant_key": document["variant_key"], "manual_variant_id": document["manual_variant_id"],
            "document_id": document["id"], "url": document["url"],
            "model": document["model"], "region": document["region"], "language": document["language"],
            "language_status": document["language_status"], "revision": document["revision"],
            "revision_kind": document["revision_kind"], "publication_version": document["publication_version"],
            "generation_mode": document["machine_surface"]["generation_mode"],
            "release_path": source.get("release_path"), "authority": source.get("authority"),
            "html_sha256": document["html_sha256"], "surface_sha256": surface_sha256(document),
            "status": "fresh", "counts": _counts(document),
        })
    return {"schema": MANIFEST_SCHEMA, "generator_version": GENERATOR_VERSION,
            "source_sha256": corpus["source_sha256"], "published_at": corpus["published_at"],
            "region": corpus["region"],
            "corpus": {"path": artifact, "schema": corpus["schema"], "bytes": len(corpus_bytes),
                       "sha256": hashlib.sha256(corpus_bytes).hexdigest()},
            "totals": {"variants": len(variants),
                       "status": dict(Counter(v["status"] for v in variants)),
                       "generation_mode": dict(Counter(v["generation_mode"] for v in variants)),
                       "revision_kind": dict(sorted(Counter(v["revision_kind"] for v in variants).items())),
                       "language_status": dict(sorted(Counter(v["language_status"] for v in variants).items()))},
            "variants": variants}


def check_freshness(read: Callable[[str], bytes], *, receipt_name: str,
                    manifest: dict | None = None) -> dict:
    """Judge a manifest (current by default, or a cached copy) against the live receipt."""
    receipt = json.loads(read(receipt_name))
    files = receipt.get("files") if isinstance(receipt, dict) else None
    if not isinstance(files, dict):
        raise ValueError("Deployment receipt has no file inventory")
    problems = []
    if manifest is None:
        manifest_bytes = read(MANIFEST)
        if hashlib.sha256(manifest_bytes).hexdigest() != files.get(MANIFEST):
            problems.append("manifest bytes differ from the deployment receipt")
        manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("Unsupported machine-surface manifest")
    corpus_path = manifest["corpus"]["path"]
    documents: dict[str, dict] = {}
    if files.get(corpus_path) != manifest["corpus"]["sha256"]:
        problems.append("corpus in the deployment is not the one this manifest describes")
    try:
        corpus_bytes = read(corpus_path)
        if hashlib.sha256(corpus_bytes).hexdigest() != files.get(corpus_path):
            problems.append("corpus bytes differ from the deployment receipt")
        documents = {d["id"]: d for d in json.loads(corpus_bytes).get("documents", [])}
    except (OSError, ValueError) as exc:
        problems.append(f"corpus unreadable: {exc}")
    if manifest.get("source_sha256") != receipt.get("source_sha256"):
        problems.append("manifest was generated from a different frozen source")
    variants = []
    for variant in manifest["variants"]:
        if variant["url"] not in files:
            status = "unavailable"
        elif files[variant["url"]] != variant["html_sha256"]:
            status = "stale"
        elif variant["document_id"] not in documents or surface_sha256(
                documents[variant["document_id"]]) != variant["surface_sha256"]:
            status = "failed"
        else:
            status = "fresh"
        variants.append({"manual_variant_id": variant["manual_variant_id"], "url": variant["url"],
                         "status": status})
    totals = Counter(v["status"] for v in variants)
    return {"status": "fresh" if not problems and set(totals) <= {"fresh"} else "not_fresh",
            "problems": problems, "totals": {s: totals.get(s, 0) for s in STATUSES},
            "variants": variants}


def main(argv: list[str] | None = None) -> int:
    from tools.rtd.deployment_receipt import RECEIPT

    parser = argparse.ArgumentParser(description="Check machine-surface freshness against a deployment receipt")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--site", type=Path, help="built HTML output directory")
    where.add_argument("--base-url", help="deployed site, e.g. https://ht-doc.readthedocs.io")
    parser.add_argument("--manifest", type=Path, help="cached manifest to judge instead of the deployed one")
    args = parser.parse_args(argv)
    if args.site is not None:
        root = args.site.resolve()

        def read(path: str) -> bytes:
            target = (root / path).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"Unsafe path: {path}")
            return target.read_bytes()
    else:
        from tools.manual_operations_online_health import publication_url
        from tools.rtd.deployment_receipt import FetchSession

        session = FetchSession()

        def read(path: str) -> bytes:
            return session.fetch(publication_url(args.base_url, path))
    cached = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
    report = check_freshness(read, receipt_name=RECEIPT, manifest=cached)
    summary = {key: report[key] for key in ("status", "problems", "totals")}
    summary["not_fresh"] = [v for v in report["variants"] if v["status"] != "fresh"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "fresh" else 1


if __name__ == "__main__":
    sys.exit(main())
