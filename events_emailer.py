import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

def get_upcoming_weekend_dates():
    today = datetime.today()
    friday = today + timedelta((4 - today.weekday()) % 7 + 7)
    saturday = friday + timedelta(days=1)
    sunday = friday + timedelta(days=2)
    return [friday, saturday, sunday]

def get_weekend_range():
    dates = get_upcoming_weekend_dates()
    return dates[0].strftime("%Y-%m-%d"), dates[-1].strftime("%Y-%m-%d")

def scrape_eventbrite():
    print("🔍 Scraping Eventbrite...")
    start_date, end_date = get_weekend_range()
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_date}&end_date={end_date}"
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(3)

    events = []
    retries = 0
    prev_height = 0

    print(driver.page_source[:6000])  

    while retries < 5:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(1.2)
        curr_height = driver.execute_script("return document.body.scrollHeight")
        if curr_height == prev_height:
            retries += 1
        else:
            retries = 0
            prev_height = curr_height

    soup = BeautifulSoup(driver.page_source, 'lxml')
    cards = soup.select("li[data-testid='event-card']")
    print(f"🧾 Found {len(cards)} event cards.")

    for card in cards:
        try:
            title_el = card.select_one("h3")
            date_el = card.select_one("p")
            img_el = card.select_one("img.event-card-image")
            link_el = card.select_one("a.event-card-link")
            price_el = card.select_one("div[class*='priceWrapper'] p")

            title = title_el.text.strip() if title_el else "N/A"
            date = date_el.text.strip() if date_el else "N/A"
            img_url = img_el['src'] if img_el else ""
            link = link_el['href'] if link_el else ""
            price = price_el.text.strip() if price_el else "Free"

            events.append({
                "title": title,
                "date": date,
                "image": img_url,
                "url": link,
                "price": price,
                "source": "Eventbrite"
            })
        except Exception as e:
            print("⚠️ Error extracting event:", e)

    driver.quit()
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

def generate_html(events):
    friday, sunday = get_upcoming_weekend_dates()[0], get_upcoming_weekend_dates()[-1]
    html_content = f"<h2>Toronto Events – {friday.strftime('%B %d')} to {sunday.strftime('%d, %Y')}</h2><ul>"
    for e in events:
        html_content += f"<li><a href='{e['url']}'>{e['title']}</a> – {e['date']} – {e['price']}</li>"
    html_content += "</ul>"
    return html_content

def send_email(html_content):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Toronto Weekend Events"
    msg["From"] = os.environ["GMAIL_USER"]
    msg["To"] = os.environ["EMAIL_TO"]
    msg.attach(MIMEText(html_content, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["GMAIL_USER"], os.environ["GMAIL_PASS"])
        server.sendmail(msg["From"], msg["To"], msg.as_string())

if __name__ == "__main__":
    events = scrape_eventbrite()
    html_output = generate_html(events)
    with open("eventbrite_stealth_events.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("✅ File saved: eventbrite_stealth_events.html")
    if os.getenv("EMAIL_TO"):
        send_email(html_output)
        print("📧 Email sent!")

