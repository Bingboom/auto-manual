"""Recheck source lines, native tables, resources and anchors against built HTML."""
from pathlib import Path
import hashlib
import json
import re
import sys
from urllib.parse import unquote, urlsplit
import fitz
from bs4 import BeautifulSoup

SOURCE = Path(__file__).resolve().parent.parent
HTML = Path(sys.argv[1]).resolve()
MANUAL = HTML / 'manual_jaad500asil_jp_ja.html'
def normalize(value):
    return re.sub(r'\s+', '', value)

soup = BeautifulSoup(MANUAL.read_text(), 'html.parser')
body = soup.select_one('article')
text = normalize(body.get_text())
matched, missing = [], []
with fitz.open(SOURCE / 'source/original.pdf') as pdf:
    assert len(pdf) == 10
    for index, page in enumerate(pdf):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                value = ''.join(span['text'] for span in line['spans'])
                value = re.sub(r'^[·・■*＊\s]+', '', value)
                value = re.sub(r'^\d+[.．]\s*', '', value)
                # Print folios and miniature duplicate booklet cover are artwork.
                if (len(normalize(value)) < 3 or line['bbox'][1] > 348
                        or index == 1 and max(s['size'] for s in line['spans']) < 3):
                    continue
                (matched if normalize(value) in text else missing).append(
                    {'physical_page': index + 1, 'text': value})
    assert not missing, missing
led = [[c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
       for row in body.select_one('table.manual-table').find_all('tr')]
assert led == [['LEDライトの状態', 'ライトの色', '製品の状態'],
               ['点滅', '緑色', '充電中'], ['点灯', '赤色', '異常状態'],
               ['点灯', '緑色', '接続成功、充電準備完了'], ['消灯', 'なし', '電源オフ']]
assert len(body.select('[data-component-id="HB-WARRANTY-SECTION"]')) == 6
assert len(body.select('table.manual-callout-table')) == 2
ids = [node['id'] for node in soup.select('[id]')]
assert len(ids) == len(set(ids)), 'duplicate anchor'
resources = []
for node in soup.select('[src], link[href], a[href]'):
    value = node.get('src') or node.get('href')
    url = urlsplit(value)
    if url.scheme or url.netloc:
        continue
    if url.path:
        path = (HTML / unquote(url.path)).resolve()
        assert path.is_relative_to(HTML) and path.is_file(), value
        resources.append(value)
    if not url.path and url.fragment:
        assert unquote(url.fragment) in ids, value
result = {'source_lines_matched': len(matched), 'missing': missing,
          'coverage_boundary': 'all native PDF lines >=3 characters except print folios and miniature booklet duplicate; LED cells independently exact',
          'led_rows_exact': True, 'warranty_sections': 6, 'callouts': 2,
          'unique_anchors': len(ids), 'local_resource_references': len(resources),
          'original_pdf_sha256': hashlib.sha256((SOURCE/'source/original.pdf').read_bytes()).hexdigest(),
          'built_html_sha256': hashlib.sha256(MANUAL.read_bytes()).hexdigest()}
(SOURCE / 'evidence/source-line-parity.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
