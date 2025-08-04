import os
import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import calendar
import html
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from playwright.sync_api import sync_playwright
import random


# === Calculate Upcoming Friday–Sunday Dates ===
def get_upcoming_weekend_dates():
    today = datetime.today()
    days_until_friday = (4 - today.weekday()) % 7
    friday = today + timedelta(days=days_until_friday + 7)
    return [friday, friday + timedelta(days=1), friday + timedelta(days=2)]

# === HTML Output ===
def generate_html(events):
    dates = get_upcoming_weekend_dates()
    title = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}"
    
    html_output = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>{title}</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.4.1/css/buttons.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/responsive/2.5.0/css/responsive.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/searchbuilder/1.5.0/css/searchBuilder.dataTables.min.css">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border: 1px solid #ccc; vertical-align: top; }}
            img {{ max-width: 150px; height: auto; border-radius: 10px; }}
            .dtsb-title {{ display: none; }}
            button {{ background-color: black !important; color: white !important; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <table id="events">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Date</th>
                    <th>Price</th>
                    <th>Description</th>
                    <th>Source</th>
                    <th>Image</th>
                </tr>
            </thead>
            <tbody>
    """

    for e in events:
        if not e.get('title') or not e.get('url'):
            continue
        html_output += f"""
            <tr>
                <td><a href="{html.escape(e['url'])}" target="_blank">{html.escape(e['title'])}</a></td>
                <td>{html.escape(e.get('date', ''))}</td>
                <td>{html.escape(e.get('price', ''))}</td>
                <td>{html.escape(e.get('description', ''))}</td>
                <td>{html.escape(e.get('source', ''))}</td>
                <td>{f'<img src="{html.escape(e["image"])}">' if e.get('image', '').startswith('http') else ''}</td>
            </tr>
        """

    html_output += """
            </tbody>
        </table>

        <!-- jQuery + DataTables JS -->
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.html5.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.print.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.colVis.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.68/pdfmake.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.68/vfs_fonts.js"></script>
        <script src="https://cdn.datatables.net/responsive/2.5.0/js/dataTables.responsive.min.js"></script>
        <script src="https://cdn.datatables.net/searchbuilder/1.5.0/js/dataTables.searchBuilder.min.js"></script>

        <script>
        function addFancyRandomEventButtonBelowH1() {
          const dt = $('#events').DataTable();
          if (!dt) return console.warn("⚠️ DataTable not ready.");

          dt.buttons('.random-event').remove();

          dt.button().add(null, {
            text: '🎲 Random Event Picker',
            className: 'random-event btn btn-outline-primary',
            action: function () {
              const rows = dt.rows({ search: 'applied' }).nodes();
              if (!rows.length) return alert("No visible events to pick from.");
              const randIndex = Math.floor(Math.random() * rows.length);
              const row = rows[randIndex];
              const linkEl = row.querySelector("td:first-child a");
              const imgEl = row.querySelector("td:last-child img");
              const title = linkEl?.textContent.trim() || "No title";
              const href = linkEl?.href || "#";
              const image = imgEl?.src || "";

              document.getElementById('random-event-card')?.remove();

              const card = document.createElement("div");
              card.id = "random-event-card";
              card.style = `
                border: 1px solid #ccc;
                border-left: 5px solid #007acc;
                padding: 16px;
                margin-top: 20px;
                max-width: 600px;
                border-radius: 8px;
                position: relative;
                background: #f9f9f9;
                font-family: sans-serif;
              `;
              card.innerHTML = `
                <button style="
                  position: absolute;
                  top: 8px;
                  right: 10px;
                  background: transparent;
                  border: none;
                  font-size: 20px;
                  cursor: pointer;
                  color: #999;
                " onclick="document.getElementById('random-event-card').remove()">×</button>
                <h3 style="margin: 0 0 10px">🎯 Your Random Pick:</h3>
                <a href="${href}" target="_blank" style="font-size: 16px; font-weight: bold; color: #007acc;">${title}</a>
                ${image ? `<div><img src="${image}" style="margin-top: 10px; max-width: 100%; border-radius: 6px;" /></div>` : ''}
              `;

              const h1 = document.querySelector("h1");
              if (h1) h1.insertAdjacentElement("afterend", card);
            }
          });
        }

        (function waitForTableAndUpgrade(retries = 10) {
          const tableEl = document.querySelector("#events");
          if (!tableEl || !tableEl.querySelector("thead")) {
            if (retries > 0) return setTimeout(() => waitForTableAndUpgrade(retries - 1), 500);
            else return console.warn("❌ Table not found.");
          }

          if ($.fn.DataTable.isDataTable("#events")) $('#events').DataTable().destroy();

          if (!tableEl.querySelector("tfoot")) {
            const tfoot = tableEl.querySelector("thead").cloneNode(true);
            tfoot.querySelectorAll("th").forEach(cell => cell.innerHTML = "");
            tableEl.appendChild(tfoot);
          }

          $('#events').DataTable({
            responsive: true,
            paging: false,
            ordering: true,
            info: false,
            dom: 'QBfrtip',
            buttons: ['csv', 'excel'],
            searchBuilder: { columns: true },
            columnDefs: [{ targets: -1, orderable: false }],
            initComplete: function () {
              this.api().columns().every(function () {
                const input = document.createElement("input");
                input.placeholder = "Filter...";
                input.style.width = "100%";
                $(input).appendTo($(this.footer()).empty())
                  .on("keyup change clear", function () {
                    this.search(this.value).draw();
                  }.bind(this));
              });
              addFancyRandomEventButtonBelowH1();
            }
          });
        })();
        </script>
    </body>
    </html>
    """
    return html_output

# === Scrapers ===
async def scrape_eventbrite(page):
    print("🔍 Scraping Eventbrite...")
    events = []
    target_dates = [(d.strftime('%b %d')) for d in get_upcoming_weekend_dates()]
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_str}&end_date={end_str}"
    await page.goto(url)

    while True:
        print("🔄 Scrolling to load events on current page...")
        prev_height = 0
        retries = 0
        while retries < 5:
            await page.mouse.wheel(0, 5000)
            await asyncio.sleep(1.2)
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
                title = (await title_el.inner_text()).strip() if title_el else "N/A"

                date_el = await card.query_selector("p:nth-of-type(1)")
                date_text = (await date_el.inner_text()).strip() if date_el else "N/A"

                img_el = await card.query_selector("img.event-card-image")
                img_url = await img_el.get_attribute("src") if img_el else ""

                link_el = await card.query_selector("a.event-card-link")
                link = await link_el.get_attribute("href") if link_el else ""

                price_el = await card.query_selector("div[class*='priceWrapper'] p")
                price = (await price_el.inner_text()).strip() if price_el else "Free"

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
                print("⚠️ Error extracting event:", e)

        try:
            next_btn = await page.query_selector('[data-testid="page-next"]:not([aria-disabled="true"])')
            if next_btn:
                print("➡️ Going to next page...")
                await next_btn.click()
                await asyncio.sleep(2)
            else:
                print("🛑 No more pages.")
                break
        except Exception as e:
            print("⚠️ Pagination error:", e)
            break
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

async def scrape_fever(page):
    print("🔍 Scraping Fever...") 
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://feverup.com/en/toronto/things-to-do?date={start_str}until{end_str}"
    await page.goto(url)
    await page.wait_for_selector('li[data-testid="fv-wpf-plan-grid__list-item"]')

    previous_height = 0
    retries = 0
    while retries < 5:
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            retries += 1
            await asyncio.sleep(1)
        else:
            await page.mouse.wheel(0, current_height)
            previous_height = current_height
            retries = 0
            await asyncio.sleep(1.5)

    cards = await page.query_selector_all('li[data-testid="fv-wpf-plan-grid__list-item"]')
    for card in cards:
        try:
            title = await card.eval_on_selector('[data-testid="fv-plan-card-title"]', 'el => el.textContent')
            date = await card.eval_on_selector('[data-testid="fv-plan-card-v2__date-range"]', 'el => el.textContent')
            price = await card.eval_on_selector('[data-testid="fv-plan-card-v2__price"]', 'el => el.textContent')
            link_el = await card.query_selector('a.fv-plan-card-v2')
            url = await link_el.get_attribute('href') if link_el else ''
            img = await card.eval_on_selector("img", "el => el.getAttribute('src')") or ""
            if not url.startswith("http"): url = "https://feverup.com" + url
            events.append({
                "title": title.strip(), "date": date.strip(), "description": "",
                "image": img.strip(), "url": url.strip(), "price": price.strip(), "source": "Fever"
            })
        except:
            continue
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

async def scrape_meetup(page):
    print("🔍 Scraping Meetup...")
    events = []
    url = "https://www.meetup.com/find/?location=ca--on--Toronto&source=EVENTS&customStartDate=2025-07-25T00%3A00%3A00-04%3A00&customEndDate=2025-07-27T23%3A59%3A00-04%3A00&eventType=inPerson"
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%dT00%%3A00%%3A00-04%%3A00")  # URL encoded "T00:00:00-04:00"
    end_str = dates[-1].strftime("%Y-%m-%dT23%%3A59%%3A00-04%%3A00")
    url = f"https://www.meetup.com/find/?location=ca--on--Toronto&source=EVENTS&customStartDate={start_str}&customEndDate={end_str}&eventType=inPerson"
    await page.goto(url)

    retries = 0
    prev_height = 0
    while retries < 5:
        await page.mouse.wheel(0, 5000)
        await asyncio.sleep(2)
        curr_height = await page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            retries += 1
        else:
            prev_height = curr_height
            retries = 0

    raw_events = await page.evaluate("""
        () => Array.from(document.querySelectorAll("a[href*='/events/']")).map(e => ({
            title: e.querySelector("h3")?.innerText || "N/A",
            date: e.querySelector("time")?.innerText || "N/A",
            url: e.href,
            image: e.querySelector("img")?.src || "",
            desc: e.querySelector("p")?.innerText || ""
        }))
    """)
    for e in raw_events:
        events.append({
            "title": e['title'], "date": e['date'], "description": e['desc'],
            "image": e['image'], "url": e['url'], "price": "Free", "source": "Meetup"
        })
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

async def scrape_stubhub(page):
    print("🔍 Scraping StubHub...")

    # Step 1: Go to Explore
    await page.goto("https://www.stubhub.ca/explore", timeout=60000)
    await page.wait_for_timeout(3000)

    # Step 2: Set location to Toronto
    try:
        await page.click("div[role='combobox']", timeout=5000)
        await page.wait_for_selector("input[placeholder='Search location']", timeout=10000)
        await page.fill("input[placeholder='Search location']", "Toronto")
        await page.wait_for_timeout(2000)
        toronto_option = await page.query_selector("ul[role='listbox'] li:has-text('Toronto, ON, Canada')")
        if toronto_option:
            await toronto_option.click()
        else:
            print("❌ 'Toronto, ON, Canada' option not found.")
            return []
        await page.wait_for_timeout(5000)
    except Exception as e:
        print(f"❌ Failed to select Toronto location: {e}")
        #return []

    # Step 3: Open Date dropdown
    try:
        await page.click("div[aria-label='Filter by date']")
        await page.click("[role='dialog'] > div > div:last-child", timeout=3000)
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"❌ Failed to open or click Custom Dates: {e}")
        return []

    # Step 4: Click the correct date range in calendar
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime('%a %b %d %Y')  # e.g. 'Fri Aug 01 2025'
    end_str = dates[-1].strftime('%a %b %d %Y')    # e.g. 'Sun Aug 03 2025'

    # click "next month" if August is not shown
    for i in range(3):
        if not await page.query_selector(f"[aria-label='{start_str}']"):
            next_btn = await page.query_selector("button[aria-label='Next Month']")
            if next_btn:
                await next_btn.click()
                await page.wait_for_timeout(1000)
        else:
            break

    try:
        await page.click(f"[aria-label='{start_str}']")
        await page.wait_for_timeout(300)
        await page.click(f"[aria-label='{end_str}']")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"❌ Failed selecting dates {start_str} to {end_str}: {e}")
        return []

    # Step 5: Load all listings via scroll + "Show More"
    max_scrolls = 15
    for _ in range(max_scrolls):
        await page.mouse.wheel(0, 8000)
        await page.wait_for_timeout(1500)

        show_more = await page.query_selector("button.sc-ikkxIA.dplCTc")
        if show_more:
            try:
                await show_more.click()
                await page.wait_for_timeout(3000)
            except:
                break
        else:
            break

    # Step 5: Wait for event cards
    try:
        await page.wait_for_selector("li > div.sc-38c7e8f1-3", timeout=10000)
    except:
        print("❌ Event listings not found.")
        return []

    # Step 6: Scrape events
    events = []
    cards = await page.query_selector_all("li > div.sc-38c7e8f1-3")
    for card in cards:
        try:
            title_el = await card.query_selector("p.sc-38c7e8f1-6")
            datetime_el = await card.query_selector_all("p.sc-38c7e8f1-8")
            link_el = await card.query_selector("a")
            img_el = await card.query_selector("img")

            title = await title_el.inner_text() if title_el else "N/A"
            datetime_text = await datetime_el[0].inner_text() if len(datetime_el) > 0 else "N/A"
            venue = await datetime_el[1].inner_text() if len(datetime_el) > 1 else "N/A"
            link = await link_el.get_attribute("href") if link_el else ""
            image = await img_el.get_attribute("src") if img_el else "N/A"

            events.append({
                "source": "StubHub",
                "title": title.strip(),
                "date": datetime_text.strip(),
                "description": venue.strip(),
                "url": link if link.startswith("http") else f"https://www.stubhub.ca{link}",
                "price": "N/A",
                "image": image
            })
        except Exception as e:
            print(f"⚠️ Error parsing card: {e}")
            continue

    print(f"✅ StubHub: Scraped {len(events)} events.")
    return events



async def scrape_blogto(page):
    print("🔍 Scraping BlogTO...")
    await page.goto("https://www.blogto.com/events/")
    await page.wait_for_selector(".event-info-box")

    target_days = get_upcoming_weekend_dates()
    events, seen = [], set()

    for day in target_days:
        try:
            selector = f'button[data-pika-year="{day.year}"][data-pika-month="{day.month - 1}"][data-pika-day="{day.day}"]'
            await page.click(selector)
            await asyncio.sleep(2)  # allow events to load
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            for card in soup.select(".event-info-box"):
                title_el = card.select_one(".event-info-box-title-link")
                if not title_el:
                    continue
                title = title_el.text.strip()
                if title in seen:
                    continue
                seen.add(title)

                date_text = card.select_one(".event-info-box-date").text.strip() if card.select_one(".event-info-box-date") else "N/A"
                desc = card.select_one(".event-info-box-description").text.strip() if card.select_one(".event-info-box-description") else ""
                image = card.select_one(".event-info-box-image")["src"] if card.select_one(".event-info-box-image") else ""
                url = title_el['href']

                events.append({
                    "title": title,
                    "date": f"{day.strftime('%A %B %d')} {date_text}" if date_text != "N/A" else day.strftime('%A %B %d'),
                    "description": desc,
                    "image": image,
                    "url": url,
                    "price": "N/A",
                    "source": "BlogTO"
                })

        except Exception as e:
            print(f"⚠️ Error on {day.strftime('%Y-%m-%d')}: {e}")
            continue
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

def send_email_with_attachment(to_email, subject, html_path):
    from_email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASS")  # Use an App Password, not your Gmail password

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach body
    msg.attach(MIMEText("open your 'Toronto Weekend Events' HTML file and book an event 2 weeks from now for your social life.", 'plain'))

    # Attach the file
    with open(html_path, "rb") as file:
        part = MIMEApplication(file.read(), Name="weekend_events_toronto.html")
        part['Content-Disposition'] = 'attachment; filename="weekend_events_toronto.html"'
        msg.attach(part)

    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, app_password)
        server.send_message(msg)
    print("📧 Email sent!")

# === Main Runner ===
async def aggregate_events():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")
    all_events = []
           
    async with async_playwright() as p:

        browser = await p.chromium.launch(
        headless=True,
        slow_mo=50,
        args=["--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        "--start-maximized"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True,
            locale="en-US",
            bypass_csp=True
        )
        
        page = await browser.new_page()
        #all_events += await scrape_eventbrite(page)
        #all_events += await scrape_fever(page)
        #all_events += await scrape_meetup(page)
        #all_events += await scrape_stubhub(page)
        #all_events += await scrape_blogto(page)
        await browser.close()

        # 🧹 De-duplicate by title only
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


    # Send the email
    send_email_with_attachment(
        to_email=os.getenv("EMAIL_TO"),
        subject = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}",
        html_path="weekend_events_toronto.html"
    )


def tester():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")
    all_events = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(user_agent=random_user_agent())
        page = context.new_page()
        all_events += scrape_eventbrite(page)
        browser.close()

def random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
    ])

if __name__ == "__main__":
    tester()
    #asyncio.run(aggregate_events())








