import pandas as pd


buildings = pd.read_csv("OSM/OSM_buildings.csv")
cate = buildings["category"].unique()
category ={}
for c in cate:
    category[c] = "|".join(buildings[buildings["category"]==c]["tag"].values)



CATEGORY = category
OVERPASS_URL = "http://overpass-api.de/api/interpreter"
