"""Restore this PDF's native text/figure pairing without changing shared renderers."""
from tools.web.frozen_ai_flow import node,root,text
from tools.component_specs.manual_tables import symbol_icon_component_spec
from tools.manual_ir.components import component_flow_node
import fitz,json
from bs4 import BeautifulSoup
from tools.component_specs.model import ComponentSpec
from tools.manual_ir.flow import flow_nodes_to_html,html_to_flow_nodes
from tools.web.spec_component import render_specification_component
from tools.web.prepared_style_audit import table_text_sha256

def g(key,children,css='docutils container'):
 return node('group',children,role='container',presentation={'html':{'attributes':{'class':css,'data-source-layout':key}}})
def im(path):return node('image',source='assets/'+path,alt='')
def para(value):return node('paragraph',[text(value)])
def slots(spec):return {x['role']:x['content']for x in spec['slots']}
def carrier_cells(n):return n['carrier_flow'][0]['children'][0]['children'][0]['children']
def source_art(p):
 doc=fitz.open(p/'JE-2000F-US-EN.pdf');recipes=[]
 # Rectangles are measured on the retained 850px-wide original-page renders.
 for name,page,box in [('source-risk',4,(77,126,128,173)),('source-warning',4,(77,207,149,272)),('source-triangle',5,(70,83,117,126)),('contact-phone',22,(82,1083,128,1129)),('contact-mail',22,(481,1083,505,1104)),('contact-web',22,(480,1107,508,1131)),('contact-qr',22,(710,1068,784,1142))]:
  pg=doc[page-1];scale=pg.rect.width/850;rect=fitz.Rect(*[v*scale for v in box]);dest=p/'assets'/f'{name}.png';pg.get_pixmap(matrix=fitz.Matrix(4,4),clip=rect,alpha=False).save(dest);recipes.append({'path':'assets/'+dest.name,'physical_page':page,'bbox_pdf_points':list(rect),'operation':'exact source clip; no redraw'})
 (p/'source/layout-assets.json').write_text(json.dumps(recipes,indent=2)+'\n')
def restore(content,p):
 source_art(p);chap={x['id']:x for x in content['chapters']};n=chap['safety']['nodes'];basic=carrier_cells(n[2]);label=basic[0]['children'];body=basic[1]['children'];n[1]=root(g('risk-title',[im('source-risk.png'),n[1]]));warning=g('warning-with-icon',[im('source-warning.png'),g('warning-title',[para('WARNING'),*body[:1]])]);n[2]=root(g('safety-columns',[warning,*body[1:]]));n[4:6]=[root(g('operating-columns',n[4:6]))]
 for i,x in enumerate(n):
  if x.get('component_spec',{}).get('source_ref')in['native-pdf/page-5/grounding-warning','native-pdf/page-5/danger']:
   cells=carrier_cells(x);n[i]=root(g('source-warning-strip',[g('warning-label',[im('source-triangle.png'),*cells[0]['children']]),g('warning-copy',cells[1]['children'])],'manual-callout-body docutils container'))
 # Keep the five-row right symbol panel and separate full-width battery-disposal box.
 n=chap['symbols']['nodes'];old=n[2]['component_spec'];ss=slots(old);panels=ss['panels'];last=panels[1].pop();refs=[x['path']if'path'in x else x.get('ref')for x in old['assets']]
 # Asset references in component specs are resolved URI strings.
 refs=[x.get('ref',x.get('path',x.get('asset_ref'))) for x in old['assets']]
 if any(x is None for x in refs):refs=['assets/symbol-'+f'{i:02d}'+('.svg'if i<=10 else'.png')for i in range(1,13)]
 spec=symbol_icon_component_spec(accessibility_label=ss['accessibility_label'],headers=ss['headers'],panels=panels,icon_refs=refs[:11],source_ref='native-pdf/page-5/symbols',language='en',icon_locale_policy='exact');n[2]=component_flow_node(spec,root=True);n.insert(3,root(g('battery-disposal',[im('symbol-12.png'),g('battery-copy',[para(s)for s in last['meaning_html'].split('<br/>')])], 'hb-text-panel docutils container')))
 # Original black circular badges are native text above each own-source image.
 n=chap['in_the_box']['nodes'];ss=slots(n[1]['component_spec']);cards=ss.get('cards',[])
 if cards:
  parts=[]
  for i,c in enumerate(cards):
   ref=c.get('image_ref');ref=ref or ['assets/inbox-unit.png','assets/inbox-ac-cable.svg','assets/inbox-usb-c-cable.svg','assets/inbox-documents.svg'][i]
   card=g('inbox-card',[node('image',source=ref,alt=c.get('alt','')),para(c['label'])],'hb-inbox-card docutils container');card['presentation']['html']['attributes']['data-item-number']=str(i+1);parts.append(card)
  tip=n[1]['carrier_flow'][1]['children'][0]['children'][0]['children'];n[1:2]=[root(g('inbox-four',parts)),root(g('inbox-tip',[g('tip-label',tip[0]['children']),g('tip-copy',tip[1]['children'])],'hb-text-panel docutils container'))]
 chap['lcd_display']['nodes'][2]['component_spec'].setdefault('metadata',{})['number_cell_layout']='span-adjacent-equal'
 # Own PDF specification groups are subsection headings, not chapter title strips.
 exceptions=[];specnodes=[]
 for n in chap['specifications']['nodes']:
  if n.get('component_spec',{}).get('component_id')=='HB-TABLE-SPEC':
   html=render_specification_component(ComponentSpec.from_dict(n['component_spec']),flow_nodes_to_html([root(v)for v in n['carrier_flow']]));soup=BeautifulSoup(html,'html.parser');soup.find('h2').name='h3'
   for el in soup.select('.manual-spec-value'):el['class']=[c for c in el.get('class',[])if c!='manual-spec-value']
   converted=html_to_flow_nodes(str(soup))
   def find_tables(x):
    if x.get('kind')=='table':yield x
    for v in x.get('children',[]):yield from find_tables(v)
   for v in converted:
    for tab in find_tables(v):exceptions.append({'language':'en','page_id':'specifications','kind':'table','text_sha256':table_text_sha256(tab),'reason':'Exact shared specification table projection retained with source p18 subsection heading level. HB-TABLE-SPEC emits a chapter heading strip, unlike this source; native editable table keeps the same source cells and shared theme classes.'})
   specnodes.extend(root(v)for v in converted)
  else:specnodes.append(n)
 chap['specifications']['nodes']=specnodes
 manifest=json.loads((p/'source_manifest.json').read_text());manifest['shared_component_exceptions']=exceptions;(p/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 # Native source text occupies its original space inside the stripped source figure.
 n=chap['operations']['nodes'];out=[];i=0
 while i<len(n):
  x=n[i];ref=x.get('component_spec',{}).get('source_ref','')
  if ref.endswith('/power-on-off'):
   out.append(root(g('panel-scroll',[g('power-panel',[x,g('power-standby',n[i+1]['children'],'hb-text-panel docutils container'),g('power-note',[n[i+2]])])])));i+=3;continue
  if x.get('presentation',{}).get('html',{}).get('attributes',{}).get('class')=='hb-text-panel' and i+1<len(n):
   nextref=n[i+1].get('component_spec',{}).get('source_ref','')
   if nextref.endswith(('/ac-output','/dc-usb-output')):
    out.append(root(g('panel-scroll',[g('output-panel',[n[i+1],g('prerequisite',x['children'],'hb-text-panel docutils container')])])));i+=2;continue
   if nextref.endswith('/led-light'):
    steps=n[i+2]['children'];out.append(root(g('panel-scroll',[g('led-panel',[n[i+1],g('led-modes',x['children'],'hb-text-panel docutils container'),*[g('led-step-'+str(j+1),v['children'])for j,v in enumerate(steps)]])])));i+=3;continue
   if nextref.endswith('/energy-saving'):
    out.append(root(g('panel-scroll',[g('energy-panel',[n[i+1],g('energy-copy',x['children'],'hb-text-panel docutils container')])])));i+=2;continue
  out.append(x);i+=1
 chap['operations']['nodes']=out
 n=chap['charging']['nodes'];n[2]['presentation']={'html':{'attributes':{'class':'hb-sold-separately'}}};i=next(i for i,x in enumerate(n)if x.get('component_spec',{}).get('source_ref','').endswith('/charging-ac'));n[i:i+2]=[root(g('panel-scroll',[g('charging-panel',[n[i],g('charging-caption',n[i+1]['children'])])]))]
 content['chapters'].append({'id':'source_back_contact','title':'','nodes':[root(g('source-back-contact',[node('paragraph',[node('strong',[text('JACKERY INC.')])]),para('5310 Bunche Dr., Fremont, CA 94538-8301'),g('back-contact-pair',[g('contact-strip',[g('contact-phone',[im('contact-phone.png'),para('1-888-502-2236 (US)')]),g('contact-address',[g('contact-item',[im('contact-mail.png'),para('hello@jackery.com')]),g('contact-item',[im('contact-web.png'),para('www.jackery.com')])])],'hb-text-panel docutils container'),im('contact-qr.png')])]))]})
 def clean(n):
  for child in n.get('children',[]):
   child.pop('schema_version',None);clean(child)
 for ch in content['chapters']:
  for n in ch['nodes']:clean(n)
 return content
