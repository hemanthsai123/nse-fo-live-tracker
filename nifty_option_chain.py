import json
from datetime import datetime, timezone, timedelta
import requests

OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/option-chain",
}

def fetch_option_chain():
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
        resp = session.get(OPTION_CHAIN_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        filtered_data = data.get("records", {})
        expiry_dates = filtered_data.get("expiryDates", [])
        nearest_expiry = expiry_dates[0] if expiry_dates else None
        rows = filtered_data.get("data", [])

        strike_matrix = []
        total_call_oi = 0
        total_put_oi = 0

        for row in rows:
            if row.get("expiryDate") != nearest_expiry:
                continue
            
            strike = row.get("strikePrice")
            ce = row.get("CE", {})
            pe = row.get("PE", {})
            
            ce_oi = ce.get("openInterest", 0)
            pe_oi = pe.get("openInterest", 0)
            
            total_call_oi += ce_oi
            total_put_oi += pe_oi

            strike_matrix.append({
                "strike": strike,
                "call_oi": ce_oi,
                "put_oi": pe_oi,
                "net_diff_pe_ce": pe_oi - ce_oi
            })

        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0
        ist_time = datetime.now(timezone(timedelta(hours=5, minutes=30)))

        output = {
            "last_updated_ist": ist_time.strftime("%Y-%m-%d %I:%M:%S %p IST"),
            "nearest_expiry": nearest_expiry,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "put_call_ratio": pcr,
            "strike_chain": strike_matrix
        }

        with open("nifty_option_chain.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)
        print("Nifty Option Chain data successfully updated.")
    except Exception as e:
        print("NSE request failed:", e)

if __name__ == "__main__":
    fetch_option_chain()
