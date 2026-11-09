from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bs4 import BeautifulSoup

from tests import test_rtd_feedback
from tests.web_language_evidence_fixture import isolate_shared_component_admission
from tools.rtd.manual_chat import chat_endpoint, manual_chat_markup


class RtdManualChatTests(unittest.TestCase):
    def setUp(self) -> None:
        isolate_shared_component_admission(self)

    def test_opt_in_requires_a_plain_https_origin(self) -> None:
        self.assertEqual(chat_endpoint(""), "")
        self.assertEqual(chat_endpoint("https://ask.example/"), "https://ask.example")
        for value in ("http://ask.example", "https://u:p@ask.example", "https://ask.example?key=x",
                      "https://ask.example/#key", "https://ask.example/api/chat", "https://ask.example\n",
                      "https://ask.example\\evil", "https://ask.example:invalid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                chat_endpoint(value)

    def test_frozen_identity_is_escaped_and_no_secret_is_embedded(self) -> None:
        publication = {"model": 'JE-TEST"<', "region": "EU", "lang": "fr", "version": "1.2",
                       "url": "JE-TEST/EU/fr/md/manual.html"}
        markup = manual_chat_markup("https://ask.example", publication)
        page = BeautifulSoup(markup, "html.parser")
        chat = page.select_one(".manual-chat")
        self.assertEqual(chat["data-model"], publication["model"])
        self.assertEqual(chat["data-version"], "1.2")
        self.assertEqual(chat["data-page"], publication["url"])
        self.assertEqual(page.select_one("input")["type"], "password")
        self.assertNotIn("<script", markup)
        self.assertNotIn("Authorization", markup)
        self.assertEqual(manual_chat_markup("", publication), "")

    def test_real_sphinx_opt_in_has_context_and_assets_without_touching_source(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, _ = test_rtd_feedback.RtdFeedbackTests._fixture(root, channels=[], include_legacy=True)
            original = (source / "JE-TEST/EU/fr/md/manual.md").read_bytes()
            with patch.dict(os.environ, {"HT_DOCS_CHAT_URL": "https://ask.example"}):
                output = test_rtd_feedback.RtdFeedbackTests._build(source, root / "enabled")
            page = BeautifulSoup((output / "JE-TEST/EU/fr/md/manual.html").read_text(), "html.parser")
            self.assertEqual(page.select_one(".manual-chat")["data-version"], "1.2")
            self.assertEqual(page.select_one(".manual-chat")["data-language"], "fr")
            self.assertTrue(page.select_one('script[src*="manual-chat.js"]'))
            self.assertTrue((output / "_static/manual-chat.css").is_file())
            self.assertNotIn('class="manual-chat"', (output / "JE-TEST/EU/md/manual_legacy.html").read_text())
            self.assertNotIn('class="manual-chat"', (output / "index.html").read_text())
            self.assertEqual((source / "JE-TEST/EU/fr/md/manual.md").read_bytes(), original)

    def test_real_sphinx_default_does_not_offer_an_unconfigured_service(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, _ = test_rtd_feedback.RtdFeedbackTests._fixture(root, channels=[])
            with patch.dict(os.environ, {"HT_DOCS_CHAT_URL": ""}):
                output = test_rtd_feedback.RtdFeedbackTests._build(source, root / "disabled")
            page = (output / "JE-TEST/EU/fr/md/manual.html").read_text()
            self.assertNotIn('class="manual-chat"', page)
            self.assertNotIn("manual-chat.js", page)
