import requests
import pandas as pd
import time

# --- НАСТРОЙКИ ---
TOKEN = "8033733352:AAHp0TYZ1CJjbjjcNrqiJ53jXHqq4kQbeRI"
CHAT_ID = "462399522"
SPREAD_THRESHOLD = 0.3  # Порог спреда для отправки уведомления (> 0.5%)
MARK_PRICE_THRESHOLD = 0.1  # Порог отклонения от Mark Price (> 0.2%)
MIN_FUTURES_VOLUME = 100000  # Минимальный объем на фьючерсах (100k USDT)
SCAN_INTERVAL = 600  # Время между проверками (в секундах) - 600 секунд = 10 минут

# --- API Binance ---
FUTURES_BOOK_TICKER_URL = "https://fapi.binance.com/fapi/v1/ticker/bookTicker"
SPOT_BOOK_TICKER_URL = "https://api.binance.com/api/v3/ticker/bookTicker"
FUTURES_24HR_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr"
EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
MARK_PRICE_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"

# --- Функция отправки уведомлений в Telegram ---
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# --- Основная функция сканирования ---
def scan_binance():
    # Получаем список фьючерсных пар
    try:
        exchange_info = requests.get(EXCHANGE_INFO_URL).json()
        print("Ответ от API Binance:")
        print(exchange_info)  # Выводим полный ответ API для диагностики

        if 'symbols' in exchange_info:
            futures_pairs = {symbol['symbol'] for symbol in exchange_info['symbols'] if symbol['contractType'] == 'PERPETUAL'}
        else:
            print("Ошибка: 'symbols' не найдены в ответе API.")
            return
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе данных с {EXCHANGE_INFO_URL}: {e}")
        return

    print(f"Всего найдено {len(futures_pairs)} фьючерсных пар.")

    # Получаем объемы торгов за 24 часа
    try:
        futures_volume_data = requests.get(FUTURES_24HR_URL).json()
        futures_volumes = {item['symbol']: float(item['quoteVolume']) for item in futures_volume_data}
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе данных с {FUTURES_24HR_URL}: {e}")
        return

    # Фильтруем пары с объемом > 100 000 USDT
    filtered_pairs = {symbol for symbol in futures_pairs if futures_volumes.get(symbol, 0) > MIN_FUTURES_VOLUME}
    print(f"Отобрано {len(filtered_pairs)} пар с объемом > {MIN_FUTURES_VOLUME} USDT.")

    # Получаем цены
    try:
        spot_data = requests.get(SPOT_BOOK_TICKER_URL).json()
        futures_data = requests.get(FUTURES_BOOK_TICKER_URL).json()
        mark_price_data = requests.get(MARK_PRICE_URL).json()

        spot_prices = {item['symbol']: float(item['bidPrice']) for item in spot_data}  # Покупка на споте (bid)
        futures_prices = {item['symbol']: float(item['askPrice']) for item in futures_data}  # Продажа на фьючерсе (ask)
        mark_prices = {item['symbol']: float(item['markPrice']) for item in mark_price_data}  # Справедливая цена
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе данных с одного из API: {e}")
        return

    data_list = []

    # Обрабатываем пары
    for symbol in filtered_pairs:
        spot_bid = spot_prices.get(symbol.replace("USDT", "USDT"), None)  # Цена покупки на споте
        futures_ask = futures_prices.get(symbol, None)  # Цена продажи на фьючерсе
        mark_price = mark_prices.get(symbol, None)  # Справедливая цена фьючерса
        volume = futures_volumes.get(symbol, 0)  # Оборот на фьючерсах

        if spot_bid and futures_ask and mark_price and spot_bid > 0:
            spread = ((futures_ask - spot_bid) / spot_bid) * 100
            deviation_from_mark = ((futures_ask - mark_price) / mark_price) * 100
            data_list.append([symbol, spot_bid, futures_ask, mark_price, round(spread, 2), round(deviation_from_mark, 2), volume])

            # Отправка уведомления в Telegram, если спред и отклонение от Mark Price выше порогов
            if spread > SPREAD_THRESHOLD and deviation_from_mark > MARK_PRICE_THRESHOLD:
                message = (f"⚠️ {symbol} - Найдена арбитражная возможность!\n"
                           f"Спот: {spot_bid} USDT\n"
                           f"Фьючерсы: {futures_ask} USDT\n"
                           f"Mark Price: {mark_price} USDT\n"
                           f"📊 Спред: {round(spread, 2)}%\n"
                           f"📈 Отклонение от Mark: {round(deviation_from_mark, 2)}%")
                send_telegram_message(message)

    # Создаем DataFrame
    columns = ["Валютная пара", "Спот покупка", "Фьючерс продажа", "Mark Price", "Спред %", "Отклонение от Mark %", "Объем фьючерсов"]
    df = pd.DataFrame(data_list, columns=columns)

    # Сортируем по спреду
    df = df.sort_values(by="Спред %", ascending=False)

    # Сохраняем в CSV
    csv_filename = "binance_futures_spread.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8')

    print(f"✅ Сканирование завершено. Результаты сохранены в {csv_filename}")

    # --- Отправляем уведомление о завершении проверки ---
    send_telegram_message("✅ Binance завершил сканирование. Жду 10 минут до следующей проверки.")

# --- Бесконечный цикл сканирования ---
#while True:
   # scan_binance()
   # print(f"🔄 Ожидание {SCAN_INTERVAL // 60} минут перед следующим сканированием...\n")
   # time.sleep(SCAN_INTERVAL)  # Ждем 10 минут перед следующим запуском
