import json

# Файлы
# JSON_FILE = "/home/anya2812/Migration-Model/wood_thrush/grid_abundance_normalized.json"
# GRID_FILE = "wood_thrush/grid_data.json"
#
JSON_FILE = "/home/anya2812/Migration-Model/amewoo/grid_abundance_normalized.json"
GRID_FILE = "amewoo/grid_data.json"


# excluded_coordinates = {(43.5, -88.5), (37.5, -78.5), (41.5, -68.5)}
excluded_coordinates = {}


def get_grid_cell(lat, lon):
    grid_lat = int(lat)
    if grid_lat == 12:
        print(lat, lon, "LALALALLALALLA")
    grid_lon = int(lon)
    return (grid_lat, grid_lon)


def build_fixed_grid():
    grid_cells = {}

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        points = json.load(f)

    for point in points:
        lat, lon, season, abundance = point["latitude"], point["longitude"], point["season"], point["abundance"]
        grid_cell = get_grid_cell(lat, lon)

        if grid_cell in excluded_coordinates:
            season = "breeding"

        if grid_cell not in grid_cells:
            grid_cells[grid_cell] = {
                "wintering": {"count": 0, "abundance": []},
                "breeding": {"count": 0, "abundance": []},
                "migration": {"count": 0}
            }

        grid_cells[grid_cell][season]["count"] += 1

        if season in ["wintering", "breeding"] and abundance is not None:
            grid_cells[grid_cell][season]["abundance"].append(abundance)

    grid_result = []
    for (lat, lon), counts in grid_cells.items():
        season_counts = {
            "wintering": counts["wintering"]["count"],
            "breeding": counts["breeding"]["count"],
            "migration": counts["migration"]["count"]
        }
        majority_season = max(season_counts, key=season_counts.get)

        if majority_season == "migration":
            if counts["breeding"]["count"] > 0:
                majority_season = "breeding"
            elif counts["wintering"]["count"] > 0:
                majority_season = "wintering"

        if majority_season == "wintering":
            abundance_list = counts["wintering"]["abundance"]
            abundance_value = sum(abundance_list)  if abundance_list else 0
        elif majority_season == "breeding":
            abundance_list = counts["breeding"]["abundance"]
            abundance_value = sum(abundance_list) if abundance_list else 0
        else:
            abundance_value = 0

        if abundance_value > 0:
            if lat + 0.5 == 12.5:
                print("LLALALLALA", lat, lon)
            grid_result.append({
                "latitude": lat + 0.5,
                "longitude": lon + 0.5,
                "season": majority_season,
                "breeding_count": counts["breeding"]["count"],
                "wintering_count": counts["wintering"]["count"],
                "migration_count": counts["migration"]["count"],
                "abundance": abundance_value
            })


            print(f"Клетка: ({lat + 0.5}, {lon + 0.5})")
            print(f"  Количество точек wintering: {counts['wintering']['count']}")
            print(f"  Количество точек breeding: {counts['breeding']['count']}")
            print(f"  Количество точек migration: {counts['migration']['count']}")
            print(f"  Средняя плотность: {abundance_value}")
            print("-" * 40)

    with open(GRID_FILE, "w", encoding="utf-8") as f:
        json.dump(grid_result, f, ensure_ascii=False, indent=4)

    print(f"✅ Фиксированная сетка построена ({len(grid_result)} клеток) и сохранена в {GRID_FILE}")


# Запуск
if __name__ == "__main__":
    build_fixed_grid()
