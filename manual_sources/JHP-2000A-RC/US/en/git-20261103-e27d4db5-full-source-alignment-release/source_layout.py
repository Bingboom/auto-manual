"""Target-only JHP-2000A-RC layout restoration from its own 24-page PDF."""
from copy import deepcopy
from pathlib import Path
import json
from tools.web.frozen_ai_flow import node, root, text
from tools.component_specs.callout import callout_component_spec
from tools.manual_ir.components import component_flow_node

def attrs(**kw): return {'html':{'attributes':kw}}
def group(children, **kw):return node('group',children,role='container',presentation=attrs(**{'class':'container',**kw}))
def para(s):return node('paragraph',[text(s)])
def flat(n):return n.get('text','')+''.join(flat(c) for c in n.get('children',[]))
def callout_body(n):return n['carrier_flow'][0]['children'][0]['children'][0]['children'][1]['children']
def align_source_layout(content, package):
    chapters={c['id']:c for c in content['chapters']}
    # Preserve each moved text block as native text, but put it back in the
    # rectangle printed inside the same model's source artwork.
    placements={'operations':[(2,[(3,[176,167,326,199]),(4,[48,217,325,234])]),(8,[(6,[46,286,169,295]),(7,[46,310,321,327])]),(11,[(10,[46,61,170,70])]),(17,[(16,[39.61,57.83,329.9,116.97]),(18,[39.61,227.54,329.9,268.66])]),(23,[(22,[40,396,323,422]),(24,[254,427,329,495])])], 'ups':[(2,[(3,[129,215,333,256])])], 'charging':[(5,[(6,[191,273,313,290])])]}
    recipes={Path(p['path']).stem:p for p in json.loads((package/'source/asset_recipe.json').read_text())['panels']}
    css=[]
    for chapter, patches in placements.items():
        nodes=chapters[chapter]['nodes'];remove=set();replace={}
        for figidx,panels in patches:
            figure=nodes[figidx];ref=figure['component_spec']['source_ref'].rsplit('/',1)[-1];recipe=recipes[ref];x0,y0,x1,y1=recipe['bbox'];w=x1-x0;h=y1-y0
            children=[deepcopy(figure)]
            for j,(idx,b) in enumerate(panels):
                n=deepcopy(nodes[idx]);sid=f'{ref}-{j}';
                if n.get('presentation'):n['presentation']['html']['attributes']['class']='container'
                children.append(group([n],**{'data-native-copy':sid}));remove.add(idx)
                l,t,r,bt=b;css.append(f'[data-native-copy="{sid}"] {{left:{(l-x0)/w*100:.5f}%;top:{(t-y0)/h*100:.5f}%;width:{(r-l)/w*100:.5f}%;height:{(bt-t)/h*100:.5f}%;}}')
            replace[figidx]=root(group([group(children,**{'data-native-panel':ref})],**{'data-native-panel-scroll':ref}))
        chapters[chapter]['nodes']=[replace.get(i,n) for i,n in enumerate(nodes) if i not in remove]
    # Own p4: full-width risk strip, then six/five safety bullets; no small warning card.
    s=chapters['safety']['nodes'];body=callout_body(s[1]);lead=deepcopy(body[1]);items=deepcopy(body[2]['children'])
    risk=deepcopy(s[1]);callout_body(risk)[:]=[deepcopy(body[0])]
    def columns(left,right,name):
        return root(group([group(left,**{'data-native-column':'left'}),group(right,**{'data-native-column':'right'})],**{'data-native-columns':name}))
    safetycols=columns([lead,node('list',items[:6],ordered=False)],[node('list',items[6:],ordered=False)],'safety-warning')
    ops=s[4]['children'][0]['children'] if s[4]['kind']=='root' else s[4]['children']
    opcols=columns([node('list',deepcopy(ops[:7]),ordered=False)],[node('list',deepcopy(ops[7:]),ordered=False)],'operating')
    chapters['safety']['nodes']=[s[0],risk,safetycols,s[2],s[3],opcols,*s[5:]]
    # Own source p6 prints ISED licence text left and RF text right.
    ised=chapters['fcc']['nodes'][2]
    parts=ised['children']
    ised['children']=[group([group(deepcopy(parts[:6]),**{'data-native-column':'left'}),group(deepcopy(parts[6:]),**{'data-native-column':'right'})],**{'data-native-columns':'ised'})]
    # Own p4/p5 original strips: retain PDF frames/icons, native exact copy.
    stripnames={'native-pdf/page-4/warning':'risk-strip','native-pdf/page-5/warning':'ground-strip','native-pdf/page-5/danger':'danger-strip'}
    for index,n in enumerate(chapters['safety']['nodes']):
        if n.get('kind')=='component' and n['component_spec']['source_ref'] in stripnames:
            name=stripnames[n['component_spec']['source_ref']]
            label=next(x['content'] for x in n['component_spec']['slots'] if x['role']=='label')
            body=deepcopy(callout_body(n))
            art=group([node('image',source='assets/'+name+'.png',alt=''),group([para(label)],**{'data-native-strip-label':name}),group(body,**{'data-native-strip-copy':name})],**{'data-native-strip':name})
            chapters['safety']['nodes'][index]=root(group([art],**{'data-native-strip-scroll':name}))
    # Restore the source's language badge without hiding source copy.
    chapters['preface']['nodes'][0]=root(group([node('inline_group',[text('US')],presentation=attrs(**{'class':'hb-signal-badge'})),node('strong',[text('IMPORTANT')])],**{'data-source-preface-title':'true'}))
    # The print's two safety subsection titles are dark bars, not dotted labels.
    for i,n in enumerate(chapters['safety']['nodes']):
        if n.get('kind')=='heading' and flat(n) in ['OPERATING INSTRUCTIONS','USER MAINTENANCE INSTRUCTIONS']:
            chapters['safety']['nodes'][i]=root(node('paragraph',[node('strong',[text(flat(n))])],presentation=attrs(**{'class':'hb-prose-pill','data-source-safety-title':'true'})))
    for chapter in ['safety','charging']:
        for i,n in enumerate(chapters[chapter]['nodes']):
            if n.get('kind')=='heading' and flat(n) in ['SAVE THESE INSTRUCTIONS']:
                chapters[chapter]['nodes'][i]=root(node('paragraph',[node('strong',[text(flat(n))])],presentation=attrs(**{'data-source-plain-lead':'true'})))
    for i,n in enumerate(chapters['charging']['nodes']):
        if n.get('kind')=='heading' and flat(n)=='Emergency Charging Mode':
            chapters['charging']['nodes'][i]=root(node('paragraph',[node('strong',[text(flat(n))])],presentation=attrs(**{'class':'hb-prose-pill','data-source-emergency':'true'})))
    chapters['charging']['nodes'][2]['presentation']=attrs(**{'class':'hb-prose-pill','data-source-first-charge':'true'})
    (package/'source/layout-positions.css').write_text('\n'.join(css)+'\n')
    # The shared signal component draws a generic glyph. This source requires
    # its exact original white triangle, with the signal words still native.
    from tools.web.prepared_style_audit import table_text_sha256
    signal=chapters['symbols']['nodes'][1]['component_spec']
    slots={row['role']:row['content'] for row in signal['slots']}
    heads=node('table_head',[node('table_row',[node('table_cell',[text(h['content_text'])],header=True) for h in slots['headers']])])
    rows=[]
    for r in slots['rows']:
        badge=node('inline_group',([node('image',source='assets/source-signal-glyph.png',alt='')] if r.get('show_icon') else [])+[node('inline_group',[text(r['label'])],presentation=attrs(**{'class':'hb-signal-label'}))],presentation=attrs(**{'class':'hb-signal-badge'}))
        rows.append(node('table_row',[node('table_cell',[badge],header=False,presentation=attrs(**{'class':'hb-symbol-signal-label-cell'})),node('table_cell',[para(r['meaning_text'])],header=False,presentation=attrs(**{'class':'hb-symbol-signal-meaning-cell'}))]))
    table=node('table',[heads,node('table_body',rows)],presentation=attrs(**{'class':'hb-symbol-signal-table','data-source-signal':'true'}))
    chapters['symbols']['nodes'][1]=root(group([table],**{'class':'hb-symbol-signal-composition'}))
    manifest_path=package/'source_manifest.json'
    manifest=json.loads(manifest_path.read_text())
    expected_exceptions=[r for r in manifest.get('shared_component_exceptions',[]) if r.get('page_id')!='symbols']+[{'kind':'table','page_id':'symbols','language':'en','text_sha256':table_text_sha256(table),'reason':'Exact original PDF triangle is required; shared HB-TABLE-SYMBOL-SIGNAL accepts only a generic drawn glyph and cannot bind the source glyph. Native signal labels and meanings retain shared table/badge classes.'}]
    if manifest.get('shared_component_exceptions') != expected_exceptions:
        raise ValueError('Bind this target signal-table exception: '+json.dumps(expected_exceptions))
    # Use the original clock mark instead of the shared drawn duration marker.
    for n in chapters['operations']['nodes']:
        if n.get('kind')=='component' and n['component_spec']['component_id']=='HB-TABLE-KEY-COMBINATIONS':
            for row in n['carrier_flow'][0]['children'][1]['children']:
                duration=row['children'][1]['children'][0]
                duration['presentation']['html']['attributes'].pop('data-duration-icon',None)
                duration['children'].insert(0,node('image',source='assets/source-clock.png',alt=''))
    # The source's repeated LCD number 23 spans the temperature rows.
    chapters['lcd_display']['nodes'][2]['component_spec']['metadata']['number_cell_layout']='span-adjacent-equal'
    def image(name):return node('image',source='assets/'+name+'.png',alt='')
    def contact(back=False):
        phone=node('paragraph',[text('1-888-502-2236 '),node('inline_group',[text('(US)')],presentation=attrs(**{'data-contact-country':'true'}))])
        art=group([image('back-contact-base'),group([phone],**{'data-native-copy':'back-phone'}),group([para('hello@jackery.com')],**{'data-native-copy':'back-mail'}),group([para('www.jackery.com')],**{'data-native-copy':'back-web'})],**{'data-native-panel':'back-contact'})
        return group([art],**{'data-native-panel-scroll':'back-contact','data-source-contact':'back'})
    back={'id':'back-cover','title':'JACKERY INC.','nodes':[root(node('heading',[text('JACKERY INC.')],level=3)),root(para('5310 Bunche Dr., Fremont, CA 94538-8301')),root(contact(True))]}
    # Existing operator conversion scope excludes front cover and paper TOC.
    content['chapters']=[*content['chapters'],back]
    def nested(n):
        for ch in n.get('children',[]):
            ch.pop('schema_version',None)
            nested(ch)
    for chapter in content['chapters']:
        for block in chapter['nodes']:nested(block)
    return content
