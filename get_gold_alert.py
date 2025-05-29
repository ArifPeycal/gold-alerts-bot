import requests
from datetime import datetime, timedelta
import csv
import os
# --- CONFIG ---
API_KEY = os.getenv("METALPRICE_API_KEY")
BASE = "XAU"
QUOTE = "MYR"
CSV_FILE = "gold_ohlc_per_gram.csv"

GRAMS_PER_TROY_OUNCE = 31.1035  # Constant to convert troy ounce to gram

def fetch_ohlc(date_str):
    API_URL = (
        f"https://api.metalpriceapi.com/v1/ohlc"
        f"?api_key={API_KEY}"
        f"&base={BASE}"
        f"&currency={QUOTE}"
        f"&date={date_str}"
    )
    try:
        response = requests.get(API_URL)
        data = response.json()
        if response.status_code == 200 and data.get("success") is True:
            rate = data.get("rate", {})
            # Convert prices from per troy ounce to per gram
            open_gram = rate.get("open") / GRAMS_PER_TROY_OUNCE if rate.get("open") else None
            high_gram = rate.get("high") / GRAMS_PER_TROY_OUNCE if rate.get("high") else None
            low_gram = rate.get("low") / GRAMS_PER_TROY_OUNCE if rate.get("low") else None
            close_gram = rate.get("close") / GRAMS_PER_TROY_OUNCE if rate.get("close") else None
            
            return {
                "date": date_str,
                "open": open_gram,
                "high": high_gram,
                "low": low_gram,
                "close": close_gram,
            }
        else:
            print("Error fetching OHLC data:", data)
            return None
    except Exception as e:
        print(f"Exception fetching OHLC data: {e}")
        return None

def load_existing_dates():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, newline='') as f:
        reader = csv.DictReader(f)
        return {row["date"] for row in reader}

def append_ohlc_to_csv(ohlc):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:  # Create a header if the file doesn't exist
            writer.writerow(["date", "open", "high", "low", "close"])
        if ohlc:  # Write OHLC data only if valid data is fetched
            writer.writerow([
                ohlc["date"],
                f"{ohlc['open']:.4f}" if ohlc['open'] else "",
                f"{ohlc['high']:.4f}" if ohlc['high'] else "",
                f"{ohlc['low']:.4f}" if ohlc['low'] else "",
                f"{ohlc['close']:.4f}" if ohlc['close'] else "",
            ])
        else:
            print("No valid data to append to CSV.")

def main():
    date_str = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
    print(f"Fetching OHLC data for {date_str} (prices per gram)...")
    ohlc = fetch_ohlc(date_str)
    if ohlc:
        print(f"OHLC for {date_str}: Open={ohlc['open']:.4f}, High={ohlc['high']:.4f}, Low={ohlc['low']:.4f}, Close={ohlc['close']:.4f}")
        append_ohlc_to_csv(ohlc)
    else:
        print("Failed to fetch OHLC data.")

if __name__ == "__main__":
    main()


