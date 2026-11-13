"""Restore omitted back-cover contact information; historical scope excludes the front cover.
Generated only from source/cover-contact.json and exact source crop assets.
Run by the source builder; no network, no inferred product information.
"""
from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]
c=json.loads((p/'source/cover-contact.json').read_text())
f=p/'source/en/content.json';d=json.loads(f.read_text());schema=d['chapters'][0]['nodes'][0]['schema_version']
def node(k,children=(),**kw):
 n={'kind':k,**kw}
 if k not in ['text','image']:n['children']=list(children)
 return n
def text(t):return node('text',text=t)
def para(t):return node('paragraph',[text(t)])
def group(ch,kind):return node('group',ch,role='container',presentation={'html':{'attributes':{'class':'docutils container','data-source-layout':kind}}})
def root(n):n['schema_version']=schema;return n
d['chapters']=[x for x in d['chapters'] if x['id'] not in ['source_cover','source_back_contact']]
if c['back_copy'] or c['back_qr']:
 ch=[para(t) for t in c['back_copy']]
 if c['back_qr']:ch.append(node('image',source='assets/back-contact-qr.png',alt='Jackery contact QR code from source back cover'))
 d['chapters'].append({'id':'source_back_contact','title':'JACKERY INC.','pages':[c['last_page']],'nodes':[root(group(ch,'source-back-contact'))]})
# Original safety boxes: icon at left, signal word above the paired body at right.
def restore_safety(item):
 spec=item.get('component_spec',{})
 if spec.get('variant')=='danger' and spec.get('component_id')=='HB-CALLOUT-STRIP':
  slots={x['role']:x['content'] for x in spec['slots']};version=item.get('schema_version')
  label=slots['label']+(':' if c.get('danger_colon') else '')
  replacement=group([node('image',source='assets/safety-risk-triangle.png',alt='Danger'),node('paragraph',[node('strong',[text(label)])]),para(slots['body'])],'danger-box')
  if version:replacement['schema_version']=version
  item.clear();item.update(replacement)
 attrs=item.get('presentation',{}).get('html',{}).get('attributes',{})
 if attrs.get('data-source-layout')=='warning-with-icon':
  item['children'][0]['source']='assets/safety-warning-icon.png'
  spec=item['children'][1]['component_spec'];slots={x['role']:x['content'] for x in spec['slots']}
  label=slots['label']+(':' if c.get('warning_colon') else '')
  item['children'][1]=group([node('paragraph',[node('strong',[text(label)])]),node('paragraph',[node('strong',[text(slots['body'])])])],'warning-copy')
 for child in item.get('children',[]):restore_safety(child)
for ch in d['chapters']:
 if ch['id']=='safety':
  for item in ch['nodes']:restore_safety(item)
# Retain source phone/mail/web pictograms with native contact copy and adjacent QR.
ch=next(ch for ch in d['chapters'] if ch['id']=='contact')
contact_index=next(i for i,n in enumerate(ch['nodes']) if n.get('kind')=='paragraph' and any(t.get('text','').startswith('1-888') for t in n.get('children',[])))
values=[t['text'] for t in ch['nodes'][contact_index]['children'] if t.get('kind')=='text']
rows=[]
for name,value in zip(['phone','mail','web'],values):
 icon=node('image',source='assets/contact-'+name+'.png',alt=name+' symbol from source')
 copy=para(value)
 if name=='phone':copy=node('paragraph',[node('strong',[text(value.split(' (US)')[0])]),text(' (US)')])
 rows.append(group([icon,copy],'contact-'+name))
qr=ch['nodes'][contact_index+1];qr.pop('schema_version',None)
ch['nodes'][contact_index:contact_index+2]=[root(group([rows[0],group(rows[1:],'contact-mailweb'),qr],'contact-strip'))]
# The single source temperature number spans both high/low-temperature rows.
def restore_lcd_spans(n):
 if n.get('kind')=='component' and n.get('component_spec',{}).get('component_id')=='HB-TABLE-LCD-ICON':
  spec=n['component_spec'];spec.setdefault('metadata',{})['number_cell_layout']='span-adjacent-equal'
  for slot in spec['slots']:
   if slot['role']=='rows':
    for row in slot['content']:
     for key in ['number_text','number_html']:
      if row.get(key,'').isdigit():row[key]=chr(0x2460+int(row[key])-1)
 for child in n.get('children',[]):restore_lcd_spans(child)
for chapter in d['chapters']:
 for n in chapter['nodes']:restore_lcd_spans(n)
# Source troubleshooting keeps one Restart cell spanning F0 through F3.
from tools.manual_ir.flow import html_to_flow_nodes
chapter=next(ch for ch in d['chapters'] if ch['id']=='troubleshooting')
for index,item in enumerate(chapter['nodes']):
 spec=item.get('component_spec',{})
 if spec.get('component_id')!='HB-TABLE-TROUBLESHOOTING':continue
 slots={x['role']:x['content'] for x in spec['slots']};rows=slots['rows'];heads=slots['headers']
 assert [x['code_text'] for x in rows[:4]]==['F0','F1','F2','F3']
 assert len({x['measures_html'] for x in rows[:4]})==1
 markup='<div class="table-wrapper docutils container" data-source-layout="source-troubleshooting"><table class="manual-table hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"><col class="hb-troubleshooting-col-measures"></colgroup><thead><tr>'+''.join('<th>'+h['content_html']+'</th>' for h in heads)+'</tr></thead><tbody>'
 for j,row in enumerate(rows):
  markup+='<tr><td class="hb-troubleshooting-code">'+row['code_html']+'</td>'
  if j==0:markup+='<td class="hb-troubleshooting-measures" rowspan="4">'+row['measures_html']+'</td>'
  elif j>=4:markup+='<td class="hb-troubleshooting-measures">'+row['measures_html']+'</td>'
  markup+='</tr>'
 markup+='</tbody></table></div>'
 chapter['nodes'][index:index+1]=[root(n) for n in html_to_flow_nodes(markup)]

f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
