from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from datetime import datetime, timedelta
import html

def get_upcoming_weekend_dates():
    today = datetime.today()
    days_until_friday = (4 - today.weekday()) % 7
    friday = today + timedelta(days=days_until_friday + 7)
    return [friday, friday + timedelta(days=1), friday + timedelta(days=2)]

def generate_html(events):
    dates = get_upcoming_weekend_dates()
    title = f"Toronto Weekend Events – {dates[0].strftime('%B %d')} to {dates[-1].strftime('%d, %Y')}"
    html_output = f"<html><head><title>{title}</title></head><body><h1>{title}</h1><ul>"
    for e in events:
        html_output += f"<li><a href='{html.escape(e['url'])}'>{html.escape(e['title'])}</a> – {html.escape(e['date'])} – {html.escape(e['price'])}</li>"
    html_output += "</ul></body></html>"
    return html_output

def scrape_eventbrite(page):
    print("🔍 Scraping Eventbrite...")
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_str}&end_date={end_str}"
    page.goto(url, timeout=60000)
    page.mouse.move(100, 100)
    page.wait_for_timeout(2000)
    print("🔎 Page preview:\n", page.content()[:1000])

    while True:
        # Scroll to load more events on the current page
        print("🔄 Scrolling...")
        retries, prev_height = 0, 0
        while retries < 3:
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1500)
            curr_height = page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                retries += 1
            else:
                retries = 0
                prev_height = curr_height

        # Extract events
        cards = page.query_selector_all("li [data-testid='search-event']")
        print(f"🧾 Found {len(cards)} event cards on this page.")

        for card in cards:
            try:
                title_el = card.query_selector("h3")
                title = title_el.inner_text().strip() if title_el else "N/A"
                date_el = card.query_selector("p:nth-of-type(1)")
                date = date_el.inner_text().strip() if date_el else "N/A"
                link_el = card.query_selector("a.event-card-link")
                link = link_el.get_attribute("href") if link_el else ""
                price_el = card.query_selector("div[class*='priceWrapper'] p")
                price = price_el.inner_text().strip() if price_el else "Free"

                event = {
                    "title": title,
                    "date": date,
                    "price": price,
                    "url": link,
                    "source": "Eventbrite"
                }
                if event not in events:
                    events.append(event)
            except Exception as e:
                print("⚠️ Error extracting event:", e)

        # Check for next page
        next_btn = page.query_selector('[aria-label="Next page"]:not([disabled])')
        if next_btn:
            print("➡️ Moving to next page...")
            next_btn.click()
            page.wait_for_timeout(3000)
        else:
            print("🛑 No more pages.")
            break

    return events

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        stealth_sync(page)
        events = scrape_eventbrite(page)
        html_data = generate_html(events)

        with open("eventbrite_stealth_events.html", "w", encoding="utf-8") as f:
            f.write(html_data)
        print("✅ Saved to eventbrite_stealth_events.html")
        browser.close()

if __name__ == "__main__":
    main()

