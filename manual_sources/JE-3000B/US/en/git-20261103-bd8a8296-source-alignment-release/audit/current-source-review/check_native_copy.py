from pathlib import Path
from bs4 import BeautifulSoup
import json,re,unicodedata,sys
P=Path(sys.argv[1]);H=Path(sys.argv[2]);out=Path(sys.argv[3]);d=json.loads((P/'source/en/content.json').read_text());s=BeautifulSoup(H.read_text(),'html.parser');m=s.select_one('[role=main]')
for n in m.select('[hidden],[aria-hidden="true"],style,script'):n.decompose()
def norm(x):return re.sub(r'\W','',unicodedata.normalize('NFKC',x).lower())
corpus=norm(m.get_text(' '));checks=[]
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if isinstance(v,str) and (k=='text' or k.endswith('_text')) and len(norm(v))>=3:checks.append(v)
   else:walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(d);missing=[v for v in checks if norm(v) not in corpus and not (re.match(r'^1\. ',v) and norm(re.sub(r'(?:^| )\d+\. ', ' ', v)) in corpus)];report={'checked_native_fragments':len(checks),'missing':missing};out.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(bool(missing))
