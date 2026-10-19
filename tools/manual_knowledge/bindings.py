"""Where each claimed edition of the knowledge ledger is edited (machine-readable Phase 3a, P3-3).

Every published edition has one authority (plan §4.2). The portal catalogue names its release path
(``tools/rtd/publication_catalog.py``) and the corpus ``manual-knowledge.json`` carries it per document:

- ``git_only_frozen``: the frozen source manifest declares the authority. The package is never edited; a fix
  is rebuilt as a new version and published.
- ``queue``: the build table's ``Git_ref`` (a review branch) declares it; backport, template sync and F6 are
  the entries.
- ``unclassified`` and ``legacy``: nothing declares it. A person binds the sources to edit in the finding's
  ``bindings`` before the change is approved (D20); ``check`` enforces that.

``binding_report`` covers every finding still open to a change. For each claimed edition it gives the
release path, the concrete source (the frozen source manifest, or the bound paths) and whether the source is
``declared``, ``bound`` or ``unbound``; ``entries`` repeats §4.2's editing entry and approval per release path.
Each edition lists the findings that claim it, so one rebuild can carry them all. A release path the ledger
records that the corpus no longer publishes, or an edition the corpus no longer has, is a problem. It reads
the ledger and the corpus only, writes neither, and its output depends on nothing else.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from tools.manual_knowledge.export import SCHEMA as CORPUS_SCHEMA
from tools.manual_knowledge.findings import UNDECLARED
from tools.manual_knowledge.governance import serialize, write_file
from tools.utils.path_utils import PathSegments, docs_publish_of

BINDINGS = "findings-bindings.json"
BINDINGS_SCHEMA = "auto-manual-knowledge-findings-bindings/v1"
STATES = ("declared", "bound", "unbound")
# A finding that needs no further change: done, refuted, exempt or replaced.
INACTIVE = ("closed", "rejected", "not_applicable", "superseded")
_REBUILD = "操作者指定内容；工程 PR + Hello-Docs 发布 PR"
# Plan §4.2, one row per release path.
ENTRIES = {
    "git_only_frozen": {"entry": "发布包不可改，修正后重建为新版本再发布", "approval": _REBUILD},
    "unclassified": {"entry": "文档构建表 `Git_ref` 指向的源，多为 `docs/templates/` 与冻结的 phase2 输入",
                     "approval": f"{_REBUILD}；先确认绑定"},
    "queue": {"entry": "回写 R 类改 `docs/_review/`、模板同步 T 类改 `docs/templates/`、F6 改飞书源表",
              "approval": "各自的门禁与回读"},
    "legacy": {"entry": "没有发布元数据，同 `unclassified`", "approval": f"{_REBUILD}；先确认绑定"},
}
_PUBLICATION = ("manual_variant_id", "release_path", "authority", "version", "git_ref", "built_at",
                "source_manifest")


def _publications(corpus: dict, region: str) -> dict[str, dict]:
    """Each published edition's release facts; a frozen source manifest as its Hello-Docs path."""
    if not isinstance(corpus, dict) or corpus.get("schema") != CORPUS_SCHEMA or corpus.get("region") != region:
        raise ValueError(f"Not a {region} manual-knowledge corpus ({CORPUS_SCHEMA})")
    publications = {}
    for document in corpus["documents"]:
        source = document.get("source") or {}
        manifest = source.get("source_manifest")
        publications[document["variant_key"]] = {
            "manual_variant_id": document["manual_variant_id"],
            "release_path": source.get("release_path", "legacy"), "authority": source.get("authority", "unknown"),
            "version": document.get("publication_version"), "git_ref": source.get("git_ref"),
            "built_at": source.get("built_at"),
            "source_manifest": (docs_publish_of(Path(PathSegments.DOCS)) / manifest["path"]).as_posix()
            if manifest else None}
    return publications


def _row(variant: str, release: str, publication: dict | None, binding: dict | None) -> dict:
    """One claimed edition: its release path, where to edit it and whether a source is known."""
    if release not in UNDECLARED:
        manifest = (publication or {}).get("source_manifest")
        return {"variant": variant, "release_path": release, "binding": "declared",
                "sources": [manifest] if manifest else []}
    if binding is None:
        return {"variant": variant, "release_path": release, "binding": "unbound", "sources": []}
    return {"variant": variant, "release_path": release, "binding": "bound", "sources": list(binding["sources"]),
            "by": binding["by"], "role": binding["role"], "date": binding["date"]}


def _finding(finding: dict, publications: dict[str, dict], problems: list[str]) -> dict:
    rows = []
    for variant, recorded in sorted(finding["authority"].items()):
        publication = publications.get(variant)
        if publication is None:
            problems.append(f"{finding['finding_id']}: {variant} is not in the corpus")
        elif publication["release_path"] != recorded:
            problems.append(f"{finding['finding_id']}: {variant} is published as {publication['release_path']}, "
                            f"the ledger records {recorded}")
        release = publication["release_path"] if publication else recorded
        rows.append(_row(variant, release, publication, finding.get("bindings", {}).get(variant)))
    return {"finding_id": finding["finding_id"], "status": finding["status"], "priority": finding.get("priority"),
            "editions": rows}


def binding_report(ledger: dict, corpus: dict) -> dict:
    """Editing entry and binding state of every edition claimed by a finding still open to a change."""
    publications = _publications(corpus, ledger["region"])
    problems: list[str] = []
    findings = [_finding(finding, publications, problems) for finding in ledger["findings"]
                if finding["status"] not in INACTIVE]
    claimants: dict[str, list[str]] = defaultdict(list)
    unbound: dict[str, list[str]] = defaultdict(list)
    release: dict[str, str] = {}
    for finding in findings:
        for row in finding["editions"]:
            claimants[row["variant"]].append(finding["finding_id"])
            release.setdefault(row["variant"], row["release_path"])
            if row["binding"] == "unbound":
                unbound[row["variant"]].append(finding["finding_id"])
    editions = {variant: {**publications.get(variant, dict.fromkeys(_PUBLICATION)), "findings": ids}
                for variant, ids in sorted(claimants.items())}
    states = Counter(row["binding"] for finding in findings for row in finding["editions"])
    return {"schema": BINDINGS_SCHEMA, "region": ledger["region"],
            "corpus": {"published_at": corpus.get("published_at"), "source_sha256": corpus.get("source_sha256")},
            "entries": ENTRIES, "states": list(STATES),
            "totals": {"findings": len(findings), "inactive": len(ledger["findings"]) - len(findings),
                       "editions": len(editions),
                       "release_paths": dict(sorted(Counter(release.values()).items())),
                       "bindings": {state: states[state] for state in STATES}, "unbound_editions": len(unbound)},
            "findings": findings, "editions": editions,
            "unbound": [{"variant": variant, "findings": ids} for variant, ids in sorted(unbound.items())],
            "inactive": [finding["finding_id"] for finding in ledger["findings"] if finding["status"] in INACTIVE],
            "problems": problems}


def report_bindings(args: argparse.Namespace, ledger: dict) -> int:
    """The ``bindings`` command of ``python -m tools.manual_knowledge.findings``."""
    try:
        report = binding_report(ledger, json.loads(args.corpus.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"status": "refused", "problems": [str(error)]}, ensure_ascii=False, indent=2))
        return 1
    output = args.output or args.corpus.parent / BINDINGS
    write_file(output, serialize(report))
    result: dict = {"status": "written", "path": str(output), "totals": report["totals"]}
    if report["problems"]:
        result["problems"] = report["problems"]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if report["problems"] else 0
