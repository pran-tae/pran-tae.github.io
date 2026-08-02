// Letterboxd's sort pages 403 plain HTTP clients but admit real browsers.
// This helper fetches the rated-date order and prints JSON for the Python script.
import { chromium } from 'playwright';

const USER = 'term_2222';
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
  });
  await page.goto(`https://letterboxd.com/${USER}/films/by/rated-date/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForSelector('.griditem [data-item-slug]', { timeout: 25000 });
  const items = await page.evaluate(() =>
    [...document.querySelectorAll('.griditem')].slice(0, 8).map((li) => {
      const el = li.querySelector('[data-item-slug]');
      if (!el) return null;
      let rating = null;
      const rated = li.innerHTML.match(/rated-(\d+)/);
      if (rated) rating = Number(rated[1]);
      return { slug: el.dataset.itemSlug, name: el.dataset.itemName, rating };
    }).filter(Boolean)
  );
  console.log(JSON.stringify(items));
} finally {
  await browser.close();
}
