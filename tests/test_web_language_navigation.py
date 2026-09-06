from __future__ import annotations

from types import SimpleNamespace
import unittest

from bs4 import BeautifulSoup

from tools.web_language_navigation import (
    WebLanguageNavigationError,
    add_web_language_navigation,
    protect_web_language_navigation_for_pandoc,
    restore_web_language_navigation_after_pandoc,
)


class WebLanguageNavigationTests(unittest.TestCase):
    def _ir(self, declared: tuple[str, ...], pages: tuple[str, ...]) -> SimpleNamespace:
        return SimpleNamespace(
            metadata={"declared_languages": list(declared)},
            pages=tuple(SimpleNamespace(language=language) for language in pages),
        )

    def test_multilingual_document_gets_native_links_and_stable_boundaries(self) -> None:
        languages = ("en", "fr", "es", "de", "it")
        fragments = (
            "<p>English / French / Spanish / German / Italian</p><p>IMPORTANT</p>",
            "<h1>English safety</h1>",
            "<h1>Sécurité</h1>",
            "<h1>Seguridad</h1>",
            "<h1>Sicherheit</h1>",
            "<h1>Sicurezza</h1>",
        )
        result = add_web_language_navigation(
            self._ir(languages, ("en", "en", "fr", "es", "de", "it")),
            fragments,
        )

        combined = BeautifulSoup("".join(result), "html.parser")
        nav = combined.select_one("nav.hb-language-nav")
        self.assertIsNotNone(nav)
        self.assertEqual(
            "English / Français / Español / Deutsch / Italiano",
            nav["aria-label"],
        )
        links = nav.select("a.hb-language-link")
        self.assertEqual(
            ["English", "Français", "Español", "Deutsch", "Italiano"],
            [link.get_text(strip=True) for link in links],
        )
        self.assertEqual(
            ["#hb-lang-en", "#hb-lang-fr", "#hb-lang-es", "#hb-lang-de", "#hb-lang-it"],
            [link["href"] for link in links],
        )
        self.assertEqual(list(languages), [link["lang"] for link in links])
        self.assertEqual(list(languages), [link["hreflang"] for link in links])
        self.assertEqual(
            ["hb-lang-en", "hb-lang-fr", "hb-lang-es", "hb-lang-de", "hb-lang-it"],
            [anchor["id"] for anchor in combined.select("span.hb-language-anchor")],
        )
        self.assertNotIn(
            "English / French / Spanish / German / Italian",
            combined.get_text(" ", strip=True),
        )
        self.assertEqual(1, result[0].count('id="hb-lang-en"'))
        self.assertEqual(1, result[2].count('id="hb-lang-fr"'))

    def test_single_language_document_stays_byte_identical(self) -> None:
        fragments = ("<h1>Manual</h1>",)
        self.assertEqual(
            fragments,
            add_web_language_navigation(self._ir(("en",), ("en",)), fragments),
        )

    def test_declared_language_without_page_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            WebLanguageNavigationError,
            "no page boundary for: fr",
        ):
            add_web_language_navigation(
                self._ir(("en", "fr"), ("en",)),
                ("<h1>Manual</h1>",),
            )

    def test_duplicate_declared_language_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            WebLanguageNavigationError,
            "repeats declared language: en",
        ):
            add_web_language_navigation(
                self._ir(("en", "en"), ("en",)),
                ("<h1>Manual</h1>",),
            )

    def test_page_language_outside_declared_scope_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            WebLanguageNavigationError,
            "page language 'es' is not declared",
        ):
            add_web_language_navigation(
                self._ir(("en", "fr"), ("en", "es")),
                ("<h1>English</h1>", "<h1>Español</h1>"),
            )

    def test_pandoc_boundary_restores_every_nav_node_exactly_once(self) -> None:
        html = "".join(
            add_web_language_navigation(
                self._ir(("en", "fr"), ("en", "fr")),
                ("<p>English / French</p><h1>English</h1>", "<h1>Français</h1>"),
            )
        )
        protected_html, protected = protect_web_language_navigation_for_pandoc(html)

        self.assertEqual(3, len(protected))
        self.assertNotIn("hb-language-nav", protected_html)
        pandoc_output = "\n\n".join(protected)
        restored = restore_web_language_navigation_after_pandoc(
            pandoc_output,
            protected,
        )
        soup = BeautifulSoup(restored, "html.parser")
        self.assertEqual(1, len(soup.select("nav.hb-language-nav")))
        self.assertEqual(2, len(soup.select("span.hb-language-anchor")))
        self.assertNotIn("AUTOMANUALWEBLANGUAGE", restored)
        first_token = next(iter(protected))
        with self.assertRaisesRegex(WebLanguageNavigationError, "occurred 0 times"):
            restore_web_language_navigation_after_pandoc(
                pandoc_output.replace(first_token, ""),
                protected,
            )


if __name__ == "__main__":
    unittest.main()
