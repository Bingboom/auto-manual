from pathlib import Path
import fitz,json,hashlib
from derive_assets import render_panel
p=Path(__file__).resolve().parent;d=fitz.open(p/'JHP-2000A-RC-US-en-V2.pdf');proof=[]
rows=[
('risk-strip',4,[27.75,54.21,341.46,84.23],[[61,60,118,79],[132,59,338,80]]),
('ground-strip',5,[29.01,26.63,341.42,64.46],[[57,39,114,53],[116,29,337,61]]),
('danger-strip',5,[29.01,67.48,341.42,98.47],[[58,78,108,90],[114,70,339,97]]),
('source-signal-glyph',5,[39.5,196.5,49.5,205.5],[]),
('source-clock',14,[161.5,260.4,173,272.3],[]),
('back-contact-base',24,[27,459,343,497],[[57,468,195,494],[221,467,296,479],[221,479,296,491]])]
for name,page,bbox,strips in rows:
 with fitz.open() as one:
  one.insert_pdf(d,from_page=page-1,to_page=page-1);pg=one[0]
  for box in strips:pg.add_redact_annot(fitz.Rect(box),fill=False)
  if strips:pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,text=fitz.PDF_REDACT_TEXT_NONE,graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
  out=p/'assets'/(name+'.png');pg.get_pixmap(matrix=fitz.Matrix(5,5),clip=fitz.Rect(bbox),alpha=False).save(out)
  proof.append({'path':'assets/'+name+'.png','physical_page':page,'bbox':bbox,'strip':strips,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operation':'Own PDF crop; only declared prose paths removed, original frame/icon preserved; corresponding text native HTML.'})
a=json.loads((p/'source/asset_recipe.json').read_text())
for panel in a['panels']:
 if Path(panel['path']).stem in ['power-on-off','ac-output','dc-usb-output','energy-saving','led-light','ups','charging-ac','battery-stack','charging-solar','charging-car']:
  out=p/panel['path'];render_panel(d,panel,fitz.Matrix(a['panel_scale'],a['panel_scale'])).save(out)
  proof.append({'path':panel['path'],'physical_page':panel['physical_page'],'bbox':panel['bbox'],'strip':panel.get('strip',[]),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operation':'Own PDF frame bounds restored, declared prose removed and native HTML copy at source coordinates.'})
(p/'source/restored-artwork.json').write_text(json.dumps(proof,indent=2)+'\n')
