// Usage: PLAYWRIGHT_MODULE=... node rasterize.cjs <scratch> <output> [qa-directory]
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
(async () => {
  const [scratch, output, qa] = process.argv.slice(2);
  const receipt = JSON.parse(fs.readFileSync(path.join(scratch, 'export_receipt.json')));
  const browser = await chromium.launch({headless: true});
  for (const scale of (qa ? [4, 12] : [4])) {
    const page = await browser.newPage({deviceScaleFactor: scale});
    for (const entry of receipt.filter(e => e.svg_sha256)) {
      const svg = fs.readFileSync(path.join(scratch, entry.name + '.svg'), 'utf8');
      const width = entry.bbox_pt[2] - entry.bbox_pt[0];
      const height = entry.bbox_pt[3] - entry.bbox_pt[1];
      await page.setViewportSize({width: Math.ceil(width), height: Math.ceil(height)});
      await page.setContent('<style>html,body{margin:0;padding:0;background:transparent}svg{display:block}</style>' + svg);
      if (scale === 4) {
        const file = path.join(output, entry.path);
        await page.screenshot({path: file, omitBackground: true, clip: {x:0,y:0,width,height}});
        entry.png_sha256 = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
        entry.browser_version = browser.version();
      } else {
        fs.mkdirSync(qa, {recursive: true});
        for (const [label, color] of [['white', '#fff'], ['gray', '#999']]) {
          await page.evaluate(c => document.body.style.background = c, color);
          await page.screenshot({path:path.join(qa, entry.name + '-12x-' + label + '.png'), clip:{x:0,y:0,width,height}});
        }
      }
    }
    await page.close();
  }
  fs.writeFileSync(path.join(scratch, 'export_receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
  await browser.close();
})().catch(error => {console.error(error); process.exit(1);});
