"""Exercise the native rebind function with InDesign's font-style reset behavior."""
from __future__ import annotations

import json
import shutil
import subprocess
import unittest

from tools.indesign_finalize import JSX


@unittest.skipUnless(shutil.which("node"), "Node is needed to exercise native JSX")
class JapaneseFontRebindTests(unittest.TestCase):
    def rebind(self, *, missing_style: str = "", language: str = "ja") -> dict:
        source = JSX.read_text(encoding="utf-8")
        functions = source[source.index("    function isJapaneseCodeUnit("):
                           source.index("    function substituteMissingFont(")]
        harness = r'''
const missingStyle = MISSING_STYLE;
const family = "HB Manual Sans JP (OTF)";
function waitForInstalledApplicationFont(name) {
    return name === family + "\t" + missingStyle ? null : {name: name};
}
const chars = [
    {contents: "目", fontStyle: "Bold"},
    {contents: "次", fontStyle: "Medium"},
    {contents: "あ", fontStyle: "DemiLight"},
    {contents: "ア", fontStyle: "Regular"},
    {contents: "A", fontStyle: "Italic"}
];
chars.forEach(function (char) {
    Object.defineProperty(char, "appliedFont", {
        set: function (font) {
            this.selectedFont = font.name;
            this.fontStyle = font.name.split("\t")[1];
        }
    });
});
const doc = {
    stories: [{characters: {everyItem: function () {
        return {getElements: function () { return chars; }};
    }}}],
    recompose: function () {}
};
let report = null, error = null;
try { report = rebindJapanesePortableFont(doc, family + "\tRegular", LANGUAGE); }
catch (exc) { error = String(exc); }
process.stdout.write(JSON.stringify({chars: chars, report: report, error: error}));
'''
        harness = harness.replace("MISSING_STYLE", json.dumps(missing_style))
        harness = harness.replace("LANGUAGE", json.dumps(language))
        result = subprocess.run(
            [shutil.which("node"), "-e", functions + harness],
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)

    def test_rebind_preserves_each_japanese_weight_and_leaves_latin_alone(self) -> None:
        result = self.rebind()
        self.assertIsNone(result["error"])
        self.assertEqual(
            ["Bold", "Medium", "DemiLight", "Regular", "Italic"],
            [char["fontStyle"] for char in result["chars"]],
        )
        for char in result["chars"][:4]:
            self.assertEqual(
                "HB Manual Sans JP (OTF)\t" + char["fontStyle"], char["selectedFont"]
            )
        self.assertNotIn("selectedFont", result["chars"][4])
        self.assertEqual(4, result["report"]["replacements"])

    def test_missing_required_weight_stops_export_instead_of_downgrading(self) -> None:
        result = self.rebind(missing_style="Bold")
        self.assertIsNone(result["report"])
        self.assertIn("Bold", result["error"])

    def test_non_japanese_document_keeps_original_fonts(self) -> None:
        result = self.rebind(language="en")
        self.assertIsNone(result["report"])
        self.assertTrue(all("selectedFont" not in char for char in result["chars"]))
