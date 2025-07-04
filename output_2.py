# Удаление повторяющихся сделок по точному времени (дата + время)
seen_times = set()
filtered_lines = []

with open('output.txt', 'r', encoding='utf-8') as infile:
    for line in infile:
        # Извлекаем дату и время из начала строки (первые 16 символов)
        timestamp = line[:16]
        if timestamp not in seen_times:
            seen_times.add(timestamp)
            filtered_lines.append(line)

# Сохраняем результат
with open('filtered_output.txt', 'w', encoding='utf-8') as outfile:
    outfile.writelines(filtered_lines)
