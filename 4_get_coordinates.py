import json
import math
from collections import defaultdict

GRID_FILE = "amewoo/grid_data.json"
OUTPUT_TRIPLE_FILE = "amewoo/migration_routes.json"
OUTPUT_TRIPLE_FILE_FALL = "amewoo/migration_routes_fall.json"
OUTPUT_SORTED_TRIPLE_JSON = "amewoo/sorted_migration_routes.json"
OUTPUT_SORTED_TRIPLE_JSON_FALL = "amewoo/sorted_migration_routes_fall.json"

# excluded_coordinates = {(43.5, -88.5), (37.5, -78.5), (41.5, -69.5)}
excluded_coordinates = {}

def haversine(lat1, lon1, lat2, lon2):
    """ Рассчитывает расстояние между двумя точками (км) """
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def sort_migration_routes(routes):
    """ Сортируем маршруты по расстоянию, затем по широте точки прилёта и добавляем n_k и номер маршрута в группе. """
    # Сначала сортируем маршруты по L_k, затем по широте точки прилёта (route[1][0])
    sorted_routes = sorted(routes, key=lambda r: (r[2][0], r[1][0]))

    # Группируем маршруты по (lat_j, lon_j, L_k)
    groups = defaultdict(list)
    for route in sorted_routes:
        lat_j, lon_j = route[1]  # Точка прибытия
        L_k = route[2][0]  # Расстояние
        groups[(lat_j, lon_j, L_k)].append(route)

    result = []
    for group_key, group_routes in groups.items():
        n_k = len(group_routes)
        for idx, route in enumerate(group_routes, start=1):  # Нумерация маршрутов в группе от 1 до n_k
            new_route = (route[0], route[1], (route[2][0], route[2][1], route[2][2], n_k, idx))
            result.append(new_route)

    return result


def building_triples():
    """ Создает маршруты миграции, используя нормализованные данные из grid_data.json. """
    with open(GRID_FILE, "r", encoding="utf-8") as f:
        grid_data = json.load(f)

    breeding_cells = [cell for cell in grid_data if cell["season"] == "breeding"]
    wintering_cells = [cell for cell in grid_data if cell["season"] == "wintering"]

    migration_routes_spring = []
    migration_routes_autumn = []

    for b_cell in breeding_cells:
        b_lat, b_lon = round(b_cell["latitude"], 1), round(b_cell["longitude"], 1)
        u = b_cell["abundance"]  # Берем плотность для гнездования

        for w_cell in wintering_cells:
            w_lat, w_lon = round(w_cell["latitude"], 1), round(w_cell["longitude"], 1)
            w = w_cell["abundance"]  # Берем плотность для зимовки

            L = haversine(b_lat, b_lon, w_lat, w_lon)

            autumn_route = ((b_lat, b_lon), (w_lat, w_lon), (L, u, w))
            spring_route = ((w_lat, w_lon), (b_lat, b_lon), (L, w, u))

            migration_routes_spring.append(spring_route)
            migration_routes_autumn.append(autumn_route)

    with open(OUTPUT_TRIPLE_FILE, "w", encoding="utf-8") as f:
        json.dump(migration_routes_spring, f, ensure_ascii=False, indent=4)

    with open(OUTPUT_TRIPLE_FILE_FALL, "w", encoding="utf-8") as f:
        json.dump(migration_routes_autumn, f, ensure_ascii=False, indent=4)

    sorted_routes_spring = sort_migration_routes(migration_routes_spring)
    sorted_routes_autumn = sort_migration_routes(migration_routes_autumn)

    with open(OUTPUT_SORTED_TRIPLE_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_routes_spring, f, ensure_ascii=False, indent=4)

    with open(OUTPUT_SORTED_TRIPLE_JSON_FALL, "w", encoding="utf-8") as f:
        json.dump(sorted_routes_autumn, f, ensure_ascii=False, indent=4)

    print("Файлы с маршрутами миграции сохранены")


if __name__ == "__main__":
    building_triples()