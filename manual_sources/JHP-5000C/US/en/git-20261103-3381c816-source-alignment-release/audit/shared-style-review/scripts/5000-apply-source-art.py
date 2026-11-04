from pathlib import Path
import json,hashlib,sys,os,xml.etree.ElementTree as ET
from copy import deepcopy
W=Path('/Users/hello-tech-team/.codex/worktrees/manual-warning-alignment/auto-manual-codex');P=W/'manual_sources/JHP-5000C/US/en/git-20261103-3381c816-source-alignment-release';sys.path.insert(0,str(W))
from tools.manual_ir.flow import flow_nodes_to_html,html_to_flow_nodes
from tools.manual_ir.components import component_spec_from_flow_node
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection
from tools.web.reference_figure_component import _component_contract
from tools.web.composite_presentation import WebCompositeContext
from tools.web.presentation import _transform_reference_figure
from bs4 import BeautifulSoup
S='{http://www.w3.org/2000/svg}';d=json.loads((P/'source/en/content.json').read_text());newassets=[]
def a(n):return n.setdefault('presentation',{}).setdefault('html',{}).setdefault('attributes',{})
def grp(ch,at):return {'kind':'group','role':'container','children':ch,'presentation':{'html':{'attributes':at}}}
def img(path,at):return {'kind':'image','source':path,'alt':'','presentation':{'html':{'attributes':at}}}
def bind(n,asset,rects=None,remove_fill=False):
 s=n['component_spec'];old=s['assets'][0]['asset_ref'];s['assets'][0]['asset_ref']=asset;layout=s['metadata']['base_art_layout'];layout['art_sha256']=hashlib.sha256((P/asset).read_bytes()).hexdigest();n['carrier_flow'][0]['source']=asset
 if rects:
  assert len(rects)==len(layout['labels']),(s['source_ref'],len(rects),len(layout['labels']))
  for l,r in zip(layout['labels'],rects):l['rect']=r
 if remove_fill:
  for l in layout['labels']:l.pop('fill',None)
 # Regenerate real source-fragment hash from this exact modified carrier.
 spec=component_spec_from_flow_node(n);payload=web_reference_figure_projection(spec);payload.update(capture_following_lines=s['metadata']['capture_following_lines'],captions_origin='carrier',composite_locale='');contract=_component_contract(payload);soup=BeautifulSoup(flow_nodes_to_html([{**x,'schema_version':'manual-flow/v2'} for x in n['carrier_flow']]),'html.parser');_transform_reference_figure(soup,image=soup.find('img'),spec=contract,source_path=Path('source/en/content.json'),composites=WebCompositeContext(None,'JHP-5000C','US','en',ValueError));s['metadata']['source_fragment_sha256']=soup.find('figure')['data-source-fragment-sha256'];newassets.append(asset)
def composite(old,frame,out):
 root=ET.parse(P/old).getroot();w,h=[float(x) for x in root.get('viewBox').split()][2:];top=ET.Element(S+'svg',{'viewBox':f'0 0 {w} {h}','width':str(w),'height':str(h)});back=ET.parse(P/frame).getroot();back.set('width',str(w));back.set('height',str(h));back.set('preserveAspectRatio','none');root.set('width',str(w));root.set('height',str(h));
 def prefix(tree,tag):
  ids={x.get('id'):tag+x.get('id') for x in tree.iter() if x.get('id')}
  for x in tree.iter():
   for k,v in list(x.attrib.items()):
    if k=='id':x.set(k,ids[v])
    else:
     for old,new in ids.items():v=v.replace('url(#'+old+')','url(#'+new+')');v=('#'+new) if v=='#'+old else v
     x.set(k,v)
 prefix(back,'source-frame-');prefix(root,'accepted-art-');top.extend([back,root]);ET.register_namespace('','http://www.w3.org/2000/svg');(P/out).write_bytes(ET.tostring(top,encoding='utf-8',xml_declaration=True));return out
os.chdir(P)
frames={'power':'source-power-frame','ac-output':'source-ac-frame','package-host':'source-package-host-frame','package-battery':'source-package-battery-frame','package-sts':'source-package-sts-frame'}
newfull={'ups':'current-ups-art','battery-packs':'current-battery-art','sts-connect':'current-sts-art'}
def rect(b,box):return [(b[0]-box[0])*100/(box[2]-box[0]),(b[1]-box[1])*100/(box[3]-box[1]),(b[2]-b[0])*100/(box[2]-box[0]),(b[3]-b[1])*100/(box[3]-box[1])]
def walk(n):
 if not isinstance(n,dict):return
 at=a(n)
 if 'data-source-card'in at:
  role=at['data-source-card'];n['children']=[img(f'assets/source-{role}-frame.svg',{'data-source-frame':role}),n['children'][1]]
 if n.get('kind')=='inline_group' and 'native-inline-plus' in at.get('data-source-role',''):
  n.clear();n.update(img('assets/source-app-plus.svg',{'data-source-inline-symbol':'plus'}));return
 if n.get('kind')=='component' and n['component_spec']['component_id']=='HB-SPECIAL-REFERENCE-FIGURE':
  s=n['component_spec'];rid=next(x['content'] for x in s['slots'] if x['role']=='reference_id')
  if rid in frames:
   asset=composite(s['assets'][0]['asset_ref'],'assets/'+frames[rid]+'.svg','assets/'+rid+'-source-framed.svg');bind(n,asset,remove_fill=rid=='power')
  if rid in newfull:
   if rid=='ups':rr=[rect([157,357,311,383],[28.4,243,340,402])]
   elif rid=='battery-packs':rr=[rect(b,[28.3,149.3,342,283.4]) for b in [[114,269,165,278],[193,269,244,278]]]
   else:
    lines=next(x['content'] for x in s['slots'] if x['role']=='captions');print('sts captions',len(lines),[x['text'] for x in lines]);rr=[rect([155,369,313,395],[28.3,352.5,340,496.2])]+[rect([204,406+i*6.95,316,413+i*6.95],[28.3,352.5,340,496.2]) for i in range(len(lines)-1)]
   bind(n,'assets/'+newfull[rid]+'.svg',rr,True)
  return
 for x in n.get('children',[]):walk(x)
for c in d['chapters']:
 for n in c['nodes']:walk(n)
c=next(c for c in d['chapters'] if c['id']=='safety');danger=c['nodes'][-1];cells=danger['carrier_flow'][0]['children'][0]['children'][0]['children'];c['nodes'][-1]={**grp([img('assets/source-danger-frame.svg',{'data-source-frame':'danger'}),{'kind':'paragraph','children':[{'kind':'strong','children':[{'kind':'text','text':'DANGER'}]}],'presentation':{'html':{'attributes':{'data-source-copy':'danger-label'}}}},grp(cells[1]['children'],{'data-source-copy':'danger-body'})],{'data-source-card':'danger'}),'schema_version':'manual-flow/v2'}
# Contact source frame, original icon/QR assets and native text.
c=next(c for c in d['chapters'] if c['id']=='contact');card=c['nodes'][0];panel=card['children'][2]['children'][0];panel['children'].insert(0,img('assets/source-contact-frame.svg',{'data-source-contact-frame':'true'}))
(P/'source/en/content.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
css='''
/* The native source SVGs carry source structural lines, badges and pointer shapes. */
#furo-main-content [data-source-card] {isolation:isolate;}
#furo-main-content [data-source-frame] {position:absolute;inset:0;width:100%!important;height:100%!important;max-height:none;z-index:-1;margin:0!important;object-fit:fill;}
#furo-main-content [data-source-card="risk"] {min-height:3rem;padding:.4rem .6rem .4rem 12%;}
#furo-main-content [data-source-card="warning"] {min-height:5rem;padding:.4rem .5rem .4rem 32%;}
#furo-main-content [data-source-card="danger"] {min-height:4rem;padding:.4rem .6rem;display:grid;grid-template-columns:24% 1fr;gap:.6rem;}
#furo-main-content [data-source-copy="danger-label"] {padding-left:28%;font-size:1.2rem;}
#furo-main-content [data-source-copy="danger-body"] {font-size:.75rem;}
#furo-main-content [data-source-inline-symbol="plus"] {display:inline-block;width:.9em!important;height:.9em!important;margin:0 .2em!important;vertical-align:baseline;}
#furo-main-content [data-source-role~="native-contact-panel"] {position:relative;isolation:isolate;}
#furo-main-content [data-source-contact-frame] {position:absolute;inset:0;width:100%!important;height:100%!important;max-height:none;z-index:-1;margin:0!important;object-fit:fill;}
#furo-main-content [data-source-role~="native-ups"] .hb-reference-live-label {font-size:1.55cqw!important;line-height:1.25;}
#furo-main-content [data-source-role~="native-sts-connect"] .hb-reference-live-label {font-size:1.55cqw!important;line-height:1.2;}
@media(max-width:640px){#furo-main-content [data-source-card="risk"] {min-height:3rem;}#furo-main-content [data-source-card="danger"] {min-height:5rem;}#furo-main-content [data-source-copy="danger-label"] {font-size:.9rem;}#furo-main-content [data-source-copy="danger-body"] {font-size:.65rem;}}
'''
with (P/'source/presentation.css').open('a') as f:f.write(css)
mf=P/'source_manifest.json';m=json.loads(mf.read_text());paths={x['path'] for x in m['inputs']}
for path in [*(str(x.relative_to(P)) for x in (P/'assets').glob('source-*.svg')),*(str(x.relative_to(P)) for x in (P/'assets').glob('current-*.svg')),*newassets,'source/structural-art-provenance.json']:
 if path not in paths:b=(P/path).read_bytes();m['inputs'].append({'path':path,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()});paths.add(path)
mf.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
