import rasterio
import json
import numpy as np
from rasterio.transform import rowcol
from pyproj import Transformer

wintering_tif_path = "/home/anya2812/Загрузки/amewoo_abundance_seasonal_nonbreeding_mean_2022.tif"
breeding_tif_path = "/home/anya2812/Загрузки/amewoo_abundance_seasonal_breeding_mean_2022.tif"
json_path = "/home/anya2812/Migration-Model/amewoo/data_final_2017.json"
output_json = "/home/anya2812/Migration-Model/amewoo/grid_abundance.json"
finish_output_json = "amewoo/grid_abundance_normalized.json"


with open(json_path, "r", encoding="utf-8") as f:
    data_points = json.load(f)

rasters = {
    "wintering": rasterio.open(wintering_tif_path),
    "breeding": rasterio.open(breeding_tif_path),
}

raster_data = {season: rasters[season].read(1) for season in rasters}
nodata_values = {season: rasters[season].nodata for season in rasters}

transformers = {season: Transformer.from_crs("EPSG:4326", rasters[season].crs, always_xy=True) for season in rasters}

results = []

for point in data_points:
    lat, lon = point["latitude"], point["longitude"]
    season = point["season"]

    if season not in rasters:
        abundance = None
    else:
        raster = rasters[season]
        transformer = transformers[season]

        x, y = transformer.transform(lon, lat)
        row, col = rowcol(raster.transform, x, y)

        if 0 <= row < raster.height and 0 <= col < raster.width:
            abundance = raster_data[season][row, col]

            if abundance == nodata_values[season]:
                abundance = None
            else:
                abundance = float(abundance)
        else:
            abundance = None


    results.append({"latitude": lat, "longitude": lon, "season": season, "abundance": abundance})

for raster in rasters.values():
    raster.close()

with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"Results saved to {output_json}")


breeding_abundances = [p["abundance"] for p in results if p["season"] == "breeding" and p["abundance"] is not None and not np.isnan(p["abundance"])]
wintering_abundances = [p["abundance"] for p in results if p["season"] == "wintering" and p["abundance"] is not None and not np.isnan(p["abundance"])]

breeding_sum = sum(breeding_abundances) if breeding_abundances else 0
wintering_sum = sum(wintering_abundances) if wintering_abundances else 0


print(f"1Сумма breeding: {breeding_sum}")
print(f"1Сумма wintering: {wintering_sum}")

breeding_max = max(breeding_abundances) if breeding_abundances else 0
wintering_max = max(wintering_abundances) if wintering_abundances else 0



print(f" max breeding: {breeding_max}")
print(f" max wintering: {wintering_max}")

breeding_min = min(breeding_abundances) if breeding_abundances else 0
wintering_min = min(wintering_abundances) if wintering_abundances else 0


print(f" 2/Сумма breeding: {breeding_min}")
print(f" 2/Сумма wintering: {wintering_min}")

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
            norm_abundance = None
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

breeding_sum = sum(breeding_abundances) if breeding_abundances else 0
wintering_sum = sum(wintering_abundances) if wintering_abundances else 0

print(f"3 Сумма breeding: {breeding_sum}")
print(f" 3 Сумма wintering: {wintering_sum}")

with open(finish_output_json, "w", encoding="utf-8") as f:
    json.dump(normalized_data, f, ensure_ascii=False, indent=4)

print(f"✅ Нормализованные данные сохранены в {output_json}")