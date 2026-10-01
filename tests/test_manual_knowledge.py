"""Safety and semantic preservation at the rendered-manual query boundary."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.manual_knowledge.export import ARTIFACT, make_corpus, write_knowledge
from tools.manual_knowledge.html import extract_sections
from tools.rtd_deployment_receipt import write_deployment_receipt
from tools.rtd_portal import setup


def extract(body):
    return extract_sections('<article role="main">' + body + '</article>', url='MODEL/EU/en/md/manual.html')


class SemanticManualTests(unittest.TestCase):
    def test_inline_spans_do_not_split_numbers_units_or_sentences(self):
        sections, _ = extract('<p><strong>On:</strong> Press for <span>3</span> seconds.<br/>Then release.</p>')
        self.assertEqual(sections[0]['blocks'][0]['text'], 'On: Press for 3 seconds.\nThen release.')

    def test_reversed_and_explicit_list_numbers_are_preserved(self):
        sections, _ = extract('<ol reversed><li>A</li><li value="5">B</li><li>C</li></ol>')
        self.assertEqual(sections[0]['blocks'][0]['text'], '3. A\n5. B\n4. C')

    def test_embedded_warning_and_table_lists_preserve_step_numbers(self):
        sections, _ = extract('''<div class="admonition"><p class="admonition-title">Warning</p>
        <ol start="2"><li><p>Disconnect.</p></li><li>Wait.</li></ol></div>
        <table><tr><td><ol><li>Off.</li><li>On.</li></ol></td><td><img alt="USB-C"/></td></tr></table>''')
        self.assertIn('2. Disconnect.\n3. Wait.', sections[0]['blocks'][0]['body'])
        self.assertIn('1. Off.\n2. On.', sections[0]['blocks'][1]['grid'][0][0])
        self.assertEqual(sections[0]['blocks'][1]['rows'][0][1]['image_text_coverage'], 'alt_only_no_ocr')
        with self.assertRaisesRegex(ValueError, 'Nested'):
            extract('<table><tr><td><table><tr><td>X</td></tr></table></td></tr></table>')

    def test_table_spans_bind_each_value_to_its_label(self):
        sections, _ = extract('''<section id="specs"><h1>Specifications</h1>
        <table><tr><th>Port</th><th>Voltage</th><th>Current</th></tr>
        <tr><td rowspan="2">USB-C</td><td>5 V</td><td>3 A</td></tr>
        <tr><td>20 V</td><td>5 A</td></tr></table><p>* One port only.</p></section>''')
        table = sections[0]['blocks'][0]
        self.assertEqual(table['grid'][2], ['USB-C', '20 V', '5 A'])
        self.assertEqual(table['rows'][1][0]['rowspan'], 2)
        self.assertTrue(table['rows'][0][0]['header'])
        self.assertEqual(sections[0]['blocks'][1]['text'], '* One port only.')
        self.assertEqual(sections[0]['anchor'], 'specs')

    def test_colspan_and_invalid_span(self):
        sections, _ = extract('<table><tr><th colspan="2">Input</th></tr><tr><td>AC</td><td>230 V</td></tr></table>')
        self.assertEqual(sections[0]['blocks'][0]['grid'][0], ['Input', 'Input'])
        for span in ['0', '-1', '1000', 'oops', '2']:
            with self.subTest(span=span), self.assertRaises(ValueError):
                extract(f'<table><tr><td rowspan="{span}">Invalid</td></tr></table>')

    def test_callouts_exclude_sizers_and_keep_complete_conditions(self):
        sections, _ = extract('''<div lang="en"><section id="ups"><h1>UPS</h1><p>Connect directly.</p>
        <table class="manual-callout-table"><tr><td class="manual-callout-label">WARNING
        <span class="manual-callout-label-sizer" aria-hidden="true">CAUTION NOTE</span></td>
        <td class="manual-callout-body"><p>Do not cascade.</p><ul><li>Single unit only.</li></ul></td></tr></table>
        </section></div>''')
        self.assertEqual(sections[0]['title'], 'UPS')
        self.assertEqual(sections[0]['blocks'][0]['text'], 'Connect directly.')
        warning = sections[0]['blocks'][1]
        self.assertEqual(warning['type'], 'callout')
        self.assertEqual(warning['label'], 'WARNING')
        self.assertIn('Single unit only.', warning['body'])
        self.assertNotIn('CAUTION', json.dumps(sections))

    def test_nested_steps_and_parent_chapter_context_stay_together(self):
        sections, _ = extract('''<section id="charging"><h1>Charging</h1><p>Disconnect before cleaning.</p>
        <section id="ac"><h2>AC charging</h2><ol start="2"><li>Connect.<ul><li>Dry hands only.</li></ul></li>
        <li>Press.</li></ol></section></section>''')
        self.assertEqual(len(sections), 1)
        steps = sections[0]['blocks'][2]
        self.assertEqual(steps['start'], '2')
        self.assertEqual(steps['items'][0]['children'][0]['items'][0]['text'], 'Dry hands only.')
        self.assertIn('2. Connect.', steps['text'])
        self.assertIn('3. Press.', steps['text'])
        self.assertEqual(sections[0]['blocks'][1]['anchor'], 'ac')

    def test_noise_removal_preserves_semantic_carriers_and_visible_durations(self):
        sections, _ = extract('''<section id="operation"><h1>Operation<a class="headerlink">¶</a></h1>
        <script>secret()</script><style>.x{color:red}</style><nav>Choose language</nav>
        <div hidden>Hidden duplicate</div><span style="display: none">Hidden</span>
        <div class="hb-composite-stage" aria-hidden="true"><img alt="duplicate"/></div>
        <div class="hb-reference-semantic"><p>Hold button.</p></div>
        <div class="hb-operation-duration" aria-hidden="true">3s</div></section>''')
        text = json.dumps(sections)
        for noise in ['secret', 'color:red', 'Choose language', 'Hidden', 'duplicate', '¶']:
            self.assertNotIn(noise, text)
        self.assertIn('Hold button.', text)
        self.assertIn('3s', text)

    def test_image_alts_are_labelled_not_claimed_as_ocr(self):
        sections, coverage = extract('<section id="ports"><h1>Ports</h1><img alt="USB-C 100 W"/><img src="diagram.png"/></section>')
        self.assertEqual(coverage['images'], 2)
        self.assertEqual(coverage['images_with_alt'], 1)
        self.assertEqual(coverage['image_text_coverage'], 'alt_only_no_ocr')
        self.assertFalse(sections[0]['blocks'][0]['transcribed'])
        self.assertEqual(sections[0]['blocks'][0]['evidence_kind'], 'image_alt')

    def test_missing_main_empty_content_and_duplicate_anchor_fail(self):
        with self.assertRaisesRegex(ValueError, 'no main'):
            extract_sections('<body>Not a manual</body>', url='manual.html')
        with self.assertRaisesRegex(ValueError, 'no queryable'):
            extract('<script>only script</script>')
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            extract('<h1 id="x">First</h1><p>A</p><h1 id="x">Second</h1><p>B</p>')

    def test_ids_are_stable_across_style_changes(self):
        left, _ = extract('<section id="specs"><h1>Specs</h1><p>230 V</p></section>')
        right, _ = extract('<section id="specs" style="color:red"><h1>Specs</h1><p class="new">230 V</p></section>')
        self.assertEqual(left, right)


class KnowledgeExportTests(unittest.TestCase):
    def test_frozen_export_precedes_receipt_and_requires_every_eu_route(self):
        hooks = {}
        app = SimpleNamespace(add_config_value=lambda *a: None,
                              connect=lambda event, callback, priority=500: hooks.update({callback.__name__: priority}),
                              add_css_file=lambda *a: None, add_js_file=lambda *a: None)
        setup(app)
        self.assertLess(hooks['write_knowledge'], hooks['write_deployment_receipt'])
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'publish' / 'web'
            source.mkdir(parents=True)
            out = root / 'html'
            out.mkdir()
            manifest_path = source.parent / 'publish_manifest.json'
            manifest = {'built_at': '2026-10-01', 'targets': [
                {'region': 'EU', 'route': 'MODEL/EU/en', 'manual': 'md/manual.md'}]}
            manifest_path.write_text(json.dumps(manifest))
            url = 'MODEL/EU/en/md/manual.html'
            (out / url).parent.mkdir(parents=True)
            (out / url).write_text('<main><h1 id="specs">Specs</h1><p>230 V</p></main>')
            products = [{'model': 'MODEL', 'region': 'EU', 'name': 'Product', 'publications': [
                {'url': url, 'lang': 'en', 'language_scope': 'single', 'version': '1.0'}]}]
            app = SimpleNamespace(srcdir=source, outdir=out, builder=SimpleNamespace(format='html'))
            with patch('tools.rtd_portal.portal_data', return_value=({}, products)):
                write_knowledge(app, None)
                write_deployment_receipt(app, None)
                receipt = json.loads((out / 'manual-deployment.json').read_text())
                corpus = json.loads((out / ARTIFACT).read_text())
                self.assertEqual(receipt['files'][ARTIFACT], hashlib.sha256((out / ARTIFACT).read_bytes()).hexdigest())
                self.assertEqual(receipt['source_sha256'], corpus['source_sha256'])
                manifest['targets'].append({'region': 'EU', 'route': 'OTHER/EU/en', 'manual': 'md/manual.md'})
                manifest_path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, 'does not cover'):
                    write_knowledge(app, None)
                manifest_path.write_text('{}')
                with self.assertRaisesRegex(ValueError, 'requires a frozen'):
                    write_knowledge(app, None)

    def test_receipt_only_frozen_builds_keep_their_existing_contract(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'publish' / 'web'
            source.mkdir(parents=True)
            (source.parent / 'publish_manifest.json').write_text('{}')
            app = SimpleNamespace(srcdir=source, outdir=tmp, builder=SimpleNamespace(format='html'))
            with patch('tools.rtd_portal.portal_data', return_value=({}, [])):
                write_knowledge(app, None)
            self.assertFalse((Path(tmp) / ARTIFACT).exists())

    def test_eu_only_and_legacy_language_is_explicitly_unknown(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'manual.html').write_text('<main><p>Published</p></main>')
            publications = [{'url': 'manual.html', 'lang': 'en',
                             'language_scope': 'legacy_unspecified', 'version': '2.0'}]
            products = [{'model': 'MODEL', 'region': r, 'name': 'Product', 'publications': publications}
                        for r in ['EU', 'US']]
            corpus = make_corpus(products, root, source_sha256='a' * 64, published_at='2026-10-01')
            self.assertEqual(corpus['counts']['editions'], 1)
            self.assertIsNone(corpus['documents'][0]['lang'])
            self.assertEqual(corpus['documents'][0]['declared_lang'], 'en')
            self.assertEqual(corpus['documents'][0]['version'], '2.0')

    def test_duplicate_and_escaping_publications_fail(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'manual.html').write_text('<main><p>Published</p></main>')
            pub = {'url': 'manual.html', 'lang': 'en', 'language_scope': 'single'}
            product = {'model': 'MODEL', 'region': 'EU', 'name': 'Product', 'publications': [pub, pub]}
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                make_corpus([product], root, source_sha256='a' * 64, published_at='')
            product['publications'] = [{**pub, 'url': '../escape.html'}]
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                make_corpus([product], root, source_sha256='a' * 64, published_at='')

    def test_non_release_builds_never_emit_production_corpus(self):
        with TemporaryDirectory() as tmp:
            app = SimpleNamespace(srcdir=tmp, outdir=tmp, builder=SimpleNamespace(format='html'))
            write_knowledge(app, None)
            write_knowledge(app, RuntimeError('failed build'))
            self.assertFalse((Path(tmp) / ARTIFACT).exists())
