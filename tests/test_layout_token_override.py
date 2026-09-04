"""The layout plane inherits and overrides the way the config plane does.

The repo is built on inheritance and override. The config plane shows the
shape: `extends:` names the layer below, a deep merge lets the later
definition win, and the chain is real -- `config.eu-de.yaml` ->
`eu-single-language-base.yaml` -> `us-single-language-base.yaml`. Nothing
annotates a key before reassigning it; being in the upper layer is the
declaration.

The layout plane has the common half already: `data/layout_params.csv` is the
common style definition, all 1047 of its keys resolve in every target across
both product categories, and the paragraph style table renders to one
identical digest across all 14 (target, language) combinations.

What it lacked was the override half. Collisions were banned outright, so a
category or target had no legal way to say "this book genuinely differs" -- and
the difference did not vanish, it moved into key names. Measured across the two
live overlays, 46 keys are renamed shadows of a common key: 21 carrying a
`compact_` category infix, 12 carrying `lang_ko_` while changing panel heights
and column widths rather than any font metric.

So binding an overlay to a target is now the inheritance declaration, and a key
the overlay defines wins. Non-silence comes from the audit trail plus the
ratchet below -- the same guard shape this repo already uses for SKIP counts,
warnings, file sizes and language literals.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.render_contract import (
    load_layout_token_layers,
    resolve_layout_token_layers,
)

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "data/layout_params.csv"
COMPACT = ROOT / "data/layout_params.idml-compact.csv"
KR = ROOT / "data/layout_params.idml-je3000c-kr.csv"

HEADER = "key,value,unit,comment\n"

# Every common value a bound overlay currently replaces. Empty today: the 46
# shadow keys still carry scope infixes instead of overriding under their own
# name. Migrating them lands here, one line per override, which is what makes
# the migration reviewable -- and what makes an unintended one impossible to
# slip in. Update deliberately, never to make a build pass.
PINNED_OVERRIDES: dict[str, tuple[str, ...]] = {
    "layout_params.idml-compact.csv": (),
    "layout_params.idml-je3000c-kr.csv": (),
}


def write(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(HEADER + body, encoding="utf-8")
    return path


class AnUpperLayerWins(unittest.TestCase):
    """No per-row ceremony, exactly as `zh_CN_conf.py` reassigns `project`."""

    def setUp(self) -> None:
        self.dir = TemporaryDirectory()
        d = Path(self.dir.name)
        self.base = write(
            d, "common.csv",
            "type_body_font_size,6.0,pt,common\n"
            "comp_panel_height,54.0,mm,common\n",
        )
        self.overlay = write(
            d, "layer.csv",
            "type_body_font_size,5.6,pt,German runs long\n"
            "comp_extra_only_here,3.0,pt,a genuinely new token\n",
        )

    def tearDown(self) -> None:
        self.dir.cleanup()

    def test_a_redefined_key_takes_the_upper_layers_value(self) -> None:
        tokens = load_layout_token_layers(self.base, (self.overlay,))
        self.assertEqual("5.6", tokens["type_body_font_size"].value)

    def test_an_untouched_common_key_is_inherited(self) -> None:
        tokens = load_layout_token_layers(self.base, (self.overlay,))
        self.assertEqual("54.0", tokens["comp_panel_height"].value)

    def test_a_new_key_is_added(self) -> None:
        tokens = load_layout_token_layers(self.base, (self.overlay,))
        self.assertEqual("3.0", tokens["comp_extra_only_here"].value)

    def test_later_layers_win_over_earlier_ones(self) -> None:
        d = Path(self.dir.name)
        higher = write(d, "higher.csv", "type_body_font_size,5.0,pt,tighter still\n")
        tokens = load_layout_token_layers(self.base, (self.overlay, higher))
        self.assertEqual("5.0", tokens["type_body_font_size"].value)


class EveryOverrideIsReported(unittest.TestCase):
    """The audit trail is what replaced the ban: visible, not forbidden."""

    def setUp(self) -> None:
        self.dir = TemporaryDirectory()
        d = Path(self.dir.name)
        self.base = write(d, "common.csv", "type_body_font_size,6.0,pt,common\n")
        self.overlay = write(
            d, "layer.csv",
            "type_body_font_size,5.6,pt,German runs long\n"
            "comp_extra_only_here,3.0,pt,new token\n",
        )

    def tearDown(self) -> None:
        self.dir.cleanup()

    def test_it_carries_the_value_that_was_replaced(self) -> None:
        _tokens, applied = resolve_layout_token_layers(self.base, (self.overlay,))
        self.assertEqual(1, len(applied))
        entry = applied[0]
        self.assertEqual("type_body_font_size", entry.key)
        self.assertEqual("layer.csv", entry.overlay)
        self.assertEqual("6.0", entry.base_value)
        self.assertEqual("5.6", entry.value)
        self.assertEqual("German runs long", entry.comment)

    def test_an_addition_is_not_an_override(self) -> None:
        _tokens, applied = resolve_layout_token_layers(self.base, (self.overlay,))
        self.assertNotIn("comp_extra_only_here", [entry.key for entry in applied])

    def test_each_layer_is_attributed_separately(self) -> None:
        d = Path(self.dir.name)
        higher = write(d, "higher.csv", "type_body_font_size,5.0,pt,tighter still\n")
        _tokens, applied = resolve_layout_token_layers(self.base, (self.overlay, higher))
        self.assertEqual(["layer.csv", "higher.csv"], [e.overlay for e in applied])
        self.assertEqual(["6.0", "5.6"], [e.base_value for e in applied])


class TheOverrideSetIsRatcheted(unittest.TestCase):
    """A new override must be written down here, so review sees it."""

    def test_the_live_overlays_match_the_pin(self) -> None:
        for overlay in (COMPACT, KR):
            with self.subTest(overlay=overlay.name):
                _tokens, applied = resolve_layout_token_layers(COMMON, (overlay,))
                self.assertEqual(
                    list(PINNED_OVERRIDES[overlay.name]),
                    sorted(entry.key for entry in applied),
                    "an overlay now overrides a common value that the pin above "
                    "does not list; add it deliberately, with the reason",
                )

    def test_the_pin_would_catch_a_new_override(self) -> None:
        """A gate that cannot fail is not a gate."""
        with TemporaryDirectory() as td:
            d = Path(td)
            base = write(d, "common.csv", "type_body_font_size,6.0,pt,common\n")
            overlay = write(d, "layer.csv", "type_body_font_size,5.6,pt,new\n")
            _tokens, applied = resolve_layout_token_layers(base, (overlay,))
        self.assertEqual(["type_body_font_size"], [entry.key for entry in applied])


class TheCommonIsStillFullyInherited(unittest.TestCase):
    def test_every_common_key_resolves_for_every_target(self) -> None:
        common = load_layout_token_layers(COMMON)
        for overlay in ((), (COMPACT,), (KR,)):
            with self.subTest(overlay=[p.name for p in overlay] or "none"):
                resolved = load_layout_token_layers(COMMON, overlay)
                self.assertEqual([], sorted(set(common) - set(resolved)))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
