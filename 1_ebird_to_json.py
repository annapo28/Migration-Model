import json
from datetime import datetime

TXT_FILE = "/home/anya2812/Загрузки/ebd_amewoo_201612_202412_smp_relFeb-2025.txt"
JSON_FILE = "/home/anya2812/Migration-Model/amewoo/data_final_2017.json"

def get_season(event_date):
    try:
        date = datetime.strptime(event_date, "%Y-%m-%d")
        month, day = date.month, date.day

        if (month == 5 and day >= 31) or month in [6, 7] or (month == 8 and day <= 23):
            return "breeding"
        elif (month == 11 and day >= 22) or month in [12, 1] or (month == 3 and day <= 8):
            return "wintering"
        else:
            return "migration"
    except ValueError:
        return "unknown"

def convert_txt_to_json_2017():
    with open(TXT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    headers = lines[0].strip().split("\t")
    lat_index = headers.index("LATITUDE")
    lon_index = headers.index("LONGITUDE")
    date_index = headers.index("OBSERVATION DATE")

    results = []

    for line in lines[1:]:
        columns = line.strip().split("\t")

        latitude = columns[lat_index]
        longitude = columns[lon_index]
        event_date = columns[date_index]

        if not latitude or not longitude or not event_date:
            continue

        if event_date.startswith("2017"):
            season = get_season(event_date)

            results.append({
                "latitude": float(latitude),
                "longitude": float(longitude),
                "eventDate": event_date,
                "season": season
            })


    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"✅ Успешно сохранено {len(results)} записей за 2017 год в {JSON_FILE}")

# Запуск скрипта
if __name__ == "__main__":
    convert_txt_to_json_2017()
