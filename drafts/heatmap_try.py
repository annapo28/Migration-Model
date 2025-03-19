import json
import numpy as np
import dash
from dash import dcc, html, Output, Input
import plotly.graph_objects as go
import pandas as pd
from flask import Flask

# Загрузка данных
with open("../edges_weight.json", "r", encoding="utf-8") as f:
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


# Функция подготовки данных для тепловой карты
def generate_heatmap_data():
    heatmap_data = []

    for center_coord, edges in edges_weight.items():
        for (to_lat, to_lon, uk) in edges:
            scaled_uk = scale_uk_log(uk, min_uk=0, max_uk=1)
            heatmap_data.append([to_lat, to_lon, scaled_uk])

    return heatmap_data


# Flask сервер
server = Flask(__name__)

# Dash приложение
app = dash.Dash(__name__, server=server)

app.layout = html.Div([
    html.H1("HeatMap для uk с использованием Plotly"),
    html.Label("Выберите центр квадрата:"),
    dcc.Dropdown(
        id="coord-dropdown",
        options=[{"label": str(coord), "value": str(coord)} for coord in edges_weight.keys()],
        value=str(list(edges_weight.keys())[0])
    ),
    dcc.Graph(id="heatmap-graph", style={"height": "700px"})
])


# Функция обновления карты
@app.callback(
    Output("heatmap-graph", "figure"),
    Input("coord-dropdown", "value")
)
def update_heatmap(selected_coord):
    heatmap_data = generate_heatmap_data()

    df = pd.DataFrame(heatmap_data, columns=["Latitude", "Longitude", "Weight"])

    fig = go.Figure(go.Densitymapbox(
        lat=df["Latitude"],
        lon=df["Longitude"],
        z=df["Weight"],
        radius=20,
        colorscale="YlOrRd",
        zmin=0,
        zmax=1
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=np.mean(df["Latitude"]), lon=np.mean(df["Longitude"])),
            zoom=5
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
