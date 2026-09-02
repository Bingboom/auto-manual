"""Bundled faces must be nameable, or InDesign resolves none of the family.

OpenType restricts name ID 2 to Regular / Italic / Bold / Bold Italic. A first
pass at the Japanese weights put "DemiLight" and "Medium" there. The files were
valid TrueType and their hashes matched the manifest, so every existing check
passed -- and InDesign then failed to register the family at all, reporting every
Japanese run as a missing font. Nothing in the repo could have caught it.

The convention these tests pin is the one Google's own Noto static releases use:
a non-RIBBI weight folds into the family name (ID 1) with ID 2 back at Regular,
and the real family and style live in the typographic names (ID 16 / 17), which
is what style linking reads.
"""

from __future__ import annotations

import struct
import unittest
from pathlib import Path

from tools.idml.font_family import DELIVERY_FONT_FAMILY_TOKENS

ROOT = Path(__file__).resolve().parents[1]
FONT_ROOT = ROOT / "docs/templates/word_template/common_assets/fonts/idml_portable"
RIBBI = frozenset({"Regular", "Italic", "Bold", "Bold Italic"})
WANTED = (1, 2, 4, 6, 16, 17)


def name_records(path: Path) -> dict[int, str]:
    """Read the Windows-platform name records without a font library."""
    data = path.read_bytes()
    table_count = struct.unpack(">H", data[4:6])[0]
    offset = None
    for index in range(table_count):
        record = 12 + index * 16
        if data[record:record + 4] == b"name":
            offset = struct.unpack(">I", data[record + 8:record + 12])[0]
            break
    if offset is None:  # pragma: no cover - would mean a corrupt font
        raise AssertionError(f"{path.name} has no name table")
    count, string_offset = struct.unpack(">HH", data[offset + 2:offset + 6])
    out: dict[int, str] = {}
    for index in range(count):
        record = offset + 6 + index * 12
        platform, encoding, _lang, name_id, length, str_off = struct.unpack(
            ">HHHHHH", data[record:record + 12]
        )
        if name_id not in WANTED or platform != 3:
            continue
        start = offset + string_offset + str_off
        raw = data[start:start + length]
        try:
            out.setdefault(name_id, raw.decode("utf-16-be").strip("\x00").strip())
        except UnicodeDecodeError:  # pragma: no cover
            continue
    return out


class BundledFontNameTables(unittest.TestCase):
    def _faces(self):
        for token in DELIVERY_FONT_FAMILY_TOKENS:
            for face in token.faces:
                path = FONT_ROOT / f"{face.postscript_name}.ttf"
                if path.exists():
                    yield token, face, path

    def test_at_least_one_multi_weight_family_is_covered(self) -> None:
        """Guard the guard: this test is worthless if it matches nothing."""
        multi = [
            token
            for token in DELIVERY_FONT_FAMILY_TOKENS
            if len(token.faces) > 1
            and any(
                (FONT_ROOT / f"{face.postscript_name}.ttf").exists()
                for face in token.faces
            )
        ]
        self.assertTrue(multi, "no bundled multi-weight family found to check")

    def test_subfamily_name_is_ribbi_legal(self) -> None:
        for _token, face, path in self._faces():
            with self.subTest(face=face.postscript_name):
                names = name_records(path)
                self.assertIn(
                    names.get(2),
                    RIBBI,
                    f"{path.name} name ID 2 is {names.get(2)!r}; OpenType allows "
                    f"only {sorted(RIBBI)}, and an illegal value stops the whole "
                    "family from registering",
                )

    def test_typographic_names_carry_the_real_family_and_weight(self) -> None:
        """Only where they are load-bearing.

        A family with one RIBBI face needs no typographic names -- the upstream
        single-weight Noto faces omit them, legally. They become required the
        moment a family has more than one face, because that is when InDesign
        has to link styles rather than just resolve a name.
        """
        for token, face, path in self._faces():
            if len(token.faces) == 1:
                continue
            with self.subTest(face=face.postscript_name):
                names = name_records(path)
                self.assertEqual(token.name, names.get(16), "typographic family")
                self.assertEqual(face.style_name, names.get(17), "typographic style")

    def test_postscript_name_matches_the_declared_face(self) -> None:
        for _token, face, path in self._faces():
            with self.subTest(face=face.postscript_name):
                self.assertEqual(face.postscript_name, name_records(path).get(6))

    def test_non_ribbi_weight_folds_into_the_family_name(self) -> None:
        for token, face, path in self._faces():
            if face.style_name in RIBBI:
                continue
            with self.subTest(face=face.postscript_name):
                self.assertEqual(
                    f"{token.name} {face.style_name}",
                    name_records(path).get(1),
                    "a non-RIBBI weight must appear in name ID 1",
                )

    def test_full_name_is_family_plus_style(self) -> None:
        for token, face, path in self._faces():
            if len(token.faces) == 1:
                continue
            with self.subTest(face=face.postscript_name):
                self.assertEqual(
                    f"{token.name} {face.style_name}", name_records(path).get(4)
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
