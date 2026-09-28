"""The new copy of the JE-3000C/EU V2.0-2026-09-15 print (operator ruling 2026-09-27).

The operator adopted only the new copy of the 09-15 print (sha256 f3264481...);
its figures carry drawing defects, so the Web keeps the V2.0-2026-07-31 crops.
Each of the six language blocks adds three items:

* an Energy Saving Mode WARNING below the energy-saving NOTE (PDF pages
  13/29/45/61/77/93) -- JE-3000C only, in
  ``docs/templates/targets/je3000c/05_operation_guide_*.rst``;
* a UPS WARNING between the UPS text and its CAUTION (PDF pages
  14/30/46/62/78/94), and
* a fourth UPS CAUTION bullet: one unit directly on a wall outlet, no cascade
  (PDF pages 15/31/47/63/79/95).

The two UPS items go into the shared ``docs/templates/page_shared/<lang>/06_ups_mode.rst``
for every model that uses it (ruling 「所有用这个模板的型号都加」), and into the
en/fr/es/de/it JE-1000F/EU review pages, which that model's Web routes render
instead of the templates. House fixes, not print defects: en ``outlet. Do``
(printed ``outlet.Do``), whole-word labels (the fr and uk labels print split
across two lines) and a real list item for the uk bullet (printed without its
glyph). Everything else is the print's text.

The UPS carriers of languages the print has no block for (ko, pt-BR, ja, zh),
the JE-500A English UPS page and the US/KR review pages stay byte for byte:
they await the operator's decision. So does the JE-1000F/EU uk review page:
that model ships no Ukrainian, so no output renders it.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

from tools.config_loader import load_config_mapping
from tools.config_pages import GeneratedPage, RstIncludePage, parse_config_pages

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"
JE3000C_DATA_ROOT = ROOT / "manual_sources/JE-3000C/EU/en/2.0/phase2"
LANGS = ("en", "fr", "es", "de", "it", "uk")

# The print's text per language block. Straight and curly apostrophes are as printed.
PRINT = {
    "en": {
        "warning": "WARNING", "note": "NOTE", "caution": "CAUTION",
        "energy": "When Energy Saving Mode is enabled, the product automatically turns off the AC output if the connected device’s power consumption remains low for the configured period. When powering devices that require continuous power, such as refrigerators, routers, security cameras, or aquarium air pumps, we recommend turning off Energy Saving Mode to prevent unexpected power loss from interrupting their operation.",
        "ups": (
            "Do not use this product for applications such as data servers or medical devices, where a malfunction could endanger life or cause significant property damage.",
            "For the following equipment, a loss of power supply during use could cause serious harm to personal safety or property:",
            ("Medical devices and other equipment closely related to life safety.",
             "Critical equipment such as social infrastructure and public services.",
             "Business-critical enterprise equipment, etc."),
            "Individuals who wear a cardiac pacemaker (pacemaker implant recipients) must not use this product.",
        ),
        "bullet": "The UPS function works only when a single unit is connected directly to a wall outlet. Do not connect multiple portable power stations in series (cascade connection). In a cascaded setup, the UPS function will not operate: the unit may fail to switch over during a power outage, causing connected devices to shut down.",
    },
    "fr": {
        "warning": "AVERTISSEMENT", "note": "REMARQUE", "caution": "ATTENTION",
        "energy": "Lorsque le mode d'économie d'énergie est activé, le produit coupe automatiquement la sortie CA si la consommation de l'appareil connecté reste faible pendant la durée définie. Lorsque vous alimentez des appareils nécessitant une alimentation continue, tels qu'un réfrigérateur, un routeur, une caméra de surveillance ou une pompe à air pour aquarium, il est recommandé de désactiver le mode d'économie d'énergie afin d'éviter qu'une coupure inattendue n'interrompe leur fonctionnement.",
        "ups": (
            "N’utilisez pas ce produit dans des applications telles que des serveurs de données ou des dispositifs médicaux, où un dysfonctionnement pourrait mettre la vie en danger ou entraîner des dommages matériels importants.",
            "Pour les équipements suivants, une perte d’alimentation pendant l’utilisation pourrait entraîner de graves atteintes à la sécurité des personnes ou des biens :",
            ("Dispositifs médicaux et autres équipements étroitement liés à la sécurité des personnes.",
             "Équipements essentiels tels que les infrastructures publiques et les services publics.",
             "Équipements essentiels aux activités de l’entreprise, etc."),
            "Les personnes portant un stimulateur cardiaque (pacemaker) ne doivent pas utiliser ce produit.",
        ),
        "bullet": "La fonction UPS ne fonctionne que lorsqu'un seul appareil est raccordé directement à une prise murale. Ne raccordez pas plusieurs stations d'énergie portables en série (montage en cascade). Dans une configuration en cascade, la fonction UPS ne fonctionne pas : l'appareil peut ne pas basculer lors d'une coupure de courant, ce qui entraîne l'arrêt des appareils connectés.",
    },
    "es": {
        "warning": "ADVERTENCIA", "note": "NOTA", "caution": "PRECAUCIÓN",
        "energy": "Cuando el modo de Ahorro de Energía está activado, el producto apaga automáticamente la salida de CA si el consumo del dispositivo conectado se mantiene bajo durante el período establecido. Al alimentar dispositivos que requieren suministro eléctrico continuo, como frigoríficos, routers, cámaras de seguridad o bombas de aire para acuarios, se recomienda desactivar el modo de Ahorro de Energía para evitar que una interrupción inesperada afecte a su funcionamiento.",
        "ups": (
            "No utilice este producto en aplicaciones como servidores de datos o dispositivos médicos, donde un fallo podría poner en peligro la vida o causar daños materiales significativos.",
            "Para los siguientes equipos, una pérdida de suministro eléctrico durante el uso podría causar graves daños a las personas o a la propiedad:",
            ("Dispositivos médicos y otros equipos estrechamente relacionados con la seguridad de las personas.",
             "Equipos críticos como infraestructuras sociales y servicios públicos.",
             "Equipos empresariales críticos para el negocio, etc."),
            "Las personas que lleven un marcapasos cardíaco (portadores de marcapasos implantado) no deben usar este producto.",
        ),
        "bullet": "La función UPS solo funciona cuando una única unidad está conectada directamente a una toma de pared. No conecte varias estaciones de energía portátiles en serie (conexión en cascada). En una configuración en cascada, la función UPS no funcionará: es posible que la unidad no conmute durante un corte de suministro eléctrico, lo que provocaría que los dispositivos conectados se apaguen.",
    },
    "de": {
        "warning": "WARNUNG", "note": "HINWEIS", "caution": "VORSICHT",
        "energy": "Wenn der Energiesparmodus aktiviert ist, schaltet das Produkt den AC-Ausgang automatisch ab, wenn die Leistungsaufnahme des angeschlossenen Geräts über den eingestellten Zeitraum hinweg niedrig bleibt. Bei der Stromversorgung von Geräten, die eine kontinuierliche Stromversorgung benötigen, z. B. Kühlschränken, Routern, Überwachungskameras oder Aquarium-Luftpumpen, wird empfohlen, den Energiesparmodus auszuschalten, damit der Betrieb der Geräte nicht durch eine unerwartete Stromunterbrechung beeinträchtigt wird.",
        "ups": (
            "Verwenden Sie dieses Produkt nicht für Anwendungen wie Datenserver oder medizinische Geräte, bei denen eine Fehlfunktion lebensgefährlich sein oder erhebliche Sachschäden verursachen kann.",
            "Bei den folgenden Geräten kann ein Ausfall der Stromversorgung während des Betriebs zu schweren Personenschäden oder erheblichen Sachschäden führen:",
            ("Medizinische Geräte und andere Geräte, die unmittelbar der Sicherheit von Menschen dienen.",
             "Kritische Einrichtungen wie Infrastruktur und öffentliche Versorgung.",
             "Geschäftskritische Unternehmenssysteme usw."),
            "Personen mit einem Herzschrittmacher (Schrittmacherträger) dürfen dieses Produkt nicht verwenden.",
        ),
        "bullet": "Die UPS-Funktion funktioniert nur, wenn ein einzelnes Gerät direkt an eine Netzsteckdose angeschlossen ist. Schließen Sie nicht mehrere tragbare Power Stations in Reihe (Kaskadenschaltung) an. In einer Kaskadenschaltung funktioniert die UPS-Funktion nicht: Das Gerät kann bei einem Stromausfall möglicherweise nicht umschalten, wodurch angeschlossene Geräte ausfallen.",
    },
    "it": {
        "warning": "AVVERTENZA", "note": "NOTA", "caution": "ATTENZIONE",
        "energy": "Quando la Modalità di risparmio energetico è attiva, il prodotto disattiva automaticamente l'uscita CA se il consumo energetico del dispositivo collegato rimane basso per il periodo di tempo impostato. Quando si alimentano dispositivi che richiedono un'alimentazione continua, come frigoriferi, router, telecamere di sicurezza o pompe ad aria per acquari, si consiglia di disattivare la Modalità di risparmio energetico per evitare che un'interruzione imprevista ne comprometta il funzionamento.",
        "ups": (
            "Non utilizzare questo prodotto per applicazioni quali server di dati o dispositivi medici, in cui un malfunzionamento potrebbe mettere in pericolo la vita o causare ingenti danni materiali.",
            "Per le seguenti apparecchiature, una perdita dell'alimentazione elettrica durante l'uso potrebbe causare gravi rischi per la sicurezza delle persone o gravi danni materiali:",
            ("Dispositivi medici e altre apparecchiature strettamente correlate alla sicurezza della vita.",
             "Apparecchiature critiche, come infrastrutture sociali e servizi pubblici essenziali.",
             "Apparecchiature aziendali critiche, ecc."),
            "Le persone portatrici di un pacemaker cardiaco (destinatari di un impianto di pacemaker) non devono utilizzare questo prodotto.",
        ),
        "bullet": "La funzione UPS è disponibile solo quando una singola unità è collegata direttamente a una presa a muro. Non collegare più power station portatili in serie (collegamento in cascata). In una configurazione in cascata la funzione UPS non funziona: l'unità potrebbe non commutare durante un'interruzione di corrente, causando lo spegnimento dei dispositivi collegati.",
    },
    "uk": {
        "warning": "ПОПЕРЕДЖЕННЯ", "note": "ПРИМІТКА", "caution": "УВАГА",
        "energy": "Коли режим енергозбереження ввімкнено, виріб автоматично вимикає вихід змінного струму, якщо енергоспоживання підключеного пристрою залишається низьким протягом заданого часу. Під час живлення пристроїв, що потребують безперервного електроживлення, наприклад холодильників, маршрутизаторів, камер відеоспостереження або повітряних насосів для акваріумів, рекомендується вимкнути режим енергозбереження, щоб несподіване знеструмлення не вплинуло на роботу пристроїв.",
        "ups": (
            "Не використовуйте цей продукт у таких сферах застосування, як сервери обробки даних або медичні пристрої, де збій може загрожувати життю або спричинити значну майнову шкоду.",
            "Для наведеного нижче обладнання втрата живлення під час використання може становити серйозну загрозу для життя або майна:",
            ("Медичні пристрої та інше обладнання, безпосередньо пов’язане з безпекою життя.",
             "Критично важливе обладнання, таке як об’єкти соціальної інфраструктури та громадські служби.",
             "Критично важливе для бізнесу обладнання тощо."),
            "Особи з імплантованим кардіостимулятором не повинні використовувати цей продукт.",
        ),
        "bullet": "Функція UPS працює лише тоді, коли один пристрій підключено безпосередньо до розетки. Не підключайте кілька портативних зарядних станцій послідовно (каскадне підключення). У каскадній схемі функція UPS не працює: пристрій може не перемкнутися під час відключення електроенергії, через що підключені пристрої вимкнуться.",
    },
}

ENERGY_CARRIERS = {
    lang: TEMPLATES / "targets/je3000c" / f"05_operation_guide_{'placeholder' if lang == 'en' else lang}.rst"
    for lang in LANGS
}
UPS_TEMPLATES = {lang: TEMPLATES / "page_shared" / lang / "06_ups_mode.rst" for lang in LANGS}
# The pages JE-1000F/EU's en/fr/es/de/it Web routes render (it ships no uk).
JE1000F_EU_REVIEW_UPS = {
    lang: ROOT / "docs/_review/JE-1000F/EU/page" / name
    for lang, name in zip(LANGS[:5], ("06_ups_mode.rst", "p24_06_ups_mode.rst", "p39_06_ups_mode.rst",
                                      "p54_06_ups_mode.rst", "p69_06_ups_mode.rst"))
}

# Each edited carrier before the change: removing the added blocks must give these bytes back.
PRE_CHANGE_SHA256 = {
    "docs/templates/targets/je3000c/05_operation_guide_placeholder.rst": "4c1fc59abf1a3e543e7aedfec355ac183c02500aaf27f3ed6a1983b99880ace0",
    "docs/templates/targets/je3000c/05_operation_guide_fr.rst": "998d04b40534df05a858f5d0ea587ab41a8e1d2f30c84719c63162a248e219ec",
    "docs/templates/targets/je3000c/05_operation_guide_es.rst": "260237c69803ed7735b27f62b32ce5f040c4bc8efdbc67aaa59bcbc5f21b3eaf",
    "docs/templates/targets/je3000c/05_operation_guide_de.rst": "fb2e3d445c05a8b39bc2de0fa1ccf320015a59bf3c88bb4b44934059002f2fe0",
    "docs/templates/targets/je3000c/05_operation_guide_it.rst": "f9a364466bd52bbaccaa50227716fd0355b11d7bfc233413cd4f41e26144a586",
    "docs/templates/targets/je3000c/05_operation_guide_uk.rst": "a31642e4ffe19d465545d514b72c04b4c41494a3d29f2addb2eab286b8ae5a74",
    "docs/templates/page_shared/en/06_ups_mode.rst": "c26c7c9c3c255ef469da87deadf16a5e31d843aebaa88738490637dfa0edcb0e",
    "docs/templates/page_shared/fr/06_ups_mode.rst": "1c7d193805ce2adf1ac0febeefd0e0e78464b511a669719d89ce8dfdb2a658e5",
    "docs/templates/page_shared/es/06_ups_mode.rst": "80e9f2310637c89760d1468385a2d2de3845e0eadfb2badad2ffdb7073b39509",
    "docs/templates/page_shared/de/06_ups_mode.rst": "d948a4922603106bbe57ca270a268a25d8f96e4fb830eb16a850ea120c138479",
    "docs/templates/page_shared/it/06_ups_mode.rst": "6d6b074c0bfc328b83b72f26b64b1c011a4aac38fd744bc8cb00b98b4f3c3880",
    "docs/templates/page_shared/uk/06_ups_mode.rst": "0761ccc0fa73b3029d22c5476ab14a500d80be252a18f9471235865c9252f799",
    "docs/_review/JE-1000F/EU/page/06_ups_mode.rst": "f4ad3c3009f2b9e980c6fa9bae6870c952b00a7ff10a06a8b88915dde599da39",
    "docs/_review/JE-1000F/EU/page/p24_06_ups_mode.rst": "f5905e61ccfdf8d2086c1831c0c91e55b3f7046afff9729368f0a6ace641fa00",
    "docs/_review/JE-1000F/EU/page/p39_06_ups_mode.rst": "638697edc57cbbae91fed1b50b8ece7c2bbe076e8013a6654941a5d15ac44896",
    "docs/_review/JE-1000F/EU/page/p54_06_ups_mode.rst": "24fd46b5b5aad8d5bb43568ca20362471ff80ddfa734dffaf7b6af686b95d4c8",
    "docs/_review/JE-1000F/EU/page/p69_06_ups_mode.rst": "57fc8674aa798430b0d295fd4d90d6a9eafcd1e3614f1d2b479e44de7de06cfe",
}

# UPS carriers left for the operator: no print block for their language, not the
# shared template (JE-500A's own page), another region's review line, or a review
# page no output renders (JE-1000F/EU uk).
UNTOUCHED_SHA256 = {
    "docs/templates/page_shared/ko/06_ups_mode.rst": "0fb720f9f4a37a3d6ed55fba53ffe7ead1d3aad7e4676c09b871299797cf0c8a",
    "docs/templates/page_shared/pt-BR/06_ups_mode.rst": "640c072659fdc20b24448cae4fbe9666b160ecae06f6963e26d3ce8a0269219e",
    "docs/templates/page_jp/06_ups_mode.rst": "6a27b689763361e948add7d0fe2564b7a68856f63aca054b43ab5a52671f4413",
    "docs/templates/page_zh/06_ups_mode.rst": "88ccfbf022124a2d37c883bb3106df6d457db16f69d20a8b3783f4f4b1f8c006",
    "docs/templates/page_je500a_eu-en/06_ups_mode.rst": "a940aa134298aef6b23828bbf73a508f69602af92af3f14def0bc218a7f7c138",
    "docs/_review/JE-1000F/US/page/06_ups_mode.rst": "eb87f4fa77ac5ab17ef230ca16569ddb9ca199eafeac76137e7d82677052dc53",
    "docs/_review/JE-1000F/US/page/p27_06_ups_mode.rst": "e9de192a5e93aec9df5c3e9312355908372150022b71cfe63b418418b638d73a",
    "docs/_review/JE-1000F/US/page/p43_06_ups_mode.rst": "3f26e6b0b126f73a3149d962e5ef04e719fa6fcb9d2aa942993f7413dfe5c43a",
    "docs/_review/JE-3000C/KR/ko/page/06_ups_mode.rst": "d36c2800ba5225650e0a7d63929869084e3607363cf819b80af6e4d849b117b2",
    "docs/_review/JE-1000F/EU/page/p84_06_ups_mode.rst": "944bd8194857e03d14f96be112b18e9e4f9f7e4d66f180891a520ab73f2500e5",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def callout_tables(text: str) -> list[tuple[int, str, str]]:
    """(line index, label, cell body) of each two-column callout list-table, in order."""
    lines = text.split("\n")
    tables = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"   \* - \*\*(.+?)\*\*", line)
        if not match:
            continue
        body = []
        for follower in lines[index + 1:]:
            if follower.strip() and not follower.startswith("     "):
                break
            body.append(follower[7:] if follower.startswith("       ") else follower.strip())
        cell = "\n".join(body)
        cell = re.sub(r"^- ", "", cell)  # the cell marker of the second column
        tables.append((index, match.group(1), cell.strip()))
    return tables


def warning_cell(lang: str) -> str:
    first, second, items, last = PRINT[lang]["ups"]
    return "\n".join([first, "", second, "", *[f"- {item}" for item in items], "", last])


def ups_blocks(lang: str) -> tuple[str, str]:
    """The exact RST the change adds to a UPS page: the WARNING table and the bullet line."""
    first, second, items, last = PRINT[lang]["ups"]
    table = "\n".join([
        ".. list-table::", "   :header-rows: 0", "   :widths: 12 88", "",
        f"   * - **{PRINT[lang]['warning']}**", f"     - {first}", "", f"       {second}", "",
        *[f"       - {item}" for item in items], "", f"       {last}", "", "",
    ])
    return table, f"       - {PRINT[lang]['bullet']}\n"


def energy_block(lang: str) -> str:
    return "\n".join([
        ".. list-table::", "   :header-rows: 0", "   :widths: 12 88", "",
        f"   * - **{PRINT[lang]['warning']}**", f"     - {PRINT[lang]['energy']}", "", "",
    ])


def ups_carriers_of_configured_targets() -> dict[Path, set[str]]:
    """Shared UPS carrier -> the UPS-capable configured targets that read it (six print languages)."""
    capable = {}
    with (ROOT / "data/model_capabilities.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            capable[row["Document_key"]] = row["UPS功能"].strip().upper() == "TRUE"
    carriers: dict[Path, set[str]] = {}
    for config_path in sorted((ROOT / "configs").glob("config.*.yaml")):
        config = load_config_mapping(config_path)
        paths = config.get("paths", {})
        per_target = paths.get("page_manifests") or {}
        for target in config.get("build", {}).get("targets") or []:
            model, region = target["model"], target["region"]
            manifest_rel = str(per_target.get(f"{model}_{region}", paths.get("page_manifest", ""))).replace("{model}", model)
            manifest_path = ROOT / manifest_rel
            if not manifest_rel or not manifest_path.is_file() or not capable.get(f"{model}_{region}"):
                continue
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            pages, _ = parse_config_pages(manifest["pages"], model=model)
            for page in pages:
                relative = page.template if isinstance(page, GeneratedPage) else getattr(page, "file", None)
                if not isinstance(page, (GeneratedPage, RstIncludePage)) or not relative:
                    continue
                path = ROOT / "docs" / relative
                if path.name == "06_ups_mode.rst" and path.parent.name in LANGS and path.parent.parent.name == "page_shared":
                    carriers.setdefault(path, set()).add(f"{model}/{region} ({config_path.name})")
    return carriers


class Je3000cEnergySavingWarningTests(unittest.TestCase):
    def test_each_operation_template_sets_the_warning_right_after_the_note(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                text = ENERGY_CARRIERS[lang].read_text(encoding="utf-8")
                tables = callout_tables(text)
                labels = [label for _, label, _ in tables]
                note = labels.index(PRINT[lang]["note"])
                self.assertEqual((PRINT[lang]["warning"], PRINT[lang]["energy"]), tables[note + 1][1:])
                # still inside ENERGY SAVING MODE: nothing but blank lines, the NOTE
                # and (fr) its stray empty line block lie between NOTE and WARNING.
                between = text.split("\n")[tables[note][0] + 2:tables[note + 1][0] - 4]
                self.assertTrue(all(not line.strip() or line.strip() == "|" for line in between), between)
                self.assertEqual(1, text.count(PRINT[lang]["energy"]))

    def test_the_energy_warning_is_scoped_to_je3000c(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                found = sorted(
                    path.relative_to(ROOT).as_posix()
                    for path in (ROOT / "docs").rglob("*.rst")
                    if "_build" not in path.parts and PRINT[lang]["energy"] in path.read_text(encoding="utf-8")
                )
                self.assertEqual([ENERGY_CARRIERS[lang].relative_to(ROOT).as_posix()], found)


class SharedUpsAdditionTests(unittest.TestCase):
    def _assert_ups_additions(self, path: Path, lang: str) -> None:
        text = path.read_text(encoding="utf-8")
        tables = callout_tables(text)
        self.assertEqual([PRINT[lang]["warning"], PRINT[lang]["caution"]], [label for _, label, _ in tables], path)
        self.assertEqual(warning_cell(lang), tables[0][2], path)
        bullets = [line[len("- "):] for line in tables[1][2].split("\n") if line.startswith("- ")]
        self.assertEqual(4, len(bullets), path)
        self.assertEqual(PRINT[lang]["bullet"], bullets[3], path)
        # the WARNING sits after the figure and the UPS text, directly before the CAUTION
        lines = text.split("\n")
        self.assertLess(lines.index(".. image:: asset:operation/ups_mode"), tables[0][0], path)
        # label, 9 cell lines, one blank line, then the CAUTION's list-table directive
        self.assertEqual(".. list-table::", lines[tables[1][0] - 4], path)
        self.assertEqual(tables[0][0] + 11, tables[1][0] - 4, path)

    def test_shared_templates_carry_the_warning_and_the_fourth_bullet(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                self._assert_ups_additions(UPS_TEMPLATES[lang], lang)

    def test_je1000f_eu_review_pages_carry_the_same_additions(self) -> None:
        self.assertEqual(["en", "fr", "es", "de", "it"], list(JE1000F_EU_REVIEW_UPS))
        for lang, path in JE1000F_EU_REVIEW_UPS.items():
            with self.subTest(lang=lang):
                self._assert_ups_additions(path, lang)

    def test_every_configured_ups_target_reads_an_edited_template(self) -> None:
        carriers = ups_carriers_of_configured_targets()
        self.assertEqual(set(UPS_TEMPLATES.values()), set(carriers))
        readers = set().union(*carriers.values())
        for model in ("JE-1000F/EU", "JE-1000H/EU", "JE-2000E/EU", "JE-2000F/EU", "JE-3000C/EU", "JE-3600A/EU",
                      "JE-1000F/AU", "JE-1000F/US"):
            self.assertTrue(any(reader.startswith(model + " ") for reader in readers), model)
        for path in carriers:
            lang = path.parent.name
            with self.subTest(carrier=path.relative_to(ROOT).as_posix()):
                self._assert_ups_additions(path, lang)


class UntouchedCarrierTests(unittest.TestCase):
    def test_carriers_without_a_print_block_stay_byte_identical(self) -> None:
        for relative, expected in UNTOUCHED_SHA256.items():
            with self.subTest(carrier=relative):
                self.assertEqual(expected, _sha256(ROOT / relative))

    def test_edited_carriers_differ_from_before_only_by_the_added_blocks(self) -> None:
        for relative, expected in PRE_CHANGE_SHA256.items():
            with self.subTest(carrier=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                lang = next(
                    (candidate for candidate, path in ENERGY_CARRIERS.items() if path == ROOT / relative), None
                )
                if lang is not None:
                    removed = text.replace(energy_block(lang), "", 1)
                else:
                    lang = next(candidate for candidate in LANGS
                                if ROOT / relative in (UPS_TEMPLATES[candidate], JE1000F_EU_REVIEW_UPS.get(candidate)))
                    table, bullet = ups_blocks(lang)
                    removed = text.replace(table, "", 1).replace(bullet, "", 1)
                self.assertNotEqual(text, removed, "the added blocks are missing")
                self.assertEqual(expected, hashlib.sha256(removed.encode("utf-8")).hexdigest())


class HouseWordingTests(unittest.TestCase):
    """The print's typesetting defects must not come back."""

    EDITED = (*ENERGY_CARRIERS.values(), *UPS_TEMPLATES.values(), *JE1000F_EU_REVIEW_UPS.values())

    def test_no_missing_space_after_outlet(self) -> None:
        for path in self.EDITED:
            with self.subTest(carrier=path.relative_to(ROOT).as_posix()):
                self.assertNotIn("outlet.Do", path.read_text(encoding="utf-8"))
        self.assertIn("wall outlet. Do not connect", UPS_TEMPLATES["en"].read_text(encoding="utf-8"))

    def test_labels_are_whole_words(self) -> None:
        split = re.compile(r"AVERTISSE(?!MENT)|AVERTISSEM(?!ENT)|ПОПЕРЕД(?!ЖЕННЯ)|ПОПЕРЕДЖЕ(?!ННЯ)")
        for path in self.EDITED:
            with self.subTest(carrier=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(split.search(path.read_text(encoding="utf-8")))
        for lang in ("fr", "uk"):
            self.assertIn(f"   * - **{PRINT[lang]['warning']}**\n", UPS_TEMPLATES[lang].read_text(encoding="utf-8"))
            self.assertIn(f"   * - **{PRINT[lang]['warning']}**\n", ENERGY_CARRIERS[lang].read_text(encoding="utf-8"))

    def test_the_ukrainian_fourth_bullet_is_a_list_item(self) -> None:
        text = UPS_TEMPLATES["uk"].read_text(encoding="utf-8")
        lines = [line for line in text.split("\n") if "Функція UPS працює" in line]
        self.assertEqual([f"       - {PRINT['uk']['bullet']}"], lines)

    def test_no_print_bullet_glyph_is_copied(self) -> None:
        for path in self.EDITED:
            with self.subTest(carrier=path.relative_to(ROOT).as_posix()):
                self.assertNotIn("●", path.read_text(encoding="utf-8"))


def _build_je3000c_web(tmp: Path, lang: str) -> str:
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
         "--model", "JE-3000C", "--region", "EU", "--lang", lang, "--data-root", str(JE3000C_DATA_ROOT),
         "--staging-root", str(staging)],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise AssertionError(f"JE-3000C/{lang} Web build failed:\n" + result.stdout + result.stderr)
    return (staging / f"docs/_build/JE-3000C/EU/{lang}/md/manual_bundle.html").read_text(encoding="utf-8")


class Je3000cRenderedWarningTests(unittest.TestCase):
    """The six JE-3000C/EU Web routes, built from the frozen source, place the new copy as printed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.html = {lang: _build_je3000c_web(Path(cls._tmp.name), lang) for lang in LANGS}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    @staticmethod
    def _callouts(soup: BeautifulSoup) -> list:
        return soup.select("table.manual-callout-table")

    @staticmethod
    def _label(table) -> str:
        cell = table.select_one("td.manual-callout-label")
        for sizer in cell.select(".manual-callout-label-sizer"):
            sizer.extract()
        return cell.get_text(" ", strip=True)

    def test_energy_warning_follows_the_energy_saving_panel(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                soup = BeautifulSoup(self.html[lang], "html.parser")
                panel = soup.select_one('img[data-web-finished-panel-path$="/operation_energy.png"]')
                self.assertIsNotNone(panel)
                # the NOTE is printed in the panel and stays its alt text; the WARNING is live text
                self.assertNotIn(PRINT[lang]["energy"], panel.get("alt", ""))
                following = panel.find_next("table", class_="manual-callout-table")
                self.assertEqual(PRINT[lang]["warning"], self._label(following))
                body = following.select_one("td.manual-callout-body").get_text(" ", strip=True)
                self.assertEqual(PRINT[lang]["energy"], body)
                self.assertEqual(1, " ".join(soup.get_text(" ").split()).count(PRINT[lang]["energy"]))

    def test_ups_warning_precedes_a_four_bullet_caution(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                soup = BeautifulSoup(self.html[lang], "html.parser")
                panel = soup.select_one('img[data-web-finished-panel-path$="/ups.png"]')
                self.assertIsNotNone(panel)
                warning = panel.find_next("table", class_="manual-callout-table")
                caution = warning.find_next("table", class_="manual-callout-table")
                self.assertEqual(PRINT[lang]["warning"], self._label(warning))
                self.assertEqual(PRINT[lang]["caution"], self._label(caution))
                first, second, items, last = PRINT[lang]["ups"]
                body = warning.select_one("td.manual-callout-body")
                self.assertEqual([first, second, last], [p.get_text(" ", strip=True) for p in body.find_all("p", recursive=False)])
                self.assertEqual(list(items), [li.get_text(" ", strip=True) for li in body.select("li")])
                bullets = [li.get_text(" ", strip=True) for li in caution.select("td.manual-callout-body li")]
                self.assertEqual(4, len(bullets))
                self.assertEqual(PRINT[lang]["bullet"], bullets[3])


if __name__ == "__main__":
    unittest.main()
