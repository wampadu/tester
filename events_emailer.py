from fake_browser_profile.fake_profile import FakeProfile
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import time

# Generate a realistic fake profile
profile = FakeProfile(locale='en-US', browser='chrome', os='windows')
user_agent = profile.user_agent

options = uc.ChromeOptions()
options.add_argument(f'user-agent={user_agent}')
options.add_argument('--no-sandbox')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--headless=new')  # Remove if you want visual debugging

driver = uc.Chrome(options=options)
url = "https://www.eventbrite.ca/d/canada--toronto/events/"
driver.get(url)

# Log the page title and source for debugging
print("Page Title:", driver.title)
with open("eventbrite_fakeprofile.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

# Extract some events for testing
time.sleep(5)
soup = BeautifulSoup(driver.page_source, "lxml")
events = soup.select("li[data-testid='event-card']")
print(f"Found {len(events)} event cards.")

for e in events[:5]:  # Print first 5 for brevity
    title = e.select_one("h3")
    print("Title:", title.text.strip() if title else "N/A")

driver.quit()
