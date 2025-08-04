const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs-extra');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();

  // Set viewport and user agent to reduce detection
  await page.setViewport({ width: 1280, height: 800 });
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36');

  const today = new Date();
  const daysUntilFriday = (5 - today.getDay() + 7) % 7;
  const friday = new Date(today.getFullYear(), today.getMonth(), today.getDate() + daysUntilFriday + 7);
  const sunday = new Date(friday.getTime() + 2 * 86400000);

  const start_date = friday.toISOString().split('T')[0];
  const end_date = sunday.toISOString().split('T')[0];

  const url = `https://www.eventbrite.ca/d/canada--toronto/events/?start_date=${start_date}&end_date=${end_date}`;
  console.log("🔍 Navigating to:", url);
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });

  console.log("🔄 Scrolling...");
  let previousHeight;
  for (let i = 0; i < 10; i++) {
    previousHeight = await page.evaluate('document.body.scrollHeight');
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
    await page.waitForTimeout(2000);
    const newHeight = await page.evaluate('document.body.scrollHeight');
    if (newHeight === previousHeight) break;
  }

  console.log("🧾 Extracting event cards...");
  const events = await page.evaluate(() => {
    const items = [];
    const cards = document.querySelectorAll("li [data-testid='search-event']");
    cards.forEach(card => {
      const title = card.querySelector("h3")?.innerText?.trim() || "N/A";
      const date = card.querySelector("p:nth-of-type(1)")?.innerText?.trim() || "N/A";
      const price = card.querySelector("div[class*='priceWrapper'] p")?.innerText?.trim() || "Free";
      const url = card.querySelector("a.event-card-link")?.href || "";
      items.push({ title, date, price, url });
    });
    return items;
  });

  console.log(`✅ Found ${events.length} events.`);

  // Save to HTML
  const html = `
  <html><head><title>Toronto Events</title></head><body>
  <h1>Toronto Events from ${start_date} to ${end_date}</h1>
  <ul>
    ${events.map(e => `<li><a href="${e.url}">${e.title}</a> – ${e.date} – ${e.price}</li>`).join('\n')}
  </ul>
  </body></html>`;

  await fs.writeFile('eventbrite_stealth_events.html', html, 'utf-8');
  console.log("📄 Saved to eventbrite_stealth_events.html");

  await browser.close();
})();
