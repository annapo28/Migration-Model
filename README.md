# Migration-Model

Исследование на тему: "Метод моделировании миграции птиц на основе  данных общественных наблюдений (eBird)."

1. ebird_to_json:

   Данные я беру из eBrid: от для american woodcock : https://science.ebird.org/ru/status-and-trends/species/amewoo/downloads?week=1
   там надо запрашивать доступ для скачивания, его быстро дают

   Преобразую в json

2. abundance_from_tif

   Я беру по той же ссылке tif-файлы плотностей распределний и перевожу в плотности по квадратам карты

3. building_grid

   Делю карту на сетку и присваиваю наблюдения квадратам сетки

4. get_coordinates

   Строю маршруты

5. model

   Алгоритм модели, получение альфа для разныех моделей миграции

6. phi_parametr

   Учет цепной модели

7. tracked_data, сsv

   Из Movebank я взяла лчшие, какие нашла, треки для этого вальдшнепа (https://www.movebank.org/cms/webapp?gwt_fragment=page%3Dsearch_map), сделала csv-маршрутов для валидации

8. В ноутбуках визуализации для wood thrush  american woodcock.


