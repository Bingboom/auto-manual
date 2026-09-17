"""Author plane vs staged plane for ``build.py web-sideload``.

The defect these cover: a sideloaded book whose components were hand-written
as raw HTML shipped as an unstyled shell, because hand-written markup cannot
reproduce the structure the stylesheet keys off. The fix makes the semantic
directive layer the only source of component markup, so these tests pin both
directions -- a directive-authored bundle compiles into real component
markup, and a hand-written one is refused.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.manual_md_directives import DIRECTIVES
from tools.web_sideload_expand import (
    SideloadExpansionError,
    expand_sideload_bundle,
    lint_author_markdown,
    scan_directive_blocks,
    verify_expanded_products,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

CONF_PY = """\
project = "Sideload Fixture"
html_title = project
source_suffix = {".md": "markdown"}
root_doc = "index"
master_doc = "index"
html_theme = "furo"
exclude_patterns = ["_build"]
language = "en"
"""

INDEX_MD = "# Fixture\n\n```{toctree}\n:maxdepth: 2\n\nmanual\n```\n"

# One of every component directive, so the expansion contract is pinned for
# the whole vocabulary rather than the one component a fix happened to touch.
AUTHOR_MD = """\
# Manual

```{callout} WARNING
Do not open the enclosure.

- bullets work here
```

```{spec-table} INPUT PORTS
1 × AC Input | Charge Mode: 100-120 V~ 60 Hz, 15 A max.
             | Bypass Mode^①^: 12 A max.
2 × DC8020 Ports | 11 V-16 V⎓8 A max.
```

```{troubleshooting} Fault table
:headers: Error Code | Corrective Measures

E01 | Cool the unit / Restart
E02 | Contact support
```

```{lcd-icons} LCD legend
① | ![battery](assets/batt.png) | Battery | Shows charge / Blinks when low
② | ![ac](assets/ac.png) | AC | Mains present
```

```{symbols} Safety symbols
![weee](assets/weee.png) | Dispose separately
![ce](assets/ce.png) | CE marked
```

```{lcd-mode} ![screen](assets/screen.png)
Standby | Press POWER | Wakes the display
        | Hold POWER | Powers off
```

```{comparison} Resumes | Does not resume
AC output | USB output
DC output |
```

```{manual-table} Key combos
:headers: Keys | Action

Hold POWER | Power on
           | Power off
```
"""


def _bundle(directory: Path, manual_text: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "conf.py").write_text(CONF_PY, encoding="utf-8")
    (directory / "index.md").write_text(INDEX_MD, encoding="utf-8")
    (directory / "manual.md").write_text(manual_text, encoding="utf-8")
    return directory


class AuthorPlaneLintTests(unittest.TestCase):
    """The negative control: hand-written component markup must be refused."""

    def test_hand_written_component_class_is_rejected(self) -> None:
        naked = (
            "# Manual\n\n"
            '<table class="manual-callout-table"><tbody><tr>'
            '<td class="manual-callout-label"><p><strong>WARNING</strong></p></td>'
            '<td class="manual-callout-body"><p>Do not open.</p></td>'
            "</tr></tbody></table>\n"
        )
        problems = lint_author_markdown(naked, label="manual.md")

        self.assertTrue(problems)
        joined = "\n".join(problems)
        self.assertIn("manual-callout-table", joined)
        # The error must route the author to the directive, not just complain.
        self.assertIn("{callout}", joined)

    def test_every_hb_component_family_is_rejected_with_its_owning_directive(self) -> None:
        for token, directive in (
            ("hb-spec-table-composition", "{spec-table}"),
            ("hb-troubleshooting-composition", "{troubleshooting}"),
            ("hb-lcd-icon-table", "{lcd-icons}"),
            ("hb-lcd-mode-composition", "{lcd-mode}"),
            ("hb-symbol-pair-composition", "{symbols}"),
            ("hb-auto-resume-table", "{comparison}"),
        ):
            with self.subTest(token=token):
                problems = lint_author_markdown(
                    f'<figure class="{token}">x</figure>', label="manual.md"
                )
                self.assertTrue(problems, f"{token} must be refused")
                self.assertIn(directive, "\n".join(problems))

    def test_inline_style_is_rejected(self) -> None:
        problems = lint_author_markdown(
            '<table style="width:100%; border-collapse:collapse;">x</table>',
            label="manual.md",
        )

        self.assertTrue(problems)
        self.assertIn("inline style", "\n".join(problems))

    def test_ordinary_prose_and_directives_pass(self) -> None:
        self.assertEqual([], lint_author_markdown(AUTHOR_MD, label="manual.md"))

    def test_lint_runs_before_any_build(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = _bundle(
                Path(tmp) / "md",
                '# Manual\n\n<table class="manual-callout-table">x</table>\n',
            )
            with self.assertRaises(SideloadExpansionError) as caught:
                expand_sideload_bundle(md_dir=md_dir, repo_root=REPO_ROOT)

        self.assertIn("author-plane lint failed", str(caught.exception))


class FenceScannerTests(unittest.TestCase):
    def test_only_component_directives_are_matched(self) -> None:
        text = (
            "# T\n\n"
            "```{toctree}\n:maxdepth: 2\n\nmanual\n```\n\n"
            "```python\nprint('hi')\n```\n\n"
            "```{callout} NOTE\nBody.\n```\n"
        )
        blocks = scan_directive_blocks(text)

        self.assertEqual(["callout"], [block.name for block in blocks])

    def test_all_three_fence_spellings(self) -> None:
        for fence, closer in (("```", "```"), ("~~~", "~~~"), (":::", ":::")):
            with self.subTest(fence=fence):
                text = f"# T\n\n{fence}{{callout}} NOTE\nBody.\n{closer}\n"
                blocks = scan_directive_blocks(text)
                self.assertEqual(1, len(blocks))
                self.assertEqual("callout", blocks[0].name)

    def test_nested_shorter_fence_does_not_close_the_block(self) -> None:
        # A callout body is full Markdown, so it may carry its own code
        # fence; MyST requires the outer fence to be longer, and the scanner
        # must read it the same way or it would truncate the block.
        text = (
            "# T\n\n"
            "````{callout} NOTE\n"
            "Run this:\n\n"
            "```bash\n"
            "echo hi\n"
            "```\n\n"
            "Done.\n"
            "````\n"
        )
        blocks = scan_directive_blocks(text)

        self.assertEqual(1, len(blocks))
        self.assertEqual(3, blocks[0].start_line)
        self.assertEqual(11, blocks[0].end_line)

    def test_unterminated_directive_fails_closed(self) -> None:
        with self.assertRaises(SideloadExpansionError) as caught:
            scan_directive_blocks("# T\n\n```{callout} NOTE\nBody.\n")

        self.assertIn("unterminated", str(caught.exception))

    def test_scanner_covers_the_whole_directive_vocabulary(self) -> None:
        # Guard against a directive being added to the layer without the
        # sideload lane learning about it.
        found = {block.name for block in scan_directive_blocks(AUTHOR_MD)}
        self.assertEqual(set(DIRECTIVES), found)


class ProductCheckTests(unittest.TestCase):
    def test_missing_component_markup_is_reported(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = _bundle(Path(tmp) / "md", "# Manual\n\nPlain prose only.\n")
            with self.assertRaises(SideloadExpansionError) as caught:
                verify_expanded_products(md_dir=md_dir, counts={"callout": 1})

        self.assertIn("manual-callout-table", str(caught.exception))


class ExpansionTests(unittest.TestCase):
    """Runs one real Sphinx build -- the contract is what Sphinx emits."""

    def test_every_directive_compiles_into_component_markup(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = _bundle(Path(tmp) / "md", AUTHOR_MD)
            counts = expand_sideload_bundle(md_dir=md_dir, repo_root=REPO_ROOT)
            verify_expanded_products(md_dir=md_dir, counts=counts)
            staged = (md_dir / "manual.md").read_text(encoding="utf-8")

        self.assertEqual({name: 1 for name in DIRECTIVES}, counts)
        # No directive survives into the staged plane: Read the Docs builds
        # with myst_parser + tools.rtd_portal only and would render every
        # remaining fence as an unknown-directive error.
        self.assertNotIn("```{", staged)
        for marker in (
            "manual-callout-table",
            "hb-spec-table-composition",
            "hb-troubleshooting-composition",
            "hb-lcd-table-composition",
            "hb-symbol-pair-composition",
            "hb-lcd-mode-composition",
            "hb-auto-resume-composition",
        ):
            self.assertIn(marker, staged)
        # Structure a pipe table cannot express, and which a hand-written
        # component reliably loses -- this is what "styled" actually rests on.
        self.assertIn('scope="row"', staged)
        self.assertIn("rowspan=", staged)
        self.assertIn('<col class="hb-spec-col-label"/>', staged)
        # The web adapter binds classes only (see component_specs.adapters:
        # web_callout_classes vs word_callout_markup, which is the plane that
        # carries inline styles), so the shared stylesheet owns the look.
        self.assertNotIn('style="', staged)
        # Internal sentinels must never reach a staged file.
        self.assertNotIn("AMX:", staged)

    def test_expansion_leaves_a_directive_free_bundle_alone(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = _bundle(Path(tmp) / "md", "# Manual\n\nJust prose.\n")
            before = (md_dir / "manual.md").read_text(encoding="utf-8")
            counts = expand_sideload_bundle(md_dir=md_dir, repo_root=REPO_ROOT)

            self.assertEqual({}, counts)
            self.assertEqual(before, (md_dir / "manual.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
