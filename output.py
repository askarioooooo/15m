from datetime import datetime

# Чтение исходных строк из файла
with open("signals_output_4.txt", "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# Фильтруем строки, у которых корректный формат даты
valid_lines = []
for line in lines:
    try:
        timestamp_str = line.split('|')[0].strip()
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
        valid_lines.append((timestamp, line))
    except Exception:
        continue  # Пропускаем строки без корректного времени

# Сортируем по времени
sorted_lines = sorted(valid_lines, key=lambda x: x[0])

# Извлекаем только текст
sorted_text_lines = [line for _, line in sorted_lines]

# Сохраняем в output.txt
with open("output.txt", "w") as f:
    f.write("\n".join(sorted_text_lines))

print("✅ Все строки отсортированы по дате и времени и записаны в output.txt.")
