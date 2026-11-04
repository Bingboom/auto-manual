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
# Preserve source-side paragraph/art pairing, without changing any descendant content.
for chapter_id,start,end in [('charging', 2, 5)]:
 ch=next(ch for ch in d['chapters'] if ch['id']==chapter_id)
 original=ch['nodes'][start:end]
 for n in original:n.pop('schema_version',None)
 ch['nodes'][start:end]=[root(group([group(original[:-1],'charging-copy'),original[-1]],'charging-pair'))]
ch=next(ch for ch in d['chapters'] if ch['id']=='introduction')
items=ch['nodes'][5:7]
for n in items:n.pop('schema_version',None)
ch['nodes'][5:7]=[root(group(items,'certification-pair'))]
ch=next(ch for ch in d['chapters'] if ch['id']=='lcd_display')
legend=next(n for n in ch['nodes'] if n.get('kind')=='list')
for i,item in enumerate(legend['children']):item['children'].insert(0,text(chr(0x2460+i)+' '))
ch=next(ch for ch in d['chapters'] if ch['id']=='contact')
items=ch['nodes'][1:]
for n in items:n.pop('schema_version',None)
ch['nodes'][1:]=[root(group(items,'back-contact-pair'))]
f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
