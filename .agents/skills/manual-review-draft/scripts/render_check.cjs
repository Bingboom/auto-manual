// Render the JP review draft in Chromium and check it, then screenshot sections.
//
//   NODE_PATH=$(npm root -g) node render_check.cjs <draft.html> <out_dir> [section ids a,b,c or ""] [widths, default 1280,390]
//
// Prints per width: image count / broken images, page-level horizontal overflow,
// the colour of the first H1 bar and the distinct computed colours of green new
// translation (.en-new), Chinese glosses, placeholders and purple spec/R&D values —
// expected rgb(4,120,87), rgb(22,87,187), rgb(194,24,91) and rgb(126,34,206). Lazy images are forced to eager first (otherwise screenshots
// show empty icon cells). Uses /opt/pw-browsers/chromium when present.
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const [, , file, out, ids = '', widths = '1280,390'] = process.argv;
  const exe = fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined;
  const browser = await chromium.launch({ executablePath: exe });
  let failed = false;
  for (const width of widths.split(',').map(Number)) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto('file://' + require('path').resolve(file));
    await page.evaluate(() => document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; }));
    await page.waitForTimeout(1500);
    const info = await page.evaluate(() => {
      const colours = sel => [...new Set([...document.querySelectorAll(sel)].map(e => getComputedStyle(e).color))];
      const h1 = document.querySelector('#furo-main-content h1');
      return {
        images: document.images.length,
        broken: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src')),
        pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        h1: h1 ? [getComputedStyle(h1).backgroundColor, getComputedStyle(h1).color] : null,
        greenEnglish: colours('#furo-main-content .en-new'),
        chinese: colours('#furo-main-content p > .zh-translation'),
        placeholders: colours('#furo-main-content .jp-parameter'),
        specValues: colours('#furo-main-content :is(.jp-spec-updated, .jp-spec-filled)'),
      };
    });
    console.log(width, JSON.stringify(info));
    if (info.broken.length || info.pageOverflow) failed = true;
    await page.addStyleTag({ content: 'header.preview-toolbar{position:static!important}' });
    for (const id of ids.split(',').filter(Boolean)) {
      const el = await page.$('#' + id);
      if (!el) { console.log('missing section', id); continue; }
      await el.screenshot({ path: `${out}/${id}-${width}.png` });
    }
    await page.close();
  }
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
