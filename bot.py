import requests
import os
import time

# GitHub Secrets'tan alınacak bilgiler
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def get_okx_candles(symbol):
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar=1H&limit=2"
    try:
        res = requests.get(url, timeout=10).json()
        if res['code'] == '0' and len(res['data']) >= 2:
            return res['data']
        return None
    except:
        return None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    requests.post(url, json=payload)

def run_scanner():
    market_url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    try:
        tickers = requests.get(market_url).json()['data']
    except:
        return

    found_coins = []
    for ticker in tickers:
        symbol = ticker['instId']
        if not symbol.endswith('-USDT'): continue

        candles = get_okx_candles(symbol)
        if not candles: continue

        # [0] Mevcut saat, [1] Bir önceki saat
        current_vol = float(candles[0][7]) 
        prev_vol = float(candles[1][7])
        
        if prev_vol > 0 and current_vol > (prev_vol * 2.5) and current_vol > 30000:
            ratio = current_vol / prev_vol
            found_coins.append({'symbol': symbol, 'ratio': ratio, 'volume': current_vol})

    if found_coins:
        found_coins = sorted(found_coins, key=lambda x: x['ratio'], reverse=True)[:15]
        msg = "🚀 *OKX Hacim Girişi Tespit Edildi!*\n\n"
        for coin in found_coins:
            msg += f"🔹 *{coin['symbol']}*\n   • Artış: {coin['ratio']:.1f}x\n   • Hacim: ${coin['volume']:,.0f}\n\n"
        send_telegram(msg)

if __name__ == "__main__":
    run_scanner()
