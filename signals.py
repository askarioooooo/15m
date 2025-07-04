

import asyncio

import aiohttp

import time

from datetime import datetime, timedelta

import pandas as pd

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

def analyze_candles(symbol, klines):

df = pd.DataFrame(klines, columns=[

"open_time", "open", "high", "low", "close", "volume",  

"close_time", "quote_asset_volume", "number_of_trades",  

"taker_buy_base_volume", "taker_buy_quote_volume", "ignore"

])

df["open"] = df["open"].astype(float)

df["close"] = df["close"].astype(float)

df["high"] = df["high"].astype(float)

df["low"] = df["low"].astype(float)

df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')

results = []

i = 0

n = len(df)

while i < n - 1:

open_price = df.iloc[i]["open"]  

close_price = df.iloc[i]["close"]  

change = (close_price - open_price) / open_price * 100  



if abs(change) >= 7:  

    direction = "LONG" if change > 0 else "SHORT"  

    entry_price = close_price  



    tp = entry_price * (1 - 0.05) if direction == "LONG" else entry_price * (1 + 0.05)  

    sl = entry_price * (1 + 0.007) if direction == "LONG" else entry_price * (1 - 0.007)  



    outcome = "NONE"  

    exit_index = None  



    for j in range(i + 1, n):  

        row = df.iloc[j]  

        high = row["high"]  

        low = row["low"]  



        if direction == "LONG":  

            if high >= sl:  

                outcome = "STOP"  

                exit_index = j  

                break  

            elif low <= tp:  

                outcome = "TAKE"  

                exit_index = j  

                break  

        else:  # SHORT  

            if low <= sl:  

                outcome = "STOP"  

                exit_index = j  

                break  

            elif high >= tp:  

                outcome = "TAKE"  

                exit_index = j  

                break  

              



    if outcome in ["TAKE", "STOP"]:  

        results.append({  

            "symbol": symbol,  

            "time": df.iloc[i]["open_time"],  

            "direction": direction,  

            "change": round(change, 2),  

            "outcome": outcome  

        })  

        i = exit_index + 1 if exit_index is not None else i + 1  

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

        output_lines.append(f"{r['time']} | {r['symbol']} | {r['direction']} | {r['change']}% -> {r['outcome']}")  



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

if name == "main":

asyncio.run(main())

