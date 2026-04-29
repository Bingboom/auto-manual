#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .renderers_common import _enabled, _scope_allows, apply_vars, rst_escape
from ..signal_words import get_signal_word, get_symbols_notice_label
from ..utils.spec_master import canonicalize_model_token

PH_SYMBOLS_SIGNAL_SECTION_RST = "{{ symbols_signal_section_rst }}"
PH_SYMBOLS_ICON_TABLE_RST = "{{ symbols_icon_table_rst }}"

_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n"}


@dataclass(frozen=True)
class SymbolAsset:
    path: str
    alt: str
    width: str = "40px"


SYMBOL_ASSETS: dict[str, SymbolAsset] = {
    "warning_triangle": SymbolAsset(
        path="templates/word_template/common_assets/symbols/warning_triangle.png",
        alt="Warning symbol.",
    ),
    "read_manual": SymbolAsset(
        path="templates/word_template/common_assets/symbols/read_manual_operator.png",
        alt="Read manual symbol.",
    ),
    "electric_shock": SymbolAsset(
        path="templates/word_template/common_assets/symbols/electric_shock.png",
        alt="Electric shock symbol.",
    ),
    "battery_charging": SymbolAsset(
        path="templates/word_template/common_assets/symbols/battery_charging.png",
        alt="Battery charging symbol.",
    ),
    "explosive_material": SymbolAsset(
        path="templates/word_template/common_assets/symbols/explosive_material.png",
        alt="Explosive material symbol.",
    ),
    "heavy_object": SymbolAsset(
        path="templates/word_template/common_assets/symbols/heavy_object.png",
        alt="Heavy object symbol.",
    ),
    "do_not_dismantle": SymbolAsset(
        path="templates/word_template/common_assets/symbols/do_not_dismantle.png",
        alt="Do not dismantle symbol.",
    ),
    "no_open_flame": SymbolAsset(
        path="templates/word_template/common_assets/symbols/no_open_flame.png",
        alt="No open flame symbol.",
    ),
    "keep_away_from_children": SymbolAsset(
        path="templates/word_template/common_assets/symbols/keep_away_from_children.png",
        alt="Keep away from children symbol.",
    ),
    "li_ion": SymbolAsset(
        path="templates/word_template/common_assets/symbols/li_ion.png",
        alt="Li-ion battery symbol.",
    ),
    "weee": SymbolAsset(
        path="templates/word_template/common_assets/symbols/weee.png",
        alt="WEEE disposal symbol.",
    ),
    "weee2": SymbolAsset(
        path="templates/word_template/common_assets/symbols/weee2.png",
        alt="Battery disposal symbol.",
    ),
}


LANG_COPY: dict[str, dict[str, object]] = {
    "en": {
        "danger_title": "DANGER",
        "danger_bullets": [
            "This device is intended for indoor use only (Please place this device in a similar indoor environment when using it outdoors, e.g., Home, RVs, tents, cabins, etc.).",
            "This device is not waterproof or dustproof. Keep away from rain and humid environments during use.",
        ],
        "maintenance_title": "USER MAINTENANCE INSTRUCTIONS",
        "maintenance_paragraph": (
            "During the lifecycle of energy storage products, a certain degree of capacity and energy degradation is "
            "expected. As the number of charge and discharge cycles increases and storage time extends, this "
            "degradation will gradually intensify, which is a normal phenomenon consistent with the natural aging of "
            "battery cells."
        ),
        "page_title": "MEANING OF SYMBOLS",
        "header_symbol": "Symbol",
        "header_meaning": "Meaning",
        "signal_rows": [
            {
                "mode": "banner",
                "image": "templates/word_template/common_assets/symbols/warning_bar.png",
                "alt": "WARNING banner placeholder.",
                "width": "140px",
                "meaning": "Hazardous practices that may result in severe injury, death, and/or property damage.",
            },
            {
                "mode": "banner",
                "image": "templates/word_template/common_assets/symbols/caution_bar.png",
                "alt": "CAUTION banner placeholder.",
                "width": "140px",
                "meaning": "Hazardous practices that may result in personal injury and/or property damage.",
            },
            {
                "mode": "banner",
                "image": "templates/word_template/common_assets/symbols/note_bar.png",
                "alt": "NOTE banner placeholder.",
                "width": "140px",
                "meaning": "Hazardous practices that may result in equipment damage, data loss, performance deterioration, or unanticipated results.",
            },
            {
                "mode": "banner",
                "image": "templates/word_template/common_assets/symbols/tip_bar.png",
                "alt": "TIP banner placeholder.",
                "width": "140px",
                "meaning": "Supplements the important information or operation tips in the text.",
            },
        ],
    },
    "de": {
        "danger_title": get_symbols_notice_label("de"),
        "danger_bullets": [
            "Dieses Gerät ist nur für die Verwendung in Innenräumen bestimmt (stellen Sie das Gerät bei der Nutzung im Freien in einer vergleichbaren Innenumgebung auf, z. B. in Wohnmobilen, Zelten, Hütten usw.).",
            "Dieses Gerät ist weder wasserdicht noch staubdicht. Halten Sie es während der Verwendung von Regen und feuchten Umgebungen fern.",
        ],
        "maintenance_title": "ANWEISUNGEN ZUR WARTUNG DURCH DEN BENUTZER",
        "maintenance_paragraph": (
            "Während des Lebenszyklus von Energiespeicherprodukten ist mit einem gewissen Verlust an Kapazität "
            "und Energie zu rechnen. Mit zunehmender Anzahl von Lade- und Entladezyklen und längerer "
            "Lagerdauer nimmt diese Degradation allmählich zu. Dies ist ein normales Phänomen, das der "
            "natürlichen Alterung der Batteriezellen entspricht."
        ),
        "page_title": "BEDEUTUNG DER SYMBOLE",
        "header_symbol": "Symbol",
        "header_meaning": "Bedeutung",
        "signal_rows": [
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Warnsymbol.",
                "label": get_signal_word("de", "warning"),
                "meaning": "Gefährliche Handlungen, die zu schweren Verletzungen, zum Tod und/oder zu Sachschäden führen können.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Vorsichtssymbol.",
                "label": get_signal_word("de", "caution"),
                "meaning": "Gefährliche Handlungen, die zu Personenschäden und/oder zu Sachschäden führen können.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Hinweissymbol.",
                "label": get_signal_word("de", "note"),
                "meaning": "Handlungen, die zu Geräteschäden, Datenverlust, Leistungseinbußen oder unerwarteten Ergebnissen führen können.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Tippsymbol.",
                "label": get_signal_word("de", "tips"),
                "meaning": "Ergänzt wichtige Informationen oder Bedienhinweise im Text.",
            },
        ],
    },
    "fr": {
        "danger_title": get_symbols_notice_label("fr"),
        "danger_bullets": [
            "Cet appareil est destiné à un usage intérieur uniquement (veuillez placer cet appareil dans un environnement intérieur similaire lors de son utilisation à l'extérieur, par exemple dans des VR résidentiels, des tentes, des chalets, etc.).",
            "Cet appareil n'est pas étanche ni résistant à la poussière. Éloignez-le de la pluie et des environnements humides pendant son utilisation.",
        ],
        "maintenance_title": "INSTRUCTIONS D'ENTRETIEN PAR L'UTILISATEUR",
        "maintenance_paragraph": (
            "Au cours du cycle des produits de stockage d'énergie, une certaine dégradation de la capacité et de "
            "l'énergie se produira. À mesure que le nombre de cycles d'utilisation augmente et que la durée de "
            "stockage s'allonge, cette dégradation s'intensifiera progressivement, ce qui est un phénomène normal "
            "conforme au modèle de vieillissement naturel des cellules de batterie. "
        ),
        "page_title": "SIGNIFICATION DES SYMBOLES",
        "header_symbol": "Symbole",
        "header_meaning": "Signification",
        "signal_rows": [
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Symbole d'avertissement.",
                "label": get_signal_word("fr", "warning"),
                "meaning": "Pratiques dangereuses pouvant entraîner des blessures graves, la mort et/ou des dommages matériels.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Symbole de mise en garde.",
                "label": get_signal_word("fr", "caution"),
                "meaning": "Pratiques dangereuses pouvant entraîner des blessures corporelles et/ou des dommages matériels.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Symbole de remarque.",
                "label": get_signal_word("fr", "note"),
                "meaning": "Pratiques dangereuses pouvant entraîner des dommages à l'équipement, une perte de données, une détérioration des performances ou des résultats inattendus.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Symbole de conseil.",
                "label": get_signal_word("fr", "tips"),
                "meaning": "Complémente les informations importantes ou les conseils d'utilisation dans le texte.",
            },
        ],
    },
    "es": {
        "danger_title": get_symbols_notice_label("es"),
        "danger_bullets": [
            "Este dispositivo está diseñado únicamente para uso en interiores (coloque este dispositivo en un ambiente similar a interiores cuando lo use en exteriores, ej. autocaravanas, tiendas de campaña, cabañas, etc.).",
            "Este dispositivo no es resistente al agua ni al polvo. Manténgalo alejado de la lluvia y ambientes húmedos durante su uso.",
        ],
        "maintenance_title": "INSTRUCCIONES DE MANTENIMIENTO PARA EL USUARIO",
        "maintenance_paragraph": (
            "Durante el ciclo de vida de los productos de almacenamiento de energía, se producirá cierto grado de degradación "
            "de capacidad y energía. A medida que aumenta el número de ciclos de uso y se extiende el tiempo de "
            "almacenamiento, esta degradación se intensificará gradualmente, lo cual es un fenómeno normal acorde con el "
            "patrón de envejecimiento natural de las celdas de la batería. "
        ),
        "page_title": "SIGNIFICADO DE LOS SÍMBOLOS",
        "header_symbol": "Símbolo",
        "header_meaning": "Significado",
        "signal_rows": [
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Símbolo de advertencia.",
                "label": get_signal_word("es", "warning"),
                "meaning": "Prácticas peligrosas que pueden resultar en lesiones graves, muerte y/o daños a la propiedad.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Símbolo de precaución.",
                "label": get_signal_word("es", "caution"),
                "meaning": "Prácticas peligrosas que pueden resultar en lesiones personales y/o daños a la propiedad.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Símbolo de nota.",
                "label": get_signal_word("es", "note"),
                "meaning": "Prácticas peligrosas que pueden resultar en daños en el equipo, pérdida de datos, deterioro del rendimiento o resultados inesperados.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Símbolo de consejo.",
                "label": get_signal_word("es", "tips"),
                "meaning": "Complementa la información importante o consejos de operación en el texto.",
            },
        ],
    },
    "it": {
        "danger_title": get_symbols_notice_label("it"),
        "danger_bullets": [
            "Questo dispositivo è destinato esclusivamente all'uso in ambienti interni (quando lo si utilizza all'aperto, collocarlo in un ambiente simile a un interno, ad es. casa, camper, tende, cabine, ecc.).",
            "Questo dispositivo non è impermeabile né antipolvere. Tenerlo lontano dalla pioggia e dagli ambienti umidi durante l'uso.",
        ],
        "maintenance_title": "ISTRUZIONI DI MANUTENZIONE PER L'UTENTE",
        "maintenance_paragraph": (
            "Durante il ciclo di vita dei prodotti per l'accumulo di energia, è previsto un certo grado di degrado "
            "della capacità e dell'energia. Con l'aumentare dei cicli di carica e scarica e il prolungarsi del "
            "tempo di immagazzinamento, tale degrado tenderà a intensificarsi gradualmente, in linea con il "
            "naturale invecchiamento delle celle della batteria."
        ),
        "page_title": "SIGNIFICATO DEI SIMBOLI",
        "header_symbol": "Simbolo",
        "header_meaning": "Significato",
        "signal_rows": [
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Simbolo di avvertenza.",
                "label": get_signal_word("it", "warning"),
                "meaning": "Pratiche pericolose che possono causare lesioni gravi, morte e/o danni materiali.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Simbolo di attenzione.",
                "label": get_signal_word("it", "caution"),
                "meaning": "Pratiche pericolose che possono causare lesioni personali e/o danni materiali.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Simbolo di nota.",
                "label": get_signal_word("it", "note"),
                "meaning": "Pratiche che possono causare danni all'apparecchiatura, perdita di dati, deterioramento delle prestazioni o risultati imprevisti.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Simbolo di suggerimento.",
                "label": get_signal_word("it", "tips"),
                "meaning": "Integra le informazioni importanti o i consigli operativi nel testo.",
            },
        ],
    },
    "uk": {
        "danger_title": get_symbols_notice_label("uk"),
        "danger_bullets": [
            "Цей пристрій призначений лише для використання в приміщенні (під час використання на вулиці розміщуйте його в подібному до приміщення середовищі, наприклад у будинку, автофургоні, наметі, кабіні тощо).",
            "Цей пристрій не є водонепроникним і пилонепроникним. Під час використання тримайте його подалі від дощу та вологого середовища.",
        ],
        "maintenance_title": "ІНСТРУКЦІЇ З ОБСЛУГОВУВАННЯ ДЛЯ КОРИСТУВАЧА",
        "maintenance_paragraph": (
            "Протягом життєвого циклу продуктів для накопичення енергії очікується певний ступінь деградації "
            "ємності та енергії. Зі збільшенням кількості циклів заряджання й розряджання та тривалості "
            "зберігання ця деградація поступово посилюватиметься, що є нормальним явищем і відповідає "
            "природному старінню акумуляторних елементів."
        ),
        "page_title": "ЗНАЧЕННЯ СИМВОЛІВ",
        "header_symbol": "Символ",
        "header_meaning": "Значення",
        "signal_rows": [
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Попереджувальний символ.",
                "label": get_signal_word("uk", "warning"),
                "meaning": "Небезпечні дії, які можуть призвести до тяжких травм, смерті та/або пошкодження майна.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "alt": "Символ уваги.",
                "label": get_signal_word("uk", "caution"),
                "meaning": "Небезпечні дії, які можуть призвести до травмування людей та/або пошкодження майна.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Символ примітки.",
                "label": get_signal_word("uk", "note"),
                "meaning": "Дії, які можуть призвести до пошкодження обладнання, втрати даних, погіршення продуктивності або неочікуваних результатів.",
            },
            {
                "mode": "icon_label",
                "image": "templates/word_template/common_assets/symbols/mandatory.png",
                "alt": "Символ поради.",
                "label": get_signal_word("uk", "tips"),
                "meaning": "Доповнює важливу інформацію або поради з експлуатації в тексті.",
            },
        ],
    },
}


def _sort_key(row: dict[str, str]) -> float:
    try:
        return float(row.get("order") or "0")
    except ValueError:
        return 0.0


def _has_unique_explicit_orders(rows: list[dict[str, str]]) -> bool:
    orders = [(row.get("order") or "").strip() for row in rows]
    if any(not order for order in orders):
        return False
    return len({order.casefold() for order in orders}) == len(orders)


def _distribute_ordered_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    ordered = sorted(rows, key=_sort_key)
    split_at = (len(ordered) + 1) // 2
    return {
        "left": ordered[:split_at],
        "right": ordered[split_at:],
    }


def _pick_target_model(vars_map: dict[str, str]) -> str:
    for key in ("model", "product_model", "model_no", "model_number", "Model"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def _pick_target_region(vars_map: dict[str, str]) -> str:
    for key in ("region", "Region"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def _truthy(value: str, *, default: bool = True) -> bool:
    raw = (value or "").strip().casefold()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    return default


def _split_condition_tokens(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw:
        return []
    if raw.startswith(("[", "{")):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, list):
            tokens: list[str] = []
            for item in payload:
                if isinstance(item, dict):
                    item_value = item.get("text") or item.get("name") or item.get("value")
                else:
                    item_value = item
                token = str(item_value or "").strip()
                if token:
                    tokens.append(token)
            return tokens
    return [token for token in re.split(r"[,;|/、，\s]+", raw) if token]


def _matches_market(block: dict[str, str], *, vars_map: dict[str, str]) -> bool:
    value = block.get("Market") or block.get("market") or block.get("Markets") or block.get("markets") or ""
    tokens = _split_condition_tokens(value)
    if not tokens:
        return True
    if any(token.casefold() == "all" for token in tokens):
        return True
    target_region = _pick_target_region(vars_map)
    if not target_region:
        return False
    return any(token.casefold() == target_region.casefold() for token in tokens)


def _matches_row_conditions(block: dict[str, str], *, vars_map: dict[str, str]) -> bool:
    is_latest = block.get("Is_Latest") or block.get("Is_latest") or block.get("is_latest") or ""
    if not _truthy(is_latest, default=True):
        return False
    return _matches_market(block, vars_map=vars_map)


def _matches_symbols_target(
    block: dict[str, str],
    *,
    sku_id: str,
    vars_map: dict[str, str],
) -> bool:
    block_region = (block.get("Region") or block.get("region") or "").strip()
    block_model = canonicalize_model_token(
        (block.get("Model") or block.get("model") or "").strip(),
        region=block_region,
    )

    if block_region or block_model:
        target_region = _pick_target_region(vars_map)
        target_model = canonicalize_model_token(_pick_target_model(vars_map), region=target_region)
        if block_region and (not target_region or block_region.casefold() != target_region.casefold()):
            return False
        if block_model and (not target_model or block_model.casefold() != target_model.casefold()):
            return False
        return True

    return _scope_allows(block.get("sku_scope", "ALL"), sku_id)


def _matches_symbols_fallback_scope(block: dict[str, str], *, vars_map: dict[str, str]) -> bool:
    block_region = (block.get("Region") or block.get("region") or "").strip()
    block_model = canonicalize_model_token(
        (block.get("Model") or block.get("model") or "").strip(),
        region=block_region,
    )
    if not block_region and not block_model:
        return False

    target_region = _pick_target_region(vars_map)
    target_model = canonicalize_model_token(_pick_target_model(vars_map), region=target_region)
    if block_region and target_region and block_region.casefold() == target_region.casefold():
        return False
    if block_model and (not target_model or block_model.casefold() != target_model.casefold()):
        return False
    return True


def _rst_heading(title: str) -> list[str]:
    title = rst_escape(title)
    return [title, "-" * len(title)]


def _append_text_cell(lines: list[str], prefix: str, text: str) -> None:
    raw_lines = [rst_escape(part) for part in (text or "").splitlines()]
    if not raw_lines:
        lines.append(prefix.rstrip())
        return
    lines.append(prefix + raw_lines[0])
    continuation = " " * len(prefix)
    for line in raw_lines[1:]:
        lines.append(continuation + line)


def _append_notice_table(
    lines: list[str],
    *,
    title: str,
    paragraphs: list[str],
    note_prefix: str = "※ ",
) -> None:
    lines.extend(
        [
            ".. list-table::",
            "   :header-rows: 0",
            "   :widths: 18 82",
            "",
            f"   * - **{rst_escape(title)}**",
        ]
    )

    if not paragraphs:
        lines.append("     -")
        return

    first = rst_escape(paragraphs[0])
    lines.append(f"     - {first}")

    for extra in paragraphs[1:]:
        text = rst_escape(extra)
        lines.append("")
        lines.append(f"       {note_prefix}{text}")


def _append_image_cell(
    lines: list[str],
    prefix: str,
    *,
    image_path: str,
    alt: str,
    width: str,
    label: str | None = None,
) -> None:
    lines.append(prefix + f".. image:: {image_path}")
    lines.append(f"          :alt: {rst_escape(alt)}")
    lines.append(f"          :width: {width}")
    if label:
        lines.append("")
        lines.append(f"       **{rst_escape(label)}**")


def _figure_image_path(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("{", "[")):
        return raw
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in ("path", "local_path", "relative_path", "file_path"):
            path_value = str(item.get(key) or "").strip()
            if path_value:
                return path_value
        file_token = str(item.get("file_token") or item.get("token") or "").strip()
        if file_token:
            name = str(item.get("name") or item.get("file_name") or "").strip()
            suffix = Path(name).suffix.lower() or ".png"
            return f"data/phase2/_attachments/symbols/{file_token}{suffix}"
    return ""


def _signal_section(lang: str) -> str:
    copy = LANG_COPY.get(lang)
    if copy is None:
        raise ValueError(f"unsupported symbols language: {lang}")

    danger_title = str(copy["danger_title"])
    maintenance_title = str(copy["maintenance_title"])
    maintenance_paragraph = str(copy["maintenance_paragraph"])
    page_title = str(copy["page_title"])
    header_symbol = str(copy["header_symbol"])
    header_meaning = str(copy["header_meaning"])
    danger_bullets = [str(item) for item in copy["danger_bullets"]]
    signal_rows = list(copy["signal_rows"])

    lines: list[str] = []
    lines.append("|")
    lines.append("")
    _append_notice_table(lines, title=danger_title, paragraphs=danger_bullets)
    lines.append("")
    lines.extend(_rst_heading(maintenance_title))
    lines.append("")
    lines.append(rst_escape(maintenance_paragraph))
    lines.append("")
    lines.extend(
        [
            ".. raw:: latex",
            "",
            f"   \\section{{{rst_escape(page_title)}}}",
            "",
            ".. raw:: html",
            "",
            f"   <h1>{rst_escape(page_title)}</h1>",
            "",
            ".. list-table::",
            "   :header-rows: 1",
            "   :widths: 22 78",
            "",
            f"   * - {header_symbol}",
            f"     - {header_meaning}",
        ]
    )

    for row in signal_rows:
        mode = str(row["mode"]).strip()
        _append_image_cell(
            lines,
            "   * - ",
            image_path=str(row["image"]),
            alt=str(row["alt"]),
            width=str(row.get("width", "40px")),
            label=str(row["label"]) if mode == "icon_label" else None,
        )
        _append_text_cell(lines, "     - ", str(row["meaning"]))

    return "\n".join(lines) + "\n"


def _collect_icon_rows(
    blocks: list[dict[str, str]],
    *,
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> dict[str, list[dict[str, str]]]:
    lang_col = f"text_{lang}"
    if not blocks:
        raise ValueError(f"symbols page has no blocks for sku={sku_id} lang={lang}")
    if lang_col not in blocks[0]:
        raise ValueError(f"content csv missing language column: {lang_col}")

    rows: list[dict[str, str]] = []
    fallback_scopes: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for block in blocks:
        if not _enabled(block.get("enabled", "1")):
            continue
        if not _matches_row_conditions(block, vars_map=vars_map):
            continue

        block_type = (block.get("block_type") or "").strip()
        if block_type != "table_row":
            raise ValueError(
                f"symbols page only supports block_type='table_row', got '{block_type or '?'}'"
            )

        text = apply_vars(block.get(lang_col, "") or "", vars_map)
        if not text.strip():
            raise ValueError(
                f"symbols row missing {lang_col} text at line {(block.get('__line__') or '?').strip()}"
            )

        symbol_key = (block.get("symbol_key") or "").strip()
        if not symbol_key:
            raise ValueError(
                f"symbols row missing symbol_key at line {(block.get('__line__') or '?').strip()}"
            )
        if symbol_key not in SYMBOL_ASSETS:
            raise ValueError(f"unknown symbols symbol_key='{symbol_key}'")
        asset = SYMBOL_ASSETS[symbol_key]
        image_path = _figure_image_path(block.get("Figure") or block.get("figure") or "")
        image_path = image_path or (block.get("image_path") or "").strip() or asset.path

        row = {
            "symbol_key": symbol_key,
            "image_path": image_path,
            "text": rst_escape(text),
            "order": (block.get("order") or "").strip(),
        }
        if _matches_symbols_target(block, sku_id=sku_id, vars_map=vars_map):
            rows.append(row)
            continue
        if _matches_symbols_fallback_scope(block, vars_map=vars_map):
            block_region = (block.get("Region") or block.get("region") or "").strip().casefold()
            block_model = canonicalize_model_token(
                (block.get("Model") or block.get("model") or "").strip(),
                region=(block.get("Region") or block.get("region") or "").strip(),
            ).casefold()
            source_lang = (block.get("Source_lang") or block.get("source_lang") or "").strip().casefold()
            fallback_scopes.setdefault((block_region, block_model, source_lang), []).append(row)

    if not rows:
        ranked_scopes: list[tuple[tuple[int, int, str, str], list[dict[str, str]]]] = []
        for (scope_region, scope_model, _scope_source_lang), scope_rows in fallback_scopes.items():
            ranked_scopes.append(
                (
                    (
                        -len(scope_rows),
                        0 if scope_model else 1,
                        scope_region,
                        scope_model,
                    ),
                    scope_rows,
                )
            )
        ranked_scopes.sort(key=lambda item: item[0])
        if ranked_scopes:
            best_score = ranked_scopes[0][0]
            best_matches = [scope_rows for score, scope_rows in ranked_scopes if score == best_score]
            if len(best_matches) == 1:
                rows = list(best_matches[0])

    if not rows:
        raise ValueError(f"symbols page has no matching rows sku={sku_id} lang={lang}")
    if not _has_unique_explicit_orders(rows):
        raise ValueError(f"symbols page requires unique non-empty order values sku={sku_id} lang={lang}")

    groups = _distribute_ordered_rows(rows)
    return groups


def _icon_table(lang: str, groups: dict[str, list[dict[str, str]]]) -> str:
    copy = LANG_COPY.get(lang)
    if copy is None:
        raise ValueError(f"unsupported symbols language: {lang}")

    header_symbol = str(copy["header_symbol"])
    header_meaning = str(copy["header_meaning"])
    left_rows = groups["left"]
    right_rows = groups["right"]
    max_rows = max(len(left_rows), len(right_rows))

    lines: list[str] = [
        ".. list-table::",
        "   :header-rows: 0",
        "   :widths: 12 38 12 38",
        "",
        f"   * - **{header_symbol}**",
        f"     - **{header_meaning}**",
        f"     - **{header_symbol}**",
        f"     - **{header_meaning}**",
    ]

    for idx in range(max_rows):
        left = left_rows[idx] if idx < len(left_rows) else None
        right = right_rows[idx] if idx < len(right_rows) else None

        if left is not None:
            left_asset = SYMBOL_ASSETS[left["symbol_key"]]
            _append_image_cell(
                lines,
                "   * - ",
                image_path=str(left["image_path"]),
                alt=left_asset.alt,
                width=left_asset.width,
            )
            _append_text_cell(lines, "     - ", left["text"])
        else:
            lines.append("   * -")
            lines.append("     -")

        if right is not None:
            right_asset = SYMBOL_ASSETS[right["symbol_key"]]
            _append_image_cell(
                lines,
                "     - ",
                image_path=str(right["image_path"]),
                alt=right_asset.alt,
                width=right_asset.width,
            )
            _append_text_cell(lines, "     - ", right["text"])
        else:
            lines.append("     -")
            lines.append("     -")

    return "\n".join(lines) + "\n"


def render_symbols_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    groups = _collect_icon_rows(blocks, sku_id=sku_id, lang=lang, vars_map=vars_map)
    rendered = template.replace(PH_SYMBOLS_SIGNAL_SECTION_RST, _signal_section(lang))
    rendered = rendered.replace(PH_SYMBOLS_ICON_TABLE_RST, _icon_table(lang, groups))
    return rendered
