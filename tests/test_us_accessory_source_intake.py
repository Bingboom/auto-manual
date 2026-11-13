"""Source facts and identity boundaries for the four US accessory candidates."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "JS-45A": ("000912", "2198a1b781b9e62748d19e896e1032e3caeedb458b2556c06918ff0087dce7bf"),
    "JS-38A": ("000913", "8a76fee8450bd436eabdaae9caa1df1319a13a5d281b4c9557dbc36c2575b518"),
    "JS-CONNECTION-GUIDE": ("000716", "899cb3dd395903c4fa41ddbee282e70480e6ce39605107407cb1da295289bece"),
    "JA-IB07A-SO": ("000156", "e1f2a5fad81afdca636bfcf7f619389caf9d367712be208664aa5e85bf2a1ca0"),
}


def package(model):
    suffix, digest = CASES[model]
    return ROOT / "manual_sources" / model / "US/en" / f"git-20261112-{digest[:8]}-m{suffix}"


def transcription(model):
    return json.loads((package(model) / "source/transcription.json").read_text())


def blocks(model, kind):
    return [
        block
        for chapter in transcription(model)["chapters"]
        for block in chapter["blocks"]
        if block["kind"] == kind
    ]


class UsAccessorySourceIntakeTests(unittest.TestCase):
    def test_original_identity_and_candidate_boundary(self):
        for model, (_, digest) in CASES.items():
            with self.subTest(model=model):
                source = package(model)
                manifest = json.loads((source / "source_manifest.json").read_text())
                self.assertEqual(manifest["target"]["model"], model)
                self.assertEqual(manifest["target"]["region"], "US")
                self.assertEqual(manifest["target"]["languages"], ["en"])
                self.assertEqual(manifest["original_source"]["sha256"], digest)
                original = source / manifest["original_source"]["path"]
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)
                self.assertFalse(manifest["publication_eligible"])
                self.assertEqual(
                    manifest["publication_status"], "review-candidate-no-release-authorization"
                )

    def test_curved_tiles_keep_distinct_electrical_ratings_and_real_subscripts(self):
        expected = {
            "JS-45A": ("45W±5%", "9.93A±5%", "10.36A±5%"),
            "JS-38A": ("38W±5%", "8.38A±5%", "9.14A±5%"),
        }
        for model, (power, current, short_circuit) in expected.items():
            with self.subTest(model=model):
                rows = blocks(model, "specification")[0]["rows"]
                self.assertEqual(rows[2][1], power)
                self.assertEqual(rows[3][1], current)
                self.assertEqual(rows[5][1], short_circuit)
                self.assertEqual(rows[5][0]["subscript"], "sc")
                self.assertEqual(rows[6][0]["subscript"], "oc")
                self.assertIn(["Maximum System Voltage", "1000V"], rows)
                self.assertIn(["Ingress Protection", "IP68"], rows)
        first = package("JS-45A") / "assets/inbox-product.png"
        second = package("JS-38A") / "assets/inbox-product.png"
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_bottle_keeps_distinct_warranty_scopes(self):
        model = "JA-IB07A-SO"
        periods = blocks(model, "years")[0]["periods"]
        self.assertEqual([item["number"] for item in periods], ["1", "5"])
        self.assertIn("general warranty", periods[0]["label"])
        self.assertIn("stainless steel vacuum layer", periods[1]["label"])
        common = blocks(model, "warranty")
        coverage = [item for item in common if item["title"] == "Warranty coverage"]
        self.assertEqual(len(coverage), 1)
        self.assertIn("proper proof of purchase", " ".join(coverage[0]["paragraphs"]))
        rows = blocks(model, "specification")[0]["rows"]
        self.assertIn(["Capacity", "24 Fluid Ounces"], rows)
        self.assertIn(["Material", "18/8 Stainless Steel"], rows)

    def test_generic_guide_keeps_port_partition_and_shared_photographs(self):
        model = "JS-CONNECTION-GUIDE"
        data = transcription(model)
        self.assertEqual(data["model"], model)
        rows = blocks(model, "plain_table")[0]["rows"]
        self.assertEqual([len(row[0].splitlines()) for row in rows], [4, 9, 14])
        self.assertEqual(rows[0][1]["text"], "USB-C")
        self.assertIn("DC7909", rows[1][1]["text"])
        self.assertIn("DC8020", rows[2][1]["text"])
        self.assertEqual(rows[2][0].splitlines()[-1], "New Arrivals")
        native = " ".join(block["text"] for block in blocks(model, "paragraph"))
        self.assertIn("does not allow current to flow", native)
        donor = (
            ROOT / "manual_sources/JS-CONNECTION-GUIDE/JP/ja"
            / "git-20261026-bc35fd65-connection-guide/assets"
        )
        for name in ["port-usb-c.png", "port-dc7909.png", "port-dc8020.png"]:
            self.assertEqual((package(model) / "assets" / name).read_bytes(), (donor / name).read_bytes())
