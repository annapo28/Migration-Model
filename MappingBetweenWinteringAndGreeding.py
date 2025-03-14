import json
import numpy as np
import dash
from dash import dcc, html, Output, Input
import dash_leaflet as dl
from dash_leaflet import Tooltip
from flask import Flask

with open("/home/anya2812/Migration-Model/migration_probabilities.json", "r", encoding="utf-8") as f:
    edges_weight_json = json.load(f)

edges_weight = {}
uk_min_max = {}
for key, values in edges_weight_json.items():
    lat, lon = map(float, key.split(','))
    edges_weight[(lat, lon)] = [
        (float(to_lat), float(to_lon), float(weight)) for to_lat_lon, weight in values
        for to_lat, to_lon in [to_lat_lon.split(",")]
    ]
    uk_values = [uk for (_, _, uk) in edges_weight[(lat, lon)]]
    uk_min_max[(lat, lon)] = (min(uk_values), max(uk_values))

def scale_uk_log(uk, min_uk, max_uk):
    if uk == min_uk:
        return 0
    epsilon = 1e-10
    log_uk = np.log(uk + epsilon)
    log_min_uk = np.log(min_uk + epsilon)
    log_max_uk = np.log(max_uk + epsilon)
    return (log_uk - log_min_uk) / (log_max_uk - log_min_uk) if log_max_uk != log_min_uk else 0

def generate_map_elements(center_coord):
    if center_coord not in edges_weight:
        return []

    relevant_edges = edges_weight[center_coord]
    min_uk, max_uk = uk_min_max[center_coord]

    rectangles = []
    for (to_lat, to_lon, uk) in relevant_edges:
        scaled_uk = scale_uk_log(uk, min_uk, max_uk)
        color_intensity = int(255 * scaled_uk)
        color = f'#ff{color_intensity:02x}00'

        rectangles.append(
            dl.Rectangle(
                bounds=[
                    [to_lat - 0.5, to_lon - 0.5],
                    [to_lat + 0.5, to_lon + 0.5]
                ],
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=1,
                children=Tooltip(f"UK: {uk:.6f}")  # Добавление всплывающей подсказки
            )
        )

    rectangles.append(
        dl.Rectangle(
            bounds=[
                [center_coord[0] - 0.5, center_coord[1] - 0.5],
                [center_coord[0] + 0.5, center_coord[1] + 0.5]
            ],
            color="blue",
            fill=False,
            weight=2
        )
    )

    return rectangles

server = Flask(__name__)
app = dash.Dash(__name__, server=server)

available_coords = list(edges_weight.keys())

app.layout = html.Div([
    html.H1("Миграционная карта"),
    html.Label("Выберите центр квадрата:"),
    dcc.Dropdown(
        id="coord-dropdown",
        options=[{"label": str(coord), "value": str(coord)} for coord in available_coords],
        value=str(available_coords[0])
    ),
    dl.Map(
        id="map",
        center=available_coords[0],
        zoom=6,
        children=[
            dl.TileLayer(),
            dl.LayerGroup(id="migration-map")
        ],
        style={"height": "600px"}
    )
])

@app.callback(
    Output("migration-map", "children"),
    Input("coord-dropdown", "value")
)
def update_map(selected_coord):
    center_coord = tuple(map(float, selected_coord.strip("()").split(",")))
    return generate_map_elements(center_coord)

if __name__ == "__main__":
    app.run_server(debug=True)
