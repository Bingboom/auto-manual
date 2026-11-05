from pathlib import Path
import json,re,unicodedata
from bs4 import BeautifulSoup
R=Path('/private/tmp/manual-web-audit-20261102');B=R/'remaining-warning-build'
def norm(t):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKC',t).lower())
for m in ['JE-3000B']:
 v='v12';corpus=norm(' '.join(b['text'] for p in sorted((R/'pdf-pages'/m).glob('p*.ocr.json')) for b in json.loads(p.read_text())));grams={corpus[i:i+8] for i in range(len(corpus)-7)}
 soup=BeautifulSoup((B/(m+'-html-'+v)/('manual_'+m.replace('-','').lower()+'_us_en.html')).read_text(),'html.parser');main=soup.select_one('[role=main]')
 for t in main.select('style,script,[hidden],[aria-hidden="true"]'):t.decompose()
 rows=[]
 for tag in main.select('p,li,td'):
  if tag.select('p,li,td'):continue
  text=tag.get_text(' ',strip=True);s=norm(text)
  if len(s)<35:continue
  score=sum(s[i:i+8] in grams for i in range(len(s)-7))/(len(s)-7)
  if score<.65:rows.append({'text':text,'coverage':round(score,3)})
 (B/(m+'-extra-copy.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(m,json.dumps(rows,ensure_ascii=False))
