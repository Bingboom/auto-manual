"""Check final browser ink, loaded images and source figure layout at three widths.

Requires Playwright Chromium. Serve strict Sphinx outputs under /en, /fr, /es.
Evidence is written outside the frozen source package, never into its inventory.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

PACKAGE = Path(__file__).resolve().parent
CHAPTERS = tuple(c["id"] for c in json.loads((PACKAGE/"source/en/content.json").read_text())["chapters"])
FIGURES = tuple(g["id"] for g in json.loads((PACKAGE/"source/figures.json").read_text()) if not g["id"].startswith("inbox"))
CHECK = r"""() => {
 const root=document.querySelector('[role=main]');
 const labels=[...root.querySelectorAll('.hb-reference-live-label')];
 const outside=[],overlaps=[],clippedCards=[],occluded=[];
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
 return {
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
                    f"{base_url.rstrip('/')}/{language}/manual_jhp5000c_us_{language}.html",
                    wait_until="domcontentloaded",
                )
                await page.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
                await page.evaluate("document.fonts.ready")
                await page.wait_for_function("[...document.images].every(i=>i.complete&&i.naturalWidth>0)")
                info = await page.evaluate(CHECK)
                info.update(language=language, width=width, height=height, errors=errors, resourceErrors=resource_errors)
                records.append(info)
                if width in [1280, 390]:
                    for anchor in CHAPTERS:
                        await page.evaluate("""id=>{
                          document.documentElement.style.scrollBehavior='auto';
                          window.scrollTo({top:Math.max(0,document.getElementById('native-'+id).getBoundingClientRect().top+window.scrollY-80),behavior:'instant'});
                        }""", anchor)
                        await page.screenshot(path=str(evidence_dir / f"{language}-{width}-{anchor}.png"))
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
            "outside", "overlaps", "occluded", "clippedCards", "errors", "resourceErrors",
        )}, ensure_ascii=False))
    if any(row["pageWidth"] > row["width"] or row["broken"] or row["outside"]
           or row["overlaps"] or row["occluded"] or row["clippedCards"] or row["errors"] or row["resourceErrors"] for row in records):
        raise ValueError("browser layout admission failed; inspect browser_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--languages", nargs="+", choices=("en", "fr", "es"), default=["en", "fr", "es"])
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(validate(args.base_url, args.languages, args.evidence_dir.resolve()))
