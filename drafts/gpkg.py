import geopandas as gpd

# Укажите путь к вашему .gpkg файлу
gpkg_file = "/home/anya2812/Загрузки/woothr_range_2022.gpkg"

# Прочитайте файл и выведите список слоёв
layers = gpd.read_file(gpkg_file, layer=None)
print("Слои в файле GeoPackage:")
print(layers)
print(layers.info())
unique_seasons = layers['season'].unique()
print("Уникальные значения в столбце 'season':")
print(unique_seasons)