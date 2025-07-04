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
    return [
        s['symbol']
        for s in data['symbols']
        if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT'
    ]

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

async def fetch_last_3_days_klines(session, symbol):
    now = int(time.time() * 1000)
    three_days_ago = now - 30 * 24 * 60 * 60 * 1000  # 3 дня в миллисекундах
    klines = []
    current = three_days_ago

    while current < now:
        data = await get_klines(session, symbol, start_time=current, limit=1000)
        if not data:
            break
        klines.extend(data)
        current = data[-1][0] + 60_000  # 1 минута вперёд
    return klines

def analyze_candles(symbol, klines):
    results = []
    n = len(klines)
    i = 0

    while i < n - 2:  # оставляем 2 свечи: сигнальную и свечу ожидания
        candle = klines[i]
        open_time = candle[0]
        open_price = float(candle[1])
        close_price = float(candle[4])
        change = (close_price - open_price) / open_price * 100

        if abs(change) >= 7:
            direction = "SHORT" if change > 0 else "LONG"

            sl = close_price * 1.007 if direction == "SHORT" else close_price * 0.993
            tp = None  # посчитаем позже от entry

            # Ждём 1 свечу
            next_candle = klines[i + 1]
            high = float(next_candle[2])
            low = float(next_candle[3])
            wait_close = float(next_candle[4])
            wait_time = next_candle[0]

            # Проверяем: не задет ли SL или TP за эту 1 минуту
            sl_hit = (high >= sl) if direction == "SHORT" else (low <= sl)
            if sl_hit:
                i += 1
                continue  # сигнал отменяется

            # Открываем сделку
            entry = wait_close
            tp = entry * 0.95 if direction == "SHORT" else entry * 1.05

            # Размер стопа в процентах
            sl_pct = (sl - entry) / entry * 100 if direction == "SHORT" else (entry - sl) / entry * 100

            # Мониторим дальнейшие свечи
            outcome = "NONE"
            for j in range(i + 2, n):
                future = klines[j]
                future_high = float(future[2])
                future_low = float(future[3])

                if direction == "SHORT":
                    if future_low <= tp:
                        outcome = "TAKE"
                        break
                    elif future_high >= sl:
                        outcome = "STOP"
                        break
                else:  # LONG
                    if future_high >= tp:
                        outcome = "TAKE"
                        break
                    elif future_low <= sl:
                        outcome = "STOP"
                        break

            if outcome != "NONE":
                results.append({
                    "symbol": symbol,
                    "time": datetime.utcfromtimestamp(wait_time / 1000).strftime("%Y-%m-%d %H:%M"),
                    "direction": direction,
                    "entry": round(entry, 4),
                    "tp": round(tp, 4),
                    "sl": round(sl, 4),
                    "sl_pct": round(sl_pct, 2),
                    "outcome": outcome
                })
                i = j + 1
            else:
                i += 1
        else:
            i += 1

    return results

async def main():
    async with aiohttp.ClientSession() as session:
        symbols = await get_symbols(session)
        output_lines = []
        output_lines.append(f"Found {len(symbols)} symbols. Starting analysis...\n")

        all_results = []

        for symbol in tqdm(symbols):
            try:
                klines = await fetch_last_3_days_klines(session, symbol)
                result = analyze_candles(symbol, klines)
                if result:
                    all_results.extend(result)
            except Exception as e:
                output_lines.append(f"Error for {symbol}: {e}")
                continue

        if all_results:
            output_lines.append("\nMatching signals found:\n")
            for r in all_results:
                output_lines.append(
                                  f"{r['time']} | {r['symbol']} | {r['direction']} | Entry: {r['entry']} | "
                                  f"TP: {r['tp']} (+5%) | SL: {r['sl']} ({'-' if r['direction'] == 'SHORT' else ''}{r['sl_pct']}%) | "
                                  f"Outcome: {r['outcome']}"
                )

            # Подсчёт итогов
            take_count = sum(1 for r in all_results if r['outcome'] == 'TAKE')
            stop_count = sum(1 for r in all_results if r['outcome'] == 'STOP')
            be_count = sum(1 for r in all_results if r['outcome'] == 'BE')

            output_lines.append(f"\nSummary:")
            output_lines.append(f"TAKE: {take_count}")
            output_lines.append(f"STOP: {stop_count}")
            output_lines.append(f"BE:   {be_count}")
            output_lines.append(f"TOTAL: {len(all_results)} signals")
        else:
            output_lines.append("\nNo matching signals found.")

        # Save to file
        with open("signals_output_4.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))

if __name__ == "__main__":
    asyncio.run(main())
