from datetime import datetime

# Чтение исходных данных
with open("signals_output_4.txt", "r") as f:
    lines = f.read().strip().split('\n')

filtered = []

for line in lines:
    try:
        parts = line.split('|')
        timestamp = datetime.strptime(parts[0].strip(), "%Y-%m-%d %H:%M:%S")
        pair = parts[1].strip()
        direction = parts[2].strip()
        percent_str = parts[3].strip().replace('%', '').replace('+', '')
        percent = float(percent_str)

        if direction == 'SHORT' and abs(percent) >= 7.0:
            filtered.append((timestamp, line))
    except:
        continue  # Пропускаем некорректные строки

# Сортировка по дате и времени
filtered.sort(key=lambda x: x[0])

# Сохраняем результат
with open("output.txt", "w") as f:
    f.write('\n'.join([line for _, line in filtered]))
