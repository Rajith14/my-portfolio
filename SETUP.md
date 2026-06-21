# Auto-updating Portfolio Dashboard — free monthly price refresh

This makes your dashboard fetch the latest NSE prices **automatically every month**, for free,
using GitHub Actions (the scheduler) + GitHub Pages (the free host). No server to run, no cost.

## What's in here
- `Portfolio Allocation.dc.html` + `support.js` — the dashboard (reads `prices.json` on load)
- `prices.json` — the latest prices (this is what gets refreshed each month)
- `automation/update_prices.py` — the Python script that fetches prices via `yfinance`
- `.github/workflows/update-prices.yml` — the monthly schedule (1st of each month, 09:00 IST)

## One-time setup (~10 minutes)

1. **Create a free GitHub account** at github.com (if you don't have one).

2. **Make a new repository** — name it anything (e.g. `my-portfolio`). Keep it Public
   (Pages is free for public repos) or Private if you prefer (Pages works on private too on free plans).

3. **Upload all these files** keeping the folder structure intact:
   - `Portfolio Allocation.dc.html`, `support.js`, `prices.json` at the top level
   - the `automation/` folder
   - the `.github/` folder (GitHub may hide it in the UI — it's there)

   Easiest way: on the repo page click **Add file -> Upload files**, drag everything in, Commit.

4. **Turn on GitHub Pages** — repo **Settings -> Pages -> Build and deployment**,
   Source = "Deploy from a branch", Branch = `main`, folder = `/ (root)`, Save.
   After a minute your dashboard is live at:
   `https://<your-username>.github.io/<repo-name>/Portfolio%20Allocation.dc.html`
   **Bookmark that link** — that's your dashboard, openable from any device.

5. **Enable Actions write access** — repo **Settings -> Actions -> General ->
   Workflow permissions**, choose **Read and write permissions**, Save.
   (Lets the monthly job save the refreshed `prices.json` back.)

## Test it now (don't wait for the 1st)
Repo **Actions** tab -> "Update portfolio prices" -> **Run workflow**.
It fetches live prices, commits `prices.json`, and your Pages link shows the new numbers
with "Prices auto-updated <date>" in the header.

## After that
It runs by itself on the 1st of every month. Just open your bookmarked link whenever you
want to check — it always shows the latest fetched prices. You can still use the
**Update prices** button to hand-correct any single stock (your manual edit wins over the
auto price for that stock, saved in your browser).

## Notes / honest caveats
- Prices come from Yahoo Finance via `yfinance` (free, unofficial). Fine for a personal
  monthly view; occasionally a ticker may miss — the script keeps the previous price if so.
- Free GitHub Actions minutes are far more than this needs (one short run a month).
- To change the schedule, edit the `cron` line in `.github/workflows/update-prices.yml`
  (it's in UTC). To add/remove stocks, edit the `TICKERS` map in `automation/update_prices.py`
  and the matching data in the dashboard.
