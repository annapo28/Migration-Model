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
edges_weight = {}


def loss_function(alpha, migration_routes):
    """
        Функция потерь, которую минимизируем.
    """
    breeding_cells_clone = breeding_cells.copy()
    wintering_cells_clone = wintering_cells.copy()

    for route in migration_routes:
        (lat_i, lon_i), (lat_j, lon_j), (Lij, wi, uj) = route

        uk = min(
            alpha * wintering_cells_clone[(lat_i, lon_i)],
            (breeding_cells_clone[(lat_j, lon_j)] -  alpha * wintering_cells_clone[(lat_i, lon_i)])
        )

        # wintering_cells_clone[(lat_i, lon_i)] * (1 - alpha)
        # breeding_cells_clone[(lat_j, lon_j)] * (1 - alpha)

        breeding_cells_clone[(lat_j, lon_j)] -= uk
        wintering_cells_clone[(lat_i, lon_i)] -= uk

        pi_lm = uk / (wi + 1e-10) if wi > 0 else 0
        if isinstance(uk, np.ndarray):
            uk = uk.item()


        if (lat_i, lon_i) not in edges_weight:
            edges_weight[(lat_i, lon_i)] = []
        edges_weight[(lat_i, lon_i)].append((lat_j, lon_j, max(0.0, float(uk))))

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
        total_loss_u += breeding_cells_clone[(lat_j, lon_j)]
        total_loss_w += wintering_cells_clone[(lat_i, lon_i)]
    total_loss = total_loss_u ** 2 + total_loss_w ** 2
    print(f"alpha: {alpha}, total_loss: {total_loss}")  # Добавьте этот вывод

    return total_loss


def optimize_alpha(migration_routes, initial_alpha=0.7):
    """
        Оптимизирует α, минимизируя функцию потерь.
    """
    result = minimize(loss_function, initial_alpha, args=(migration_routes,), bounds=[(0, 1)])
    return result.x[0]


with open(INPUT_SORTED_TRIPLE_FILE, "r", encoding="utf-8") as f:
    migration_routes = json.load(f)

optimal_alpha = optimize_alpha(migration_routes)

for i in edges_weight.keys():
    print(i)


try:
    with open(OUTPUT_PROBABILITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(probabilities, f, ensure_ascii=False, indent=4)
except Exception as e:
    print(f"Ошибка при сохранении файла: {e}")
import json

# edges_weight = {(lat, lon): [(to_lat, to_lon, weight), ...], ...}

try:
    with open("edges_weight.json", "w", encoding="utf-8") as f:
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

    print("edges_weight сохранен в edges_weight.json")

except Exception as e:
    print(f"Ошибка при сохранении файла: {e}")
print(f"Готово! Оптимальное α: {optimal_alpha:.4f}")
print(f"Вероятности сохранены в {OUTPUT_PROBABILITIES_FILE}")

import folium
import numpy as np
from branca.colormap import linear

# Фильтруем edges_weight по заданной координате
center_coord = (17.5, -90.5)
def building_map(center_coord):
    if center_coord in edges_weight:
        relevant_edges = edges_weight[center_coord]
        print(relevant_edges)

        # Определяем min и max значения uk для нормализации
        uk_values = [uk for (_, _, uk) in relevant_edges]
        min_uk, max_uk = min(uk_values), max(uk_values)
        print(min_uk, max_uk)


        # Функция для линейного масштабирования uk

        def scale_uk(uk, min_uk, max_uk):
            # Добавляем небольшой сдвиг, чтобы избежать слишком маленьких значений
            min_uk = max(min_uk, 1e-10)
            max_uk = max(max_uk, 1e-10)
            scaled_value = (uk - min_uk) / (max_uk - min_uk)
            return scaled_value


        def scale_uk_log(uk, min_uk, max_uk):
            epsilon = 1e-10  # маленькая константа для предотвращения логарифмирования нуля
            log_uk = np.log(uk + epsilon)  # сдвигаем все значения, чтобы избежать log(0)
            log_min_uk = np.log(min_uk + epsilon)
            log_max_uk = np.log(max_uk + epsilon)
            if log_max_uk == log_min_uk:
                return 0  # если логарифмы одинаковы, то нет различий
            scaled_value = (log_uk - log_min_uk) / (log_max_uk - log_min_uk)
            return scaled_value


        # Создаем карту с центром в указанной точке
        m = folium.Map(location=center_coord, zoom_start=6)

        # Проходим по всем клеткам
        for (to_lat, to_lon, uk) in relevant_edges:
            scaled_uk = scale_uk_log(uk, min_uk, max_uk)  # Масштабируем uk
            color_intensity = int(255 * scaled_uk)  # Чем больше uk, тем ярче цвет
            color = f'#ff{color_intensity:02x}00'
            print(scaled_uk, uk, color)
            # Добавляем квадрат (ячейку) размером 1 градус на 1 градус
            folium.Rectangle(
                bounds=[(to_lat - 0.5, to_lon - 0.5), (to_lat + 0.5, to_lon + 0.5)],
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=1,
                tooltip=f"uk, coords: {uk:.4e}, {to_lat}, {to_lon}"  # Показываем uk в экспоненциальном формате
            ).add_to(m)

        # Сохраняем карту в HTML-файл
        m.save("migration_map.html")
        print("Карта сохранена в migration_map.html")
    else:
        print("Ключ (43.5, -88.5) отсутствует в edges_weight.")



building_map((17.5, -90.5))
