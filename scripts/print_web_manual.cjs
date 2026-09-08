/* Print the delivered page itself; Playwright is an external build prerequisite. */
const { chromium } = require('playwright');
const { pathToFileURL } = require('node:url');
const [html, pdf, executablePath] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch({headless: true, ...(executablePath ? {executablePath} : {})});
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(html).href, {waitUntil: 'networkidle'});
    await page.emulateMedia({media: 'print', colorScheme: 'light'});
    const failures = await page.evaluate(async () => {
      const images = [...document.images];
      images.forEach(image => image.loading = 'eager');
      await Promise.all(images.map(image => image.decode().catch(() => {})));
      await document.fonts.ready;
      return images.filter(image => !image.complete || !image.naturalWidth).map(image => image.getAttribute('src'));
    });
    if (failures.length) throw new Error(`Unloaded print images: ${failures.join(', ')}`);
    await page.pdf({path: pdf, printBackground: true, preferCSSPageSize: true, displayHeaderFooter: false});
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
