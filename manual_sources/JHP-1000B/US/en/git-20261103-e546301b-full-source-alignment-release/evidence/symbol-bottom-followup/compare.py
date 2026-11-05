from pathlib import Path
import json,sys,hashlib
from PIL import Image,ImageChops
from bs4 import BeautifulSoup
r=Path('/private/tmp/manual-web-audit-20261102/symbol-bottom-followup')/sys.argv[1];p=Path((r/'package.txt').read_text());a=r/'before-web';b=r/'after-web';md=next(a.glob('manual_*.md')).name
texts=[]
for d in [a,b]:
 s=BeautifulSoup((d/md).read_text(),'html.parser')
 for tag in s.select('style'):tag.decompose()
 texts.append(str(s))
assert texts[0]==texts[1]
for f in (a/'assets').rglob('*'):
 if f.is_file():assert f.read_bytes()==(b/'assets'/f.relative_to(a/'assets')).read_bytes(),f
ir1=json.loads((a/'manual.ir.json').read_text());ir2=json.loads((b/'manual.ir.json').read_text());assert ir1['pages']==ir2['pages']
rows=[]
for f in sorted((r/'after-views').glob('view-*.png')):
 old=r/'before-views'/f.name;delta=ImageChops.difference(Image.open(old).convert('RGB'),Image.open(f).convert('RGB')).getbbox();rows.append({'file':f.name,'pixel_identical':delta is None,'changed_bbox':delta,'before_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
report={'model':sys.argv[1],'native_markdown_without_style_identical':True,'manual_ir_pages_identical':True,'all_asset_bytes_identical':True,'actual_instant_scroll_viewports':len(rows),'pixel_identical':sum(x['pixel_identical'] for x in rows),'rows':rows};(r/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(sys.argv[1],[x['file'] for x in rows if not x['pixel_identical']])
