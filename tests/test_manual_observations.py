"""Knowledge observation identity, freshness and determinism (Phase 2a, P2-1)."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.manual_knowledge.export import ARTIFACT as CORPUS, write_knowledge
from tools.manual_knowledge.observe import (SCHEMA, build_items, content_sha256, judge_previous, main,
                                            normalized)
from tools.rtd.deployment_receipt import write_deployment_receipt

CALLOUT = '<div class="admonition"><p class="admonition-title">{}</p><p>{}</p></div>'


def page(*callouts):
    return '<main><h1 id="safety">Safety</h1>' + ''.join(CALLOUT.format(*c) for c in callouts) + '</main>'


def build_site(root, body, *, url='MODEL/EU/en/md/manual.html'):
    """Build a sealed one-manual deployment the way the frozen RTD build does."""
    source, out = root / 'publish' / 'web', root / 'html'
    shutil.rmtree(out, ignore_errors=True)
    source.mkdir(parents=True, exist_ok=True)
    (out / url).parent.mkdir(parents=True, exist_ok=True)
    (out / url).write_text(body)
    route, manual = url.split('/md/')
    (source.parent / 'publish_manifest.json').write_text(json.dumps({'built_at': '2026-10-01', 'targets': [
        {'region': 'EU', 'route': route, 'manual': 'md/' + Path(manual).with_suffix('.md').name}]}))
    products = [{'model': 'MODEL', 'region': 'EU', 'name': 'Product', 'publications': [
        {'url': url, 'lang': 'en', 'language_scope': 'single', 'version': '2.6'}]}]
    app = SimpleNamespace(srcdir=source, outdir=out, builder=SimpleNamespace(format='html'))
    with patch('tools.rtd.portal.portal_data', return_value=({}, products)):
        write_knowledge(app, None)
        write_deployment_receipt(app, None)
    return out


def corpus_of(out):
    return json.loads((out / CORPUS).read_text())


def ids(corpus):
    return [item['knowledge_id'] for item in build_items(corpus, {})]


def run(argv):
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(argv)
    return code, json.loads(output.getvalue())


class KnowledgeIdentityTests(unittest.TestCase):
    def test_ids_survive_insertions_and_route_moves_but_not_label_or_text_edits(self):
        hot, wet = ('WARNING', 'Hot surface.'), ('CAUTION', 'Wet floor.')
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = build_items(corpus_of(build_site(root, page(hot, wet))), {})
            base_ids = [item['knowledge_id'] for item in base]
            # Inserting a block shifts every later block_id; the knowledge_ids stay.
            inserted = build_items(corpus_of(build_site(root, page(('NOTE', 'Read first.'), hot, wet))), {})
            self.assertEqual([item['knowledge_id'] for item in inserted[1:]], base_ids)
            self.assertNotEqual([item['source']['block_id'] for item in inserted[1:]],
                                [item['source']['block_id'] for item in base])
            # A route move changes every section and block id; the knowledge_ids stay.
            moved = build_items(corpus_of(build_site(root, page(hot, wet),
                                                     url='MODEL/EU/en/md/manual_model_eu_en.html')), {})
            self.assertEqual([item['knowledge_id'] for item in moved], base_ids)
            self.assertNotEqual(moved[0]['source']['source_ref'], base[0]['source']['source_ref'])
            # The item's own text or label is its content: editing either replaces only that id.
            edited = ids(corpus_of(build_site(root, page(hot, ('CAUTION', 'Wet floor ahead.')))))
            self.assertEqual((edited[0] == base_ids[0], edited[1] == base_ids[1]), (True, False))
            relabelled = ids(corpus_of(build_site(root, page(('CAUTION', 'Hot surface.'), wet))))
            self.assertEqual((relabelled[0] == base_ids[0], relabelled[1] == base_ids[1]), (False, True))

    def test_identity_text_ignores_width_bullets_and_spacing_but_keeps_signs_and_markers(self):
        self.assertEqual(normalized('• Ｈot\n   surface  1０ °C'), 'Hot surface 10 °C')
        self.assertNotEqual(normalized('-10 °C'), normalized('10 °C'))
        self.assertEqual(normalized('*Sold separately.'), '*Sold separately.')
        self.assertNotEqual(content_sha256('WARNING', 'Hot.'), content_sha256('WARNING Hot.', ''))

    def test_repeated_items_get_occurrence_numbers_and_items_keep_identity_and_source(self):
        with TemporaryDirectory() as tmp:
            corpus = corpus_of(build_site(Path(tmp), page(('WARNING', 'Hot.'), ('WARNING', 'Hot.'), ('Tipp?', 'x'))))
            items = build_items(corpus, {'MODEL_EU': {'UPS功能': True}})
            self.assertEqual([i['knowledge_id'][-2:] for i in items[:2]], [':0', ':1'])
            self.assertEqual(items[0]['knowledge_id'].rsplit(':', 2)[0], 'kn:MODEL/EU/en:warning')
            first = items[0]
            self.assertEqual((first['manual_variant_id'], first['status'], first['severity'], first['label']),
                             ('MODEL/EU/en@2.6', 'extracted', 'warning', 'WARNING'))
            self.assertEqual(first['observed_context']['feature'], {'UPS功能': True})
            self.assertEqual(first['source']['source_ref'], 'MODEL/EU/en/md/manual.html#safety')
            self.assertEqual((first['topic'], first['review_flags']), (['temperature'], []))
            self.assertEqual(items[2]['review_flags'], ['severity_unknown', 'topic_unknown'])
            self.assertEqual(build_items(corpus, {})[0]['observed_context']['feature'], 'unknown')


class ObservationCommandTests(unittest.TestCase):
    def test_artifact_is_deterministic_and_bound_to_the_sealed_corpus(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = build_site(root, page(('WARNING', 'Hot.'), ('NOTE', 'Charge first.')))
            code, result = run(['--site', str(out), '--output', str(root / 'a.json')])
            self.assertEqual((code, result['summary']['items'], result['summary']['relations']), (0, 2, 0))
            run(['--site', str(out), '--output', str(root / 'b.json')])
            self.assertEqual((root / 'a.json').read_bytes(), (root / 'b.json').read_bytes())
            artifact = json.loads((root / 'a.json').read_text())
            receipt = json.loads((out / 'manual-deployment.json').read_text())
            self.assertEqual((artifact['schema'], artifact['corpus_sha256']), (SCHEMA, receipt['files'][CORPUS]))
            self.assertEqual(artifact['summary']['items_by_variant'], {'MODEL/EU/en': 2})

    def test_refuses_a_deployment_whose_corpus_does_not_match_its_receipt(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = build_site(root, page(('WARNING', 'Hot.')))
            (out / CORPUS).write_text((out / CORPUS).read_text().replace('Hot.', 'Cold.'))
            code, result = run(['--site', str(out), '--output', str(root / 'a.json')])
            self.assertEqual((code, result['status']), (1, 'refused'))
            self.assertFalse((root / 'a.json').exists())

    def test_previous_items_and_relations_turn_stale_only_where_their_evidence_changed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = build_site(root, page(('WARNING', 'Hot.'), ('CAUTION', 'Wet floor.')))
            run(['--site', str(out), '--output', str(root / 'old.json')])
            old = json.loads((root / 'old.json').read_text())
            hot, wet = (item['knowledge_id'] for item in old['items'])
            html = old['items'][0]['source']['html_sha256']
            old['relations'] = [
                {'observation_id': 'obs:hot', 'members': [{'knowledge_id': hot}]},
                {'observation_id': 'obs:wet', 'members': [{'knowledge_id': wet}]},
                {'observation_id': 'obs:absent', 'members': [{'knowledge_id': hot}],
                 'absent_in': [{'variant_key': 'MODEL/EU/en', 'html_sha256': html}]}]
            (root / 'old.json').write_text(json.dumps(old))
            out = build_site(root, page(('WARNING', 'Hot.'), ('CAUTION', 'Wet floor ahead.')))
            code, result = run(['--site', str(out), '--output', str(root / 'new.json'),
                                '--previous', str(root / 'old.json')])
            self.assertEqual(code, 0)
            self.assertEqual(result['previous']['items'], {'fresh': 1, 'stale': 1})
            self.assertEqual(result['previous']['stale_items'], [wet])
            self.assertEqual(result['previous']['stale_relations'], ['obs:absent', 'obs:wet'])
            with self.assertRaises(ValueError):
                judge_previous({'schema': 'other'}, [], corpus_of(out))


if __name__ == '__main__':
    unittest.main()
