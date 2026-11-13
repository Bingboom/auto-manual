"""Source facts and identity boundaries for the JBP-2000A / JBP-1000A US review candidates."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "JBP-2000A": ("000574", "90e9ed96c7128d4849825ef8179e6e79a677f9c3a709b19cc78c3cffa6d7b050", "JAK-UM-V1.0"),
    "JBP-1000A": ("000575", "a69ce9e14ba0c83a762b9b6530f7bb2652f1cb771d595ffc251cd960c10662ec", "JAK-UM-V5.0"),
}


def package(model):
    suffix, digest, _ = CASES[model]
    return ROOT / "manual_sources" / model / "US/en" / f"git-20261113-{digest[:8]}-m{suffix}"


def transcription(model):
    return json.loads((package(model) / "source/transcription.json").read_text())


def blocks(model, kind):
    return [
        block
        for chapter in transcription(model)["chapters"]
        for block in chapter["blocks"]
        if block["kind"] == kind
    ]


def spec_rows(model, title):
    return next(b["rows"] for b in blocks(model, "specification") if b["title"] == title)


class JbpPlusUsSourceIntakeTests(unittest.TestCase):
    def test_original_identity_and_candidate_boundary(self):
        for model, (suffix, digest, version) in CASES.items():
            with self.subTest(model=model):
                source = package(model)
                manifest = json.loads((source / "source_manifest.json").read_text())
                self.assertEqual(manifest["target"]["model"], model)
                self.assertEqual(manifest["target"]["region"], "US")
                self.assertEqual(manifest["material"], "38-0001-" + suffix)
                self.assertEqual(manifest["original_source"]["sha256"], digest)
                original = source / manifest["original_source"]["path"]
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)
                self.assertEqual(manifest["printed_manual_version"], version)
                self.assertFalse(manifest["publication_eligible"])
                self.assertEqual(
                    manifest["publication_status"], "review-candidate-no-release-authorization"
                )
                self.assertFalse((source / "approval.json").exists())
                self.assertEqual(manifest["shared_component_exceptions"], [])

    def test_each_booklet_keeps_its_own_ratings(self):
        rows = dict(spec_rows("JBP-2000A", "GENERAL INFO"))
        self.assertEqual(rows["Model No."], "JBP-2000A")
        self.assertEqual(rows["Capacity"], "Lithium-ion 45.6Ah / 44.8V DC (2042.8Wh)")
        ports = dict(spec_rows("JBP-2000A", "INPUT PORTS"))
        self.assertEqual(ports["2 x DC Expansion Port"], "32.2V-50.4V⎓97A Max")
        # Printed as-is, including the questionable doubled value (source concern).
        self.assertIn("8A Max, Double to 8A Max", ports["DC input"])
        rows = dict(spec_rows("JBP-1000A", "GENERAL INFO"))
        self.assertEqual(rows["Model No."], "JBP-1000A")
        self.assertEqual(rows["Capacity"], "Lithium-ion 30.4Ah/41.6V DC (1264.64Wh)")
        self.assertEqual(spec_rows("JBP-1000A", "INPUT PORTS"), [["2x DC Expansion Port", "32.5V-46.8V⎓68A Max"]])

    def test_expansion_limits_and_fcc_scope_stay_per_booklet(self):
        def text(model):
            return json.dumps(transcription(model), ensure_ascii=False)

        self.assertIn("Up to 10 sets", text("JBP-2000A"))
        self.assertIn("Up to 3 sets", text("JBP-1000A"))
        self.assertNotIn("1000 Plus", text("JBP-2000A"))
        self.assertNotIn("2000 Plus", text("JBP-1000A"))
        self.assertNotIn("modification", blocks("JBP-2000A", "fcc")[0])
        self.assertIn("modification", blocks("JBP-1000A", "fcc")[0])

    def test_back_cover_contacts_kept_as_printed(self):
        for model in CASES:
            with self.subTest(model=model):
                chapters = {c["id"]: c for c in transcription(model)["chapters"]}
                mexico = [b["text"] for b in chapters["mexico"]["blocks"]]
                self.assertEqual(chapters["mexico"]["title"], "JACKERY MEXICO S.A. DE C.V.")
                self.assertIn("C.P. 03940, Ciudad de México, México", mexico)
                self.assertEqual(chapters["contacts"]["title"], "JACKERY INC.")

    def test_artwork_is_source_bound(self):
        for model in CASES:
            with self.subTest(model=model):
                source = package(model)
                decisions = json.loads((source / "source/asset_decisions.json").read_text())["assets"]
                for slot, row in decisions.items():
                    data = (source / row["path"]).read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"], slot)
                    if row["mode"] == "reuse-packaged-donor":
                        self.assertEqual((ROOT / row["source_path"]).read_bytes(), data)
                    else:
                        self.assertEqual(row["mode"], "new-extraction")


if __name__ == "__main__":
    unittest.main()
