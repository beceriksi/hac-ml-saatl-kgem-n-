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
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Hata: Token veya Chat ID eksik!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Linklerin tıklanabilir olması için parse_mode Markdown veya HTML olmalı
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

def run_scanner():
    market_url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    try:
        response = requests.get(market_url, timeout=10).json()
        tickers = response.get('data', [])
    except:
        print("Piyasa verisi alınamadı.")
        return

    found_coins = []
    for ticker in tickers:
        symbol = ticker['instId'] # Örn: BTC-USDT
        if not symbol.endswith('-USDT'): continue

        candles = get_okx_candles(symbol)
        if not candles: continue

        curr_open  = float(candles[0][1])
        curr_close = float(candles[0][4])
        curr_vol   = float(candles[0][7]) 
        prev_vol   = float(candles[1][7])
        
        is_buying_heavy = curr_close > curr_open
        is_volume_spike = prev_vol > 0 and curr_vol > (prev_vol * 2.5)
        is_meaningful = curr_vol > 30000
        price_change_pct = ((curr_close - curr_open) / curr_open) * 100
        is_not_pumped = price_change_pct < 5.0

        if is_buying_heavy and is_volume_spike and is_meaningful and is_not_pumped:
            # TradingView Formatı: OKX:BTCUSDT (Aradaki tireyi kaldırıyoruz)
            tv_symbol = f"OKX:{symbol.replace('-', '')}"
            tv_link = f"https://www.tradingview.com/chart/?symbol={tv_symbol}"
            
            ratio = curr_vol / prev_vol
            found_coins.append({
                'symbol': symbol,
                'ratio': ratio,
                'vol': curr_vol,
                'change': price_change_pct,
                'link': tv_link
            })

    if found_coins:
        found_coins = sorted(found_coins, key=lambda x: x['ratio'], reverse=True)[:15]
        msg = "🎯 *OKX Alım Ağırlıklı Hacim Artışı*\n\n"
        for coin in found_coins:
            msg += f"✅ *{coin['symbol']}*\n"
            msg += f"   • Hacim Artışı: {coin['ratio']:.1f}x\n"
            msg += f"   • Mum Değişimi: %{coin['change']:.2f}\n"
            msg += f"   • Saatlik Hacim: ${coin['vol']:,.0f}\n"
            msg += f"   🔗 [TradingView'da Aç]({coin['link']})\n\n" # Link buraya eklendi
        send_telegram(msg)
    else:
        print("Kriterlere uygun alım sinyali bulunamadı.")

if __name__ == "__main__":
    run_scanner()
