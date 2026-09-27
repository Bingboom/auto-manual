"""The German 12 V caution follows each model's own approved print.

The DC/USB section's 12 V caution called the car socket "Der DC-12-V-Anschluss"
for every model. The approved EU-UK prints (DE block) differ by model:

- JE-1000F (PDF page 64) and JE-2000E (PDF page 70): "Die DC-12V-Buchse ...";
  the other two bullets match the shared wording.
- JE-1000H (PDF page 63) and JE-3000C (PDF page 60): all three bullets are
  worded differently ("Der Zigarettenanzünderanschluss ...").
- JE-2000F (PDF page 60) prints "Die DC-12-V-Anschluss", an article error, so
  it keeps the shared "Der DC-12-V-Anschluss".

JE-1000H shares the German carrier with JE-2000F, so its wording lives in a
``model_je_1000h`` branch; these tests also pin that the branch selects per
model the way the Web renderer evaluates ``.. only::`` blocks.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.word_bundle_html import _normalize_sphinx_only_blocks_for_docutils
from tools.word_bundle_html_only import _build_word_only_tags

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"

SHARED = "Der DC-12-V-Anschluss ist nur mit 12-V-Autobatterien kompatibel und nicht für 24-V-Systeme geeignet."
BUCHSE = "Die DC-12V-Buchse ist nur mit 12-V-Autobatterien kompatibel und nicht für 24-V-Systeme geeignet."
CIGARETTE_LIGHTER = (
    "Der Zigarettenanzünderanschluss ist nur mit 12V-Autobatterien kompatibel und nicht für 24V-Systeme geeignet.",
    "Starten Sie das Fahrzeug nicht, während das Gerät die Autobatterie über den 12V-DC-Ausgang "
    "(Zigarettenanzünderanschluss) lädt, da dies das Gerät beschädigen kann.",
    "Diese Funktion ist ausschließlich für den Notfall vorgesehen und kann eine vollständig entladene "
    "oder defekte Autobatterie nicht aufladen.",
)


def web_view(path: Path, model: str) -> str:
    """The carrier as the Web renderer keeps it for one German EU target."""
    return _normalize_sphinx_only_blocks_for_docutils(
        path.read_text(encoding="utf-8"),
        active_tags=_build_word_only_tags(model=model, region="EU", lang="de"),
    )


class GermanTwelveVoltCautionTests(unittest.TestCase):
    def test_model_specific_carriers_follow_their_print(self) -> None:
        cases = {
            ROOT / "docs/_review/JE-1000F/EU/page/p53_05_operation_guide_placeholder.rst": (BUCHSE,),
            TEMPLATES / "page_eu-de/05_operation_guide_je2000e.rst": (BUCHSE,),
            TEMPLATES / "targets/je3000c/05_operation_guide_de.rst": CIGARETTE_LIGHTER,
        }
        for path, sentences in cases.items():
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                for sentence in sentences:
                    self.assertIn(sentence, text)
                self.assertNotIn(SHARED, text)

    def test_shared_carrier_branches_for_je1000h_only(self) -> None:
        shared = TEMPLATES / "page_eu-de/05_operation_guide_placeholder.rst"
        je1000h = web_view(shared, "JE-1000H")
        for sentence in CIGARETTE_LIGHTER:
            self.assertIn(sentence, je1000h)
        self.assertNotIn(SHARED, je1000h)

        je2000f = web_view(shared, "JE-2000F")
        self.assertIn(SHARED, je2000f)
        self.assertNotIn("Zigarettenanzünderanschluss", je2000f)


if __name__ == "__main__":
    unittest.main()
