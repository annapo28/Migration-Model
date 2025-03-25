import pandas as pd
import numpy as np
import json
from math import radians, sin, cos, sqrt, atan2


# Функция для расчёта расстояния Haversine
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6371 * c  # Радиус Земли в км


# Загрузка данных из CSV
gps_data = pd.read_csv('/home/anya2812/Загрузки/USGS Woodcock Migration.csv')

# Предполагаем, что для каждой особи (individual-local-identifier) у нас есть несколько точек
gps_data = gps_data[['individual-local-identifier', 'location-long', 'location-lat']]
gps_data = gps_data.dropna()

# Создаём столбец 'coordinates' для хранения пары координат (широта, долгота)
gps_data['coordinates'] = list(zip(gps_data['location-lat'], gps_data['location-long']))

# Группируем данные по individual-local-identifier
individuals = gps_data.groupby('individual-local-identifier')['coordinates'].apply(list).to_dict()

# Создаём структуру для миграционных вероятностей
migration_probabilities = {}

# Проходим по каждой особи и генерируем вероятности прилета
for individual_id, coordinates in individuals.items():
    for i, (lat1, lon1) in enumerate(coordinates):
        for j, (lat2, lon2) in enumerate(coordinates):
            if i != j:
                # Вычисляем расстояние между двумя точками
                dist = haversine(lon1, lat1, lon2, lat2)
                # Считаем вероятность (чем ближе, тем выше вероятность)
                prob = 1 / (dist + 1.0)  # Просто примерный способ расчета вероятности

                # Формируем ключи для точек вылета (lat1, lon1) и прилета (lat2, lon2)
                departure_point = f"{lat1},{lon1}"
                arrival_point = f"{lat2},{lon2}"

                if departure_point not in migration_probabilities:
                    migration_probabilities[departure_point] = []

                migration_probabilities[departure_point].append((arrival_point, prob))

# Нормируем вероятности для каждой точки вылета
for departure_point, arrivals in migration_probabilities.items():
    total_prob = sum(prob for _, prob in arrivals)  # Сумма всех вероятностей для данной точки вылета
    if total_prob > 0:
        # Нормируем вероятности
        migration_probabilities[departure_point] = [
            (arrival_point, prob / total_prob) for arrival_point, prob in arrivals
        ]

# Преобразуем в формат JSON и сохраняем
with open('migration_probabilities_from_gps_normalized.json', 'w') as f:
    json.dump(migration_probabilities, f, indent=4)

print("Миграционные вероятности успешно сохранены и нормализованы!")
