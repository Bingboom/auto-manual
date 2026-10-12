"""Source-local native text/geometry intake through shared Web components.

The source PDF is immutable. External words are live flow nodes, original
figure groups share one artwork set, and complete word selections are logged.
"""
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / 'build.py').is_file())
sys.path.insert(0, str(REPO))

import html  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import fitz  # noqa: E402
from native import Native, SOURCE, dump, normalize, pair, prose, attrs, rich_nodes  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.app import app_download_component_spec  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
from tools.component_specs.manual_tables import lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_lead_component_spec, warranty_section_component_spec, warranty_years_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.frozen_ai_flow import callout, cell, heading, node, paragraph, table, text, root  # noqa: E402

CSS = []
CAPTION_FRAMES = {}
ADJUSTMENTS = json.loads((SOURCE/'source/layout_adjustments.json').read_text())
LABELS = {'en': {'Note':'note','Caution':'caution','WARNING':'warning','DANGER':'danger','Remarks':'note'},
          'fr': {'Remarque':'note','Mise en garde':'caution','AVERTISSEMENT':'warning','DANGER':'danger','Remarques':'note'},
          'es': {'Nota':'note','Precaución':'caution','ADVERTENCIA':'warning','PELIGRO':'danger','Observaciones':'note'}}


def expanded(b, pad=.08):
    return [b[0]-pad,b[1]-pad,b[2]+pad,b[3]+pad]


def free_words(n, pg, box):
    return [w for i,w in enumerate(n.words[pg]) if (pg,i) not in n.used
            and fitz.Rect(box).contains(fitz.Point((w[0]+w[2])/2,(w[1]+w[3])/2))]


def heading_pair(n, pg, box, level=3):
    # Native title and sold-separately badge remain separate shared capsules.
    words=free_words(n,pg,box)
    if not words:return
    labelbox=None
    # A PDF block may contain both title and badge (notably native ES).
    # Select only the sold phrase, preserving the title as its own shared slot.
    tokens=[normalize(w[4]).upper() for w in words]
    for phrase in ('SOLD SEPARATELY','VENDU SÉPARÉMENT','SE VENDE POR SEPARADO'):
        wanted=phrase.split()
        for i in range(len(words)-len(wanted)+1):
            if tokens[i:i+len(wanted)]==wanted:
                badge=words[i:i+len(wanted)]
                labelbox=expanded([min(w[0] for w in badge),min(w[1] for w in badge),max(w[2] for w in badge),max(w[3] for w in badge)])
                break
        if labelbox:break
    if labelbox:
        sold=n.t(pg,labelbox,unused=True);title=n.t(pg,box,unused=True)
        n.add(node('heading',[node('inline_group',[text(title)],presentation=attrs('hb-heading-title')),text(' '),node('inline_group',[text(sold)],presentation=attrs('hb-sold-separately'))],level=level,presentation=attrs('hb-heading-label-pair')))
    else:
        n.add(heading(n.t(pg,box,unused=True),level=level))


def auto_prose(n,pg,region=None):
    box=region or [20,20,348,500]
    page=n.doc[pg-1]
    for block in sorted(page.get_text('dict')['blocks'],key=lambda b:(round(b['bbox'][1]/3),b['bbox'][0])):
        if not block.get('lines'):continue
        selected=[w for w in free_words(n,pg,box) if fitz.Rect(expanded(block['bbox'])).contains(fitz.Point((w[0]+w[2])/2,(w[1]+w[3])/2))]
        if not selected:continue
        rect=[min(w[0] for w in selected)-.08,min(w[1] for w in selected)-.08,max(w[2] for w in selected)+.08,max(w[3] for w in selected)+.08]
        spans=[s for line in block['lines'] for s in line['spans'] if fitz.Rect(rect).intersects(fitz.Rect(s['bbox']))]
        value,raw,_=n.take(pg,rect,unused=True,reading_order='vertical')
        if not value:continue
        bold=bool(spans) and all('Bold' in s['font'] for s in spans if s['text'].strip())
        if pg==n.page(20) and value.startswith('2.1') and {'en':'button','fr':'bouton','es':'dispositivo'}[n.language] in value:
            marker={'en':'button','fr':'bouton','es':'dispositivo'}[n.language]
            before,after=value.rsplit(marker,1)
            n.add(node('paragraph',[text(before+marker+' '),node('inline_group',[text('+')],presentation=attrs('native-inline-plus')),text(after)]))
        elif bold and min(s['size'] for s in spans)>=8 and len(value)<150:
            n.add(heading(value,level=3))
        else:
            n.add(*prose(raw))


def paragraph_region(n,pg,box):
    _,raw,_=n.take(pg,box,unused=True,reading_order='vertical');n.add(*prose(raw))


def native_callouts(n,pg,fig_boxes):
    page=n.doc[pg-1];result=[]
    for b in page.get_text('blocks'):
        label=normalize(b[4])
        if label not in LABELS[n.language]:continue
        point=fitz.Point((b[0]+b[2])/2,(b[1]+b[3])/2)
        if any(fitz.Rect(box).contains(point) for box in fig_boxes):continue
        candidates=[d['rect'] for d in page.get_drawings() if d['rect'].width>260 and d['rect'].height>12 and d['rect'].contains(point) and d['rect'].y1<501]
        if not candidates:continue
        region=min(candidates,key=lambda box:box.height)
        result.append((region.y0,list(region),expanded(b[:4]),LABELS[n.language][label]))
    return result


def emit_callout(n,pg,box,labelbox,variant):
    label=n.t(pg,labelbox,unused=True)
    _,raw,_=n.take(pg,box,unused=True,reading_order='vertical')
    if not normalize(raw):return
    label=display_label(label)
    n.add(callout(label,prose(raw),variant=variant,language=n.language,source_ref=f'native-pdf/page-{pg}/notice-{len(n.selections)}'))


def caption_frames(n,g):
    """Match only independently removed English caption plates to native art.

    Matching uses fill, height and predicted position, not drawing index or
    color alone. Translated header widths may grow; device shading never gains
    a CSS caption role. Ambiguous or missing matches fail closed.
    """
    english=fitz.Rect(g['bbox']);box=fitz.Rect(g.get('locale_boxes',{}).get(n.language,g['bbox']))
    pg=g['page']+n.offset;result=[]
    for index in g['removed_drawing_indices']:
        source=n.drawings(g['page'])[index];r=source['rect']
        if not (source['fill'] and r.width>50 and r.height>5 and english.contains(r)):continue
        chosen=index
        explicit=g.get('locale_caption_indices',{}).get(n.language,{}).get(str(index))
        if n.offset and explicit is not None:
            chosen=explicit;source=n.drawings(pg)[chosen];r=source['rect']
            if not source['fill'] or not box.contains(r):raise ValueError('invalid native caption override')
        elif n.offset:
            prediction=fitz.Rect(box.x0+(r.x0-english.x0)/english.width*box.width,
                                 box.y0+(r.y0-english.y0)/english.height*box.height,
                                 box.x0+(r.x1-english.x0)/english.width*box.width,
                                 box.y0+(r.y1-english.y0)/english.height*box.height)
            candidates=[]
            for i,drawing in enumerate(n.drawings(pg)):
                q=drawing['rect'];fill=drawing['fill']
                if not fill or not box.contains(q):continue
                if max(abs(a-b) for a,b in zip(fill,source['fill']))>.015:continue
                if not (.65<q.height/prediction.height<1.4 and .5<q.width/prediction.width<2.3):continue
                if abs(q.x0-prediction.x0)>12 or abs(q.y0-prediction.y0)>12:continue
                score=abs(q.x0-prediction.x0)+abs(q.y0-prediction.y0)+abs(q.height-prediction.height)
                candidates.append((score,i,drawing))
            candidates.sort(key=lambda item:item[0])
            if not candidates or (len(candidates)>1 and candidates[1][0]-candidates[0][0]<2):
                raise ValueError(('ambiguous/missing native caption plate',n.language,g['id'],index))
            _,chosen,source=candidates[0];r=source['rect']
        body=None
        if g['id']=='power':
            tops=[item[1].y for item in source['items'] if item[0]=='l' and abs(item[1].y-item[2].y)<.01 and abs(item[1].x-item[2].x)>r.width*.4]
            if not tops:raise ValueError('power caption body edge missing')
            body=[r.x0,min(tops),r.x1,r.y1]
        result.append({'body_bbox':body,'physical_page':pg,'drawing_index':chosen,'english_drawing_index':index,
                       'bbox':list(r),'fill':list(source['fill'])})
    return result


def fig_labels(n,g):
    pg=g['page']+n.offset;box=g.get('locale_boxes',{}).get(n.language,g['bbox']);page=n.doc[pg-1]
    groups=[];assigned=set()
    # A caption background belongs to one live block, even when the PDF stores
    # its title/body as several text blocks. Resolve the native locale plate
    # before selecting words; English geometry cannot classify translated ink.
    for frame in caption_frames(n,g):
        r=fitz.Rect(frame['bbox'])
        ws=[w for w in n.words[pg] if r.contains(fitz.Point((w[0]+w[2])/2,(w[1]+w[3])/2))]
        if not ws:raise ValueError(('empty native caption frame',n.language,g['id'],frame))
        keys={(w[5],w[6],w[7]) for w in ws}
        if assigned & keys:raise ValueError(('overlapping native caption frames',n.language,g['id']))
        assigned.update(keys);groups.append((ws,frame))
        CAPTION_FRAMES.setdefault(n.language,[]).append({**frame,'figure':g['id'],'text':normalize(' '.join(w[4] for w in ws))})
    # Non-plated exterior labels retain their actual line/gap geometry.
    for b in page.get_text('blocks'):
        ws=[w for w in n.words[pg] if (w[5],w[6],w[7]) not in assigned and fitz.Rect(box).contains(fitz.Point((w[0]+w[2])/2,(w[1]+w[3])/2)) and w[5]==b[5]]
        if not ws:continue
        if g['id']=='lcd-map':groups.extend(([w],None) for w in ws);continue
        lines={}
        for w in ws:lines.setdefault((w[5],w[6]),[]).append(w)
        for v in lines.values():
            chunks=[[]]
            for w in sorted(v,key=lambda w:w[0]):
                if chunks[-1] and w[0]-chunks[-1][-1][2]>12:chunks.append([])
                chunks[-1].append(w)
            groups.extend((chunk,None) for chunk in chunks)
    labels=[];spans=n.spans(pg);occurrences={}
    for ws,frame in sorted(groups,key=lambda v:(min(w[1] for w in v[0]),min(w[0] for w in v[0]))):
        b=[min(w[0] for w in ws),min(w[1] for w in ws),max(w[2] for w in ws),max(w[3] for w in ws)]
        cap=n.caption(pg,expanded(b));idx=len(labels)
        plain=' '.join(w[4] for w in ws)
        if any('⎓' in w[4] for w in ws):
            normals=[z['bbox'][1] for z in n.spans(pg) if z['font']!='SegoeUISymbol' and fitz.Rect(expanded(b)).contains(fitz.Point((z['bbox'][0]+z['bbox'][2])/2,(z['bbox'][1]+z['bbox'][3])/2))]
            if normals:b[1]=min(normals)
        if (g['id']=='overview-left' and plain.startswith('Connect to Smart')) or (g['id']=='ac-output' and plain=='Press once') or (g['id']=='package-sts' and plain.startswith('(secure')):b[1]+=1.5
        size=max((s['size'] for s in spans if fitz.Rect(expanded(b)).contains(fitz.Point((s['bbox'][0]+s['bbox'][2])/2,(s['bbox'][1]+s['bbox'][3])/2))),default=6)
        key=normalize(plain);occurrence=occurrences.get(key,0);occurrences[key]=occurrence+1
        adjustment=dict(ADJUSTMENTS.get(n.language,{}).get(g['id'],{}).get(key,{}))
        adjustment.update(adjustment.get('occurrences',{}).get(str(occurrence),{}))
        b[0]+=adjustment.get('dx_pt',0);b[2]+=adjustment.get('dx_pt',0)
        b[1]+=adjustment.get('dy_pt',0);b[3]+=adjustment.get('dy_pt',0)
        size*=adjustment.get('font_scale',1)
        localwidth=box[2]-box[0];font=size/localwidth*100
        # Rich text keeps native line breaks; source-derived cqw scales with art.
        CSS.append(f'html[lang="{n.language}"] .native-{g["id"]} [data-source-line="{idx}"] {{font-size:{font:.4f}cqw!important;}}')
        rect=[(b[0]-box[0])/localwidth*100,(b[1]-box[1])/(box[3]-box[1])*100,(b[2]-b[0]+1)/localwidth*100,(b[3]-b[1]+1.5)/(box[3]-box[1])*100]
        fill=None
        if frame:
            r=fitz.Rect(frame.get('body_bbox') or frame['bbox']);color=frame['fill']
            fill='#ffffff' if sum(color)>2.97 else '#f2f2f3' if sum(color)>2.7 else '#b5b5b6'
            rect=[(r.x0-box[0])/localwidth*100,(r.y0-box[1])/(box[3]-box[1])*100,r.width/localwidth*100,r.height/(box[3]-box[1])*100]
            CSS.append(f'html[lang="{n.language}"] .native-{g["id"]} [data-source-line="{idx}"] {{padding:{max(0,b[1]-r.y0)/localwidth*100:.4f}cqw {max(0,b[0]-r.x0)/localwidth*100:.4f}cqw!important;}}')
        if fill:
            CSS.append(f'html[lang="{n.language}"] .native-{g["id"]} [data-source-line="{idx}"] {{border-radius:{(15 if g["id"].startswith("package") else 6)/localwidth*100:.4f}cqw!important;}}')
            if g['id'].startswith('package'):
                CSS.append(f'html[lang="{n.language}"] .native-{g["id"]} [data-source-line="{idx}"]::after {{content:"";position:absolute;left:8%;top:12%;width:33%;height:76%;background:url("assets/sold-separately-cart.svg") center/contain no-repeat;}}')
        labels.append((cap,rect,*([fill] if fill else [])))
    return labels


def emit_figure(n,g):
    labels=fig_labels(n,g)
    width='regular' if g['id'].startswith(('inbox','app')) else 'dense'
    out=n.figure(g['id'],labels,width=width)
    if g['id'] in ('power','ac-output','usb-output','dc-output','ups','battery-packs','sts-connect','ac-charge','sts-charge','ess','package-host','package-battery','package-sts'):
        out['presentation']['html']['attributes']['class']+=' native-operation'
    return out


def symbols(n,pg):
    tabs=n.doc[pg-1].find_tables().tables
    signal=tabs[0];vals=signal.extract()[0];heads=[pair('content',n.t(pg,[29,signal.bbox[1],107,signal.bbox[1]+17])),pair('content',n.t(pg,[108,signal.bbox[1],341,signal.bbox[1]+17]))]
    words=n.words[pg];meanings=[b for b in n.doc[pg-1].get_text('blocks') if b[0]>105 and signal.bbox[1]+15<b[1]<signal.bbox[3]]
    labels={'en':['WARNING','CAUTION','Note'],'fr':['AVERTISSEMENT','ATTENTION','Remarque'],'es':['ADVERTENCIA','PRECAUCIÓN','Nota']}[n.language]
    rows=[]
    for i,b in enumerate(sorted(meanings,key=lambda b:b[1])):
        value=n.t(pg,expanded(b[:4]));rows.append({'label':labels[i],'show_icon':i<2,**pair('meaning',value)})
    n.take(pg,list(signal.bbox),purpose='source-signal-badge',unused=True)
    n.add(n.comp(symbol_signal_component_spec,accessibility_label='Signal words',headers=heads,rows=rows))
    panels=[];headers=[]
    for j,t in enumerate(tabs[1:3]):
        cells=t.rows[0].cells
        headers.extend(pair('content',n.t(pg,expanded(c))) for c in cells)
        panel=[]
        for i,row in enumerate(t.rows[1:]):
            c=row.cells[1];value=n.t(pg,expanded(c));panel.append({'asset_index':j*4+i,'icon_alt':value,**pair('meaning',value)})
        panels.append(panel)
    refs=json.loads((SOURCE/'source/symbol_refs.json').read_text())
    n.add(n.comp(symbol_icon_component_spec,accessibility_label='Safety symbols',headers=headers,panels=panels,icon_refs=refs))


def lcd(n):
    rows=[]
    for ep in [8,9]:
        pg=n.page(ep);tab=n.doc[pg-1].find_tables().tables[0]
        # Native p9 has split subrows and an accidental line near entry 22.
        ranges=[[row.cells[-1][1],row.cells[-1][3]] for row in tab.rows]
        if ep==9:
            ranges[-2][1]=ranges[-1][0];ranges[-2][1]=max(ranges[-2][1],475)
            ranges[-1][0]=max(ranges[-1][0],475)
        lastnumber=''
        for y0,y1 in ranges:
            if ep==8:cuts=[27,45,82,164,343]
            else:cuts=[27,45,83 if n.language=='es' else 86,164,343]
            numberbox=tab.rows[len(rows)-(10 if ep==9 else 0)].cells[0]
            num=(n.t(pg,expanded(numberbox),unused=True) if numberbox else '') or lastnumber
            lastnumber=num
            # Caption-side embedded subicons are native art, not prose words.
            namebox=fitz.Rect(cuts[2],y0,cuts[3],y1)
            name=n.t(pg,list(namebox),unused=True,reading_order='vertical')
            body=n.t(pg,[cuts[3],y0,cuts[4],y1],unused=True,reading_order='vertical')
            if not name or not body:raise ValueError(('LCD bounds',n.language,pg,y0,y1,num,name,body))
            copy=pair('name',name)
            regular=[s for s in n.spans(pg) if 'Regular' in s['font'] and namebox.contains(fitz.Point((s['bbox'][0]+s['bbox'][2])/2,(s['bbox'][1]+s['bbox'][3])/2))]
            if regular:
                note_y=min(s['bbox'][1] for s in regular)
                title=n.t(pg,[cuts[2],y0,cuts[3],note_y],reading_order='vertical')
                note=n.t(pg,[cuts[2],note_y,cuts[3],y1],reading_order='vertical')
                if title and note:copy['name_html']=pair('name',title)['name_html']+'<br><span class="native-lcd-note">'+pair('name',note)['name_html']+'</span>'
            rows.append({**pair('number',num),**copy,**pair('description',body),'asset_index':len(rows),'icon_alt':name})
    assert len(rows)==26,(n.language,len(rows))
    n.add(n.comp(lcd_icon_component_spec,accessibility_label='LCD indicators',rows=rows,icon_refs=json.loads((SOURCE/'source/lcd_refs.json').read_text())))


def semantic_table(n,pg,t,spec=False):
    boxes=[list(row.cells) for row in t.rows];bbox=list(t.bbox)
    if spec:
        # Native temperature values continue below the last detected border.
        if len(boxes)==2 and bbox[1]>400:
            end={'en':464,'fr':475,'es':477}[n.language]
            left,right=boxes[0]
            y=left[3]
            boxes[-1]=[[left[0],y,left[2],end],[right[0],y,right[2],end]]
        titleboxes=[b for b in n.doc[pg-1].get_text('blocks') if b[0]<45 and bbox[1]-24<b[1]<bbox[1] and len(normalize(b[4]))<130]
        if not titleboxes:raise ValueError(('missing table title',n.language,pg,bbox))
        titlebox=max(titleboxes,key=lambda b:b[1]);title=n.t(pg,expanded(titlebox[:4]),unused=True)
        rows=[]
        for cells in boxes:
            if len(cells)!=2:raise ValueError(('non-pair spec',pg,cells))
            vals=[n.t(pg,expanded(c),unused=True) if c else '' for c in cells]
            if not vals[0] and not vals[1]:continue
            rows.append(vals)
        # Technical rowgroup label DC Input legitimately has an empty value.
        if pg==n.page(26) and bbox[1]>350:
            following=n.doc[n.page(27)-1].find_tables().tables[0]
            rows.extend([n.t(n.page(27),expanded(c),unused=True) if c else '' for c in row.cells] for row in following.rows)
        n.add(n.comp(spec_table_component_spec,section_title=title,rows=rows))
    else:
        rows=[]
        for cells in boxes:
            rows.append([node('table_cell',rich_nodes(n.t(pg,expanded(c),unused=True) if c else ''),header=False) for c in cells])
        head=node('table_head',[node('table_row',[{**c,'header':True} for c in rows[0]])]);body=node('table_body',[node('table_row',row) for row in rows[1:]])
        n.add(node('group',[node('table',[head,body],presentation=attrs('manual-table native-troubleshooting'))],role='container',presentation=attrs('table-wrapper docutils container')))


def combinations(n,pg,t):
    header=[n.t(pg,expanded(c)) for c in t.rows[0].cells];rows=[];carriers=[]
    for i,row in enumerate(t.rows[1:]):
        c=row.cells;start,end=c[0][1],c[0][3]
        # Preserve the native left/right button names and pair artwork.
        left=n.t(pg,[30,start,95,end],reading_order='vertical');right=n.t(pg,[96,start,157,end],reading_order='vertical');op=n.t(pg,c[1],reading_order='vertical');fun=n.t(pg,c[2],reading_order='vertical');rows.append([left+' '+right,op,fun])
        kinds=[('power','usb'),('power','ac'),('usb','ac'),('dc','ac')][i]
        parts=[]
        for j,(kind,name) in enumerate(zip(kinds,[left,right],strict=True)):
            if j:parts.append(node('inline_group',[],presentation=attrs('hb-key-button-plus')))
            image='assets/button-'+kind+'-bottom.svg'
            parts.append(node('group',[node('image',source=image,alt=''),paragraph(name)],role='container',presentation=attrs('hb-key-button')))
        first=node('table_cell',[node('group',parts,role='container',presentation=attrs('hb-key-button-pair'))],header=False)
        dur=re.search(r'^(\d+\s*(?:secondes|segundos|s)\b)',op)
        second=node('table_cell',[paragraph(op)],header=False)
        if dur:
            value=dur[0];second['children']=[node('inline_group',[text(value)],presentation={'html':{'attributes':{'class':'hb-key-duration','data-duration-icon':'clock'}}}),paragraph(op[len(value):].strip())]
        carriers.append(node('table_row',[first,second,cell(fun)]))
    spec=key_combinations_component_spec(headers=header,rows=rows,source_ref=f'native-pdf/page-{pg}/key-combinations',language=n.language)
    carrier=node('table',[node('table_head',[node('table_row',[cell(v,header=True) for v in header])]),node('table_body',carriers)],presentation=attrs('hb-key-combination-table'))
    n.add(component_flow_node(spec,carrier_flow=[carrier],root=True))


def warranty(n,pg):
    lead=n.t(pg,[25,50,345,82]);note=n.t(pg,[25,82,345,98])
    n.add(n.comp(warranty_lead_component_spec,accessibility_label=n.current['title'],lead_html='<strong>'+html.escape(lead)+'</strong>',local_note_html=html.escape(note)))
    titles=[]
    for block in n.doc[pg-1].get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            raw=''.join(s['text'] for s in line['spans'])
            if 96<line['bbox'][1]<470 and line['bbox'][0]<50 and len(raw)<100 and any(6.8<s['size']<8.5 and 'Bold' in s['font'] for s in line['spans']):titles.append((line['bbox'],normalize(raw)))
    titles.sort(key=lambda v:v[0][1]);assert len(titles)==6,(n.language,titles)
    for i,(box,title) in enumerate(titles):
        n.t(pg,expanded(box));end=titles[i+1][0][1] if i<5 else 500
        n.add(heading(title,level=3))
        if i==1:
            # Source columns have independent standard/extended warranties.
            body_y={'en':213,'fr':223,'es':219}[n.language]
            labels=[n.t(pg,[35,box[3],214,body_y]),n.t(pg,[216,box[3],345,body_y])]
            bodies=[n.t(pg,[35,body_y,214,end]),n.t(pg,[216,body_y,345,end])];periods=[]
            unit={'en':'YEARS','fr':'ANS','es':'AÑOS'}[n.language]
            for number,raw,body in zip(['5','2'],labels,bodies,strict=True):
                clean=re.sub(r'\b(?:5|2|YEARS|ANS|A?ÑOS)\b','',raw).strip();periods.append({'number':number,'unit':unit,'label':clean,'body_html':html.escape(body),'body_text':body})
            n.add(n.comp(warranty_years_component_spec,title=title,periods=periods))
        else:
            _,raw,_=n.take(pg,[25,box[3],345,end],unused=True,reading_order='vertical');blocks=[]
            for v in prose(raw):
                if v['kind']=='list':
                    values=[c['children'][0]['text'] for c in v['children']];blocks.append({'kind':'list','items':values,'html':'<ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in values)+'</ul>'})
                else:
                    value=v['children'][0]['text'];blocks.append({'kind':'paragraph','text':value,'html':html.escape(value)})
            n.add(n.comp(warranty_section_component_spec,title=title,section_index=i+1,blocks=blocks))


def make(language):
    n=Native(language);p=n.page
    # Preface is native-language copy. The EN/FR/ES region badge is outlined.
    starts={'en':(20,131),'fr':(132,244),'es':(245,355)};y0,y1=starts[language]
    blocks=[b for b in n.doc[1].get_text('blocks') if y0<=b[1]<y1]
    titlebox=min(blocks,key=lambda b:b[1]);title=n.t(2,expanded(titlebox[:4]));title=re.sub(r'\b(?:US|FR|ES)\b','',title).strip();n.chapter('preface',language.upper()+' '+title)
    n.current['nodes'][0].update(level=1,presentation=attrs('hb-preface-heading'))
    n.current['nodes'][0]['children']=[node('inline_group',[text(language.upper())],presentation=attrs('hb-preface-region')),text(' '+title)]
    auto_prose(n,2,[20,y0,348,y1]);pre=n.current['nodes'][1:];n.current['nodes'][1:]=[];n.add(node('group',pre,role='container',presentation=attrs('hb-preface-prose')))
    chapters={4:'safety',6:'inbox',8:'lcd',10:'operations',13:'ups',14:'connections',15:'charging',19:'storage',20:'app',22:'warranty',23:'specifications',24:'ess',25:'ess-host',26:'ess-battery'}
    for ep in range(4,28):
        pg=p(ep);page=n.doc[pg-1];events=[]
        if ep in chapters:
            box=[25,20,260,79 if ep==24 and language!='en' else 62 if ep==24 else 49]
            events.append((20,'chapter',(chapters[ep],box)))
        if ep==5:
            # Maintenance, signal symbols and FCC are separate shared chapters.
            events.extend([(20,'chapter',('maintenance',[25,20,345,41])),(70,'chapter',('symbols',[25,70,345,95]))])
            tabs=page.find_tables().tables
            events.append((tabs[0].bbox[1],'symbols',None))
            # FCC closing paragraph is in source two-column reading order.
            events.append((390,'fcc',None))
        if ep==6:events.append((228,'chapter',('overview',[25,226,345,249])))
        if ep==12:
            tabs=page.find_tables().tables;events.append((tabs[0].bbox[1],'combinations',tabs[0]));events.append((230,'chapter',('troubleshooting',[25,225,345,253])));events.append((tabs[1].bbox[1],'table',tabs[1]))
        if ep==26:
            events.append((50,'heading-pair',[25,50,250,64]))
            events.append((319,'chapter',('ess-sts',[25,315,245,340])))
            events.append((342,'heading-pair',[25,342,250,358]))
        if ep==27:events.append((139,'chapter',('ess-package',[25,136,345,163])))
        figs=[g for g in n.figures.values() if g['page']==ep and not g['id'].startswith('inbox')]
        figboxes=[g.get('locale_boxes',{}).get(language,g['bbox']) for g in figs]
        # Preclaim figure text so ordinary prose never duplicates labels.
        figure_nodes={g['id']:emit_figure(n,g) for g in figs}
        for g,b in zip(figs,figboxes,strict=True):events.append((b[1],'figure',g['id']))
        notices=native_callouts(n,pg,figboxes)
        for y,box,labelbox,variant in notices:events.append((y,'callout',(box,labelbox,variant)))
        if ep in (23,25,26,27):
            for t in page.find_tables().tables:
                if ep==27:continue
                events.append((t.bbox[1]-18,'spec',t))
            if ep==26:
                events.append((185,'bp-ports',None))
        if ep==8:events.append((239,'lcd',None))
        if ep==9:
            # Both LCD pages have already been claimed by the one shared glossary.
            continue
        if ep==22:events.append((49,'warranty',None))
        if ep==6:events.append((49,'inbox',None))
        if ep==20:events.append((68,'app-download',None))
        if ep==21:
            # Native App titles can share a PDF block with regular body copy.
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    spans=[s for s in line['spans'] if s['text'].strip()]
                    if spans and re.match(r'^[34]\.',normalize(' '.join(s['text'] for s in spans))) and all('Bold' in s['font'] and s['size']>=9 for s in spans):
                        events.append((line['bbox'][1],'app-heading',expanded(line['bbox'])))
        if ep==4:
            # Safety reading order is left column then right column, before operations.
            identity,box=events.pop(0)[2];n.chapter(identity,n.t(pg,box));heading_pair(n,pg,[55,53,345,82])
            warning=next(b for b in page.get_text('dict')['blocks'] if b.get('lines') and any('WARNING'==z['text'].strip() or 'AVERTISSEMENT'==z['text'].strip() or 'ADVERTENCIA'==z['text'].strip() or 'ATTENTION'==z['text'].strip() for line in b['lines'] for z in line['spans']))
            lines=warning['lines'];warning_label=n.t(pg,expanded(lines[0]['bbox']));bodybox=[warning['bbox'][0],lines[1]['bbox'][1],warning['bbox'][2],warning['bbox'][3]];body=n.take(pg,expanded(bodybox),unused=True)[1]
            n.add(callout(display_label(warning_label),prose(body),variant='warning',language=language,source_ref=f'native-pdf/page-{pg}/warning'))
            titles=sorted([b for b in page.get_text('blocks') if 258<b[1]<295 and len(b[4])<100],key=lambda b:b[1])
            op,save=titles
            left=n.take(pg,[25,129,187,op[1]],unused=True)[1];right=n.take(pg,[187,82,345,op[1]],unused=True)[1];n.add(*prose(left+'\n'+right))
            heading_pair(n,pg,expanded(op[:4]));value=n.t(pg,expanded(save[:4]),unused=True);n.add(node('paragraph',[node('strong',[text(value)])]))
            left=n.take(pg,[25,save[3],187,462],unused=True)[1];right=n.take(pg,[187,save[3],345,462],unused=True)[1];n.add(*prose(left+'\n'+right))
            danger={'en':'DANGER','fr':'DANGER','es':'PELIGRO'}[language];n.take(pg,[20,462,55,500],purpose='source-danger-badge',unused=True);body=n.t(pg,[55,462,345,500],unused=True)
            if body:n.add(callout(danger,[paragraph(body)],variant='danger',language=language,source_ref=f'native-pdf/page-{pg}/outlined-danger'))
            auto_prose(n,pg);continue
        last_y=20
        for y,kind,value in sorted(events,key=lambda e:e[0]):
            if y>last_y:auto_prose(n,pg,[20,last_y,348,y])
            if kind=='chapter':
                identity,box=value;title=n.t(pg,box,unused=True);n.chapter(identity,title);last_y=max(last_y,box[3])
            elif kind=='heading-pair':heading_pair(n,pg,value);last_y=max(last_y,value[3])
            elif kind=='app-heading':n.add(heading(n.t(pg,value,unused=True),level=3));last_y=max(last_y,value[3])
            elif kind=='figure':n.add(figure_nodes[value]);last_y=max(last_y,n.figures[value].get('locale_boxes',{}).get(language,n.figures[value]['bbox'])[3])
            elif kind=='callout':emit_callout(n,pg,*value);last_y=max(last_y,value[0][3])
            elif kind=='symbols':symbols(n,pg);last_y=max(last_y,page.find_tables().tables[2].bbox[3])
            elif kind=='fcc':
                n.chapter('fcc','FCC');cut={'en':190,'fr':183.8,'es':189}[language];left=n.t(pg,[25,390,cut,500],unused=True);_,right,_=n.take(pg,[cut,390,345,500],unused=True,reading_order='vertical')
                intro,*items=re.split(r'(?:^|\n)\s*(?:--|[•·–—])\s+',right)
                # The first sentence continues across the two native columns.
                full=normalize(left+' '+intro);match=re.match(r'^([^:]+):\s*(.*)',full)
                leftlabel,leftbody=(match[1]+':',match[2]) if match else ('',full)
                last=items.pop() if items else ''
                tail=re.split(r'\n(?=[A-ZÀ-Ý][A-ZÀ-Ý ]+:)',last,maxsplit=1)
                items.append(tail[0]);mod=normalize(tail[1]) if len(tail)>1 else ''
                match=re.match(r'^([^:]+):\s*(.*)',mod)
                rightblocks=[{'kind':'list','items':[normalize(v) for v in items]}]
                if mod:rightblocks.append({'kind':'paragraph','label':match[1]+':' if match else '', 'text':match[2] if match else mod})
                n.add(n.comp(fcc_component_spec,accessibility_label='FCC',opening_copy=[],mark_asset_ref='assets/fcc-mark.svg',left_blocks=[{'kind':'paragraph','label':leftlabel,'text':leftbody}],right_blocks=rightblocks));last_y=500
            elif kind=='lcd':lcd(n);last_y=500
            elif kind=='spec':semantic_table(n,pg,value,spec=True);last_y=max(last_y,value.bbox[3])
            elif kind=='table':semantic_table(n,pg,value);last_y=max(last_y,value.bbox[3])
            elif kind=='combinations':combinations(n,pg,value);last_y=max(last_y,value.bbox[3])
            elif kind=='bp-ports':
                title=n.t(pg,[25,185,345,200],unused=True);rows=[[n.t(pg,[25,y0,164,y1],unused=True),n.t(pg,[164,y0,345,y1],unused=True)] for y0,y1 in [(200,212),(212,229)]];n.add(n.comp(spec_table_component_spec,section_title=title,rows=rows));last_y=229
            elif kind=='warranty':warranty(n,pg);last_y=500
            elif kind=='inbox':
                n.take(pg,[25,60,345,85],purpose='shared-inbox-live-ordinal')
                cards=[]
                for box,asset in [([25,155,110,181],'inbox-main.svg'),([110,155,185,181],'inbox-cable.png'),([185,155,260,181],'inbox-mc4.svg'),([260,155,345,181],'inbox-manual.svg')]:
                    label=n.t(pg,box);cards.append({'image_ref':'assets/'+asset,'label':label,'alt':label})
                label=n.t(pg,[25,190,64,222]);body=n.t(pg,[65,190,345,222]);n.add(n.comp(inbox_component_spec,accessibility_label=n.current['title'],cards=cards,tip_label=display_label(label),tip_body=body,require_tip=True,variant='responsive-card-grid'));last_y=224
                # Physical tiny book printing is part of this picture, now also live.
                for g in n.figures.values():
                    if g['id'].startswith('inbox'):n.take(pg,g['bbox'],purpose='fixed-product-markings/inbox')
            elif kind=='app-download':
                cols=[{'role':'store','text':n.t(pg,[45,120,187,156])},{'role':'qr','text':n.t(pg,[195,120,345,156])}]
                for v in cols:v['html']=html.escape(v['text'])
                n.add(n.comp(app_download_component_spec,accessibility_label='App download',columns=cols,source_art_ref='assets/app_store_badges.png',store_art_ref='assets/app_store_badges.png',qr_art_ref='assets/app_download_qr.png'));last_y=155
        auto_prose(n,pg,[20,last_y,348,500])
        # Every residual token is reviewed instead of silently being discarded.
        auto_prose(n,pg)
    n.chapter('contact',{'en':'CONTACT US','fr':'CONTACTEZ-NOUS','es':'CONTÁCTENOS'}[language]);auto_prose(n,76,[0,0,369,525])
    missing=n.finish();print(language,'chapters',len(n.chapters),'unmapped',len(missing));return missing


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--languages',nargs='+',choices=['en','fr','es'],default=['en','fr','es']);args=parser.parse_args()
    old=SOURCE/'source/unmapped.json';results=json.loads(old.read_text()) if old.exists() else {};results.update({l:make(l) for l in args.languages});dump(old,results)
    framepath=SOURCE/'source/caption_frames.json';frames=json.loads(framepath.read_text()) if framepath.exists() else {};frames.update(CAPTION_FRAMES);dump(framepath,frames)
    previous=(SOURCE/'source/presentation.css').read_text();base=previous.split('/* Source-derived label geometry */')[0]
    retained=[line for line in previous.split('/* Source-derived label geometry */')[-1].splitlines() if line.startswith('html[lang=') and not any(line.startswith('html[lang="'+language+'"]') for language in args.languages)]
    (SOURCE/'source/presentation.css').write_text(base+'/* Source-derived label geometry */\n'+'\n'.join(retained+CSS)+'\n')
