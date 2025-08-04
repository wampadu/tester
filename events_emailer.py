import os
import random
import tempfile
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import html
import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# === Calculate Upcoming Friday–Sunday Dates ===
def get_upcoming_weekend_dates():
    today = datetime.today()
    days_until_friday = (4 - today.weekday()) % 7
    friday = today + timedelta(days=days_until_friday)
    return [friday, friday + timedelta(days=1), friday + timedelta(days=2)]

# === HTML Output ===
def generate_html(events):
    dates = get_upcoming_weekend_dates()
    title = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}"
    html_output = f"<html><head><title>{title}</title></head><body><h1>{title}</h1><ul>"
    for e in events:
        html_output += f"<li><a href='{html.escape(e['url'])}'>{html.escape(e['title'])}</a> – {html.escape(e['date'])} – {html.escape(e['price'])}</li>"
    html_output += "</ul></body></html>"
    return html_output

# === Scraper ===
async def scrape_eventbrite(page):
    print("🔍 Scraping Eventbrite...")
    await stealth_async(page)
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_str}&end_date={end_str}"
    await page.goto(url)

    retries = 0
    prev_height = 0
    while retries < 5:
        await page.mouse.wheel(0, random.randint(3000, 6000))
        await page.wait_for_timeout(random.randint(1000, 2000))
        curr_height = await page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            retries += 1
        else:
            retries = 0
            prev_height = curr_height

    cards = await page.query_selector_all("li [data-testid='search-event']")
    print(f"🧾 Found {len(cards)} event cards on this page.")

    for card in cards:
        try:
            title_el = await card.query_selector("h3")
            title = await title_el.inner_text() if title_el else "N/A"

            date_el = await card.query_selector("p:nth-of-type(1)")
            date_text = await date_el.inner_text() if date_el else "N/A"

            img_el = await card.query_selector("img.event-card-image")
            img_url = await img_el.get_attribute("src") if img_el else ""

            link_el = await card.query_selector("a.event-card-link")
            link = await link_el.get_attribute("href") if link_el else ""

            price_el = await card.query_selector("div[class*='priceWrapper'] p")
            price = await price_el.inner_text() if price_el else "Free"

            events.append({
                "title": title.strip(),
                "date": date_text.strip(),
                "description": "",
                "image": img_url,
                "url": link,
                "price": price.strip(),
                "source": "Eventbrite"
            })
        except Exception as e:
            print("⚠️ Error extracting event:", e)

    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

# === Email ===
def send_email_with_attachment(to_email, subject, html_path):
    from_email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASS")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText("Open your 'Toronto Weekend Events' HTML file and book an event 2 weeks from now.", 'plain'))

    with open(html_path, "rb") as file:
        part = MIMEApplication(file.read(), Name="weekend_events_toronto.html")
        part['Content-Disposition'] = 'attachment; filename="weekend_events_toronto.html"'
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, app_password)
        server.send_message(msg)
    print("📧 Email sent!")

# === Main Runner ===
async def main():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")
    all_events = []

    user_data_dir = tempfile.mkdtemp()

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-extensions",
                "--disable-infobars",
                "--lang=en-US,en",
                "--window-size=1920,1080",
                "--start-maximized",
                "--font-render-hinting=none",
                "--disable-gpu",
                "--hide-scrollbars",
                "--mute-audio",
                "--disable-features=IsolateOrigins,site-per-process"
            ],
            locale="en-US",
            timezone_id="America/Toronto",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await browser.new_page()

        await page.route("**/*", lambda route, request: (
            asyncio.create_task(route.abort()) if any(x in request.url for x in ["captcha", "botd", "challenge"]) else asyncio.create_task(route.continue_())
        ))

        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await page.wait_for_timeout(random.randint(300, 700))
        await page.keyboard.type("Hello Eventbrite")
        await page.wait_for_timeout(random.randint(500, 900))

        all_events += await scrape_eventbrite(page)
        await browser.close()

    seen_titles = set()
    deduped_events = []
    for event in all_events:
        title_key = event['title'].strip().lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped_events.append(event)
    all_events = deduped_events

    html_output = generate_html(all_events)
    with open("weekend_events_toronto.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("✅ File saved: weekend_events_toronto.html")

    send_email_with_attachment(
        to_email=os.getenv("EMAIL_TO"),
        subject=f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}",
        html_path="weekend_events_toronto.html"
    )

if __name__ == "__main__":
    asyncio.run(main())


