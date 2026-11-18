"""Printed specification values -> numbers in canonical units. Never fills a value the text does not print.

``parse_value(key, text)`` returns the metric value and unit, an imperial value where printed, a range (voltage,
temperature), the qualifier words (約 / about …), a condition (cycle-life end point) and a surge figure for power
rows. Which parser applies is decided by the attribute key; power rows share ``parse_power``.
"""
from __future__ import annotations

import re

NUM = r"\d+(?:[.,]\d+)*"
QUAL = re.compile(r"\b(about|approx\.?|approximately|ca\.|circa|environ|aprox\.?|aproximadamente|około|ok\.|близько|приблизно|ongeveer|etwa|ungefähr|cerca de|aproximadamente)(?=\s|\d)|約|约|大约|약", re.I)
SURGE = re.compile(r"surge|peak|突波|瞬間最大|瞬时|瞬時|峰值|crête|pico|picco|piek|szczyt|пік|spitze|spitzen|皮克|サージ", re.I)


def to_float(s: str, unit: str = "") -> float | None:
    s = s.strip()
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", s):
        return float(s.replace(",", ""))
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s) and unit.lower() in ("w", "wh", "cycles", "mah", "kwh"):
        return float(s.replace(".", ""))
    if s.count(",") == 1 and "." not in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def fmt(v: float | None) -> str:
    if v is None:
        return ""
    return f"{v:.4f}".rstrip("0").rstrip(".")


def qualifier(text: str) -> str:
    return " ".join(dict.fromkeys(m.group(0) for m in QUAL.finditer(text)))


def all_units(text: str, unit_pat: str, unit_name: str) -> list[float]:
    out = []
    for m in re.finditer(r"(?<![\d.,])(" + NUM + r")\s?(?:" + unit_pat + r")(?![a-zA-Z])", text):
        v = to_float(m.group(1), unit_name)
        if v is not None:
            out.append(v)
    return out


def parse_weight(text: str) -> dict:
    text = re.sub(r"\s*±\s*[\d.,]+\s*(kg|g|lbs?)?", "", text).replace("(", "").replace(")", "")
    kg = all_units(text, r"kg|キロ", "kg")
    g = all_units(text, r"g(?!\w)|グラム", "g")
    lb = all_units(text, r"lbs?|pounds|lb\.", "lb")
    metric = kg[0] if kg else (g[0] / 1000 if g else None)
    return {"value_metric": fmt(metric), "unit_metric": "kg" if metric is not None else "",
            "value_imperial": fmt(lb[0]) if lb else "", "unit_imperial": "lb" if lb else "",
            "numeric_detail": ("from g" if not kg and g else "")}


DIM = re.compile(r"(" + NUM + r")\s?(mm|cm|мм|см|in|inch|inches|\"|″)?\s?[x×*X]\s?(" + NUM + r")\s?(mm|cm|мм|см|in|inch|inches|\"|″)?\s?[x×*X]\s?(" + NUM + r")\s?(mm|cm|мм|см|m(?!\w)|in|inch|inches|\"|″)", re.I)


def parse_dims(text: str) -> dict:
    metric = imperial = None
    for m in DIM.finditer(text):
        unit = (m.group(6) or "").lower().replace("мм", "mm").replace("см", "cm")
        vals = [to_float(m.group(i)) for i in (1, 3, 5)]
        if unit in ("mm", "cm", "m") and metric is None:
            factor = {"mm": 1, "cm": 10, "m": 1000}[unit]
            metric = ("×".join(fmt(v * factor) for v in vals if v is not None), "mm", unit)
        elif unit in ("in", "inch", "inches", '"', "″") and imperial is None:
            imperial = ("×".join(fmt(v) for v in vals if v is not None), "in")
    return {"value_metric": metric[0] if metric else "", "unit_metric": "mm" if metric else "",
            "value_imperial": imperial[0] if imperial else "", "unit_imperial": "in" if imperial else "",
            "numeric_detail": f"printed in {metric[2]}" if metric and metric[2] != "mm" else ""}


TEMP_RANGE = re.compile(r"(-?\s?" + NUM + r")\s?(°C|°F|℃|℉|°)?\s?(?:~|～|to|-|–|—|bis|à|a|al|до|do|tot|〜)\s?(-?\s?" + NUM + r")\s?(°C|°F|℃|℉)", re.I)


def parse_temp(text: str) -> dict:
    c = f = None
    for m in TEMP_RANGE.finditer(text):
        unit = m.group(4).upper().replace("℃", "°C").replace("℉", "°F")
        lo, hi = to_float(m.group(1).replace(" ", "")), to_float(m.group(3).replace(" ", ""))
        if unit == "°C" and c is None:
            c = (lo, hi)
        elif unit == "°F" and f is None:
            f = (lo, hi)
    return {"range_min": fmt(c[0]) if c else "", "range_max": fmt(c[1]) if c else "", "range_unit": "°C" if c else "",
            "value_imperial": f"{fmt(f[0])}~{fmt(f[1])}" if f else "", "unit_imperial": "°F" if f else "",
            "numeric_detail": "several ranges printed" if len(TEMP_RANGE.findall(text)) > 2 else ""}


def parse_cycles(text: str) -> dict:
    m = re.search(r"(?<![\d.])(\d{1,2}(?:[,.]\d{3})+|\d{3,5})\s?\+?\s?(cycles?|zyklen|ciclos|cicli|cycli|cykl\w*|циклів|回|次|サイクル|사이클)?", text, re.I)
    cond = re.search(r"(\d{2,3})\s?%\s?\+?", text)
    v = to_float(m.group(1).replace(".", "").replace(",", "")) if m else None
    return {"value_metric": fmt(v), "unit_metric": "cycles" if v is not None else "",
            "condition": (f"to {cond.group(1)}% capacity (as printed: {text})" if cond else ""),
            "numeric_detail": ""}


def parse_capacity(text: str) -> dict:
    wh = all_units(text, r"Wh", "wh")
    kwh = all_units(text, r"kWh", "kwh")
    ah = all_units(text, r"Ah", "ah")
    v = all_units(text, r"V(?:dc|DC| DC)?", "v")
    val = wh[0] if wh else (kwh[0] * 1000 if kwh else None)
    detail = []
    if ah:
        detail.append(f"{fmt(ah[0])} Ah")
    if v:
        detail.append(f"{fmt(v[0])} V")
    return {"value_metric": fmt(val), "unit_metric": "Wh" if val is not None else "",
            "numeric_detail": "; ".join(detail) + ("; from kWh" if not wh and kwh else "")}


def parse_power(text: str) -> dict:
    """Electrical rating cell: max W (rated), surge W, voltage range, frequency, current."""
    watts = []
    surge = []
    for m in re.finditer(r"(?<![\d.,])(" + NUM + r")\s?(W|Вт|瓦)(?![a-zA-Z])", text):
        val = to_float(m.group(1), "w")
        if val is None:
            continue
        before = re.split(r"[,，;；)）|/]", text[max(0, m.start() - 10): m.start()])[-1]
        after = re.split(r"[,，;；(（|/]", text[m.end(): m.end() + 20])[0]
        (surge if SURGE.search(before) or SURGE.search(after) else watts).append(val)
    volts = all_units(text, r"V(?![a-zA-Z])|В(?![а-яА-Я])", "v")
    hz = all_units(text, r"Hz", "hz")
    amps = all_units(text, r"A(?![a-zA-Z])|А(?![а-яА-Я])", "a")
    ms = all_units(text, r"ms", "ms")
    detail = []
    if volts:
        detail.append(f"V {fmt(min(volts))}-{fmt(max(volts))}" if len(set(volts)) > 1 else f"V {fmt(volts[0])}")
    if hz:
        detail.append("Hz " + "/".join(fmt(h) for h in dict.fromkeys(hz)))
    if amps:
        detail.append(f"A max {fmt(max(amps))}")
    if ms:
        detail.append(f"ms {fmt(min(ms))}-{fmt(max(ms))}" if len(set(ms)) > 1 else f"ms {fmt(ms[0])}")
    return {"value_metric": fmt(max(watts)) if watts else "", "unit_metric": "W" if watts else "",
            "surge_w": fmt(max(surge)) if surge else "",
            "range_min": fmt(min(volts)) if volts else "", "range_max": fmt(max(volts)) if volts else "",
            "range_unit": "V" if volts else "",
            "numeric_detail": "; ".join(detail) + (f"; all W printed: {', '.join(fmt(w) for w in watts)}" if len(watts) > 1 else ""),
            "_ms": ms, "_volts": volts, "_hz": hz}


def parse_hours(text: str) -> dict:
    h = all_units(text, r"h|hrs?|hours?|時間|小时|小時|std\.?|stunden|heures|horas|ore|uur|godz\.?|год", "h")
    mins = all_units(text, r"min|minutes?|分", "min")
    return {"value_metric": fmt(h[0]) if h else (fmt(mins[0] / 60) if mins else ""),
            "unit_metric": "h" if (h or mins) else "", "numeric_detail": "from minutes" if not h and mins else ""}


def parse_years(text: str) -> dict:
    y = all_units(text, r"years?|yrs?|年|jahre|ans|años|anni|jaar|lat|роки|років|anos|\| years", "y")
    mo = all_units(text, r"months?|か月|ヶ月|ケ月|カ月|個月|monate|mois|meses|mesi|maanden|miesięcy|місяців", "m")
    if not y:
        m = re.match(r"^\s*(\d+)\s*\|\s*years", text, re.I)
        if m:
            y = [float(m.group(1))]
    return {"value_metric": fmt(y[0]) if y else (fmt(mo[0] / 12) if mo else ""),
            "unit_metric": "year" if (y or mo) else "", "numeric_detail": "from months" if not y and mo else ""}


def parse_first(text: str, unit_pat: str, unit: str) -> dict:
    v = all_units(text, unit_pat, unit.lower())
    return {"value_metric": fmt(v[0]) if v else "", "unit_metric": unit if v else ""}


def parse_ip(text: str) -> dict:
    m = re.search(r"IP[X\d]\d", text)
    return {"value_metric": m.group(0) if m else "", "unit_metric": ""}


PARSERS = {
    "capacity_wh": parse_capacity, "weight_kg": parse_weight, "net_weight": parse_weight,
    "dimensions_mm": parse_dims, "dimensions_folded": parse_dims, "dimensions_unfolded": parse_dims,
    "charge_temperature": parse_temp, "discharge_temp_range": parse_temp, "storage_temperature": parse_temp,
    "operating_temperature": parse_temp, "cycle_life": parse_cycles, "ip_rating": parse_ip,
    "ac_charge_time": parse_hours, "car_charge_time": parse_hours, "solar_charge_time": parse_hours,
    "warranty_period": parse_years,
    "panel_power_w": lambda t: parse_first(t, r"W", "W"), "pv_vmp": lambda t: parse_first(t, r"V", "V"),
    "pv_voc": lambda t: parse_first(t, r"V", "V"), "pv_imp": lambda t: parse_first(t, r"A", "A"),
    "pv_isc": lambda t: parse_first(t, r"A", "A"), "pv_max_system_voltage": lambda t: parse_first(t, r"V", "V"),
    "operating_altitude": lambda t: parse_first(t, r"m(?!a)", "m"),
}
POWER_KEYS = {"ac_output_port", "ac_output_total", "ac_output_bypass", "ac_parallel_output", "ac_input", "ac_input_bypass",
              "dc_input", "dc8020_input", "car_input", "solar_input", "solar_input_high_voltage",
              "solar_input_low_voltage", "usb_c_output", "usb_c_input", "usb_a_output", "usb_output_total",
              "usb_combined_output", "dc12_car_output", "dc_output", "total_output", "output_w", "input_rating",
              "output_rating", "expansion_port_dc", "expansion_port_ac", "ups", "heating_module_input",
              "heating_module_power", "ac_voltage_nominal"}


def parse_value(key: str, text: str) -> dict:
    base = {"value_metric": "", "unit_metric": "", "value_imperial": "", "unit_imperial": "", "range_min": "",
            "range_max": "", "range_unit": "", "qualifier": qualifier(text), "condition": "", "surge_w": "",
            "numeric_detail": ""}
    text = re.sub(r"(?<=\d)[ \u202f\u00a0](?=\d{3}\b)", "", text)
    if key in PARSERS:
        base.update(PARSERS[key](text))
    elif key in POWER_KEYS:
        base.update(parse_power(text))
    if key == "dimensions_and_weight":
        d, w = parse_dims(text), parse_weight(text)
        base.update({"value_metric": d["value_metric"], "unit_metric": d["unit_metric"],
                     "value_imperial": d["value_imperial"], "unit_imperial": d["unit_imperial"],
                     "numeric_detail": f"weight {w['value_metric']} kg" if w["value_metric"] else ""})
    return base


def port_count(label: str) -> int | None:
    m = re.match(r"^\s*(\d+)\s*[x×]|^\s*(\d+)\s+(?=\D)", label)
    if m:
        return int(m.group(1) or m.group(2))
    m = re.search(r"[x×]\s*(\d+)\s*$", label)
    return int(m.group(1)) if m else None


AC_TOTAL_IN_VALUE = re.compile(r"(?:合計|合计|总计|總計|total|in total|insgesamt|totale?)\s?:?\s?(" + NUM + r")\s?W|(" + NUM + r")\s?W\s?(?:rated )?(?:in total|total|insgesamt|au total|en total|in totale)", re.I)


def ac_total_in_text(text: str) -> float | None:
    """A whole-unit AC total printed inside a port row ("3ポート合計1000W", "1000 W rated in total")."""
    vals = []
    for m in AC_TOTAL_IN_VALUE.finditer(text):
        before = text[max(0, m.start() - 6): m.start()]
        if SURGE.search(before):
            continue
        v = to_float(m.group(1) or m.group(2), "w")
        if v is not None:
            vals.append(v)
    return max(vals) if vals else None
