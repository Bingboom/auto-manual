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
# Match the exact source circled LCD row numbers with native Unicode characters.
def restore_circled(n):
 if n.get('kind')=='component' and n.get('component_spec',{}).get('component_id')=='HB-TABLE-LCD-ICON':
  for slot in n['component_spec']['slots']:
   if slot['role']=='rows':
    for row in slot['content']:
     for key in ['number_text','number_html']:
      if row.get(key,'').isdigit():row[key]=chr(0x2460+int(row[key])-1)
 for child in n.get('children',[]):restore_circled(child)
for chapter in d['chapters']:
 for n in chapter['nodes']:restore_circled(n)

f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
