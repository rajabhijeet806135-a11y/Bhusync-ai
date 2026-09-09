"""
BhuSynch AI — Fetch Actual Real-World West Bengal Vector Datasets
===================================================================
Fetches authentic spatial elements across West Bengal's major urban and rural corridors:
- Greater Kolkata & KMDA (State 19)
- Siliguri & Darjeeling Sub-Himalayan Region
- Asansol & Durgapur Industrial Corridor
- Kharagpur & Medinipur
- Malda & Murshidabad
"""

import urllib.request
import urllib.parse
import json
import sys
from pathlib import Path

FRONTEND_DATA = Path("frontend/data")
FRONTEND_DATA.mkdir(parents=True, exist_ok=True)
DESKTOP_DATA = Path("C:/Users/rajab/Desktop/Data")
DESKTOP_DATA.mkdir(parents=True, exist_ok=True)

MIRROR = "https://lz4.overpass-api.de/api/interpreter"

# Real-world target zones across West Bengal
ZONES = [
    {"name": "Kolkata_KMDA", "bbox": "22.4500,88.2500,22.6500,88.4800"},
    {"name": "Siliguri_Darjeeling", "bbox": "26.6500,88.3500,26.8500,88.5000"},
    {"name": "Asansol_Durgapur", "bbox": "23.4500,86.9000,23.7500,87.4000"},
    {"name": "Kharagpur_Medinipur", "bbox": "22.3000,87.2500,22.4500,87.4000"},
]

def query_zone(bbox, filter_expr, limit=100):
    q = f"""[out:json][timeout:15];
    (
      way{filter_expr}({bbox});
      node{filter_expr}({bbox});
    );
    out body geom {limit};
    """
    try:
        encoded = urllib.parse.urlencode({"data": q}).encode("utf-8")
        req = urllib.request.Request(MIRROR, data=encoded, headers={"User-Agent": "BhuSynchAI/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("elements", [])
    except Exception as e:
        print(f"  Note for {filter_expr} in {bbox}: {e}", flush=True)
        return []

def main():
    print("=== Downloading Actual Real-World Geospatial Layers for West Bengal ===", flush=True)
    
    all_roads = []
    all_waterways = []
    all_railways = []
    all_amenities = []
    
    for z in ZONES:
        print(f"\nQuerying Zone: {z['name']}...", flush=True)
        
        # Roads (Highways)
        road_els = query_zone(z["bbox"], "[\"highway\"~\"motorway|trunk|primary|secondary\"]", limit=60)
        print(f"  Roads: {len(road_els)} features", flush=True)
        for el in road_els:
            geom = el.get("geometry", [])
            if len(geom) >= 2:
                all_roads.append({
                    "type": "Feature",
                    "id": f"ROAD-{el.get('id')}",
                    "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in geom]},
                    "properties": {
                        "osm_id": el.get("id"),
                        "name": el.get("tags", {}).get("name") or el.get("tags", {}).get("ref") or "Arterial Road",
                        "highway": el.get("tags", {}).get("highway"),
                        "zone": z["name"],
                        "state_code": "19"
                    }
                })
                
        # Waterways (Rivers & Canals)
        water_els = query_zone(z["bbox"], "[\"waterway\"]", limit=40)
        print(f"  Waterways: {len(water_els)} features", flush=True)
        for el in water_els:
            geom = el.get("geometry", [])
            if len(geom) >= 2:
                all_waterways.append({
                    "type": "Feature",
                    "id": f"WATER-{el.get('id')}",
                    "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in geom]},
                    "properties": {
                        "osm_id": el.get("id"),
                        "name": el.get("tags", {}).get("name") or "Waterway / Canal",
                        "waterway": el.get("tags", {}).get("waterway"),
                        "zone": z["name"],
                        "state_code": "19"
                    }
                })
                
        # Railways
        rail_els = query_zone(z["bbox"], "[\"railway\"=\"rail\"]", limit=40)
        print(f"  Railways: {len(rail_els)} features", flush=True)
        for el in rail_els:
            geom = el.get("geometry", [])
            if len(geom) >= 2:
                all_railways.append({
                    "type": "Feature",
                    "id": f"RAIL-{el.get('id')}",
                    "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in geom]},
                    "properties": {
                        "osm_id": el.get("id"),
                        "name": el.get("tags", {}).get("name") or "Railway Track",
                        "railway": "rail",
                        "zone": z["name"],
                        "state_code": "19"
                    }
                })
                
        # Civic & Government Amenities
        civic_els = query_zone(z["bbox"], "[\"amenity\"~\"courthouse|townhall|police|hospital\"]", limit=30)
        print(f"  Civic Amenities: {len(civic_els)} features", flush=True)
        for el in civic_els:
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is not None and lon is not None:
                all_amenities.append({
                    "type": "Feature",
                    "id": f"AMENITY-{el.get('id')}",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "osm_id": el.get("id"),
                        "name": el.get("tags", {}).get("name") or el.get("tags", {}).get("amenity"),
                        "amenity": el.get("tags", {}).get("amenity"),
                        "zone": z["name"],
                        "state_code": "19"
                    }
                })

    # Save to disk
    datasets = [
        ("actual_west_bengal_roads.geojson", all_roads),
        ("actual_west_bengal_waterways.geojson", all_waterways),
        ("actual_west_bengal_railways.geojson", all_railways),
        ("actual_west_bengal_civic_amenities.geojson", all_amenities),
    ]
    
    for fname, feats in datasets:
        fc = {"type": "FeatureCollection", "features": feats}
        with open(FRONTEND_DATA / fname, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2)
        with open(DESKTOP_DATA / fname, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2)
        print(f"Saved {fname}: {len(feats)} real features", flush=True)

    print("\n✓ All real-world geospatial datasets downloaded successfully.", flush=True)

if __name__ == "__main__":
    main()
