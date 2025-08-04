import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

def get_weekend_range():
    today = datetime.today()
    friday = today + timedelta((4 - today.weekday()) % 7 + 7)
    return friday.strftime("%Y-%m-%d"), (friday + timedelta(days=2)).strftime("%Y-%m-%d")

def scrape_eventbrite():
    start_date, end_date = get_weekend_range()
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_date}&end_date={end_date}"
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    # Scroll to load more
    for _ in range(5):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(2)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    events = soup.select("li[data-testid='event-card']")

    items = []
    for e in events:
        title = e.select_one("h3")
        link = e.find("a", class_="event-card-link")
        date = e.select_one("p")
        price = e.select_one("div[class*='priceWrapper'] p")
        items.append({
            "title": title.text.strip() if title else "N/A",
            "url": link['href'] if link else "",
            "date": date.text.strip() if date else "N/A",
            "price": price.text.strip() if price else "Free"
        })

    driver.quit()
    return items

def generate_html(events):
    friday, sunday = get_weekend_range()
    html_content = f"<h2>Toronto Events – {friday} to {sunday}</h2><ul>"
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
    html = generate_html(events)
    with open("selenium_eventbrite_events.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Saved to selenium_eventbrite_events.html")
    if os.getenv("EMAIL_TO"):
        send_email(html)
        print("📧 Email sent!")
