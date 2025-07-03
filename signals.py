import asyncio
import aiohttp
import time
from datetime import datetime
from tqdm import tqdm

BASE_URL = "https://fapi.binance.com"

async def fetch(session, url, params=None):
    async with session.get(url, params=params) as response:
        return await response.json()

async def get_symbols(session):
    url = f"{BASE_URL}/fapi/v1/exchangeInfo"
    data = await fetch(session, url)
    return [s['symbol'] for s in data['symbols'] if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT']

async def get_klines(session, symbol, interval="1m", limit=1000, start_time=None, end_time=None):
    url = f"{BASE_URL}/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
    data = await fetch(session, url, params)
    return data

async def fetch_last_month_klines(session, symbol):
    now = int(time.time() * 1000)
    month_ago = now - 30 * 24 * 60 * 60 * 1000
    klines = []
    current = month_ago

    while current < now:
        data = await get_klines(session, symbol, interval="1m", limit=1000, start_time=current)
        if not data:
            break
        klines.extend(data)
        last_time = data[-1][0]
        current = last_time + 60_000
        if current <= last_time:
            break
    return klines

def timestamp_to_date(ts_ms):
    return datetime.utcfromtimestamp(ts_ms / 1000).date()

def analyze_symbol_without_pandas(symbol, klines):
    if not klines:
        return []

    # Группировка по дням
    grouped = {}
    for k in klines:
        dt = timestamp_to_date(k[0])
        if dt not in grouped:
            grouped[dt] = []
        grouped[dt].append(k)

    results = []

    for date_key in grouped:
        candles = grouped[date_key]
        if len(candles) < 2:
            continue

        day_open = float(candles[0][1])
        day_high = max(float(c[2]) for c in candles)

        if day_high >= day_open * 1.10:
            # Нашли рост на 10%
            threshold = day_open * 1.10

            # Находим первую свечу, пробившую +10%
            entry_candle = next((c for c in candles if float(c[2]) >= threshold), None)
            if not entry_candle:
                continue

            entry_time = datetime.utcfromtimestamp(entry_candle[0] / 1000)
            entry_price = threshold
            take_profit = entry_price * 1.10
            stop_loss = entry_price * 0.99

            outcome = "HOLD"
            entry_index = candles.index(entry_candle)

            for c in candles[entry_index + 1:]:
                high = float(c[2])
                low = float(c[3])
                if low <= stop_loss:
                    outcome = "STOP"
                    break
                if high >= take_profit:
                    outcome = "TAKE"
                    break

            results.append({
                "symbol": symbol,
                "date": str(date_key),
                "entry_time": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                "entry_price": round(entry_price, 6),
                "take_profit": round(take_profit, 6),
                "stop_loss": round(stop_loss, 6),
                "outcome": outcome
            })

    return results

async def main():
    async with aiohttp.ClientSession() as session:
        symbols = await get_symbols(session)
        print(f"Найдено {len(symbols)} USDT perpetual символов.")

        all_results = []

        for symbol in tqdm(symbols):
            try:
                klines = await fetch_last_month_klines(session, symbol)
                res = analyze_symbol_without_pandas(symbol, klines)
                all_results.extend(res)
            except Exception as e:
                print(f"Ошибка с {symbol}: {e}")

        if all_results:
            with open("signals_results.txt", "w", encoding="utf-8") as f:
                for r in all_results:
                    line = (
                        f"{r['date']} | {r['symbol']} | Entry: {r['entry_time']} | "
                        f"Price: {r['entry_price']} | TP: {r['take_profit']} | "
                        f"SL: {r['stop_loss']} | Outcome: {r['outcome']}\n"
                    )
                    f.write(line)
                    print(line, end='')
        else:
            print("Сигналы не найдены.")

if __name__ == "__main__":
    asyncio.run(main())
