from datetime import datetime, timedelta
from dateutil.parser import parse, ParserError
import requests
from bs4 import BeautifulSoup

def parse_event_date(raw_text):
    try:
        if "Tomorrow" in raw_text:
            time_part = raw_text.split()[-1]
            return parse(str(datetime.today().date() + timedelta(days=1)) + ' ' + time_part)
        elif "Today" in raw_text:
            time_part = raw_text.split()[-1]
            return parse(str(datetime.today().date()) + ' ' + time_part)
        else:
            return parse(raw_text)
    except ParserError:
        return "N/A"

def scrape_eventbrite_toronto(search_term="music"):
    url = f"https://www.eventbrite.ca/d/canada--toronto/{search_term}/"
    print(f"🔍 Fetching: {url}")
    response = requests.get(url, timeout=30)
    
    print("\n🖨️ Page HTML:\n")
    print(response.text)

    soup = BeautifulSoup(response.content, "html.parser")
    events = soup.find_all("div", class_="search-event-card-wrapper")

    results = []
    for e in events:
        try:
            title = e.find("div", class_="eds-is-hidden-accessible").get_text(strip=True)
            date_raw = e.select_one(".eds-event-card-content__sub-title")
            date = parse_event_date(date_raw.get_text(strip=True)) if date_raw else "N/A"
            location = e.find("div", attrs={"data-subcontent-key": "location"}).get_text(strip=True).split("•")[-1]
            link = e.find("a", class_="eds-event-card-content__action-link")["href"]

            results.append({
                "title": title,
                "date": date,
                "location": location,
                "url": link
            })
        except Exception as ex:
            print("⚠️ Skipping event due to parsing error:", ex)

    return results

def save_as_html(events, filename="eventbrite_simple_test.html"):
    html = "<h2>Toronto Eventbrite Events</h2><ul>"
    for e in events:
        html += f"<li><a href='{e['url']}'>{e['title']}</a> – {e['date']} – {e['location']}</li>"
    html += "</ul>"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ File saved: {filename}")

if __name__ == "__main__":
    events = scrape_eventbrite_toronto()
    if events:
        save_as_html(events)
    else:
        print("😕 No events found.")

