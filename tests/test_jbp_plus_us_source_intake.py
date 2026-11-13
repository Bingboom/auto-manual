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

    def test_cover_facts_stay_out_of_the_web_body(self):
        for model, (_, _, version) in CASES.items():
            with self.subTest(model=model):
                data = transcription(model)
                self.assertEqual(data["cover_facts"]["version_line"], "Version: " + version)
                first = data["chapters"][0]
                self.assertTrue(first["heading_from_first_component"])
                self.assertTrue(first["blocks"][0]["text"].startswith("Congratulations on your new"))
                markdown = next((package(model) / "web/en").glob("manual_*.md")).read_text()
                self.assertTrue(markdown.startswith("<p>Congratulations on your new"))
                for cover_only in ("USER MANUAL", "Version: JAK-UM", "Model: " + model, "Contact us"):
                    self.assertNotIn(cover_only, markdown)

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


class JbpPlusUsReleaseCopyTests(unittest.TestCase):
    def test_release_copy_changes_metadata_only(self):
        for model in CASES:
            with self.subTest(model=model):
                candidate = package(model)
                release = candidate.parent / (candidate.name + "-release")
                approval = json.loads((release / "source/release_approval.json").read_text())
                self.assertEqual(approval["merge_authorization"], "MA-438")
                self.assertEqual(approval["candidate_path"], candidate.relative_to(ROOT).as_posix())
                self.assertEqual(
                    approval["candidate_IR_sha256"],
                    hashlib.sha256((candidate / "web/en/manual.ir.json").read_bytes()).hexdigest(),
                )
                manifest = json.loads((release / "source_manifest.json").read_text())
                self.assertTrue(manifest["publication_eligible"])
                self.assertEqual(manifest["publication_status"], "operator-approved-git-only-release")
                self.assertEqual(manifest["revision_of"], approval["candidate_path"])
                served = sorted(p.relative_to(release / "web/en").as_posix()
                                for p in (release / "web/en").rglob("*") if p.is_file())
                self.assertNotIn("shared-style-admission.json", served)
                for name in served:
                    if name != "manual.ir.json":
                        self.assertEqual((release / "web/en" / name).read_bytes(),
                                         (candidate / "web/en" / name).read_bytes(), name)
                self.assertEqual((release / "evidence/publish_shared_style_admission.json").read_bytes(),
                                 (candidate / "web/en/shared-style-admission.json").read_bytes())
                release_ir = json.loads((release / "web/en/manual.ir.json").read_text())
                candidate_ir = json.loads((candidate / "web/en/manual.ir.json").read_text())
                self.assertEqual(release_ir["content_sha256"], candidate_ir["content_sha256"])
                self.assertEqual(release_ir["pages"], candidate_ir["pages"])
                self.assertEqual(release_ir["metadata"]["pending_source_review"], [])
