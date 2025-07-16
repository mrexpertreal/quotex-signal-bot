import ccxt
import pandas as pd
import time
import os
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands
from telegram import Bot

# Use environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'

RSI_BUY = 30
RSI_SELL = 70

bot = Bot(token=TELEGRAM_TOKEN)
exchange = ccxt.binance()

def fetch_data(symbol, timeframe='1m', limit=100):
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    return df

def analyze_market(df):
    close = df['close']
    rsi = RSIIndicator(close, window=14).rsi()
    macd = MACD(close).macd_diff()
    ema_fast = EMAIndicator(close, window=9).ema_indicator()
    ema_slow = EMAIndicator(close, window=21).ema_indicator()
    bb = BollingerBands(close)

    df['rsi'] = rsi
    df['macd'] = macd
    df['ema_fast'] = ema_fast
    df['ema_slow'] = ema_slow
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()

    latest = df.iloc[-1]
    signals = []

    if latest['rsi'] < RSI_BUY:
        signals.append("RSI Buy")
    elif latest['rsi'] > RSI_SELL:
        signals.append("RSI Sell")

    if latest['macd'] > 0:
        signals.append("MACD Buy")
    elif latest['macd'] < 0:
        signals.append("MACD Sell")

    if latest['ema_fast'] > latest['ema_slow']:
        signals.append("EMA Bullish")
    elif latest['ema_fast'] < latest['ema_slow']:
        signals.append("EMA Bearish")

    if latest['close'] < latest['bb_lower']:
        signals.append("BB Buy")
    elif latest['close'] > latest['bb_upper']:
        signals.append("BB Sell")

    buy_signals = [s for s in signals if "Buy" in s or "Bullish" in s]
    sell_signals = [s for s in signals if "Sell" in s or "Bearish" in s]

    if len(buy_signals) >= 3:
        return "BUY", signals
    elif len(sell_signals) >= 3:
        return "SELL", signals
    return None, signals

def send_signal(signal, price, indicators):
    message = f"""📢 *Quotex Auto Signal*
🔹 Pair: `{SYMBOL}`
🔹 Signal: *{signal}*
🔹 Price: {price}
📊 Indicators: {', '.join(indicators)}
🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')

def run_bot():
    while True:
        try:
            df = fetch_data(SYMBOL, TIMEFRAME)
            signal, indicators = analyze_market(df)
            if signal:
                price = df['close'].iloc[-1]
                send_signal(signal, price, indicators)
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            time.sleep(30)

run_bot()
