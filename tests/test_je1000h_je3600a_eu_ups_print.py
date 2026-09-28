"""JE-1000H/EU and JE-3600A/EU: the UPS body follows each model's own print (2026-09-27).

Operator ruling 「JE-1000H/JE-3600A UPS 措辞按印刷（推荐）」: where the UPS body of these
two models' Web differs from their own approved print, it follows the print.

* JE-1000H/EU, EUUK V2.0-2026-08-03 print (sha256 07e9ac4b...), all six language
  blocks (PDF pages 14-15/31-32/48-49/65-66/82-83/99-100). The first sentence names
  the printed buttons. The rest is the print's wording: in fr/de/it/uk the JE-3000C
  print's, in en/es the wording the JE-3000C print shares but its Web does not use.
  The bypass sentence is one line, and the peak output is the printed 7.83 A (the
  frozen source's ``ups_bypass_output`` row held 10 A).
* JE-3600A/EU 2026-05-25 print (sha256 bfbcc437...), the en/es/fr routes (PDF pages
  14/48/31): es takes the printed "cargue", "en el modo derivación" and "menor que";
  fr takes "mode dérivation"; en joins the bypass sentence, which the print sets as
  one paragraph. The two sentences the print sets inside the figure are unchanged:
  the crop prints them, and the page moves them into the figure's alt text
  (covered annotations, which fail the build if the copy changes).

Both prints place the figure after the first sentence, so it stays there. Values
come from the frozen sources in the house format (``7.83 A``, ``7,83 A``); the
product name stays ``|PRODUCT_NAME|`` (the de/it blocks print the short
"Explorer 1000 Plus"); rewritten lines keep the print's apostrophes.

The six carriers are shared, so each model reads its own ``.. only:: model_je_1000h``
or ``model_je_3600a`` branch. JE-3000C and every other model read main's text: the
isolation tests pin their screen views to main's docutils output, and
tests/test_je3000c_eu_print_gaps.py and tests/test_je3000c_0915_warnings.py pin
the other-model source view and the JE-3000C IDML blocks.
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

from bs4 import BeautifulSoup
from docutils.core import publish_parts

from tools.build_paths import resolve_web_illustration_manifest
from tools.idml_rst_extract import extract_page
from tools.utils.spec_master import resolve_template_substitutions_from_spec_master
from tools.word_bundle_html import _normalize_sphinx_only_blocks_for_docutils
from tools.word_bundle_html_only import _build_word_only_tags

ROOT = Path(__file__).resolve().parents[1]
UPS = {lang: ROOT / "docs/templates/page_shared" / lang / "06_ups_mode.rst"
       for lang in ("en", "fr", "es", "de", "it", "uk")}
DATA_ROOTS = {
    "JE-1000H": ROOT / "manual_sources/JE-1000H/EU/en/2.0/phase2",
    "JE-3600A": ROOT / "manual_sources/JE-3600A/EU/en/2026-05-25/phase2",
}
ROUTES = {"JE-1000H": ("en", "fr", "es", "de", "it", "uk"), "JE-3600A": ("en", "es", "fr")}
UPS_IMAGE = ".. image:: asset:operation/ups_mode"
LATEX_RENDERER = ROOT / "docs" / "renderers" / "latex"

# The UPS body as each print block sets it, one line per paragraph, with the frozen
# source's values. The figure follows the first line.
PRINT = {
    ("JE-1000H", "en"): (
        "Connect the product to a wall outlet with the AC charging cable, then press the AC 1/AC 2 output button and power your appliances at the same time.",
        "An Uninterruptible Power Supply (UPS) is a type of continuous power system that provides automated backup electric power to a load when the mains grid power fails.",
        "In the event of a sudden loss of grid power, the Jackery Explorer 1000 Plus will automatically switch to stored power within 10 ms to keep your appliances running.",
        "In UPS mode, the unit's peak output reaches 7.83 A before power outages. As simultaneous charging/discharging is enabled in Bypass Mode, the actual output power is lower than the rated output power in this mode, but returns to the rated output power during outages.",
    ),
    ("JE-1000H", "fr"): (
        "Connectez le produit à une prise murale à l’aide du câble de charge CA, puis appuyez sur le bouton d'alimentation CA 1/CA 2 pour alimenter vos appareils en même temps.",
        "Une alimentation sans interruption (ASI) est un système d’alimentation continue qui fournit automatiquement une alimentation électrique de secours à une charge lorsque l’alimentation du réseau principal est interrompue.",
        "En cas de perte soudaine de l’alimentation du réseau, le Jackery Explorer 1000 Plus basculera automatiquement sur l’alimentation stockée en moins de 10 ms pour maintenir vos appareils en fonctionnement.",
        "En mode ASI, la puissance de crête de sortie de l’appareil atteint 7,83 A avant les coupures de courant. Comme la charge et la décharge simultanées sont activées en mode dérivation, la puissance de sortie réelle est inférieure à la puissance nominale en mode dérivation, mais revient à la puissance nominale lors des coupures.",
    ),
    ("JE-1000H", "es"): (
        "Conecte el producto a una toma de corriente con el cable de carga de CA, luego presione el botón de energía CA y cargue sus electrodomésticos al mismo tiempo.",
        "Un sistema de alimentación ininterrumpida (UPS) es un tipo de sistema de energía continua que proporciona energía eléctrica de respaldo automática a una carga cuando falla la energía de la red principal.",
        "En caso de una pérdida repentina de energía de la red, el Jackery Explorer 1000 Plus cambiará automáticamente a la energía almacenada en menos de 10 ms para mantener sus electrodomésticos en funcionamiento.",
        "En modo UPS, la potencia máxima de salida de la unidad alcanza 7,83 A antes de los cortes de energía. Como la carga y descarga simultáneas están habilitadas en el modo derivación, la potencia de salida real es menor que la potencia nominal en este modo, pero vuelve a la potencia nominal durante los cortes.",
    ),
    ("JE-1000H", "de"): (
        "Schließen Sie das Produkt mit dem AC-Ladekabel an eine Steckdose an und drücken Sie anschließend die AC1- oder AC2-Taste, um gleichzeitig Ihre Geräte mit Strom zu versorgen.",
        "Eine unterbrechungsfreie Stromversorgung (UPS) ist ein kontinuierliches Stromversorgungssystem, das bei einem Ausfall der Netzstromversorgung automatisch Backup-Strom für angeschlossene Geräte bereitstellt.",
        "Im Falle eines plötzlichen Stromausfalls schaltet der Jackery Explorer 1000 Plus automatisch innerhalb von 10 ms auf die gespeicherte Energie um, damit Ihre Geräte weiterhin betrieben werden können.",
        "Voraussetzung: Das Produkt ist eingeschaltet.",
        "Im USV-Modus erreicht das Gerät vor Stromausfällen eine Spitzenausgangsstromstärke von 7,83 A. Da im Bypass-Modus gleichzeitiges Laden und Entladen möglich ist, liegt die tatsächliche Ausgangsleistung in diesem Modus unter der Nennleistung; bei Stromausfällen wird jedoch wieder die Nennleistung erreicht.",
    ),
    ("JE-1000H", "it"): (
        "Collegare il prodotto a una presa a muro con il cavo di ricarica CA, quindi premere il pulsante di alimentazione CA1 o CA2 e alimentare contemporaneamente i propri dispositivi.",
        "Condizione: assicurarsi che il prodotto sia acceso.",
        "Un gruppo di continuità (UPS) è un tipo di sistema di alimentazione continua che fornisce automaticamente energia elettrica di backup a un carico quando l'alimentazione dalla rete elettrica viene a mancare.",
        "In caso di improvvisa interruzione della corrente di rete, Jackery Explorer 1000 Plus passerà automaticamente all’energia immagazzinata entro 10 ms per mantenere in funzione i dispositivi collegati.",
        "In modalità UPS, la potenza di picco dell'unità raggiunge i 7,83 A prima dell'interruzione di corrente. Poiché la modalità Bypass consente la ricarica/scarica simultanea, la potenza di uscita effettiva è inferiore alla potenza di uscita nominale in questa modalità, ma torna alla potenza di uscita nominale durante le interruzioni di corrente.",
    ),
    ("JE-1000H", "uk"): (
        "Підключіть продукт до розетки за допомогою кабелю заряджання змінного струму, потім натисніть кнопку виходу AC 1/AC 2 і одночасно живіть ваші прилади.",
        "Джерело безперебійного живлення (ДБЖ) — це тип системи безперервного живлення, що забезпечує автоматичне резервне електроживлення навантаження у разі відмови електромережі.",
        "У разі раптового відключення електроенергії Jackery Explorer 1000 Plus автоматично перемкнеться на накопичену енергію протягом 10 мс, щоб ваші прилади продовжували працювати.",
        "У режимі ДБЖ піковий вихідний струм пристрою досягає 7,83 A до відключення електроенергії. Оскільки в режимі байпаса (Bypass Mode) увімкнено одночасне заряджання/розряджання, фактична вихідна потужність у цьому режимі нижча за номінальну, але під час відключень вона повертається до номінальної вихідної потужності.",
    ),
    # JE-3600A: lines 2 and 3 are printed inside the figure (the covered annotations).
    ("JE-3600A", "en"): (
        "Connect the product to a wall outlet with the AC charging cable, then press the AC power button and power your appliances at the same time.",
        "An uninterruptible power supply (UPS) is a type of continual power system that provides automated backup electric power to a load when the mains grid power fails.",
        "In the event of a sudden loss of grid power, Jackery Explorer 3600 Plus will automatically switch to stored power within 10 ms to keep your appliances running.",
        "In UPS mode, the unit's peak output reaches 10 A before power outages. As simultaneous charging/discharging is enabled in Bypass Mode, the actual output power is lower than the rated output power in this mode but returns to rated output power during outages.",
    ),
    ("JE-3600A", "es"): (
        "Conecte el producto a una toma de corriente con el cable de carga de CA, luego presione el botón de energía CA y cargue sus electrodomésticos al mismo tiempo.",
        "Un sistema de alimentación ininterrumpida (UPS) es un tipo de sistema de energía continua que proporciona energía eléctrica de respaldo automática a una carga cuando falla la energía de la red principal.",
        "En caso de una pérdida repentina de energía de la red, Jackery Explorer 3600 Plus cambiará automáticamente a la energía almacenada en menos de 10 ms para mantener sus electrodomésticos en funcionamiento.",
        "En modo UPS, la potencia máxima de salida de la unidad alcanza 10 A antes de los cortes de energía. Como la carga y descarga simultáneas están habilitadas en el modo derivación, la potencia de salida real es menor que la potencia nominal en este modo, pero vuelve a la potencia nominal durante los cortes.",
    ),
    ("JE-3600A", "fr"): (
        # Already the print's words; only its apostrophes differ, so it keeps the family line.
        "Connectez le produit à une prise murale à l'aide du câble de charge CA, puis appuyez sur le bouton d’alimentation CA pour alimenter vos appareils en même temps.",
        "Une alimentation sans coupure (UPS) est un système d'alimentation continue qui fournit automatiquement une alimentation électrique de secours à une charge lorsque l'alimentation du réseau principal est interrompue.",
        "En cas de perte soudaine de l'alimentation du réseau, le Jackery Explorer 3600 Plus basculera automatiquement sur l'alimentation stockée en moins de 10 ms pour maintenir vos appareils en fonctionnement.",
        "En mode UPS, la puissance de crête de sortie de l’appareil atteint 10 A avant les coupures de courant. Comme la charge et la décharge simultanées sont activées en mode dérivation, la puissance de sortie réelle est inférieure à la puissance nominale en mode dérivation, mais revient à la puissance nominale lors des coupures.",
    ),
}
FIGURE_LINES = {"JE-3600A": (1, 2)}  # indexes of the lines the JE-3600A crops print
# The Web's previous wording, which these prints do not use (it stays on the other models).
FAMILY_ONLY = {
    ("JE-1000H", "en"): ("AC1/AC2 power button", "continual power system", "in this mode but returns to rated"),
    ("JE-1000H", "fr"): ("sans coupure (UPS)", "mode bypass", "En mode UPS"),
    ("JE-1000H", "es"): ("y alimente sus", "en modo bypass", "es inferior a la potencia nominal"),
    ("JE-1000H", "de"): ("Spitzenleistung von", "damit Ihre Geräte weiterlaufen", "AC-1-Ausgangstaste/AC-2-Ausgangstaste"),
    ("JE-1000H", "it"): ("energia di riserva", "prima dei interruzioni", "premi il pulsante AC 1/2"),
    ("JE-1000H", "uk"): ("(UPS) - це", "зникнення мережевого живлення", "натисніть кнопку AC і"),
    ("JE-3600A", "es"): ("y alimente sus", "en modo bypass", "es inferior a la potencia nominal"),
    ("JE-3600A", "fr"): ("mode bypass",),
}
# The family split the bypass sentence over two lines, which the Web showed as two paragraphs.
SPLIT_TAIL = {
    "en": "the actual output power is lower than the rated output power in this mode but returns to rated output power during outages.",
    "es": "la potencia de salida real es inferior a la potencia nominal en este modo, pero vuelve a la potencia nominal durante los cortes.",
}

# sha256 of each carrier on origin/main a3c7a2d1. Dropping the two new branches and
# restoring the family gate (en/es: unwrapping the outer gate) gives these bytes.
MAIN_CARRIER_SHA256 = {
    "en": "f6fe2af83c81cced8534e3e0f69007722171d34629973856ad6745231474575b",
    "fr": "1106415e98861dd55e25ebfde767392df7b36d910209bba6d9fd5eeeafffed54",
    "es": "ef3e9271b781da8ef2a7d7cae3aa4f1a3d049c7a1ec7451a5cc1c4bff721b0e5",
    "de": "b6afd0e48a3bc07114babf349d3b8a739c437642c22f9cd643bf18b2708211f8",
    "it": "bd9dad19387574302ead42e155ea2034d735ad323ac8fce9274eb906da51954f",
    "uk": "ea8c970a78fa105fe7aac0ffccbdfdb32a3dc041a3e1dd3f953e5b04da6fe69d",
}
NEW_BRANCHES = (".. only:: model_je_1000h", ".. only:: model_je_3600a")
OUTER_GATE = ".. only:: not (model_je_1000h or model_je_3600a)"  # en/es: wraps main's text
FAMILY_GATES = {".. only:: not (model_je_3000c or model_je_1000h or model_je_3600a)": ".. only:: not model_je_3000c",
                ".. only:: not (model_je_3000c or model_je_1000h)": ".. only:: not model_je_3000c"}

# sha256 of the docutils HTML of each carrier's screen view (tools.word_bundle_html's
# only-normalizer, the Web/Word tag set) on origin/main a3c7a2d1, for JE-3000C and
# for another model (JE-2000E stands for every model without its own branch).
MAIN_SCREEN_HTML_SHA256 = {
    "JE-3000C": {
        "en": "1fa3a6cd58ea61431c1da4c0c626922100f234f32fea6433095e358606ecf00a",
        "fr": "befa3f48abad68183efb949e2aac2e9ff0064badc668212ae610ca76f26edf83",
        "es": "dd2415bd06c7c0b9e7dc377d0d046a8216fdf2749d7ee74ed44bbb359965b4ec",
        "de": "78d3d33c043bdc284610b749fc050fea73ca176615cda4acfb0ad8d6ceeef412",
        "it": "05093c87ed0fa068386b4027a7f3e60f21f3854089acd241ad5c825d76555579",
        "uk": "e7fcf059f36201643464ca2519880d0c6719aefce4f731e4b4812e70f2400007",
    },
    "JE-2000E": {
        "en": "dcdc4942141c14b7f35644b9f1ed8898802f7602c7e19f39e17201802547c295",
        "fr": "39a01f6463f6e9f1778181bb67eea939ca112f78d9f8657e2013ee1397c777ee",
        "es": "ebb3cb5753ad163052bef3fd69735410becbd972d1b068c64314e4d01ca82310",
        "de": "e97c5f7b44913c4393dfe7e556620121eec599c5de6f56d80ba25b0d93bcd9ed",
        "it": "d6698f56b5405e22c91b532dde9c3188552a64f17420a94ce5e6963c017ea7ae",
        "uk": "b05b22b4c8ca86cebfb4731800d1341ed67d861b92a0974cfd4a639126516f15",
    },
}

_VALUES: dict[tuple[str, str], dict[str, str]] = {}


def values(model: str, lang: str) -> dict[str, str]:
    if (model, lang) not in _VALUES:
        _VALUES[model, lang] = resolve_template_substitutions_from_spec_master(
            DATA_ROOTS[model] / "Spec_Master.csv", model=model, region="EU", lang=lang)
    return _VALUES[model, lang]


def render(text: str, model: str, lang: str) -> str:
    found = values(model, lang)
    return re.sub(r"\|([A-Z][A-Z0-9_]+)\|", lambda m: found.get(m.group(1), m.group(0)), text)


def screen_view(model: str, lang: str) -> str:
    """The carrier as the model's Web and Word pipelines read it."""
    tags = _build_word_only_tags(model=model, region="EU", lang=lang)
    return _normalize_sphinx_only_blocks_for_docutils(UPS[lang].read_text(encoding="utf-8"), active_tags=tags)


def ups_body(view: str) -> list[str]:
    """The UPS body lines and the figure marker, up to the first callout table."""
    lines = view.split("\n")
    end = next(i for i, line in enumerate(lines) if line.lstrip().startswith(".. list-table::"))
    return [line[2:] if line.startswith("| ") else UPS_IMAGE for line in lines[:end]
            if line.startswith("| ") or line == UPS_IMAGE]


def _block_end(lines: list[str], start: int) -> int:
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith("   ")):
        end += 1
    return end


def without_new_branches(text: str) -> str:
    """The carrier with the JE-1000H/JE-3600A branches removed and main's family gate back."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i] in NEW_BRANCHES:
            i = _block_end(lines, i)
        elif lines[i] == OUTER_GATE:
            end = _block_end(lines, i)
            out.extend(line[3:] if line.startswith("   ") else line for line in lines[i + 2:end])
            i = end
        else:
            out.append(FAMILY_GATES.get(lines[i], lines[i]))
            i += 1
    return "\n".join(out)


def screen_html_sha256(model: str, lang: str) -> str:
    rst = screen_view(model, lang)
    names = sorted(set(re.findall(r"\|([A-Z][A-Z0-9_]+)\|", rst)))
    rst += "\n\n" + "".join(f".. |{name}| replace:: {name}\n" for name in names)
    body = publish_parts(rst, writer_name="html5", settings_overrides={"report_level": 5, "halt_level": 6})["body"]
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def idml_blocks(model: str, lang: str) -> list:
    tags = {"latex", "idml", "region_eu", "model_" + model.lower().replace("-", "_"), f"lang_{lang}"}
    return extract_page(UPS[lang], tags).blocks


def sphinx_latex(tag: str, out: Path) -> str:
    """One Sphinx LaTeX build of the six carriers with ``-t <tag>``; the .tex text."""
    src = out / "src"
    src.mkdir(parents=True)
    names = []
    substitutions: set[str] = set()
    for lang, path in UPS.items():
        text = path.read_text(encoding="utf-8")
        names.append(f"ups_{lang}")
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
    result = subprocess.run([sys.executable, "-m", "sphinx", "-b", "latex", "-q", "-t", tag, "-t", "region_eu",
                             str(src), str(out / "latex")], check=False, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError("Sphinx LaTeX build failed:\n" + result.stdout + result.stderr)
    return (out / "latex" / "gate.tex").read_text(encoding="utf-8")


class ScreenWordingTests(unittest.TestCase):
    """What the Web and Word pipelines read for the two models."""

    def test_the_ups_body_is_the_prints(self) -> None:
        for (model, lang), printed in PRINT.items():
            with self.subTest(model=model, lang=lang):
                body = [render(line, model, lang) for line in ups_body(screen_view(model, lang))]
                self.assertEqual([printed[0], UPS_IMAGE, *printed[1:]], body)

    def test_the_previous_web_wording_is_gone(self) -> None:
        for (model, lang), fragments in FAMILY_ONLY.items():
            view = render(screen_view(model, lang), model, lang)
            for fragment in fragments:
                with self.subTest(model=model, lang=lang, fragment=fragment):
                    self.assertNotIn(fragment, view)
        for model in ROUTES:
            for lang, tail in SPLIT_TAIL.items():
                with self.subTest(model=model, lang=lang, split=True):
                    self.assertNotIn(tail, ups_body(render(screen_view(model, lang), model, lang)))

    def test_the_figure_crops_keep_their_covered_lines(self) -> None:
        # Changing a line a crop prints would fail the Web build (covered annotations).
        for lang in ROUTES["JE-3600A"]:
            with self.subTest(lang=lang):
                manifest = resolve_web_illustration_manifest(
                    ROOT / f"configs/config.eu-{lang}.yaml", repo_root=ROOT, model="JE-3600A", region="EU")
                entry = next(item for item in json.loads(manifest.read_text(encoding="utf-8"))["illustrations"]
                             if item["path"].endswith("/ups.png"))
                covered = [binding["text"] for binding in entry["covered_annotations"]]
                printed = PRINT["JE-3600A", lang]
                self.assertEqual([printed[i] for i in FIGURE_LINES["JE-3600A"]], covered)


class FrozenSourceValueTests(unittest.TestCase):
    def test_je1000h_peak_output_is_the_printed_bypass_current(self) -> None:
        with (DATA_ROOTS["JE-1000H"] / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = {row["Row_key"]: row for row in csv.DictReader(handle)}
        ups, bypass = rows["ups_bypass_output"], rows["ac_output_bypass"]
        self.assertEqual("7.83 A", ups["Value_source"])
        self.assertTrue(bypass["Value_source"].endswith("7.83A"), bypass["Value_source"])
        for lang in ("fr", "es", "de", "it", "uk"):
            with self.subTest(lang=lang):
                self.assertEqual("7,83 A", ups[f"Value_{lang}"])
                self.assertTrue(bypass[f"Value_{lang}"].endswith(", 7,83 A"), bypass[f"Value_{lang}"])

    def test_je3600a_peak_output_already_matched(self) -> None:
        for lang in ROUTES["JE-3600A"]:
            with self.subTest(lang=lang):
                self.assertEqual("10 A", values("JE-3600A", lang)["UPS_BYPASS_OUTPUT_TEXT"])


class PrintOutputTests(unittest.TestCase):
    """The PDF (Sphinx LaTeX) and IDML read the same branch."""

    def test_idml_extraction_reads_the_model_branch(self) -> None:
        for (model, lang), printed in PRINT.items():
            with self.subTest(model=model, lang=lang):
                blocks = idml_blocks(model, lang)
                self.assertEqual(["h1", "body", "image", "body", "component"], [kind for kind, _ in blocks])
                self.assertEqual(printed[0], render(blocks[1][1], model, lang))
                self.assertEqual("\n".join(printed[1:]), render(blocks[3][1], model, lang))

    def test_sphinx_latex_selects_the_model_branch(self) -> None:
        # Fragments of each branch, and of the family text they replace, that LaTeX does
        # not escape (no placeholder, apostrophe or hyphen).
        je1000h = ("AC 1/AC 2 output button", "continuous power system", "CA 1/CA 2 pour alimenter",
                   "y cargue sus", "oder AC2", "CA1 o CA2", "кнопку виходу AC 1/AC 2")
        je3600a = ("y cargue sus", "en el modo derivación", "mode dérivation")
        family = ("continual power system", "y alimente sus", "sans coupure (UPS)", "Spitzenleistung von",
                  "energia di riserva", "кнопку AC і одночасно")
        with tempfile.TemporaryDirectory() as tmp:
            tex = {tag: sphinx_latex(tag, Path(tmp) / tag)
                   for tag in ("model_je_1000h", "model_je_3600a", "model_je_2000e")}
        for fragment in je1000h:
            with self.subTest(model="JE-1000H", fragment=fragment):
                self.assertIn(fragment, tex["model_je_1000h"])
                self.assertNotIn(fragment, tex["model_je_2000e"])
        for fragment in je3600a:
            with self.subTest(model="JE-3600A", fragment=fragment):
                self.assertIn(fragment, tex["model_je_3600a"])
        for fragment in family:
            with self.subTest(model="JE-2000E", fragment=fragment):
                self.assertIn(fragment, tex["model_je_2000e"])
                self.assertNotIn(fragment, tex["model_je_1000h"])
        # JE-3600A has no de/it/uk route; those carriers give it the family text.
        self.assertIn("Spitzenleistung von", tex["model_je_3600a"])


class IsolationTests(unittest.TestCase):
    def test_the_change_is_only_the_two_branches(self) -> None:
        for lang, path in UPS.items():
            with self.subTest(lang=lang):
                stripped = without_new_branches(path.read_text(encoding="utf-8"))
                self.assertEqual(MAIN_CARRIER_SHA256[lang], hashlib.sha256(stripped.encode("utf-8")).hexdigest())

    def test_je3000c_and_other_models_read_mains_screen_view(self) -> None:
        for model, expected in MAIN_SCREEN_HTML_SHA256.items():
            for lang, digest in expected.items():
                with self.subTest(model=model, lang=lang):
                    self.assertEqual(digest, screen_html_sha256(model, lang))

    def test_je3600a_reads_the_family_text_where_it_has_no_route(self) -> None:
        for lang in ("de", "it", "uk"):
            with self.subTest(lang=lang):
                self.assertEqual(screen_html_sha256("JE-2000E", lang), screen_html_sha256("JE-3600A", lang))

    def test_every_model_gate_sits_above_the_0915_blocks(self) -> None:
        for lang, path in UPS.items():
            with self.subTest(lang=lang):
                lines = path.read_text(encoding="utf-8").split("\n")
                gates = [i for i, line in enumerate(lines) if line.lstrip().startswith(".. only::") and "model_" in line]
                self.assertTrue(gates)
                self.assertLess(max(gates), lines.index(".. only:: not latex"))


def _build_web(tmp: Path, model: str, lang: str) -> str:
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
         "--model", model, "--region", "EU", "--lang", lang, "--data-root", str(DATA_ROOTS[model]),
         "--staging-root", str(staging)],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise AssertionError(f"{model}/{lang} Web build failed:\n" + result.stdout + result.stderr)
    return (staging / f"docs/_build/{model}/EU/{lang}/md/manual_bundle.html").read_text(encoding="utf-8")


def _text(node) -> str:
    return " ".join(node.get_text(" ").split())


class RenderedRouteTests(unittest.TestCase):
    """The nine Web routes, built from the frozen sources."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.soup = {(model, lang): BeautifulSoup(_build_web(Path(cls._tmp.name), model, lang), "html.parser")
                    for model, langs in ROUTES.items() for lang in langs}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_the_page_shows_the_print_around_the_figure(self) -> None:
        for (model, lang), soup in self.soup.items():
            with self.subTest(model=model, lang=lang):
                printed = PRINT[model, lang]
                covered = FIGURE_LINES.get(model, ())
                panel = soup.select_one('img[data-web-finished-panel-path$="/ups.png"]')
                heading = panel.find_previous("h1")
                before = []
                for node in heading.next_siblings:
                    if node is panel:
                        break
                    if getattr(node, "name", None):
                        before.extend(_text(line) for line in node.select(".line"))
                after = []
                for node in panel.next_siblings:
                    if "manual-callout-table" in (getattr(node, "get", lambda *_: None)("class") or []):
                        break
                    if getattr(node, "name", None):
                        after.extend(_text(line) for line in node.select(".line"))
                self.assertEqual([printed[0]], before)
                self.assertEqual([line for i, line in enumerate(printed[1:], 1) if i not in covered], after)
                if covered:
                    self.assertEqual("；".join(printed[i] for i in covered), panel["alt"])


if __name__ == "__main__":
    unittest.main()
