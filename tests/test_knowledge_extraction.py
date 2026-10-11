"""Knowledge extraction scope and topic vocabulary (Phase 2a, P2-2)."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.test_manual_observations import build_site, run
from tools.manual_knowledge.carriers import carriers, section_kind
from tools.manual_knowledge.html import extract_sections
from tools.manual_knowledge.topics import TOPICS, classify


def table(*rows, header=('Symbol', 'Meaning')):
    head = '<tr>' + ''.join(f'<th>{cell}</th>' for cell in header) + '</tr>' if header else ''
    return '<table>' + head + ''.join('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
                                      for row in rows) + '</table>'


LEGEND = table(('WARNING', 'Hazardous practices that may result in serious injury.'),
               ('CAUTION', 'Hazardous practices that may result in injury.'), ('NOTE', 'May damage the product.'))


def extracted(html):
    """(section title, rule, category, label, text, item_index) for every carrier, in reading order."""
    sections, _ = extract_sections(f'<main>{html}</main>', url='MODEL/EU/en/md/manual.html')
    return [(section['title'], c.rule, c.category, c.label, c.text, c.item_index)
            for section in sections for _, c in carriers(section)]


class CarrierTests(unittest.TestCase):
    def test_signal_rows_and_paragraphs_are_warnings_but_legend_tables_are_definitions(self):
        found = extracted('<h1 id="ops">Operations</h1>' + LEGEND
                          + table(('HINWEISE', 'Schalten Sie das Gerät aus.'), ('Gewicht', '10 kg'), header=None)
                          + '<p>Note: Tighten terminals 1 and 2.</p><p>Note:</p><p>Plain text.</p>'
                          + '<p>NOTE: This device complies with part 15 of the FCC Rules.</p>')
        self.assertEqual([row[1:] for row in found], [
            ('extract.signal_row', 'warning', 'HINWEISE', 'Schalten Sie das Gerät aus.', 0),
            ('extract.signal_paragraph', 'warning', 'Note', 'Tighten terminals 1 and 2.', None),
            # Cited legislation outranks the signal-word prefix.
            ('extract.compliance_legislation', 'compliance', None,
             'NOTE: This device complies with part 15 of the FCC Rules.', None)])

    def test_safety_sections_split_by_paragraph_top_level_list_item_and_table_row(self):
        found = extracted('<h1 id="s">SICHERHEITSHINWEISE</h1><p>Nicht ins Feuer werfen.</p>'
                          '<ul><li>Von Kindern fernhalten.<ul><li>Auch beim Laden.</li></ul></li>'
                          '<li>Nicht zerlegen.</li></ul><h2>Lagerung</h2><img alt="icon">'
                          + table(('⚠ WARNING', 'May result in serious injury.'),
                                  ('⚠ CAUTION', 'May result in injury.'))
                          + table(('Lagerung', '-10 °C bis 45 °C'), header=None)
                          + '<p>Batteries comply with Regulation (EU) 2023/1542.</p>')
        self.assertEqual([row[1:3] + row[4:] for row in found], [
            ('extract.safety_section', 'safety', 'Nicht ins Feuer werfen.', None),
            ('extract.safety_section', 'safety', 'Von Kindern fernhalten.\n• Auch beim Laden.', 0),
            ('extract.safety_section', 'safety', 'Nicht zerlegen.', 1),
            ('extract.safety_section', 'safety', 'Lagerung\n-10 °C bis 45 °C', 0),
            ('extract.compliance_legislation', 'compliance', 'Batteries comply with Regulation (EU) 2023/1542.',
             None)])

    def test_symbol_rows_follow_their_icon_and_markings_are_compliance(self):
        dutch = 'Batterijen mogen niet bij het huishoudelijk afval.'
        found = extracted('<h1 id="sym">MEANING OF SYMBOLS</h1>' + table(
            ('<img alt="weee">', 'Do not dispose of as household waste.'),
            ('<img alt="li_ion">', 'A lithium-ion battery is inside.'),
            # Alt text that repeats the meaning is no icon name; the WEEE statement still marks it.
            (f'<img alt="{dutch}">', dutch),
            # Without an icon the cells are meanings side by side and stay one row.
            ('Read the manual.', 'Keep away from fire.')))
        self.assertEqual([row[1:] for row in found], [
            ('extract.marking_symbol', 'compliance', 'weee', 'Do not dispose of as household waste.', 1),
            ('extract.symbol_row', 'safety', 'li_ion', 'A lithium-ion battery is inside.', 2),
            ('extract.marking_symbol', 'compliance', None, dutch, 3),
            ('extract.symbol_row', 'safety', None, 'Read the manual.\nKeep away from fire.', 4)])

    def test_compliance_sections_keep_every_statement_and_other_sections_carry_nothing(self):
        found = extracted('<h1 id="eu">EU Regulations</h1>'
                          '<p>Hereby, the company declares that this product complies with '
                          'Directive 2014/53/EU.</p>'
                          '<p>Manufacturer: Company</p><h1 id="specs">Specifications</h1><p>Capacity 1 kWh</p>')
        self.assertEqual([row[1:3] for row in found], [('extract.compliance_legislation', 'compliance'),
                                                        ('extract.compliance_section', 'compliance')])

    def test_section_titles_are_recognized_in_every_manual_language(self):
        titles = {'IMPORTANT SAFETY INSTRUCTIONS': 'safety', 'CONSIGNES DE SÉCURITÉ': 'safety',
                  'PRECAUCIONES': 'safety', 'VEILIGHEIDSINSTRUCTIES': 'safety', 'ZASADY BEZPIECZEŃSTWA': 'safety',
                  'ВАЖЛИВІ ІНСТРУКЦІЇ З БЕЗПЕКИ': 'safety', 'SIGNIFICADO DOS SÍMBOLOS': 'symbols',
                  'EU Declaration of Conformity': 'compliance', 'AUTHORIZED REPRESENTATIVE': 'compliance',
                  'SPECIFICATIONS': None}
        self.assertEqual({title: section_kind(title) for title in titles}, titles)


class TopicTests(unittest.TestCase):
    def test_anchors_and_stems_classify_every_manual_language(self):
        cases = {
            'Do not use it for data servers; it does not support 0 ms UPS switching.': ['ups'],
            'Ne branchez pas la sortie CA sur le réseau.': ['ac_output', 'connection'],
            'Порт DC 12 В сумісний лише з автомобільними акумуляторами.': ['dc_usb_car', 'battery'],
            'Connect the solar panel to the PV input.': ['pv_input', 'connection'],
            'Laden Sie das Gerät nicht bei Temperaturen unter 0 °C.': ['temperature', 'charging'],
            'Turn on energy saving mode in the app via Bluetooth.': ['energy_saving', 'app_wireless'],
            'Kortsluiting kan brand veroorzaken.': ['electrical', 'fire'],
            'Les piles usagées doivent être recyclées.': ['battery', 'disposal'],
            'Store and transport the product at 20–30 °C.': ['temperature', 'storage_transport'],
            'Use a grounded outlet.': ['grounding'], 'Mantenha fora do alcance de crianças.': ['children'],
            'Не занурюйте у воду.': ['water'], 'Nie rozmontowuj produktu.': ['disassembly'],
        }
        self.assertEqual({text: classify(text) for text in cases}, cases)
        self.assertEqual(len(TOPICS), 18)

    def test_false_friends_stay_unclassified(self):
        texts = ['Evite la luz solar directa.',  # sunlight, not PV input
                 'Ce produit ne prend pas en charge le mode ECO.',  # "supports", not charging
                 "Le produit dispose d'une poignée.",  # "has", not disposal
                 'Works with home energy storage systems.',  # not storage or transport
                 'What kind of cable is included?',  # English "kind", not German "Kind"
                 'Не залишайте в салоні припаркованого автомобіля.']  # a parked car, not car charging
        self.assertEqual({text: classify(text) for text in texts}, {text: [] for text in texts})
        self.assertEqual(classify('Riesgo de descarga eléctrica.'), ['electrical'])


class ObservationScopeTests(unittest.TestCase):
    def test_artifact_records_compliance_as_found_and_reports_undetermined_topics(self):
        body = ('<main><h1 id="safety">Safety</h1>' + LEGEND
                + '<div class="admonition"><p class="admonition-title">WARNING</p><p>Hot surface.</p></div>'
                + '<p>Read all instructions.</p><h1 id="eu">EU Regulations</h1>'
                + '<p>This product complies with Directive 2014/53/EU and carries the CE mark.</p></main>')
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, result = run(['--site', str(build_site(root, body)), '--output', str(root / 'a.json')])
            items = json.loads((root / 'a.json').read_text())['items']
        self.assertEqual(code, 0)
        self.assertEqual([(i['category'], i['topic'], i['review_flags']) for i in items], [
            ('warning', ['temperature'], []), ('safety', [], ['topic_unknown']),
            ('compliance', [], ['topic_unknown'])])
        self.assertEqual((items[2]['applicability'], items[2]['legislation'], items[2]['severity']),
                         ('unknown', ['2014/53/EU', 'CE'], None))
        self.assertNotIn('applicability', items[0])
        summary = result['summary']
        self.assertEqual(
            (summary['items_by_category'], summary['topic_undetermined'], summary['items_by_severity']),
            ({'warning': 1, 'safety': 1, 'compliance': 1}, {'warning': 0, 'safety': 1, 'compliance': 1},
             {'warning': 1}))
        self.assertEqual(items[0]['method']['rules'], ['extract.callout', 'topic.temperature'])


if __name__ == '__main__':
    unittest.main()
