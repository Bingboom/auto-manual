"""Comparison relations across products and languages (Phase 2a, P2-3)."""
from collections import defaultdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.manual_knowledge.export import make_corpus
from tools.manual_knowledge.observe import SCHEMA, build_items, judge_previous
from tools.manual_knowledge.relations import build_relations, loose, numbers, summarize_relations

SNAPSHOT = 'git-20261002-45219a6e'
CALLOUT = '<div class="admonition"><p class="admonition-title">{}</p><p>{}</p></div>'


def callout(label, text):
    return CALLOUT.format(label, text)


def section(anchor, title, *blocks):
    return f'<h1 id="{anchor}">{title}</h1>' + ''.join(blocks)


def corpus(root, manuals):
    """``manuals`` maps (model, language) to (body, version); each becomes a published single-language edition."""
    products = defaultdict(list)
    for (model, language), (body, version) in manuals.items():
        url = f'{model}/EU/{language}/md/manual.html'
        (root / url).parent.mkdir(parents=True, exist_ok=True)
        (root / url).write_text(f'<main>{body}</main>', encoding='utf-8')
        products[model].append({'url': url, 'lang': language, 'language_scope': 'single', 'version': version})
    return make_corpus([{'model': model, 'region': 'EU', 'name': model, 'publications': publications}
                        for model, publications in products.items()], root, source_sha256='s', published_at='t')


def observe(root, manuals):
    built = corpus(root, manuals)
    items = build_items(built, {})
    return built, items, build_relations(built, items, 'test')


def parity(relations, model):
    return [r for r in relations if r['kind'] == 'language_parity' and r['scope']['model'] == model]


def languages(relation):
    return [member['variant_key'].rsplit('/', 1)[1] for member in relation['members']]


UPS = {
    'en': section('ups', 'UNINTERRUPTIBLE POWER SUPPLY (UPS)',
                  callout('WARNING', 'Do not use this product for data servers or medical devices.'),
                  callout('CAUTION', 'This product does not support 0 ms switching.'),
                  callout('NOTE', 'Charge the product between 0 °C and 45 °C.')),
    'de': section('usv', 'UNTERBRECHUNGSFREIE STROMVERSORGUNG (UPS)',
                  callout('WARNUNG', 'Verwenden Sie dieses Produkt nicht für Datenserver oder medizinische Geräte.'),
                  callout('VORSICHT', 'Dieses Produkt unterstützt kein Umschalten mit 0 ms.'),
                  '<table><tr><td>HINWEISE</td><td>Laden Sie das Produkt zwischen 0 °C und 45 °C.</td></tr></table>'),
    'nl': section('ups', 'ONONDERBROKEN STROOMVOORZIENING (UPS)',
                  callout('OPGELET', 'Dit product ondersteunt geen omschakeling binnen 0 ms.'),
                  callout('OPMERKING', 'Laad het product op tussen 0 °C en 45 °C.')),
}


class LanguageParityTests(unittest.TestCase):
    def test_a_missing_warning_is_a_topic_backed_candidate_while_presentation_differences_align(self):
        with TemporaryDirectory() as tmp:
            _, _, relations = observe(Path(tmp), {('M', 'en'): (UPS['en'], '2.6'), ('M', 'de'): (UPS['de'], '2.6'),
                                                  ('M', 'nl'): (UPS['nl'], SNAPSHOT)})
        warning, caution, note = parity(relations, 'M')
        self.assertEqual((languages(warning), warning['differences'], warning['context_topics']),
                         (['en', 'de'], ['absent'], ['ups']))
        [absent] = warning['absent_in']
        self.assertEqual((absent['variant_key'], absent['searched'], absent['revision_alignment'], absent['hits'],
                          absent['confidence']), ('M/EU/nl', 'topic_items', 'unknown', [], 'medium'))
        self.assertEqual((languages(caution), caution['anchors'], caution['differences'], caution['confidence']),
                         (['en', 'de', 'nl'], ['0'], [], 'high'))
        # The German note is a table row: a presentation difference, not a missing item.
        self.assertEqual((note['differences'], [m['block_type'] for m in note['members']]),
                         (['presentation'], ['callout', 'table', 'callout']))
        self.assertEqual(warning['observation_id'].rsplit(':', 1)[0], 'obs:language_parity:M/EU')
        self.assertTrue(all(r['status'] == 'candidate' for r in relations))

    def test_absence_confidence_follows_numbers_blind_spots_and_revisions(self):
        cable = 'The DC8020 adapter cable charges Jackery power stations only.'
        manuals = {
            ('M', 'en'): (section('box', 'IN THE BOX', callout('NOTE', cable)), '2.6'),
            # The same note as a plain paragraph is found by its number: maybe only presented differently.
            ('M', 'de'): (section('laden', 'LADEN', '<p>Das DC8020-Adapterkabel lädt nur Jackery-Powerstations.</p>'),
                          '2.6'),
            ('M', 'fr'): (section('boite', 'CONTENU', '<p>Câble de charge solaire.</p>'), '2.6'),
            ('M', 'nl'): (section('doos', 'INHOUD', '<p>Zonnekabel.</p><img src="cable.png">'), '2.6'),
            ('M', 'it'): (section('scatola', 'CONTENUTO', '<p>Cavo solare.</p>'), SNAPSHOT),
        }
        with TemporaryDirectory() as tmp:
            _, _, relations = observe(Path(tmp), manuals)
        [note] = parity(relations, 'M')
        absent = {entry['variant_key'].rsplit('/', 1)[1]: entry for entry in note['absent_in']}
        self.assertEqual({language: (entry['searched'], entry['confidence']) for language, entry in absent.items()},
                         {'de': ('whole_document', 'low'), 'fr': ('whole_document', 'high'),
                          'it': ('whole_document', 'medium'), 'nl': ('whole_document', 'medium')})
        self.assertEqual(len(absent['de']['hits']), 1)
        self.assertEqual((absent['nl']['images_without_alt'], absent['it']['revision_alignment']), (1, 'unknown'))
        self.assertEqual((note['anchors'], note['confidence']), (['8020'], 'high'))

    def test_moved_items_join_and_severity_disagreements_are_claims(self):
        en = section('ups', 'UPS', callout('WARNING', 'Do not use this product for data servers.'),
                     callout('CAUTION', 'This product does not support 0 ms switching.'),
                     callout('CAUTION', 'Charge the product between 0 °C and 45 °C.'))
        nl = section('ups', 'UPS', callout('OPGELET', 'Dit product ondersteunt geen omschakeling binnen 0 ms.'),
                     callout('WAARSCHUWING', 'Gebruik dit product niet voor dataservers.'),
                     callout('OPMERKING', 'Laad het product op tussen 0 °C en 45 °C.'))
        with TemporaryDirectory() as tmp:
            _, _, relations = observe(Path(tmp), {('M', 'en'): (en, '2.6'), ('M', 'nl'): (nl, '2.6')})
        found = {tuple(r['differences']): r for r in parity(relations, 'M')}
        self.assertEqual(sorted(found), [(), ('order',), ('severity',)])
        self.assertEqual(languages(found['order',]), ['en', 'nl'])
        # Shared numbers and equal printed revisions back a severity disagreement fully.
        self.assertEqual(([m['severity'] for m in found['severity',]['members']], found['severity',]['confidence']),
                         (['caution', 'note'], 'high'))

    def test_a_moved_paragraph_is_found_by_its_topics_but_a_broader_passage_is_not(self):
        storage = 'Battery capacity drops with every charge cycle and during long storage.'
        moved = '<p>De batterijcapaciteit neemt af bij het laden en bij lange opslag.</p>'
        broad = '<p>Laad, bewaar en vervoer de batterij niet bij vuur, water of kinderen.</p>'
        for nl, expected in ((moved + broad, ('topic_document', 1, 'low')), (broad, ('topic_document', 0, 'medium'))):
            with TemporaryDirectory() as tmp:
                _, _, relations = observe(Path(tmp), {
                    ('M', 'en'): (section('s', 'SAFETY', f'<p>{storage}</p>'), '2.6'),
                    # A maintenance section is no safety section: its prose carries no item.
                    ('M', 'nl'): (section('o', 'ONDERHOUD', nl), SNAPSHOT)})
            [absent] = parity(relations, 'M')[0]['absent_in']
            self.assertEqual((absent['searched'], len(absent['hits']), absent['confidence']), expected)

    def test_compliance_lines_pair_on_identical_text_never_on_position(self):
        en = section('eu', 'EU Regulations', '<p>sales@hello-tech.com</p>',
                     '<p>The full text of the declaration is available online.</p>', '<p>www.hello-tech.com</p>')
        nl = section('eu', 'EU declaration', '<p>Download de app.</p>', '<p>www.hello-tech.com</p>',
                     '<p>sales@hello-tech.com</p>')
        with TemporaryDirectory() as tmp:
            _, items, relations = observe(Path(tmp), {('M', 'en'): (en, '2.6'), ('M', 'nl'): (nl, '2.6')})
        text = {item['knowledge_id']: item['text'] for item in items}
        groups = sorted((sorted(text[m['knowledge_id']] for m in r['members']), r['differences'])
                        for r in parity(relations, 'M'))
        self.assertEqual(groups, [
            (['Download de app.'], ['absent']),
            (['The full text of the declaration is available online.'], ['absent']),
            (['sales@hello-tech.com', 'sales@hello-tech.com'], ['order']),
            (['www.hello-tech.com', 'www.hello-tech.com'], [])])

    def test_previous_relations_go_stale_only_where_their_evidence_changed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manuals = {('M', 'en'): (UPS['en'], '2.6'), ('M', 'de'): (UPS['de'], '2.6'),
                       ('M', 'nl'): (UPS['nl'], SNAPSHOT)}
            _, items, relations = observe(root, manuals)
            previous = {'schema': SCHEMA, 'items': items, 'relations': relations}
            # An unrelated nl paragraph changes the edition the missing warning was searched in.
            manuals['M', 'nl'] = (UPS['nl'] + '<p>Lees de handleiding.</p>', SNAPSHOT)
            built, current, _ = observe(root, manuals)
        result = judge_previous(previous, build_items(built, {}), built)
        self.assertEqual(result['items'], {'fresh': len(items), 'stale': 0})
        self.assertEqual(result['stale_relations'], [parity(relations, 'M')[0]['observation_id']])
        self.assertEqual(len(current), len(items))


class CrossProductTests(unittest.TestCase):
    def test_reuse_kinds_and_product_specific_warnings(self):
        a = section('s', 'SAFETY', callout('WARNING', 'Keep away from water.'), callout('NOTE', 'Charge at 0°C to 45°C.'),
                    callout('WARNING', 'Do not touch the vents.'), callout('WARNING', 'UPS mode is not for servers.'),
                    callout('NOTE', 'Read this first.'))
        b = section('s', 'SAFETY', callout('WARNING', 'Keep away from water.'),
                    callout('NOTE', 'Charge at 0 °C to 45 °C.'), callout('CAUTION', 'Do not touch the vents.'))
        with TemporaryDirectory() as tmp:
            _, _, relations = observe(Path(tmp), {('A', 'en'): (a, '1.0'), ('B', 'en'): (b, '1.0')})
        kinds = defaultdict(list)
        for relation in relations:
            kinds[relation['kind']].append(relation)
        self.assertNotIn('language_parity', kinds)  # one language per model: nothing to align
        [exact] = kinds['exact_reuse']
        self.assertEqual(([m['variant_key'] for m in exact['members']], exact['confidence'], exact['scope']),
                         (['A/EU/en', 'B/EU/en'], 'high', {'region': 'EU', 'language': 'en'}))
        self.assertEqual(sorted(tuple(r['differences']) for r in kinds['near_reuse']),
                         [('label', 'severity'), ('text_form',)])
        specific = {r['members'][0]['knowledge_id']: r for r in kinds['product_specific']}
        self.assertEqual(sorted(r['confidence'] for r in specific.values()), ['low', 'medium'])
        absent = next(iter(specific.values()))['absent_in']
        self.assertEqual([(e['variant_key'], e['searched'], e['revision_alignment']) for e in absent],
                         [('B/EU/en', 'same_category_items', 'not_applicable')])
        summary = summarize_relations(relations)
        self.assertEqual((summary['relations'], summary['relations_by_kind']['product_specific']),
                         (len(relations), {'low': 1, 'medium': 1}))

    def test_relations_are_deterministic_and_uniquely_identified(self):
        manuals = {('M', 'en'): (UPS['en'], '2.6'), ('M', 'de'): (UPS['de'], '2.6'), ('M', 'nl'): (UPS['nl'], SNAPSHOT)}
        with TemporaryDirectory() as tmp:
            first = observe(Path(tmp), manuals)[2]
            second = observe(Path(tmp), manuals)[2]
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        ids = [relation['observation_id'] for relation in first]
        self.assertEqual(len(ids), len(set(ids)))

    def test_comparison_keys_keep_meaning_and_ignore_form(self):
        self.assertEqual(numbers('2,4 GHz, 12 V and 3–6 months'), {'2.4', '12', '3', '6'})
        self.assertEqual(loose('• Charge at 0°C – “fast”'), loose('Charge at 0 °C - "Fast"'))
        self.assertNotEqual(loose('-10 °C'), loose('10 °C'))


if __name__ == '__main__':
    unittest.main()
