import json

# Файлы
JSON_FILE = "/home/anya2812/Migration-Model/grid_abundance_normalized.json"  # Входные данные
GRID_FILE = "grid_data.json"  # Выходные данные


# Исключенные клетки (в этих клетках будем менять зимовку на гнездование)
excluded_coordinates = {(43.5, -88.5), (37.5, -78.5), (41.5, -68.5)}  # Пример: исключаем определенные клетки

# Функция для привязки точки к фиксированной сетке 1×1 градус
def get_grid_cell(lat, lon):
    grid_lat = int(lat)  # Округляем вниз
    grid_lon = int(lon)
    return (grid_lat, grid_lon)


# Функция для построения сетки и расчета плотности
def build_fixed_grid():
    grid_cells = {}  # Обычный словарь

    # Читаем входные данные
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        points = json.load(f)

    # Заполняем сетку данными
    for point in points:
        lat, lon, season, abundance = point["latitude"], point["longitude"], point["season"], point["abundance"]
        grid_cell = get_grid_cell(lat, lon)

        # Если клетка в исключенных, меняем ее сезон на "breeding"
        if grid_cell in excluded_coordinates:
            season = "breeding"  # Изменяем сезон на гнездование

        # Если клетки нет в словаре, создаем ее
        if grid_cell not in grid_cells:
            grid_cells[grid_cell] = {
                "wintering": {"count": 0, "abundance": []},
                "breeding": {"count": 0, "abundance": []},
                "migration": {"count": 0}
            }

        # Увеличиваем счетчик для соответствующего сезона
        grid_cells[grid_cell][season]["count"] += 1

        # Добавляем abundance в список (только для wintering и breeding), **но игнорируем None**
        if season in ["wintering", "breeding"] and abundance is not None:
            grid_cells[grid_cell][season]["abundance"].append(abundance)

    # Обрабатываем данные и формируем список клеток
    grid_result = []
    for (lat, lon), counts in grid_cells.items():
        # Определяем доминирующий сезон
        season_counts = {
            "wintering": counts["wintering"]["count"],
            "breeding": counts["breeding"]["count"],
            "migration": counts["migration"]["count"]
        }
        majority_season = max(season_counts, key=season_counts.get)

        # Если миграция доминирует, но есть хотя бы одно наблюдение wintering или breeding → выбираем его
        if majority_season == "migration":
            if counts["breeding"]["count"] > 0:
                majority_season = "breeding"
            elif counts["wintering"]["count"] > 0:
                majority_season = "wintering"

        # Вычисляем плотность в зависимости от доминирующего сезона
        if majority_season == "wintering":
            abundance_list = counts["wintering"]["abundance"]
            abundance_value = sum(abundance_list) / len(abundance_list) if abundance_list else 0
        elif majority_season == "breeding":
            abundance_list = counts["breeding"]["abundance"]
            abundance_value = sum(abundance_list) if abundance_list else 0
        else:  # migration без других наблюдений
            abundance_value = 0

        # Добавляем клетку в результат, только если плотность больше нуля
        if abundance_value > 0:
            grid_result.append({
                "latitude": lat + 0.5,  # Центр клетки
                "longitude": lon + 0.5,
                "season": majority_season,
                "breeding_count": counts["breeding"]["count"],
                "wintering_count": counts["wintering"]["count"],
                "migration_count": counts["migration"]["count"],
                "abundance": abundance_value
            })

            # Вывод информации о клетке
            print(f"Клетка: ({lat + 0.5}, {lon + 0.5})")
            print(f"  Количество точек wintering: {counts['wintering']['count']}")
            print(f"  Количество точек breeding: {counts['breeding']['count']}")
            print(f"  Количество точек migration: {counts['migration']['count']}")
            print(f"  Средняя плотность: {abundance_value}")
            print("-" * 40)

    # Сохраняем результат в JSON
    with open(GRID_FILE, "w", encoding="utf-8") as f:
        json.dump(grid_result, f, ensure_ascii=False, indent=4)

    print(f"✅ Фиксированная сетка построена ({len(grid_result)} клеток) и сохранена в {GRID_FILE}")


# Запуск
if __name__ == "__main__":
    build_fixed_grid()
