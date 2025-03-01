import requests

def get_btc_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка статуса HTTP-запроса
        
        data = response.json()
        print("Ответ API:", data)  # Выводим полный ответ API
        
        if "price" in data:
            return float(data["price"])
        else:
            print("Ошибка: ключ 'price' отсутствует в ответе API")
            return None
    
    except requests.exceptions.RequestException as e:
        print("Ошибка запроса:", e)
        return None
    except ValueError:
        print("Ошибка преобразования JSON")
        return None

# Основной код
price = get_btc_price()

if price is not None:
    print(f"Текущая цена BTC: {price} USDT")
else:
    print("Не удалось получить цену BTC")

