import json
from math import radians, sin, cos, sqrt, asin

# Функция для расчёта расстояния по формуле хаверсинуса
def haversine(lat1, lon1, lat2, lon2):
    # Радиус Земли в километрах
    R = 6371.0

    # Преобразуем градусы в радианы
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Разница широт и долгот
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Формула хаверсинуса
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    # Расстояние
    distance = R * c
    return distance

# Загружаем данные из файла
with open('/home/anya2812/Migration-Model/migration_probabilities.json', 'r') as file:
    data = json.load(file)

# Извлекаем ключи (координаты клеток)
keys = list(data.keys())

# Преобразуем ключи в пары (широта, долгота)
coordinates = [tuple(map(float, key.split(','))) for key in keys]

# Находим максимальное расстояние
max_distance = 0

# Перебираем все пары клеток
for i in range(len(coordinates)):
    for j in range(i + 1, len(coordinates)):
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[j]

        # Рассчитываем расстояние
        distance = haversine(lat1, lon1, lat2, lon2)

        # Обновляем максимальное расстояние
        if distance > max_distance:
            max_distance = distance

# Выводим результат
print(f"Максимальное расстояние между клетками: {max_distance} км")