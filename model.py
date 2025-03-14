import json
import numpy as np
from scipy.optimize import minimize
import copy
import folium

INPUT_SORTED_TRIPLE_FILE = "sorted_migration_routes.json"
INPUT_SORTED_TRIPLE_FILE_FALL = "sorted_migration_routes_fall.json"

OUTPUT_PROBABILITIES_FILE = "/home/anya2812/Migration-Model/migration_probabilities.json"
OUTPUT_WEIGHTS_FILE = "/home/anya2812/Migration-Model/output_densities.json"

GRID_FILE = "/home/anya2812/Migration-Model/grid_data.json"
NEW_GRID_DATA = "changed_grid_data.json"

excluded_coordinates = {(43.5, -88.5), (37.5, -78.5), (41.5, -69.5)}  # Пример: исключаем опред

with open(NEW_GRID_DATA, "r", encoding="utf-8") as f:
    grid_data = json.load(f)

breeding_cells = {}
wintering_cells = {}

wi_max = 0
uj_max = 0

for cell in grid_data:
    coords = (cell["latitude"], cell["longitude"])
    density = float(cell["density"])

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

        # pi_lm = uk / (wi + 1e-10) if wi > 0 else 0
        # if isinstance(uk, np.ndarray):
        #     uk = uk.item()

        #

        # if isinstance(pi_lm, np.ndarray):
        #     pi_lm = pi_lm.item()
        # probabilities.append({
        #     "from": {"latitude": lat_i, "longitude": lon_i},
        #     "to": {"latitude": lat_j, "longitude": lon_j},
        #     "probability": float(pi_lm)
        # })

    total_loss = 0
    for route in routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route
        total_loss += breeding_cells_clone[(lat_i, lon_i)]**2
        total_loss += wintering_cells_clone[(lat_j, lon_j)]**2
    # total_loss = total_loss_u ** 2 + total_loss_w ** 2
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
for route in migration_routes:
    (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route

    uk = min(
        optimal_alpha_spring * wintering_cells_clone_final[(lat_i, lon_i)],
        (breeding_cells_clone_final[(lat_j, lon_j)])
    )

    pi_lm = uk / (wi + 1e-10) if wi > 0 else 0
    if isinstance(uk, np.ndarray):
        uk = uk.item()

    if isinstance(pi_lm, np.ndarray):
        pi_lm = pi_lm.item()

    # Добавляем данные в edges_weight
    if (lat_i, lon_i) not in edges_weight and (lat_i, lon_i) not in excluded_coordinates:
        edges_weight[(lat_i, lon_i)] = []
    if (lat_i, lon_i) not in excluded_coordinates:
        edges_weight[(lat_i, lon_i)].append((lat_j, lon_j, float(pi_lm)))

    # Обновляем плотности
    breeding_cells_clone_final[(lat_j, lon_j)] -= uk
    wintering_cells_clone_final[(lat_i, lon_i)] -= uk

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

# try:
#     with open("edges_weight.json", "w", encoding="utf-8") as f:
#         json.dump(
#             {
#                 f"{lat},{lon}": [
#                     (f"{to_lat},{to_lon}", float(weight)) for to_lat, to_lon, weight in values
#                 ]
#                 for (lat, lon), values in edges_weight.items()
#             },
#             f,
#             ensure_ascii=False,
#             indent=4
#         )
#
#     print("edges_weight сохранен в edges_weight.json")
#
# except Exception as e:
#     print(f"Ошибка при сохранении файла: {e}")
#
# def scale_uk_log(uk, min_uk, max_uk):
#     if uk is None or np.isnan(uk) or uk < 0:
#         return 0
#     if min_uk is None or np.isnan(min_uk) or max_uk is None or np.isnan(max_uk):
#         return 0
#     if min_uk == max_uk:
#         return 0
#
#     epsilon = 1e-10
#     log_uk = np.log(max(uk, epsilon))
#     log_min_uk = np.log(max(min_uk, epsilon))
#     log_max_uk = np.log(max(max_uk, epsilon))
#
#     denominator = log_max_uk - log_min_uk
#     if denominator == 0:
#         return 0
#
#     return (log_uk - log_min_uk) / denominator
#
# #
# # def safe_log(x, epsilon=1e-10):
# #     return np.log(max(x, epsilon))  # Добавляем малое число, чтобы избежать log(0)
# #
# # def scale_uk_log(uk, min_uk, max_uk):
# #     if uk is None or np.isnan(uk) or uk < 0:
# #         return 0
# #     if min_uk == max_uk:  # Если плотности одинаковые, нормализовать бессмысленно
# #         return 0
# #     log_uk = safe_log(uk)
# #     log_min_uk = safe_log(min_uk)
# #     log_max_uk = safe_log(max_uk)
# #     return (log_uk - log_min_uk) / (log_max_uk - log_min_uk)
# #
#
#
# breeding_coords = np.array(list(breeding_cells_clone_final.keys()))
# breeding_densities = np.array(list(breeding_cells_clone_final.values()))
#
# min_breeding_density, max_breeding_density = breeding_densities.min(), breeding_densities.max()
# norm_breeding_densities = [scale_uk_log(d, min_breeding_density, max_breeding_density) for d in breeding_densities]
#
# wintering_coords = np.array(list(wintering_cells_clone_final.keys()))
# wintering_densities = np.array(list(wintering_cells_clone_final.values()))
#
# min_wintering_density, max_wintering_density = wintering_densities.min(), wintering_densities.max()
# norm_wintering_densities = [scale_uk_log(d, min_wintering_density, max_wintering_density) for d in wintering_densities]
#
# all_coords = np.vstack([breeding_coords, wintering_coords])
# map_center = [np.mean(all_coords[:, 0]), np.mean(all_coords[:, 1])]
#
# m = folium.Map(location=map_center, zoom_start=6)
#
# for (lat, lon), norm_value in zip(breeding_coords, norm_breeding_densities):
#     color_intensity = int(255 * norm_value)
#     color = f'#ff{color_intensity:02x}00'  # Оттенок оранжевого
#     popup_text = f"Breeding Density: {breeding_cells_clone_final[(lat, lon)]}"
#     folium.Rectangle(
#         bounds=[
#             [lat - 0.5, lon - 0.5],
#             [lat + 0.5, lon + 0.5]
#         ],
#         color=color,
#         fill=True,
#         fill_color=color,
#         fill_opacity=0.7,
#         weight=1,
#         tooltip=popup_text
#     ).add_to(m)
#
# for (lat, lon), norm_value in zip(wintering_coords, norm_wintering_densities):
#     color_intensity = int(255 * norm_value)
#     color = f'#00{color_intensity:02x}{255 - color_intensity:02x}'
#
#     # color = f'#00{color_intensity:02x}ff'  # Оттенок синего
#     popup_text = f"Wintering Density: {wintering_cells_clone_final[(lat, lon)]}"
#     folium.Rectangle(
#         bounds=[
#             [lat - 0.5, lon - 0.5],
#             [lat + 0.5, lon + 0.5]
#         ],
#         color=color,
#         fill=True,
#         fill_color=color,
#         fill_opacity=0.7,
#         weight=1,
#         tooltip=popup_text
#     ).add_to(m)
#
# m.save("breeding_and_wintering_clone_map.html")
# print("Карта сохранена в breeding_and_wintering_clone_map.html")
import folium
import numpy as np

# Функция для нормализации на логарифмической шкале
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
with open(NEW_GRID_DATA, "r", encoding="utf-8") as f:
    grid_data = json.load(f)

# Разделение клеток на гнездование и зимовку
breeding_cells = { (cell["latitude"], cell["longitude"]): cell["density"] for cell in grid_data if cell["season"] == "breeding" }
wintering_cells = { (cell["latitude"], cell["longitude"]): cell["density"] for cell in grid_data if cell["season"] == "wintering" }

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