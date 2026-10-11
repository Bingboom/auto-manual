"""Comparison relations between knowledge items (Phase 2a, P2-3).

Two comparisons with their own rules, never one shared similarity (parent plan §9):

- **Across products** (same region and language): ``exact_reuse`` groups items
  whose label and text are identical in two or more models; ``near_reuse`` groups
  items whose texts differ only in spacing, letter case, quote or dash style or
  list glyphs, or only in their labels; ``product_specific`` marks a warning whose
  text no other model of that language uses. Reworded counterparts (semantic
  variants) are not judged.
- **Across languages** (same model and region, single-language editions):
  ``language_parity`` aligns each category's items against the English edition in
  reading order, one language after another. A pair scores on shared numbers,
  topics and severity; block types are ignored. An item that no earlier language
  had opens its own cluster, so a note missing from English still groups across
  the other languages.

Every relation keeps each member's identity and source. ``absent_in`` lists the
editions where no counterpart was aligned, how far the search went and how the
revisions relate; an absence is a candidate, never an error. Each claimed
difference (an absence, or members that disagree on severity or numbers) carries
its own confidence: ``high`` needs numbers that every member states, a whole
document that lacks them with every image described, and printed, equal
revisions; topic evidence alone stays ``medium``; no evidence, or anchors found
elsewhere in the edition (a possible presentation difference), is ``low``. A
relation takes the confidence of its strongest claim, or of the alignment itself
when it claims none.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
import hashlib
import re
import unicodedata

from tools.manual_knowledge.topics import classify

CATEGORIES = ("warning", "safety", "compliance")
PIVOT_LANGUAGE = "en"
HITS = 3  # blocks or items reported for an absence whose evidence turned up elsewhere
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_BULLETS = re.compile(r"^[ \t]*[•●▪◦‧·][ \t]*", re.MULTILINE)
_FORMS = str.maketrans("‘’‚“”„«»–—‑", "'''\"\"\"\"\"---")
_CONFIDENCE = {"strong": "high", "moderate": "medium", "weak": "low"}
_RANK = {"low": 0, "medium": 1, "high": 2}


def numbers(text: str) -> frozenset[str]:
    """Numbers as any manual language writes them; a decimal comma reads as a point."""
    return frozenset(match.replace(",", ".") for match in _NUMBER.findall(text))


def loose(text: str) -> str:
    """Comparison key that ignores spacing, letter case, quote and dash style and list glyphs."""
    text = _BULLETS.sub("", unicodedata.normalize("NFKC", text)).translate(_FORMS).casefold()
    return "".join(text.split())


def revision_alignment(left: dict, right: dict) -> str:
    """``same`` or ``different`` only between printed revisions; otherwise ``unknown`` (D11)."""
    if left["revision_kind"] != "printed" or right["revision_kind"] != "printed":
        return "unknown"
    return "same" if left["revision"] == right["revision"] else "different"


def _member(item: dict) -> dict:
    return {"knowledge_id": item["knowledge_id"], "variant_key": item["variant_key"],
            "manual_variant_id": item["manual_variant_id"], "source_ref": item["source"]["source_ref"],
            "severity": item["severity"], "block_type": item["source"]["block_type"]}


def _relation(kind: str, category: str, scope: dict, members: list[dict], **fields) -> dict:
    absent = fields.get("absent_in", [])
    key = "\x1f".join([kind, category, *sorted(item["knowledge_id"] for item in members),
                       *sorted(entry["variant_key"] for entry in absent)])
    relation = {"observation_id": f"obs:{kind}:{'/'.join(scope.values())}:"
                                  f"{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}",
                "kind": kind, "category": category, "scope": scope, "members": [_member(m) for m in members],
                "absent_in": [], "anchors": [], "differences": [], "confidence": "low", "status": "candidate"}
    relation.update(fields)
    return relation


def _searched(document: dict, searched: str, alignment: str) -> dict:
    return {"variant_key": document["variant_key"], "manual_variant_id": document["manual_variant_id"],
            "searched": searched, "revision_alignment": alignment, "html_sha256": document["html_sha256"]}


def _models(items: Iterable[dict]) -> set[str]:
    return {item["observed_context"]["model"] for item in items}


def _near_differences(members: list[dict], category: str) -> list[str]:
    differences = []
    if len({member["label"] for member in members}) > 1:
        # A warning's label is its signal word; elsewhere it names a symbol's icon.
        differences.append("label" if category == "warning" else "symbol_name")
    if len({member["severity"] for member in members}) > 1:
        differences.append("severity")
    if len({" ".join(unicodedata.normalize("NFKC", member["text"]).split()) for member in members}) > 1:
        differences.append("text_form")
    return differences


def _reuse(group: list[dict], category: str, scope: dict) -> Iterator[dict]:
    exact: dict[str, list[dict]] = defaultdict(list)
    near: dict[str, list[dict]] = defaultdict(list)
    for item in group:
        exact[item["content_sha256"]].append(item)
        near[loose(item["text"])].append(item)
    for members in exact.values():
        if len(_models(members)) > 1:
            yield _relation("exact_reuse", category, scope, members, anchors=sorted(numbers(members[0]["text"])),
                            confidence="high")
    for members in near.values():
        if len(_models(members)) > 1 and len({member["content_sha256"] for member in members}) > 1:
            yield _relation("near_reuse", category, scope, members, anchors=sorted(numbers(members[0]["text"])),
                            differences=sorted(_near_differences(members, category)), confidence="high")


def _product_specific(group: list[dict], documents: list[dict], scope: dict) -> Iterator[dict]:
    models: dict[str, set[str]] = defaultdict(set)
    for item in group:
        models[loose(item["text"])].add(item["observed_context"]["model"])
    unique: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in group:
        key = loose(item["text"])
        if len(models[key]) == 1:
            unique[item["variant_key"], key].append(item)
    for members in unique.values():
        model = members[0]["observed_context"]["model"]
        others = [_searched(document, "same_category_items", "not_applicable")
                  for document in documents if document["model"] != model]
        if others:
            # A reworded counterpart in another product is not judged, so this never reaches high.
            yield _relation("product_specific", "warning", scope, members, absent_in=others,
                            anchors=sorted(numbers(members[0]["text"])),
                            confidence="medium" if members[0]["topic"] else "low")


def _cross_product(items: list[dict], documents: list[dict], region: str) -> Iterator[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in items:
        groups[item["observed_context"]["language"], item["category"]].append(item)
    for (language, category), group in sorted(groups.items()):
        scope = {"region": region, "language": language}
        yield from _reuse(group, category, scope)
        if category == "warning":
            yield from _product_specific(group, [d for d in documents if d["language"] == language], scope)


def _features(item: dict) -> dict:
    topics = frozenset(item["topic"])
    return {"numbers": numbers(item["text"]), "topics": topics, "severity": item["severity"],
            "context": topics | frozenset(classify(item["source"]["section_title"]))}


def _overlap(left: frozenset, right: frozenset, *, scale: int, offset: int, one_sided: int, cap: int) -> int:
    """Jaccard overlap mapped to [-offset, scale - offset]; a one-sided set costs ``one_sided`` per element."""
    if not left and not right:
        return 0
    if not left or not right:
        return -min(cap, one_sided * len(left | right))
    return scale * len(left & right) // len(left | right) - offset


def _score(left: dict, right: dict) -> int:
    """Evidence that two items of one category state the same thing in two languages.

    One number may be spelled out in a translation; several numbers on one side only mean different items.
    """
    score = 10 + _overlap(left["numbers"], right["numbers"], scale=60, offset=20, one_sided=15, cap=45)
    score += _overlap(left["topics"], right["topics"], scale=40, offset=10, one_sided=5, cap=5)
    severities = {left["severity"], right["severity"]}
    if not severities & {None, "unknown"}:
        score += 10 if len(severities) == 1 else -25
    return score


def _align(left: list[dict], right: list[dict]) -> list[tuple[int | None, int | None]]:
    """Order-preserving alignment with the highest total score; only positive pairs match."""
    rows, cols = len(left), len(right)
    score = [[_score(a, b) for b in right] for a in left]
    best = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(rows - 1, -1, -1):
        for j in range(cols - 1, -1, -1):
            paired = best[i + 1][j + 1] + score[i][j] if score[i][j] > 0 else 0
            best[i][j] = max(best[i + 1][j], best[i][j + 1], paired)
    pairs: list[tuple[int | None, int | None]] = []
    i = j = 0
    while i < rows and j < cols:
        if score[i][j] > 0 and best[i][j] == best[i + 1][j + 1] + score[i][j]:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif best[i][j] == best[i + 1][j]:
            pairs.append((i, None))
            i += 1
        else:
            pairs.append((None, j))
            j += 1
    return pairs + [(k, None) for k in range(i, rows)] + [(None, k) for k in range(j, cols)]


def _clusters(sequences: list[list[dict]], features: dict[str, dict]) -> list[list[dict]]:
    """Each language joins the clusters of the languages before it; a cluster is represented by its first item."""
    profile: list[list[dict]] = []
    for sequence in sequences:
        merged = []
        for i, j in _align([features[cluster[0]["knowledge_id"]] for cluster in profile],
                           [features[item["knowledge_id"]] for item in sequence]):
            if i is not None and j is not None:
                merged.append(profile[i] + [sequence[j]])
            elif i is not None:
                merged.append(profile[i])
            elif j is not None:
                merged.append([sequence[j]])
        profile = merged
    return profile


def _merge_crossings(clusters: list[list[dict]], features: dict[str, dict], rank: dict[str, int]) -> list[bool]:
    """Join clusters from disjoint editions whose first items still match: one item placed elsewhere.

    Reading-order alignment cannot pair items that a lineage moved to another position; such an item
    leaves two clusters with complementary editions. Returns, per cluster, whether it was joined.
    """
    moved = [False] * len(clusters)
    while True:
        best: tuple[int, int, int] | None = None
        for a, left in enumerate(clusters):
            for b in range(a + 1, len(clusters)):
                right = clusters[b]
                if {item["variant_key"] for item in left} & {item["variant_key"] for item in right}:
                    continue
                score = _score(features[left[0]["knowledge_id"]], features[right[0]["knowledge_id"]])
                if score > 0 and (best is None or score > best[0]):
                    best = (score, a, b)
        if best is None:
            return moved
        _, a, b = best
        clusters[a] = sorted(clusters[a] + clusters.pop(b), key=lambda item: rank[item["variant_key"]])
        moved.pop(b)
        moved[a] = True


def _blocks(document: dict) -> Iterator[dict]:
    for section in document["sections"]:
        yield from section["blocks"]


def _absent(document: dict, reference: dict, evidence: tuple[frozenset, frozenset], candidates: list[dict],
            features: dict[str, dict]) -> dict:
    anchors, context = evidence
    entry = _searched(document, "aligned_items", revision_alignment(reference["observed_context"], document))
    hits: list[dict] = []
    if anchors:
        entry["searched"] = "whole_document"
        hits = [{"block_id": block["block_id"], "source_ref": block["source_ref"]}
                for block in _blocks(document) if anchors <= numbers(block["text"])]
    elif context:
        entry["searched"] = "topic_items"
        hits = [{"knowledge_id": item["knowledge_id"], "source_ref": item["source"]["source_ref"]}
                for item in candidates if context <= features[item["knowledge_id"]]["context"]]
    strength = "weak" if hits or not (anchors or context) else "strong" if anchors else "moderate"
    # Text in an image without alt is invisible here (no OCR), so it can always hide the counterpart.
    blind = document["coverage"]["images"] - document["coverage"]["images_with_alt"]
    if blind and strength == "strong":
        strength = "moderate"
    entry.update(hits=hits[:HITS], images_without_alt=blind,
                 confidence=_confidence(strength, [entry["revision_alignment"]]))
    return entry


def _confidence(strength: str, alignments: list[str]) -> str:
    """A difference reaches high only between printed, equal revisions."""
    confidence = _CONFIDENCE[strength]
    return "medium" if confidence == "high" and "same" not in alignments else confidence


def _disagreeing_alignments(members: list[dict], value) -> list[str]:
    return [revision_alignment(a["observed_context"], b["observed_context"])
            for index, a in enumerate(members) for b in members[index + 1:] if value(a) != value(b)]


def _member_claims(cluster: list[dict], features: dict[str, dict], strength: str) -> tuple[list[str], list[str]]:
    """Differences between the aligned members themselves, with each claim's confidence."""
    differences: list[str] = []
    confidences: list[str] = []
    if len({item["severity"] for item in cluster}) > 1:
        differences.append("severity")
        confidences.append(_confidence(strength, _disagreeing_alignments(cluster, lambda item: item["severity"])))
    reference = features[cluster[0]["knowledge_id"]]["numbers"]
    if any(not reference <= features[item["knowledge_id"]]["numbers"] for item in cluster[1:]):
        differences.append("numbers")
        confidences.append(_confidence(strength, _disagreeing_alignments(
            cluster, lambda item: reference <= features[item["knowledge_id"]]["numbers"])))
    if len({item["source"]["block_type"] for item in cluster}) > 1:
        differences.append("presentation")
    return differences, confidences


def _anchors(cluster: list[dict], features: dict[str, dict]) -> frozenset[str]:
    """Numbers every member states: the language-neutral evidence that the members are one item."""
    return frozenset.intersection(*(features[item["knowledge_id"]]["numbers"] for item in cluster))


def _parity_relation(cluster: list[dict], editions: list[dict], candidates: dict[str, list[dict]],
                     features: dict[str, dict], scope: dict, moved: bool) -> dict:
    anchors = _anchors(cluster, features)
    context = frozenset.intersection(*(features[item["knowledge_id"]]["context"] for item in cluster))
    strength = "strong" if anchors else "moderate" if context else "weak"
    present = {item["variant_key"] for item in cluster}
    absent = [_absent(document, cluster[0], (anchors, context), candidates[document["variant_key"]], features)
              for document in editions if document["variant_key"] not in present]
    differences, confidences = _member_claims(cluster, features, strength)
    if moved:
        differences.append("order")
    if absent:
        differences.append("absent")
        confidences.extend(entry["confidence"] for entry in absent)
    confidence = max(confidences, key=_RANK.__getitem__) if confidences else _CONFIDENCE[strength]
    return _relation("language_parity", cluster[0]["category"], scope, cluster, absent_in=absent,
                     anchors=sorted(anchors), context_topics=sorted(context), differences=sorted(differences),
                     confidence=confidence)


def _editions(documents: list[dict]) -> dict[str, list[dict]]:
    """Each model's single-language editions, pivot first; combined multi-language editions take no part (D3)."""
    found: dict[str, dict[str, dict]] = defaultdict(dict)
    for document in documents:
        if document["language"] != "multi":
            found[document["model"]][document["language"]] = document
    return {model: [by_language[language] for language in sorted(
                by_language, key=lambda language: (language != PIVOT_LANGUAGE, language))]
            for model, by_language in sorted(found.items()) if len(by_language) > 1}


def _candidates(order: list[dict], clusters: dict[str, list[list[dict]]], sequences: dict[tuple[str, str], list[dict]],
                features: dict[str, dict]) -> dict[str, list[dict]]:
    """Per edition, the items a topic search may still take for a missing one.

    Only shared numbers tie an item firmly to a pivot item; any other item may be a missing one reworded,
    merged into a neighbour or moved to another category.
    """
    firm = {item["knowledge_id"] for found in clusters.values() for cluster in found
            if cluster[0]["variant_key"] == order[0]["variant_key"] and _anchors(cluster, features)
            for item in cluster}
    return {document["variant_key"]: [item for category in CATEGORIES
                                      for item in sequences[document["variant_key"], category]
                                      if item["knowledge_id"] not in firm]
            for document in order}


def _parity(items: list[dict], documents: list[dict], region: str) -> Iterator[dict]:
    sequences: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in items:
        sequences[item["variant_key"], item["category"]].append(item)
    features = {item["knowledge_id"]: _features(item) for item in items}
    for model, order in _editions(documents).items():
        rank = {document["variant_key"]: index for index, document in enumerate(order)}
        clusters = {category: _clusters([sequences[d["variant_key"], category] for d in order], features)
                    for category in CATEGORIES}
        moved = {category: _merge_crossings(clusters[category], features, rank) for category in CATEGORIES}
        candidates = _candidates(order, clusters, sequences, features)
        for category in CATEGORIES:
            for cluster, was_moved in zip(clusters[category], moved[category], strict=True):
                yield _parity_relation(cluster, order, candidates, features, {"model": model, "region": region},
                                       was_moved)


def _rules(relation: dict) -> list[str]:
    return [f"compare.{relation['kind']}"] + sorted({f"search.{entry['searched']}" for entry in relation["absent_in"]})


def build_relations(corpus: dict, items: list[dict], generator: str) -> list[dict]:
    """Cross-product reuse, then per-model language parity, in a fixed order."""
    relations = [*_cross_product(items, corpus["documents"], corpus["region"]),
                 *_parity(items, corpus["documents"], corpus["region"])]
    for relation in relations:
        relation["method"] = {"generator": generator, "rules": _rules(relation)}
    return relations


def summarize_relations(relations: list[dict]) -> dict:
    by_kind: dict[str, Counter[str]] = defaultdict(Counter)
    for relation in relations:
        by_kind[relation["kind"]][relation["confidence"]] += 1
    return {"relations": len(relations),
            "relations_by_kind": {kind: dict(sorted(counts.items())) for kind, counts in sorted(by_kind.items())},
            "relation_differences": dict(sorted(Counter(difference for relation in relations
                                                        for difference in relation["differences"]).items()))}
