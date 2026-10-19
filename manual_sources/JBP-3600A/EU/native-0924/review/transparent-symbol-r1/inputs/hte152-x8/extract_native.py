import json,hashlib,shutil
from pathlib import Path
import fitz
from PIL import Image,ImageDraw
out=Path('.tmp/intake-assist/transparent-symbol-review/hte152-x8')
src=Path('/Users/pika/Downloads/HTE152-EU-9国语言-0924.ai');sha=hashlib.sha256(src.read_bytes()).hexdigest()
assert sha=='d64624547e3b88fd1d8c3ea78f9e446f07e2364b148b707eb0d97ba4c24415de'
d=fitz.open(src);p=d[12];r=fitz.Rect(55.0467,160.1394,76.6242,171.7731);before=p.get_drawings()[70:80]
# Touch only the large table-background path, outside every icon. MuPDF preserves native compound path winding.
p.add_redact_annot(fitz.Rect(30,33,30.2,33.2),fill=False);p.apply_redactions(images=0,graphics=2,text=1)
after=[x for x in p.get_drawings() if x['rect'].intersects(r)]
assert len(after)==10
for a,b in zip(before,after):
 for key in ['items','fill','even_odd','fill_opacity','rect']:assert a[key]==b[key],key
n=fitz.open();q=n.new_page(width=r.width,height=r.height);q.show_pdf_page(q.rect,d,12,clip=r,keep_proportion=False)
name='connected-batteries-x8-transparent'
n.save(out/(name+'.pdf'),garbage=4,clean=True,deflate=True,no_new_id=True)
q.get_pixmap(matrix=fitz.Matrix(24,24),alpha=True).save(out/(name+'.png'))
q.get_pixmap(matrix=fitz.Matrix(12,12),alpha=True).save(out/'verification-12x.png')
(out/(name+'.svg')).write_text(q.get_svg_image())
im=Image.open(out/(name+'.png'));alpha=im.getchannel('A');assert alpha.getextrema()==(0,255)
# Verify both the battery cavity and the small internal rectangular hole are truly transparent.
for x,y in [(60,164.8),(60,168),(55.1,160.2)]:
 assert alpha.getpixel((int((x-r.x0)*24),int((y-r.y0)*24)))==0,(x,y)
canvas=Image.new('RGB',(1200,410),'#f8fafc');draw=ImageDraw.Draw(canvas)
for k,label in enumerate(['SOURCE / grey cell','EXTRACTED / transparent']):
 x=20+k*600;draw.text((x,18),label,fill='#111111')
 if k:
  for y in range(70,390,20):
   for xx in range(x,x+560,20):draw.rectangle((xx,y,xx+19,y+19),fill='#dfe5ed' if (xx//20+y//20)%2 else '#ffffff')
 img=Image.open(out/('source-crop.png' if k==0 else name+'.png')).convert('RGBA');canvas.paste(img,(x+20,90),img)
canvas.save(out/'before-after.png')
meta={'status':'candidate-not-enrolled','source':str(src),'source_sha256':sha,'physical_page':13,'printed_page':'06','icon_number':21,'source_label':'Connected Batteries','crop_pt':list(r),'retained_original_drawing_indices':list(range(70,80)),'removed_background_drawing':3,'background_touch_rect_pt':[30,33,30.2,33.2],'method':'Native PDF compound paths retained; remove touched backdrop outside icon, then clip. No path redraw, recolor or AI generation.','geometry_items_fill_rule_and_color_exact_before_after':True,'size':im.size,'alpha_extrema':alpha.getextrema(),'fully_transparent_pixels':sum(v==0 for v in alpha.get_flattened_data()),'interior_holes_transparent':True,'variant_note':'This user-supplied source has no outer capsule. Preserve as HTE152 variant, not equivalent to prior capsule drawing.','rejected_attempt':'retain_vector_drawings replay filled the inner rectangle due to rectangle winding; never enroll that output. Its recipe.json and extract.py are rejected diagnostics, not production recipe.','files':[{'file':name+suffix,'sha256':hashlib.sha256((out/(name+suffix)).read_bytes()).hexdigest()} for suffix in ['.pdf','.png','.svg']]}
(out/'evidence.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False,indent=2))
