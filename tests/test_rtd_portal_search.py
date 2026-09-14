"""Regression coverage for section links and visible-body search extraction."""
import unittest

from tools.rtd_portal_search import ManualSections


class SearchSectionsTest(unittest.TestCase):
    def test_visible_text_tables_and_real_section_anchors(self):
        parser = ManualSections()
        parser.feed('''<nav>Outside navigation</nav><main><article>
        <section id="charging"><h1>Charging<a class="headerlink">¶</a></h1>
        <p>Use the AC cable.</p><table><tr><td>Input</td><td>100V</td></tr></table>
        <section id="solar"><h2>Solar</h2><p>Connect panels.</p></section>
        </section><nav>Feedback menu</nav><script>secret()</script></article></main>''')
        parser.flush()
        self.assertEqual([row['anchor'] for row in parser.rows], ['charging', 'solar'])
        self.assertEqual(parser.rows[0]['title'], 'Charging')
        self.assertIn('Input 100V', parser.rows[0]['text'])
        self.assertNotIn('Connect panels', parser.rows[0]['text'])
        self.assertEqual(parser.rows[1]['text'], 'Connect panels.')

    def test_image_alt_is_not_claimed_as_indexed_illustration_text(self):
        parser = ManualSections()
        parser.feed('<main><section id="display"><h2>Display</h2><img alt="unverified OCR"><p>Charging indicator</p></section></main>')
        parser.flush()
        self.assertEqual(parser.rows[0]['text'], 'Charging indicator')
