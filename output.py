from datetime import datetime

# Чтение исходных данных
with open("signals_output_4.txt", "r", encoding="utf-8") as f:
    lines = f.read().strip().split('\n')

filtered = []

for line in lines:
    try:
        parts = line.split('|')
        timestamp_str = parts[0].strip()
        pair = parts[1].strip()
        direction = parts[2].strip()
        percent_raw = parts[3].strip().split()[0]  # "-7.88%" part before "->"
        percent = float(percent_raw.replace('%', '').replace('+', ''))

        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        if direction == 'SHORT' and abs(percent) >= 7.0:
            filtered.append((timestamp, line))

    except Exception as e:
        print(f"Ошибка обработки строки: {line}\nПричина: {e}")
        continue

# Сортировка по дате и времени
filtered.sort(key=lambda x: x[0])

# Сохраняем результат
with open("output.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join([line for _, line in filtered]))
