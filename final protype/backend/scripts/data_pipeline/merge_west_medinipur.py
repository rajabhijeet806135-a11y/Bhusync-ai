import json

with open("frontend/data/statewide_west_bengal_cadastral_parcels.geojson", encoding="utf-8") as f:
    state_parcels = json.load(f)

with open("frontend/data/west_medinipur_cadastral_parcels.geojson", encoding="utf-8") as f:
    pmed_parcels = json.load(f)

# Filter any previous west-medinipur parcels
clean_features = [f for f in state_parcels["features"] if not str(f.get("id", "")).startswith("west-medinipur-dag-")]
clean_features.extend(pmed_parcels["features"])
state_parcels["features"] = clean_features

with open("frontend/data/statewide_west_bengal_cadastral_parcels.geojson", "w", encoding="utf-8") as f:
    json.dump(state_parcels, f, indent=2)

print("Updated statewide parcels. Total count:", len(clean_features))

# Now RoR records
with open("frontend/data/statewide_west_bengal_ror_records.json", encoding="utf-8") as f:
    state_ror = json.load(f)

with open("frontend/data/west_medinipur_ror_records.json", encoding="utf-8") as f:
    pmed_ror = json.load(f)

clean_ror = [r for r in state_ror if r.get("district") != "Paschim Medinipur"]
clean_ror.extend(pmed_ror)

with open("frontend/data/statewide_west_bengal_ror_records.json", "w", encoding="utf-8") as f:
    json.dump(clean_ror, f, indent=2)

print("Updated statewide RoRs. Total count:", len(clean_ror))
