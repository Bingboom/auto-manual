"""Target-only JHP-1000B-RC layout restoration from its own 22-page PDF."""
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
    placements={'operations':[(2,[(3,[150,141,331,187])]),(7,[(6,[29,255,167,271]),(8,[31,465,332,492])]),(11,[(10,[31,49,169,66])]),(17,[(16,[31,376,335,403]),(18,[253,416,333,487])]),(25,[(24,[32,237,330,263])])],'charging':[(5,[(6,[35,363,331,377])])]}
    recipes={Path(p['path']).stem:p for p in json.loads((package/'source/asset_recipe.json').read_text())['panels']}
    css=[]
    for chapter, patches in placements.items():
        nodes=chapters[chapter]['nodes'];remove=set();replace={}
        for figidx,panels in patches:
            figure=nodes[figidx];ref=figure['component_spec']['source_ref'].rsplit('/',1)[-1];recipe=recipes[ref];x0,y0,x1,y1=recipe['bbox'];w=x1-x0;h=y1-y0
            children=[deepcopy(figure)]
            for j,(idx,b) in enumerate(panels):
                n=deepcopy(nodes[idx]);sid=f'{ref}-{j}';
                if ref=='charging-ac':n['presentation']['html']['attributes']['class']='container'
                children.append(group([n],**{'data-native-copy':sid}));remove.add(idx)
                l,t,r,bt=b;css.append(f'[data-native-copy="{sid}"] {{left:{(l-x0)/w*100:.5f}%;top:{(t-y0)/h*100:.5f}%;width:{(r-l)/w*100:.5f}%;height:{(bt-t)/h*100:.5f}%;}}')
            replace[figidx]=root(group([group(children,**{'data-native-panel':ref})],**{'data-native-panel-scroll':ref}))
        chapters[chapter]['nodes']=[replace.get(i,n) for i,n in enumerate(nodes) if i not in remove]
    # p4's warning card occupies the top of the left column; its bullets are
    # outside the card and flow across the two printed columns.
    s=chapters['safety']['nodes'];old=s[2];body=callout_body(old);lead=deepcopy(body[0]);items=deepcopy(body[1]['children']);header=deepcopy(old)
    callout_body(header)[:]=[lead]
    spec=callout_component_spec(label='WARNING',body=' '.join(flat(lead).split()),items=[],variant='warning',language='en',source_ref='native-pdf/page-4/warning-basic-card')
    header['component_spec']=spec.to_dict()
    header=group([node('image',source='assets/source-warning-card.png',alt=''),group([node('paragraph',[node('strong',[text('WARNING')])]),lead],**{'data-source-warning-card-copy':'true'})],**{'data-source-warning-card':'true'})
    # Break at the exact source column boundary inside the sixth bullet.
    item6=flat(items[5]);cut='product can result';left,right=item6.split(cut,1)
    first=deepcopy(items[:5])+[node('list_item',[para(left.rstrip())])]
    second=[para(cut+right),node('list',deepcopy(items[6:]),ordered=False)]
    safetycols=group([group([header,node('list',first,ordered=False)],**{'data-native-column':'left'}),group(second,**{'data-native-column':'right'})],**{'data-native-columns':'safety-warning'})
    # Original operating left column ends with cord/plug instruction (item 9).
    ops=s[5]['children'][0]['children'] if s[5]['kind']=='root' else s[5]['children']
    # root() may return the list itself; retain the semantic items unchanged.
    if ops and ops[0].get('kind')!='list_item':raise ValueError('unexpected operating source structure')
    ground_body=deepcopy(callout_body(s[8]));ground_label=node('paragraph',[node('strong',[text('WARNING')])])
    opcols=group([group([node('list',deepcopy(ops[:9]),ordered=False)],**{'data-native-column':'left'}),group([node('list',deepcopy(ops[9:]),ordered=False),node('paragraph',[node('strong',[text(flat(s[6]))])]),deepcopy(s[7]),ground_label,*ground_body],**{'data-native-column':'right'})],**{'data-native-columns':'operating'})
    chapters['safety']['nodes']=[s[0],s[1],root(safetycols),s[3],s[4],root(opcols),*s[9:]]
    # Own source p6 prints ISED licence text left and RF text right.
    ised=chapters['fcc']['nodes'][2]
    parts=ised['children']
    ised['children']=[group([group(deepcopy(parts[:6]),**{'data-native-column':'left'}),group(deepcopy(parts[6:]),**{'data-native-column':'right'})],**{'data-native-columns':'ised'})]
    # Source-wide warning strips retain their actual frame/icon and native copy.
    for index,n in enumerate(chapters['safety']['nodes']):
        if n.get('kind')=='component' and n['component_spec']['source_ref'] in ['native-pdf/page-4/warning-risk','native-pdf/page-5/danger']:
            isrisk=n['component_spec']['source_ref'].endswith('warning-risk')
            name='risk-strip' if isrisk else 'danger-strip'
            label=next(x['content'] for x in n['component_spec']['slots'] if x['role']=='label')
            body=deepcopy(callout_body(n))
            if isrisk:
                a,b=flat(body[0]).split('SHOCK,',1)
                body=[node('paragraph',[node('strong',[text(a.rstrip()),node('line_break'),text('SHOCK,'+b)])])]
            art=group([node('image',source='assets/'+name+'.png',alt=''),group([node('paragraph',[node('strong',[text(label)])])],**{'data-native-strip-label':name}),group(body,**{'data-native-strip-copy':name})],**{'data-native-strip':name})
            chapters['safety']['nodes'][index]=root(group([art],**{'data-native-strip-scroll':name}))
    # Restore the source's language badge without hiding source copy.
    chapters['preface']['nodes'][0]=root(group([node('inline_group',[text('EN')],presentation=attrs(**{'class':'hb-signal-badge'})),node('strong',[text('IMPORTANT')])],**{'data-source-preface-title':'true'}))
    # The print's two safety subsection titles are dark bars, not dotted labels.
    for i,n in enumerate(chapters['safety']['nodes']):
        if n.get('kind')=='heading' and flat(n) in ['OPERATING INSTRUCTIONS','USER MAINTENANCE INSTRUCTIONS']:
            chapters['safety']['nodes'][i]=root(node('paragraph',[node('strong',[text(flat(n))])],presentation=attrs(**{'class':'hb-prose-pill','data-source-safety-title':'true'})))
    for chapter in ['safety','charging']:
        for i,n in enumerate(chapters[chapter]['nodes']):
            if n.get('kind')=='heading' and flat(n) in ['SAVE THESE INSTRUCTIONS','Emergency Charging Mode']:
                chapters[chapter]['nodes'][i]=root(node('paragraph',[node('strong',[text(flat(n))])],presentation=attrs(**{'data-source-plain-lead':'true'})))
    chapters['charging']['nodes'][2]['presentation']=attrs(**{'class':'hb-prose-pill','data-source-first-charge':'true'})
    # App headings have an explicit source bullet; shared app CSS suppresses its generic marker.
    for n in chapters['app_setup']['nodes']:
        if n.get('kind')=='heading' and n.get('level')==3:
            n['children'].insert(0,text('● '))
    (package/'source/layout-positions.css').write_text('\n'.join(css)+'\n')
    # The shared signal component draws a generic glyph. This source requires
    # its exact original white triangle, with the signal words still native.
    from tools.web.prepared_style_audit import table_text_sha256
    signal=chapters['symbols']['nodes'][1]['component_spec']
    slots={row['role']:row['content'] for row in signal['slots']}
    heads=node('table_head',[node('table_row',[node('table_cell',[text(h['content_text'])],header=True) for h in slots['headers']])])
    rows=[]
    for r in slots['rows']:
        badge=node('inline_group',[node('image',source='assets/source-signal-glyph.png',alt=''),node('inline_group',[text(r['label'])],presentation=attrs(**{'class':'hb-signal-label'}))],presentation=attrs(**{'class':'hb-signal-badge'}))
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
    # Preserve source warning marks in their native carrier cells, without drawing new icons.
    for c in content['chapters']:
        def marks(n):
            if n.get('kind')=='component' and n['component_spec']['component_id']=='HB-CALLOUT-STRIP':
                ref=n['component_spec']['source_ref']
                if ref in ['native-pdf/page-4/warning-risk','native-pdf/page-4/warning-basic-card','native-pdf/page-5/danger']:
                    label=n['carrier_flow'][0]['children'][0]['children'][0]['children'][0]
                    icon='source-warning-light' if ref.endswith('basic-card') else 'source-warning-dark'
                    label['children'].insert(0,node('image',source='assets/'+icon+'.png',alt=''))
                    label['presentation']['html']['attributes']['data-source-warning']='true'
            for ch in n.get('children',[]):marks(ch)
        for n in c['nodes']:marks(n)
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
