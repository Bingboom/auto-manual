from pathlib import Path
import fitz,json,hashlib
p=Path(__file__).resolve().parent;d=fitz.open(p/'JHP-1000B-US-en-V2.pdf')
# Original source-space artwork only. All surrounding prose remains native flow.
rows=[('source-warning-dark',5,[33,34,53,52]),('source-warning-light',4,[33,100,60,125]),('back-qr',22,[307,462,339,493]),('contact-phone',22,[33,469,56,493]),('contact-mail',22,[207,469,220,479]),('contact-web',22,[207,479,220,491])]
proof=[]
for name,page,bbox in rows:
 out=p/'assets'/f'{name}.png';d[page-1].get_pixmap(matrix=fitz.Matrix(5,5),clip=fitz.Rect(bbox),alpha=False).save(out);proof.append({'path':f'assets/{name}.png','physical_page':page,'bbox':bbox,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operation':'Direct original PDF crop; no reconstruction'})
(p/'source/restored-artwork.json').write_text(json.dumps(proof,indent=2)+'\n')

with fitz.open() as one:
    one.insert_pdf(d,from_page=3,to_page=3)
    pg=one[0]
    pg.add_redact_annot(fitz.Rect(73,98,176,133),fill=False)
    pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,text=fitz.PDF_REDACT_TEXT_NONE,graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
    pg.get_pixmap(matrix=fitz.Matrix(5,5),clip=fitz.Rect(26,95,178,136),alpha=False).save(p/'assets/source-warning-card.png')

d[4].get_pixmap(matrix=fitz.Matrix(8,8),clip=fitz.Rect(37,195,47.5,204.5),alpha=False).save(p/'assets/source-signal-glyph.png')

d[12].get_pixmap(matrix=fitz.Matrix(8,8),clip=fitz.Rect(158,151.5,169.5,163),alpha=False).save(p/"assets/source-clock.png")

for name,page,bbox,strip in [('source-warning-card',4,[26,95,178,136],[[73,98,176,133]]),('source-signal-glyph',5,[37,195,47.5,204.5],[]),('source-clock',13,[158,151.5,169.5,163],[])]:
    proof.append({'path':'assets/'+name+'.png','physical_page':page,'bbox':bbox,'strip':strip,'sha256':hashlib.sha256((p/'assets'/(name+'.png')).read_bytes()).hexdigest(),'operation':'Original PDF crop; card text vectors removed only within declared strip, no reconstruction or overpaint'})
(p/'source/restored-artwork.json').write_text(json.dumps(proof,indent=2)+'\n')

with fitz.open() as one:
    one.insert_pdf(d,from_page=21,to_page=21)
    pg=one[0]
    strips=[[57,467,202,494],[220,468,299,479],[220,479,299,491]]
    for box in strips:pg.add_redact_annot(fitz.Rect(box),fill=False)
    pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,text=fitz.PDF_REDACT_TEXT_NONE,graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
    out=p/'assets/back-contact-base.png'
    pg.get_pixmap(matrix=fitz.Matrix(5,5),clip=fitz.Rect(27,460,342,498),alpha=False).save(out)
    proof.append({'path':'assets/back-contact-base.png','physical_page':22,'bbox':[27,460,342,498],'strip':strips,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operation':'Retain original contact frames, icons and QR. Delete only source body text vectors and render those words as native HTML at source positions.'})
(p/'source/restored-artwork.json').write_text(json.dumps(proof,indent=2)+'\n')

for name,page,bbox,strips in [('risk-strip',4,[26,55,338,85],[[56,59,116,81],[118,58,335,83]]),('danger-strip',5,[26,27,338,61],[[55,35,108,54],[111,29,335,59]])]:
    with fitz.open() as one:
        one.insert_pdf(d,from_page=page-1,to_page=page-1)
        pg=one[0]
        for box in strips:pg.add_redact_annot(fitz.Rect(box),fill=False)
        pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,text=fitz.PDF_REDACT_TEXT_NONE,graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
        out=p/'assets'/(name+'.png');pg.get_pixmap(matrix=fitz.Matrix(5,5),clip=fitz.Rect(bbox),alpha=False).save(out)
        proof.append({'path':'assets/'+name+'.png','physical_page':page,'bbox':bbox,'strip':strips,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operation':'Original warning strip frame and icon retained. Source body/label paths removed; the same source strings are native overlay.'})
(p/'source/restored-artwork.json').write_text(json.dumps(proof,indent=2)+'\n')

# Final own-PDF frame bounds and complete right-view outline, verified visually.
from derive_assets import render_panel
recipe=json.loads((p/'source/asset_recipe.json').read_text())
for panel in recipe['panels']:
    if Path(panel['path']).stem in ['overview-right', 'power-on-off', 'ac-output', 'dc-usb-output', 'led-light', 'energy-saving', 'charging-ac', 'lcd-screen']:
        out=p/panel['path'];render_panel(d,panel,fitz.Matrix(recipe['panel_scale'],recipe['panel_scale'])).save(out)
        proof.append({'path':panel['path'],'physical_page':panel['physical_page'],'bbox':panel['bbox'],'strip':panel.get('strip',[]),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operation':'Re-crop this source PDF to retain full product outline and complete original frame; declared text strips only, native copy elsewhere.'})
(p/'source/restored-artwork.json').write_text(json.dumps(proof,indent=2)+'\n')
