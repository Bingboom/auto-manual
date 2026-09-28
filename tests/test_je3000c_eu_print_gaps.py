"""JE-3000C/EU: four older Web gaps follow the print (operator ruling of 2026-09-27).

Operator ruling 「JE-3000C 旧差异按印刷对齐」: where the JE-3000C/EU Web differs from
both the V2.0-2026-07-31 print (the authority, sha256 55fee5a2...) and its
V2.0-2026-09-15 revision (f3264481...), the Web follows the print. Both prints
agree on every item here:

1. fr-uk Energy Saving Mode: the print's opening paragraph (on by default, the
   icon, the 25 W / 2 W threshold over 12 hours, the App setting) and its disable
   sentence replace the Web's reworded disable sentence and its low-power advice,
   which no print carries (PDF pages 28-29/44-45/60-61/76-77/92-93).
2. fr-uk output-resume function: the print's sentence replaces the unprinted
   "off by default, enable it in the App" claim; the section follows the LCD
   screen, as printed and as the English route already does; its table cells
   follow the print (PDF pages 29/45/61/77/93).
3. UPS: the figure follows all of the UPS text, on every language block (PDF
   pages 14/30/46/62/78/94).
4. UPS text in this print's wording: fr, de, it, uk.

House format and print defects: values come from the frozen source in the house
format (unit spacing; the uk threshold "25 Вт" for the printed "25 В"); the
German threshold prints "o" and a 25 W USB limit, which read "oder" and the
source's 2 W; the Italian block's stray German fragment is not copied; the
product name is |PRODUCT_NAME| (de/it print "Explorer 3000"); apostrophes are as
printed.

The UPS page is shared by every EU, US, AU and BP model that prints en/fr/es/de/
it/uk, so the JE-3000C copy sits under ``.. only:: model_je_3000c`` and every
other model reads main's text under ``.. only:: not model_je_3000c``: the
IsolationTests pin that view to main's bytes and its IDML extraction to main's.
Since 2026-09-27 JE-1000H/EU and JE-3600A/EU read their own print's branch as well
(tests/test_je1000h_je3600a_eu_ups_print.py), and the family gate leaves them out.
The model-scoped ``targets/je3000c`` operation templates carry gaps 1 and 2 as
plain text; the English one is unchanged.

On the tree before this change, every gap test here fails and the isolation
tests pass.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from tools.idml_rst_extract import extract_page
from tools.utils.spec_master import resolve_template_substitutions_from_spec_master
from tools.word_bundle_html import _normalize_sphinx_only_blocks_for_docutils
from tools.word_bundle_html_only import _build_word_only_tags, _evaluate_only_expression

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"
DATA_ROOT = ROOT / "manual_sources/JE-3000C/EU/en/2.0/phase2"
LANGS = ("en", "fr", "es", "de", "it", "uk")
BLOCKS = ("fr", "es", "de", "it", "uk")  # gaps 1 and 2
REWORDED = ("fr", "de", "it", "uk")  # gap 4

OPERATION = {
    lang: TEMPLATES / "targets/je3000c" / f"05_operation_guide_{'placeholder' if lang == 'en' else lang}.rst"
    for lang in LANGS
}
UPS = {lang: TEMPLATES / "page_shared" / lang / "06_ups_mode.rst" for lang in LANGS}
UPS_IMAGE = ".. image:: asset:operation/ups_mode"
ENERGY_IMAGE = ".. image:: asset:operation/energy_saving"

# Section headings as the operation templates set them (energy, LCD, resume, keys).
HEADINGS = {
    "en": ("ENERGY SAVING MODE", "LCD SCREEN", "AC and DC Output Resume Function", "KEY COMBINATION"),
    "fr": ("MODE D'ÉCONOMIE D'ÉNERGIE", "AFFICHAGE LCD", "Fonction de reprise de Sortie CA et CC",
           "FONCTIONNEMENT DES BOUTONS"),
    "es": ("MODO DE AHORRO DE ENERGÍA", "PANTALLA LCD", "Función de reanudación de Salida de CA y CC",
           "COMBINACIONES DE TECLAS"),
    "de": ("ENERGIESPARMODUS", "LCD-ANZEIGE", "Wiederaufnahmefunktion für AC- und DC-Ausgänge", "TASTENKOMBINATION"),
    "it": ("MODALITÀ RISPARMIO ENERGETICO", "SCHERMO LCD", "Funzione di ripristino delle uscite CA e CC",
           "COMBINAZIONI DI TASTI"),
    "uk": ("РЕЖИМ ЕНЕРГОЗБЕРЕЖЕННЯ", "ЕКРАН LCD", "Функція відновлення виходів AC і DC", "КОМБІНАЦІЯ КНОПОК"),
}

# Gap 1: the print's two paragraphs, rendered with the frozen source's values.
ENERGY = {
    "fr": (
        "Pour éviter une consommation inutile de la batterie due à l’oubli de désactiver la sortie, le produit active par défaut le Mode d’Économie d’Énergie. Lorsque la sortie CA ou CC/USB est activée, l'icône du mode Économie d'énergie s'affichera sur l'écran LCD. Si aucun appareil n’est connecté ou si la consommation de l’appareil connecté est inférieure à un certain seuil (Sortie CA de 25 W ou sortie CC/USB de 2 W) pendant 12 heures, l’appareil désactivera automatiquement toutes les sorties. Veuillez configurer la durée du mode Économie d'énergie dans l'application Jackery.",
        "Pour désactiver le mode d'économie d'énergie, appuyez et maintenez enfoncé à la fois le bouton d'alimentation CA et le bouton d'alimentation principal pendant plus de 3 secondes. Le produit n'éteindra pas automatiquement la sortie CA ou CC/USB.",
    ),
    "es": (
        "Para evitar el consumo innecesario de batería al olvidar apagar la salida, el producto activa por defecto el Modo de Ahorro de Energía. Cuando la salida de CA o CC/USB está encendida, el ícono del modo de Ahorro de Energía se mostrará en la pantalla LCD. Si no hay ningún dispositivo conectado o si el consumo del dispositivo conectado está por debajo de un cierto umbral (salida de CA de 25 W o salida CC/USB de 2 W) durante 12 horas, el dispositivo apagará automáticamente todas las salidas. Configure la duración del modo de Ahorro de Energía en la aplicación Jackery.",
        "Para desactivar el modo de ahorro de energía, presione y mantenga presionados el botón de energía CA y el botón de encendido principal durante más de 3 segundos. El producto no apagará automáticamente la salida CA o CC.",
    ),
    "de": (
        "Um unnötigen Batterieverbrauch durch das Vergessen des Ausschaltens des Ausgangs zu verhindern, ist der Energiesparmodus standardmäßig aktiviert. Wenn kein Gerät angeschlossen ist oder der Stromverbrauch des angeschlossenen Geräts unter einem bestimmten Schwellenwert liegt (AC-Ausgang ≤ 25 W oder USB-Ausgang ≤ 2 W), werden alle Ausgänge nach 12 Stunden automatisch abgeschaltet.",
        "Um den Energiesparmodus zu deaktivieren, halten Sie die AC-Stromtaste und die POWER-Taste gleichzeitig länger als 3 Sekunden gedrückt. Das Gerät schaltet den AC- oder DC-Ausgang nicht automatisch ab.",
    ),
    "it": (
        "Per prevenire un consumo inutile della batteria dimenticando di spegnere l'uscita, il prodotto attiva la Modalità di risparmio energetico per impostazione predefinita. Quando il pulsante di alimentazione CA è acceso, l’icona della MODALITÀ DI RISPARMIO ENERGETICO verrà visualizzata sullo schermo LCD. Se non è collegato alcun dispositivo o il consumo del dispositivo collegato è inferiore a una determinata soglia (uscita AC ≤ 25 W oppure uscita USB-C ≤ 2 W), il dispositivo spegne automaticamente tutte le uscite dopo 12 ore.",
        "Per disattivare la Modalità risparmio energetico, tenere premuti entrambi i pulsanti di accensione AC e POWER per più di 3 secondi. Il prodotto non disattiva automaticamente l’uscita CA o l’uscita CC/USB.",
    ),
    "uk": (
        "Щоб запобігти зайвому споживанню заряду через забуте вимкнення виходу, за замовчуванням увімкнено режим енергозбереження. Коли увімкнено вихід AC або DC/USB, на ЖК-екрані відображається значок режиму енергозбереження. Якщо жоден пристрій не підключено або споживання підключеного пристрою нижче певного порогу (25 Вт для змінного струму або 2 Вт для DC/USB) протягом 12 годин, пристрій автоматично вимикає виходи. Будь ласка, встановіть тривалість режиму енергозбереження в Jackery App.",
        "Щоб вимкнути режим енергозбереження, натисніть і утримуйте кнопки живлення AC та POWER більше ніж 3 секунди. Пристрій не вимикатиме автоматично вихід змінного струму або постійного струму/USB.",
    ),
}
# The Web's two sentences that neither print carries.
ENERGY_UNPRINTED = {
    "fr": ("l'icône ne s'affichera plus", "Lors de l'alimentation d'appareils à faible puissance"),
    "es": ("el icono dejará de mostrarse", "Cuando alimente dispositivos de baja potencia"),
    "de": ("wird das Symbol nicht mehr auf dem LCD angezeigt", "Wenn Sie Geräte mit geringem Stromverbrauch betreiben"),
    "it": ("l'icona non comparirà più", "Quando si alimentano dispositivi a basso consumo"),
    "uk": ("значок більше не з'являтиметься", "Під час живлення малопотужних пристроїв"),
}

# Gap 2: the print's sentence, the claim it replaces, and the printed table.
RESUME_INTRO = {
    "fr": "Cette fonction mémorise l’état de la sortie et reprend automatiquement les sorties CA et CC sous certaines conditions définies.",
    "es": "Esta función memoriza el estado de la salida y reanuda automáticamente las salidas de CA y CC bajo condiciones definidas.",
    "de": "Diese Funktion speichert den Ausgangszustand und stellt die AC- und DC-Ausgänge unter bestimmten Bedingungen automatisch wieder her.",
    "it": "Questa funzione memorizza lo stato delle uscite e ripristina automaticamente le uscite CA e CC in determinate condizioni.",
    "uk": "Ця функція запам’ятовує стан виходу та автоматично відновлює виходи AC і DC за визначених умов.",
}
RESUME_CLAIM = {
    "fr": "désactivée par défaut",
    "es": "desactivada de forma predeterminada",
    "de": "standardmäßig deaktiviert",
    "it": "disattivata per impostazione predefinita",
    "uk": "за замовчуванням вимкнено",
}
# (header row, then the body cells top-down: left column, right column)
RESUME_TABLE = {
    "fr": (("Conditions de reprise automatique", "Conditions sans reprise automatique"),
           ("Mise sous tension/redémarrage après arrêt ou redémarrage",
            "SOC de la batterie ≥ limite de décharge +10 % après avoir atteint la limite",
            "Mise à niveau OTA terminée"),
           ("Sortie désactivée manuellement (bouton/App)", "Sortie désactivée en mode économie d’énergie",
            "Sortie désactivée suite à un déclenchement de protection", "Sortie désactivée par le minuteur de décharge")),
    "es": (("Condiciones de reanudación automática", "Condiciones sin reanudación automática"),
           ("Encendido/Reiniciar después de apagado o reinicio",
            "SOC de la batería ≥ límite de descarga +10 % después de alcanzar el límite",
            "Actualización OTA completada"),
           ("Apagado manual de la salida (botón/App)", "Apagado de salida en modo de ahorro de energía",
            "Apagado de salida activado por protección", "Apagado de salida activado por temporizador de descarga")),
    "de": (("Bedingungen für automatische Wiederherstellung", "Bedingungen ohne automatische Wiederherstellung"),
           ("Einschalten/Neustart nach Abschalten oder Neustart",
            "Batterie-SOC ≥ Entladegrenze +10% nach Erreichen der Grenze", "OTA-Update abgeschlossen"),
           ("Manuelles Ausschalten der Ausgänge (Taste/App)", "Ausgang im Energiesparmodus deaktiviert",
            "Schutzbedingter Ausgang deaktiviert", "Durch Entlade-Timer gesteuerter Ausgang deaktiviert")),
    "it": (("Condizioni di ripristino automatico", "Condizioni senza ripristino automatico"),
           ("Accensione/Riavvio dopo lo spegnimento o il riavvio",
            "SOC della batteria ≥ limite di scarica +10% dopo aver raggiunto il limite",
            "Aggiornamento OTA completato"),
           ("Spegnimento manuale delle uscite (pulsante/App)", "Spegnimento delle uscite in modalità risparmio energetico",
            "Spegnimento delle uscite attivato da protezione", "Spegnimento delle uscite attivato dal timer di scarica")),
    "uk": (("Умови автоматичного відновлення", "Умови без автоматичного відновлення"),
           ("Увімкнення/перезапуск після вимкнення або перезапуску",
            "Рівень заряду батареї ≥ межа розряду +10% після досягнення межі", "Завершено OTA-оновлення"),
           ("Ручне вимкнення виходу (кнопка/додаток)", "Вимкнення виходу в режимі енергозбереження",
            "Вимкнення виходу через спрацювання захисту", "Вимкнення виходу за таймером розряду")),
}

# Gap 4: the UPS text as each block prints it (one line per printed line), rendered.
UPS_PRINT = {
    "fr": (
        "Connectez le produit à une prise murale à l’aide du câble de charge CA, puis appuyez sur le bouton d'alimentation CA pour alimenter vos appareils en même temps.",
        "Une alimentation sans interruption (ASI) est un système d’alimentation continue qui fournit automatiquement une alimentation électrique de secours à une charge lorsque l’alimentation du réseau principal est interrompue.",
        "En cas de perte soudaine de l’alimentation du réseau, le Jackery Explorer 3000 basculera automatiquement sur l’alimentation stockée en moins de 10 ms pour maintenir vos appareils en fonctionnement.",
        "En mode ASI, la puissance de crête de sortie de l’appareil atteint 12 A avant les coupures de courant. Comme la charge et la décharge simultanées sont activées en mode dérivation, la puissance de sortie réelle est inférieure à la puissance nominale en mode dérivation, mais revient à la puissance nominale lors des coupures.",
    ),
    "de": (
        "Schließen Sie das Produkt mit dem AC-Ladekabel an eine Steckdose an, drücken Sie dann die AC-Ausgangstaste, und versorgen Sie gleichzeitig Ihre Geräte mit Strom.",
        "Eine unterbrechungsfreie Stromversorgung (UPS) ist ein kontinuierliches Stromversorgungssystem, das bei einem Ausfall der Netzstromversorgung automatisch Backup-Strom für angeschlossene Geräte bereitstellt.",
        "Im Falle eines plötzlichen Stromausfalls schaltet der Jackery Explorer 3000 automatisch innerhalb von 10 ms auf die gespeicherte Energie um, damit Ihre Geräte weiterhin betrieben werden können.",
        "Voraussetzung: Das Produkt ist eingeschaltet.",
        "Im USV-Modus erreicht das Gerät vor Stromausfällen eine Spitzenausgangsstromstärke von 12 A. Da im Bypass-Modus gleichzeitiges Laden und Entladen möglich ist, liegt die tatsächliche Ausgangsleistung in diesem Modus unter der Nennleistung; bei Stromausfällen wird jedoch wieder die Nennleistung erreicht.",
    ),
    "it": (
        "Collega il prodotto a una presa a muro utilizzando il cavo di ricarica AC, quindi premi il pulsante di uscita AC per alimentare contemporaneamente i tuoi dispositivi.",
        "Condizione: assicurarsi che il prodotto sia acceso.",
        "Un gruppo di continuità (UPS) è un tipo di sistema di alimentazione continua che fornisce automaticamente energia elettrica di backup a un carico quando l'alimentazione dalla rete elettrica viene a mancare.",
        "In caso di improvvisa interruzione della corrente di rete, Jackery Explorer 3000 passerà automaticamente all’energia immagazzinata entro 10 ms per mantenere in funzione i dispositivi collegati.",
        "In modalità UPS, la potenza di picco dell'unità raggiunge i 12 A prima dell'interruzione di corrente. Poiché la modalità Bypass consente la ricarica/scarica simultanea, la potenza di uscita effettiva è inferiore alla potenza di uscita nominale in questa modalità, ma torna alla potenza di uscita nominale durante le interruzioni di corrente.",
    ),
    "uk": (
        "Підключіть продукт до розетки за допомогою кабелю заряджання змінного струму, потім натисніть кнопку виходу AC і одночасно живіть ваші прилади.",
        "Джерело безперебійного живлення (ДБЖ) — це тип системи безперервного живлення, що забезпечує автоматичне резервне електроживлення навантаження у разі відмови електромережі.",
        "У разі раптового відключення електроенергії Jackery Explorer 3000 автоматично перемкнеться на накопичену енергію протягом 10 мс, щоб ваші прилади продовжували працювати.",
        "У режимі ДБЖ піковий вихідний струм пристрою досягає 12 A до відключення електроенергії. Оскільки в режимі байпаса (Bypass Mode) увімкнено одночасне заряджання/розряджання, фактична вихідна потужність у цьому режимі нижча за номінальну, але під час відключень вона повертається до номінальної вихідної потужності.",
    ),
}
# The family wording this print does not use (it stays on every other model).
UPS_FAMILY_ONLY = {
    "fr": ("mode bypass", "sans coupure (UPS)"),
    "de": ("Spitzenleistung von", "damit Ihre Geräte weiterlaufen"),
    "it": ("dei interruzioni", "energia di riserva"),
    "uk": ("(UPS) - це", "зникнення мережевого живлення"),
}
# Print defects the Web does not copy: the Italian UPS block's stray German
# fragment, the German threshold's "o" and 25 W USB limit, the uk "25 В" (volts).
UPS_PRINT_DEFECTS = {"it": ("Modus unter der Nennleistung",)}
ENERGY_PRINT_DEFECTS = {"de": (" o USB-Ausgang", "USB-Ausgang ≤ 25 W"), "uk": ("(25 В ",)}

# Isolation pins, from origin/main 138c9654 (#1309): sha256 of each shared UPS
# template with trailing whitespace stripped per line, and of its IDML
# extraction for another model (JE-1000H/EU until 2026-09-27, when it and
# JE-3600A/EU took their own print's branch; JE-2000E/EU since, same pins).
MAIN_UPS_SHA256 = {
    "en": "049b6162f0a6fde75abc821c4d55947b485c55cb2f86f0927ed5f1855e64ae70",
    "fr": "cce52d4dd4e69c9f65613ff14c0f6f2c428fcc50cb7f0127fc890b2175f195bd",
    "es": "a4e893f6b4b04d031ddf3703ef045cfaa1599ad18f898228d63f344276d0d8e9",
    "de": "59246cbd27564a91a5fa0209fd57a0cdba82e008782184036b87912ea6b53ec2",
    "it": "d14b1ecbeb534e28a8f495a589db1621da6b59c6faae63894c495d5d385ea0f9",
    "uk": "5076dbf4d494fe12300645484210148f2afe711e446cea6349b4e37452c0199a",
}
MAIN_UPS_IDML_OTHER_MODEL_SHA256 = {
    "en": "7712986924d2f69a151ead889a42fb59f3b1df5a08a9357d0239577179417436",
    "fr": "13036c2e7451a2aacdd2518b6efe806dbccd93e9db00e232d7610e8fcf4738a2",
    "es": "4be79cbe346545aac153db7acc61118e7e30a80c255275da1f59b83170ef0b2f",
    "de": "b25ad2752367362d5466a51263e4c9e11b65f4ef6c508723c20abf81e6151337",
    "it": "a00fde95a395d9d9eb9fb9750967f5346d07d189e46701c10f4c3e0278127a3a",
    "uk": "ca261161529b8b4e3dbd79e828cdcd82184f13dc124585fcf8f3bc109e6179e9",
}
MAIN_ENGLISH_OPERATION_SHA256 = "9d1b3f993632ab6bf8300257831ac34bff783838bfb04ebb5e154a70f10c6073"

_SUBSTITUTIONS: dict[str, dict[str, str]] = {}


def substitutions(lang: str) -> dict[str, str]:
    if lang not in _SUBSTITUTIONS:
        _SUBSTITUTIONS[lang] = resolve_template_substitutions_from_spec_master(
            DATA_ROOT / "Spec_Master.csv", model="JE-3000C", region="EU", lang=lang)
    return _SUBSTITUTIONS[lang]


def render(text: str, lang: str) -> str:
    values = substitutions(lang)
    return re.sub(r"\|([A-Z][A-Z0-9_]+)\|", lambda m: values.get(m.group(1), m.group(0)), text)


def je3000c_view(path: Path, lang: str) -> str:
    """The carrier as the JE-3000C Web and Word pipelines read it, values filled in."""
    tags = _build_word_only_tags(model="JE-3000C", region="EU", lang=lang)
    return render(_normalize_sphinx_only_blocks_for_docutils(path.read_text(encoding="utf-8"), active_tags=tags), lang)


# A model without its own UPS branch. Since 2026-09-27 JE-1000H and JE-3600A have one
# too (tests/test_je1000h_je3600a_eu_ups_print.py), so JE-2000E stands in for them.
OTHER_MODEL = "JE-2000E"
OTHER_MODEL_TAGS = {"model_je_2000e"}


def _is_model_gate(line: str) -> bool:
    names = re.findall(r"[A-Za-z_]\w*", line[len(".. only:: "):]) if line.startswith(".. only:: ") else []
    return bool(names) and all(name in ("not", "or", "and") or name.startswith("model_") for name in names)


def other_model_view(text: str) -> str:
    """Model gates resolved for a model without its own branch (nested ones too); unwrap or drop."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if _is_model_gate(lines[i]):
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].startswith("   ")):
                j += 1
            if _evaluate_only_expression(lines[i][len(".. only:: "):], OTHER_MODEL_TAGS):
                body = "\n".join(line[3:] if line.startswith("   ") else line for line in lines[i + 2:j])
                out.extend(other_model_view(body).split("\n"))
            i = j
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def idml_blocks(path: Path, model: str, lang: str) -> list:
    tags = {"latex", "idml", "region_eu", "model_" + model.lower().replace("-", "_"), f"lang_{lang}"}
    return extract_page(path, tags).blocks


def section(text: str, heading: str) -> list[str]:
    """Lines of the level-two section titled ``heading`` (up to the next title)."""
    lines = text.split("\n")
    start = lines.index(heading)
    assert set(lines[start + 1]) == {"-"}, lines[start + 1]
    end = len(lines)
    for k in range(start + 2, len(lines) - 1):
        if lines[k] and not lines[k].startswith(" ") and lines[k + 1] and set(lines[k + 1]) <= set("-=") \
                and len(lines[k + 1]) >= 3:
            end = k
            break
    return lines[start + 2:end]


def paragraphs_before(lines: list[str], marker: str) -> list[str]:
    body = "\n".join(lines[:lines.index(marker)])
    return [" ".join(p.split("\n")).strip() for p in body.split("\n\n") if p.strip()]


def grid_cells(lines: list[str]) -> tuple:
    """(header cells, left-column cells, right-column cells) of the resume grid table."""
    grid = [line for line in lines if line.startswith(("+", "|"))]
    split = grid[0].index("+", 1)
    rows: list[list[str]] = []
    current: list[list[str]] = [[], []]
    for line in grid:
        if line.startswith("+") and set(line) <= set("+-="):
            if any(current):
                rows.append([" ".join(c).strip() for c in current])
            current = [[], []]
            continue
        if line[split] == "+":  # the continuation row's divider inside the right column
            rows.append([" ".join(current[0]).strip(), " ".join(current[1]).strip()])
            current = [[], []]
            continue
        left, right = line[1:split].strip(), line[split + 1:-1].strip()
        for k, cell in enumerate((left, right)):
            if cell:
                current[k].append(cell)
    header, *body = rows
    return tuple(header), tuple(r[0] for r in body if r[0]), tuple(r[1] for r in body)


class EnergySavingSectionTests(unittest.TestCase):
    def test_the_print_paragraphs_open_the_section(self) -> None:
        for lang in BLOCKS:
            with self.subTest(lang=lang):
                lines = section(je3000c_view(OPERATION[lang], lang), HEADINGS[lang][0])
                self.assertEqual(list(ENERGY[lang]), paragraphs_before(lines, ENERGY_IMAGE))

    def test_sentences_no_print_carries_are_gone(self) -> None:
        for lang in BLOCKS:
            text = OPERATION[lang].read_text(encoding="utf-8")
            view = je3000c_view(OPERATION[lang], lang)
            for fragment in ENERGY_UNPRINTED[lang]:
                with self.subTest(lang=lang, fragment=fragment):
                    self.assertNotIn(fragment, text)
            for fragment in ENERGY_PRINT_DEFECTS.get(lang, ()):
                with self.subTest(lang=lang, defect=fragment):
                    self.assertNotIn(fragment, view)

    def test_the_english_route_is_unchanged(self) -> None:
        self.assertEqual(MAIN_ENGLISH_OPERATION_SHA256, hashlib.sha256(OPERATION["en"].read_bytes()).hexdigest())


class ResumeFunctionTests(unittest.TestCase):
    def test_the_print_sentence_replaces_the_unprinted_claim(self) -> None:
        for lang in BLOCKS:
            with self.subTest(lang=lang):
                text = OPERATION[lang].read_text(encoding="utf-8")
                self.assertNotIn(RESUME_CLAIM[lang], text)
                lines = section(je3000c_view(OPERATION[lang], lang), HEADINGS[lang][2])
                self.assertEqual(RESUME_INTRO[lang], paragraphs_before(lines, next(l for l in lines if l.startswith("+")))[0])

    def test_the_section_follows_the_lcd_screen(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                lines = OPERATION[lang].read_text(encoding="utf-8").split("\n")
                energy, lcd, resume, keys = (lines.index(h) for h in HEADINGS[lang])
                self.assertLess(energy, lcd)
                self.assertLess(lcd, resume)
                self.assertLess(resume, keys)
                # the capability markers wrap exactly the resume section
                self.assertEqual(".. hb-capability-begin: AC/DC输出记忆恢复", lines[resume - 2])
                end = lines.index(".. hb-capability-end:")
                self.assertLess(resume, end)
                self.assertLess(end, keys)

    def test_the_table_follows_the_print(self) -> None:
        for lang in BLOCKS:
            with self.subTest(lang=lang):
                lines = section(OPERATION[lang].read_text(encoding="utf-8"), HEADINGS[lang][2])
                self.assertEqual(RESUME_TABLE[lang], grid_cells(lines))


class UpsFigureTests(unittest.TestCase):
    def test_the_figure_follows_all_of_the_ups_text(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                lines = je3000c_view(UPS[lang], lang).split("\n")
                self.assertEqual(1, lines.count(UPS_IMAGE))
                image = lines.index(UPS_IMAGE)
                first_table = next(i for i, line in enumerate(lines) if line.lstrip().startswith(".. list-table::"))
                text_lines = [i for i, line in enumerate(lines[:first_table]) if line.startswith("| ")]
                self.assertTrue(text_lines)
                self.assertLess(max(text_lines), image)
                self.assertLess(image, first_table)

    def test_the_print_outputs_place_it_there_too(self) -> None:
        # IDML extraction (the LaTeX branch): heading, the UPS text, the figure, the CAUTION.
        for lang in LANGS:
            with self.subTest(lang=lang):
                kinds = [kind for kind, _ in idml_blocks(UPS[lang], "JE-3000C", lang)]
                image = kinds.index("image")
                self.assertEqual(["h1"], kinds[:1])
                self.assertEqual({"body"}, set(kinds[1:image]))
                self.assertEqual(["component"], kinds[image + 1:])


class UpsWordingTests(unittest.TestCase):
    def test_the_ups_text_is_this_prints(self) -> None:
        for lang in REWORDED:
            with self.subTest(lang=lang):
                lines = je3000c_view(UPS[lang], lang).split("\n")
                text = [line[2:] for line in lines[:lines.index(UPS_IMAGE)] if line.startswith("| ")]
                self.assertEqual(list(UPS_PRINT[lang]), text)
                blocks = idml_blocks(UPS[lang], "JE-3000C", lang)
                self.assertEqual("\n".join(UPS_PRINT[lang]), render(blocks[1][1], lang))

    def test_the_family_wording_and_print_defects_stay_out(self) -> None:
        for lang in REWORDED:
            view = je3000c_view(UPS[lang], lang)
            for fragment in (*UPS_FAMILY_ONLY[lang], *UPS_PRINT_DEFECTS.get(lang, ())):
                with self.subTest(lang=lang, fragment=fragment):
                    self.assertNotIn(fragment, view)


class IsolationTests(unittest.TestCase):
    """Every model without its own branch reads main's UPS template."""

    def test_other_models_read_mains_text(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                view = other_model_view(UPS[lang].read_text(encoding="utf-8"))
                normalized = "\n".join(line.rstrip() for line in view.split("\n"))
                self.assertEqual(MAIN_UPS_SHA256[lang], hashlib.sha256(normalized.encode("utf-8")).hexdigest())

    def test_other_models_idml_extraction_is_mains(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                blocks = idml_blocks(UPS[lang], OTHER_MODEL, lang)
                digest = hashlib.sha256(json.dumps(blocks, ensure_ascii=False).encode("utf-8")).hexdigest()
                self.assertEqual(MAIN_UPS_IDML_OTHER_MODEL_SHA256[lang], digest)

    def test_the_gate_sits_above_the_0915_blocks(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                lines = UPS[lang].read_text(encoding="utf-8").split("\n")
                gates = [i for i, line in enumerate(lines) if "model_je_3000c" in line]
                # The family gate, then JE-3000C's branch. Since 2026-09-27 the family gate
                # also leaves out JE-1000H/JE-3600A (en/es: an outer gate wraps both).
                self.assertEqual(2, len(gates))
                self.assertTrue(lines[gates[0]].lstrip().startswith(".. only:: not "), lines[gates[0]])
                self.assertEqual(".. only:: model_je_3000c", lines[gates[1]].lstrip())
                self.assertLess(max(gates), lines.index(".. only:: not latex"))


def _build_web(tmp: Path, lang: str) -> str:
    fake_bin = tmp / "bin"
    fake_bin.mkdir(exist_ok=True)
    fake_pandoc = fake_bin / "pandoc"
    fake_pandoc.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import sys\n"
        "if '--list-output-formats' in sys.argv:\n"
        "    print('myst')\n"
        "    raise SystemExit(0)\n"
        "source = Path(sys.argv[1])\n"
        "target = Path(sys.argv[sys.argv.index('-o') + 1])\n"
        "target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')\n",
        encoding="utf-8",
    )
    fake_pandoc.chmod(0o755)
    env = {
        **os.environ,
        "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
        "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
        "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
    }
    staging = tmp / f"staging-{lang}"
    result = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), "md", "--config", str(ROOT / f"configs/config.eu-{lang}.yaml"),
         "--model", "JE-3000C", "--region", "EU", "--lang", lang, "--data-root", str(DATA_ROOT),
         "--staging-root", str(staging)],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise AssertionError(f"JE-3000C/{lang} Web build failed:\n" + result.stdout + result.stderr)
    return (staging / f"docs/_build/JE-3000C/EU/{lang}/md/manual_bundle.html").read_text(encoding="utf-8")


def _text(node) -> str:
    return " ".join(node.get_text(" ").split())


class RenderedRouteTests(unittest.TestCase):
    """The six JE-3000C/EU Web routes, built from the frozen source."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.soup = {lang: BeautifulSoup(_build_web(Path(cls._tmp.name), lang), "html.parser") for lang in LANGS}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _operation_sections(self, lang: str) -> list:
        """The level-two sections that share the energy-saving section's parent, in order."""
        soup = self.soup[lang]
        energy = next(s for s in soup.find_all("section")
                      if s.find("h2", recursive=False) and _text(s.find("h2", recursive=False)) == HEADINGS[lang][0])
        return [s for s in energy.parent.find_all("section", recursive=False) if s.find("h2", recursive=False)]

    def test_energy_section_opens_with_the_print_paragraphs(self) -> None:
        for lang in BLOCKS:
            with self.subTest(lang=lang):
                energy = next(s for s in self._operation_sections(lang)
                              if _text(s.find("h2", recursive=False)) == HEADINGS[lang][0])
                panel = energy.select_one('img[data-web-finished-panel-path$="/operation_energy.png"]')
                paragraphs = [_text(p) for p in panel.find_all_previous("p") if p.parent is energy][::-1]
                self.assertEqual(list(ENERGY[lang]), paragraphs)

    def test_resume_follows_the_lcd_screen_with_the_print_sentence(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                titles = [_text(s.find("h2", recursive=False)) for s in self._operation_sections(lang)]
                energy, lcd, resume, keys = (titles.index(h) for h in HEADINGS[lang])
                self.assertEqual([lcd, resume, keys], [energy + 1, energy + 2, energy + 3])
                if lang in BLOCKS:
                    section_node = self._operation_sections(lang)[resume]
                    self.assertEqual(RESUME_INTRO[lang], _text(section_node.find("p")))
                    self.assertNotIn(RESUME_CLAIM[lang], _text(section_node))

    def test_ups_text_precedes_the_figure(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                soup = self.soup[lang]
                panel = soup.select_one('img[data-web-finished-panel-path$="/ups.png"]')
                heading = panel.find_previous("h1")
                between = []
                for node in heading.next_siblings:
                    if node is panel:
                        break
                    if getattr(node, "name", None):
                        between.append(node)
                self.assertTrue(between)
                self.assertTrue(all("line-block" in (n.get("class") or []) for n in between), between)
                following = panel.find_next_sibling()
                self.assertIn("manual-callout-table", following.get("class") or [])
                if lang in REWORDED:
                    lines = [_text(line) for n in between for line in n.select(".line")]
                    self.assertEqual(list(UPS_PRINT[lang]), lines)


if __name__ == "__main__":
    unittest.main()
