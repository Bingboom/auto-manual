"""Export canonical EU manual evidence before the RTD deployment is sealed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.manual_knowledge.html import extract_sections, identity
from tools.rtd_deployment_receipt import MAX_FILE_BYTES, source_fingerprint
from tools.utils.path_utils import PathSegments

ARTIFACT = "manual-knowledge.json"
SCHEMA = "auto-manual-knowledge/v1"


def make_corpus(products: list[dict], output_root: Path, *, source_sha256: str,
                published_at: str) -> dict:
    documents = []
    for product in products:
        if product["region"] != "EU":
            continue
        for publication in product["publications"]:
            url = publication["url"]
            rendered = (output_root / url).resolve()
            if not rendered.is_relative_to(output_root.resolve()) or not rendered.is_file():
                raise ValueError(f"Missing or unsafe rendered publication: {url}")
            data = rendered.read_bytes()
            if len(data) > MAX_FILE_BYTES:
                raise ValueError(f"Rendered publication exceeds query limits: {url}")
            sections, coverage = extract_sections(data.decode("utf-8"), url=url)
            documents.append({
                "id": identity(url), "model": product["model"], "region": "EU",
                "name": product["name"], "url": url,
                "lang": publication["lang"] if publication["language_scope"] == "single" else None,
                "declared_lang": publication["lang"], "language_scope": publication["language_scope"],
                "version": publication.get("version"), "html_sha256": hashlib.sha256(data).hexdigest(),
                "sections": sections, "coverage": coverage,
            })
    ids = [document["id"] for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate canonical EU publication in query catalog")
    return {"schema": SCHEMA, "source_sha256": source_sha256,
            "published_at": published_at, "region": "EU", "documents": documents,
            "counts": {"models": len({d["model"] for d in documents}), "editions": len(documents),
                       "sections": sum(len(d["sections"]) for d in documents)}}


def write_knowledge(app, exception) -> None:
    """Do not emit a production query corpus for drafts or bootstrap fixtures."""
    source = Path(app.srcdir)
    manifest_path = source.parent / "publish_manifest.json"
    if (exception is not None or getattr(app.builder, "format", None) != "html"
            or source.name != PathSegments.WEB or source.parent.name != PathSegments.PUBLISH
            or not manifest_path.is_file()):
        return
    from tools.rtd_portal import portal_data

    _, products = portal_data(app)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # The receipt extension also supports minimal frozen trees without a
    # publication catalog. They must retain their existing build contract.
    if "targets" not in manifest and not products:
        return
    if not isinstance(manifest.get("targets"), list):
        raise ValueError("EU query export requires a frozen publication target list")
    corpus = make_corpus(products, Path(app.outdir), source_sha256=source_fingerprint(source),
                         published_at=str(manifest.get("built_at") or ""))
    # A catalog omission is not an acceptable partial-success export.
    expected = {f"{target['route']}/{Path(target['manual']).with_suffix('.html')}"
                for target in manifest["targets"] if target["region"] == "EU"}
    if {doc["url"] for doc in corpus["documents"]} != expected:
        raise ValueError("EU query corpus does not cover the frozen publication manifest")
    data = (json.dumps(corpus, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("EU query corpus exceeds the deployment artifact size limit")
    destination = Path(app.outdir) / ARTIFACT
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)
