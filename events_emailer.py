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

    seen_titles = set()
    while True:
        print("🔄 Scrolling to load events on current page...")
        retries = 0
        prev_height = 0
        while retries < 5:
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(1200)
            curr_height = page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                retries += 1
            else:
                prev_height = curr_height
                retries = 0

        cards = page.query_selector_all("li [data-testid='search-event']")
        print(f"🧾 Found {len(cards)} event cards on this page.")

        for card in cards:
            try:
                title_el = card.query_selector("h3")
                title = title_el.inner_text().strip() if title_el else "N/A"
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                date_el = card.query_selector("p:nth-of-type(1)")
                date = date_el.inner_text().strip() if date_el else "N/A"
                link_el = card.query_selector("a.event-card-link")
                link = link_el.get_attribute("href") if link_el else ""
                price_el = card.query_selector("div[class*='priceWrapper'] p")
                price = price_el.inner_text().strip() if price_el else "Free"

                events.append({
                    "title": title,
                    "date": date,
                    "price": price,
                    "url": link,
                    "source": "Eventbrite"
                })
            except Exception as e:
                print("⚠️ Error extracting event:", e)

        # Try to find and click the "Next" button
        next_btn = page.query_selector('[data-testid="page-next"]:not([aria-disabled="true"])')
        if next_btn:
            print("➡️ Going to next page...")
            next_btn.click()
            page.wait_for_timeout(2000)
        else:
            print("🛑 No more pages.")
            break

    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page)
        events = scrape_eventbrite(page)
        html_data = generate_html(events)

        with open("eventbrite_stealth_events.html", "w", encoding="utf-8") as f:
            f.write(html_data)
        print("✅ Saved to eventbrite_stealth_events.html")
        
        with open("eventbrite_stealth_events.html", "r", encoding="utf-8") as f:
            content = f.read()
            max_chars = 5000  # ⛔ Set your desired limit here
            print("\n🔍 Preview (capped):\n")
            print(content[:max_chars])
        browser.close()

if __name__ == "__main__":
    main()


