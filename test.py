import requests
import time

BINANCE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

def get_btc_price():
    response = requests.get(BINANCE_URL)
    data = response.json()
    return float(data["price"])

while True:
    price = get_btc_price()
    print(f"Текущая цена BTC/USDT: {price} USDT")
    time.sleep(60)  # Обновление каждые 60 секунды
