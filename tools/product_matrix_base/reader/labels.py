"""Printed specification label -> attribute key, in every published language.

Labels are matched after normalisation (port counts and footnote marks removed). The section heading above a row is
used only to tell an input port from an output port, and, for specification-like tables outside the specification
section, which table a row belongs to (charge times, warranty, in-box items). A label no rule claims, or one that is
ambiguous, maps to ``UNMAPPED`` with a note; the row is kept and reported, never dropped.
"""
from __future__ import annotations

import re

UNMAPPED = "UNMAPPED"
INPUT_CTX = re.compile(r"input|eingang|entrée|entrada|ingresso|ingang|wejś|вхід|вхідні|入力|输入|輸入|입력", re.I)
OUTPUT_CTX = re.compile(r"output|ausgang|sortie|salida|uscit|uitgang|wyjś|вихід|вихідні|saída|出力|出カ|输出|輸出|출력", re.I)
CHARGE_TIME_CTX = re.compile(r"充電時間|charging time|charge time|ladezeit|temps de charge|tiempo de carga", re.I)
WARRANTY_CTX = re.compile(r"warrant|garant|gwaranc|гаранті|保証|保修", re.I)
RUNTIME_CTX = re.compile(r"給電の目安|使用機器への給電", re.I)
IN_BOX_CTX = re.compile(r"同梱品|包装清单|包裝清單|package list|in the box", re.I)
COMPAT_CTX = re.compile(r"compatib|kompatyb|kompatib|сумісн|互換|兼容", re.I)


def norm(label: str) -> str:
    s = label.lower()
    s = re.sub(r"[①-⑳➀-➉¹²³⁴]", "", s)
    s = s.replace("ポ一卜", "ポート").replace("出カ", "出力").replace("－", "-")
    s = re.sub(r"^\s*\d+\s*[x×]\s*", "", s)
    s = re.sub(r"^\s*\d+\s+(?=\w)", "", s)  # "2 porty DC8020", "1 port DC 12V"
    s = re.sub(r"\s+", " ", s).strip(" :：")
    return s


def context_dir(ctx: str) -> str:
    i, o = bool(INPUT_CTX.search(ctx)), bool(OUTPUT_CTX.search(ctx))
    return "io" if i and o else "input" if i else "output" if o else ""


OUT_W = r"(output|ausgang|ausgänge|sortie|sorties|salida|salidas|uscita|uscite|uitgang|wyjści[ae]|вихід|виходи|saída|saídas|出力|输出|輸出|출력)"
IN_W = r"(input|eingang|entrée|entrada|ingresso|ingang|wejście|вхід|入力|输入|輸入|입력)"

# Ordered rules: (key, pattern on normalised label). First match wins.
RULES: list[tuple[str, str]] = [
    ("UNMAPPED:two attributes in one label (colour and model number)", r"^色/型番$"),
    ("recycling_mark", r"^\[img:li-ion"),
    ("product_name", r"^(product name|produktname|nom du produit|nombre del? producto|nome del prodotto|nome do produto|productnaam|nazwa produktu|назва продукту|製品の名称|製品名称?|产品名称|名称|名稱|제품명|品名)$"),
    ("model_number", r"^(model( no\.?| number| name)?|product model|modell(-nr\.?|nummer)?|modelo|modèle|n[°º]? ?(de |do )?mod[eè]lo?|n° modèle|numéro de modèle|número de modelo|modello( n\.)?|numero di modello|modelnummer|numer modelu|номер моделі|№ моделі|модель|型番|型号|型號|型名|모델명)$"),
    ("color", r"^色$|^colou?r$"),
    ("pv_cell_technology", r"^cell technology$"),
    ("battery_chemistry", r"cell chemistry|zellchemie|cellule chimique|chimie cellulaire|química (celular|de (la |las )?celdas?|da célula)|chimica (celle|delle celle)|celchemie|typ ogniw|хімічний склад|バッテリータイプ|充電池タイプ|电芯类型|電芯類型|전지 화학"),
    ("cycle_life", r"cycle life|zykluslebensdauer|nutzungsdauer|durée de vie|ciclo de vida|vida útil|durata del ciclo|vita ciclica|levenscyclus|levensduur|żywotność|ресурс циклів|サイクル寿命|サイクル数|循环寿命|循環壽命|충전, 방전 주기"),
    ("dimensions_and_weight", r"サイズ ?[&＆] ?重量|^size / weight$"),
    ("battery_voltage_and_ah", r"^电池组电压/容量$"),
    ("ac_output_energy", r"^ac 额定输出能量$"),
    ("capacity_wh", r"^(capacity|internal battery|kapazität|capacité|capacidad|capacità|capaciteit|pojemność|ємність|capacidade|定格容量|容量|充電池容量|용량|电池能量|电池组能量)$"),
    ("net_weight", r"^正味重量$"),
    ("weight_kg", r"^(weight|gewicht|poids|peso|waga|вага|重量|質量|무게)$"),
    ("dimensions_unfolded", r"unfold|aufgeklappt|déplié|desplegado|dispiegato|uitgevouwen|po rozłożeniu|розкладеному|desdobrad|展開|寸法（展開）"),
    ("dimensions_folded", r"fold|zusammengeklappt|plié|plegado|piegato|opgevouwen|po złożeniu|складеному|dobrad|折りたたみ|収納サイズ"),
    ("dimensions_mm", r"^(dimensions?|size|abmessungen|dimensiones|dimensioni|afmetingen|wymiary|розміри|dimensões|外形寸法|最大外形寸法.*|寸法|尺寸|크기)$"),
    ("heating_module_input", r"heating module input"),
    ("heating_module_power", r"heating module power"),
    ("heating_module_operating_temperature", r"operating temperature of heating module"),
    ("heating_module_storage_temperature", r"storage temperature of heating module"),
    ("discharge_temp_range", r"discharg|entladetemperatur|décharge|descarga|scarica|ontlaadtemperatuur|rozładowania|zasilania urządzeń odbiorczych|температура розряд|放電温度|放电温度|放電溫度|방전 온도"),
    ("charge_temperature", r"charg(e|ing) temp|ladetemperatur|température de charg|temperatura de carga|temperatura di (carica|ricarica|caricatra)|oplaadtemperatuur|temperatura ładowania|температура заряджання|temperatura de carregamento|充電温度|充电温度|充電溫度|충전 온도"),
    ("storage_temperature", r"storage temp|lagertemp|stockage|almacenamiento|stoccaggio|opslagtemp|przechowywania|зберігання|armazenamento|保存温度"),
    ("pv_nmot", r"nominal module operating temperature|tnmot"),
    ("pv_module_tmax", r"module \[t98\]max"),
    ("operating_temperature", r"operating temp|working temp|betriebstemp|température de fonctionnement|plage de température de fonctionnement|température opérationnelle|temperatura de (funcionamiento|trabajo|operação)|rango de temperatura de funcionamiento|temperatura di funzionamento|gamma di temperatura operativa|bedrijfstemp|temperatura robocza|zakres temperatury pracy|робоча температура|діапазон робочих температур|faixa de temperatura de operação|動作温度|作動温度"),
    ("operating_altitude", r"altitud|betriebshöhe|werkhoogte|wysokość robocza|робоча висота|使用高度"),
    ("operating_humidity", r"humidity|feuchtigkeit|humidité|humedad|umidità|vochtigheid|wilgotność|вологість|umidade"),
    ("shock_protection_class", r"protection (class )?against electric shock|schutzklasse|classe de protection contre|clase de protección contra choque|classe di protezione contro|beschermingsklasse|klasa ochrony przed|клас захисту від|classe de proteção contra|感電保護クラス"),
    ("ip_rating", r"ip rating|ip-schutzart|^schutzart$|waterproof|ingress protection|protection rating|indice de protection|protection contre les intrusions|clasificación ip|protección contra la entrada|grado de protección|grado di protezione|ip-classificatie|beschermingsgraad|stopień ochrony|ступінь захисту|grau de proteção|índice de proteção|防塵防水|防水規格|防水防塵|防水防塵等級"),
    ("overvoltage_category", r"overvoltage|surtension|sobretensión"),
    ("pollution_degree", r"pollution|contamination|contaminación"),
    ("fire_rating", r"fire rating"),
    ("impact_resistance_class", r"impact resistance"),
    ("enclosure_type", r"enclosure type|type d’enveloppe|type d'annexe|tipo de caja"),
    ("max_short_circuit_current_and_duration", r"short circuit (\| )?current and duration|courant et durée maximum|corriente máxima de (\| )?cortocircuito y duración|corrente massima di cortocircuito e durata"),
    ("max_input_short_circuit_current", r"input short-circuit current|court-circuit d.entrée|cortocircuito de entrada"),
    ("max_input_current", r"maximum input current|courant (maximal d.entrée|d.entrée maximal)|corriente de entrada máxima"),
    ("max_output_current", r"maximum output current|courant maximal de sortie|courant de sortie maximal|corriente de salida máxima"),
    ("inverter_topology", r"inverter topology|topologie de l.onduleur|topología de inversor"),
    ("power_factor", r"power factor|facteur de puissance|factor de potencia"),
    ("feed_in_type", r"feed-in type|tipo de alimentación|type d.alimentation"),
    ("standby_power", r"standby|veille|modo de espera"),
    ("number_of_load_branches", r"number of load branches|nombre de branches|número de ramas"),
    ("main_circuit", r"^(main circuit|circuit principal|circuito principal)$"),
    ("branch_circuit", r"^(branch circuit|circuit de branchement|circuito derivado)$"),
    ("load_circuit", r"^(load circuit|circuit de charge|circuito de carga)$"),
    ("max_load", r"^maximum load$"),
    ("ac_voltage_nominal", r"ac voltage \(nominal\)|tension ca \(nominale\)|voltage ac \(nominal\)|tensión ca \(nominal\)|voltaje ca \(nominal\)|^定格電圧$"),
    ("ac_bypass_input_output", r"(bypass|パススルー).*(入力/出力|input/output)|パススルー充電 ac入力/出力|bypass mode ac input/output|bypass mode ac input/output"),
    ("ac_input_bypass", r"(bypass|derivación|dérivation).*" + IN_W + r"|" + IN_W + r".*(bypass|derivación)|^mode bypass entrée ca$"),
    ("ac_output_bypass", r"(bypass|derivación|dérivation|obejściowym|байпас|パススルー|旁路|바이패스|bypassmodus|bypass-modus)"),
    ("ac_input", r"charge mode ac input|mode de charge entrée ca|entrada de ca en modo de carga"),
    ("ac_output_total", r"ac total|total ac|ac-gesamt|sortie totale ca|total sorties ca|ca salida total|salida (de ca )?total|salida total de ca|uscita totale ca|ac-totaal|totale ac|całkowita moc wyjściowa ac|загальний вихід змінного|saída total|ac出力合計|ac总输出|ac 총 출력"),
    ("ac_parallel_output", r"并机输出"),
    ("parallel_port", r"^并机端口$"),
    ("expansion_port_ac", r"^ac.*(expansion|extension|expansión|拡張)|(expansion|extension|expansión|espansione).*\bca\b"),
    ("expansion_port_dc", r"(expansion|erweiterungsanschluss|extension|expansión|espansione|uitbreidingspoort|rozszerzeń|розширення|expansão|拡張|加电包连接端口)"),
    ("ac_input", r"^(ac input|ac-eingang|entrée ca|entrada (de )?ca|ingresso ca|ac-ingang|wejście ac|вхід змінного струму|ac入力(ポート)?|ac 입력|in1 \(ac输入\))$"),
    ("ac_output_port", r"^(ac output|ac-ausgang|ac-ausgänge|sorties? ca|salidas? (de )?ca|uscit[ae] ca|ac-uitgang|wyjści[ae] ac|(вихід|виходи) (ac|змінного струму)|saídas? ca|ac ?出力(ポート)?|ac输出|ac 출력|out5/out6/out7 \(ac输出端口\)|вихід змінного струму × 3|ac \(nema.*)( ?[(（].*)?$"),
    ("ac_output_port", r"ac ?出力"),
    ("car_input", r"car input|車載入力|^usb-c1/c2 input \(car input\)$"),
    ("solar_input", r"solar input|ソーラー入力"),
    ("solar_input_high_voltage", r"high-pv|pv élevée|alta tensión fv|高電圧入力"),
    ("solar_input_low_voltage", r"low-pv|pv faible|baja tensión fv|低電圧入力"),
    ("dc8020_input", r"dc8020|8020"),
    ("dc_input", r"^(dc input|dc-eingang|entrée (cc|dc)|entrada (de )?cc|ingresso cc|dc-ingang|wejście dc|вхід постійного струму|dc ?入力(ポート)?)$"),
    ("usb_combined_output", r"\+|port output mode"),
    ("usb_output_total", r"usb total|usb総出力"),
    ("usb_c_input", r"usb-c.*" + IN_W + r"|" + IN_W + r".*usb-c|\(pd input\)|pd 入力"),
    ("dc12_car_output", r"dc ?12 ?v|12 v-anschluss|cc 12 ?v|car port|cigarette|allume-cigare|encendedor|presa da 12 ?v|シガーソケット|ｼｶﾞｰｿｹｯﾄ|车充|12 в|dc 12v 連接埠|dc 12v 포트|^out1 \(车充输出端口\)$"),
    ("usb_c_output", r"usb-c.*" + OUT_W + r"|" + OUT_W + r".*usb-c|usb-c ?\d+ ?w|usb-c\d? (\d+ ?w|maks|max|da )|usb-c \d+ вт|usb-c, вихід|usb-c.?(\(out\)|\(in/out\) output)|usb-c(1|2) output|^out[23] \(usb-c|usb-c ?\d+ ?w max|usb-c maks"),
    ("usb_a_output", r"usb-a"),
    ("ups", r"^(ups|ups \((asi|sai)\)|sai)$"),
    ("communication", r"communication|comunicación"),
    ("dc_output", r"^(dc output|dc ?出力|sortie cc|salidas de cc)$"),
    ("total_output", r"^(total output|総出力)$"),
    ("output_w", r"^(output power|ausgangsleistung|puissance de sortie|potencia de salida|potenza di uscita|uitgangsvermogen|moc wyjściowa|вихідна потужність|potência de saída|最大出力)$"),
    ("output_voltage", r"^(output voltage|ausgangsspannung|tension de sortie|voltaje de salida|tensão de saída|uitgangsspanning|napięcie wyjściowe|вихідна напруга)$"),
    ("output_current", r"^(output current|ausgangsstrom|courant de sortie|corriente de salida|corrente di uscita|corrente de saída|uitgangsstroom|prąd wyjściowy|вихідний струм)$"),
    ("rated_voltage", r"^電圧$"),
    ("rated_current", r"^(定格電流|電流)$"),
    ("input_rating", r"^(input|入力|入力ポート)$"),
    ("output_rating", r"^(output|sortie|salida|出力ポート)$"),
    ("usb_pps", r"^pps$"),
    ("panel_power_w", r"peak power|maximum power \(p|rated maximum power|最大出力 \(pmax\)|maximale leistung|puissance maximale|potencia máxima|potenza massima|maximaal vermogen|maksymalna moc|максимальна потужність|potência máxima"),
    ("pv_vmp", r"vmp|vₘₚ|動作電圧"),
    ("pv_imp", r"imp\)|iₘₚ|動作電流"),
    ("pv_voc", r"voc|vₒ꜀|open.circuit|開放電圧|leerlaufspannung|circuito abierto|circuit ouvert|circuito aperto|openklemspanning|obwodu otwartego|розімкнутого|circuito aberto"),
    ("pv_isc", r"isc\)|iₛ꜀|^short.circuit current$|短絡電流|kurzschlussstrom|court-circuit \(isc\)|cortocircuito \(isc\)|corto circuito \(isc\)|kortsluitstroom|prąd zwarciowy|короткого замикання|curto-circuito"),
    ("pv_max_system_voltage", r"system voltage|systemspannung|tension maximale du système|tensión máxima del sistema|tensione massima del sistema|systeemspanning|napięcie w układzie|напруга системи|tensão máxima do sistema|最大システム電圧"),
    ("pv_max_reverse_current", r"reverse current|corrente reversa|rückstrom|courant maximal inverse|corriente máxima inversa|corrente inversa|massima corrente inversa|terugstroom|prąd wsteczny|зворотний струм|最大逆電流"),
    ("pv_max_series_fuse", r"series fuse"),
    ("pv_temp_coeff_pmax", r"power temperature coefficient|leistungs-temperaturkoeffizient|coefficient de température de puissance|coeficiente de temperatura de potencia|coefficiente di temperatura della potenza|temperatuurcoëfficiënt van het vermogen|temperaturowy współczynnik mocy|температурний коефіцієнт потужності|coeficiente de temperatura de potência|出力温度係数"),
    ("pv_temp_coeff_voc", r"voltage temperature coefficient|temperaturkoeffizient der spannung|coefficient de température de tension|coeficiente de temperatura de voltaje|coefficiente di temperatura della tensione|temperatuurcoëfficiënt van spanning|temperaturowy współczynnik napięcia|температурний коефіцієнт напруги|coeficiente de temperatura de tensão|電圧温度係数"),
    ("pv_bifaciality", r"bifacial|bifazial|bifaccial|bifacjal|両面係数|біфаціальн"),
    ("pv_connector_type", r"^connector type$"),
    ("pv_connector_manufacturer", r"^connector manufacturer$"),
    ("pv_min_design_load", r"min\.design load"),
    ("pv_application_class", r"^application class$"),
    ("pv_test_condition", r"all technical data at standard"),
    ("consumer_product_category", r"photovolta|fotovolta|fotowolta|фотоелектричні|consumer goods category|消費財カテゴリー"),
    ("max_parallel_connections", r"parallel connections|最大並列接続数"),
    ("max_series_connections", r"series connections|最大直列接続数"),
    ("iec_code", r"iec|code cei"),
    ("material", r"^(material|材質)$"),
    ("fabric", r"^fabric$"),
    ("in_box_contents", r"^付属品$"),
    ("certifications", r"^認証$"),
    ("warranty_period", r"^保証期間$"),
    ("special_feature", r"^special feature$"),
]
_COMPILED = [(k, re.compile(p, re.I)) for k, p in RULES]

GENERIC_PORT = {
    "ac": ("ac_input", "ac_output_port"), "ca": ("ac_input", "ac_output_port"), "acポート": ("ac_input", "ac_output_port"),
    "ac 連接埠": ("ac_input", "ac_output_port"), "usb-c": ("usb_c_input", "usb_c_output"),
    "usb-cポート": ("usb_c_input", "usb_c_output"), "usb-c1": ("usb_c_input", "usb_c_output"),
    "usb-c2": ("usb_c_input", "usb_c_output"), "usb-c3": ("usb_c_input", "usb_c_output"),
    "usb-c1 / usb-c2": ("usb_c_input", "usb_c_output"), "usb-c port": ("usb_c_input", "usb_c_output"), "usb-c1/usb-c2": ("usb_c_input", "usb_c_output"),
    "dc8020 連接埠": ("dc8020_input", "UNMAPPED"), "usb-a 連接埠": ("UNMAPPED", "usb_a_output"),
}


def _spec_like(label: str, context: str) -> tuple[str, str] | None:
    """The key of a row in a specification-like table outside the section, from the table's heading."""
    if RUNTIME_CTX.search(context):
        return "runtime_estimate", "usage estimate per appliance; label names the appliance"
    if CHARGE_TIME_CTX.search(context):
        return _charge_time(label)
    if WARRANTY_CTX.search(context):
        if re.search(r"保証期間|year|jahr|\bans\b|años|anni|jaar|lat|рок|anos|warranty", label):
            return "warranty_period", "warranty table"
        return UNMAPPED, "warranty card field, not a product attribute"
    if IN_BOX_CTX.search(context):
        return "in_box_contents", "in-box table: label and value are both items"
    if re.fullmatch(r"l1|l2|n|gnd", label):
        return UNMAPPED, "wiring terminal table"
    if re.fullmatch(r"f[0-9a-f]|error code", label):
        return UNMAPPED, "error-code table"
    if COMPAT_CTX.search(context):
        return UNMAPPED, "compatibility / status table"
    return None


def _charge_time(label: str) -> tuple[str, str]:
    if re.search(r"＋|\+", label):
        return UNMAPPED, "combined charging sources in one row"
    for key, pattern in (("ac_charge_time", r"コンセント|wall|ac"), ("car_charge_time", r"シガー|car"),
                         ("solar_charge_time", r"ソーラー|solar")):
        if re.search(pattern, label):
            return key, "charge-time table" + ("; panel size in label" if key == "solar_charge_time" else "")
    return UNMAPPED, "charge-time row with unknown source"


SPECIAL = {"usb出力": "generic 'USB output': per-port or total not stated",
           "onduleur": "'Onduleur' means inverter or UPS",
           "充電時間": "charge time without the charging source",
           "entire unit": "'Entire unit' row (value 'Type 1'): the printed table does not say what is typed",
           "unité complète": "'Entire unit' row (value 'Type 1'): the printed table does not say what is typed",
           "unidad entera": "'Entire unit' row (value 'Type 1'): the printed table does not say what is typed"}


def _generic_port(label: str, original: str, context: str) -> tuple[str, str]:
    direction = context_dir(context)
    into, out = GENERIC_PORT[label]
    if direction == "input" and into != UNMAPPED:
        return into, "bare port label; section heading says input"
    if direction == "output" and out != UNMAPPED:
        return out, "bare port label; section heading says output"
    return UNMAPPED, f"bare port label '{original}' without an input/output heading: could be {into} or {out}"


def _rule(label: str, context: str) -> tuple[str, str]:
    for key, pattern in _COMPILED:
        if not pattern.search(label):
            continue
        if key.startswith("UNMAPPED:"):
            return UNMAPPED, key.split(":", 1)[1]
        if key == "dc8020_input" and context_dir(context) == "output":
            return UNMAPPED, "DC8020 under an output heading"
        if key == "dc12_car_output" and context_dir(context) == "input" and not OUTPUT_CTX.search(label):
            return "car_input", "12V/car label under an input heading"
        return key, ""
    return UNMAPPED, "no rule"


def map_label(label: str, context: str, table_kind: str, heading_path: str = "") -> tuple[str, str]:
    """(attribute key or UNMAPPED, note). ``context``: the nearest headings; ``heading_path``: the whole path."""
    normalised = norm(label)
    if not normalised:
        return UNMAPPED, "empty label"
    if table_kind == "spec_like_elsewhere":
        found = _spec_like(normalised, heading_path or context)
        if found:
            return found
    if normalised == "ac input / charge mode":
        return "ac_input", ""
    port = re.sub(r"\s*[(（].*$", "", normalised)
    if port in GENERIC_PORT and normalised not in GENERIC_PORT:
        normalised = port
    if normalised in GENERIC_PORT:
        return _generic_port(normalised, label, context)
    if normalised in SPECIAL:
        return UNMAPPED, SPECIAL[normalised]
    return _rule(normalised, context)


__all__ = ["UNMAPPED", "map_label", "norm"]
