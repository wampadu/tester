# 🎉 Toronto Events Aggregator

This Python script scrapes and compiles a list of **Toronto weekend events** (Friday–Sunday) from five popular sites:

- [BlogTO](https://www.blogto.com/events/)
- [Eventbrite](https://www.eventbrite.ca/)
- [Meetup](https://www.meetup.com/)
- [StubHub](https://www.stubhub.ca/)
- [Fever](https://feverup.com/toronto)

It generates an interactive, searchable HTML table and emails the file to you weekly.

---

## 🧠 What It Does

- Aggregates all upcoming **next-weekend** events
- Compiles data into a styled HTML file with:
  - Search + filter + CSV/Excel export
  - Responsive design
  - "🎲 Random Event Picker" button
- Sends the HTML as an **email attachment**

---

## 📣 Disclaimer:  It Scrapes 2 Weeks Ahead

This script is currently set to scrape events **two weekends from now** (not for the upcoming weekend).  
The idea is to give you **more time to plan, invite friends, and book tickets early**.
Want it to scrape only this upcoming weekend?
In `events_emailer.py`, find this line:
```python
friday = today + timedelta(days=days_until_friday + 7)
And replace it with:
friday = today + timedelta(days=days_until_friday)
```
---

## 🛠️ How to Use This Repo Yourself

1. **Fork or clone this repo** to your GitHub account.
2. In your repo, go to:
   - `Settings` → `Secrets and variables` → `Actions`
3. Click **“New repository secret”** and add the following:

| Secret Name   | What to Enter                            |
|---------------|------------------------------------------|
| `GMAIL_USER`  | Your Gmail address (e.g., you@gmail.com) |
| `GMAIL_PASS`  | Your Gmail **App Password** (not your normal password) |
| `EMAIL_TO`    | The email address to receive the file    |

📌 **Note:** You must enable [2FA in Gmail](https://myaccount.google.com/security) and create an [App Password](https://myaccount.google.com/apppasswords).

It runs every **Friday at 6:00 AM EST**, triggered by a **GitHub Actions** scheduled workflow (`.github/workflows/scrape-events.yml`) when forked, so you'll always have event picks before the weekend after next.

You can also manually trigger it via the **"Run workflow"** button on the GitHub Actions tab.

## 📦 Requirements

The script uses:

- `playwright`
- `beautifulsoup4`
- Python standard libraries: `asyncio`, `datetime`, `html`, `smtplib`, `email`

Install with:

```bash
pip install -r requirements.txt
playwright install --with-deps



