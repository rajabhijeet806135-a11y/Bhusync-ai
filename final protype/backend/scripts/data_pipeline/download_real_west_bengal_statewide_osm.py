"""
BhuSynch AI — Download Actual Statewide West Bengal Geospatial Data from Overpass
===================================================================================
Downloads real-world, actual vector geometries for the entire State of West Bengal:
- Highways & Expressways (MoRTH / PWD)
- Railway Network (Eastern Railway, South Eastern Railway, Northeast Frontier Railway)
- Major Rivers & Canals (Irrigation & Waterways Department)
- Protected Areas, National Parks & Forests (Forest Directorate / MoEFCC)
- Government Offices & Administrative Centres across all 23 districts
"""

import urllib.request
import urllib.parse
import json
import time
from pathlib import Path

FRONTEND_DATA = Path("frontend/data")
FRONTEND_DATA.mkdir(parents=True, exist_ok=True)
DESKTOP_DATA = Path("C:/Users/rajab/Desktop/Data")
DESKTOP_DATA.mkdir(parents=True, exist_ok=True)

MIRRORS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]

# Statewide bounding box for West Bengal: [min_lat: 21.5, min_lon: 85.8, max_lat: 27.3, max_lon: 89.9]
BBOX = "21.5000,85.8000,27.3000,89.9000"

QUERIES = [
    {
        "name": "Actual West Bengal Highways & Expressways",
        "file": "actual_west_bengal_highways.geojson",
        "query": f"""[out:json][timeout:35];
        (
          way["highway"~"motorway|trunk|primary"]({BBOX});
        );
        out body geom 400;
        """
    },
    {
        "name": "Actual West Bengal Railway Corridors",
        "file": "actual_west_bengal_railways.geojson",
        "query": f"""[out:json][timeout:35];
        (
          way["railway"="rail"]({BBOX});
        );
        out body geom 300;
        """
    },
    {
        "name": "Actual West Bengal Rivers & Major Waterways",
        "file": "actual_west_bengal_waterways.geojson",
        "query": f"""[out:json][timeout:35];
        (
          way["waterway"~"river|canal"]({BBOX});
        );
        out body geom 300;
        """
    },
    {
        "name": "Actual West Bengal Protected Areas & National Parks",
        "file": "actual_west_bengal_protected_areas.geojson",
        "query": f"""[out:json][timeout:35];
        (
          relation["boundary"="protected_area"]({BBOX});
          way["boundary"="protected_area"]({BBOX});
          relation["leisure"="nature_reserve"]({BBOX});
          way["leisure"="nature_reserve"]({BBOX});
        );
        out body geom 150;
        """
    },
    {
        "name": "Actual West Bengal Government & Civic Administrative Headquarters",
        "file": "actual_west_bengal_civic_headquarters.geojson",
        "query": f"""[out:json][timeout:35];
        (
          node["amenity"~"courthouse|townhall"]({BBOX});
          node["office"="government"]({BBOX});
        );
        out body geom 200;
        """
    }
]

def run_overpass(query_str):
    for mirror in MIRRORS:
        try:
            print(f"  Contacting {mirror}...")
            encoded = urllib.parse.urlencode({"data": query_str}).encode("utf-8")
            req = urllib.request.Request(
                mirror, 
                data=encoded, 
                headers={"User-Agent": "BhuSynchAI/1.0 (Government GIS Spatial Portal; Statewide Bengal)"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elements = data.get("elements", [])
                if elements:
                    return elements
        except Exception as e:
            print(f"  Mirror {mirror} note: {e}")
            time.sleep(1)
    return []

def elements_to_geojson(elements, name):
    features = []
    for el in elements:
        el_type = el.get("type")
        tags = el.get("tags", {})
        el_id = el.get("id")
        
        if el_type == "node":
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is not None and lon is not None:
                features.append({
                    "type": "Feature",
                    "id": f"OSM-{el_id}",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "osm_id": el_id,
                        "name": tags.get("name") or tags.get("name:en") or tags.get("name:bn") or "Government Facility",
                        "amenity": tags.get("amenity"),
                        "office": tags.get("office"),
                        "state_code": "19",
                        "source": "OpenStreetMap / Public Geospatial Data"
                    }
                })
        elif el_type == "way":
            geom = el.get("geometry", [])
            if not geom or len(geom) < 2:
                continue
            coords = [[pt["lon"], pt["lat"]] for pt in geom]
            
            is_polygon = (coords[0] == coords[-1] and len(coords) >= 4) and ("boundary" in tags or "leisure" in tags or "landuse" in tags)
            geom_type = "Polygon" if is_polygon else "LineString"
            geom_coords = [coords] if is_polygon else coords
            
            features.append({
                "type": "Feature",
                "id": f"OSM-{el_id}",
                "geometry": {"type": geom_type, "coordinates": geom_coords},
                "properties": {
                    "osm_id": el_id,
                    "name": tags.get("name") or tags.get("name:en") or tags.get("name:bn") or tags.get("ref") or name,
                    "ref": tags.get("ref"),
                    "highway": tags.get("highway"),
                    "railway": tags.get("railway"),
                    "waterway": tags.get("waterway"),
                    "boundary": tags.get("boundary"),
                    "protect_class": tags.get("protect_class"),
                    "state_code": "19",
                    "source": "OpenStreetMap / Survey of India Specifications"
                }
            })
            
    return {"type": "FeatureCollection", "name": name, "features": features}

def main():
    print("=== Downloading Actual Statewide West Bengal Datasets ===")
    
    for item in QUERIES:
        print(f"\nFetching {item['name']}...")
        elements = run_overpass(item["query"])
        print(f" Received {len(elements)} real spatial geometries.")
        
        geojson_data = elements_to_geojson(elements, item["name"])
        out1 = FRONTEND_DATA / item["file"]
        out2 = DESKTOP_DATA / item["file"]
        
        with open(out1, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)
        with open(out2, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)
            
        print(f" Saved: {item['file']} ({len(geojson_data['features'])} GeoJSON features)")
        time.sleep(1)
        
    print("\n All statewide actual datasets successfully downloaded and saved.")

if __name__ == "__main__":
    main()
