import json
import math

from math import floor

def find_cell(lat, lon):
    return f"{floor(lat) + 0.5},{floor(lon) + 0.5}"

def normalize_probabilities(prob_data):
    for start_cell, targets in prob_data.items():
        total_prob = sum(prob for _, prob in targets)
        if total_prob > 0:
            prob_data[start_cell] = [(target, prob / total_prob) for target, prob in targets]

with open('amewoo/chain_migration_weights.json', 'r') as f:
    chain_prob_data = json.load(f)

with open('amewoo/migration_probabilities.json', 'r') as f:
    prob_data = json.load(f)

with open('amewoo/wintering_to_breeding_routes.json', 'r') as f:
    raw_routes = json.load(f)

normalize_probabilities(chain_prob_data)
normalize_probabilities(prob_data)

# Разворачиваем JSON в список маршрутов
routes = []
for bird_id, bird_routes in raw_routes.items():
    routes.extend(bird_routes)

print(f"Всего маршрутов: {len(routes)}")  # Отладка

# Создаём таблицу
table_data = []

for route in routes:
    if 'start' in route and 'end' in route:
        start_lat, start_lon = route['start']['lat'], route['start']['lon']
        end_lat, end_lon = route['end']['lat'], route['end']['lon']

        start_cell = find_cell(start_lat, start_lon)
        end_cell = find_cell(end_lat, end_lon)

        prob_chain = 0
        log_chain = -float('inf')
        if start_cell in chain_prob_data:
            for target, prob in chain_prob_data[start_cell]:
                if target == end_cell:
                    prob_chain = prob
                    log_chain = math.log(prob_chain) if prob_chain > 0 else -float('inf')

        prob_migration = 0
        log_migration = -float('inf')
        if start_cell in prob_data:
            for target, prob in prob_data[start_cell]:
                if target == end_cell:
                    prob_migration = prob
                    log_migration = math.log(prob_migration) if prob_migration > 0 else -float('inf')

        route_info = [
            f"Start: ({start_lat}, {start_lon}) -> End: ({end_lat}, {end_lon})",
            f"{prob_migration:.10e}" if prob_migration > 0 else "0",
            f"{log_migration:.5f}" if log_migration > -float('inf') else "-inf",
            f"{prob_chain:.10e}" if prob_chain > 0 else "0",
            f"{log_chain:.5f}" if log_chain > -float('inf') else "-inf"
        ]

        table_data.append(route_info)

print(f"Собрано маршрутов: {len(table_data)}")

with open("amewoo/migration_routes_table.txt", "w", encoding="utf-8") as f:
    f.write("route\tprob\tlog\tprob_chain\tlog_chain\n")
    for row in table_data:
        f.write("\t".join(row) + "\n")

print("Таблица сохранена в migration_routes_table.txt")
