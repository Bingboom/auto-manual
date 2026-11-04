from pathlib import Path
import fitz,pickle,json,sys,xml.etree.ElementTree as ET,copy
W=Path('/Users/hello-tech-team/.codex/worktrees/manual-warning-alignment/auto-manual-codex');sys.path.insert(0,str(W));from tools.asset_pipeline.native_svg import _drawing_paths,SVG
R=Path('/private/tmp/manual-web-audit-20261102/root-5000c');P=W/'manual_sources/JHP-5000C/US/en/git-20261103-3381c816-source-alignment-release';dr=pickle.loads((R/'draw-4.pickle').read_bytes());origin=dr[0]['rect'];root=ET.parse(R/'source04.svg').getroot();visible=[]
def collect(n,defs=False):
 defs=defs or n.tag==SVG+'defs'
 if not defs and n.tag==SVG+'path':visible.append(n)
 for c in n:collect(c,defs)
collect(root);mapped=_drawing_paths(dr,visible);print('verified SVG/source path mapping',len(mapped),flush=True)
# All PDF pages share the original Illustrator spread. Indices are invariant;
# each page differs only by a verified drawing-0 translation.
origins={4:(6784.0458984375,1.53515625),10:(4511.72265625,1.53515625),13:(3381.48193359375,1.53515625),14:(3004.47412109375,1.35546875),20:(750.87890625,.828125),27:(-1880.68359375,-.21875),28:(8289.642578125,1.53515625)}
# Resolve each selected page through its actual original Form matrix.
doc=fitz.open(P/'source/review-reference.pdf')
import re
matrices={}
for no in [4,11,15,24]:
 form=doc[no-1].get_xobjects()[0][0];raw=doc.xref_get_key(form,'Matrix')[1];matrices[no]=list(map(float,re.findall(r'[-+]?\d+(?:\.\d+)?',raw)))
for no in [11,15,24]:origins[no]=(origins[4][0]+matrices[no][4]-matrices[4][4],origins[4][1]-matrices[no][5]+matrices[4][5])
def translated_rect(no,b):return fitz.Rect(b)+tuple([origins[4][0]-origins[no][0],origins[4][1]-origins[no][1]]*2)
def inside(no,b):box=translated_rect(no,b);return [i for i,x in enumerate(dr) if box.contains(x['rect'])]
print('warning left',inside(4,[28,87,73,130]),flush=True)
print('plus',inside(20,[106,170,118,179]),flush=True)
# Source notes/structural frames only: live text and independent label pills excluded.
records=[
 ('source-risk-frame',4,[27.7,53.1,341.1,82.9],[102699,102787]),
 ('source-warning-frame',4,[28.2,87.3,180.5,128.7],sorted(set([99827]+inside(4,[28,87,73,130])))),
 ('source-danger-frame',4,[25.3,463.5,338.3,497.1],[103936,104158]),
 ('source-power-frame',10,[27.5,113,341.5,270.5],[94504,109185]),
 ('source-ac-frame',10,[27.5,297.4,341.5,482],[105268]),
 ('source-ups-frame',13,[28.4,243,340,402],[81861,81862,160863]),
 ('source-battery-frame',14,[28.3,149.3,342,283.4],[256617,256624]),
 ('source-sts-frame',14,[28.3,352.5,340,496.2],[115215,116005,160865]),
 ('source-package-host-frame',27,[26,164.7,338.2,274.7],[302003]),
 ('source-package-battery-frame',27,[26,276.9,338.2,359.1],[302004]),
 ('source-package-sts-frame',27,[26,361.3,338.2,497.1],[302005]),
 ('source-contact-frame',28,[27.7,459.3,300.9,496.9],[201998,202090]),
 ('source-app-plus',20,[106,170,118,179],inside(20,[106,170,118,179])),
]
for name,no,b in [('source-usb-frame',11,[27.5,43,341.5,154.8]),('source-dc-frame',11,[27.5,170,341.5,277.5]),('source-ac-charge-frame',15,[26.7,166.7,340.8,275.2]),('source-sts-charge-frame',15,[26.5,291.8,340.8,466.6]),('source-ess-frame',24,[30.3,111.6,340,387.6])]:
 ids=[i for i in inside(no,b) if dr[i]['rect'].width>300 and dr[i]['type']=='s' and dr[i]['rect'].height>70];assert len(ids)==1,(name,ids);records.append((name,no,b,ids))
records.append(('source-contact-qr',28,[305,459,343,497],inside(28,[305,459,343,497])))
# Include original gray sold-separately badges/cart marks; retain captions as native copy.
for q,(name,no,b,ids) in enumerate(records):
 if name in ['source-package-battery-frame','source-package-sts-frame']:
  bb=[267,299,338,335] if 'battery'in name else [266,447,340,485]
  textbox=translated_rect(27,([297,307,337,328] if 'battery'in name else [297,456,337,477]))
  records[q]=(name,no,b,sorted(set(ids+[i for i in inside(27,bb) if not textbox.contains(dr[i]['rect'])])))
for idx,nodes in enumerate(mapped):
 for node in nodes:node.set('data-pdf-drawing-index',str(idx))
full_figures=[('current-ups-art',13,[28.4,243,340,402],[[154,355.5,311,382]]),('current-battery-art',14,[28.3,149.3,342,283.4],[[113,268.5,164,277.5],[192,268.5,243,277.5]]),('current-sts-art',14,[28.3,352.5,340,496.2],[[154,369,302,393],[202,406,315,464]])]
for name,no,b,exclude in full_figures:
 boxes=[translated_rect(no,x) for x in exclude];ids=[i for i in inside(no,b) if not any(q.contains(dr[i]['rect']) for q in boxes)];records.append((name,no,b,ids))
allids={id(node) for _,_,_,ids in records for i in ids for node in mapped[i]}
def prune(n,keep):
 if n.tag==SVG+'defs':return copy.deepcopy(n)
 if n.tag==SVG+'path':return copy.deepcopy(n) if id(n) in keep else None
 if n.tag not in [SVG+'svg',SVG+'g']:return None
 out=ET.Element(n.tag,n.attrib)
 for c in n:
  q=prune(c,keep)
  if q is not None:out.append(q)
 return out if len(out) else None
# prune once while preserving every source path's original transforms/clip ancestors.
minimal=prune(root,allids)
# IDs are changed by deepcopy: path identity use exact original serialized bytes.
keys={i:{tuple(sorted(x.attrib.items())) for x in mapped[i]} for _,_,_,ids in records for i in ids}
def small(n,keep):
 if n.tag==SVG+'defs':return copy.deepcopy(n)
 if n.tag==SVG+'path':return copy.deepcopy(n) if tuple(sorted(n.attrib.items())) in keep else None
 out=ET.Element(n.tag,n.attrib)
 for c in n:
  q=small(c,keep)
  if q is not None:out.append(q)
 return out if len(out) else None
proof=[]
for name,no,b,ids in records:
 assert ids,(name,'empty');s=small(minimal,{key for i in ids for key in keys[i]});box=translated_rect(no,b);s.set('viewBox',f'{box.x0} {box.y0} {box.width} {box.height}');
 for g in s.iter():
  if g.get('clip-path')=='url(#clip_1)':g.attrib.pop('clip-path')
 s.set('width',str(box.width));s.set('height',str(box.height));ET.register_namespace('','http://www.w3.org/2000/svg');dest=P/'assets'/f'{name}.svg';dest.write_bytes(ET.tostring(s,encoding='utf-8',xml_declaration=True));proof.append({'asset':dest.name,'current_pdf_page':no,'bbox':b,'drawing_indices':ids,'source_svg_page':4,'source_svg_translation':[box.x0-b[0],box.y0-b[1]],'viewport_clip':'Original page-4 viewport clip_1 removed; this asset root viewBox is the requested current source crop. All artwork-internal clips retained.', 'method':'Exact original SVG paths, ancestor transforms and internal clips; no new drawing commands. Shared spread drawing index equality and translation verified.'});print(name,len(dest.read_bytes()),ids,flush=True)
(P/'source/structural-art-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
