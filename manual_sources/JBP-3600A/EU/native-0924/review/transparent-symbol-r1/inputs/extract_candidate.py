from pathlib import Path
import fitz,json,hashlib,shutil
from PIL import Image
out=Path('.tmp/intake-assist/transparent-symbol-review');src=Path('/Users/pika/Downloads/HTP011-EU-9国语言-0924.ai');doc=fitz.open(src);page=doc[22];bounds=fitz.Rect(36.5,330.5,60.2,351.8);paths=page.get_drawings();dest=fitz.open();p=dest.new_page(width=bounds.width,height=bounds.height)
def pt(a):return fitz.Point(a.x-bounds.x0,a.y-bounds.y0)
for index in (906,907):
 d=paths[index];assert bounds.contains(d['rect']);shape=p.new_shape()
 for item in d['items']:
  if item[0]=='l':shape.draw_line(pt(item[1]),pt(item[2]))
  elif item[0]=='c':shape.draw_bezier(*[pt(a) for a in item[1:]])
  else:raise ValueError(item[0])
 shape.finish(fill=d['fill'],color=d['color'],even_odd=d['even_odd'],closePath=d['closePath'],fill_opacity=d['fill_opacity']);shape.commit()
pdf=out/'warning-triangle-transparent.pdf';dest.save(pdf)
p.get_pixmap(matrix=fitz.Matrix(24,24),alpha=True).save(out/'warning-triangle-transparent.png')
# Reuse existing transparent artwork, without altering originals.
rep=Path('manual_sources/JE-1000H/EU/three-language/git-20260930-8bcb378f-intake/artwork/shared/lcd-connected-batteries.pdf')
r=fitz.open(rep);r[0].get_pixmap(matrix=fitz.Matrix(24,24),alpha=True).save(out/'connected-batteries-x8-source-variant.png')
shutil.copyfile('docs/templates/word_template/common_assets/symbols/weee2.png',out/'weee2-transparent.png')
records=[]
for f in out.glob('*.png'):
 im=Image.open(f);a=im.getchannel('A');records.append({'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size':im.size,'alpha_extrema':a.getextrema(),'transparent_pixels':sum(1 for v in a.getdata() if v==0)})
(out/'evidence.json').write_text(json.dumps({'status':'candidate-not-approved','warning_source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'physical_page':23,'drawing_indices':[906,907],'excluded_background_indices':[896,905],'reason':'896 is cell backdrop;905 is triangle interior shade with parent SVG opacity0.199997; retain original outline906 and exclamation907','bounds':list(bounds),'x8_source':str(rep),'x8_boundary':'native outlined-digit source variant; outer capsule differs from rejected low-res sample, not an automatic replacement','art':records},indent=2));print(records)
