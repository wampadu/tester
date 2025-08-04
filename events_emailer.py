import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse
import os

def get_upcoming_weekend_dates():
    today = datetime.today()
    friday = today + timedelta((4 - today.weekday()) % 7 + 7)
    saturday = friday + timedelta(days=1)
    sunday = friday + timedelta(days=2)
    return friday, saturday, sunday

def get_event_pages(search_url):
    response = requests.get(search_url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    soup = BeautifulSoup(response.content, "html.parser")
    pagination = soup.select("ul.pagination__list li")
    if pagination:
        pages = [li.get_text(strip=True) for li in pagination if li.get_text(strip=True).isdigit()]
        return int(pages[-1]) if pages else 1
    return 1

def parse_event_card(card):
    try:
        title = card.select_one("div.eds-event-card__formatted-name--is-clamped").text.strip()
        url = card.find("a", class_="eds-event-card-content__action-link")["href"]
        date = card.select_one("div.eds-event-card-content__sub-title").text.strip()
        location_el = card.select_one("div.card-text--truncated__one")
        location = location_el.text.strip() if location_el else "Toronto"
        return {"title": title, "url": url, "date": date, "location": location}
    except Exception as e:
        print(f"⚠️ Skipping malformed event: {e}")
        return None

def scrape_eventbrite_toronto():
    friday, sunday = get_upcoming_weekend_dates()
    start_date = friday.strftime("%Y-%m-%d")
    end_date = sunday.strftime("%Y-%m-%d")

    base_url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_date}&end_date={end_date}"
    max_pages = get_event_pages(base_url)
    print(f"🔢 Found {max_pages} pages of events.")

    all_events = []

    for page in range(1, max_pages + 1):
        page_url = f"{base_url}&page={page}"
        print(f"📄 Scraping page {page}...")
        response = requests.get(page_url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        soup = BeautifulSoup(response.content, "html.parser")
        cards = soup.select("div.search-event-card-wrapper")

        for card in cards:
            event = parse_event_card(card)
            if event:
                all_events.append(event)

    print(f"✅ Total events scraped: {len(all_events)}")
    return all_events

def generate_html(events):
    friday, sunday = get_upcoming_weekend_dates()
    html = f"<h2>Toronto Weekend Events – {friday.strftime('%b %d')} to {sunday.strftime('%b %d')}</h2><ul>"
    for e in events:
        html += f"<li><a href='{e['url']}'>{e['title']}</a> – {e['date']} – {e['location']}</li>"
    html += "</ul>"
    return html

def save_html_file(html, filename="eventbrite_hybrid_events.html"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ File saved: {filename}")

if __name__ == "__main__":
    events = scrape_eventbrite_toronto()
    html = generate_html(events)
    save_html_file(html)
