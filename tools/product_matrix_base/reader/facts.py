"""Facts from the captured rows: one value per model × market × attribute, read from one primary language edition.

The primary edition of a model in a market is the English one, else the market's main language
(``market_languages.json``), else the edition with the most rows. Rows of the same attribute in that edition are
joined into one value; the other editions are compared with it and the outcome is kept as the language check (they
are never merged). A manual that prints the tables of a bundled or separately sold component (a battery pack, a
transfer switch, a panel) splits at each product-name row: blocks other than the manual's own product are component
facts, never the main product's. Derived figures (whole-unit AC output, surge, port counts, input maxima) are read
only from printed text and say which rows they come from.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.product_matrix_base.reader.labels import UNMAPPED, map_label
from tools.product_matrix_base.reader.values import (
    PARSERS, ac_total_in_text, fmt, parse_power, parse_value, port_count, to_float,
)

FACT_KINDS = {"spec_section", "spec_class_elsewhere"}
SPEC_LIKE_FACT_KEYS = {"ac_charge_time", "car_charge_time", "solar_charge_time", "warranty_period", "in_box_contents"}
MULTI_ROW_PORTS = ("usb_c_output", "usb_a_output", "ac_output_port", "dc12_car_output")
MARKET_LANGUAGES = Path(__file__).with_name("market_languages.json")
_URL = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\w+")
_SUBDIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SOLAR_SEGMENT = re.compile(r"PV|solar|ソーラー|太阳能|solaire|Solar|fotovolt|photovolt", re.I)
_OUTLET_TYPE = re.compile(r"NEMA ?[A-Z]?\d+-\d+R?|TT-30R?|Type [A-Z]\b|BS ?1363|Schuko|AS/NZS ?3112|JIS C ?8303")


def scrub(text: str) -> str:
    """Links and addresses never travel with a value."""
    return _URL.sub("[link removed]", text or "")


def context_of(row: dict[str, Any]) -> str:
    parts = (row["section_path"].split(" > ")[-1], row["html_subheading"], row["table_subheading"])
    return " > ".join(part for part in parts if part)


def map_rows(rows: list[dict[str, Any]]) -> None:
    """Give every value row its attribute key and note; header and sub-heading rows get none."""
    for row in rows:
        if row["row_type"] in ("header", "subheading"):
            row["attribute_key"], row["mapping_note"] = "", f"{row['row_type']} row (not a value)"
            continue
        key, note = map_label(row["row_label_clean"], context_of(row), row["table_kind"], row["section_path"])
        if key == "capacity_wh" and not re.search(r"Wh", row["value_text"]):
            key, note = "capacity_other", "capacity label but no Wh printed (volume or charge, e.g. cooler or power bank)"
        row["attribute_key"], row["mapping_note"] = key, note
        for field in ("row_label", "row_label_clean", "value_text", "section_path", "described_product"):
            row[field] = scrub(row[field])


def _blocks_of(rows: list[dict[str, Any]]) -> tuple[list[str], set[str]]:
    """Product-name blocks in order, and the blocks that name the manual's own model."""
    current, names = "", []
    model = rows[0]["model"]
    for row in rows:
        if row["table_kind"] not in FACT_KINDS:
            row["product_block"], row["is_primary_product"] = "", "n/a"
            continue
        if row["attribute_key"] == "product_name" and row["value_text"]:
            current = row["value_text"]
            if current not in names:
                names.append(current)
        row["product_block"] = current or row["described_product"]
    own = {row["product_block"] for row in rows if row.get("product_block") and (
        model in row["described_product"] or (row["attribute_key"] == "model_number" and model in row["value_text"]))}
    return names, own


def assign_blocks(rows: list[dict[str, Any]]) -> None:
    """Per manual: which rows describe the manual's own product and which a component."""
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_file[row["source_file"]].append(row)
    for file_rows in by_file.values():
        names, own = _blocks_of(file_rows)
        primary = next((n for n in names if n in own), names[0]) if names else None
        model = file_rows[0]["model"]
        for row in file_rows:
            if row["table_kind"] not in FACT_KINDS:
                continue
            if primary is None or row["product_block"] in ("", primary) or (
                    row["described_product"] and model in row["described_product"]):
                row["is_primary_product"] = "yes"
            else:
                row["is_primary_product"] = "no (component)"


def _usable(row: dict[str, Any]) -> bool:
    if row["attribute_key"] in ("", UNMAPPED, "runtime_estimate"):
        return False
    return row["table_kind"] in FACT_KINDS or (
        row["table_kind"] == "spec_like_elsewhere" and row["attribute_key"] in SPEC_LIKE_FACT_KEYS)


def group(rows: list[dict[str, Any]], components: bool = False) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Usable rows by (component, attribute); identical printed rows once. Main product or components only."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not _usable(row):
            continue
        component = "" if row.get("is_primary_product") in ("yes", "n/a", None) else row["product_block"]
        if bool(component) != components:
            continue
        seen = {(r["row_label"], r["col_header"], r["value_text"]) for r in grouped[(component, row["attribute_key"])]}
        if (row["row_label"], row["col_header"], row["value_text"]) not in seen:
            grouped[(component, row["attribute_key"])].append(row)
    return grouped


def joined(rows: list[dict[str, Any]]) -> str:
    """One row's value as printed; several rows as `label [column]: value` joined by ‖."""
    if len(rows) == 1 and not rows[0]["col_header"]:
        return rows[0]["value_text"]
    return " ‖ ".join(f"{r['row_label']}{' [' + r['col_header'] + ']' if r['col_header'] else ''}: {r['value_text']}"
                      for r in rows)


def numbers(text: str) -> list[float]:
    text = re.sub(r"(?<=\d)[   ](?=\d{3}\b)", "", text.translate(_SUBDIGITS))
    found = []
    for match in re.finditer(r"\d+(?:[.,]\d+)*", text):
        value = to_float(match.group(0))
        if value is not None:
            found.append(round(value, 3))
    return sorted(found)


def compare_values(key: str, first: list[str], second: list[str]) -> str:
    """agree / extent (one edition prints a subset, e.g. no imperial figure or an extra row) / differ."""
    if key in PARSERS:
        a, b = parse_value(key, " | ".join(first)), parse_value(key, " | ".join(second))
        figures = (a["value_metric"], a["range_min"], a["range_max"])
        if any(figures) and figures == (b["value_metric"], b["range_min"], b["range_max"]):
            return "agree"
    numbers_a, numbers_b = set(numbers(" ".join(first))), set(numbers(" ".join(second)))
    if numbers_a == numbers_b:
        return "agree"
    return "extent" if numbers_a <= numbers_b or numbers_b <= numbers_a else "differ"


def language_check(key: str, rows: list[dict[str, Any]], others: dict[str, dict]) -> str:
    """How the other language editions of the same model and market print this attribute."""
    if not others:
        return "only one edition"
    printed = [r["value_text"] for r in rows]
    notes, verdicts = [], []
    for language, grouped in sorted(others.items()):
        their = grouped.get(("", key))
        if not their:
            notes.append(f"{language}: absent")
            continue
        verdict = compare_values(key, printed, [r["value_text"] for r in their])
        if verdict != "agree":
            verdicts.append(verdict)
            notes.append(f"{language} ({verdict}): {joined(their)[:160]}")
    if not notes:
        return "agree (" + ", ".join(sorted(others)) + ")"
    if not verdicts:
        return "agree where present; " + "; ".join(notes)
    return ("differ: " if "differ" in verdicts else "extent differs: ") + "; ".join(notes)


def primary_language(market: str, editions: dict[str, list], main: dict[str, str]) -> str:
    if "en" in editions:
        return "en"
    if main.get(market) in editions:
        return main[market]
    return max(editions, key=lambda language: len(editions[language]))


def _fact(model: str, market: str, key: str, rows: list[dict[str, Any]], language: str, check: str
          ) -> dict[str, Any]:
    text = joined(rows)
    parsed = parse_value(key, rows[0]["value_text"] if len(rows) == 1 else text)
    if len(rows) > 1 and key in MULTI_ROW_PORTS:
        parsed["numeric_detail"] = (parsed.get("numeric_detail", "") + f"; {len(rows)} rows").strip("; ")
    first = rows[0]
    return {"model": model, "region": market, "attribute_key": key, "value_text": text, "rows_combined": len(rows),
            **{k: v for k, v in parsed.items() if not k.startswith("_")}, "derived_from": "",
            "source_language": language, "source_file": first["source_file"], "source_section": first["section_path"],
            "source_anchor": first["anchor_id"], "source_table_kind": first["table_kind"], "language_check": check,
            "rows": rows}


def solar_text(row: dict[str, Any]) -> str:
    """The solar part of a shared DC input cell; the whole cell when the label itself is solar."""
    if row["attribute_key"].startswith("solar_input"):
        return row["value_text"]
    return " | ".join(s for s in re.split(r" \| |；|;", row["value_text"]) if _SOLAR_SEGMENT.search(s))


Derive = Callable[[str, str, str, str, str], None]


def _derive_ac(source: dict[str, list], add: Derive) -> None:
    """Whole-unit AC output and surge: a total row; else a 'Total output' row that states surge; else a total printed
    inside the port rows; else the only AC-output row."""
    ports = source.get("ac_output_port", [])
    totals = source.get("ac_output_total", [])
    total_outputs = [r for r in source.get("total_output", []) if parse_power(r["value_text"])["surge_w"]]
    in_ports = ac_total_in_text(" | ".join(r["value_text"] for r in ports)) if ports else None
    if totals:
        add("ac_rated_w", parse_power(totals[0]["value_text"])["value_metric"], "W", "ac_output_total",
            totals[0]["value_text"])
    elif total_outputs:
        add("ac_rated_w", parse_power(total_outputs[0]["value_text"])["value_metric"], "W",
            "total_output (states surge)", total_outputs[0]["value_text"])
    elif ports and in_ports is not None:
        add("ac_rated_w", fmt(in_ports), "W", "total printed inside AC-output rows", joined(ports)[:200])
    elif len({r["row_label"] for r in ports}) == 1:
        add("ac_rated_w", parse_power(ports[0]["value_text"])["value_metric"], "W", "only AC-output row",
            ports[0]["value_text"])
    surges = [(float(s), r) for s, r in ((parse_power(r["value_text"])["surge_w"], r)
                                         for r in totals + total_outputs + ports) if s]
    if surges:
        surge, row = max(surges, key=lambda item: item[0])
        add("ac_surge_w", fmt(surge), "W", row["attribute_key"], row["value_text"])


def _count(rows: list[dict[str, Any]]) -> str | None:
    """The sum of the `N ×` counts in the labels, or None when a label has none."""
    counts = [port_count(r["row_label"]) for r in rows]
    return str(sum(c for c in counts if c is not None)) if rows and all(c is not None for c in counts) else None


def _labels(rows: list[dict[str, Any]]) -> str:
    return " ‖ ".join(r["row_label"] for r in rows)


def _derive_ac_ports(source: dict[str, list], add: Derive) -> None:
    ports = source.get("ac_output_port", [])
    totals = source.get("ac_output_total", [])
    main = [r for r in ports if r["rowspan_continuation"] == "no"]
    count = _count(main)
    if count is not None:
        add("ac_outlet_count", count, "count", "ac_output_port labels", _labels(main))
    printed = [m.group(0) for r in ports + totals for m in _OUTLET_TYPE.finditer(f"{r['row_label']} {r['value_text']}")]
    if printed:
        types = ", ".join(sorted(set(printed)))
        add("ac_outlet_type", types, "", "ac_output_port labels/values", types)
    _derive_ac_electrical(ports + totals, add)


def _derive_ac_electrical(rows: list[dict[str, Any]], add: Derive) -> None:
    volts = sorted({v for r in rows for v in parse_power(r["value_text"])["_volts"]})
    hertz = sorted({h for r in rows for h in parse_power(r["value_text"])["_hz"]})
    if volts:
        add("ac_output_voltage_v", "/".join(fmt(v) for v in volts), "V", "ac_output_port/total values",
            joined(rows)[:200])
    if hertz:
        add("ac_output_frequency_hz", "/".join(fmt(h) for h in hertz), "Hz", "ac_output_port/total values",
            joined(rows)[:200])


def _derive_usb(source: dict[str, list], add: Derive) -> None:
    usb_c = [r for r in source.get("usb_c_output", []) if r["rowspan_continuation"] == "no"]
    if usb_c:
        _derive_usb_c(usb_c, add)
    usb_a = [r for r in source.get("usb_a_output", []) if r["rowspan_continuation"] == "no"]
    count = _count(usb_a)
    if count is not None:
        add("usb_a_port_count", count, "count", "usb_a_output labels", _labels(usb_a))


def _derive_usb_c(rows: list[dict[str, Any]], add: Derive) -> None:
    count = _count(rows)
    if count is not None:
        add("usb_c_port_count", count, "count", "usb_c_output labels", _labels(rows))
    elif all(re.search(r"USB-C\d", r["row_label"]) and "/" not in r["row_label"] for r in rows):
        add("usb_c_port_count", str(len({r["row_label"] for r in rows})), "count", "distinct USB-Cn rows",
            _labels(rows))
    watts = _max_watts(rows, lambda r: r["value_text"] + " " + r["row_label"])
    if watts:
        add("usb_c_max_w", fmt(max(watts)), "W", "usb_c_output rows", joined(rows)[:200])


def _max_watts(rows: list[dict[str, Any]], text: Callable[[dict[str, Any]], str] = lambda r: r["value_text"]
               ) -> list[float]:
    return [float(p["value_metric"]) for p in (parse_power(text(r)) for r in rows if text(r)) if p["value_metric"]]


def _derive_inputs(source: dict[str, list], add: Derive) -> None:
    ac_in = source.get("ac_input", [])
    if _max_watts(ac_in):
        add("ac_input_max_w", fmt(max(_max_watts(ac_in))), "W", "ac_input rows", joined(ac_in)[:200])
    dc_in = [r for key in ("dc_input", "dc8020_input", "solar_input", "solar_input_high_voltage",
                           "solar_input_low_voltage") for r in source.get(key, [])]
    if _max_watts(dc_in):
        add("dc_input_max_w", fmt(max(_max_watts(dc_in))), "W", "dc/dc8020/solar input rows", joined(dc_in)[:200])
    solar = [r for r in dc_in if solar_text(r)]
    solar_watts = _max_watts(solar, solar_text)
    if solar_watts:
        add("solar_input_max_w", fmt(max(solar_watts)), "W", "rows or cell segments labelled solar/PV",
            " | ".join(solar_text(r) for r in solar)[:200])
    volts = [v for r in solar for v in parse_power(solar_text(r))["_volts"]]
    if len(volts) >= 2:
        add("solar_input_voltage_range", f"{fmt(min(volts))}-{fmt(max(volts))}", "V",
            "rows or cell segments labelled solar/PV", " | ".join(solar_text(r) for r in solar)[:200])
    car = source.get("car_input", [])
    if _max_watts(car):
        add("car_input_max_w", fmt(max(_max_watts(car))), "W", "car_input rows", joined(car)[:200])


def _derive_other(source: dict[str, list], add: Derive) -> None:
    ups = source.get("ups", [])
    times = sorted({m for r in ups for m in parse_power(r["value_text"])["_ms"]})
    if times:
        add("ups_switch_ms", "/".join(fmt(m) for m in times), "ms", "ups row", joined(ups)[:200])
    expansion = source.get("expansion_port_dc", []) + source.get("expansion_port_ac", [])
    if expansion:
        add("expansion_port", "yes", "", "expansion_port rows", joined(expansion)[:200])


def derived(model: str, market: str, language: str, source_file: str, source: dict[str, list]
            ) -> list[dict[str, Any]]:
    """The derived figures of one model and market, from its main-product groups."""
    found: list[dict[str, Any]] = []

    def add(key: str, value: str, unit: str, origin: str, text: str) -> None:
        if value not in ("", None):
            found.append({"model": model, "region": market, "attribute_key": key, "value_text": text,
                          "rows_combined": "", "value_metric": value, "unit_metric": unit, "derived_from": origin,
                          "source_language": language, "source_file": source_file,
                          "language_check": "see source attribute", "rows": []})

    for step in (_derive_ac, _derive_ac_ports, _derive_usb, _derive_inputs, _derive_other):
        step(source, add)
    return found


def read_facts(rows: list[dict[str, Any]], editions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Main-product facts and component facts for every model and market that has an edition."""
    main_language = json.loads(MARKET_LANGUAGES.read_text(encoding="utf-8"))["main_language"]
    by_market: dict[tuple[str, str], dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for edition in editions:
        by_market[(edition["model"], edition["market"])].setdefault(edition["language"], [])
    for row in rows:
        if row["row_type"] not in ("header", "subheading"):
            by_market[(row["model"], row["region"])][row["language"]].append(row)
    source_files = {(e["model"], e["market"], e["language"]): e["source_file"] for e in editions}
    facts: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    for (model, market), languages in sorted(by_market.items()):
        language = primary_language(market, languages, main_language)
        own = group(languages[language])
        others = {lang: group(rs) for lang, rs in languages.items() if lang != language}
        source: dict[str, list] = defaultdict(list)
        for (_component, key), grouped in sorted(own.items()):
            facts.append(_fact(model, market, key, grouped, language, language_check(key, grouped, others)))
            source[key] = grouped
        facts += derived(model, market, language, source_files[(model, market, language)], source)
        for (component, key), grouped in sorted(group(languages[language], components=True).items()):
            components.append({"model": model, "region": market, "component_product": component, "attribute_key": key,
                               "value_text": joined(grouped), "source_language": language,
                               "source_file": grouped[0]["source_file"], "source_section": grouped[0]["section_path"],
                               "rows": grouped})
    return {"facts": facts, "components": components}


__all__ = ["assign_blocks", "compare_values", "derived", "group", "joined", "map_rows", "read_facts"]
