from pathlib import Path
from bs4 import BeautifulSoup
import re,json,unicodedata,difflib
R=Path('/private/tmp/manual-web-audit-20261102');s=BeautifulSoup((R/'style-3000d-html-v19/manual_jhp3000d_us_en.html').read_text(),'html.parser').select_one('#furo-main-content')
for e in s.select('.headerlink'):e.decompose()
norm=lambda s:re.sub('[^a-z0-9]','',unicodedata.normalize('NFKC',s).lower())
web=norm(s.get_text(' ',strip=True)+' '+' '.join(i.get('alt','') for i in s.find_all('img')));wg={web[i:i+10] for i in range(len(web)-9)};pages=[];allocr=[]
for f in sorted((R/'style-3000d-ownref').glob('p*.ocr.json')):
 pn=int(f.name[1:3]);items=json.loads(f.read_text());ocr=' '.join(i['text'] for i in items)
 if pn in [1,3]:continue
 allocr.append(ocr);c=[]
 for i in items:
  n=norm(i['text'])
  if len(n)<12:continue
  cov=sum(n[j:j+10] in wg for j in range(len(n)-9))/(len(n)-9)
  if cov<.75:c.append({'text':i['text'],'coverage':round(cov,3)})
 pages.append({'page':pn,'line_count':len(items),'candidates':c})
source=norm(' '.join(allocr));sg={source[i:i+10] for i in range(len(source)-9)};reverse=[]
for e in s.select('p,li,td,th'):
 if e.select('p,li,td,th'):continue
 t=e.get_text(' ',strip=True);n=norm(t)
 if len(n)<15:continue
 cov=sum(n[j:j+10] in sg for j in range(len(n)-9))/(len(n)-9)
 if cov<.75:reverse.append({'text':t,'coverage':round(cov,3)})
result={'source':'source/review-reference.pdf','source_sha256':'34fedc156d52e8a50ca65d23327d323b3647aee03bd6b6b4aa1d681723e249dc','pages':pages,'reverse_candidates':reverse};(R/'style-3000d-current-text-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({'source_candidates':[{ 'page':p['page'],'candidates':p['candidates']} for p in pages if p['candidates']],'reverse_candidates':reverse},indent=2))
