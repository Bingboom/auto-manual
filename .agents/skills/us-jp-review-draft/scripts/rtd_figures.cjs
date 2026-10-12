// Screenshot US reference figures (base art + live labels) from the published RTD page.
//
//   NODE_PATH=$(npm root -g) node rtd_figures.cjs <rtd_url> <out_dir> <reference-id,...>
//
// Each figure[data-reference-id=<id>] is saved as <out_dir>/<id>.png at 2x. These
// are US originals for review only: put them in a .us-review-figure with an orange
// "美规原图 … 需按日规重绘" caption. Honours HTTPS_PROXY.
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const [, , url, out, ids] = process.argv;
  const exe = fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined;
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  const browser = await chromium.launch({ executablePath: exe, proxy });
  const ctx = await browser.newContext({ viewport: { width: 1100, height: 1000 }, deviceScaleFactor: 2, ignoreHTTPSErrors: true });
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.evaluate(() => document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; }));
  await page.waitForTimeout(3000);
  for (const id of ids.split(',')) {
    const el = await page.$(`figure[data-reference-id="${id}"]`);
    if (!el) { console.log('missing', id); continue; }
    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    const ok = await el.evaluate(f => [...f.querySelectorAll('img')].every(i => i.complete && i.naturalWidth > 0));
    await el.screenshot({ path: `${out}/${id}.png` });
    console.log(id, 'images loaded:', ok);
  }
  await browser.close();
})();
