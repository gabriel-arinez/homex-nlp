// Optional browser regression over a separately generated one-case synthetic workspace.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function main() {
  const [htmlPath, exportPath, playwrightPath] = process.argv.slice(2);
  if (!htmlPath || !exportPath || !playwrightPath) {
    console.error('Usage: node commercial_review_browser_probe.cjs <synthetic-review.html> <synthetic-export.json> <playwright-module-path>');
    process.exitCode = 2;
    return;
  }
  const review = JSON.parse(fs.readFileSync(path.join(path.dirname(htmlPath), 'review.json'), 'utf8'));
  const original = JSON.parse(fs.readFileSync(exportPath, 'utf8'));
  assert.equal(review.cases.length, 1, 'Never run this synthetic decision probe on the 120-case workspace');
  assert.equal(original.decisions.length, 1);
  assert.match(original.decisions[0].reviewer, /synthetic/i);
  assert.equal(original.decisions[0].listening_attested, true);
  const decision = original.decisions[0];
  const reordered = Object.fromEntries(Object.keys(decision).reverse().map(key => [key, decision[key]]));
  const { chromium } = require(path.resolve(playwrightPath));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const network = [];
    page.on('request', request => { if (/^https?:/.test(request.url())) network.push(request.url()); });
    await page.goto(pathToFileURL(path.resolve(htmlPath)).href);
    async function importPayload(payload) {
      // Clear only the previous display message, never application history.
      await page.locator('#message').evaluate(element => { element.textContent = ''; });
      await page.locator('#import').setInputFiles({ name: 'synthetic.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(payload)) });
      await page.waitForFunction(() => document.querySelector('#message').textContent.includes('importad') || document.querySelector('#message').textContent.includes('rechazada'));
      return page.locator('#message').innerText();
    }
    for (const item of [decision, reordered]) {
      assert.match(await importPayload({ ...original, decisions: [item] }), /Historial importado/);
    }
    const changed = { ...decision, value: 999 };
    assert.match(await importPayload({ ...original, decisions: [changed] }), /Importación rechazada/);
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#export').click();
    const download = await downloadPromise;
    const exported = JSON.parse(fs.readFileSync(await download.path(), 'utf8'));
    assert.equal(exported.decisions.length, 1);
    assert.equal(exported.decisions[0].value, decision.value);
    assert.equal(exported.decisions[0].listening_attested, true);
    assert.equal(network.length, 0);
    console.log('PASS reordered JSON identities deduplicate; changed identities reject; one unchanged synthetic decision retained; no network');
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
