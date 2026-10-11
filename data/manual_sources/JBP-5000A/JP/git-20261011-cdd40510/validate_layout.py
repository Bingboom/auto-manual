"""Check final browser ink, loaded images and source figure layout at three widths.

Requires Playwright Chromium. Serve strict Sphinx outputs under /ja.
Evidence is written outside the frozen source package, never into its inventory.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

PACKAGE = Path(__file__).resolve().parent
CHAPTERS = tuple('native-'+c["id"] for c in json.loads((PACKAGE/"source/ja/content.json").read_text())["chapters"])
FIGURES = tuple(g["id"] for g in json.loads((PACKAGE/"source/figures.json").read_text()) if not g["id"].startswith("inbox"))
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
 return {
  emptyArtwork,duplicateIds,clippedCells,bodyText:(()=>{
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
            "language", "width", "pageWidth", "imageCount", "liveLabels", "broken",
            "outside", "overlaps", "occluded", "clippedCards", "clippedCells", "emptyArtwork", "duplicateIds", "visibleCopyCoverage", "errors", "resourceErrors",
        )}, ensure_ascii=False))
    if any(row["pageWidth"] > row["width"] or row["broken"] or row["outside"]
           or row["emptyArtwork"] or row["clippedCells"] or row["duplicateIds"] or row["visibleCopyCoverage"]["missing"] or row["overlaps"] or row["occluded"] or row["clippedCards"] or row["errors"] or row["resourceErrors"] for row in records):
        raise ValueError("browser layout admission failed; inspect browser_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--languages", nargs="+", choices=("ja",), default=["ja"])
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(validate(args.base_url, args.languages, args.evidence_dir.resolve()))
