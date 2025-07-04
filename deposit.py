from datetime import datetime, timedelta

# Настройки
START_DEPOSIT = 1
TAKE_PROFIT = 0.03
STOP_LOSS = -0.01

# Загрузка сделок
with open("filtered_output.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Преобразование сделок в список словарей
trades = []
for line in lines:
    try:
        dt_str, symbol, direction, *_rest, outcome_part = line.strip().split('|')
        dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M")
        direction = direction.strip()
        outcome = outcome_part.strip().split(":")[-1].strip()
        trades.append({"datetime": dt, "direction": direction, "outcome": outcome})
    except Exception as e:
        print(f"Ошибка разбора строки: {line}\n{e}")

# Сортировка по дате
trades.sort(key=lambda x: x["datetime"])

# Параметры перебора
max_consecutive_stops_range = range(0, 6)
block_days_range = range(0, 11)
directions_variants = {
    "ALL": lambda d: True,
    "LONG_ONLY": lambda d: d == "LONG",
    "SHORT_ONLY": lambda d: d == "SHORT"
}

# Функция симуляции
def simulate(trades, max_stops, block_days, direction_filter):
    deposit = START_DEPOSIT
    last_block_time = None
    consecutive_stops = 0

    for trade in trades:
        if not direction_filter(trade["direction"]):
            continue

        # Пропустить сделки в блоке
        if last_block_time and trade["datetime"] < last_block_time:
            continue

        # Применение исхода сделки
        if trade["outcome"] == "TAKE":
            deposit *= (1 + TAKE_PROFIT)
            consecutive_stops = 0
        elif trade["outcome"] == "STOP":
            deposit *= (1 + STOP_LOSS)
            consecutive_stops += 1

            # Если достигли лимита стопов — блокируем
            if consecutive_stops >= max_stops:
                last_block_time = trade["datetime"] + timedelta(days=block_days)
                consecutive_stops = 0

    return round(deposit, 2)

# Сохранение результатов
with open("deposit_variants.txt", "w", encoding="utf-8") as f_out:
    for dir_label, filter_func in directions_variants.items():
        f_out.write(f"=== {dir_label} ===\n")
        for max_stops in max_consecutive_stops_range:
            for block_days in block_days_range:
                final_deposit = simulate(trades, max_stops, block_days, filter_func)
                f_out.write(
                    f"Stops before block: {max_stops}, Block days: {block_days} => Final deposit: {final_deposit}\n"
                )
        f_out.write("\n")
