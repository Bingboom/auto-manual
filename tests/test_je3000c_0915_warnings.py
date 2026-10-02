"""The new copy of the JE-3000C/EU V2.0-2026-09-15 print, on the Web and in Word only.

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
for every model that uses it (ruling 「所有用这个模板的型号都加」), into the
en/fr/es/de/it JE-1000F/EU review pages that model's Web routes render, and into
JE-500A's own English UPS page (ruling 「也加上」).

Operator ruling 「先只进网页和 Word」 (2026-09-27): until the LaTeX and IDML
renderers keep these callouts' paragraphs, the new copy reaches only the Web and
Word outputs. The PDF (LaTeX) and IDML stay exactly as on main. The gate is the
repo's print/screen branch selection:

* ``.. only:: not latex`` bodies reach the Web and Word pipelines, whose tag set
  is ``html`` plus model/region/lang (``tools.word_bundle_html``); the Sphinx
  LaTeX builder and the IDML extractor (tags ``latex``/``idml``) drop them;
* ``.. only:: latex`` bodies go the other way.

So the energy WARNING is one ``not latex`` block after the NOTE, and each UPS
page holds a ``not latex`` block (the WARNING plus the four-bullet CAUTION)
followed by main's CAUTION, unchanged, under ``latex``.

House fixes, not print defects: en ``outlet. Do`` (printed ``outlet.Do``),
whole-word labels (the fr and uk labels print split across two lines) and a real
list item for the uk bullet (printed without its glyph). Everything else is the
print's text.

The ko, pt-BR, ja and zh UPS carriers (no print block; translations await
review), the US/KR review pages and the JE-1000F/EU uk review page (a language
JE-1000F/EU does not ship) stay byte for byte.
"""

from __future__ import annotations

import csv
import hashlib
import json
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
from tools.idml_rst_extract import extract_page
from tools.word_bundle_html import _normalize_sphinx_only_blocks_for_docutils
from tools.word_bundle_html_only import _build_word_only_tags

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"
LATEX_RENDERER = ROOT / "docs" / "renderers" / "latex"
JE3000C_DATA_ROOT = ROOT / "manual_sources/JE-3000C/EU/en/2.0/phase2"
JE500A_DATA_ROOT = ROOT / "manual_sources/JE-500A/EU/en/2.0/phase2"
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
                                      "p54_06_ups_mode.rst", "p69_06_ups_mode.rst"),
                                          strict=True)
}
JE500A_UPS = TEMPLATES / "page_je500a_eu-en" / "06_ups_mode.rst"

# carrier -> (language, shape, model whose outputs read it)
EDITED: dict[Path, tuple[str, str, str]] = {}
for _lang in LANGS:
    EDITED[ENERGY_CARRIERS[_lang]] = (_lang, "energy", "JE-3000C")
    EDITED[UPS_TEMPLATES[_lang]] = (_lang, "ups", "JE-3000C")
for _lang, _path in JE1000F_EU_REVIEW_UPS.items():
    EDITED[_path] = (_lang, "ups", "JE-1000F")
EDITED[JE500A_UPS] = ("en", "admonitions", "JE-500A")

# sha256 of print_view() of each carrier on origin/main (bd201fc2). The UPS pages had
# no only-blocks there, so for them this is main's file hash itself.
# The six shared UPS templates and the five fr-uk JE-3000C operation carriers moved
# on 2026-09-27 with the JE-3000C/EU print-gap corrections
# (tests/test_je3000c_eu_print_gaps.py): those correct older copy and so reach
# every output, the print one included. The 09-15 copy is still absent from the
# print branch (the checks below), and every other model still reads main's UPS
# text under `.. only:: not model_je_3000c`.
MAIN_PRINT_VIEW_SHA256 = {
    "docs/_review/JE-1000F/EU/page/06_ups_mode.rst": "f4ad3c3009f2b9e980c6fa9bae6870c952b00a7ff10a06a8b88915dde599da39",
    "docs/_review/JE-1000F/EU/page/p24_06_ups_mode.rst": "f5905e61ccfdf8d2086c1831c0c91e55b3f7046afff9729368f0a6ace641fa00",
    "docs/_review/JE-1000F/EU/page/p39_06_ups_mode.rst": "638697edc57cbbae91fed1b50b8ece7c2bbe076e8013a6654941a5d15ac44896",
    "docs/_review/JE-1000F/EU/page/p54_06_ups_mode.rst": "24fd46b5b5aad8d5bb43568ca20362471ff80ddfa734dffaf7b6af686b95d4c8",
    "docs/_review/JE-1000F/EU/page/p69_06_ups_mode.rst": "57fc8674aa798430b0d295fd4d90d6a9eafcd1e3614f1d2b479e44de7de06cfe",
    "docs/templates/page_je500a_eu-en/06_ups_mode.rst": "a940aa134298aef6b23828bbf73a508f69602af92af3f14def0bc218a7f7c138",
    "docs/templates/page_shared/de/06_ups_mode.rst": "b2d0b4c122355a1586234df69d66be790cc3db99b59f715f8c579be28ab25e5b",
    "docs/templates/page_shared/en/06_ups_mode.rst": "3f873ddc0aa14488bf1ecc94f8ebe9f03e840e0e315d6769d4ff4390932ff0ae",
    "docs/templates/page_shared/es/06_ups_mode.rst": "0b399aae3dff661f6f35ba57554b4fb086a0492ac577cf17843885c0a6774267",
    "docs/templates/page_shared/fr/06_ups_mode.rst": "7bcc7496ba80864c9f230483880c9507ee44394c27b8de5f780441ef3c0c0ff8",
    "docs/templates/page_shared/it/06_ups_mode.rst": "2b5cedaa9b5fd1c5740699ff136fcb24fe34fc8a4c03b7b26d3211b48a74d902",
    "docs/templates/page_shared/uk/06_ups_mode.rst": "61f39ee85f1cee748fcb98fcf70c52cdb0666abde276d9f997ca7a03b434ae6d",
    "docs/templates/targets/je3000c/05_operation_guide_de.rst": "b948416c1c2fa778b0967f71820b9f82a8f800e38cc395da384536dad22368b1",
    "docs/templates/targets/je3000c/05_operation_guide_es.rst": "3b4e9aec2cf195022fa41d3e38e47faeff22a5abfa7376c4c4fb650e6787878a",
    "docs/templates/targets/je3000c/05_operation_guide_fr.rst": "5e29a3ba9951cfe535f0281393bdbb7b7013becf37ca083da80fca5505f5c6fa",
    "docs/templates/targets/je3000c/05_operation_guide_it.rst": "8b5aa837431ee54a86a4a7efee2b7a4f35f737cdb4dc5a9e6e7941408d088106",
    "docs/templates/targets/je3000c/05_operation_guide_placeholder.rst": "a63bd412bf45b7e65eef0e17882bcbe0218627f4cd4c64d6c8e68b5e72952529",
    "docs/templates/targets/je3000c/05_operation_guide_uk.rst": "59fcbd705691af6ed6eb0d9f9118cf7c43b092b071d0bc471cfb1be9ed19bbf1",
}

# sha256 of the IDML extractor's blocks (tools.idml_rst_extract.extract_page, ManualIR
# tags: latex, idml, region_eu, the model, the language) for each carrier on origin/main,
# with the same eleven carriers moved by the 2026-09-27 print-gap corrections.
MAIN_IDML_BLOCKS_SHA256 = {
    "docs/_review/JE-1000F/EU/page/06_ups_mode.rst": "597c3c7894164d0b91ddb7c9196851fd15ff6cc57fe07f7dd7bd0cf6afd82952",
    "docs/_review/JE-1000F/EU/page/p24_06_ups_mode.rst": "a16367f5d4b537f71eca5d449b763e9b4667dbcd53088d458c46529c59ac2c6b",
    "docs/_review/JE-1000F/EU/page/p39_06_ups_mode.rst": "e5bb6b398032bcc845e28acd25425cb52d6afcfa0216591d8779c775535d623e",
    "docs/_review/JE-1000F/EU/page/p54_06_ups_mode.rst": "7b27bdd9edd802264eb2f200849d950f6a4fb76c30d9e9c5b279a4d97ba22258",
    "docs/_review/JE-1000F/EU/page/p69_06_ups_mode.rst": "c945f4b17e08674e568650d76bdf547ab5d248ff429decb34fbff0c3ee38a927",
    "docs/templates/page_je500a_eu-en/06_ups_mode.rst": "493ad48295c883a6acb12002884aa932cf6992b9820f4c5a70ef22f974b2fc6f",
    "docs/templates/page_shared/de/06_ups_mode.rst": "77746d4723dcd74109d173898a8d165683192c8cdb685c8e3fd00c3dbecf8373",
    "docs/templates/page_shared/en/06_ups_mode.rst": "f4933b83b5db7e364fd89f05a56e75e135d33466a95b2dcedd0eae69bf51009a",
    "docs/templates/page_shared/es/06_ups_mode.rst": "a4a01c4ee9dc0435e513bcc8373987b97b231ca3a389d2259cc5bbfa3e1a1d17",
    "docs/templates/page_shared/fr/06_ups_mode.rst": "8910ac7b4ffa8c79a6903f50c9ab9700d11fb47056ff72669a98caf64ea055fc",
    "docs/templates/page_shared/it/06_ups_mode.rst": "1e74ae19d0946e2a51c4f4639f7be8fdb9e8bfbbe97b34fb070e0c9baaf1032e",
    "docs/templates/page_shared/uk/06_ups_mode.rst": "ef8ff37faf618c621cae378ac07a261db9481622764a97bb05505b6d85660196",
    "docs/templates/targets/je3000c/05_operation_guide_de.rst": "ae2f29e1609b5d9a81b271e3d59c7797bd99015002fdcdb72df7434436762553",
    "docs/templates/targets/je3000c/05_operation_guide_es.rst": "55c5178e5709c4dc69eb2cedc9ea19d6d95807c0b51053e9b766b9d975489b9f",
    "docs/templates/targets/je3000c/05_operation_guide_fr.rst": "509177f678eaf3902df55297cd10eb6b44cff0046081c198c3f2894b11ab5304",
    "docs/templates/targets/je3000c/05_operation_guide_it.rst": "53e7fbe4b030d359d30d3e20d9e6471779bd7f67953266df8ba90862128a6bc7",
    "docs/templates/targets/je3000c/05_operation_guide_placeholder.rst": "6c8293688acebf52d6eea94d508ead01e52d8053025e0e9a0b5addb03816ab0d",
    "docs/templates/targets/je3000c/05_operation_guide_uk.rst": "7c333569ae8d4ee48359974fba14fa9d5ebee03f070ca3aad07a85f55d0160db",
}

# UPS carriers left for the operator: no print block for their language (ko, pt-BR,
# ja, zh), another region's review line (US, KR), or a review page no output renders
# (JE-1000F/EU uk).
UNTOUCHED_SHA256 = {
    "docs/templates/page_shared/ko/06_ups_mode.rst": "0fb720f9f4a37a3d6ed55fba53ffe7ead1d3aad7e4676c09b871299797cf0c8a",
    "docs/templates/page_shared/pt-BR/06_ups_mode.rst": "640c072659fdc20b24448cae4fbe9666b160ecae06f6963e26d3ce8a0269219e",
    "docs/templates/page_jp/06_ups_mode.rst": "6a27b689763361e948add7d0fe2564b7a68856f63aca054b43ab5a52671f4413",
    "docs/templates/page_zh/06_ups_mode.rst": "88ccfbf022124a2d37c883bb3106df6d457db16f69d20a8b3783f4f4b1f8c006",
    "docs/_review/JE-1000F/US/page/06_ups_mode.rst": "eb87f4fa77ac5ab17ef230ca16569ddb9ca199eafeac76137e7d82677052dc53",
    "docs/_review/JE-1000F/US/page/p27_06_ups_mode.rst": "e9de192a5e93aec9df5c3e9312355908372150022b71cfe63b418418b638d73a",
    "docs/_review/JE-1000F/US/page/p43_06_ups_mode.rst": "3f26e6b0b126f73a3149d962e5ef04e719fa6fcb9d2aa942993f7413dfe5c43a",
    "docs/_review/JE-3000C/KR/ko/page/06_ups_mode.rst": "d36c2800ba5225650e0a7d63929869084e3607363cf819b80af6e4d849b117b2",
    "docs/_review/JE-1000F/EU/page/p84_06_ups_mode.rst": "944bd8194857e03d14f96be112b18e9e4f9f7e4d66f180891a520ab73f2500e5",
}

_ONLY = re.compile(r"\.\. only:: (not latex|latex)")


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def new_texts(lang: str, shape: str) -> list[str]:
    if shape == "energy":
        return [PRINT[lang]["energy"]]
    first, second, items, last = PRINT[lang]["ups"]
    return [first, second, *items, last, PRINT[lang]["bullet"]]


def screen_view(path: Path) -> str:
    """The carrier as the Web and Word pipelines read it (Word's own only-tag set)."""
    lang, _, model = EDITED[path]
    tags = _build_word_only_tags(model=model, region="EU", lang=lang)
    return _normalize_sphinx_only_blocks_for_docutils(path.read_text(encoding="utf-8"), active_tags=tags)


def print_view(text: str) -> str:
    """The branch the Sphinx LaTeX builder and the IDML extractor select.

    Top-level ``.. only:: not latex`` blocks are dropped with the blank line that
    separates them from what follows; ``.. only:: latex`` blocks are unwrapped.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        match = _ONLY.fullmatch(lines[i])
        if not match:
            out.append(lines[i])
            i += 1
            continue
        j = i + 2
        body = []
        while j < len(lines) and (lines[j].startswith("   ") or (
                not lines[j] and j + 1 < len(lines) and lines[j + 1].startswith("   "))):
            body.append(lines[j])
            j += 1
        if match.group(1) == "latex":
            out.extend(line[3:] if line else "" for line in body)
        elif j < len(lines) and not lines[j]:
            j += 1
        i = j
    return "\n".join(out)


def idml_blocks(path: Path) -> list:
    lang, _, model = EDITED[path]
    tags = {"latex", "idml", "region_eu", "model_" + model.lower().replace("-", "_"), f"lang_{lang}"}
    return extract_page(path, tags).blocks


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
        cell = re.sub(r"^- ", "", "\n".join(body))  # the second column's cell marker
        tables.append((index, match.group(1), cell.strip()))
    return tables


def admonitions(text: str) -> list[tuple[str, str]]:
    """(kind, body) of each top-level admonition directive, in order."""
    lines = text.split("\n")
    found = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"\.\. (warning|caution|note)::", line)
        if not match:
            continue
        body = []
        for follower in lines[index + 1:]:
            if follower.strip() and not follower.startswith("   "):
                break
            body.append(follower[3:])
        found.append((match.group(1), "\n".join(body).strip()))
    return found


def warning_cell(lang: str) -> str:
    first, second, items, last = PRINT[lang]["ups"]
    return "\n".join([first, "", second, "", *[f"- {item}" for item in items], "", last])


def sphinx_latex(sources: dict[str, str], out: Path) -> bytes:
    """One Sphinx LaTeX build of ``sources`` with the repo's callout extension; the .tex bytes."""
    src = out / "src"
    src.mkdir(parents=True)
    names, substitutions = [], set()
    for index, (_, text) in enumerate(sorted(sources.items())):
        names.append(f"p{index:02d}")
        (src / f"{names[-1]}.rst").write_text(text, encoding="utf-8")
        substitutions.update(re.findall(r"\|([A-Z][A-Z0-9_]+)\|", text))
    (src / "index.rst").write_text(
        "gate\n====\n\n.. toctree::\n\n" + "".join(f"   {name}\n" for name in names), encoding="utf-8")
    epilog = "".join(f".. |{name}| replace:: {name}\n" for name in sorted(substitutions))
    (src / "conf.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(LATEX_RENDERER)!r})\n"
        "extensions = ['hb_latex_callouts']\n"
        "project = 'gate'\n"
        "latex_documents = [('index', 'gate.tex', 'gate', 'gate', 'manual')]\n"
        f"rst_epilog = {epilog!r}\n",
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, "-m", "sphinx", "-b", "latex", "-q", str(src), str(out / "latex")],
                            check=False, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError("Sphinx LaTeX build failed:\n" + result.stdout + result.stderr)
    return (out / "latex" / "gate.tex").read_bytes()


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


class ScreenCopyTests(unittest.TestCase):
    """What the Web and Word pipelines read: the new copy, placed as printed."""

    def _assert_ups_additions(self, path: Path, lang: str) -> None:
        text = screen_view(path)
        tables = callout_tables(text)
        self.assertEqual([PRINT[lang]["warning"], PRINT[lang]["caution"]], [label for _, label, _ in tables], path)
        self.assertEqual(warning_cell(lang), tables[0][2], path)
        bullets = [line[len("- "):] for line in tables[1][2].split("\n") if line.startswith("- ")]
        self.assertEqual(4, len(bullets), path)
        self.assertEqual(PRINT[lang]["bullet"], bullets[3], path)
        lines = text.split("\n")
        # after the figure and the UPS text, directly before the CAUTION
        self.assertLess(lines.index(".. image:: asset:operation/ups_mode"), tables[0][0], path)
        self.assertEqual(".. list-table::", lines[tables[1][0] - 4], path)
        self.assertEqual(tables[0][0] + 11, tables[1][0] - 4, path)

    def test_energy_warning_follows_the_note(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                text = screen_view(ENERGY_CARRIERS[lang])
                tables = callout_tables(text)
                labels = [label for _, label, _ in tables]
                note = labels.index(PRINT[lang]["note"])
                self.assertEqual((PRINT[lang]["warning"], PRINT[lang]["energy"]), tables[note + 1][1:])
                # nothing but blank lines (and fr's stray empty line block) between NOTE and WARNING
                between = text.split("\n")[tables[note][0] + 2:tables[note + 1][0] - 4]
                self.assertTrue(all(not line.strip() or line.strip() == "|" for line in between), between)
                self.assertEqual(1, text.count(PRINT[lang]["energy"]))

    def test_the_energy_warning_is_scoped_to_je3000c(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                found = sorted(
                    _rel(path) for path in (ROOT / "docs").rglob("*.rst")
                    if "_build" not in path.parts and PRINT[lang]["energy"] in path.read_text(encoding="utf-8")
                )
                self.assertEqual([_rel(ENERGY_CARRIERS[lang])], found)

    def test_shared_templates_show_the_warning_and_the_fourth_bullet(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                self._assert_ups_additions(UPS_TEMPLATES[lang], lang)

    def test_je1000f_eu_review_pages_show_the_same_additions(self) -> None:
        self.assertEqual(["en", "fr", "es", "de", "it"], list(JE1000F_EU_REVIEW_UPS))
        for lang, path in JE1000F_EU_REVIEW_UPS.items():
            with self.subTest(lang=lang):
                self._assert_ups_additions(path, lang)

    def test_je500a_page_shows_the_warning_and_the_fourth_bullet(self) -> None:
        found = admonitions(screen_view(JE500A_UPS))
        self.assertEqual(["warning", "caution"], [kind for kind, _ in found])
        self.assertEqual(warning_cell("en"), found[0][1])
        bullets = [line[len("- "):] for line in found[1][1].split("\n") if line.startswith("- ")]
        self.assertEqual(4, len(bullets))
        self.assertEqual(PRINT["en"]["bullet"], bullets[3])

    def test_every_configured_ups_target_reads_an_edited_template(self) -> None:
        carriers = ups_carriers_of_configured_targets()
        self.assertEqual(set(UPS_TEMPLATES.values()), set(carriers))
        readers = set().union(*carriers.values())
        for model in ("JE-1000F/EU", "JE-1000H/EU", "JE-2000E/EU", "JE-2000F/EU", "JE-3000C/EU", "JE-3600A/EU",
                      "JE-1000F/AU", "JE-1000F/US"):
            self.assertTrue(any(reader.startswith(model + " ") for reader in readers), model)
        for path in carriers:
            with self.subTest(carrier=_rel(path)):
                self._assert_ups_additions(path, path.parent.name)


class PrintCopyTests(unittest.TestCase):
    """What the LaTeX and IDML renderers read: exactly main's copy."""

    def test_the_print_branch_is_mains_carrier(self) -> None:
        self.assertEqual(set(MAIN_PRINT_VIEW_SHA256), {_rel(path) for path in EDITED})
        for path in EDITED:
            with self.subTest(carrier=_rel(path)):
                view = print_view(path.read_text(encoding="utf-8"))
                self.assertEqual(MAIN_PRINT_VIEW_SHA256[_rel(path)], hashlib.sha256(view.encode("utf-8")).hexdigest())

    def test_idml_extraction_is_unchanged_from_main(self) -> None:
        for path, (lang, shape, _) in EDITED.items():
            with self.subTest(carrier=_rel(path)):
                blocks = idml_blocks(path)
                digest = hashlib.sha256(json.dumps(blocks, ensure_ascii=False).encode("utf-8")).hexdigest()
                self.assertEqual(MAIN_IDML_BLOCKS_SHA256[_rel(path)], digest)
                flat = json.dumps(blocks, ensure_ascii=False)
                for text in new_texts(lang, "energy" if shape == "energy" else "ups"):
                    self.assertNotIn(text, flat)

    def test_latex_output_is_the_print_branch_output(self) -> None:
        carriers = {_rel(path): path.read_text(encoding="utf-8") for path in EDITED}
        with tempfile.TemporaryDirectory() as tmp:
            branch = sphinx_latex(carriers, Path(tmp) / "branch")
            printed = sphinx_latex({rel: print_view(text) for rel, text in carriers.items()}, Path(tmp) / "print")
            self.assertEqual(printed, branch)
            for path, (lang, shape, _) in EDITED.items():
                for text in new_texts(lang, "energy" if shape == "energy" else "ups"):
                    self.assertNotIn(text[:60].encode("utf-8"), branch)
            # The check can fail: the screen branch forced into LaTeX does print the copy.
            forced = sphinx_latex({rel: text.replace(".. only:: not latex", ".. only:: latex")
                                   for rel, text in carriers.items()}, Path(tmp) / "forced")
            self.assertIn(b"cardiac pacemaker (pacemaker implant recipients)", forced)


class UntouchedCarrierTests(unittest.TestCase):
    def test_carriers_left_for_the_operator_stay_byte_identical(self) -> None:
        for relative, expected in UNTOUCHED_SHA256.items():
            with self.subTest(carrier=relative):
                self.assertEqual(expected, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())


class HouseWordingTests(unittest.TestCase):
    """The print's typesetting defects must not come back."""

    def test_no_missing_space_after_outlet(self) -> None:
        for path in EDITED:
            with self.subTest(carrier=_rel(path)):
                self.assertNotIn("outlet.Do", path.read_text(encoding="utf-8"))
        for path in (UPS_TEMPLATES["en"], JE1000F_EU_REVIEW_UPS["en"], JE500A_UPS):
            self.assertIn("wall outlet. Do not connect", screen_view(path), _rel(path))

    def test_labels_are_whole_words(self) -> None:
        split = re.compile(r"AVERTISSE(?!MENT)|AVERTISSEM(?!ENT)|ПОПЕРЕД(?!ЖЕННЯ)|ПОПЕРЕДЖЕ(?!ННЯ)")
        for path in EDITED:
            with self.subTest(carrier=_rel(path)):
                self.assertIsNone(split.search(path.read_text(encoding="utf-8")))
        for lang in ("fr", "uk"):
            self.assertIn(f"   * - **{PRINT[lang]['warning']}**\n", screen_view(UPS_TEMPLATES[lang]))
            self.assertIn(f"   * - **{PRINT[lang]['warning']}**\n", screen_view(ENERGY_CARRIERS[lang]))

    def test_the_ukrainian_fourth_bullet_is_a_list_item(self) -> None:
        lines = [line for line in screen_view(UPS_TEMPLATES["uk"]).split("\n") if "Функція UPS працює" in line]
        self.assertEqual([f"       - {PRINT['uk']['bullet']}"], lines)

    def test_no_print_bullet_glyph_is_copied(self) -> None:
        for path in EDITED:
            with self.subTest(carrier=_rel(path)):
                self.assertNotIn("●", path.read_text(encoding="utf-8"))


def _build_web(tmp: Path, *, model: str, lang: str, data_root: Path) -> str:
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
    staging = tmp / f"staging-{model}-{lang}"
    result = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), "md", "--config", str(ROOT / f"configs/config.eu-{lang}.yaml"),
         "--model", model, "--region", "EU", "--lang", lang, "--data-root", str(data_root),
         "--staging-root", str(staging)],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise AssertionError(f"{model}/{lang} Web build failed:\n" + result.stdout + result.stderr)
    return (staging / f"docs/_build/{model}/EU/{lang}/md/manual_bundle.html").read_text(encoding="utf-8")


def _label(table) -> str:
    cell = table.select_one("td.manual-callout-label")
    for sizer in cell.select(".manual-callout-label-sizer"):
        sizer.extract()
    return cell.get_text(" ", strip=True)


class Je3000cRenderedWarningTests(unittest.TestCase):
    """The six JE-3000C/EU Web routes, built from the frozen source, place the new copy as printed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.html = {lang: _build_web(Path(cls._tmp.name), model="JE-3000C", lang=lang, data_root=JE3000C_DATA_ROOT)
                    for lang in LANGS}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_energy_warning_follows_the_energy_saving_panel(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                soup = BeautifulSoup(self.html[lang], "html.parser")
                panel = soup.select_one('img[data-web-finished-panel-path$="/operation_energy.png"]')
                self.assertIsNotNone(panel)
                # the NOTE is printed in the panel and stays its alt text; the WARNING is live text
                self.assertNotIn(PRINT[lang]["energy"], panel.get("alt", ""))
                following = panel.find_next("table", class_="manual-callout-table")
                self.assertEqual(PRINT[lang]["warning"], _label(following))
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
                self.assertEqual(PRINT[lang]["warning"], _label(warning))
                self.assertEqual(PRINT[lang]["caution"], _label(caution))
                first, second, items, last = PRINT[lang]["ups"]
                body = warning.select_one("td.manual-callout-body")
                self.assertEqual([first, second, last], [p.get_text(" ", strip=True) for p in body.find_all("p", recursive=False)])
                self.assertEqual(list(items), [li.get_text(" ", strip=True) for li in body.select("li")])
                bullets = [li.get_text(" ", strip=True) for li in caution.select("td.manual-callout-body li")]
                self.assertEqual(4, len(bullets))
                self.assertEqual(PRINT[lang]["bullet"], bullets[3])


class Je500aRenderedWarningTests(unittest.TestCase):
    """JE-500A/EU en, built from its frozen source, adds the UPS WARNING and the fourth bullet."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.html = _build_web(Path(cls._tmp.name), model="JE-500A", lang="en", data_root=JE500A_DATA_ROOT)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_ups_warning_precedes_the_four_bullet_caution(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        heading = next(h for h in soup.find_all("h1") if h.get_text(" ", strip=True) == "UNINTERRUPTIBLE POWER SUPPLY (UPS)")
        section = []
        for sibling in heading.next_siblings:
            if getattr(sibling, "name", None) == "h1":
                break
            section.append(sibling)
        ups = BeautifulSoup("".join(str(node) for node in section), "html.parser")
        warnings = ups.select('[data-callout-variant="warning"]')
        cautions = ups.select('[data-callout-variant="caution"]')
        self.assertEqual((1, 1), (len(warnings), len(cautions)))
        first, second, items, last = PRINT["en"]["ups"]
        body = warnings[0].select_one(".manual-callout-body")
        paragraphs = [p.get_text(" ", strip=True) for p in body.find_all("p", recursive=False)]
        self.assertEqual([first, second, last], paragraphs)
        self.assertEqual(list(items), [li.get_text(" ", strip=True) for li in warnings[0].select("li")])
        self.assertIs(warnings[0].find_next(class_="manual-callout-table"), cautions[0])
        bullets = [li.get_text(" ", strip=True) for li in cautions[0].select("li")]
        self.assertEqual(4, len(bullets))
        self.assertEqual(PRINT["en"]["bullet"], bullets[3])


if __name__ == "__main__":
    unittest.main()
