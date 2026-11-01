import json
from datetime import datetime, timezone, timedelta
import requests
import os

OI_SPURTS_URL = "https://www.nseindia.com/api/live-analysis-oi-spurts-underlyings"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/market-data/oi-spurts",
}

DB_FILE = "stock_history_db.json"
OUTPUT_FILE = "stock_30day_analysis.json"

def fetch_live_data():
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
        resp = session.get(OI_SPURTS_URL, timeout=10)
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception as e:
        print("NSE request failed:", e)
        return []

def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_database(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)

def run_historical_tracker():
    raw_data = fetch_live_data()
    if not raw_data:
        print("No live data retrieved. Skipping update cycle.")
        return

    db = load_database()
    now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    timestamp_str = now_ist.strftime("%Y-%m-%d %H:%M")
    cutoff_date = now_ist - timedelta(days=30)

    processed_summary = []

    for row in raw_data:
        symbol = row.get("symbol")
        ltp = float(row.get("underlyingValue") or 0.0)
        p_chg = float(row.get("pChange") or 0.0)
        oi_chg = float(row.get("avgInOI") or 0.0)
        volume = int(row.get("tradedQty") or 0)

        if p_chg > 0 and oi_chg > 0:
            buildup = "Long Buildup"
        elif p_chg > 0 and oi_chg < 0:
            buildup = "Short Covering"
        elif p_chg < 0 and oi_chg > 0:
            buildup = "Short Buildup"
        else:
            buildup = "Long Unwinding"

        if symbol not in db:
            db[symbol] = []

        db[symbol].append({
            "timestamp": timestamp_str,
            "ltp": ltp,
            "p_chg": p_chg,
            "oi_chg": oi_chg,
            "volume": volume,
            "buildup": buildup
        })

        filtered_history = []
        for entry in db[symbol]:
            entry_time = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            if entry_time >= cutoff_date:
                filtered_history.append(entry)
        db[symbol] = filtered_history

        history = db[symbol]
        if len(history) > 1:
            initial_price = history[0]["ltp"]
            perf_30d_pct = round(((ltp - initial_price) / initial_price) * 100, 2) if initial_price > 0 else 0.0
            avg_volume = int(sum(item["volume"] for item in history) / len(history))
            
            long_count = sum(1 for item in history if item["buildup"] in ("Long Buildup", "Short Covering"))
            total_records = len(history)
            long_dominance_pct = round((long_count / total_records) * 100, 1) if total_records > 0 else 50.0
            trader_interest = "High Institutional/Trader Activity" if avg_volume > 1000000 else "Moderate/Retail Interest"
        else:
            perf_30d_pct = 0.0
            avg_volume = volume
            long_dominance_pct = 50.0
            trader_interest = "New Tracking Data"

        processed_summary.append({
            "symbol": symbol,
            "current_ltp": ltp,
            "current_buildup": buildup,
            "perf_30d_pct": perf_30d_pct,
            "avg_30d_volume": avg_volume,
            "trader_interest": trader_interest,
            "long_dominance_pct": long_dominance_pct,
            "short_dominance_pct": round(100 - long_dominance_pct, 1),
            "data_points_collected": len(history)
        })

    save_database(db)

    final_output = {
        "last_updated_ist": now_ist.strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "analysis": processed_summary
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

    print("Historical tracker updated successfully.")

if __name__ == "__main__":
    run_historical_tracker()
