"""JHP-2000A only: restore the geometry actually printed in its own source."""
from copy import deepcopy
import json
from tools.web.frozen_ai_flow import node, root, text
from tools.web.prepared_style_audit import table_text_sha256

def attrs(**kw):return {'html':{'attributes':{'class':'container',**kw}}}
def embed(n):
 n=deepcopy(n);n.pop('schema_version',None);return n
def group(children,**kw):return node('group',[embed(c) for c in children],role='container',presentation=attrs(**kw))
def flat(n):return n.get('text','')+''.join(flat(c) for c in n.get('children',[]))
def body(n):return n['carrier_flow'][0]['children'][0]['children'][0]['children'][1]['children']
def clean(n):
 n=embed(n)
 def visit(x):
  a=x.get('presentation',{}).get('html',{}).get('attributes',{})
  if a.get('class')=='hb-text-panel':a['class']='container'
  for c in x.get('children',[]):visit(c)
 visit(n);return n

def align_source_layout(chapters,package):
 c={x['id']:x for x in chapters};rules=[]
 # Exact source frame/text rectangles were measured on p11/12/13/15/17.
 positions={
  'operations':[(2,[(3,[176,168,329,199]),(4,[48,218,330,235])]),(8,[(6,[45,285,170,295]),(7,[46,310,325,327])]),(11,[(10,[46,61,171,70])]),(17,[(16,[46,63,326,111]),(18,[46,238,326,277])]),(22,[(21,[46,364,321,380]),(23,[255,406,333,482])])],
  'ups':[(2,[(3,[129,336,333,376])])],
  'charging':[(5,[(6,[191,273,313,290])])]}
 recipes={x['path']:x for x in json.loads((package/'source/asset_recipe.json').read_text())['panels']}
 for cid,rows in positions.items():
  nodes=c[cid]['nodes'];replace={};remove=set()
  for fi,copies in rows:
   fig=nodes[fi];spec=fig['component_spec'];assert spec['component_id']=='HB-SPECIAL-REFERENCE-FIGURE'
   ref=spec['assets'][0]['asset_ref'];recipe=recipes[ref];x0,y0,x1,y1=recipe['bbox'];w=x1-x0;h=y1-y0;children=[embed(fig)]
   for j,(idx,bbox) in enumerate(copies):
    key=f'{cid}-{fi}-{j}';l,t,r,b=bbox
    children.append(group([clean(nodes[idx])],**{'data-original-copy':key}));remove.add(idx)
    rules.append(f'[data-original-copy="{key}"]{{left:{(l-x0)/w*100:.5f}%;top:{(t-y0)/h*100:.5f}%;width:{(r-l)/w*100:.5f}%;height:{(b-t)/h*100:.5f}%;}}')
   replace[fi]=root(group([group(children,**{'data-own-frame':ref})],**{'data-original-scroll':ref}))
  c[cid]['nodes']=[replace.get(i,n) for i,n in enumerate(nodes) if i not in remove]
 s=c['safety']['nodes'];warning=s[1];wb=body(warning);items=wb[2]['children'];assert len(items)==11
 label=next(x['content'] for x in warning['component_spec']['slots'] if x['role']=='label')
 def frame(name,label,copy):return root(group([group([node('image',source=f'assets/source-{name}-frame.png',alt=''),group([node('paragraph',[node('strong',[text(label)])])],**{'data-original-label':name}),group(copy,**{'data-original-frame-copy':name})],**{'data-original-frame':name})],**{'data-original-scroll':name}))
 risk=frame('risk',label,[wb[0]])
 warningcols=root(group([group([wb[1],node('list',items[:6],ordered=False)]),group([node('list',items[6:],ordered=False)])],**{'data-original-columns':'safety'}))
 ops=s[4]['children'];assert len(ops)==15
 opcols=root(group([group([node('list',ops[:7],ordered=False)]),group([node('list',ops[7:],ordered=False)])],**{'data-original-columns':'operating'}))
 glabel=next(x['content'] for x in s[5]['component_spec']['slots'] if x['role']=='label');dlabel=next(x['content'] for x in s[6]['component_spec']['slots'] if x['role']=='label')
 c['safety']['nodes']=[s[0],risk,warningcols,s[2],s[3],opcols,frame('grounding',glabel,body(s[5])),frame('danger',dlabel,body(s[6])),*s[7:]]
 # Own source subgroup headings/pills, not arbitrary shared chapter promotion.
 for ch in chapters:
  for i,n in enumerate(ch['nodes']):
   if n.get('kind')=='heading':
    title=flat(n)
    if title in ['OPERATING INSTRUCTIONS','USER MAINTENANCE INSTRUCTIONS','Emergency Charging Mode']:
     ch['nodes'][i]=root(node('paragraph',[node('strong',[text(title)])],presentation=attrs(**{'class':'hb-prose-pill',**({'data-original-section-title':'true'} if title!='Emergency Charging Mode' else {})})))
    elif title=='SAVE THESE INSTRUCTIONS' or ch['id']=='app_setup' and title.startswith(('4.1','4.2','4.3')):
     ch['nodes'][i]=root(node('paragraph',[node('strong',[text(title)])],presentation=attrs(**{'role':'heading','aria-level':'4'})))
    elif ch['id']=='app_setup' and n.get('level')==3:
     n['level']=2;n['presentation']=attrs(**{'class':'hb-subbar','data-original-app-heading':'true'})
  # Shared spec carrier must leave small source group headings as h2.
  for n in ch['nodes']:
   if n.get('component_spec',{}).get('component_id')=='HB-TABLE-SPEC':
    for x in n.get('carrier_flow',[]):
     if x.get('kind')=='heading':x['presentation']=attrs(**{'class':'hb-spec-section hb-subbar'})
 c['charging']['nodes'][2]['presentation']=attrs(**{'class':'hb-prose-pill'})
 # The source signal badges use the original glyph only for WARNING/CAUTION.
 sig=c['symbols']['nodes'][1]['component_spec'];slots={x['role']:x['content'] for x in sig['slots']}
 header=node('table_head',[node('table_row',[node('table_cell',[text(x['content_text'])],header=True) for x in slots['headers']])]);rows=[]
 for r in slots['rows']:
  children=([node('image',source='assets/source-signal-glyph.png',alt='')] if r['show_icon'] else [])+[node('inline_group',[text(r['label'])],presentation=attrs(**{'class':'hb-signal-label'}))]
  badge=node('inline_group',children,presentation=attrs(**{'class':'hb-signal-badge'}))
  rows.append(node('table_row',[node('table_cell',[badge],header=False,presentation=attrs(**{'class':'hb-symbol-signal-label-cell'})),node('table_cell',[node('paragraph',[text(r['meaning_text'])])],header=False,presentation=attrs(**{'class':'hb-symbol-signal-meaning-cell'}))]))
 table=node('table',[header,node('table_body',rows)],presentation=attrs(**{'class':'hb-symbol-signal-table'}));c['symbols']['nodes'][1]=root(group([table],**{'class':'hb-symbol-signal-composition'}))
 f=package/'source_manifest.json';d=json.loads(f.read_text());d['shared_component_exceptions']=[{'kind':'table','page_id':'symbols','language':'en','text_sha256':table_text_sha256(table),'reason':'Own-source white signal glyph; shared badges/table classes, native labels and meanings; WARNING/CAUTION only as printed.'}];f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 (package/'source/layout-positions.css').write_text('\n'.join(rules)+'\n')
