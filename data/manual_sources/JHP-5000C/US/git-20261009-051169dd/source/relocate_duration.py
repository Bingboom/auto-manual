"""Reuse the English panel, relocating only its clock to native locale anchors.

All paths/images remain unchanged. Ancestor transforms are respected, and the
exact base/derived hashes plus native drawing bounds are recorded for replay.
"""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

REPO = next(p for p in Path(__file__).resolve().parents if (p/'build.py').is_file())
sys.path.insert(0,str(REPO))
import fitz  # noqa: E402
from tools.asset_pipeline.native_svg import native_symbol_svg, SVG  # noqa: E402

SOURCE=Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def paths(root):
    parents={c:p for p in root.iter() for c in p}
    result=[]
    for path in root.iter(SVG+'path'):
        p=path
        ancestors=[]
        while p in parents:
            p=parents[p];ancestors.append(p)
        if any(p.tag==SVG+'defs' for p in ancestors):continue
        result.append((path,list(reversed(ancestors))))
    return result


def relocate():
    base=(SOURCE/'assets/power.svg').read_bytes()
    figures=json.loads((SOURCE/'source/figures.json').read_text())
    figure=next(g for g in figures if g['id']=='power')
    box=fitz.Rect(figure['bbox']);records=[]
    with fitz.open(SOURCE/'Jackery HomePower 5000 Plus.pdf') as doc:
        indices=[754,755];original=doc[9].get_drawings()[indices[0]]['rect']
        glyph=ET.fromstring(native_symbol_svg(doc[9],indices,list(original+(-.1,-.1,.1,.1))))
        signatures=[dict(p.attrib) for p,_ in paths(glyph)]
        if len(signatures)!=2:raise ValueError('clock must have two original paths')
        for language,physical in [('fr',34),('es',58)]:
            localized=doc[physical-1].get_drawings()[1495]['rect']
            frame=fitz.Rect(figure['locale_boxes'][language])
            dx=box.x0+(localized.x0-frame.x0)/frame.width*box.width-original.x0
            dy=box.y0+(localized.y0-frame.y0)/frame.height*box.height-original.y0
            root=ET.fromstring(base);parents={c:p for p in root.iter() for c in p};matched=0
            for path,ancestors in paths(root):
                if dict(path.attrib) not in signatures:continue
                matrix=fitz.Matrix(1,0,0,1,0,0)
                for ancestor in ancestors:
                    transform=ancestor.get('transform','')
                    if transform:
                        if not transform.startswith('matrix('):raise ValueError('unexpected clock ancestor transform')
                        values=[float(x) for x in transform[7:-1].replace(',',' ').split()]
                        matrix=fitz.Matrix(*values)*matrix
                inverse=~matrix
                local=fitz.Point(dx,dy)*fitz.Matrix(inverse.a,inverse.b,inverse.c,inverse.d,0,0)
                parent=parents[path];position=list(parent).index(path)
                group=ET.Element(SVG+'g',{'transform':f'translate({local.x:.8f},{local.y:.8f})'})
                parent.remove(path);group.append(path);parent.insert(position,group);matched+=1
            if matched!=2:raise ValueError('base clock paths not found exactly once')
            result=ET.tostring(root,encoding='utf-8',xml_declaration=True)
            destination=SOURCE/f'assets/power-{language}.svg';destination.write_bytes(result)
            figure.setdefault('locale_art',{})[language]=destination.name
            records.append({'language':language,'base_asset':'assets/power.svg','base_sha256':digest(base),
                            'asset_ref':f'assets/{destination.name}','asset_sha256':digest(result),
                            'native_physical_page':physical,'native_drawing_indices':[1495,1496],
                            'native_clock_bbox':list(localized),'native_figure_bbox':list(frame),
                            'base_drawing_indices':indices,'translation_in_base_points':[dx,dy],
                            'operation':'reuse every original path; translate only two clock paths'})
    (SOURCE/'source/figures.json').write_text(json.dumps(figures,indent=2)+'\n')
    (SOURCE/'source/duration_provenance.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))


if __name__=='__main__':
    relocate()
