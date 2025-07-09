import requests
import time
import threading
from datetime import datetime
from keep_alive import keep_alive

# بيانات Telegram
TELEGRAM_BOT_TOKEN = "8086981481:AAFNOPkMrKasjIWSUtvIWKt2vSLxu6rO-o8"  # ضع التوكن الخاص بك هنا
TELEGRAM_CHAT_ID = "5927295954"    # ضع معرف الشات الخاص بك هنا

# الأزواج التي سيتم تحليلها (20 زوج)
TRADING_PAIRS = [
    "BTC_USDT", "ETH_USDT", "BNB_USDT", "SOL_USDT", "XRP_USDT",
    "ADA_USDT", "DOGE_USDT", "AVAX_USDT", "LTC_USDT", "MATIC_USDT",
    "DOT_USDT", "TRX_USDT", "LINK_USDT", "ATOM_USDT", "NEAR_USDT",
    "APE_USDT", "FIL_USDT", "UNI_USDT", "ARB_USDT", "SAND_USDT"
]

# إرسال رسالة تلغرام
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("❌ Telegram Error:", e)

# تحليل باستخدام بيانات RSI و EMA فقط
def analyze_symbol(pair):
    try:
        symbol = pair.replace("_", "")
        klines = requests.get(f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100").json()
        closes = [float(c[4]) for c in klines]

        if len(closes) < 50:
            return

        # حساب EMA
        ema_14 = sum(closes[-14:]) / 14
        ema_50 = sum(closes[-50:]) / 50
        rsi = calculate_rsi(closes)

        signal = ""
        if rsi < 30 and ema_14 > ema_50:
            signal = f"📈 فرصة شراء محتملة لـ {pair}\nRSI = {rsi:.2f}\nEMA14 > EMA50"
        elif rsi > 70 and ema_14 < ema_50:
            signal = f"📉 فرصة بيع محتملة لـ {pair}\nRSI = {rsi:.2f}\nEMA14 < EMA50"

        if signal:
            send_telegram(signal)
            print(signal)

    except Exception as e:
        print(f"❌ خطأ مع {pair}: {e}")

# حساب RSI
def calculate_rsi(closes, period=14):
    gains = []
    losses = []
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

# تشغيل التحليل المستمر
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
        time.sleep(120)  # تحليل كل دقيقتين

if __name__ == "__main__":
    keep_alive()
    send_telegram("🚀 بدأ البوت في التحليل الذكي للعملات (كل دقيقتين)...")
    start_bot()
