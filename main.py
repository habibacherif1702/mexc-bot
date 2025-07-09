import requests
import time
import threading
from datetime import datetime
from keep_alive import keep_alive

# بيانات Telegram
TELEGRAM_BOT_TOKEN = "8086981481:AAFNOPkMrKasjIWSUtvIWKt2vSLxu6rO-o8"
TELEGRAM_CHAT_ID = "5927295954"

TRADING_PAIRS = [
    "BTC_USDT", "ETH_USDT", "BNB_USDT", "SOL_USDT", "XRP_USDT",
    "ADA_USDT", "DOGE_USDT", "AVAX_USDT", "LTC_USDT", "MATIC_USDT",
    "DOT_USDT", "TRX_USDT", "LINK_USDT", "ATOM_USDT", "NEAR_USDT",
    "APE_USDT", "FIL_USDT", "UNI_USDT", "ARB_USDT", "SAND_USDT"
]

trade_results = []  # ⬅️ لحفظ كل الصفقات وتحليلها لاحقًا

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("❌ Telegram Error:", e)

def calculate_rsi(closes, period=14):
    gains, losses = [], []
    for i in range(1, period + 1):
        change = closes[-i] - closes[-i - 1]
        if change >= 0:
            gains.append(change)
        else:
            losses.append(abs(change))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def analyze_symbol(pair):
    try:
        symbol = pair.replace("_", "")
        klines = requests.get(f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100").json()
        closes = [float(c[4]) for c in klines]
        if len(closes) < 50:
            return

        ema_14 = sum(closes[-14:]) / 14
        ema_50 = sum(closes[-50:]) / 50
        rsi = calculate_rsi(closes)
        current_price = closes[-1]

        signal = ""
        direction = ""

        if rsi < 30 and ema_14 > ema_50:
            signal = f"📈 فرصة شراء محتملة لـ {pair}\nRSI = {rsi:.2f}\nEMA14 > EMA50"
            direction = "BUY"
        elif rsi > 70 and ema_14 < ema_50:
            signal = f"📉 فرصة بيع محتملة لـ {pair}\nRSI = {rsi:.2f}\nEMA14 < EMA50"
            direction = "SELL"

        if signal:
            send_telegram(signal)
            print(signal)
            threading.Thread(target=evaluate_trade_after_delay, args=(pair, current_price, direction)).start()

    except Exception as e:
        print(f"❌ خطأ مع {pair}: {e}")

def evaluate_trade_after_delay(pair, entry_price, direction):
    time.sleep(60)  # ⏳ ننتظر دقيقة
    try:
        symbol = pair.replace("_", "")
        klines = requests.get(f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=1m&limit=2").json()
        latest_price = float(klines[-1][4])

        result = "❓ غير معروف"
        if direction == "BUY":
            result = "✅ Win" if latest_price > entry_price else "❌ Lose"
        elif direction == "SELL":
            result = "✅ Win" if latest_price < entry_price else "❌ Lose"

        message = f"📊 نتيجة صفقة {pair} بعد دقيقة:\nالإتجاه: {direction}\nسعر الدخول: {entry_price}\nالسعر الآن: {latest_price}\n➡️ {result}"
        send_telegram(message)
        print(message)
        trade_results.append(result)

    except Exception as e:
        print(f"❌ تقييم الصفقة فشل لـ {pair}: {e}")

def start_bot():
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"✅ تحليل جديد في {now}")
        threads = []
        for pair in TRADING_PAIRS:
            t = threading.Thread(target=analyze_symbol, args=(pair,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        time.sleep(120)  # تحليل كل 2 دقائق الآن

if __name__ == "__main__":
    keep_alive()
    send_telegram("🚀 بدأ البوت في التحليل الذكي للعملات (مع تقييم النتائج)...")
    start_bot()
