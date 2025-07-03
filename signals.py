import asyncio
import aiohttp
import time
from datetime import datetime
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

def analyze_symbol_daily(symbol, klines_1m):
    df = pd.DataFrame(klines_1m, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    
    df['date'] = df['open_time'].dt.date
    
    results = []
    grouped = df.groupby('date')
    
    for day, group in grouped:
        day_open = group.iloc[0]['open']
        day_high = group['high'].max()
        
        if day_high >= day_open * 1.10:
            threshold = day_open * 1.10
            entry_row = group[group['high'] >= threshold].iloc[0]
            entry_price = threshold
            
            take_profit = entry_price * 1.10
            stop_loss = entry_price * 0.99
            
            after_entry = group[group['open_time'] > entry_row['open_time']]
            
            outcome = "HOLD"
            for _, row in after_entry.iterrows():
                if row['low'] <= stop_loss:
                    outcome = "STOP"
                    break
                if row['high'] >= take_profit:
                    outcome = "TAKE"
                    break
            
            results.append({
                "symbol": symbol,
                "date": day,
                "entry_time": entry_row['open_time'],
                "entry_price": round(entry_price, 6),
                "take_profit": round(take_profit, 6),
                "stop_loss": round(stop_loss, 6),
                "outcome": outcome
            })
    return results

async def main():
    async with aiohttp.ClientSession() as session:
        symbols = await get_symbols(session)
        print(f"Found {len(symbols)} USDT perpetual symbols.")
        
        all_results = []
        
        for symbol in tqdm(symbols):
            try:
                klines = await fetch_last_month_klines(session, symbol)
                if klines:
                    res = analyze_symbol_daily(symbol, klines)
                    if res:
                        all_results.extend(res)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        
        if all_results:
            print(f"\nSignals found: {len(all_results)}")
            with open("signals_results.txt", "w", encoding="utf-8") as f:
                for r in all_results:
                    line = (
                        f"{r['date']} | {r['symbol']} | Entry: {r['entry_time']} | "
                        f"Entry Price: {r['entry_price']} | TP: {r['take_profit']} | SL: {r['stop_loss']} | Outcome: {r['outcome']}\n"
                    )
                    f.write(line)
                    print(line, end='')
        else:
            print("No signals found.")

if __name__ == "__main__":
    asyncio.run(main())
