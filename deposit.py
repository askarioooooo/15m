from datetime import datetime, timedelta

# Чтение из output.txt
with open("output.txt", "r") as f:
    lines = [line.strip() for line in f if line.strip()]

deposit_start = 3.0  # Начальный депозит

def simulate(stop_streak_limit, ignore_days_after_stop):
    deposit = deposit_start
    stop_streak = 0
    ignore_until = None

    for line in lines:
        timestamp_str = line.split('|')[0].strip()
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue  # Пропустить некорректную строку

        # Пропустить сделку, если попадает в период блокировки
        if ignore_until and timestamp < ignore_until:
            continue

        base = 0.8 * deposit
        reserve = 0.2 * deposit

        if 'TAKE' in line:
            profit = base * 1
            base += profit
            stop_streak = 0
        elif 'STOP' in line:
            loss = base * 0.25
            base -= loss
            stop_streak += 1

            if stop_streak_limit > 0 and stop_streak >= stop_streak_limit:
                ignore_until = timestamp + timedelta(days=ignore_days_after_stop)
                stop_streak = 0
        else:
            stop_streak = 0

        deposit = base + reserve
        if deposit < 3:
            deposit = 3

    return deposit

results = []
for stop_limit in range(0, 6):  # от 0 до 5 подряд стопов
    for days_block in range(0, 21):  # от 0 до 20 дней блокировки
        if stop_limit == 0 and days_block > 0:
            continue  # нет смысла блокировать без условия

        final = simulate(stop_limit, days_block)
        if stop_limit == 0:
            label = "Без блокировки вообще"
        else:
            label = f"После {stop_limit} STOP'ов подряд → блок {days_block} дн."

        results.append(f"{label} → Итоговый депозит: {final:.4f}")

# Сохраняем
with open("deposit_variants.txt", "w") as f:
    f.write("\n".join(results))

# Вывод в консоль
print("\n".join(results))
