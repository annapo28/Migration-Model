import json
import numpy as np
from scipy.cluster.hierarchy import optimal_leaf_ordering
from scipy.optimize import minimize

INPUT_SORTED_TRIPLE_FILE = "sorted_migration_routes.json"
OUTPUT_PROBABILITIES_FILE = "/home/anya2812/Migration-Model/migration_probabilities.json"
OUTPUT_WEIGHTS_FILE = "/home/anya2812/Migration-Model/output_densities.json"


GRID_FILE = "/home/anya2812/Migration-Model/grid_data.json"

with open(GRID_FILE, "r", encoding="utf-8") as f:
    grid_data = json.load(f)


breeding_cells = {}
breeding_cells_clone = {}
wintering_cells = {}
wintering_cells_clone = {}


for cell in grid_data:
    coords = (cell["latitude"], cell["longitude"])  # Ключ — пара координат
    density = cell["density"]  # Значение — плотность наблюдений

    if cell["season"] == "breeding":
        breeding_cells[coords] = density
        breeding_cells_clone[coords] = density
    elif cell["season"] == "wintering":
        wintering_cells[coords] = density
        wintering_cells_clone[coords] = density

print("Клетки гнездования (breeding_cells):")
print(breeding_cells)

print("\nКлетки зимовки (wintering_cells):")
print(wintering_cells)

probabilities = []
edges_weight = []

def loss_function(alpha, migration_routes):
    """
        Функция потерь, которую минимизируем.
    """
    total_loss = 0

    for route in migration_routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route


        uej = breeding_cells.get((lat_j, lon_j), 0)
        wei = wintering_cells.get((lat_i, lon_i), 0)

        breeding_cells_clone[(lat_j, lon_j)] = (1 - alpha) * uej
        wintering_cells_clone[(lat_i, lon_i)] = alpha * wei

        uk = min(
            max((1 - alpha) * (uej - breeding_cells_clone.get((lat_j, lon_j), 0)), 0),
            max(alpha * (wei - wintering_cells_clone.get((lat_i, lon_i), 0)), 0)
        )

        breeding_cells_clone[(lat_j, lon_j)] -= uk
        wintering_cells_clone[(lat_i, lon_i)] += uk

        pi_lm = uk / (wi + 1e-10) if wi > 0 else 0

        if isinstance(pi_lm, np.ndarray):
            pi_lm = pi_lm.item()
        probabilities.append({
            "from": {"latitude": lat_i, "longitude": lon_i},
            "to": {"latitude": lat_j, "longitude": lon_j},
            "probability": float(pi_lm)
        })

    total_loss_u = 0
    total_loss_w = 0
    for route in migration_routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route
        total_loss_u += breeding_cells.get((lat_j, lon_j), 0) - breeding_cells_clone.get((lat_j, lon_j), 0)
        total_loss_w += wintering_cells.get((lat_i, lon_i), 0) - wintering_cells_clone.get((lat_i, lon_i), 0)
    total_loss = total_loss_u**2 + total_loss_w**2

    return total_loss

def optimize_alpha(migration_routes, initial_alpha=0.5):
    """
        Оптимизирует α, минимизируя функцию потерь.
    """
    result = minimize(loss_function, initial_alpha, args=(migration_routes,), bounds=[(0, 1)])
    return result.x[0]


with open(INPUT_SORTED_TRIPLE_FILE, "r", encoding="utf-8") as f:
    migration_routes = json.load(f)

optimal_alpha = optimize_alpha(migration_routes)

for route in migration_routes:
    (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route


    wi = float(wi)
    uj = float(uj)

    uej = breeding_cells.get((lat_j, lon_j), 0)
    wei = wintering_cells.get((lat_i, lon_i), 0)

    breeding_cells_clone[(lat_j, lon_j)] = (1 - optimal_alpha) * uej
    wintering_cells_clone[(lat_i, lon_i)] = optimal_alpha * wei

    uk = min(
        max((1 - optimal_alpha) * (uej - breeding_cells_clone.get((lat_j, lon_j), 0)), 0),
        max(optimal_alpha * (wei - wintering_cells_clone.get((lat_i, lon_i), 0)), 0)
    )

    breeding_cells_clone[(lat_j, lon_j)] -= uk
    wintering_cells_clone[(lat_i, lon_i)] += uk

    edges_weight.append({
        "from": {"latitude": lat_i, "longitude": lon_i},
        "to": {"latitude": lat_j, "longitude": lon_j},
        "uk": uk
    })

try:
    with open(OUTPUT_PROBABILITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(probabilities, f, ensure_ascii=False, indent=4)
    with open(OUTPUT_WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(edges_weight, f, ensure_ascii=False, indent=4)
    print(f"Готово! Оптимальное α: {optimal_alpha:.4f}")
    print(f"Вероятности сохранены в {OUTPUT_PROBABILITIES_FILE}")
except Exception as e:
    print(f"Ошибка при сохранении файла: {e}")