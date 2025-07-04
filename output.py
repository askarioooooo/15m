from datetime import datetime

# Считываем строки из файла
with open("signals_output_4.txt", "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# Функция извлечения даты и времени
def extract_datetime(line):
    try:
        timestamp_str = line.split('|')[0].strip()
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
    except Exception:
        return datetime.max  # Некорректная дата — в конец списка

# Сортировка по дате и времени
sorted_lines = sorted(lines, key=extract_datetime)

# Сохраняем результат в output.txt
with open("output.txt", "w") as f:
    f.write("\n".join(sorted_lines))

print("✅ Сортировка завершена. Результат записан в output.txt.")
