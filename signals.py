def main():
    file_path = "signals_results.txt"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Файл signals_results.txt не найден.")
        return

    take_count = 0
    stop_count = 0
    other_count = 0

    for line in lines:
        if "TAKE" in line:
            take_count += 1
        elif "STOP" in line:
            stop_count += 1
        else:
            other_count += 1

    total = take_count + stop_count + other_count

    print(f"\n📊 Результаты анализа сигналов:")
    print(f"✅ TAKE: {take_count}")
    print(f"❌ STOP: {stop_count}")
    if other_count > 0:
        print(f"⏳ Другое (HOLD или неизвестное): {other_count}")
    print(f"📦 Всего сигналов: {total}")

if __name__ == "__main__":
    main()
