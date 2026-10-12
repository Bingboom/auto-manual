from pathlib import Path
import json,hashlib,urllib.request,re
from bs4 import BeautifulSoup
root=Path('/Users/pika/.codex/worktrees/jbp3600a-en-intake/auto-manual2');base=root/'manual_sources/JBP-3600A/EU/native-0924';out=Path(__file__).resolve().parent
results=json.loads((base/'review/transparent-symbol-r1/results.json').read_text());asset=json.loads((base/'review/transparent-symbol-r1/asset-inventory.json').read_text());swaps={c['old']['sha256']:c['candidate']['sha256'] for c in asset['changes']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):
 for old,new in swaps.items():s=s.replace(old,new)
 return s
checks=[]
for c in results['candidates']:
 rev=c['revision'];lang=c['language'];oldrev=c['previous_revision'];d=base/'web'/rev;prev=base/'web'/oldrev
 manifest=json.loads((base/'review/transparent-symbol-r1'/rev/'package-manifest.json').read_text())
 for path,digest in manifest.items():assert sha(root/path)==digest,(rev,path)
 assert sha(d/'manual.ir.json')==c['ir_sha256']
 md=next(d.glob('manual*.md'));oldmd=next(prev.glob('manual*.md'));assert norm(oldmd.read_text())==md.read_text(),rev+' markdown unexpected delta'
 a=json.loads((prev/'manual.ir.json').read_text());b=json.loads((d/'manual.ir.json').read_text());assert [p['page_id']for p in a['pages']]==[p['page_id']for p in b['pages']]
 # Every visible Markdown byte is identical after the two explicitly approved-for-review hash substitutions.
 html=urllib.request.urlopen(c['preview']).read();assert hashlib.sha256(html).hexdigest()==c['html_sha256']
 (out/(rev+'.html')).write_bytes(html);(out/(rev+'.ir.json')).write_bytes((d/'manual.ir.json').read_bytes())
 soup=BeautifulSoup(html,'html.parser');imgs=soup.select('img');paths=[]
 for im in imgs:
  src=im.get('src','')
  if not src.startswith('assets/'):continue
  expected=Path(src).parts[2];assert sha(d/src)==expected,(rev,src)
  paths.append(expected)
 assert all(v in paths for v in swaps.values())
 assert asset['equipment_weee']['sha256'] in paths
 if lang!='en':assert asset['connection_icon']['jbp_x5_sha256'] in paths
 assert asset['connection_icon']['hte152_x8_sha256']not in paths
 oldassets={p.name:sha(p)for p in (prev/'assets').rglob('*')if p.is_file()};newassets={p.name:sha(p)for p in (d/'assets').rglob('*')if p.is_file()}
 diff={k:[oldassets.get(k),newassets.get(k)]for k in oldassets.keys()|newassets.keys()if oldassets.get(k)!=newassets.get(k)}
 assert set(diff)=={'symbol_warning.png','symbol_battery_weee.png'},(rev,diff)
 css=d/'_static/web_manual.css';assert sha(css)==c['stylesheet_sha256']
 checks.append({'language':lang,'revision':rev,'package_files_verified':len(manifest),'html_sha256':c['html_sha256'],'ir_sha256':c['ir_sha256'],'markdown_only_two_asset_substitutions':True,'images_verified':len(paths),'asset_changes':diff,'css_changed':c['stylesheet_sha256']!=c['previous_stylesheet_sha256']})
(out/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print([(c['revision'],c['package_files_verified'],c['images_verified'])for c in checks])
