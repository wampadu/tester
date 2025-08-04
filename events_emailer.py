import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import html
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

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

# === Scrape Eventbrite via ScraperAPI ===
def scrape_eventbrite():
    api_key = "46f16739ebbc381529ebfd21f01061dd"
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")

    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_str}&end_date={end_str}"
    payload = {'api_key': api_key, 'url': url}
    response = requests.get("http://api.scraperapi.com", params=payload)

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("li[data-testid='search-event']")
    for card in cards:
        try:
            title_el = card.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else "N/A"

            date_el = card.select_one("p")
            date_text = date_el.get_text(strip=True) if date_el else "N/A"

            img_el = card.select_one("img.event-card-image")
            img_url = img_el['src'] if img_el else ""

            link_el = card.select_one("a.event-card-link")
            link = link_el['href'] if link_el else ""

            price_el = card.select_one("div[class*='priceWrapper'] p")
            price = price_el.get_text(strip=True) if price_el else "Free"

            events.append({
                "title": title,
                "date": date_text,
                "description": "",
                "image": img_url,
                "url": link,
                "price": price,
                "source": "Eventbrite"
            })
        except Exception as e:
            print("⚠️ Error parsing event:", e)
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

# === Main ===
def main():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")
    all_events = scrape_eventbrite()

    seen_titles = set()
    deduped_events = []
    for event in all_events:
        title_key = event['title'].strip().lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped_events.append(event)
    all_events = deduped_events

    html_output = generate_html(all_events)
    output_path = "weekend_events_toronto.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print("✅ File saved:", output_path)

    send_email_with_attachment(
        to_email=os.getenv("EMAIL_TO"),
        subject=f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}",
        html_path=output_path
    )

if __name__ == "__main__":
    main()
