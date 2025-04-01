import json
from math import radians, sin, cos, sqrt, asin

# file_path = 'wood_thrush/migration_probabilities.json'
# file_path_fall = 'wood_thrush/migration_probabilities_fall.json'
# OUTPUT_SPRING = '/home/anya2812/Migration-Model/wood_thrush/chain_migration_routes.json'
# OUTPUT_FALL = '/home/anya2812/Migration-Model/wood_thrush/chain_migration_routes_fall.json'

file_path = 'amewoo/migration_probabilities.json'
file_path_fall = 'amewoo/migration_probabilities_fall.json'
OUTPUT_SPRING = '/home/anya2812/Migration-Model/amewoo/chain_migration_routes.json'
OUTPUT_FALL = '/home/anya2812/Migration-Model/amewoo/chain_migration_routes_fall.json'


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c

def find_max_distance_between_keys(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    coordinates = [tuple(map(float, key.split(','))) for key in data.keys()]
    print(coordinates)
    max_d = 0
    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            lat1, lon1 = coordinates[i]
            lat2, lon2 = coordinates[j]
            d = haversine(lat1, lon1, lat2, lon2)
            if d > max_d:
                max_d = d

    return max_d

max_distance = find_max_distance_between_keys(file_path)
max_distance_fall = find_max_distance_between_keys(file_path_fall)

print(f"Максимальное расстояние между ключами: {max_distance:.2f} км", max_distance_fall)


import json
from math import radians, sin, cos, sqrt, asin

def calculate_penalty(l, max_d, min_l, max_l):
    normalized_lat = (max_l - l) / (max_l - min_l)
    p = max_d * (1 - normalized_lat)
    return p

def calculate_penalty_fall(l, max_d, min_l, max_l):
    normalized_lat = (l - min_l) / (max_l - min_l)
    p = max_d * (1 - normalized_lat)
    return p

def sort_migration_routes(routes):
    return sorted(routes, key=lambda r: (r[2][0], r[1][0]))

with open('amewoo/sorted_migration_routes.json', 'r') as file:
    sorted_migration_routes = json.load(file)
with open('amewoo/sorted_migration_routes_fall.json', 'r') as file:
    sorted_migration_routes_fall = json.load(file)

min_lat = min(route[0][0] for route in sorted_migration_routes)
max_lat = max(route[0][0] for route in sorted_migration_routes)

min_lat_fall = min(route[0][0] for route in sorted_migration_routes_fall)
max_lat_fall = max(route[0][0] for route in sorted_migration_routes_fall)

print(min_lat_fall, max_lat_fall, min_lat, max_lat)

updated_routes = []
for route in sorted_migration_routes:
    lat, lon = route[0]
    distance, prob1, prob2, n_k, idx = route[2]
    penalty = calculate_penalty(lat, max_distance, min_lat, max_lat)
    updated_distance = distance + penalty
    updated_route = [
        [lat, lon],
        route[1],
        [updated_distance, prob1, prob2, n_k, idx]
    ]
    updated_routes.append(updated_route)

    if lat == 28.5 and lon == -81.5:
        print(lat, lon)
        print(distance)
        print(updated_distance)
        print('_' * 60)


updated_routes_fall = []

for route in sorted_migration_routes_fall:
    lat, lon = route[0]
    distance, prob1, prob2, n_k, idx = route[2]
    penalty = calculate_penalty_fall(lat, max_distance_fall, min_lat_fall, max_lat_fall)
    updated_distance = distance + penalty
    updated_route = [
        [lat, lon],
        route[1],
        [updated_distance, prob1, prob2, n_k, idx]
    ]
    updated_routes_fall.append(updated_route)

print(max_lat_fall, min_lat_fall)

sorted_updated_routes = sort_migration_routes(updated_routes)
sorted_updated_routes_fall = sort_migration_routes(updated_routes_fall)

with open(OUTPUT_SPRING, 'w') as file:
    json.dump(sorted_updated_routes, file, indent=4)
with open(OUTPUT_FALL, 'w') as file:
    json.dump(sorted_updated_routes_fall, file, indent=4)

print(max_distance, max_distance_fall)

print("Файл chain_migration_routes.json успешно создан!")
print("Файл chain_migration_routes_fall.json успешно создан!")

