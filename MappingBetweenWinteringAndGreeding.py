import json
import numpy as np
import dash
from dash import dcc, html, Output, Input
import dash_leaflet as dl
from flask import Flask

# Загрузка данных
with open("edges_weight.json", "r", encoding="utf-8") as f:
    edges_weight_json = json.load(f)

# Преобразуем ключи обратно в кортежи
edges_weight = {}
for key, values in edges_weight_json.items():
    lat, lon = map(float, key.split(','))
    edges_weight[(lat, lon)] = [
        (float(to_lat), float(to_lon), float(weight)) for to_lat_lon, weight in values
        for to_lat, to_lon in [to_lat_lon.split(",")]
    ]


# Функция масштабирования значений uk
def scale_uk_log(uk, min_uk, max_uk):
    epsilon = 1e-10
    log_uk = np.log(uk + epsilon)
    log_min_uk = np.log(min_uk + epsilon)
    log_max_uk = np.log(max_uk + epsilon)
    return 0 if log_max_uk == log_min_uk else (log_uk - log_min_uk) / (log_max_uk - log_min_uk)


# Функция генерации элементов карты
def generate_map_elements(center_coord):
    if center_coord not in edges_weight:
        return []

    relevant_edges = edges_weight[center_coord]
    uk_values = [uk for (_, _, uk) in relevant_edges]
    min_uk, max_uk = min(uk_values), max(uk_values)

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
                weight=1
            )
        )

    # Добавляем синий квадрат вокруг выбранного центра
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


# Flask сервер
server = Flask(__name__)
app = dash.Dash(__name__, server=server)

# Список доступных координат
available_coords = list(edges_weight.keys())

# Интерфейс Dash
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


# Обновление карты
@app.callback(
    Output("migration-map", "children"),
    Input("coord-dropdown", "value")
)
def update_map(selected_coord):
    center_coord = tuple(map(float, selected_coord.strip("()").split(",")))
    return generate_map_elements(center_coord)


if __name__ == "__main__":
    app.run_server(debug=True)