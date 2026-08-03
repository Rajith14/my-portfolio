"""
Auto-fetch recent company news for the portfolio and write news.json.

Runs by GitHub Actions on a weekly schedule (see .github/workflows/update-news.yml),
or locally:  pip install yfinance  &&  python automation/update_news.py

How it works
------------
- For each holding it pulls recent headlines from Yahoo Finance (yfinance).
- Each headline is bucketed into one of the dashboard's categories by keyword:
      order · orderbook · capacity · dividend · management · legal · client · guidance · macro
- Curated items already in news.json (marked "curated": true) are ALWAYS kept,
  so hand-written intel is never overwritten by the auto-feed. Fetched items are
  merged in and de-duplicated by headline.
- The dashboard (Portfolio News.dc.html) reads news.json on load and every time
  you hit "Check for updates", and keeps your read/unread state in the browser.
"""

import json
import time
import datetime

import yfinance as yf

# Dashboard's internal ticker  ->  Yahoo Finance symbol (NSE = ".NS")
TICKERS = {
    "YESBANK": "YESBANK.NS", "ACE": "ACE.NS", "HDFCAMC": "HDFCAMC.NS",
    "RELIANCE": "RELIANCE.NS", "JIOFIN": "JIOFIN.NS", "VAIBHAVGBL": "VAIBHAVGBL.NS",
    "CDSL": "CDSL.NS", "NSE:HPL": "HPL.NS", "NMDC": "NMDC.NS", "NSLNISP": "NSLNISP.NS",
    "NSE:AWL": "AWL.NS", "VALIANTORG": "VALIANTORG.NS", "BEEKAY": "BEEKAY.NS",
    "ZENTEC": "ZENTEC.NS", "ICIL": "ICIL.NS", "JGCHEM": "JGCHEM.NS", "AVANTEL": "AVANTEL.NS",
    "INDOTECH": "INDOTECH.NS", "KPITTECH": "KPITTECH.NS", "PROSTARM": "PROSTARM.NS",
    "TRANSRAILL": "TRANSRAILL.NS", "AARTIPHARM": "AARTIPHARM.NS", "GRAVITA": "GRAVITA.NS",
    "CONCORDBIO": "CONCORDBIO.NS", "ARE&M": "ARE&M.NS", "AVANTIFEED": "AVANTIFEED.NS",
    "BANDHANBNK": "BANDHANBNK.NS", "CANBK": "CANBK.NS", "EQUITASBNK": "EQUITASBNK.NS",
    "HSCL": "HSCL.NS", "IDBI": "IDBI.NS", "IRFC": "IRFC.NS", "ITC": "ITC.NS",
    "ITCHOTELS": "ITCHOTELS.NS", "MARKSANS": "MARKSANS.NS", "PNB": "PNB.NS",
    "SBILIFE": "SBILIFE.NS", "TATASTEEL": "TATASTEEL.NS", "UJJIVANSFB": "UJJIVANSFB.NS",
    "UNIONBANK": "UNIONBANK.NS", "NIFTYBEES": "NIFTYBEES.NS", "GOLDBEES": "GOLDBEES.NS",
    "UTKARSHBNK": "UTKARSHBNK.NS", "MSTCLTD": "MSTCLTD.NS", "POCL": "POCL.NS",
    "GLOBUSSPR": "GLOBUSSPR.NS", "AVALON": "AVALON.NS", "SAMHI": "SAMHI.NS",
    "ASTRAMICRO": "ASTRAMICRO.NS", "ROSSTECH": "ROSSTECH.NS", "INDGN": "INDGN.NS",
    "AARTIDRUGS": "AARTIDRUGS.NS", "SUPRIYA": "SUPRIYA.NS", "DPWIRES": "DPWIRES.NS",
    "TATACHEM": "TATACHEM.NS", "STEELCAS": "STEELCAS.NS", "AXISTECETF": "AXISTECETF.NS",
    "COCHINSHIP": "COCHINSHIP.NS", "TRIDENT": "TRIDENT.NS",
}

# Checked top-to-bottom; first bucket whose keyword appears wins.
CATEGORY_KEYWORDS = [
    ("legal",      ["sebi", "probe", "fraud", "penalty", "lawsuit", "allegation",
                     "investigat", "show cause", "fined", "raid", "insolven", "default",
                     "downgrade", "scam", "regulator"]),
    ("order",      ["order", "contract", "bags ", "bagged", "wins ", "won ", "awarded",
                     "loa ", "letter of award", "work order", "l1 "]),
    ("capacity",   ["capacity", "expansion", "greenfield", "brownfield", "new plant",
                     "facility", "commission", "mtpa", "gwh", "capex", "ramp-up"]),
    ("dividend",   ["dividend", "bonus", "stock split", "share split", "buyback",
                     "record date", "interim dividend"]),
    ("management", ["ceo", "cfo", " md ", "managing director", "resign", "appoint",
                     "steps down", "board approves", "chairman", "reshuffle"]),
    ("client",     ["client", "customer", "partnership", "tie-up", "tie up", "mou",
                     "collaborat", "joint venture", " jv ", "alliance"]),
    ("guidance",   ["guidance", "outlook", "margin", "forecast", "commentary", "concall",
                     "results", "net profit", "revenue", "q1", "q2", "q3", "q4",
                     "quarter", "yoy", "qoq", "earnings"]),
]

MAX_FETCHED_PER_TICKER = 8


def categorize(title):
    t = " " + title.lower() + " "
    for cat, kws in CATEGORY_KEYWORDS:
        if any(kw in t for kw in kws):
            return cat
    return "macro"


def parse_news(symbol):
    """Return a list of {category, date, text, url} for a ticker. yfinance has shipped
    two different news shapes; handle both and fail soft."""
    out = []
    try:
        raw = yf.Ticker(symbol).news or []
    except Exception:
        return out
    for n in raw:
        title = link = ts = None
        # newer schema: {"content": {"title", "pubDate", "canonicalUrl": {"url"}}}
        c = n.get("content") if isinstance(n, dict) else None
        if isinstance(c, dict):
            title = c.get("title")
            link = (c.get("canonicalUrl") or {}).get("url") or (c.get("clickThroughUrl") or {}).get("url")
            pd = c.get("pubDate") or c.get("displayTime")
            if pd:
                try:
                    ts = datetime.datetime.fromisoformat(pd.replace("Z", "+00:00"))
                except Exception:
                    ts = None
        # older schema: {"title", "link", "providerPublishTime"}
        if not title:
            title = n.get("title")
            link = n.get("link")
            ep = n.get("providerPublishTime")
            if ep:
                ts = datetime.datetime.utcfromtimestamp(ep)
        if not title:
            continue
        date_str = ts.strftime("%d %b %y") if ts else ""
        out.append({
            "category": categorize(title),
            "date": date_str,
            "text": title.strip(),
            "url": link or "",
            "_ts": ts.timestamp() if ts else 0,
        })
    # newest first, capped
    out.sort(key=lambda x: x["_ts"], reverse=True)
    for x in out:
        x.pop("_ts", None)
    return out[:MAX_FETCHED_PER_TICKER]


def norm(s):
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def main():
    # Preserve existing file so curated intel and prior fetches survive a bad run.
    existing = {"notes": {}}
    try:
        with open("news.json") as f:
            existing = json.load(f)
    except Exception:
        pass
    prev_notes = existing.get("notes", {})

    notes = {}
    total_fetched = 0
    for key, symbol in TICKERS.items():
        prev = prev_notes.get(key, {})
        curated = [it for it in prev.get("items", []) if it.get("curated") or prev.get("curated")]
        # keep any prior items so read-state (content-hashed in the UI) stays stable
        kept = list(prev.get("items", []))
        seen = {norm(it.get("text")) for it in kept}

        fetched = parse_news(symbol)
        added = 0
        for it in fetched:
            if norm(it["text"]) in seen:
                continue
            kept.append(it)
            seen.add(norm(it["text"]))
            added += 1
        total_fetched += added

        if kept:
            entry = {"items": kept}
            if prev.get("total"):
                entry["total"] = prev["total"]
            notes[key] = entry
        print(f"  {key:12s} {symbol:14s} -> +{added} new  ({len(kept)} total)")
        time.sleep(0.4)  # be gentle with Yahoo

    out = {
        "schema": "news_v2",
        "updatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        "notes": notes,
    }
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote news.json · {len(notes)} stocks with news · {total_fetched} new headlines · dated {out['updatedAt']}.")


if __name__ == "__main__":
    main()
