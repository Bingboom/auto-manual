"""Steps 2-6: label inventory, attribute dictionary, facts, wide matrix and report data.

Usage: python build_outputs.py <Hello-Docs root> <auto-manual root> <out dir>
Reads <out dir>/work_spec_rows_raw.csv from parse_manuals.py and writes spec_rows.csv with mapping columns.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from attributes import A, CHECKLIST, DERIVED, TOPDOWN
from label_map import map_label
from value_parse import PARSERS, ac_total_in_text, fmt, parse_power, parse_value, port_count, to_float

EXTRACTION_DATE = "2026-11-16"
FACT_KINDS = {"spec_section", "spec_class_elsewhere"}
SPEC_LIKE_FACT_KEYS = {"ac_charge_time", "car_charge_time", "solar_charge_time", "warranty_period", "in_box_contents"}
MAIN_LANG = {"JP": "ja", "CN": "zh", "TW": "zh-TW", "KR": "ko", "US": "en", "EU": "en", "UK": "en", "AU": "en", "CA": "en"}
URL = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\w+")


def read_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(p: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def scrub(text: str) -> str:
    return URL.sub("[link removed]", text or "")


def ctx_of(r: dict) -> str:
    return " > ".join(x for x in (r["section_path"].split(" > ")[-1], r["html_subheading"], r["table_subheading"]) if x)


def assign_blocks(rows: list[dict]) -> None:
    """Per manual: split spec rows into product blocks at each product-name row; first block's product is primary."""
    by_file = defaultdict(list)
    for r in rows:
        by_file[r["source_file"]].append(r)
    for file_rows in by_file.values():
        current, names, primary = "", [], None
        model = file_rows[0]["model"]
        for r in file_rows:
            if r["table_kind"] not in FACT_KINDS:
                r["product_block"] = ""
                r["is_primary_product"] = "n/a"
                continue
            if r["attribute_key"] == "product_name" and r["value_text"]:
                current = r["value_text"]
                if current not in names:
                    names.append(current)
            described = r["described_product"]
            r["product_block"] = current or described
        # the block naming the manual's model code wins; else the first block
        model_blocks = {r["product_block"] for r in file_rows if r.get("product_block") and
                        (model in r["described_product"] or (r["attribute_key"] == "model_number" and model in r["value_text"]))}
        if names:
            primary = next((n for n in names if n in model_blocks), names[0])
        rule = "only block" if len(set(names)) <= 1 else ("block naming the model" if primary in model_blocks else "first block (flag)")
        for r in file_rows:
            if r["table_kind"] not in FACT_KINDS:
                continue
            if primary is None or r["product_block"] in ("", primary):
                r["is_primary_product"] = "yes"
            elif r["described_product"] and model in r["described_product"]:
                r["is_primary_product"] = "yes"
            else:
                r["is_primary_product"] = "no (component)"
            r["primary_rule"] = rule


SUBDIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SOLAR_SEG = re.compile(r"PV|solar|ソーラー|太阳能|solaire|Solar|fotovolt|photovolt", re.I)


def solar_text(r: dict) -> str:
    """The solar part of a shared DC input cell: segments that name PV/solar; the whole cell when the label is solar."""
    if r["attribute_key"].startswith("solar_input"):
        return r["value_text"]
    segs = [s for s in re.split(r" \| |；|;", r["value_text"]) if SOLAR_SEG.search(s)]
    return " | ".join(segs)


def numbers(text: str) -> list[float]:
    text = re.sub(r"(?<=\d)[ \u202f\u00a0](?=\d{3}\b)", "", text.translate(SUBDIGITS))
    out = []
    for m in re.finditer(r"\d+(?:[.,]\d+)*", text):
        v = to_float(m.group(0))
        if v is not None:
            out.append(round(v, 3))
    return sorted(out)


def compare_values(key: str, a: list[str], b: list[str]) -> str:
    """agree / extent (one edition prints a subset, e.g. no imperial figure or an extra row) / differ."""
    if key in PARSERS:
        pa, pb = parse_value(key, " | ".join(a)), parse_value(key, " | ".join(b))
        fa = (pa["value_metric"], pa["range_min"], pa["range_max"])
        fb = (pb["value_metric"], pb["range_min"], pb["range_max"])
        if any(fa) and fa == fb:
            return "agree"
    na, nb = set(numbers(" ".join(a))), set(numbers(" ".join(b)))
    if na == nb:
        return "agree"
    if na <= nb or nb <= na:
        return "extent"
    return "differ"


def main(hd: Path, am: Path, out: Path) -> None:
    rows = read_csv(out / "work_spec_rows_raw.csv")
    manuals = read_csv(out / "work_manuals.csv")
    catalog = json.loads((am / "tools/rtd_portal_assets/product_catalog.json").read_text(encoding="utf-8"))
    cat_models, guides = catalog["models"], catalog.get("guides", {})
    hint_keys = {r["Row_key"] for r in read_csv(am / "tests/fixtures/phase2/row_key_mapping.csv")}

    # ---- map every row
    for r in rows:
        if r["row_type"] in ("header", "subheading"):
            r["attribute_key"], r["mapping_note"] = "", f"{r['row_type']} row (not a value)"
            continue
        k, note = map_label(r["row_label_clean"], ctx_of(r), r["table_kind"], r["section_path"])
        if k == "capacity_wh" and not re.search(r"Wh", r["value_text"]):
            k, note = "capacity_other", "capacity label but no Wh printed (volume or charge, e.g. cooler or power bank)"
        r["attribute_key"], r["mapping_note"] = k, note
        for f in ("row_label", "row_label_clean", "value_text", "section_path", "described_product"):
            r[f] = scrub(r[f])
    assign_blocks(rows)
    spec_fields = ["model", "region", "language", "edition_version", "source_file", "section_path", "spec_section_heading",
                   "anchor_id", "html_subheading", "table_kind", "table_index", "table_class", "row_index", "row_type", "row_label",
                   "row_label_clean", "col_header", "value_text", "footnote_markers", "table_subheading",
                   "under_table_subheading", "rowspan_continuation", "described_product", "product_block",
                   "is_primary_product", "attribute_key", "mapping_note"]
    write_csv(out / "spec_rows.csv", rows, spec_fields)

    value_rows = [r for r in rows if r["row_type"] not in ("header", "subheading")]

    # ---- label inventory
    inv = defaultdict(lambda: {"rows": 0, "manuals": set(), "models": set(), "keys": Counter(), "notes": Counter(),
                               "printed": Counter(), "example": "", "kinds": Counter()})
    for r in value_rows:
        e = inv[(r["language"], r["row_label_clean"])]
        e["rows"] += 1
        e["manuals"].add(r["source_file"])
        e["models"].add(r["model"])
        e["keys"][r["attribute_key"]] += 1
        if r["mapping_note"]:
            e["notes"][r["mapping_note"]] += 1
        e["printed"][r["row_label"]] += 1
        e["kinds"][r["table_kind"]] += 1
        if not e["example"] and r["value_text"]:
            e["example"] = r["value_text"][:120]
    inv_rows = []
    for (lang, label), e in sorted(inv.items()):
        keys = [k for k, _ in e["keys"].most_common()]
        key = keys[0] if len(keys) == 1 else ("UNMAPPED" if "UNMAPPED" in keys and len(keys) == 1 else " | ".join(keys))
        note = "; ".join(n for n, _ in e["notes"].most_common(3))
        if len(keys) > 1:
            note = (note + "; " if note else "") + "maps differently by section heading (input/output) or table"
        inv_rows.append({"language": lang, "row_label": label, "printed_variants": " ‖ ".join(list(e["printed"])[:4]),
                         "rows": e["rows"], "manuals": len(e["manuals"]), "models": len(e["models"]),
                         "table_kinds": ", ".join(e["kinds"]), "attribute_key": key, "mapping_note": note,
                         "naming_hint_from_row_key_mapping": next((h for h in hint_keys if h in key), ""),
                         "example_value": e["example"]})
    write_csv(out / "label_inventory.csv", inv_rows)

    # ---- facts
    editions = defaultdict(lambda: defaultdict(list))  # (model, region) -> lang -> rows
    for r in value_rows:
        editions[(r["model"], r["region"])][r["language"]].append(r)
    all_editions = defaultdict(set)
    for m in manuals:
        all_editions[(m["model"], m["region"])].add(m["language"])
    meta_by = {(m["model"], m["region"], m["language"]): m for m in manuals}

    def usable(r: dict) -> bool:
        if r["attribute_key"] in ("", "UNMAPPED", "runtime_estimate"):
            return False
        if r["table_kind"] in FACT_KINDS:
            return True
        return r["table_kind"] == "spec_like_elsewhere" and r["attribute_key"] in SPEC_LIKE_FACT_KEYS

    def group(rs: list[dict], primary_only: bool = True) -> dict[tuple[str, str], list[dict]]:
        g = defaultdict(list)
        for r in rs:
            if not usable(r):
                continue
            comp = "" if r.get("is_primary_product") in ("yes", "n/a", None) else r["product_block"]
            if primary_only and comp:
                continue
            if not primary_only and not comp:
                continue
            key = (comp, r["attribute_key"])
            sig = (r["row_label"], r["col_header"], r["value_text"])
            if sig not in {(x["row_label"], x["col_header"], x["value_text"]) for x in g[key]}:
                g[key].append(r)
        return g

    def joined(rs: list[dict]) -> str:
        if len(rs) == 1 and not rs[0]["col_header"]:
            return rs[0]["value_text"]
        return " ‖ ".join(f"{x['row_label']}{' [' + x['col_header'] + ']' if x['col_header'] else ''}: {x['value_text']}" for x in rs)

    facts, matrix, comp_facts = [], [], []
    region_diff = Counter()
    lang_disagree = []
    for mr in all_editions:
        editions.setdefault(mr, defaultdict(list))
        for lg in all_editions[mr]:
            editions[mr].setdefault(lg, [])
    for (model, region), langs in sorted(editions.items()):
        avail = sorted(all_editions[(model, region)])
        primary = "en" if "en" in langs else MAIN_LANG.get(region) if MAIN_LANG.get(region) in langs else \
            max(langs, key=lambda lg: len(langs[lg]))
        prim_groups = group(langs[primary])
        other_groups = {lg: group(rs) for lg, rs in langs.items() if lg != primary}
        meta = meta_by[(model, region, primary)]
        cat = cat_models.get(model, {})
        mrow = {"model": model, "region": region, "primary_language": primary, "editions": " ".join(avail),
                "category": cat.get("category", "通用指南" if model in guides else ""), "series": cat.get("series", ""),
                "capacity_tier": cat.get("capacity", ""), "short_name": cat.get("short", guides.get(model, {}).get("short", "")),
                "edition_version": meta["edition_version"]}
        derived_src = defaultdict(list)
        for (comp, key), rs in sorted(prim_groups.items()):
            text = joined(rs)
            first = rs[0]
            parsed = parse_value(key, rs[0]["value_text"] if len(rs) == 1 else text)
            if len(rs) > 1 and key in ("usb_c_output", "usb_a_output", "ac_output_port", "dc12_car_output"):
                parsed["numeric_detail"] = (parsed.get("numeric_detail", "") + f"; {len(rs)} rows").strip("; ")
            # language comparison
            pvals = [x["value_text"] for x in rs]
            comp_res, kinds = [], []
            for lg, g in sorted(other_groups.items()):
                ors = g.get((comp, key))
                if not ors:
                    comp_res.append(f"{lg}: absent")
                    continue
                verdict = compare_values(key, pvals, [x["value_text"] for x in ors])
                if verdict == "agree":
                    continue
                otext = joined(ors)
                kinds.append(verdict)
                comp_res.append(f"{lg} ({verdict}): {otext[:160]}")
                lang_disagree.append({"model": model, "region": region, "attribute": key, "verdict": verdict,
                                      "primary_language": primary, "primary_value": text[:200], "other_language": lg,
                                      "other_value": otext[:200]})
            if not other_groups:
                lang_status = "only one edition"
            elif not comp_res:
                lang_status = "agree (" + ", ".join(sorted(other_groups)) + ")"
            elif not kinds:
                lang_status = "agree where present; " + "; ".join(comp_res)
            else:
                lang_status = ("differ: " if "differ" in kinds else "extent differs: ") + "; ".join(comp_res)
            facts.append({"model": model, "region": region, "attribute_key": key,
                          "attribute_en": A.get(key, ("", key))[1], "value_text": text, "rows_combined": len(rs),
                          **{k: v for k, v in parsed.items() if not k.startswith("_")},
                          "derived_from": "", "source_language": primary, "source_edition": meta["edition_version"],
                          "source_file": first["source_file"], "source_section": first["section_path"],
                          "source_anchor": first["anchor_id"], "source_table_kind": first["table_kind"],
                          "language_check": lang_status, "extraction_date": EXTRACTION_DATE})
            mrow[key] = text
            derived_src[key] = rs
        # ---- derived numeric attributes (read only from printed text)
        def add_derived(key: str, value: str, unit: str, src: str, text: str, extra: dict | None = None) -> None:
            if value in ("", None):
                return
            facts.append({"model": model, "region": region, "attribute_key": key, "attribute_en": DERIVED[key][1],
                          "value_text": text, "rows_combined": "", "value_metric": value, "unit_metric": unit,
                          **(extra or {}), "derived_from": src, "source_language": primary,
                          "source_edition": meta["edition_version"], "source_file": meta["source_file"],
                          "language_check": "see source attribute", "extraction_date": EXTRACTION_DATE})
            mrow[key] = value

        acrows = derived_src.get("ac_output_port", [])
        tot = derived_src.get("ac_output_total", [])
        totout = [r for r in derived_src.get("total_output", []) if parse_power(r["value_text"])["surge_w"]]
        if tot:
            p = parse_power(tot[0]["value_text"])
            add_derived("ac_continuous_w", p["value_metric"], "W", "ac_output_total", tot[0]["value_text"])
        elif totout:
            p = parse_power(totout[0]["value_text"])
            add_derived("ac_continuous_w", p["value_metric"], "W", "total_output (states surge)", totout[0]["value_text"])
        elif acrows and ac_total_in_text(" | ".join(r["value_text"] for r in acrows)) is not None:
            add_derived("ac_continuous_w", fmt(ac_total_in_text(" | ".join(r["value_text"] for r in acrows))), "W",
                        "total printed inside AC-output rows", joined(acrows)[:200])
        elif len({r["row_label"] for r in acrows}) == 1:
            p = parse_power(acrows[0]["value_text"])
            add_derived("ac_continuous_w", p["value_metric"], "W", "only AC-output row", acrows[0]["value_text"])
        surges = [(parse_power(r["value_text"])["surge_w"], r) for r in tot + totout + acrows]
        surges = [(float(s), r) for s, r in surges if s]
        if surges:
            s, r = max(surges, key=lambda x: x[0])
            add_derived("ac_surge_w", fmt(s), "W", r["attribute_key"], r["value_text"])
        main_ac = [r for r in acrows if r["rowspan_continuation"] == "no"]
        counts = [port_count(r["row_label"]) for r in main_ac]
        if main_ac and all(c is not None for c in counts):
            add_derived("ac_outlet_count", str(sum(counts)), "count", "ac_output_port labels",
                        " ‖ ".join(r["row_label"] for r in main_ac))
        types = sorted({m.group(0) for r in acrows + tot for m in re.finditer(r"NEMA ?[A-Z]?\d+-\d+R?|TT-30R?|Type [A-Z]\b|BS ?1363|Schuko|AS/NZS ?3112|JIS C ?8303", r["row_label"] + " " + r["value_text"])})
        if types:
            add_derived("ac_outlet_type", ", ".join(types), "", "ac_output_port labels/values", ", ".join(types))
        if acrows or tot:
            vs = sorted({v for r in acrows + tot for v in parse_power(r["value_text"])["_volts"]})
            hz = sorted({h for r in acrows + tot for h in parse_power(r["value_text"])["_hz"]})
            if vs:
                add_derived("ac_output_voltage_v", "/".join(fmt(v) for v in vs), "V", "ac_output_port/total values", joined(acrows + tot)[:200])
            if hz:
                add_derived("ac_output_frequency_hz", "/".join(fmt(h) for h in hz), "Hz", "ac_output_port/total values", joined(acrows + tot)[:200])
        usbc = [r for r in derived_src.get("usb_c_output", []) if r["rowspan_continuation"] == "no"]
        if usbc:
            cs = [port_count(r["row_label"]) for r in usbc]
            if all(c is not None for c in cs):
                add_derived("usb_c_port_count", str(sum(cs)), "count", "usb_c_output labels", " ‖ ".join(r["row_label"] for r in usbc))
            elif all(re.search(r"USB-C\d", r["row_label"]) for r in usbc) and all("/" not in r["row_label"] for r in usbc):
                add_derived("usb_c_port_count", str(len({r["row_label"] for r in usbc})), "count",
                            "distinct USB-Cn rows", " ‖ ".join(r["row_label"] for r in usbc))
            ws = [float(p["value_metric"]) for p in (parse_power(r["value_text"] + " " + r["row_label"]) for r in usbc) if p["value_metric"]]
            if ws:
                add_derived("usb_c_max_w", fmt(max(ws)), "W", "usb_c_output rows", joined(usbc)[:200])
        usba = [r for r in derived_src.get("usb_a_output", []) if r["rowspan_continuation"] == "no"]
        if usba:
            cs = [port_count(r["row_label"]) for r in usba]
            if all(c is not None for c in cs):
                add_derived("usb_a_port_count", str(sum(cs)), "count", "usb_a_output labels", " ‖ ".join(r["row_label"] for r in usba))
        aci = derived_src.get("ac_input", [])
        ws = [float(p["value_metric"]) for p in (parse_power(r["value_text"]) for r in aci) if p["value_metric"]]
        if ws:
            add_derived("ac_input_max_w", fmt(max(ws)), "W", "ac_input rows", joined(aci)[:200])
        dci = derived_src.get("dc_input", []) + derived_src.get("dc8020_input", []) + derived_src.get("solar_input", []) + \
            derived_src.get("solar_input_high_voltage", []) + derived_src.get("solar_input_low_voltage", [])
        ps = [(parse_power(r["value_text"]), r) for r in dci]
        ws = [float(p["value_metric"]) for p, _ in ps if p["value_metric"]]
        if ws:
            add_derived("dc_input_max_w", fmt(max(ws)), "W", "dc/dc8020/solar input rows", joined(dci)[:200])
        sol = [(parse_power(solar_text(r)), r) for r in dci if solar_text(r)]
        ws = [float(p["value_metric"]) for p, _ in sol if p["value_metric"]]
        if ws:
            add_derived("solar_input_max_w", fmt(max(ws)), "W", "rows or cell segments labelled solar/PV", " | ".join(solar_text(r) for _, r in sol)[:200])
        vs = [v for p, _ in sol for v in p["_volts"]]
        if len(vs) >= 2:
            add_derived("solar_input_voltage_range", f"{fmt(min(vs))}-{fmt(max(vs))}", "V",
                        "rows or cell segments labelled solar/PV", " | ".join(solar_text(r) for _, r in sol)[:200])
        car = derived_src.get("car_input", [])
        ws = [float(p["value_metric"]) for p in (parse_power(r["value_text"]) for r in car) if p["value_metric"]]
        if ws:
            add_derived("car_input_max_w", fmt(max(ws)), "W", "car_input rows", joined(car)[:200])
        ups = derived_src.get("ups", [])
        ms = sorted({m for r in ups for m in parse_power(r["value_text"])["_ms"]})
        if ms:
            add_derived("ups_switch_ms", "/".join(fmt(m) for m in ms), "ms", "ups row", joined(ups)[:200])
        if derived_src.get("expansion_port_dc") or derived_src.get("expansion_port_ac"):
            add_derived("expandable", "yes", "", "expansion_port rows",
                        joined(derived_src.get("expansion_port_dc", []) + derived_src.get("expansion_port_ac", []))[:200])
        # numeric matrix columns from parsed facts
        for f in facts[::-1]:
            if f["model"] != model or f["region"] != region:
                break
            k = f["attribute_key"]
            if k in ("capacity_wh", "cycle_life", "pv_peak_power", "pv_voc", "pv_isc", "pv_vmp", "warranty_period"):
                mrow[f"{k}#num"] = f.get("value_metric", "")
            if k in ("weight", "net_weight"):
                mrow[f"{k}#kg"] = f.get("value_metric", "")
                mrow[f"{k}#lb"] = f.get("value_imperial", "")
            if k in ("dimensions", "dimensions_folded", "dimensions_unfolded", "dimensions_and_weight"):
                mrow[f"{k}#mm"] = f.get("value_metric", "")
            if k == "dimensions_and_weight":
                w = parse_value("weight", f["value_text"])
                mrow["dimensions_and_weight#kg"] = w["value_metric"]
            if k in ("charge_temperature", "discharge_temperature", "operating_temperature"):
                mrow[f"{k}#min_c"] = f.get("range_min", "")
                mrow[f"{k}#max_c"] = f.get("range_max", "")
            if k == "ip_rating":
                mrow["ip_rating#code"] = f.get("value_metric", "")
        matrix.append(mrow)
        for (comp, key), rs in sorted(group(langs[primary], primary_only=False).items()):
            comp_facts.append({"model": model, "region": region, "component_product": comp, "attribute_key": key,
                               "value_text": joined(rs), "source_language": primary, "source_file": rs[0]["source_file"],
                               "source_section": rs[0]["section_path"], "extraction_date": EXTRACTION_DATE})

    fact_fields = ["model", "region", "attribute_key", "attribute_en", "value_text", "rows_combined", "value_metric",
                   "unit_metric", "value_imperial", "unit_imperial", "range_min", "range_max", "range_unit", "qualifier",
                   "condition", "surge_w", "numeric_detail", "derived_from", "source_language", "source_edition",
                   "source_file", "source_section", "source_anchor", "source_table_kind", "language_check",
                   "extraction_date"]
    write_csv(out / "facts_candidate.csv", facts, fact_fields)
    write_csv(out / "facts_components.csv", comp_facts)

    # ---- attribute dictionary with coverage
    cov_models, cov_pairs, cov_cats = defaultdict(set), defaultdict(set), defaultdict(set)
    for f in facts:
        cov_models[f["attribute_key"]].add(f["model"])
        cov_pairs[f["attribute_key"]].add((f["model"], f["region"]))
        cat = cat_models.get(f["model"], {}).get("category") or ("通用指南" if f["model"] in guides else "未分类")
        cov_cats[f["attribute_key"]].add(cat)
    labels_per_key = Counter()
    for e in inv_rows:
        for k in e["attribute_key"].split(" | "):
            labels_per_key[k] += 1
    dict_rows = []
    intended = {"solar": "太阳能板; 便携储能 (input)", "battery": "便携储能; 家庭备电; 加电包",
                "AC output": "便携储能; 家庭备电", "expansion": "便携储能; 家庭备电"}
    for source, table in (("bottom-up", A), ("derived", DERIVED), ("top-down", TOPDOWN)):
        for key, (zh, en, grp, unit, definition, comp) in table.items():
            dict_rows.append({"key": key, "name_zh": zh, "name_en": en, "group": grp, "canonical_unit": unit,
                              "definition": definition, "origin": source,
                              "applies_to_categories_observed": "; ".join(sorted(cov_cats.get(key, []))) or intended.get(grp, ""),
                              "models_with_value": len(cov_models.get(key, ())),
                              "model_region_pairs_with_value": len(cov_pairs.get(key, ())),
                              "distinct_labels_mapped": labels_per_key.get(key, 0), "comparison_attribute": comp})
    # keys produced by the mapper but missing in A
    for key in sorted(set(cov_models) - set(A) - set(DERIVED) - set(TOPDOWN)):
        dict_rows.append({"key": key, "name_en": key, "origin": "bottom-up (undocumented)",
                          "models_with_value": len(cov_models[key]), "model_region_pairs_with_value": len(cov_pairs[key])})
    write_csv(out / "attribute_dictionary_v0.csv", dict_rows)

    # ---- matrix
    keys_order = [k for k in A if k in cov_models] + [k for k in DERIVED if k in cov_models]
    num_cols = sorted({k for r in matrix for k in r if "#" in k})
    base_cols = ["model", "region", "primary_language", "editions", "category", "series", "capacity_tier", "short_name",
                 "edition_version"]
    write_csv(out / "matrix_candidate.csv", matrix, base_cols + keys_order + num_cols)

    # ---- report data
    regional = defaultdict(lambda: Counter())
    by_model = defaultdict(dict)
    for f in facts:
        if f["derived_from"]:
            continue
        by_model[f["model"]].setdefault(f["attribute_key"], {})[f["region"]] = f["value_text"]
    region_pairs = 0
    region_examples = []
    for model, attrs in sorted(by_model.items()):
        regions = sorted({r for a in attrs.values() for r in a})
        if len(regions) < 2:
            continue
        region_pairs += 1
        for key, vals in sorted(attrs.items()):
            if len(vals) < len(regions):
                regional[key]["absent in some region"] += 1
                continue
            items = sorted(vals.items())
            verdicts = {compare_values(key, [items[0][1]], [v]) for _, v in items[1:]}
            verdict = "differ" if "differ" in verdicts else "extent" if "extent" in verdicts else "agree"
            regional[key]["figures differ" if verdict == "differ" else "same figures (format/extent only)" if verdict == "extent" else "same"] += 1
            if verdict == "differ":
                region_examples.append({"model": model, "attribute_key": key,
                                        **{f"value_{r}": v[:140] for r, v in items}})
    write_csv(out / "work_region_difference_examples.csv", region_examples)
    write_csv(out / "work_language_disagreements.csv", lang_disagree)
    rd = [{"attribute_key": k, **v} for k, v in sorted(regional.items(), key=lambda kv: -kv[1]["figures differ"])]
    write_csv(out / "work_region_differences.csv", rd)
    json.dump({"region_models": region_pairs, "checklist": CHECKLIST}, open(out / "work_report_data.json", "w"))
    print(f"facts={len(facts)} components={len(comp_facts)} matrix={len(matrix)} labels={len(inv_rows)} "
          f"lang_disagree={len(lang_disagree)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
