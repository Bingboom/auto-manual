"""Check final browser ink, loaded images and source figure layout at three widths.

Requires Playwright Chromium. Serve strict Sphinx outputs under /ja.
Evidence is written outside the frozen source package, never into its inventory.
"""
from __future__ import annotations

import argparse
import asyncio
from io import BytesIO
import json
from pathlib import Path

import fitz
from PIL import Image
from playwright.async_api import async_playwright

PACKAGE = Path(__file__).resolve().parent
CHAPTERS = tuple('native-'+c["id"] for c in json.loads((PACKAGE/"source/ja/content.json").read_text())["chapters"])
FIGURES = tuple(g["id"] for g in json.loads((PACKAGE/"source/figures.json").read_text()) if not g["id"].startswith("inbox"))
SPECIFICATION_TITLE = next(
    slot["content"]
    for slot in json.loads((PACKAGE / "source/ja/content.json").read_text())["chapters"][0]["nodes"][1]["component_spec"]["slots"]
    if slot["role"] == "section_title"
)
with fitz.open(next(PACKAGE.glob('*.pdf'))) as native_pdf:
    drawings = native_pdf[3].get_drawings()
    LCD_CIRCLE_CENTERS = [
        {'number': number, 'x': ((drawings[index]['rect'].x0 + drawings[index]['rect'].x1) / 2 - 70) / 214,
         'y': ((drawings[index]['rect'].y0 + drawings[index]['rect'].y1) / 2 - 54) / 62}
        for number, index in [(1, 2032), (2, 2034)]
    ]
    lock_drawings = native_pdf[4].get_drawings()
    LOCK_CIRCLES = [
        {'line': line, 'number': number,
         'x': ((lock_drawings[index]['rect'].x0 + lock_drawings[index]['rect'].x1) / 2 - 27) / 316,
         'y': ((lock_drawings[index]['rect'].y0 + lock_drawings[index]['rect'].y1) / 2 - 270) / 230,
         'radius': lock_drawings[index]['rect'].width / 2 / 316}
        for line, number, index in [(2, 1, 3793), (3, 2, 3794), (4, 1, 3791), (5, 2, 3792)]
    ]
CHECK = r"""() => {
 const root=document.querySelector('[role=main]');
 const labels=[...root.querySelectorAll('.hb-reference-live-label')];
 const outside=[],overlaps=[],clippedCards=[],occluded=[],clippedCells=[];
 const textRects=e=>{
  const tree=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),rects=[];
  while(tree.nextNode()){
   if(!tree.currentNode.textContent.trim())continue;
   const range=document.createRange();range.selectNodeContents(tree.currentNode);
   rects.push(...range.getClientRects());
  }
  return rects.filter(q=>q.width>0);
 };
 const inks=labels.map(e=>{
  const rects=textRects(e),panel=e.closest('.hb-reference-art-panel').getBoundingClientRect();
  for(const q of rects)if(q.left<panel.left-2||q.right>panel.right+2||q.top<panel.top-2||q.bottom>panel.bottom+2)
   outside.push({figure:e.closest('figure').dataset.referenceId,text:e.innerText});
  return {element:e,figure:e.closest('figure'),id:e.closest('figure').dataset.referenceId,text:e.innerText,rects};
 });
 for(let i=0;i<inks.length;i++)for(let j=i+1;j<inks.length;j++)if(inks[i].figure===inks[j].figure){
  if(inks[i].rects.some(a=>inks[j].rects.some(b=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>1.5&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1.5)))
   overlaps.push({figure:inks[i].id,a:inks[i].text,b:inks[j].text});
 }
 // A later opaque caption plate can hide ink without moving its Range.
 for(const ink of inks)for(const plate of inks)if(ink!==plate&&ink.figure===plate.figure){
  const style=getComputedStyle(plate.element),r=plate.element.getBoundingClientRect();
  const painted=style.backgroundImage!=='none'||!['transparent','rgba(0, 0, 0, 0)'].includes(style.backgroundColor);
  if(painted&&ink.rects.some(q=>Math.min(q.right,r.right)-Math.max(q.left,r.left)>2&&Math.min(q.bottom,r.bottom)-Math.max(q.top,r.top)>2))
   occluded.push({figure:ink.id,ink:ink.text,plate:plate.text});
 }
 for(const e of root.querySelectorAll('.hb-inbox-label')){
  const card=e.closest('.hb-inbox-card').getBoundingClientRect();
  if(textRects(e).some(q=>q.left<card.left-2||q.right>card.right+2||q.top<card.top-2||q.bottom>card.bottom+2))
   clippedCards.push(e.innerText);
 }
 for(const e of root.querySelectorAll('td,th')){
  const r=e.getBoundingClientRect();
  if(textRects(e).some(q=>q.left<r.left-2||q.right>r.right+2||q.top<r.top-2||q.bottom>r.bottom+2))
   clippedCells.push({table:e.closest('table').className,text:e.innerText,reason:'cell bounds'});
  for(const q of textRects(e)){
   let scrollX=false,scrollY=false;
   for(let p=e.parentElement;p&&p!==root;p=p.parentElement){
    const style=getComputedStyle(p),a=p.getBoundingClientRect();
    if(['auto','scroll'].includes(style.overflowX)&&p.scrollWidth>p.clientWidth+2)scrollX=true;
    if(['auto','scroll'].includes(style.overflowY)&&p.scrollHeight>p.clientHeight+2)scrollY=true;
    if((!scrollX&&['hidden','clip'].includes(style.overflowX)&&(q.left<a.left-2||q.right>a.right+2))||
       (!scrollY&&['hidden','clip'].includes(style.overflowY)&&(q.top<a.top-2||q.bottom>a.bottom+2)))
     clippedCells.push({table:e.closest('table').className,text:e.innerText,reason:'ancestor '+p.className});
   }
  }
 }
 const emptyArtwork=[];
 for(const img of root.querySelectorAll('img')){
  const canvas=document.createElement('canvas');canvas.width=96;canvas.height=96;
  const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0,96,96);
  const pixels=ctx.getImageData(0,0,96,96).data;let ink=0;
  for(let i=0;i<pixels.length;i+=4)if(pixels[i+3]>20&&Math.min(pixels[i],pixels[i+1],pixels[i+2])<240)ink++;
  if(ink<5)emptyArtwork.push(img.src);
 }
 const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
 const duplicateIds=[...new Set(ids.filter((id,i)=>ids.indexOf(id)!==i))];
 const recycling=(()=>{
  const panel=root.querySelector('.native-recycle'),heading=panel?.querySelector('h2,h3');
  const icon=panel?.querySelector('img'),items=panel?[...panel.querySelectorAll('li')]:[];
  const s=panel?getComputedStyle(panel):null,r=panel?.getBoundingClientRect();
  const iconWidth=icon?.getBoundingClientRect().width||0;
  const clipped=panel?textRects(panel).some(q=>q.left<r.left-1||q.right>r.right+1||q.top<r.top-1||q.bottom>r.bottom+1):true;
  const bordered=s&&['Top','Right','Bottom','Left'].every(side=>parseFloat(s['border'+side+'Width'])>0&&s['border'+side+'Style']==='solid')&&parseFloat(s.borderTopLeftRadius)>0;
  const liveBullets=items.length===3&&items.every(e=>getComputedStyle(e).display==='list-item'&&getComputedStyle(e).listStyleType==='disc');
  const square=root.querySelector('.native-spec-change-notice');
  const squareStyle=square?getComputedStyle(square,'::before'):null;
  const squareMarker=squareStyle&&parseFloat(squareStyle.width)>0&&squareStyle.width===squareStyle.height&&squareStyle.backgroundColor!=='rgba(0, 0, 0, 0)';
  const titleInside=heading&&getComputedStyle(heading,'::before').content==='none';
  return {bordered,liveBullets,titleInside:!!titleInside,iconWidth,squareMarker,clipped,
   passed:!!(bordered&&liveBullets&&titleInside&&iconWidth>=50&&squareMarker&&!clipped)};
 })();
 const warranty=(()=>{
  const intro=root.querySelector('.native-warranty-intro');
  const note=root.querySelector('.native-warranty-note');
  const panels=[...root.querySelectorAll('.native-warranty-terms')];
  const rows=panels.flatMap(p=>[...p.children]);
  const filledRounded=e=>{
   if(!e)return false;
   const s=getComputedStyle(e),rgb=s.backgroundColor.match(/[\d.]+/g)?.map(Number);
   return rgb?.length>=3&&Math.max(...rgb.slice(0,3))<250&&
    Math.max(...rgb.slice(0,3))-Math.min(...rgb.slice(0,3))<8&&parseFloat(s.borderTopLeftRadius)>0;
  };
  const bounded=e=>{
   const r=e.getBoundingClientRect();
   return textRects(e).every(q=>q.left>=r.left-1&&q.right<=r.right+1&&q.top>=r.top-1&&q.bottom<=r.bottom+1);
  };
  const groups=panels.map(p=>[...p.children].map(c=>Number(c.innerText.match(/^\d+/)?.[0])));
  const exclusions=[...root.querySelectorAll('.native-warranty-exclusion')];
  const exclusionOrder=exclusions.map(e=>Number(e.innerText.match(/^\((\d+)\)/)?.[1]));
  const panelBorders=panels.map(e=>{
   const s=getComputedStyle(e);
   return ['Top','Right','Bottom','Left'].every(side=>parseFloat(s['border'+side+'Width'])>0&&s['border'+side+'Style']==='solid')&&parseFloat(s.borderTopLeftRadius)>0;
  });
  const separators=panels.map(p=>[...p.children].slice(1).every(e=>{
   const s=getComputedStyle(e);return parseFloat(s.borderTopWidth)>0&&s.borderTopStyle==='solid';
  }));
  const clause2=rows[1]?.querySelectorAll(':scope > p');
  const secondParagraph=clause2?.length===2&&parseFloat(getComputedStyle(clause2[1]).marginTop)>0;
  const clipped=rows.filter(e=>!bounded(e)).map(e=>e.innerText);
  if(intro&&!bounded(intro))clipped.push(intro.innerText);
  if(note&&!bounded(note))clipped.push(note.innerText);
  const passed=JSON.stringify(groups)==='[[1,2,3,4,5,6,7],[8,9,10,11]]'&&
   JSON.stringify(exclusionOrder)==='[1,2,3,4,5,6,7]'&&
   exclusions.every(e=>e.closest('.native-warranty-clause')===rows[4])&&
   panelBorders.every(Boolean)&&separators.every(Boolean)&&secondParagraph&&
   filledRounded(intro)&&filledRounded(note)&&!clipped.length;
  return {groups,exclusionOrder,panelBorders,separators,secondParagraph,
   introGray:filledRounded(intro),noteGray:filledRounded(note),clipped,passed};
 })();
 return {
  specHeading:(()=>{
   const heading=root.querySelector('h2.hb-spec-group');
   return heading?{text:heading.innerText,raw:heading.textContent,
    transform:getComputedStyle(heading).textTransform,
    marker:getComputedStyle(heading,'::before').content}:null;
  })(),
  recycling,warranty,emptyArtwork,duplicateIds,clippedCells,bodyText:(()=>{
   const tree=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),parts=[];
   while(tree.nextNode()){
    const parent=tree.currentNode.parentElement,style=getComputedStyle(parent);
    if(parent.closest('[hidden],[aria-hidden=true],script,style')||style.visibility==='hidden')continue;
    const range=document.createRange();range.selectNodeContents(tree.currentNode);
    if([...range.getClientRects()].some(r=>r.width>0&&r.height>0))parts.push(tree.currentNode.textContent);
   }
   return parts.join('');
  })(),
  pageWidth:document.documentElement.scrollWidth,viewport:innerWidth,
  broken:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),
  imageCount:document.images.length,liveLabels:labels.length,outside,overlaps,occluded,clippedCards,
  headings:[...root.querySelectorAll('h1,h2,h3')].map(e=>({tag:e.tagName,text:e.innerText,font:getComputedStyle(e).fontSize,weight:getComputedStyle(e).fontWeight})),
  figures:[...root.querySelectorAll('figure[data-reference-id]')].map(e=>({id:e.dataset.referenceId,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})),
  boldWeights:[...root.querySelectorAll('.hb-reference-live-label strong')].map(e=>getComputedStyle(e).fontWeight),
  scrollSurfaces:[...root.querySelectorAll('.native-dense,.native-lcd,.native-controls')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>e.className),
 };
} """


def lcd_numeral_centers(png: bytes) -> list[dict]:
    """Measure rendered white digit ink against the unchanged dark circles."""
    image = Image.open(BytesIO(png)).convert("RGB")
    width, height = image.size
    pixels = image.load()
    records = []
    # The two circles are isolated at the bottom outer edges of the native art.
    for number, left, right in [(1, 0, 0.2), (2, 0.8, 1)]:
        dark = [(x, y) for y in range(int(height * 0.66), height)
                for x in range(int(width * left), int(width * right))
                if max(pixels[x, y]) < 120]
        if not dark:
            records.append({"number": number, "centered": False, "reason": "circle missing"})
            continue
        x0, x1 = min(x for x, _ in dark), max(x for x, _ in dark)
        y0, y1 = min(y for _, y in dark), max(y for _, y in dark)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        radius = min(x1 - x0, y1 - y0) / 2
        white = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
                 if (x - cx) ** 2 + (y - cy) ** 2 < (radius * 0.9) ** 2
                 and min(pixels[x, y]) > 160]
        if not white:
            records.append({"number": number, "centered": False, "reason": "digit missing"})
            continue
        ink_x = (min(x for x, _ in white) + max(x for x, _ in white)) / 2
        ink_y = (min(y for _, y in white) + max(y for _, y in white)) / 2
        tolerance = max(1, radius * 0.12)
        records.append({"number": number, "offset_x_px": round(ink_x - cx, 2),
                        "offset_y_px": round(ink_y - cy, 2),
                        "tolerance_px": round(tolerance, 2),
                        "centered": max(abs(ink_x - cx), abs(ink_y - cy)) <= tolerance})
    return records


def lock_numeral_center(png: bytes, circle: dict) -> dict:
    """Measure one visible digit; locator screenshots also reveal scrolled circles."""
    image = Image.open(BytesIO(png)).convert('RGB')
    width, height = image.size
    pixels = image.load()
    dark = [(x, y) for y in range(height) for x in range(width) if max(pixels[x, y]) < 120]
    if not dark:
        return {'line': circle['line'], 'centered': False, 'reason': 'circle missing'}
    x0, x1 = min(x for x, _ in dark), max(x for x, _ in dark)
    y0, y1 = min(y for _, y in dark), max(y for _, y in dark)
    cx, cy, radius = (x0+x1)/2, (y0+y1)/2, min(x1-x0, y1-y0)/2
    # At 14px, the white 1 stem can rasterize at 140–154 over a 41-gray circle.
    # Include this visible antialiased ink while excluding the circle and rim.
    white = [(x, y) for y in range(height) for x in range(width)
             if (x-cx)**2+(y-cy)**2 < (radius*.82)**2 and min(pixels[x, y]) > 100]
    if not white:
        return {'line': circle['line'], 'centered': False, 'reason': 'digit missing'}
    dx = (min(x for x, _ in white)+max(x for x, _ in white))/2-cx
    dy = (min(y for _, y in white)+max(y for _, y in white))/2-cy
    tolerance = max(1, radius*.18)
    return {'line': circle['line'], 'number': circle['number'],
            'offset_x_px': dx, 'offset_y_px': dy, 'tolerance_px': tolerance,
            'centered': max(abs(dx), abs(dy)) <= tolerance}


async def validate(base_url, languages, evidence_dir):
    evidence_dir.mkdir(parents=True, exist_ok=False)
    records = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        for language in languages:
            for width, height in [(1280, 900), (768, 1024), (390, 844)]:
                page = await browser.new_page(
                    viewport={"width": width, "height": height}, device_scale_factor=1,
                )
                errors = []
                resource_errors = []
                page.on("pageerror", lambda error, sink=errors: sink.append(str(error)))
                page.on("response", lambda response, sink=resource_errors: sink.append({"url": response.url, "status": response.status}) if response.status >= 400 else None)
                await page.goto(
                    f"{base_url.rstrip('/')}/{language}/manual_jbp5000a_jp_{language}.html",
                    wait_until="domcontentloaded",
                )
                await page.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
                await page.evaluate("document.fonts.ready")
                await page.wait_for_function("[...document.images].every(i=>i.complete&&i.naturalWidth>0)")
                info = await page.evaluate(CHECK)
                title = info['specHeading']
                info['specHeadingMatchesSource'] = bool(
                    title and title['text'] == title['raw'] == SPECIFICATION_TITLE
                    and title['transform'] == 'none' and title['marker'] == 'none'
                )
                lcd = page.locator('figure[data-reference-id="lcd-map"]')
                info['lcdLabelCenters'] = await lcd.evaluate("""(e,centers)=>{
                    const image=e.querySelector('img').getBoundingClientRect();
                    return [...e.querySelectorAll('.hb-reference-live-label')].map(label=>{
                        const r=label.getBoundingClientRect();
                        const number=Number(label.innerText),source=centers.find(c=>c.number===number);
                        const dx=r.left+r.width/2-image.left-source.x*image.width;
                        const dy=r.top+r.height/2-image.top-source.y*image.height;
                        return {number,offset_x_px:dx,offset_y_px:dy,centered:Math.max(Math.abs(dx),Math.abs(dy))<=0.5};
                    });
                }""", LCD_CIRCLE_CENTERS)
                lcd_png = await lcd.screenshot()
                (evidence_dir / f'{language}-{width}-lcd-numerals.png').write_bytes(lcd_png)
                info['lcdNumeralCenters'] = lcd_numeral_centers(lcd_png)
                lock = page.locator('figure[data-reference-id="locking-connection"]')
                info['lockLabelCenters'] = await lock.evaluate("""(e,circles)=>{
                    const image=e.querySelector('img').getBoundingClientRect();
                    return circles.map(source=>{
                        const label=e.querySelector(`[data-source-line="${source.line}"]`);
                        const r=label.getBoundingClientRect();
                        const dx=r.left+r.width/2-image.left-source.x*image.width;
                        const dy=r.top+r.height/2-image.top-source.y*image.height;
                        return {line:source.line,number:Number(label.innerText),offset_x_px:dx,offset_y_px:dy,
                            centered:Number(label.innerText)===source.number&&Math.max(Math.abs(dx),Math.abs(dy))<=0.5};
                    });
                }""", LOCK_CIRCLES)
                lock_png = await lock.screenshot()
                (evidence_dir / f'{language}-{width}-lock-numerals.png').write_bytes(lock_png)
                info['lockNumeralCenters'] = []
                for circle in LOCK_CIRCLES:
                    digit_png = await lock.locator(f'[data-source-line="{circle["line"]}"]').screenshot()
                    (evidence_dir / f'{language}-{width}-lock-digit-{circle["line"]}.png').write_bytes(digit_png)
                    info['lockNumeralCenters'].append(lock_numeral_center(digit_png, circle))
                coverage=json.loads((PACKAGE/'source/ja/coverage.json').read_text())
                normalize=lambda s: ''.join(s.split())
                body=normalize(info.pop('bodyText'))
                live=[v for v in coverage['selections'] if v['purpose'].startswith('live')]
                missing=[v for v in live if normalize(v.get('rendered_text',v['text'])) not in body]
                info['visibleCopyCoverage']={'live_selections':len(live),'missing':missing}
                info.update(language=language, width=width, height=height, errors=errors, resourceErrors=resource_errors)
                records.append(info)
                if width in [1280, 390]:
                    for anchor in CHAPTERS:
                        await page.evaluate("""id=>{
                          document.documentElement.style.scrollBehavior='auto';
                          window.scrollTo({top:Math.max(0,document.getElementById(id).getBoundingClientRect().top+window.scrollY-80),behavior:'instant'});
                        }""", anchor)
                        await page.screenshot(path=str(evidence_dir / f"{language}-{width}-{anchor}.png"))
                for index, panel in enumerate(await page.locator('.native-warranty-terms').all(), 1):
                    await panel.screenshot(path=str(evidence_dir/f'{language}-{width}-warranty-terms-{index}.png'))
                await page.locator('.native-recycle').screenshot(path=str(evidence_dir/f'{language}-{width}-recycling.png'))
                for name,selector in [('lcd-controls','.native-lcd-controls'),('key-combinations','.hb-key-combination-composition'),('spec-table','.hb-spec-table-composition'),('faults','.hb-reference-table-composition')]:
                    locator=page.locator(selector)
                    if await locator.count():
                        await locator.screenshot(path=str(evidence_dir/f'{language}-{width}-{name}.png'))
                if width == 1280:
                    for identity in FIGURES:
                        await page.locator(f'figure[data-reference-id="{identity}"]').screenshot(
                            path=str(evidence_dir / f"{language}-figure-{identity}.png"),
                        )
                await page.close()
        await browser.close()
    (evidence_dir / "browser_report.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
    )
    for row in records:
        print(json.dumps({k: row[k] for k in (
            "language", "width", "pageWidth", "imageCount", "liveLabels", "specHeading", "specHeadingMatchesSource", "lcdLabelCenters", "lcdNumeralCenters", "lockLabelCenters", "lockNumeralCenters", "recycling", "warranty", "broken",
            "outside", "overlaps", "occluded", "clippedCards", "clippedCells", "emptyArtwork", "duplicateIds", "visibleCopyCoverage", "errors", "resourceErrors",
        )}, ensure_ascii=False))
    if any(not row["recycling"]["passed"] or not row["warranty"]["passed"] or not row["specHeadingMatchesSource"] or not all(n["centered"] for n in row['lcdNumeralCenters'])
           or not all(n['centered'] for n in row['lcdLabelCenters'])
           or not all(n['centered'] for n in row['lockLabelCenters'])
           or not all(n['centered'] for n in row['lockNumeralCenters'])
           or row["pageWidth"] > row["width"] or row["broken"] or row["outside"]
           or row["emptyArtwork"] or row["clippedCells"] or row["duplicateIds"] or row["visibleCopyCoverage"]["missing"] or row["overlaps"] or row["occluded"] or row["clippedCards"] or row["errors"] or row["resourceErrors"] for row in records):
        raise ValueError("browser layout admission failed; inspect browser_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--languages", nargs="+", choices=("ja",), default=["ja"])
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(validate(args.base_url, args.languages, args.evidence_dir.resolve()))
