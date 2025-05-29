import csv
from datetime import datetime, timedelta
import statistics
import requests
import os
# --- CONFIG ---
CSV_FILE = "gold_ohlc_per_gram.csv"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
METALPRICE_API_KEY = os.getenv("METALPRICE_API_KEY")

def fetch_latest_price():
    url = (
        f"https://api.metalpriceapi.com/v1/latest"
        f"?api_key={METALPRICE_API_KEY}"
        f"&base=XAU"
        f"&currencies=MYR"
    )
    try:
        response = requests.get(url)
        data = response.json()

        if not data.get("success", False):
            return None, f"API Error: {data.get('error', {}).get('message', 'Unknown error')}"

        xau_to_myr = data["rates"]["MYR"]
        price_per_gram = xau_to_myr / GRAMS_PER_TROY_OUNCE

        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "price_per_gram": price_per_gram
        }, None
    except Exception as e:
        return None, f"Exception: {e}"

def read_last_week_data():
    today = datetime.utcnow().date()
    # Find most recent Monday (weekday=0)
    days_since_monday = today.weekday()  # Monday=0, Sunday=6
    start_of_week = today - timedelta(days=days_since_monday)

    weekly_data = []

    with open(CSV_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date_obj = datetime.strptime(row["date"], "%Y-%m-%d").date()
                if start_of_week <= date_obj <= today:
                    weekly_data.append({
                        "date": row["date"],
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "day": date_obj.strftime("%a")
                    })
            except Exception as e:
                print(f"Error parsing row: {row} | {e}")
    return weekly_data


def summarize_week(weekly_data):
    if not weekly_data or len(weekly_data) < 2:
        return "Not enough data for the week."

    opens = [d["open"] for d in weekly_data]
    closes = [d["close"] for d in weekly_data]
    highs = [d["high"] for d in weekly_data]
    lows = [d["low"] for d in weekly_data]

    trend = "📉 Downtrend"
    if closes[0] < closes[-1]:
        trend = "📈 Uptrend"
    elif closes[0] == closes[-1]:
        trend = "➖ Flat"

    percent_change = ((closes[-1] - opens[0]) / opens[0]) * 100

    highest_day = max(weekly_data, key=lambda x: x["high"])
    lowest_day = min(weekly_data, key=lambda x: x["low"])

    up_days = sum(1 for d in weekly_data if d["close"] > d["open"])
    down_days = sum(1 for d in weekly_data if d["close"] < d["open"])

    message = f"""📊 *Weekly Gold Price Summary (MYR/g)*

🗓️ {weekly_data[0]['date']} to {weekly_data[-1]['date']}
{trend}
📊 Weekly Change: {percent_change:+.2f}%
🔺 Highest: {highest_day['high']:.2f} on {highest_day['day']} ({highest_day['date']})
🔻 Lowest: {lowest_day['low']:.2f} on {lowest_day['day']} ({lowest_day['date']})
🟢 Open: {opens[0]:.2f}
🔴 Close: {closes[-1]:.2f}
📈 Up Days: {up_days} | 📉 Down Days: {down_days}
"""
    return message

def summarize_today_from_latest():
    latest, error = fetch_latest_price()
    if error or not latest:
        return f"❌ Failed to fetch today’s price: {error or 'Unknown error'}"

    price_today = latest["price_per_gram"]
    date_str = latest["date"]
    day_str = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a")

    # Get yesterday's close from CSV
    try:
        with open(CSV_FILE, newline='') as f:
            reader = list(csv.DictReader(f))
            if not reader:
                return "⚠️ No historical data found."

            # Find the last available date before today
            sorted_data = sorted(reader, key=lambda r: r["date"])
            yesterday_row = sorted_data[-1]
            yesterday_close = float(yesterday_row["close"])
            yesterday_date = yesterday_row["date"]
            change = price_today - yesterday_close
            percent_change = (change / yesterday_close) * 100

            direction = "🔼" if change > 0 else "🔽" if change < 0 else "➖"
            comparison = f"{direction} *Change vs Yesterday ({yesterday_date}):* {change:+.2f} MYR ({percent_change:+.2f}%)"
    except Exception as e:
        comparison = f"⚠️ Could not compare with yesterday: {e}"

    message = f"""📅 *Gold Daily Alert* ({day_str}, {date_str})

💰 *Current Price:* {price_today:.2f} MYR/g
{comparison}
"""
    return message

# --- Send message to Telegram ---
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Message sent to Telegram.")
    else:
        print("❌ Failed to send message:", response.text)


# --- MAIN ---
def main():
    data = read_last_week_data()
    if data:
        weekly_msg = summarize_week(data)
        send_telegram_message(weekly_msg)

    today_msg = summarize_today_from_latest()
    send_telegram_message(today_msg)


if __name__ == "__main__":
    main()
