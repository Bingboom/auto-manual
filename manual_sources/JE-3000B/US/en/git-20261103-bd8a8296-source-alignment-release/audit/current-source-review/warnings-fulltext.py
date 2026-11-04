import pathlib,json,re,unicodedata,difflib,sys
from bs4 import BeautifulSoup
R=pathlib.Path('/private/tmp/manual-web-audit-20261102'); model=sys.argv[1]; html=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3])
def norm(t):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKC',t).lower())
soup=BeautifulSoup(html.read_text(),'html.parser');main=soup.select_one('[role=main]');
for t in main.select('style,script,[hidden],[aria-hidden="true"]'):t.decompose()
corpus=norm(main.get_text(' ',strip=True));grams={corpus[i:i+8] for i in range(len(corpus)-7)}
rows=[];count=0
for page in sorted((R/'pdf-pages'/model).glob('p*.ocr.json')):
 pn=int(page.name[1:3]);
 if pn in [1,3]:continue
 for block in json.loads(page.read_text()):
  text=block['text'];s=norm(text)
  if len(s)<15:continue
  count+=1; score=sum(s[i:i+8] in grams for i in range(len(s)-7))/(len(s)-7)
  if score<.65:rows.append({'page':pn,'text':text,'coverage':round(score,3)})
report={'model':model,'source_pages':len(list((R/'pdf-pages'/model).glob('p*.ocr.json'))),'checked_lines':count,'exclusions':{'1':'historically approved print cover','3':'historically approved print TOC'},'candidates':rows};out.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
