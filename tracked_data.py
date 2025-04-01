import pandas as pd
import json
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6371 * c

def get_location_type(date_str):
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    month = date.month
    if 5 <= month <= 9:
        return 'breeding'
    else:
        return 'wintering'

df = pd.read_csv('/home/anya2812/Загрузки/USGS Woodcock Migration.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(['individual-local-identifier', 'timestamp'])

def find_migration_segments(points):
    segments = []
    current_segment = []
    prev_type = None

    for point in points:
        current_type = get_location_type(str(point['timestamp']))

        if prev_type is None:
            current_segment.append(point)
        elif current_type != prev_type:
            segments.append({
                'type': prev_type,
                'points': current_segment.copy()
            })
            current_segment = [point]
        else:
            current_segment.append(point)

        prev_type = current_type

    if current_segment:
        segments.append({
            'type': prev_type,
            'points': current_segment.copy()
        })

    return segments

wintering_to_breeding_routes = {}
breeding_to_wintering_routes = {}

for bird_id, group in df.groupby('individual-local-identifier'):
    points = [{
        'lat': row['location-lat'],
        'lon': row['location-long'],
        'timestamp': row['timestamp']
    } for _, row in group.iterrows()]

    segments = find_migration_segments(points)

    for i in range(len(segments) - 1):
        start_segment = segments[i]
        end_segment = segments[i + 1]

        # Wintering → Breeding
        if start_segment['type'] == 'wintering' and end_segment['type'] == 'breeding':
            start_point = min(start_segment['points'], key=lambda x: (x['lat'], -x['lon']))
            end_point = max(end_segment['points'], key=lambda x: (x['lat'], -x['lon']))

            if bird_id not in wintering_to_breeding_routes:
                wintering_to_breeding_routes[bird_id] = []

            wintering_to_breeding_routes[bird_id].append({
                'start': {
                    'lat': start_point['lat'],
                    'lon': start_point['lon'],
                    'timestamp': str(start_point['timestamp'])
                },
                'end': {
                    'lat': end_point['lat'],
                    'lon': end_point['lon'],
                    'timestamp': str(end_point['timestamp'])
                },
                'duration_days': (end_point['timestamp'] - start_point['timestamp']).days,
                'distance_km': haversine(
                    start_point['lon'], start_point['lat'],
                    end_point['lon'], end_point['lat']
                )
            })

        # Breeding → Wintering
        elif start_segment['type'] == 'breeding' and end_segment['type'] == 'wintering':
            start_point = max(start_segment['points'], key=lambda x: (x['lat'], -x['lon']))
            end_point = min(end_segment['points'], key=lambda x: (x['lat'], -x['lon']))

            if bird_id not in breeding_to_wintering_routes:
                breeding_to_wintering_routes[bird_id] = []

            breeding_to_wintering_routes[bird_id].append({
                'start': {
                    'lat': start_point['lat'],
                    'lon': start_point['lon'],
                    'timestamp': str(start_point['timestamp'])
                },
                'end': {
                    'lat': end_point['lat'],
                    'lon': end_point['lon'],
                    'timestamp': str(end_point['timestamp'])
                },
                'duration_days': (end_point['timestamp'] - start_point['timestamp']).days,
                'distance_km': haversine(
                    start_point['lon'], start_point['lat'],
                    end_point['lon'], end_point['lat']
                )
            })

with open('amewoo/wintering_to_breeding_routes.json', 'w') as f:
    json.dump(wintering_to_breeding_routes, f, indent=4)

with open('amewoo/breeding_to_wintering_routes.json', 'w') as f:
    json.dump(breeding_to_wintering_routes, f, indent=4)

print(f'Найдено маршрутов:')
print(f'- Wintering → Breeding: {sum(len(v) for v in wintering_to_breeding_routes.values())}')
print(f'- Breeding → Wintering: {sum(len(v) for v in breeding_to_wintering_routes.values())}')