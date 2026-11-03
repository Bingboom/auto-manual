"""JP Japanese Explorer / power bank Git-only manuals: source identity, verbatim copy, artwork and replay."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary

ROOT = Path(__file__).resolve().parents[1]
PACKAGES: dict[str, dict] = {
    "JE-100A": {
        "path": "manual_sources/JE-100A/JP/ja/git-20261103-2becaa50",
        "sha256": "2becaa507bbfd8d051888ac85d96a5399f0959224e9e6acb85211599baa06262",
        "markdown": "manual_je100a_jp_ja.md",
        "facts": ("JE-100A", "6.2Ah / 16V DC 99.2Wh(31000mAh 3.2V)", "充放電サイクル2000回後も初期容量の80%以上を維持"),
        "foreign": ("JE-100C", "Explorer 100D", "96Wh", "Power Bank"),
        "print_only": ("JAK-UM-V1", "お買い上げありがとうございます。"),
        "tamper": ("6.2Ah / 16V DC 99.2Wh", "6.3Ah / 16V DC 99.2Wh"),
    },
    "JE-100C": {
        "path": "manual_sources/JE-100C/JP/ja/git-20261103-64dd5f53",
        "sha256": "64dd5f5336e40426277bd217a555194461ab2b66f396e4a23308fac43d0203c3",
        "markdown": "manual_je100c_jp_ja.md",
        "facts": ("JE-100C", "96Wh (5Ah/19.2V DC)", "3,000回の充放電後も容量の80%以上を維持"),
        "foreign": ("JE-100A", "Explorer 100 Plus", "99.2Wh", "Power Bank"),
        "print_only": ("写真はイメージです。実際の商品とは異なる場合があります。", "お買い上げありがとうございます。"),
        "tamper": ("96Wh (5Ah/19.2V DC)", "97Wh (5Ah/19.2V DC)"),
    },
    "JE-76A": {
        "path": "manual_sources/JE-76A/JP/ja/git-20261103-d8f7d338",
        "sha256": "d8f7d338fd208af056c0dda9991422227627ab771245e791858e1480978b013c",
        "markdown": "manual_je76a_jp_ja.md",
        "facts": ("JE-76A", "JE-76A-WH", "76.8Wh", "最大 100W, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A"),
        "foreign": ("JE-100A", "JE-100C", "Explorer 100", "99.2Wh"),
        "print_only": ("お買い上げありがとうございます。",),
        "tamper": ("76.8Wh", "77.8Wh"),
    },
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def squash(value: str) -> str:
    return "".join(value.split())


def visible_text(markdown: str) -> str:
    soup = BeautifulSoup(markdown, "html.parser")
    for node in soup.find_all(["style", "script"]):
        node.decompose()
    return squash(soup.get_text(""))


class ExplorerJpJaWebTests(unittest.TestCase):
    def each(self):
        for model, case in PACKAGES.items():
            with self.subTest(model=model):
                yield model, case, ROOT / case["path"]

    def test_identity_and_candidate_status(self):
        for model, case, package in self.each():
            manifest = read(package / "source_manifest.json")
            self.assertEqual(manifest["target"]["model"], model)
            self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
            self.assertEqual(manifest["target"]["technical_version"], package.name)
            self.assertEqual(manifest["route"], f"{model}/JP/ja/md")
            self.assertIs(manifest["legacy_default"], True)
            self.assertEqual(manifest["original_source"]["sha256"], case["sha256"])
            self.assertEqual(file_sha256(package / manifest["original_source"]["filename"]), case["sha256"])
            self.assertNotIn("file_token", json.dumps(manifest))
            ir = read(package / "web/ja/manual.ir.json")
            if manifest["publication_status"] == "operator-authorized-git-only-release":
                self.assertTrue(ir["metadata"]["publication_eligible"])
            else:
                self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
                self.assertFalse(ir["metadata"]["publication_eligible"])
                self.assertFalse((package / "source/approval.json").exists())

    def test_inputs_are_pinned(self):
        for _, _, package in self.each():
            manifest = read(package / "source_manifest.json")
            for row in manifest["inputs"]:
                self.assertEqual(file_sha256(package / row["path"]), row["sha256"], row["path"])
            listed = {row["path"] for row in manifest["inputs"]}
            for folder in ("source", "assets"):
                for path in (package / folder).rglob("*"):
                    if path.is_file():
                        self.assertIn(path.relative_to(package).as_posix(), listed)

    def test_every_web_line_is_selectable_text_in_the_page(self):
        for _, case, package in self.each():
            markdown = (package / "web/ja" / case["markdown"]).read_text(encoding="utf-8")
            page = visible_text(markdown)
            soup = BeautifulSoup(markdown, "html.parser")
            alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
            lines = [line for p in read(package / "source/transcription.json")["pages"] if p["web"]
                     for line in p["lines"]]
            missing = []
            for line in lines:
                text = squash(line["text"]).replace("[+]", "+")
                if line["id"].startswith(("fig.", "names.")):
                    if text not in alts:
                        missing.append(line["id"])
                elif text not in page and text.rstrip(":：") not in page and text not in alts:
                    missing.append(line["id"])
            self.assertEqual(missing, [])

    def test_model_facts_and_print_only_pages(self):
        for _, case, package in self.each():
            markdown = (package / "web/ja" / case["markdown"]).read_text(encoding="utf-8")
            page = visible_text(markdown)
            for fact in case["facts"]:
                self.assertIn(squash(fact), page)
            for foreign in case["foreign"] + case["print_only"]:
                self.assertNotIn(squash(foreign), page)

    def test_assets_and_shared_symbols(self):
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        for _, case, package in self.each():
            recipe = read(package / "source/asset_recipe.json")
            for symbol in recipe["symbols"]:
                shared = keys[symbol["shared_symbol_key"]]
                self.assertEqual(shared["path"], symbol["shared_path"])
                self.assertEqual(file_sha256(package / symbol["path"]), shared["sha256"])
            for item in recipe["reused"]:
                self.assertEqual(file_sha256(package / item["path"]), item["sha256"])
                self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
            markdown = (package / "web/ja" / case["markdown"]).read_text(encoding="utf-8")
            for img in BeautifulSoup(markdown, "html.parser").find_all("img"):
                self.assertTrue((package / "web/ja" / img["src"]).is_file(), img["src"])
            admission = read(package / "source_manifest.json").get("symbol_asset_admission", {})
            rows = admission.get("locales", {}).get("ja", [])
            self.assertEqual([row["asset_ref"] for row in rows], [s["path"] for s in recipe["symbols"]])

    def test_content_is_rebuilt_from_transcription(self):
        for model, _, package in self.each():
            builder = load(f"{model}_jp_ja_build_content", package / "build_content.py")
            built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
            self.assertEqual(built, read(package / "source/ja/content.json"))

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        for model, case, package in self.each():
            rebuild = load(f"{model}_jp_ja_rebuild", package / "rebuild.py")
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "replay"
                rebuild.rebuild(output)
                for name in (case["markdown"], "manual.ir.json", "_static/source_geometry.css"):
                    self.assertEqual((output / name).read_bytes(), (package / "web/ja" / name).read_bytes(), name)

    def test_changed_source_input_is_rejected(self):
        for model, case, package in self.each():
            module = load(f"{model}_jp_ja_rebuild_copy", package / "rebuild.py")
            with tempfile.TemporaryDirectory() as temp:
                source = Path(temp) / "source"
                shutil.copytree(package, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
                path = source / "source/ja/content.json"
                before, after = case["tamper"]
                text = path.read_text(encoding="utf-8")
                self.assertIn(before, text)
                path.write_text(text.replace(before, after), encoding="utf-8")
                module.SOURCE_ROOT = source
                with self.assertRaisesRegex(ValueError, "input missing or changed"):
                    module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
