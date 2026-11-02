"""Label-sourced shared Web symbols stay source-bound, inked and replayable."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "docs/renderers/web/assets/shared/symbols"
SOURCE = ROOT / "data/label_sources/EU/2kwh-icon-set-20261029"
INK, PAPER = "#454546", "#ffffff"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _entries() -> list[dict]:
    manifest = json.loads((LIBRARY / "manifest.json").read_text(encoding="utf-8"))
    folder = SOURCE.relative_to(ROOT).as_posix() + "/"
    return [a for a in manifest["assets"] if a.get("provenance", {}).get("source", "").startswith(folder)]


def _replayer():
    try:
        import fitz
    except ImportError:
        return None
    if (fitz.VersionBind, fitz.VersionFitz) != ("1.28.0", "1.29.0"):
        return None  # native SVG serialisation is version-specific
    spec = importlib.util.spec_from_file_location("label_extract_marks", SOURCE / "extract_marks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LabelMarkTests(unittest.TestCase):
    def test_nine_marks_bind_their_label_and_library_file(self) -> None:
        entries = _entries()
        self.assertEqual(9, len(entries))
        for entry in entries:
            provenance = entry["provenance"]
            with self.subTest(key=entry["key"]):
                self.assertEqual(provenance["source_sha256"], _sha256(ROOT / provenance["source"]))
                self.assertEqual(entry["sha256"], _sha256(LIBRARY / entry["path"]))
                self.assertEqual("local-candidate; registry promotion pending", entry["status"])
                self.assertIn("2026-11-02", provenance["decision"])

    def test_only_the_mapped_ink_and_paper_remain(self) -> None:
        """Operator exception: label colours become symbol ink, knockouts paper, hidden paths unfilled."""
        for entry in _entries():
            text = (LIBRARY / entry["path"]).read_text(encoding="utf-8")
            colours = set(re.findall(r'(?:fill|stroke)="([^"]+)"', text))
            with self.subTest(key=entry["key"]):
                self.assertIn(INK, colours)
                self.assertLessEqual(colours, {INK, PAPER, "none"})
                self.assertLessEqual(set(entry["provenance"]["ink_map"].values()), {INK, PAPER})
                self.assertEqual("none" in colours, bool(entry["provenance"].get("hidden_fill_ordinals")))

    def test_replay_from_the_label_pdfs_is_byte_identical(self) -> None:
        module = _replayer()
        if module is None:
            self.skipTest("needs PyMuPDF 1.28.0 / MuPDF 1.29.0, as recorded")
        for entry in _entries():
            native, inked = module.replay(entry)
            with self.subTest(key=entry["key"]):
                self.assertEqual(entry["provenance"]["native_sha256"], hashlib.sha256(native).hexdigest())
                self.assertEqual(entry["sha256"], hashlib.sha256(inked).hexdigest())


if __name__ == "__main__":
    unittest.main()
