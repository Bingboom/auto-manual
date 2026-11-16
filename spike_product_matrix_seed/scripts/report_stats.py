"""Numbers for completeness_report.md. Usage: python report_stats.py <out dir>  (prints and writes work_report_stats.json)"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from attributes import CHECKLIST


def rd(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(out: Path) -> None:
    rows, manuals = rd(out / "spec_rows.csv"), rd(out / "work_manuals.csv")
    labels, facts = rd(out / "label_inventory.csv"), rd(out / "facts_candidate.csv")
    dic, matrix = rd(out / "attribute_dictionary_v0.csv"), rd(out / "matrix_candidate.csv")
    gaps, times = rd(out / "work_gap_hits.csv"), rd(out / "work_time_strings.csv")
    langd, regd = rd(out / "work_language_disagreements.csv"), rd(out / "work_region_differences.csv")
    s: dict = {}
    s["manuals"] = len(manuals)
    s["models"] = len({m["model"] for m in manuals})
    s["model_region_pairs"] = len(matrix)
    s["manuals_with_spec_section_rows"] = sum(1 for m in manuals if m["spec_section_rows"] != "0")
    s["manuals_spec_rows_any"] = sum(1 for m in manuals if m["rows_captured"] != "0")
    s["manuals_no_spec"] = [f"{m['model']} {m['region']} {m['language']} (spec heading {m['spec_heading_found']}, rows {m['rows_captured']})"
                            for m in manuals if m["spec_section_rows"] == "0"]
    s["rows"] = len(rows)
    s["rows_by_kind"] = Counter(r["table_kind"] for r in rows)
    s["rows_by_type"] = Counter(r["row_type"] for r in rows)
    vr = [r for r in rows if r["row_type"] not in ("header", "subheading")]
    s["value_rows_mapped"] = sum(1 for r in vr if r["attribute_key"] not in ("UNMAPPED", ""))
    s["value_rows_unmapped"] = sum(1 for r in vr if r["attribute_key"] == "UNMAPPED")
    s["spec_value_rows_unmapped"] = sum(1 for r in vr if r["attribute_key"] == "UNMAPPED" and r["table_kind"] != "spec_like_elsewhere")
    s["labels_total"] = len(labels)
    s["labels_unmapped"] = sum(1 for l in labels if l["attribute_key"] == "UNMAPPED")
    s["labels_multi"] = sum(1 for l in labels if " | " in l["attribute_key"])
    s["labels_by_lang"] = Counter(l["language"] for l in labels)
    s["unmapped_notes"] = Counter(l["mapping_note"].split(";")[0] for l in labels if l["attribute_key"] == "UNMAPPED").most_common(12)
    s["attributes"] = {"bottom-up": sum(1 for d in dic if d["origin"].startswith("bottom")),
                       "derived": sum(1 for d in dic if d["origin"] == "derived"),
                       "top-down": sum(1 for d in dic if d["origin"] == "top-down")}
    s["facts"] = len(facts)
    cov = {d["key"]: (int(d["models_with_value"] or 0), int(d["model_region_pairs_with_value"] or 0)) for d in dic}
    s["coverage_comparison"] = sorted(((d["key"], *cov[d["key"]]) for d in dic if d.get("comparison_attribute") == "yes"),
                                      key=lambda x: -x[2])
    s["checklist"] = [(name, key, *cov.get(key, (0, 0))) for name, key in CHECKLIST]
    gh = defaultdict(list)
    for g in gaps:
        gh[g["gap_attribute"]].append(g)
    s["gap_hits"] = {k: {"manuals": len(v), "models": len({x["model"] for x in v}),
                         "examples": [(x["model"], x["region"], x["language"], x["example_1_section"], x["example_1"][:160]) for x in v
                                      if x["language"] in ("en", "ja")][:2]} for k, v in gh.items()}
    s["region_diffs"] = regd[:15]
    s["lang_disagreements"] = langd
    s["time"] = {k: [(t["model"], t["region"], t["language"], t[k]) for t in times if t.get(k)]
                 for k in ("version_label", "date", "copyright_year", "printed_or_made_in")}
    shapes = Counter(re.sub(r"git-\d{8}", "git-<date>", t["publish_meta_version_shape"]) for t in times)
    s["build_label_git"] = sum(n for k, n in shapes.items() if k.startswith("git-"))
    s["build_label_numeric"] = [(t["model"], t["region"], t["language"], t["publish_meta_version_shape"]) for t in times
                                if re.fullmatch(r"[\d.]+", t["publish_meta_version_shape"])]
    s["built_at_range"] = (min(t["publish_meta_built_at"] for t in times)[:10], max(t["publish_meta_built_at"] for t in times)[:10])
    # completeness per model: distinct attribute keys with a value (best region) and spec rows read
    keys_by_model = defaultdict(lambda: defaultdict(set))
    for f in facts:
        keys_by_model[f["model"]][f["region"]].add(f["attribute_key"])
    rows_by_model = Counter(r["model"] for r in vr if r["table_kind"] != "spec_like_elsewhere")
    comp_keys = {d["key"] for d in dic if d.get("comparison_attribute") == "yes"}
    ranking = []
    for m in {x["model"] for x in manuals}:
        regions = keys_by_model.get(m, {})
        best = max((len(v) for v in regions.values()), default=0)
        best_cmp = max((len(v & comp_keys) for v in regions.values()), default=0)
        ranking.append((m, best, best_cmp, rows_by_model.get(m, 0)))
    ranking.sort(key=lambda x: (-x[2], -x[1], x[0]))
    s["top10"] = ranking[:10]
    s["bottom10"] = sorted(ranking, key=lambda x: (x[2], x[1], x[0]))[:10]
    s["label_lang_mismatch"] = [(l["language"], l["row_label"], l["manuals"]) for l in labels if (
        l["language"] == "es" and re.search(r"Température|Courant et durée", l["row_label"])) or (
        l["language"] == "it" and re.search(r"Tensão", l["row_label"])) or (
        l["language"] == "fr" and re.search(r"^(AC Output in Bypass Mode|Maximum Short Circuit Current and Duration|Feed-In Type|IEC code)$", l["row_label"])) or (
        l["language"] == "es" and re.search(r"^(Maximum Short Circuit Current and Duration|IEC code)$", l["row_label"])) or (
        l["language"] == "de" and l["row_label"] in ("IEC code",))]
    json.dump(s, open(out / "work_report_stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=list)
    print(json.dumps(s, ensure_ascii=False, indent=1, default=list)[:20000])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
