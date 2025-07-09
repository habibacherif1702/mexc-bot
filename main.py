import requests
import time
import threading
from datetime import datetime
from keep_alive import keep_alive
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import pandas as pd

# بيانات التليغرام
TELEGRAM_BOT_TOKEN = "8086981481:AAFNOPkMrKasjIWSUtvIWKt2vSLxu6rO-o8"  # ← ضع التوكن هنا
TELEGRAM_CHAT_ID = "5927295954"    # ← ضع Chat ID هنا

TRADING_PAIRS = [
    "BTC_USDT", "ETH_USDT", "BNB_USDT", "SOL_USDT", "XRP_USDT",
    "ADA_USDT", "DOGE_USDT", "AVAX_USDT", "LTC_USDT", "MATIC_USDT",
    "DOT_USDT", "TRX_USDT", "LINK_USDT", "ATOM_USDT", "NEAR_USDT",
    "APE_USDT", "FIL_USDT", "UNI_USDT", "ARB_USDT", "SAND_USDT"
]

# تلغرام
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)

signals_sent = []

# تحليل
def analyze_symbol(pair):
    try:
        symbol = pair.replace("_", "")
        url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100"
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        closes = df['close']

        rsi = RSIIndicator(closes, window=14).rsi().iloc[-1]
        macd = MACD(closes).macd().iloc[-1]
        macd_signal = MACD(closes).macd_signal().iloc[-1]
        ema14 = EMAIndicator(closes, window=14).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(closes, window=50).ema_indicator().iloc[-1]
        bb = BollingerBands(closes, window=20)
        upper = bb.bollinger_hband().iloc[-1]
        lower = bb.bollinger_lband().iloc[-1]
        price = closes.iloc[-1]

        signal = ""
        if rsi > 70 and macd < macd_signal and ema14 < ema50 and price > upper:
            signal = f"📉 صفقة بيع محتملة لـ {pair}\nRSI = {rsi:.2f}\nMACD < Signal\nEMA14 < EMA50\nالسعر فوق Bollinger"
        elif rsi < 30 and macd > macd_signal and ema14 > ema50 and price < lower:
            signal = f"📈 صفقة شراء محتملة لـ {pair}\nRSI = {rsi:.2f}\nMACD > Signal\nEMA14 > EMA50\nالسعر تحت Bollinger"

        if signal:
            signals_sent.append(signal)
            send_telegram(signal)
            print(signal)

    except Exception as e:
        print(f"❌ Error in {pair}: {e}")

# تقرير كل 20 دقيقة
def report():
    while True:
        time.sleep(1200)  # كل 20 دقيقة
        now = datetime.now().strftime("%H:%M:%S")
        if signals_sent:
            msg = f"📊 تقرير في {now}:\n\n" + "\n\n".join(signals_sent)
        else:
            msg = f"📊 تقرير في {now}:\nلا توجد صفقات حتى الآن."
        send_telegram(msg)
        signals_sent.clear()

# تحليل مستمر
def start_bot():
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"🌀 تحليل جديد في {now}")
        threads = []
        for pair in TRADING_PAIRS:
            t = threading.Thread(target=analyze_symbol, args=(pair,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        time.sleep(120)  # كل دقيقتين

if __name__ == "__main__":
    keep_alive()
    send_telegram("🚀 البوت يعمل بتحليل احترافي ويُرسل إشارات قوية + تقرير كل 20 دقيقة.")
    threading.Thread(target=report).start()
    start_bot()
