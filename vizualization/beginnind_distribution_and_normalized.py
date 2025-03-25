import json
import folium
import numpy as np
from folium.plugins import HeatMap

# Загружаем JSON с результатами
# output_json = "/home/anya2812/Migration-Model/grid_abundance_normalized.json"
output_json = "/home/anya2812/Migration-Model/wood_thrush/grid_data.json"
with open(output_json, "r", encoding="utf-8") as f:
    data_points = json.load(f)

# Разделяем данные по сезонам
breeding_points = []
wintering_points = []

for point in data_points:
    lat, lon, abundance = point["latitude"], point["longitude"], point["abundance"]

    if abundance is not None and not np.isnan(abundance):
        if point["season"] == "breeding":
            breeding_points.append([lat, lon, abundance])
        elif point["season"] == "wintering":
            wintering_points.append([lat, lon, abundance])

if not breeding_points:
    print("⚠ Warning: No valid breeding data found!")
if not wintering_points:
    print("⚠ Warning: No valid wintering data found!")

all_latitudes = [p[0] for p in breeding_points + wintering_points]
all_longitudes = [p[1] for p in breeding_points + wintering_points]

if all_latitudes and all_longitudes:
    map_center = [np.mean(all_latitudes), np.mean(all_longitudes)]
else:
    raise ValueError("No valid data points to display on the map!")

m = folium.Map(location=map_center, zoom_start=5)

# Более контрастные градиенты
breeding_gradient = {
    "0.1": "yellow",
    "0.3": "orange",
    "0.5": "red",
    "0.7": "darkred",
    "1.0": "black"
}

wintering_gradient = {
    "0.1": "lightblue",
    "0.3": "blue",
    "0.5": "darkblue",
    "0.7": "purple",
    "1.0": "black"
}
if wintering_points:
    heatmap_wintering = HeatMap(
        wintering_points,
        name="Wintering",
        gradient=wintering_gradient,
        radius=12,  # Аналогично
        blur=10,
        min_opacity=0.3
    )
    m.add_child(heatmap_wintering)
if breeding_points:
    heatmap_breeding = HeatMap(
        breeding_points,
        name="Breeding",
        gradient=breeding_gradient,
        radius=12,  # Сделал меньше, чтобы было более детально
        blur=10,  # Немного увеличил сглаживание
        min_opacity=0.3
    )
    m.add_child(heatmap_breeding)



# Создаем карты тепла


folium.LayerControl().add_to(m)

# Сохраняем карту
# m.save("/home/anya2812/Migration-Model/vizualization/heatmap.html")
print("✅ Карта сохранена в heatmap.html. Откройте этот файл в браузере.")
