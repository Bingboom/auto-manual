"""The product-line axis must reach both renderer planes, spelled identically.

`tools/page_contracts.py` has always resolved requirements through a
`default -> category: -> region: -> capability: -> lang` chain, but until the
`category_*` tag reached the carriers only the last three could be branched on
inside a page. A page that differed per product line had to be cloned.

Two planes render a carrier: Sphinx (HTML/LaTeX, tags via `-t`) and the manual
IR (IDML, tags in `base_tags`). A tag one plane sets and the other does not is
not an error in either -- `.. only::` simply omits the body -- so the divergence
is silent, and these tests are the only thing standing in front of it.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import build_dispatch
from tools.build_docs_theme import normalize_sphinx_tag_value, sphinx_tag_args
from tools.manual_ir import build_manual_ir
from tools.page_contracts import DEFAULT_CATEGORY, resolve_category


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "fixtures" / "phase2"

# One carrier, one body per product line -- the shape Phase 3 will use to fold
# two cloned template trees back into one file.
CARRIER = """.. raw:: latex

   \\HBApplyLang{en}

.. only:: latex and category_bp

   .. raw:: latex

      \\section{PACK}

   The battery pack sentence.

.. only:: latex and category_main

   .. raw:: latex

      \\section{MAIN}

   The main line sentence.

.. only:: latex and category_battery_pack

   .. raw:: latex

      \\section{NORMALIZED}

   The normalized spelling sentence.
"""


def _tags(**kwargs: str | None) -> list[str]:
    return sphinx_tag_args(
        normalize_sphinx_tag_value=normalize_sphinx_tag_value, **kwargs
    )


class TheSphinxPlaneEmitsTheCategory(unittest.TestCase):
    def test_the_category_becomes_a_tag(self) -> None:
        self.assertEqual(["-t", "category_bp"], _tags(category="BP"))

    def test_the_other_axes_are_unchanged(self) -> None:
        self.assertEqual(
            ["-t", "model_je_1000f", "-t", "region_us", "-t", "lang_en"],
            _tags(model="JE-1000F", region="US", lang="en"),
        )

    def test_an_absent_category_emits_nothing(self) -> None:
        self.assertEqual([], _tags(category=None))
        self.assertEqual([], _tags(category="   "))


class TheIRPlaneEmitsTheCategory(unittest.TestCase):
    def _prose(self, category: str | None) -> str:
        with TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "page").mkdir()
            (bundle / "page" / "00_preface.rst").write_text(CARRIER, encoding="utf-8")
            (bundle / "index.rst").write_text(
                ".. include:: page/00_preface.rst\n", encoding="utf-8"
            )
            ir = build_manual_ir(
                root=ROOT,
                bundle_root=bundle,
                model="JBP-2000B",
                region="JP",
                lang="en",
                source="review",
                category=category,
                data_root=DATA,
            )
        return "\n".join(
            str(block.payload) for page in ir.pages for block in page.blocks
        ).lower()

    def test_the_matching_body_survives_and_the_others_do_not(self) -> None:
        pack = self._prose("BP")
        self.assertIn("battery pack sentence", pack)
        self.assertNotIn("main line sentence", pack)

        main = self._prose("MAIN")
        self.assertIn("main line sentence", main)
        self.assertNotIn("battery pack sentence", main)

    def test_an_absent_category_silently_drops_every_branch(self) -> None:
        # Not a bug to fix here -- it is why tools/build_dispatch.py passes
        # --category unconditionally rather than only when it is interesting.
        bare = self._prose(None)
        self.assertNotIn("battery pack sentence", bare)
        self.assertNotIn("main line sentence", bare)

    def test_both_planes_spell_a_multi_word_category_the_same(self) -> None:
        # The whole point: one normalizer. Were the IR to lower-case without
        # collapsing the space (or vice versa), this body would vanish from
        # IDML while still printing in the PDF.
        self.assertEqual(
            ["-t", "category_battery_pack"], _tags(category="Battery Pack")
        )
        self.assertIn("normalized spelling sentence", self._prose("Battery Pack"))


class TheCategoryHasOneSource(unittest.TestCase):
    def test_it_is_read_from_the_configured_skeleton_family(self) -> None:
        self.assertEqual("BP", resolve_category({"skeleton_family": "BP"}))
        self.assertEqual("BP", resolve_category({"skeleton_family": "  BP  "}))

    def test_an_undeclared_family_is_the_main_line(self) -> None:
        self.assertEqual(DEFAULT_CATEGORY, resolve_category({}))
        self.assertEqual(DEFAULT_CATEGORY, resolve_category({"skeleton_family": ""}))
        self.assertEqual(DEFAULT_CATEGORY, resolve_category(None))

    def test_the_shipped_configs_resolve_to_their_declared_line(self) -> None:
        self.assertEqual(
            "BP", build_dispatch._configured_category(ROOT / "configs/config.bp-jp.yaml")
        )
        self.assertEqual(
            "BP", build_dispatch._configured_category(ROOT / "configs/config.bp-us.yaml")
        )
        self.assertEqual(
            DEFAULT_CATEGORY,
            build_dispatch._configured_category(ROOT / "configs/config.us.yaml"),
        )
        self.assertEqual(
            DEFAULT_CATEGORY,
            build_dispatch._configured_category(ROOT / "configs/config.kr.yaml"),
        )

    def test_an_unreadable_config_falls_back_to_the_main_line(self) -> None:
        self.assertEqual(
            DEFAULT_CATEGORY,
            build_dispatch._configured_category(ROOT / "configs/does-not-exist.yaml"),
        )


if __name__ == "__main__":
    unittest.main()
