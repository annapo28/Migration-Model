import json
import numpy as np
from scipy.optimize import minimize
import copy
import folium

GRID_DATA = "/home/anya2812/Migration-Model/grid_data.json"
# Загрузка данных
with open(GRID_DATA, "r", encoding="utf-8") as f:
    grid_data = json.load(f)

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
    popup_text = f"Breeding Density: {breeding_cells[(lat, lon)]}, {lat, lon}"
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
    popup_text = f"Wintering Density: {wintering_cells[(lat, lon)]}, {lat, lon}"
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