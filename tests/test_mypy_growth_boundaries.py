"""Regression contracts for the two approved mypy-growth boundary fixes."""
from collections.abc import Iterator, Mapping
from pathlib import Path
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup, Tag

from tools.component_specs.app_label_source import normalize_control_labels
from tools.manual_ir import whole_document_components as components


class RecordingMapping(Mapping[str, object]):
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values
        self.reads: list[str] = []

    def __getitem__(self, key: str) -> object:
        self.reads.append(key)
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)


class NonMapping:
    def get(self, *args: object) -> object:
        raise AssertionError("non-Mapping.get must not be called")


class MypyGrowthBoundaryTests(unittest.TestCase):
    def labels(self, suffix: str) -> tuple[BeautifulSoup, Tag, Tag]:
        soup = BeautifulSoup('<img src="phone.png"><img src="control.png">' + suffix, "html.parser")
        phone, control = soup.find_all("img")
        return soup, phone, control

    def discover(self, config: object, supports: bool) -> tuple[components.ComponentClaim, ...]:
        contract: dict[str, object] = {key: {} for key in (
            "meaning_symbols", "warranty", "operations", "reference_figures",
            "app_inline_controls", "product_overview", "fcc", "in_the_box",
        )}
        contract["app_download"] = config
        with patch.object(components, "supports_figure_contract", return_value=supports):
            return components.discover_registered_components(
                BeautifulSoup("<p>Unmatched text</p>", "html.parser"),
                source_path=Path("chapter.rst"), contract=contract,
                model="test-model", region="EU", language="en",
            )

    def test_none_class_uses_existing_validation_without_mutation(self) -> None:
        soup, phone, _ = self.labels("<div>Not three labels</div>")
        soup.div["class"] = None
        before = str(soup)
        with self.assertRaisesRegex(ValueError, "requires three nonempty label paragraphs"):
            normalize_control_labels(soup, phone, "control.png")
        self.assertEqual(str(soup), before)

    def test_existing_line_block_is_preserved(self) -> None:
        soup, phone, control = self.labels('<div class="line-block"><div class="line">Label</div></div>')
        before = str(soup)
        self.assertIs(normalize_control_labels(soup, phone, "control.png"), control)
        self.assertEqual(str(soup), before)

    def test_three_authored_labels_keep_order_and_inline_markup(self) -> None:
        soup, phone, control = self.labels("<p>One <b>bold</b></p><p>Two</p><p>Three</p><p>Tail</p>")
        self.assertIs(normalize_control_labels(soup, phone, "control.png"), control)
        self.assertEqual([node.decode_contents() for node in soup.select(".line-block > .line")],
                         ["One <b>bold</b>", "Two", "Three"])
        self.assertEqual(soup.select_one(".line-block").find_next_sibling().get_text(), "Tail")

    def test_non_mapping_download_is_skipped_for_both_figure_policies(self) -> None:
        for config in (None, [], "invalid", 3):
            for supports in (False, True):
                with self.subTest(config=config, supports=supports):
                    self.assertEqual(self.discover(config, supports), ())

    def test_mapping_without_matching_source_is_skipped(self) -> None:
        with patch.object(components, "parse_app_download_html") as parse:
            for supports in (False, True):
                self.assertEqual(self.discover({"presentation": "qr-only", "source_patterns": ["other"]}, supports), ())
            parse.assert_not_called()

    def test_valid_download_dispatch_keeps_qr_only_and_figures(self) -> None:
        for supports, presentation in [(False, "qr-only"), (True, "illustrated")]:
            config = {"presentation": presentation, "source_patterns": ["chapter"]}
            with self.subTest(supports=supports), patch.object(
                components, "parse_app_download_html", side_effect=RuntimeError("parser reached"),
            ) as parse:
                with self.assertRaisesRegex(RuntimeError, "parser reached"):
                    self.discover(config, supports)
                self.assertIs(parse.call_args.kwargs["config"], config)

    def test_non_mapping_get_is_never_called(self) -> None:
        for supports in (False, True):
            with self.subTest(supports=supports):
                self.assertEqual(self.discover(NonMapping(), supports), ())

    def test_download_mapping_read_order_preserves_short_circuit(self) -> None:
        for supports, values, expected, parsed in [
            (True, {"source_patterns": ["chapter"]}, ["source_patterns"], True),
            (False, {"presentation": "illustrated"}, ["presentation"], False),
            (False, {"presentation": "qr-only", "source_patterns": ["chapter"]},
             ["presentation", "source_patterns"], True),
        ]:
            config = RecordingMapping(values)
            with self.subTest(supports=supports, values=values), patch.object(
                components, "parse_app_download_html", side_effect=RuntimeError("parser reached"),
            ):
                if parsed:
                    with self.assertRaisesRegex(RuntimeError, "parser reached"):
                        self.discover(config, supports)
                else:
                    self.assertEqual(self.discover(config, supports), ())
                self.assertEqual(config.reads, expected)


if __name__ == "__main__":
    unittest.main()
