import urllib.request
import urllib.parse
import json
from pathlib import Path

mirrors = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]

query = """[out:json][timeout:25];
(
  way["building"](22.5650,88.4250,22.5780,88.4400);
  way["highway"](22.5650,88.4250,22.5780,88.4400);
);
out body geom 250;
"""

def fetch():
    for mirror in mirrors:
        try:
            print(f"Trying {mirror}...")
            encoded_query = urllib.parse.urlencode({"data": query}).encode("utf-8")
            req = urllib.request.Request(mirror, data=encoded_query, headers={"User-Agent": "BhuSynchAI/1.0 (Government GIS Research)"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elements = data.get("elements", [])
                print(f"Success from {mirror}! Got {len(elements)} real spatial elements.")
                
                features = []
                for el in elements:
                    geom = el.get("geometry", [])
                    tags = el.get("tags", {})
                    if not geom or len(geom) < 2:
                        continue
                    coords = [[pt["lon"], pt["lat"]] for pt in geom]
                    if "building" in tags and len(coords) >= 3:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        gtype = "Polygon"
                        gcoords = [coords]
                    else:
                        gtype = "LineString"
                        gcoords = coords
                    features.append({
                        "type": "Feature",
                        "id": el.get("id"),
                        "geometry": {"type": gtype, "coordinates": gcoords},
                        "properties": {
                            "osm_id": el.get("id"),
                            "name": tags.get("name") or tags.get("name:en") or "Plot Structure",
                            "building": tags.get("building"),
                            "highway": tags.get("highway"),
                            "state_code": "19",
                            "district": "North 24 Parganas / Kolkata",
                            "zone": "Bidhannagar Sector V"
                        }
                    })
                
                geojson_out = {"type": "FeatureCollection", "features": features}
                out1 = Path("frontend/data/official_osm_bidhannagar_elements.geojson")
                out2 = Path("C:/Users/rajab/Desktop/Data/official_osm_bidhannagar_elements.geojson")
                
                with open(out1, "w", encoding="utf-8") as f:
                    json.dump(geojson_out, f, indent=2)
                with open(out2, "w", encoding="utf-8") as f:
                    json.dump(geojson_out, f, indent=2)
                    
                print(f"Saved {out1} and {out2} with {len(features)} real-world spatial geometries.")
                return True
        except Exception as e:
            print(f"Mirror {mirror} failed: {e}")
    return False

if __name__ == "__main__":
    fetch()
