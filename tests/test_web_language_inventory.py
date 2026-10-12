from __future__ import annotations

from types import SimpleNamespace
import unittest

from bs4 import BeautifulSoup

from tools.web.language_inventory import (
    WebLanguageInventoryError,
    strip_web_language_inventory,
)


class WebLanguageInventoryTests(unittest.TestCase):
    def _ir(self, declared: tuple[str, ...], pages: tuple[str, ...]) -> SimpleNamespace:
        return SimpleNamespace(
            metadata={"declared_languages": list(declared)},
            pages=tuple(SimpleNamespace(language=language) for language in pages),
        )

    def test_multilingual_document_drops_inventory_without_language_bar(self) -> None:
        languages = ("en", "fr", "es", "de", "it")
        fragments = (
            "<p>English / French / Spanish / German / Italian</p><p>IMPORTANT</p>",
            "<h1>English safety</h1>",
            "<h1>Sécurité</h1>",
            "<h1>Seguridad</h1>",
            "<h1>Sicherheit</h1>",
            "<h1>Sicurezza</h1>",
        )
        result = strip_web_language_inventory(
            self._ir(languages, ("en", "en", "fr", "es", "de", "it")),
            fragments,
        )

        combined = BeautifulSoup("".join(result), "html.parser")
        self.assertIsNone(combined.select_one("nav"))
        self.assertEqual([], combined.select("[id^='hb-lang-']"))
        self.assertNotIn("hb-language", "".join(result))
        self.assertNotIn(
            "English / French / Spanish / German / Italian",
            combined.get_text(" ", strip=True),
        )
        self.assertEqual("<p>IMPORTANT</p>", result[0])
        self.assertEqual(fragments[1:], result[1:])

    def test_native_name_inventory_is_dropped_too(self) -> None:
        result = strip_web_language_inventory(
            self._ir(("en", "fr"), ("en", "fr")),
            ("<p>English / Français</p><h1>English</h1>", "<h1>Français</h1>"),
        )
        self.assertEqual(("<h1>English</h1>", "<h1>Français</h1>"), result)

    def test_single_language_document_stays_byte_identical(self) -> None:
        fragments = ("<h1>Manual</h1>",)
        self.assertEqual(
            fragments,
            strip_web_language_inventory(self._ir(("en",), ("en",)), fragments),
        )

    def test_declared_language_without_page_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            WebLanguageInventoryError,
            "no page for declared language: fr",
        ):
            strip_web_language_inventory(
                self._ir(("en", "fr"), ("en",)),
                ("<h1>Manual</h1>",),
            )

    def test_duplicate_declared_language_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            WebLanguageInventoryError,
            "repeats declared language: en",
        ):
            strip_web_language_inventory(
                self._ir(("en", "en"), ("en",)),
                ("<h1>Manual</h1>",),
            )

    def test_page_language_outside_declared_scope_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            WebLanguageInventoryError,
            "page language 'es' is not declared",
        ):
            strip_web_language_inventory(
                self._ir(("en", "fr"), ("en", "es")),
                ("<h1>English</h1>", "<h1>Español</h1>"),
            )


if __name__ == "__main__":
    unittest.main()
