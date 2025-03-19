import json
import numpy as np
from scipy.optimize import minimize
import copy
import folium

INPUT_SORTED_TRIPLE_FILE = "sorted_migration_routes.json"
INPUT_SORTED_TRIPLE_FILE_FALL = "sorted_migration_routes_fall.json"

OUTPUT_PROBABILITIES_FILE = "/home/anya2812/Migration-Model/migration_probabilities.json"
OUTPUT_PROBABILITIES_FILE_FALL = "/home/anya2812/Migration-Model/migration_probabilities_fall.json"  # Для осени

OUTPUT_WEIGHTS_FILE = "/home/anya2812/Migration-Model/output_densities.json"

GRID_DATA = "/home/anya2812/Migration-Model/grid_data.json"

excluded_coordinates = {(43.5, -88.5), (37.5, -78.5), (41.5, -69.5)}  # Пример: исключаем опред

with open(GRID_DATA, "r", encoding="utf-8") as f:
    grid_data = json.load(f)

breeding_cells = {}
wintering_cells = {}

wi_max = 0
uj_max = 0

for cell in grid_data:
    coords = (cell["latitude"], cell["longitude"])
    density = float(cell["abundance"])

    if cell["season"] == "breeding":
        breeding_cells[coords] = density
        uj_max += breeding_cells[coords]
        # breeding_cells_clone[coords] = density
    elif cell["season"] == "wintering":
        wintering_cells[coords] = density
        wi_max += wintering_cells[coords]
        # wintering_cells_clone[coords] = density

print("uj and wi ", uj_max, wi_max)

print("Клетки гнездования (breeding_cells):")
print(breeding_cells)

print("\nКлетки зимовки (wintering_cells):")
print(wintering_cells)
zero_count_1 = sum(1 for value in wintering_cells.values() if value == 0)
NON_zero_count_1 = sum(1 for value in wintering_cells.values() if value != 0)

print("zeros^ ", zero_count_1, NON_zero_count_1)


probabilities = []

def loss_function(alpha, routes):
    """
        Функция потерь, которую минимизируем.
    """
    breeding_cells_clone = copy.deepcopy(breeding_cells)
    wintering_cells_clone = copy.deepcopy(wintering_cells)

    for route in routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route

        uk = min(
            float(alpha.item()) * float(wintering_cells_clone[(lat_i, lon_i)]),
            float(breeding_cells_clone[(lat_j, lon_j)])
            )

        breeding_cells_clone[(lat_j, lon_j)] -= uk
        wintering_cells_clone[(lat_i, lon_i)] -= uk

    total_loss = 0
    for route in routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route
        total_loss += breeding_cells_clone[(lat_j, lon_j)]**2
        total_loss += wintering_cells_clone[(lat_i, lon_i)]**2
    # total_loss = total_loss_u ** 2 + total_loss_w ** 2
    # print(f"alpha: {alpha}, total_loss: {total_loss}")

    return total_loss


def loss_function_fall(alpha, routes):
    """
        Функция потерь, которую минимизируем.
    """

    breeding_cells_clone = copy.deepcopy(breeding_cells)
    wintering_cells_clone = copy.deepcopy(wintering_cells)
    zero_count = sum(1 for value in wintering_cells_clone.values() if value == 0)
    NON_zero_count = sum(1 for value in wintering_cells_clone.values() if value != 0)

    print("zeros^ ", zero_count, NON_zero_count)
    for route in routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route

        uk = min(
            float(alpha.item()) * float(breeding_cells_clone[(lat_i, lon_i)]),
            float(wintering_cells_clone[(lat_j, lon_j)])
            )

        # print('alpha ', alpha, 'breeding_cell ', float(breeding_cells_clone[(lat_i, lon_i)]), 'wintering_cell ', float(wintering_cells_clone[(lat_j, lon_j)]))
        # if uk != 0 :
        #
        #     print('uk ', uk)
        #


        breeding_cells_clone[(lat_i, lon_i)] -= uk
        wintering_cells_clone[(lat_j, lon_j)] -= uk

    total_loss = 0
    for route in routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route
        total_loss += breeding_cells_clone[(lat_i, lon_i)]**2
        total_loss += wintering_cells_clone[(lat_j, lon_j)]**2

    print(f"autumn alpha: {alpha}, total_loss: {total_loss}")

    return total_loss


def optimize_alpha(routes, initial_alpha=0.5):
    """
        Оптимизирует α, минимизируя функцию потерь.
    """
    result = minimize(loss_function, initial_alpha, args=(routes,), bounds=[(0, 1)])
    return result.x[0]

def optimize_alpha_fall(routes, initial_alpha=0.05):
    """
        Оптимизирует α, минимизируя функцию потерь.
    """
    result = minimize(loss_function_fall, initial_alpha, args=(routes,), bounds=[(0, 1)])
    return result.x[0]


with open(INPUT_SORTED_TRIPLE_FILE, "r", encoding="utf-8") as f:
    migration_routes = json.load(f)
with open(INPUT_SORTED_TRIPLE_FILE_FALL, "r", encoding="utf-8") as f:
    migration_routes_fall = json.load(f)


optimal_alpha_spring = optimize_alpha(migration_routes)
optimal_alpha_autumn = optimize_alpha_fall(migration_routes_fall)
print("Осень: ", optimal_alpha_autumn, "Весна: ", optimal_alpha_spring)
# exit()



breeding_cells_clone_final = copy.deepcopy(breeding_cells)
wintering_cells_clone_final = copy.deepcopy(wintering_cells)
edges_weight = {}
count = 0
all_count = 0
maxi=0
mini = 1111111111111111111
for route in migration_routes:
    (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route

    uk = min(
        float(optimal_alpha_spring) * float(wintering_cells_clone_final[(lat_i, lon_i)]),
        float(breeding_cells_clone_final[(lat_j, lon_j)])
    )
    # print("uk ", uk)

    all_count += 1
    pi_lm = uk / wi if wi != 0 else 0

    if uk == 0.0:
        count += 1

    maxi = max(maxi, pi_lm)
    if pi_lm > 0:
        mini = min(mini, pi_lm)
    # print(pi_lm)
    if isinstance(uk, np.ndarray):
        uk = uk.item()

    if isinstance(pi_lm, np.ndarray):
        pi_lm = pi_lm.item()

    # Добавляем данные в edges_weight
    if (lat_i, lon_i) not in edges_weight and (lat_i, lon_i) not in excluded_coordinates:
        edges_weight[(lat_i, lon_i)] = []
    if (lat_i, lon_i) not in excluded_coordinates:
        edges_weight[(lat_i, lon_i)].append((lat_j, lon_j, float(uk)))

    # Обновляем плотности
    breeding_cells_clone_final[(lat_j, lon_j)] -= uk
    wintering_cells_clone_final[(lat_i, lon_i)] -= uk

print(all_count, count, "LALALALLAL", maxi, mini)

# Сохраняем edges_weight в файл probabilities
try:
    with open(OUTPUT_PROBABILITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                f"{lat},{lon}": [
                    (f"{to_lat},{to_lon}", float(weight)) for to_lat, to_lon, weight in values
                ]
                for (lat, lon), values in edges_weight.items()
            },
            f,
            ensure_ascii=False,
            indent=4
        )
    print(f"Вероятности сохранены в {OUTPUT_PROBABILITIES_FILE}")
except Exception as e:
    print(f"Ошибка при сохранении файла: {e}")

def scale_uk_log(uk, min_uk, max_uk):
    if uk is None or np.isnan(uk) or uk < 0:
        return 0
    if min_uk is None or np.isnan(min_uk) or max_uk is None or np.isnan(max_uk):
        return 0
    if min_uk == max_uk:
        return 0

    epsilon = 1e-10
    log_uk = np.log(max(uk, epsilon))
    log_min_uk = np.log(max(min_uk, epsilon))
    log_max_uk = np.log(max(max_uk, epsilon))

    denominator = log_max_uk - log_min_uk
    if denominator == 0:
        return 0

    return (log_uk - log_min_uk) / denominator

# Загрузка данных
with open(GRID_DATA, "r", encoding="utf-8") as f:
    grid_data = json.load(f)

# Разделение клеток на гнездование и зимовку
breeding_cells = { (cell["latitude"], cell["longitude"]): cell["abundance"] for cell in grid_data if cell["season"] == "breeding" }
wintering_cells = { (cell["latitude"], cell["longitude"]): cell["abundance"] for cell in grid_data if cell["season"] == "wintering" }

# Нормализация плотностей на логарифмической шкале
breeding_densities = np.array(list(breeding_cells.values()))
wintering_densities = np.array(list(wintering_cells.values()))

min_breeding_density, max_breeding_density = breeding_densities.min(), breeding_densities.max()
min_wintering_density, max_wintering_density = wintering_densities.min(), wintering_densities.max()

norm_breeding_densities = [scale_uk_log(d, min_breeding_density, max_breeding_density) for d in breeding_densities]
norm_wintering_densities = [scale_uk_log(d, min_wintering_density, max_wintering_density) for d in wintering_densities]

# Создание карты
all_coords = np.vstack([list(breeding_cells.keys()), list(wintering_cells.keys())])
map_center = [np.mean(all_coords[:, 0]), np.mean(all_coords[:, 1])]

m = folium.Map(location=map_center, zoom_start=6)

# Добавление клеток гнездования
for (lat, lon), norm_value in zip(breeding_cells.keys(), norm_breeding_densities):
    color_intensity = int(255 * norm_value)
    color = f'#ff{color_intensity:02x}00'  # Оттенок оранжевого
    popup_text = f"Breeding Density: {breeding_cells[(lat, lon)]}"
    folium.Rectangle(
        bounds=[
            [lat - 0.5, lon - 0.5],
            [lat + 0.5, lon + 0.5]
        ],
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        weight=1,
        tooltip=popup_text
    ).add_to(m)

# Добавление клеток зимовки
for (lat, lon), norm_value in zip(wintering_cells.keys(), norm_wintering_densities):
    color_intensity = int(255 * norm_value)
    color = f'#00{color_intensity:02x}{255 - color_intensity:02x}'  # Оттенок синего
    popup_text = f"Wintering Density: {wintering_cells[(lat, lon)]}"
    folium.Rectangle(
        bounds=[
            [lat - 0.5, lon - 0.5],
            [lat + 0.5, lon + 0.5]
        ],
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        weight=1,
        tooltip=popup_text
    ).add_to(m)

# Сохранение карты
m.save("log_scale_breeding_and_wintering_map.html")
print("Карта с логарифмической шкалой сохранена в log_scale_breeding_and_wintering_map.html")



breeding_cells_clone_fall = copy.deepcopy(breeding_cells)
wintering_cells_clone_fall = copy.deepcopy(wintering_cells)
edges_weight_fall = {}

maxi=0
mini = 1111111111111111111

for route in migration_routes_fall:
    (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route

    uk = min(
        float(optimal_alpha_autumn) * float(breeding_cells_clone_fall[(lat_i, lon_i)]),
        float(wintering_cells_clone_fall[(lat_j, lon_j)])
    )

    pi_lm = uk / wi if wi != 0 else 0

    if (lat_i, lon_i) not in edges_weight_fall and (lat_i, lon_i) not in excluded_coordinates:
        edges_weight_fall[(lat_i, lon_i)] = []
    if (lat_i, lon_i) not in excluded_coordinates:
        edges_weight_fall[(lat_i, lon_i)].append((lat_j, lon_j, float(pi_lm)))


    if uk == 0.0:
        count += 1

    maxi = max(maxi, pi_lm)
    if pi_lm > 0:
        mini = min(mini, pi_lm)
    # print(pi_lm

    # Обновляем плотности
    breeding_cells_clone_final[(lat_i, lon_i)] -= uk
    wintering_cells_clone_final[(lat_j, lon_j)] -= uk

print("SISISIIISIISISISL", maxi, mini)


# Сохранение данных о вероятностях для осени в файл
try:
    with open(OUTPUT_PROBABILITIES_FILE_FALL, "w", encoding="utf-8") as f:
        json.dump(
            {
                f"{lat},{lon}": [
                    (f"{to_lat},{to_lon}", float(weight)) for to_lat, to_lon, weight in values
                ]
                for (lat, lon), values in edges_weight_fall.items()
            },
            f,
            ensure_ascii=False,
            indent=4
        )
    print(f"Вероятности для осени сохранены в {OUTPUT_PROBABILITIES_FILE_FALL}")
except Exception as e:
    print(f"Ошибка при сохранении файла для осени: {e}")