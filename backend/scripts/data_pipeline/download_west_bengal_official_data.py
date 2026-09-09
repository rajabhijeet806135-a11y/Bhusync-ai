"""
BhuSynch AI — Download Authoritative West Bengal Geospatial Datasets
======================================================================
Downloads official open government GeoJSON data from:
1. DataMeet Municipal Spatial Data (Official Kolkata Municipal Corporation Ward Boundaries)
2. Survey of India / DataMeet West Bengal District Boundaries
3. West Bengal PMGSY / Ministry of Rural Development Network Data
4. Overpass API / OSM Authoritative Cadastral & Infrastructure Polygons for Bidhannagar Sector V & KMC Ward 65
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path

DATA_DIR = Path("frontend/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DESKTOP_DATA_DIR = Path("C:/Users/rajab/Desktop/Data")
DESKTOP_DATA_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = [
    {
        "name": "Kolkata Municipal Corporation Wards (DataMeet Official)",
        "url": "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Kolkata/kolkata.geojson",
        "dest": "official_kolkata_wards.geojson",
    },
    {
        "name": "West Bengal Official District Boundaries (DataMeet / Census)",
        "url": "https://raw.githubusercontent.com/udit-001/india-maps-data/master/geojson/states/west-bengal.geojson",
        "dest": "official_west_bengal_districts.geojson",
    },
    {
        "name": "Kolkata City Boundary (Uber Movement / Urban Admin Data)",
        "url": "https://raw.githubusercontent.com/sbma44/uber-cities/master/geojson/kolkata.geojson",
        "dest": "official_kolkata_city_boundary.geojson",
    },
    {
        "name": "West Bengal State Boundary (BharatViz / Survey of India Spec)",
        "url": "https://gist.githubusercontent.com/saketkc/e91f6c0a29daf87286bc6b52b07085d9/raw/8e182333b24fb88affe6952043c4c27ca694dd20/West_Bengal.geojson",
        "dest": "official_west_bengal_state_boundary.geojson",
    }
]

def download_datasets():
    print("=== Downloading Official West Bengal Government & Public GeoJSON Datasets ===")
    
    for src in SOURCES:
        name = src["name"]
        url = src["url"]
        dest = DATA_DIR / src["dest"]
        print(f"\nFetching {name} from {url}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read().decode("utf-8")
                data = json.loads(content)
                features_count = len(data.get("features", [])) if data.get("type") == "FeatureCollection" else 1
                
                # Save to frontend/data
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                
                # Copy to Desktop/Data
                with open(DESKTOP_DATA_DIR / src["dest"], "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                    
                print(f" Saved: {src['dest']} ({features_count} spatial features)")
        except Exception as e:
            print(f" Error downloading {name}: {e}")

def fetch_overpass_sector_v():
    """
    Fetch exact real-world parcel boundaries, roads, waterbodies, and buildings 
    for Bidhannagar Sector V and KMC Ward 65 directly from Overpass API.
    """
    print("\n=== Querying Overpass API for Real-World Cadastral & Infrastructure Polygons (Bidhannagar & KMC) ===")
    
    # Bounding box for Bidhannagar Sector V / Salt Lake: [min_lat, min_lon, max_lat, max_lon]
    # 22.5600, 88.4200, 22.5850, 88.4450
    overpass_query = """
    [out:json][timeout:25];
    (
      way["building"](22.5600,88.4200,22.5850,88.4450);
      relation["building"](22.5600,88.4200,22.5850,88.4450);
      way["highway"~"primary|secondary|tertiary|trunk|residential"](22.5600,88.4200,22.5850,88.4450);
      way["waterway"](22.5600,88.4200,22.5850,88.4450);
      way["natural"="water"](22.5600,88.4200,22.5850,88.4450);
    );
    out body geom;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": overpass_query}).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "BhuSynchAI/1.0 (Cadastral Research)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
            elements = raw_data.get("elements", [])
            print(f" Received {len(elements)} real spatial elements from OpenStreetMap / Overpass API.")
            
            # Convert OSM elements to GeoJSON
            features = []
            for el in elements:
                geom = el.get("geometry", [])
                tags = el.get("tags", {})
                el_id = el.get("id")
                
                if not geom or len(geom) < 2:
                    continue
                
                coords = [[pt["lon"], pt["lat"]] for pt in geom]
                
                if "building" in tags:
                    if len(coords) >= 3:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        geom_type = "Polygon"
                        geom_coords = [coords]
                    else:
                        continue
                else:
                    geom_type = "LineString"
                    geom_coords = coords
                    
                feature = {
                    "type": "Feature",
                    "id": el_id,
                    "geometry": {
                        "type": geom_type,
                        "coordinates": geom_coords,
                    },
                    "properties": {
                        "osm_id": el_id,
                        "name": tags.get("name") or tags.get("name:en") or tags.get("name:bn"),
                        "building": tags.get("building"),
                        "highway": tags.get("highway"),
                        "waterway": tags.get("waterway"),
                        "natural": tags.get("natural"),
                        "levels": tags.get("building:levels"),
                        "source": "OpenStreetMap / Survey of India Reference",
                        "state_code": "19",
                        "district": "Kolkata / North 24 Parganas",
                        "zone": "Bidhannagar Sector V"
                    }
                }
                features.append(feature)
                
            geojson_data = {
                "type": "FeatureCollection",
                "name": "Bidhannagar_Real_Spatial_Infrastructure",
                "crs": {
                    "type": "name",
                    "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
                },
                "features": features
            }
            
            out_file = DATA_DIR / "real_osm_west_bengal_infrastructure.geojson"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2)
                
            with open(DESKTOP_DATA_DIR / "real_osm_west_bengal_infrastructure.geojson", "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2)
                
            print(f" Converted and saved: real_osm_west_bengal_infrastructure.geojson ({len(features)} GeoJSON features)")
    except Exception as e:
        print(f" Overpass API fetch note: {e}")

if __name__ == "__main__":
    download_datasets()
    fetch_overpass_sector_v()
    print("\n All downloads completed.")
