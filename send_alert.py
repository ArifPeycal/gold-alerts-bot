import csv
from datetime import datetime, timedelta
import statistics
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# --- CONFIG ---
CSV_FILE = "gold_ohlc_per_gram.csv"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def read_last_week_data():
    today = datetime.utcnow().date()
    one_week_ago = today - timedelta(days=7)
    weekly_data = []

    with open(CSV_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date_obj = datetime.strptime(row["date"], "%Y-%m-%d").date()
                if one_week_ago <= date_obj <= today:
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
📈 Avg Close: {statistics.mean(closes):.2f}
🟢 Open: {opens[0]:.2f}
🔴 Close: {closes[-1]:.2f}
📈 Up Days: {up_days} | 📉 Down Days: {down_days}
"""
    return message

def summarize_today(latest):
    if not latest:
        return "No data for today."

    daily_change = ((latest["close"] - latest["open"]) / latest["open"]) * 100

    if latest["close"] > latest["open"]:
        candle = "🟢 Bullish Day"
    elif latest["close"] < latest["open"]:
        candle = "🔴 Bearish Day"
    else:
        candle = "➖ Neutral Day"

    message = f"""📅 *Gold Daily Summary ({latest['day']}, {latest['date']})*

🟢 Open: {latest['open']:.2f}
🔺 High: {latest['high']:.2f}
🔻 Low: {latest['low']:.2f}
🔴 Close: {latest['close']:.2f}
📊 Change: {daily_change:+.2f}%
{candle}
"""
    return message

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

def main():
    data = read_last_week_data()
    if data:
        weekly_msg = summarize_week(data)
        send_telegram_message(weekly_msg)

        today_msg = summarize_today(data[-1])
        send_telegram_message(today_msg)

if __name__ == "__main__":
    main()
