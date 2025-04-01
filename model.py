import json
import numpy as np
from scipy.optimize import minimize
import copy
import folium

GRID_DATA = "/home/anya2812/Migration-Model/amewoo/grid_data.json"

INPUT_SORTED_TRIPLE_FILE = "amewoo/sorted_migration_routes.json"
INPUT_SORTED_TRIPLE_FILE_FALL = "amewoo/sorted_migration_routes_fall.json"
INPUT_CHAIN_TRIPLE_FILE_SPRING = "/home/anya2812/Migration-Model/amewoo/chain_migration_routes.json"
INPUT_CHAIN_TRIPLE_FILE_FALL = "/home/anya2812/Migration-Model/amewoo/chain_migration_routes_fall.json"

OUTPUT_PROBABILITIES_FILE = "/home/anya2812/Migration-Model/amewoo/migration_probabilities.json"
OUTPUT_PROBABILITIES_FILE_FALL = "/home/anya2812/Migration-Model/amewoo/migration_probabilities_fall.json"
CHAIN_OUTPUT_PROBABILITIES_FILE = "/home/anya2812/Migration-Model/amewoo/chain_migration_probabilities.json"
CHAIN_OUTPUT_PROBABILITIES_FILE_FALL = "/home/anya2812/Migration-Model/amewoo/chain_migration_probabilities_fall.json"

OUTPUT_WEIGHT = "/home/anya2812/Migration-Model/amewoo/migration_weights.json"
OUTPUT_WEIGHT_FALL = "/home/anya2812/Migration-Model/amewoo/migration_weights_fall.json"
CHAIN_OUTPUT_WEIGHT = "/home/anya2812/Migration-Model/amewoo/chain_migration_weights.json"
CHAIN_OUTPUT_WEIGHT_FALL = "/home/anya2812/Migration-Model/amewoo/chain_migration_weights_fall.json"

BREEDING_DISCREPANCY_FILE = "/home/anya2812/Migration-Model/amewoo/breeding_discrepancy.json"
WINTERING_DISCREPANCY_FILE = "/home/anya2812/Migration-Model/amewoo/wintering_discrepancy.json"

BREEDING_DISCREPANCY_FILE_FALL = "/home/anya2812/Migration-Model/amewoo/breeding_discrepancy_fall.json"
WINTERING_DISCREPANCY_FILE_FALL = "/home/anya2812/Migration-Model/amewoo/wintering_discrepancy_fall.json"

CHAIN_BREEDING_DISCREPANCY_FILE = "/home/anya2812/Migration-Model/amewoo/chain_breeding_discrepancy.json"
CHAIN_WINTERING_DISCREPANCY_FILE = "/home/anya2812/Migration-Model/amewoo/chain_wintering_discrepancy.json"

CHAIN_BREEDING_DISCREPANCY_FILE_FALL = "/home/anya2812/Migration-Model/amewoo/chain_breeding_discrepancy_fall.json"
CHAIN_WINTERING_DISCREPANCY_FILE_FALL = "/home/anya2812/Migration-Model/amewoo/chain_wintering_discrepancy_fall.json"
# excluded_coordinates = {(43.5, -88.5), (37.5, -78.5), (41.5, -69.5)}
# excluded_coordinates = {}

with open(GRID_DATA, "r", encoding="utf-8") as f:
    grid_data = json.load(f)

breeding_cells = {}
wintering_cells = {}

sum_u = 0
sum_w = 0

for cell in grid_data:
    coords = (cell["latitude"], cell["longitude"])
    density = float(cell["abundance"])
    if cell["season"] == "breeding":
        breeding_cells[coords] = density
        sum_u += breeding_cells[coords]
    elif cell["season"] == "wintering":
        wintering_cells[coords] = density
        sum_w += wintering_cells[coords]

print(sum_u,  sum_w)
# print(wintering_cells[(30.5, -83.5)])
# print(breeding_cells[(30.5, -83.5)])
#

def loss_function(alpha, routes, cells_from, cells_to):
    cells_from_clone = copy.deepcopy(cells_from)
    cells_to_clone = copy.deepcopy(cells_to)
    grouped_routes = {}
    for route in routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj, n_k, _) = route
        key = (lat_j, lon_j, Lij)
        if key not in grouped_routes:
            grouped_routes[key] = []
        grouped_routes[key].append(route)

    for (lat_j, lon_j, Lij), group in grouped_routes.items():
        Uk = sum(cells_from_clone[(lat_i, lon_i)] for (lat_i, lon_i), _, _ in group) # это все , кто вылетает в данную на фикс расстоянии, сумма шара

        uk = min(float(alpha.item()) * float(Uk), float(cells_to_clone.get((lat_j, lon_j), 0))) # столько в целом сядет
        cells_to_clone[(lat_j, lon_j)] -= uk
        for idx, ((lat_i, lon_i), _, _) in enumerate(group):
            cells_from_clone[(lat_i, lon_i)] *= (1 - (uk / (Uk + 1e-70)))
    total_loss = sum(v ** 2 for v in cells_to_clone.values()) + sum(v ** 2 for v in cells_from_clone.values())

    print("Разница между невязками: ", sum(v for v in cells_to_clone.values()) - sum(v for v in cells_from_clone.values()))
    return total_loss


def update_densities(routes, alpha, cells_from, cells_to):
    cells_from_clone = copy.deepcopy(cells_from)
    cells_to_clone = copy.deepcopy(cells_to)
    edges_weight = {}
    real_edges_weight = {}

    grouped_routes = {}
    for route in routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj, n_k, _) = route
        key = (lat_j, lon_j, Lij)
        if key not in grouped_routes:
            grouped_routes[key] = []
        grouped_routes[key].append(route)

    for (lat_j, lon_j, Lij), group in grouped_routes.items():
        Uk = sum(cells_from_clone.get((lat_i, lon_i), 0) for (lat_i, lon_i), _, _ in group)  # это все , кто вылетает в данную на фикс расстоянии, сумма шара
        uk = min(float(alpha.item()) * float(Uk), float(cells_to_clone.get((lat_j, lon_j), 0)))  # столько в целом сядет
        cells_to_clone[(lat_j, lon_j)] -= uk
        if Uk != 0:
            for idx, ((lat_i, lon_i), _, _) in enumerate(group):
                uk_next = cells_from_clone[(lat_i, lon_i)] * (uk / Uk)
                cells_from_clone[(lat_i, lon_i)] *= (1 - (uk / Uk ))
        # uk_next = cells_from_clone[(lat_i, lon_i)] * (uk / Uk)
                if (lat_i, lon_i) not in edges_weight:
                    edges_weight[(lat_i, lon_i)] = []
                if (lat_i, lon_i) not in real_edges_weight:
                    real_edges_weight[(lat_i, lon_i)] = []
                edges_weight[(lat_i, lon_i)].append((lat_j, lon_j, uk_next / (float(cells_from.get((lat_j, lon_j), 0)) + 1e-80)))
                real_edges_weight[(lat_i, lon_i)].append((lat_j, lon_j, uk_next))
        else:
            for idx, ((lat_i, lon_i), _, _) in enumerate(group):
                if (lat_i, lon_i) not in edges_weight:
                    edges_weight[(lat_i, lon_i)] = []
                if (lat_i, lon_i) not in real_edges_weight:
                    real_edges_weight[(lat_i, lon_i)] = []
                edges_weight[(lat_i, lon_i)].append((lat_j, lon_j, 1e-80))
                real_edges_weight[(lat_i, lon_i)].append((lat_j, lon_j, 1e-80))

    print("Финальная Разница между невязками: ",
          sum(v for v in cells_to_clone.values()) - sum(v for v in cells_from_clone.values()))

    return real_edges_weight, edges_weight, cells_from_clone, cells_to_clone

def optimize_alpha(routes, cells_from, cells_to, initial_alpha=0.5):
    result = minimize(loss_function, initial_alpha, args=(routes, cells_from, cells_to), bounds=[(0, 1)])
    return result.x[0]


def save_results(edges_weight, output_file):
    try:
        with open(output_file, "w", encoding="utf-8") as f:
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
        print(f"Вероятности сохранены в {output_file}")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")

def calculate_discrepancies(cells_final, cells_initial):
    sum_a = 0
    discrepancies = {}
    for coords, initial_density in cells_initial.items():
        final_density = cells_final[coords]
        if initial_density != 0:
            discrepancies[coords] = final_density / initial_density
            # if final_density == initial_density :
            #     print(coords)
            sum_a += cells_final[coords] # = final_density / initial_density
        else:
            discrepancies[coords] = 0
    print("summa", sum_a)
    return discrepancies #, sum_a

def save_discrepancies(discrepancies, output_file):
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {f"{lat},{lon}": value for (lat, lon), value in discrepancies.items()},
                f,
                ensure_ascii=False,
                indent=4
            )
        print(f"Невязки сохранены в {output_file}")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")

with open(INPUT_SORTED_TRIPLE_FILE, "r", encoding="utf-8") as f:
    migration_routes = json.load(f)
with open(INPUT_SORTED_TRIPLE_FILE_FALL, "r", encoding="utf-8") as f:
    migration_routes_fall = json.load(f)
with open(INPUT_CHAIN_TRIPLE_FILE_SPRING, "r", encoding="utf-8") as f:
    chain_migration_routes = json.load(f)
with open(INPUT_CHAIN_TRIPLE_FILE_FALL, "r", encoding="utf-8") as f:
    chain_migration_routes_fall = json.load(f)

optimal_alpha_spring = optimize_alpha(migration_routes, wintering_cells, breeding_cells)
optimal_alpha_autumn = optimize_alpha(migration_routes_fall, breeding_cells, wintering_cells)
chain_optimal_alpha_spring = optimize_alpha(chain_migration_routes, wintering_cells, breeding_cells)
chain_optimal_alpha_fall = optimize_alpha(chain_migration_routes_fall, breeding_cells, wintering_cells)

print(optimal_alpha_spring, optimal_alpha_autumn, chain_optimal_alpha_spring, chain_optimal_alpha_fall)

real_edges_weight_spring, edges_weight_spring, wintering_cells_clone_spring, breeding_cells_clone_spring= update_densities(
    migration_routes, optimal_alpha_spring, wintering_cells, breeding_cells
)
real_edges_weight_fall, edges_weight_fall, breeding_cells_clone_fall, wintering_cells_clone_fall = update_densities(
    migration_routes_fall, optimal_alpha_autumn, breeding_cells, wintering_cells
)
real_edges_weight_chain_spring, edges_weight_chain_spring, wintering_cells_clone_chain_spring, breeding_cells_clone_chain_spring = update_densities(
    chain_migration_routes, chain_optimal_alpha_spring, wintering_cells, breeding_cells
)
real_edges_weight_chain_fall, edges_weight_chain_fall, breeding_cells_clone_chain_fall, wintering_cells_clone_chain_fall = update_densities(
    chain_migration_routes_fall, chain_optimal_alpha_fall, breeding_cells, wintering_cells
)

save_results(edges_weight_spring, OUTPUT_PROBABILITIES_FILE)
save_results(edges_weight_fall, OUTPUT_PROBABILITIES_FILE_FALL)
save_results(edges_weight_chain_spring, CHAIN_OUTPUT_PROBABILITIES_FILE)
save_results(edges_weight_chain_fall, CHAIN_OUTPUT_PROBABILITIES_FILE_FALL)

save_results(real_edges_weight_spring, OUTPUT_WEIGHT)
save_results(real_edges_weight_fall, OUTPUT_WEIGHT_FALL)
save_results(real_edges_weight_chain_spring, CHAIN_OUTPUT_WEIGHT)
save_results(real_edges_weight_chain_fall, CHAIN_OUTPUT_WEIGHT_FALL)

breeding_discrepancies_spring = calculate_discrepancies(breeding_cells_clone_spring, breeding_cells)
wintering_discrepancies_spring = calculate_discrepancies(wintering_cells_clone_spring, wintering_cells)
breeding_discrepancies_fall = calculate_discrepancies(breeding_cells_clone_fall, breeding_cells)
wintering_discrepancies_fall = calculate_discrepancies(wintering_cells_clone_fall, wintering_cells)
chain_breeding_discrepancies_spring = calculate_discrepancies(breeding_cells_clone_chain_spring, breeding_cells)
chain_wintering_discrepancies_spring = calculate_discrepancies(wintering_cells_clone_chain_spring, wintering_cells)
chain_breeding_discrepancies_fall = calculate_discrepancies(breeding_cells_clone_chain_fall, breeding_cells)
chain_wintering_discrepancies_fall = calculate_discrepancies(wintering_cells_clone_chain_fall, wintering_cells)

save_discrepancies(breeding_discrepancies_spring, BREEDING_DISCREPANCY_FILE)
save_discrepancies(wintering_discrepancies_spring, WINTERING_DISCREPANCY_FILE)
save_discrepancies(breeding_discrepancies_fall, BREEDING_DISCREPANCY_FILE_FALL)
save_discrepancies(wintering_discrepancies_fall, WINTERING_DISCREPANCY_FILE_FALL)
save_discrepancies(chain_breeding_discrepancies_spring, CHAIN_BREEDING_DISCREPANCY_FILE)
save_discrepancies(chain_wintering_discrepancies_spring, CHAIN_WINTERING_DISCREPANCY_FILE)
save_discrepancies(breeding_discrepancies_fall, CHAIN_BREEDING_DISCREPANCY_FILE_FALL)
save_discrepancies(wintering_discrepancies_fall, CHAIN_WINTERING_DISCREPANCY_FILE_FALL)

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

with open(GRID_DATA, "r", encoding="utf-8") as f:
    grid_data = json.load(f)

breeding_cells = { (cell["latitude"], cell["longitude"]): cell["abundance"] for cell in grid_data if cell["season"] == "breeding" }
wintering_cells = { (cell["latitude"], cell["longitude"]): cell["abundance"] for cell in grid_data if cell["season"] == "wintering" }

breeding_densities = np.array(list(breeding_cells.values()))
wintering_densities = np.array(list(wintering_cells.values()))

min_breeding_density, max_breeding_density = breeding_densities.min(), breeding_densities.max()
min_wintering_density, max_wintering_density = wintering_densities.min(), wintering_densities.max()

norm_breeding_densities = [scale_uk_log(d, min_breeding_density, max_breeding_density) for d in breeding_densities]
norm_wintering_densities = [scale_uk_log(d, min_wintering_density, max_wintering_density) for d in wintering_densities]

all_coords = np.vstack([list(breeding_cells.keys()), list(wintering_cells.keys())])
map_center = [np.mean(all_coords[:, 0]), np.mean(all_coords[:, 1])]

m = folium.Map(location=map_center, zoom_start=6)

for (lat, lon), norm_value in zip(breeding_cells.keys(), norm_breeding_densities):
    color_intensity = int(255 * norm_value)
    color = f'#ff{color_intensity:02x}00'
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

for (lat, lon), norm_value in zip(wintering_cells.keys(), norm_wintering_densities):
    color_intensity = int(255 * norm_value)
    color = f'#00{color_intensity:02x}{255 - color_intensity:02x}'
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

m.save("vizualization/log_scale_breeding_and_wintering_map.html")
print("Карта с логарифмической шкалой сохранена в log_scale_breeding_and_wintering_map.html")