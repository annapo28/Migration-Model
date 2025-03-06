# Мы импорнули данные из базового датасета, прочитали их, прочитали код региона.
# Потом прочитали коды региона из таблицы распределений и присвоили каждой клетке долю популяции
# Получили все клетки
# Посчитали пути между парами клеток и сделали тройки

import json
import csv
from datetime import datetime
from collections import defaultdict
import math

TXT_FILE = "/home/anya2812/Загрузки/ebd_woothr_201612_202412_smp_relDec-2024/ebd_woothr_201612_202412_smp_relDec-2024.txt"
GRID_FILE = "grid_data.json"
DENSITY_FILE = "/home/anya2812/Загрузки/woothr_regional_2022.csv"
OUTPUT_TRIPLE_FILE = "migration_routes.json"
OUTPUT_SORTED_TRIPLE_JSON = "sorted_migration_routes.json"

def sort_migration_routes(routes):
    """
        Сортируем маршруты по расстоянию, затем по широте точки вылета.
    """
    return sorted(routes, key=lambda r: (r[2][0], r[0][0]))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_season(event_date):
    """
        Определяет сезон на основе даты наблюдения.
    """
    try:
        date = datetime.strptime(event_date, "%Y-%m-%d")
        month, day = date.month, date.day
        if (month == 5 and day >= 31) or month in [6, 7] or (month == 8 and day <= 23):
            return "breeding"
        elif (month == 11 and day >= 22) or month in [12, 1] or (month == 3 and day <= 8):
            return "wintering"
        return "migration"
    except ValueError:
        return "unknown"


def get_grid_cell(lat, lon):
    """
        Привязывает координаты к фиксированной сетке 1×1 градус.
    """
    return int(lat), int(lon)


def load_density_data():
    """
        Загружает данные плотности из CSV.
    """
    densities = {}
    with open(DENSITY_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region_code = row["region_code"]
            region_code = region_code.replace("USA-", "").replace("US-", "")
            densities[region_code] = float(row["abundance_mean"])
    return densities

def normalize_region_code(region_code):
    """
        Приводит код региона к единому формату.
    """
    region_code = region_code.replace("USA-", "").replace("US-", "")
    region_code = region_code.replace("MX-CAM", "MEX-CM")
    region_code = region_code.replace("MX-ROO", "MEX-QR")
    region_code = region_code.replace("MX-TAB", "MEX-TB")
    region_code = region_code.replace("MX-CHP", "MEX-CS")
    region_code = region_code.replace("MX-OAX", "MEX")
    region_code = region_code.replace("MX-PUE", "MEX")
    if region_code.startswith("CA-"):
        return "CAN"

    if region_code.startswith("BZ-"):
        return "BLZ"

    if region_code.startswith("GT-"):
        return "GTM"

    return region_code


def process_data():
    """
        Обрабатывает TXT-файл, фильтрует данные за 2017 год и строит сетку с регионами.
    """
    unique_region_codes = set()  # Множество для хранения уникальных region_code

    with open(TXT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    headers = lines[0].strip().split("\t")
    lat_index = headers.index("LATITUDE")
    lon_index = headers.index("LONGITUDE")
    date_index = headers.index("OBSERVATION DATE")
    state_index = headers.index("STATE CODE")
    country_index = headers.index("COUNTRY CODE")

    grid_cells = defaultdict(lambda: {"breeding": 0, "wintering": 0, "migration": 0, "region_code": None})
    region_counts = defaultdict(lambda: {"breeding": 0, "wintering": 0, "migration": 0})
    for line in lines[1:]:
        columns = line.strip().split("\t")
        latitude, longitude, event_date = columns[lat_index], columns[lon_index], columns[date_index]
        state_code, country_code = columns[state_index], columns[country_index]
        if not latitude or not longitude or not event_date:
            continue
        if event_date.startswith("2017"):
            season = get_season(event_date)
            grid_cell = get_grid_cell(float(latitude), float(longitude))
            region_code = state_code if state_code else country_code
            region_code = normalize_region_code(state_code if state_code else country_code)
            grid_cells[grid_cell][season] += 1
            grid_cells[grid_cell]["region_code"] = region_code
            region_counts[region_code][season] += 1
            if region_code:
                unique_region_codes.add(region_code)
    densities = load_density_data()
    grid_result = []
    for (lat, lon), counts in grid_cells.items():
        if counts["wintering"] > 0:
            majority_season = "wintering"
        elif counts["breeding"] > 0:
            majority_season = "breeding"
        else:
            majority_season = "migration"
        grid_result.append({
            "latitude": lat + 0.5,
            "longitude": lon + 0.5,
            "breeding_count": counts["breeding"],
            "wintering_count": counts["wintering"],
            "migration_count": counts["migration"],
            "region_code": counts["region_code"],
            "density": densities.get(counts["region_code"], 0),
            "season": majority_season
        })
    with open(GRID_FILE, "w", encoding="utf-8") as f:
        json.dump(grid_result, f, ensure_ascii=False, indent=4)
    print(f"Уникальные region_code: {sorted(unique_region_codes)}")
    print(f"Фиксированная сетка построена ({len(grid_result)} клеток) и сохранена в {GRID_FILE}")

def building_triples():
    with open(GRID_FILE, "r", encoding="utf-8") as f:
        grid_data = json.load(f)
    breeding_cells = [cell for cell in grid_data if cell["season"] == "breeding"]
    wintering_cells = [cell for cell in grid_data if cell["season"] == "wintering"]
    migration_routes = []
    for b_cell in breeding_cells:
        for w_cell in wintering_cells:
            L = haversine(b_cell["latitude"], b_cell["longitude"], w_cell["latitude"], w_cell["longitude"])
            u = b_cell["density"]
            w = w_cell["density"]
            route = ((w_cell["latitude"], w_cell["longitude"]),
                     (b_cell["latitude"], b_cell["longitude"]),
                     (L, u, w))
            migration_routes.append(route)
    with open(OUTPUT_TRIPLE_FILE, "w", encoding="utf-8") as f:
        json.dump(migration_routes, f, ensure_ascii=False, indent=4)
    sorted_routes = sort_migration_routes(migration_routes)
    with open(OUTPUT_SORTED_TRIPLE_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_routes, f, ensure_ascii=False, indent=4)
    print(f"Файл с маршрутами миграции сохранен: {OUTPUT_SORTED_TRIPLE_JSON}")

if __name__ == "__main__":
    process_data()
    building_triples()


