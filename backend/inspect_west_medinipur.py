import json

with open("frontend/data/west_medinipur_cadastral_parcels.geojson", encoding="utf-8") as f:
    d = json.load(f)
print("West Medinipur Parcels:", len(d["features"]))
for feat in d["features"][:4]:
    p = feat["properties"]
    print(" - Dag:", p["dag_no"], "| ULPIN:", p["ulpin"], "| Mouza:", p["mouza_name"], "| Owner:", p["owner_name"][:35], "| Area:", p["legal_area_sqm"], "sqm")

with open("frontend/data/west_medinipur_infrastructure.geojson", encoding="utf-8") as f:
    inf = json.load(f)
print("\nWest Medinipur Infrastructure:", len(inf["features"]))
for feat in inf["features"][:5]:
    p = feat["properties"]
    print(" -", p["infrastructure_type"], ":", p["name"])
