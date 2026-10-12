"""Retain exact outlined physical book printing on the shared inbox picture.

Exterior captions remain live HTML. Only glyph uses inside the native book
crop are recovered from text-as-path SVG; no external font is substituted.
"""
from pathlib import Path
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy

REPO = next(p for p in Path(__file__).resolve().parents if (p/'build.py').is_file())
sys.path.insert(0,str(REPO))
import fitz
from tools.asset_pipeline.native_svg import native_art_svg

SOURCE=Path(__file__).resolve().parents[1]
SVG='{http://www.w3.org/2000/svg}'
XLINK='{http://www.w3.org/1999/xlink}'

def restore():
    g=next(g for g in json.loads((SOURCE/'source/figures.json').read_text()) if g['id']=='inbox-manual')
    with fitz.open(SOURCE/'Jackery HomePower 5000 Plus.pdf') as doc:
        page=doc[g['page']-1];box=fitz.Rect(g['bbox'])
        raw=native_art_svg(page,g['drawing_indices'],g['bbox'])
        base=ET.fromstring(raw);full=ET.fromstring(page.get_svg_image(text_as_path=True))
        uses=[]
        for e in full.iter(SVG+'use'):
            matrix=fitz.Matrix(*map(float,re.split(r'[,\s]+',e.get('transform')[7:-1])))
            if box.contains(fitz.Point(matrix.e,matrix.f)):uses.append(deepcopy(e))
        if not uses:raise ValueError('native physical book glyphs missing')
        ids={e.get(XLINK+'href')[1:] for e in uses}
        defs=ET.SubElement(base,SVG+'defs')
        for e in full.iter():
            if e.get('id') in ids:defs.append(deepcopy(e))
        group=ET.SubElement(base,SVG+'g',{'data-native-physical-markings':'inbox-book'})
        group.extend(uses)
        ET.register_namespace('','http://www.w3.org/2000/svg')
        ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
        result=ET.tostring(base,encoding='utf-8',xml_declaration=True)
        (SOURCE/'assets/inbox-manual.svg').write_bytes(result)
        evidence={'base_sha256':hashlib.sha256(raw).hexdigest(),'final_sha256':hashlib.sha256(result).hexdigest(),
                  'page':g['page'],'crop':g['bbox'],'native_outlined_glyphs':len(uses),
                  'purpose':'fixed physical book printing only; exterior captions stay live HTML'}
        (SOURCE/'source/physical_markings.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence))

if __name__=='__main__':restore()
