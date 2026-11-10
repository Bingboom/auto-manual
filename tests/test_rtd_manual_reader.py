"""The reading frame around a verified single-language manual (tools/rtd/manual_reader.py, manual_reader.html)."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

# The feedback tests' fixture builds a verified page; import the module so its tests do not run twice here.
from tests import test_rtd_feedback
from tools.rtd.manual_reader import chapters, frame_text, load_text, locale_options, reader_context, version_date
from tools.rtd.portal import ASSETS

MANUAL = """# SAFETY

Read this first.

# CHARGING

## Via AC wall outlet

Plug it in.

## Via solar panels

Connect the panels.

# SPECIFICATIONS

The values.
"""


def section(anchor: str, rank: int, name: str, inner: str = "<p>Text.</p>") -> str:
    """A section as Sphinx renders it: its title heading with the permalink, then its content."""
    return (f'<section id="{anchor}">\n<h{rank}>{name}<a class="headerlink" href="#{anchor}" '
            f'title="Link to this heading">¶</a></h{rank}>\n{inner}\n</section>')


class Sections(HTMLParser):
    """Section ids inside the manual's main region, and where the frame's parts sit."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.depth = 0
        self.mains = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "main" or values.get("role") == "main":
            self.mains += 1
        if tag == "section" and values.get("id"):
            self.ids.append(values["id"])


class ChapterTests(unittest.TestCase):
    """The chapter list is read from the rendered body, so every entry links to an id the page has."""

    def test_top_sections_are_chapters_with_their_subsections(self):
        body = section("safety", 1, "Safety") + section(
            "charging", 1, "Charging", section("ac", 2, "AC") + section("solar", 2, "Solar", section("panel", 3, "Panel")))
        self.assertEqual(chapters(body), [
            {"id": "safety", "title": "Safety", "subs": []},
            {"id": "charging", "title": "Charging", "subs": [{"id": "ac", "title": "AC"}, {"id": "solar", "title": "Solar"}]},
        ])

    def test_a_single_title_section_lists_its_entries(self):
        body = section("manual", 1, "Explorer manual", section("safety", 2, "Safety") + section("charging", 2, "Charging"))
        self.assertEqual([chapter["title"] for chapter in chapters(body)], ["Safety", "Charging"])

    def test_raw_html_headings_with_their_own_ids_are_entries(self):
        # A raw-HTML manual: one title section whose chapters are <h2 id> headings, not sections.
        body = section("manual", 1, "Explorer 2000 Pro User Manual", (
            '<h2 class="docutils" id="native-specs">TECHNICAL SPECIFICATIONS</h2><h3 class="docutils">CERTIFICATIONS:</h3>'
            '<h2 class="docutils" id="native-charging">CHARGING</h2><h3 id="native-solar">From solar</h3>'
            '<h4 id="native-example">Example 1</h4><h2 class="docutils" id="native-faq">FAQ</h2>'))
        self.assertEqual(chapters(body), [
            {"id": "native-specs", "title": "TECHNICAL SPECIFICATIONS", "subs": []},
            {"id": "native-charging", "title": "CHARGING", "subs": [{"id": "native-solar", "title": "From solar"}]},
            {"id": "native-faq", "title": "FAQ", "subs": []},
        ])

    def test_a_name_leaves_out_the_permalink_and_the_model_label(self):
        body = (section("a", 1, 'Explorer 3000<span class="docutils" data-source-layout="model">Model: JE-3000B</span>')
                + section("b", 1, '<span class="hb-heading-title">SPECIFICATIONS</span> '
                                  '<span class="hb-heading-model">Model: <span>JHP-3600C</span></span>')
                + section("c", 1, "Charging &amp;<br>storage\n  tips"))
        self.assertEqual([chapter["title"] for chapter in chapters(body)],
                         ["Explorer 3000", "SPECIFICATIONS", "Charging & storage tips"])

    def test_unlisted_sections_hand_their_entries_up_and_page_furniture_is_skipped(self):
        body = ('<section><h1>No id</h1>' + section("x", 2, "X") + '</section>'
                + '<section id="blank">' + section("y", 2, "Y") + '</section></section>'
                + '<div class="product-voc"><h2 id="product-voc-title">How can we improve?</h2></div>'
                + '<section id="z"><h1>Z</h1>')  # left open by raw HTML
        self.assertEqual([chapter["id"] for chapter in chapters(body)], ["x", "y", "z"])

    def test_fewer_than_two_chapters_list_none(self):
        self.assertEqual(chapters(section("guide", 1, "Guide")), [])
        self.assertEqual(chapters("<p>Just a paragraph.</p>"), [])
        self.assertEqual(chapters(""), [])

    def test_version_date(self):
        self.assertEqual(version_date("git-20261027-36f9aa96-battery-symbol"), "2026-10-27")
        self.assertIsNone(version_date("1.2"))
        self.assertIsNone(version_date(""))

    def test_locale_options_select_the_current_publication(self):
        product = {"language_options": [{"url": "A/EU/en/md/manual_en.html", "display": "en-US"},
                                        {"url": "A/EU/fr/md/manual_fr.html", "display": "fr-FR"}]}
        pathto = {"A/EU/en/md/manual_en": "#", "A/EU/fr/md/manual_fr": "../../fr/md/manual_fr.html"}.get
        options = locale_options(product, {"url": "A/EU/en/md/manual_en.html"}, pathto)
        self.assertEqual(options, [{"url": "manual_en.html", "display": "en-US", "selected": True},
                                   {"url": "../../fr/md/manual_fr.html", "display": "fr-FR", "selected": False}])

    def test_reader_context_carries_the_frame(self):
        context = reader_context(
            product={"name": "Explorer Test"}, active={"model": "JE-TEST", "region": "EU", "lang": "ar",
                                                       "version": "git-20261027-36f9aa96"},
            lang_label="العربية", direction="rtl", options=[], body="", text=frame_text(load_text(ASSETS), "ar"),
            feedback="", library="../index.html", search="../search.html")
        self.assertEqual((context["version_date"], context["dir"], context["chapters"]), ("2026-10-27", "rtl", []))
        self.assertEqual((context["ui_lang"], context["text"]["contents"]), ("en", "Contents"))


class FrameTextTests(unittest.TestCase):
    """The frame's words follow the manual's language (manual_reader_text.yaml)."""

    def test_each_language_gives_every_word(self):
        table = load_text(ASSETS)
        self.assertTrue({"en", "zh", "zh-TW", "ja", "ko", "de", "fr", "es", "it", "pt", "nl", "pl", "uk"} <= set(table))
        self.assertEqual(frame_text(table, "ja")[1]["contents"], "目次")
        self.assertEqual(frame_text(table, "zh")[1]["contents"], "目录")

    def test_a_language_without_words_reads_in_english(self):
        self.assertEqual(frame_text(load_text(ASSETS), "he"), ("en", load_text(ASSETS)["en"]))

    def test_the_chapter_count_reads_in_the_frames_language(self):
        body = section("a", 1, "A") + section("b", 1, "B")
        for lang, count in (("en", "2 chapters"), ("ja", "全2章"), ("pl", "Rozdziały: 2")):
            with self.subTest(lang=lang):
                context = reader_context(
                    product={}, active={"model": "JE-TEST", "region": "EU", "lang": lang}, lang_label=lang,
                    direction="ltr", options=[], body=body, text=frame_text(load_text(ASSETS), lang), feedback="",
                    library="", search="")
                self.assertEqual(context["count"], count)

    def test_a_set_missing_a_word_or_a_placeholder_is_refused(self):
        for broken in ("en: {contents: Contents, chapters: '{n} chapters', email: 'Email {address}'}\n"
                       "fr: {contents: Sommaire, chapters: '{n} chapitres'}\n",
                       "en: {contents: Contents, chapters: '{n} chapters', email: 'Email {address}'}\n"
                       "fr: {contents: Sommaire, chapters: chapitres, email: 'Écrire à {address}'}\n"):
            with self.subTest(broken=broken), TemporaryDirectory() as temp:
                (Path(temp) / "manual_reader_text.yaml").write_text(broken, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "fr"):
                    load_text(Path(temp))


class ReaderPageTests(unittest.TestCase):
    """A real Sphinx build: the frame around a verified page, the legacy page untouched."""

    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        root = Path(cls.temp.name)
        # Synthetic sources, as in tests/web_language_evidence_fixture.isolate_shared_component_admission.
        with patch("tools.web.language_release_evidence.require_fresh_component_admission"), \
                patch("tools.web.frozen_source_evidence.require_fresh_component_admission"):
            source, _ = test_rtd_feedback.RtdFeedbackTests._fixture(
                root, channels=[{"label": "Email support", "url": "mailto:hello@example.test"}],
                include_legacy=True, markdown=MANUAL)
        output = test_rtd_feedback.RtdFeedbackTests._build(source, root / "html")
        cls.page = (output / "JE-TEST/EU/fr/md/manual.html").read_text(encoding="utf-8")
        cls.legacy = (output / "JE-TEST/EU/md/manual_legacy.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_the_top_bar_names_the_manual_and_keeps_the_language_select(self):
        page = self.page
        top = page[page.index('<header class="mr-top"'):page.index("</header>")]
        self.assertIn('<span class="mr-tag">EU</span>', top)
        self.assertIn('<span class="mr-tag">Français</span>', top)
        self.assertIn('href="../../../../index.html"', top)
        self.assertIn('href="../../../../search.html"', top)
        self.assertIn('<select id="manual-locale-select" data-manual-locale>', top)
        self.assertIn('id="manual-locale-select-narrow"', page)
        self.assertNotIn('class="mr-ver"', top)  # 1.2 is not a dated Git version
        self.assertIn("<span>Version <code>1.2</code></span>", page)
        self.assertIn('document.body.dataset.theme = "light"', page)
        self.assertIn("manual-reader.js", page)
        self.assertIn("manual-reader.css", page)
        self.assertNotIn("manual-locale-nav", page)

    def test_the_frame_speaks_the_manuals_language(self):
        page = self.page
        self.assertIn('<div class="mr has-toc" lang="fr">', page)
        self.assertIn('<a class="mr-skip" href="#furo-main-content" lang="fr">Aller au manuel</a>', page)
        self.assertIn('aria-label="Retour à la bibliothèque des manuels"', page)
        self.assertIn("<span>Rechercher dans les manuels</span>", page)
        self.assertIn('aria-expanded="false">', page)
        self.assertIn("Sommaire</button>", page)
        self.assertIn("<span>Bibliothèque des manuels · French JE-TEST · EU · Français</span>", page)
        self.assertIn(">Écrire à hello@example.test</a>", page)
        frame = page[page.index("<body>"):]
        self.assertNotIn("目录", frame)
        self.assertNotIn("说明书资料库", frame)

    def test_the_chapter_list_points_at_the_manuals_sections(self):
        page = self.page
        toc = page[page.index('<nav class="mr-toc"'):page.index("</nav>", page.index('<nav class="mr-toc"'))]
        self.assertIn('lang="fr" dir="ltr"', toc)
        self.assertEqual(toc.count('class="mr-chapter"'), 3)
        self.assertIn('<span>3 chapitres</span>', toc)
        article = page[page.index('<article role="main" id="furo-main-content">'):page.index("</article>")]
        sections = Sections()
        sections.feed(article)
        for target in ("safety", "charging", "via-ac-wall-outlet", "via-solar-panels", "specifications"):
            with self.subTest(section=target):
                self.assertIn(f'href="#{target}"', toc)
                self.assertIn(target, sections.ids)

    def test_the_manual_stays_the_only_main_region_and_feedback_sits_under_it(self):
        page = self.page
        whole = Sections()
        whole.feed(page)
        self.assertEqual(whole.mains, 1)
        self.assertIn('<div lang="fr" dir="ltr">', page)
        self.assertGreater(page.index('<aside class="manual-feedback"'), page.index("</article>"))
        self.assertIn('<details class="manual-feedback-details"><summary>Afficher les informations</summary>', page)
        self.assertIn('href="mailto:hello@example.test"', page)

    def test_a_legacy_page_keeps_the_theme(self):
        self.assertNotIn("mr-top", self.legacy)
        self.assertNotIn("manual-reader", self.legacy)
        self.assertIn("furo-main-content", self.legacy)


if __name__ == "__main__":
    unittest.main()
