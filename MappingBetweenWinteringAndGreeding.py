import folium
import json


with open("/home/anya2812/Migration-Model/grid_data.json", "r", encoding="utf-8") as f:
    grid_data = json.load(f)

with open("/home/anya2812/Migration-Model/output_densities.json", "r", encoding="utf-8") as f:
    uk_data = json.load(f)

m = folium.Map(location=[30, -90], zoom_start=3)

def get_color(uk_value, min_uk, max_uk):
    normalized = (uk_value - min_uk) / (max_uk - min_uk)
    return f"#ff{int(255 * (1 - normalized)):02x}{int(255 * (1 - normalized)):02x}"

min_uk = min(route["uk"] for route in uk_data)
max_uk = max(route["uk"] for route in uk_data)

for cell in grid_data:
    if cell["season"] == "wintering":
        folium.Rectangle(
            bounds=[[cell["latitude"] - 0.5, cell["longitude"] - 0.5], [cell["latitude"] + 0.5, cell["longitude"] + 0.5]],
            color="blue",
            fill=True,
            fill_opacity=0.5,
            weight=1,
        ).add_to(m)

for route in uk_data:
    from_coords = (route["from"]["latitude"], route["from"]["longitude"])
    to_coords = (route["to"]["latitude"], route["to"]["longitude"])
    uk_value = route["uk"]

    color = get_color(uk_value, min_uk, max_uk)

    folium.Rectangle(
        bounds=[[to_coords[0] - 0.5, to_coords[1] - 0.5], [to_coords[0] + 0.5, to_coords[1] + 0.5]],
        color=color,
        fill=True,
        fill_opacity=0.8,
        weight=1,
    ).add_to(m)

m.save("migration_map.html")
print("Карта сохранена в файл migration_map.html")