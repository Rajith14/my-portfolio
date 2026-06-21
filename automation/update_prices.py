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


def fetch_price(symbol):
    """Return the latest close price for a Yahoo symbol, or None on failure."""
    t = yf.Ticker(symbol)
    # Fast path: live/last price
    try:
        p = t.fast_info["last_price"]
        if p:
            return float(p)
    except Exception:
        pass
    # Fallback: last daily close
    try:
        hist = t.history(period="5d")
        if not hist.empty:
            return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        pass
    return None


def main():
    cmp = {}
    # Keep any prices we already have, so a single failed fetch doesn't wipe a stock
    try:
        with open("prices.json") as f:
            cmp = json.load(f).get("cmp", {})
    except Exception:
        pass

    for key, symbol in TICKERS.items():
        price = fetch_price(symbol)
        if price is not None:
            cmp[key] = round(price, 2)
            print(f"  {key:12s} {symbol:14s} -> {price:.2f}")
        else:
            print(f"  {key:12s} {symbol:14s} -> FAILED (kept previous)")

    out = {
        "cmp": cmp,
        "updatedAt": datetime.datetime.utcnow().strftime("%d %b %Y"),
    }
    with open("prices.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote prices.json with {len(cmp)} prices, dated {out['updatedAt']}.")


if __name__ == "__main__":
    main()
