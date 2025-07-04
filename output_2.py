from datetime import datetime

# Чтение из предыдущего результата
with open("output.txt", "r") as f:
    lines = f.read().strip().split('\n')

seen_timestamps = set()
last_pair = None
final_lines = []

for line in lines:
    try:
        parts = line.split('|')
        timestamp = parts[0].strip()
        pair = parts[1].strip()

        # Пропустить, если уже есть сделка в это время
        if timestamp in seen_timestamps:
            continue

        # Пропустить, если такая же пара была в предыдущей строке
        if pair == last_pair:
            continue

        final_lines.append(line)
        seen_timestamps.add(timestamp)
        last_pair = pair
    except:
        continue

# Сохраняем результат
with open("output.txt", "w") as f:
    f.write('\n'.join(final_lines))
