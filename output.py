from datetime import datetime

# Считываем данные из файла
with open("signals_output_4.txt", "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# Сортировка по дате и времени
def extract_datetime(line):
    try:
        timestamp_str = line.split('|')[0].strip()
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.max  # Если не удаётся преобразовать — ставим в конец

sorted_lines = sorted(lines, key=extract_datetime)

# Сохраняем в output.txt
with open("output.txt", "w") as f:
    f.write("\n".join(sorted_lines))

print("Сортировка завершена. Данные сохранены в output.txt.")
