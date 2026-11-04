from pathlib import Path
import json,re,unicodedata
from bs4 import BeautifulSoup
R=Path('/private/tmp/manual-web-audit-20261102');B=R/'remaining-warning-build'
def norm(t):return re.sub(r'[^a-z0-9.]','',unicodedata.normalize('NFKC',t).lower())
for m in ['JE-3000B']:
 v='v12';soup=BeautifulSoup((B/(m+'-html-'+v)/('manual_'+m.replace('-','').lower()+'_us_en.html')).read_text(),'html.parser');main=soup.select_one('[role=main]')
 for t in main.select('style,script,[hidden],[aria-hidden="true"]'):t.decompose()
 corpus=norm(main.get_text(' ',strip=True));indices=[i for i,c in enumerate(corpus) if c.isalpha()];letters=''.join(corpus[i] for i in indices);rows=[];checked=0
 for p in sorted((R/'pdf-pages'/m).glob('p*.ocr.json')):
  for b in json.loads(p.read_text()):
   t=b['text'];n=norm(t);a=''.join(c for c in n if c.isalpha())
   if not any(c.isdigit() for c in n) or len(a)<12:continue
   start=letters.find(a)
   if start<0:continue
   first=next(i for i,c in enumerate(n) if c.isalpha());last=max(i for i,c in enumerate(n) if c.isalpha());sn=n[first:last+1];wn=corpus[indices[start]:indices[start+len(a)-1]+1];sd=re.findall(r'\d+(?:\.\d+)?',sn);wd=re.findall(r'\d+(?:\.\d+)?',wn);checked+=1
   matches=[corpus[indices[j]:indices[j+len(a)-1]+1] for j in range(len(letters)) if letters.startswith(a,j)]
   if sd!=wd and not any(re.findall(r'\d+(?:\.\d+)?',match)==sd for match in matches):rows.append({'page':int(p.name[1:3]),'source':t,'web_context':wn,'source_numbers':sd,'web_numbers':wd})
 out={'model':m,'exact_letter_contexts_checked':checked,'numeric_differences':rows};(B/(m+'-number-copy.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
