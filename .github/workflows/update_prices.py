"""
Auto-fetch latest NSE prices for the portfolio and write prices.json.

Run by GitHub Actions on a schedule (see .github/workflows/update-prices.yml),
or locally:  pip install yfinance  &&  python automation/update_prices.py
"""

import json
import time
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
    "NMDC":       "NMDC.NS",
    "NSLNISP":    "NSLNISP.NS",
    "NSE:AWL":    "AWL.NS",
    "VALIANTORG": "VALIANTORG.NS",
    "BEEKAY":     "BEEKAY.NS",
    "ZENTEC":     "ZENTEC.NS",
    "ICIL":       "ICIL.NS",
    "JGCHEM":     "JGCHEM.NS",
    "AVANTEL":    "AVANTEL.NS",
    "INDOTECH":   "INDOTECH.NS",
    "KPITTECH":   "KPITTECH.NS",
    "PROSTARM":   "PROSTARM.NS",
    "TRANSRAILL": "TRANSRAILL.NS",
    "AARTIPHARM": "AARTIPHARM.NS",
    "GRAVITA":    "GRAVITA.NS",
    "CONCORDBIO": "CONCORDBIO.NS",
    "ARE&M":      "ARE&M.NS",
    "AVANTIFEED": "AVANTIFEED.NS",
    "BANDHANBNK": "BANDHANBNK.NS",
    "CANBK":      "CANBK.NS",
    "EQUITASBNK": "EQUITASBNK.NS",
    "IDBI":       "IDBI.NS",
    "IRFC":       "IRFC.NS",
    "ITC":        "ITC.NS",
    "ITCHOTELS":  "ITCHOTELS.NS",
    "MARKSANS":   "MARKSANS.NS",
    "PNB":        "PNB.NS",
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
    "INDGN":      "INDGN.NS",
    "AARTIDRUGS": "AARTIDRUGS.NS",
    "SUPRIYA":    "SUPRIYA.NS",
    "DPWIRES":    "DPWIRES.NS",
    "TATACHEM":   "TATACHEM.NS",
    "STEELCAS":   "STEELCAS.NS",
    "AXISTECETF": "AXISTECETF.NS",
    "COCHINSHIP": "COCHINSHIP.NS",
    "MBEL":       "MBEL.NS",
    "OLAELEC":    "OLAELEC.NS",
    "IRCTC":      "IRCTC.NS",
    "TRIDENT":    "TRIDENT.NS",
}


def fetch_all(symbols):
    """One batched request for ~6 weeks of daily closes for every ticker.
    Returns {symbol: (current, prev_1mo, prev_date_str)}."""
    out = {}
    data = yf.download(symbols, period="45d", interval="1d", group_by="ticker",
                       auto_adjust=False, progress=False, threads=True)
    for sym in symbols:
        try:
            closes = (data[sym]["Close"] if len(symbols) > 1 else data["Close"]).dropna()
        except Exception:
            continue
        if closes.empty:
            continue
        out[sym] = (float(closes.iloc[-1]), float(closes.iloc[0]),
                    closes.index[0].strftime("%d %b %Y"))
    return out


def fetch_one(symbol):
    """Fallback for any ticker the batch missed."""
    try:
        closes = yf.Ticker(symbol).history(period="45d")["Close"].dropna()
        if not closes.empty:
            return (float(closes.iloc[-1]), float(closes.iloc[0]),
                    closes.index[0].strftime("%d %b %Y"))
    except Exception:
        pass
    return None


def main():
    cmp, prev1mo = {}, {}
    try:
        with open("prices.json") as f:
            old = json.load(f)
            cmp = old.get("cmp", {})
            prev1mo = old.get("prev1mo", {})
    except Exception:
        pass

    symbols = list(TICKERS.values())
    try:
        batch = fetch_all(symbols)
    except Exception as e:
        print("Batch download failed:", e)
        batch = {}

    ok, prev_as_of = 0, None
    for key, symbol in TICKERS.items():
        res = batch.get(symbol)
        if res is None:
            time.sleep(1)
            res = fetch_one(symbol)
        if res is None:
            print(f"  {key:12s} {symbol:14s} -> FAILED")
            continue
        current, prev, prev_date = res
        cmp[key] = round(current, 2)
        prev1mo[key] = round(prev, 2)
        prev_as_of = prev_as_of or prev_date
        ok += 1
        print(f"  {key:12s} {symbol:14s} -> {current:.2f}  (1mo base {prev:.2f})")

    if ok == 0:
        # Fail the job loudly so it shows red in GitHub Actions instead of silently keeping stale data
        raise SystemExit("No prices fetched at all — Yahoo may be blocking/rate-limiting. Re-run later.")

    out = {
        "cmp": cmp,
        "prev1mo": prev1mo,
        "prevAsOf": prev_as_of,
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y"),
    }
    with open("prices.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote prices.json: {ok}/{len(TICKERS)} fetched, dated {out['updatedAt']}.")


if __name__ == "__main__":
    main()
