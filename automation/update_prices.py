"""
Auto-fetch latest NSE prices for the portfolio and write prices.json.

Run by GitHub Actions on a schedule (see .github/workflows/update-prices.yml),
or locally:  pip install yfinance  &&  python automation/update_prices.py
"""

import json
import datetime
import yfinance as yf

# Dashboard's internal ticker  ->  Yahoo Finance symbol (NSE = ".NS")
TICKERS = {
    "YESBANK":    "YESBANK.NS",
    "ACE":        "ACE.NS",
    "HDFCAMC":    "HDFCAMC.NS",
    "RELIANCE":   "RELIANCE.NS",
    "JIOFIN":     "JIOFIN.NS",
    "VAIBHAVGBL": "VAIBHAVGBL.NS",
    "CDSL":       "CDSL.NS",
    "NSE:HPL":    "HPL.NS",
    "NMDC":       "NMDC.NS",
    "NSLNISP":    "NSLNISP.NS",
    "NSE:AWL":    "AWL.NS",
    "VALIANTORG": "VALIANTORG.NS",
    "BEEKAY":     "BEEKAY.NS",
    "ZENTEC":     "ZENTEC.NS",
    "ICIL":       "ICIL.NS",
    "JGCHEM":     "JGCHEM.NS",
    "AVANTEL":    "AVANTEL.NS",
    "TDPOWERSYS": "TDPOWERSYS.NS",
    "INDOTECH":   "INDOTECH.NS",
    "KPITTECH":   "KPITTECH.NS",
    "PROSTARM":   "PROSTARM.NS",
    "TRANSRAILL": "TRANSRAILL.NS",
    "AARTIPHARM": "AARTIPHARM.NS",
    "GRAVITA":    "GRAVITA.NS",
    "ARE&M":      "ARE&M.NS",
    "AVANTIFEED": "AVANTIFEED.NS",
    "BANDHANBNK": "BANDHANBNK.NS",
    "CANBK":      "CANBK.NS",
    "EQUITASBNK": "EQUITASBNK.NS",
    "HSCL":       "HSCL.NS",
    "IDBI":       "IDBI.NS",
    "IRFC":       "IRFC.NS",
    "ITC":        "ITC.NS",
    "ITCHOTELS":  "ITCHOTELS.NS",
    "MARKSANS":   "MARKSANS.NS",
    "PNB":        "PNB.NS",
    "SBILIFE":    "SBILIFE.NS",
    "TATASTEEL":  "TATASTEEL.NS",
    "UJJIVANSFB": "UJJIVANSFB.NS",
    "UNIONBANK":  "UNIONBANK.NS",
    "NIFTYBEES":  "NIFTYBEES.NS",
    "GOLDBEES":   "GOLDBEES.NS",
    "UTKARSHBNK": "UTKARSHBNK.NS",
    "MSTCLTD":    "MSTCLTD.NS",
    "POCL":       "POCL.NS",
    "GLOBUSSPR":  "GLOBUSSPR.NS",
    "AVALON":     "AVALON.NS",
    "SAMHI":      "SAMHI.NS",
    "ASTRAMICRO": "ASTRAMICRO.NS",
    "ROSSTECH":   "ROSSTECH.NS",
    "INDGN":      "INDGN.NS",
    "AARTIDRUGS": "AARTIDRUGS.NS",
    "SUPRIYA":    "SUPRIYA.NS",
    "DPWIRES":    "DPWIRES.NS",
    "TATACHEM":   "TATACHEM.NS",
    "STEELCAS":   "STEELCAS.NS",
    "AXISTECETF": "AXISTECETF.NS",
    "COCHINSHIP": "COCHINSHIP.NS",
    "TRIDENT":    "TRIDENT.NS",
}


def fetch_current_and_prev(symbol):
    """Return (current_price, price_about_1_month_ago, baseline_date_str).
    Any of them may be None if the fetch fails."""
    t = yf.Ticker(symbol)
    current = prev = prev_date = None
    # ~6 weeks of history: first close = baseline ~1 month ago, last close = latest
    try:
        closes = t.history(period="45d")["Close"].dropna()
        if not closes.empty:
            current = float(closes.iloc[-1])
            prev = float(closes.iloc[0])
            prev_date = closes.index[0].strftime("%d %b %Y")
    except Exception:
        pass
    # Prefer the live/last traded price for "current" when available
    try:
        lp = t.fast_info["last_price"]
        if lp:
            current = float(lp)
    except Exception:
        pass
    return current, prev, prev_date


def main():
    cmp = {}
    prev1mo = {}
    # Keep any values we already have, so a single failed fetch doesn't wipe a stock
    try:
        with open("prices.json") as f:
            old = json.load(f)
            cmp = old.get("cmp", {})
            prev1mo = old.get("prev1mo", {})
    except Exception:
        pass

    prev_as_of = None
    for key, symbol in TICKERS.items():
        current, prev, prev_date = fetch_current_and_prev(symbol)
        if current is not None:
            cmp[key] = round(current, 2)
        if prev is not None:
            prev1mo[key] = round(prev, 2)
            if prev_as_of is None:
                prev_as_of = prev_date
        status = f"{current:.2f}" if current is not None else "FAILED"
        mom = f"  (1mo base {prev:.2f})" if prev is not None else ""
        print(f"  {key:12s} {symbol:14s} -> {status}{mom}")

    out = {
        "cmp": cmp,
        "prev1mo": prev1mo,
        "prevAsOf": prev_as_of,
        "updatedAt": datetime.datetime.utcnow().strftime("%d %b %Y"),
    }
    with open("prices.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote prices.json with {len(cmp)} prices, dated {out['updatedAt']}.")


if __name__ == "__main__":
    main()
