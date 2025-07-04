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
    three_days_ago = now - 30 * 24 * 60 * 60 * 1000
    klines = []
    current = three_days_ago

    while current < now:
        data = await get_klines(session, symbol, start_time=current, limit=1000)
        if not data:
            break
        klines.extend(data)
        current = data[-1][0] + 60_000
    return klines

def analyze_candles(symbol, klines, tp_percent):
    results = []
    n = len(klines)
    i = 0

    while i < n - 1:
        candle = klines[i]
        open_time = candle[0]
        open_price = float(candle[1])
        close_price = float(candle[4])
        change = (close_price - open_price) / open_price * 100

        if abs(change) >= 4:
            direction = "SHORT" if change > 0 else "LONG"
            entry = close_price

            if direction == "SHORT":
                tp = entry * (1 - tp_percent / 100)
                sl = entry * 1.01
            else:
                tp = entry * (1 + tp_percent / 100)
                sl = entry * 0.99

            outcome = "NONE"

            for j in range(i + 1, n):
                future = klines[j]
                high = float(future[2])
                low = float(future[3])

                if direction == "SHORT":
                    if high >= sl:
                        outcome = "STOP"
                        break
                    elif low <= tp:
                        outcome = "TAKE"
                        break
                else:
                    if low <= sl:
                        outcome = "STOP"
                        break
                    elif high >= tp:
                        outcome = "TAKE"
                        break

            if outcome != "NONE":
                results.append({
                    "symbol": symbol,
                    "time": datetime.utcfromtimestamp(open_time / 1000).strftime("%Y-%m-%d %H:%M"),
                    "direction": direction,
                    "entry": round(entry, 4),
                    "tp": round(tp, 4),
                    "sl": round(sl, 4),
                    "sl_pct": round(abs(sl - entry) / entry * 100, 2),
                    "candle_change": round(change, 2),
                    "outcome": outcome,
                    "tp_pct": tp_percent
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
        tp_levels = [3, 5, 7.5, 10]
        all_results_by_tp = {tp: [] for tp in tp_levels}

        for symbol in tqdm(symbols):
            try:
                klines = await fetch_last_3_days_klines(session, symbol)
                for tp in tp_levels:
                    results = analyze_candles(symbol, klines, tp_percent=tp)
                    if results:
                        all_results_by_tp[tp].extend(results)
            except Exception as e:
                print(f"Error for {symbol}: {e}")
                continue

        for tp in tp_levels:
            results = all_results_by_tp[tp]
            filename = f"signals_tp{str(tp).replace('.', '_')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Strategy: TP {tp}%, SL 1%\n")
                f.write(f"Total signals: {len(results)}\n\n")

                take_count = sum(1 for r in results if r['outcome'] == "TAKE")
                stop_count = sum(1 for r in results if r['outcome'] == "STOP")

                for r in results:
                    f.write(
                        f"{r['time']} | {r['symbol']} | {r['direction']} | Entry: {r['entry']} | "
                        f"TP: {r['tp']} (+{tp}%) | SL: {r['sl']} (-{r['sl_pct']}%) | "
                        f"Candle: {r['candle_change']}% | Outcome: {r['outcome']}\n"
                    )

                f.write("\nSummary:\n")
                f.write(f"TAKE: {take_count}\n")
                f.write(f"STOP: {stop_count}\n")

if __name__ == "__main__":
    asyncio.run(main())
                
