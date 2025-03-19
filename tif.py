import rasterio
import json
import numpy as np
from rasterio.transform import rowcol
from pyproj import Transformer

# Пути к растровым файлам
wintering_tif_path = "/home/anya2812/Загрузки/woothr_abundance_seasonal_nonbreeding_mean_2022.tif"
breeding_tif_path = "/home/anya2812/Загрузки/woothr_abundance_seasonal_breeding_mean_2022.tif"
json_path = "/home/anya2812/PycharmProjects/pythonProject/Oenanthe oenanthe/Grid/data_final_2017.json"
output_json = "grid_abundance.json"

# Загружаем JSON
with open(json_path, "r", encoding="utf-8") as f:
    data_points = json.load(f)

# Загружаем растровые файлы один раз
rasters = {
    "wintering": rasterio.open(wintering_tif_path),
    "breeding": rasterio.open(breeding_tif_path),
}

# Читаем данные растров в массив numpy
raster_data = {season: rasters[season].read(1) for season in rasters}
nodata_values = {season: rasters[season].nodata for season in rasters}

# Создаём трансформеры координат WGS84 -> CRS TIFF
transformers = {season: Transformer.from_crs("EPSG:4326", rasters[season].crs, always_xy=True) for season in rasters}

# Список для сохранения результатов
results = []

# Обрабатываем все точки
for point in data_points:
    lat, lon = point["latitude"], point["longitude"]
    season = point["season"]

    if season not in rasters:
        abundance = None  # Если сезона нет в растровых файлах
    else:
        raster = rasters[season]
        transformer = transformers[season]

        # Преобразуем координаты WGS84 → CRS TIFF
        x, y = transformer.transform(lon, lat)

        # Переводим в индексы пикселей
        row, col = rowcol(raster.transform, x, y)

        # Проверяем, внутри ли точка изображения
        if 0 <= row < raster.height and 0 <= col < raster.width:
            abundance = raster_data[season][row, col]

            # Если значение - NoData, то ставим None
            if abundance == nodata_values[season]:
                abundance = None
            else:
                abundance = float(abundance)
        else:
            abundance = None  # Точка за границами растра

    # Добавляем в результат
    results.append({"latitude": lat, "longitude": lon, "season": season, "abundance": abundance})

# Закрываем растровые файлы
for raster in rasters.values():
    raster.close()

# Сохраняем результат в JSON
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"Results saved to {output_json}")

finish_output_json = "grid_abundance_normalized.json"


# Убираем NaN и None из данных
breeding_abundances = [p["abundance"] for p in results if p["season"] == "breeding" and p["abundance"] is not None and not np.isnan(p["abundance"])]
wintering_abundances = [p["abundance"] for p in results if p["season"] == "wintering" and p["abundance"] is not None and not np.isnan(p["abundance"])]

# Вычисляем суммы
breeding_sum = sum(breeding_abundances) if breeding_abundances else 0
wintering_sum = sum(wintering_abundances) if wintering_abundances else 0


# Отладка: выводим суммы
print(f"🔹 Сумма breeding: {breeding_sum}")
print(f"🔹 Сумма wintering: {wintering_sum}")

breeding_max = max(breeding_abundances) if breeding_abundances else 0
wintering_max = max(wintering_abundances) if wintering_abundances else 0


# Отладка: выводим суммы
print(f"🔹 max breeding: {breeding_max}")
print(f"🔹 max wintering: {wintering_max}")

breeding_min = min(breeding_abundances) if breeding_abundances else 0
wintering_min = min(wintering_abundances) if wintering_abundances else 0


# Отладка: выводим суммы
print(f"🔹 Сумма breeding: {breeding_min}")
print(f"🔹 Сумма wintering: {wintering_min}")

# Создаём новый список с нормализованными значениями
normalized_data = []

for point in results:
    abundance = point["abundance"]
    season = point["season"]

    if abundance is not None and not np.isnan(abundance):
        if season == "breeding" and breeding_sum > 0:
            norm_abundance = abundance / breeding_sum
        elif season == "wintering" and wintering_sum > 0:
            norm_abundance = abundance / wintering_sum
        else:
            norm_abundance = None  # Если сумма 0, оставляем None
    else:
        norm_abundance = None

    normalized_data.append({
        "latitude": point["latitude"],
        "longitude": point["longitude"],
        "season": season,
        "abundance": norm_abundance
    })

breeding_abundances = [p["abundance"] for p in normalized_data if p["season"] == "breeding" and p["abundance"] is not None and not np.isnan(p["abundance"])]
wintering_abundances = [p["abundance"] for p in normalized_data if p["season"] == "wintering" and p["abundance"] is not None and not np.isnan(p["abundance"])]

# Вычисляем суммы
breeding_sum = sum(breeding_abundances) if breeding_abundances else 0
wintering_sum = sum(wintering_abundances) if wintering_abundances else 0


# Отладка: выводим суммы
print(f"🔹 Сумма breeding: {breeding_sum}")
print(f"🔹 Сумма wintering: {wintering_sum}")

breeding_max = max(breeding_abundances) if breeding_abundances else 0
wintering_max = max(wintering_abundances) if wintering_abundances else 0


# Отладка: выводим суммы
print(f"🔹 max breeding: {breeding_max}")
print(f"🔹 max wintering: {wintering_max}")

breeding_min = min(breeding_abundances) if breeding_abundances else 0
wintering_min = min(wintering_abundances) if wintering_abundances else 0


# Отладка: выводим суммы
print(f"🔹 Сумма breeding: {breeding_min}")
print(f"🔹 Сумма wintering: {wintering_min}")


# Сохраняем нормализованный JSON
with open(finish_output_json, "w", encoding="utf-8") as f:
    json.dump(normalized_data, f, ensure_ascii=False, indent=4)

print(f"✅ Нормализованные данные сохранены в {output_json}")


