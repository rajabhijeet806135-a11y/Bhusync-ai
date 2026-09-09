import urllib.request
import urllib.parse
import json

PISKA_MORE_CORRIDOR = (23.3600, 85.2650, 23.4050, 85.3250)

query = f"""[out:json][timeout:60];
(
  way["building"]({PISKA_MORE_CORRIDOR[0]},{PISKA_MORE_CORRIDOR[1]},{PISKA_MORE_CORRIDOR[2]},{PISKA_MORE_CORRIDOR[3]});
  way["highway"]({PISKA_MORE_CORRIDOR[0]},{PISKA_MORE_CORRIDOR[1]},{PISKA_MORE_CORRIDOR[2]},{PISKA_MORE_CORRIDOR[3]});
  node["amenity"]({PISKA_MORE_CORRIDOR[0]},{PISKA_MORE_CORRIDOR[1]},{PISKA_MORE_CORRIDOR[2]},{PISKA_MORE_CORRIDOR[3]});
  node["shop"]({PISKA_MORE_CORRIDOR[0]},{PISKA_MORE_CORRIDOR[1]},{PISKA_MORE_CORRIDOR[2]},{PISKA_MORE_CORRIDOR[3]});
);
out body geom;
"""

mirrors = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter"
]

for mirror in mirrors:
    try:
        print(f"Trying {mirror} ...")
        req = urllib.request.Request(
            mirror,
            data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
            headers={"User-Agent": "BhuSynchAI/1.0 (Government GIS Research)"}
        )
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elements = data.get("elements", [])
            print(f"Success from {mirror}! Total elements fetched: {len(elements)}")
            buildings = [e for e in elements if "building" in e.get("tags", {})]
            highways = [e for e in elements if "highway" in e.get("tags", {})]
            amenities = [e for e in elements if "amenity" in e.get("tags", {}) or "shop" in e.get("tags", {})]
            print(f"Buildings: {len(buildings)}")
            print(f"Roads/Highways: {len(highways)}")
            print(f"Amenities & Shops: {len(amenities)}")
            if buildings:
                with open("backend/piska_raw.json", "w", encoding="utf-8") as f:
                    json.dump(data, f)
                print("Saved raw elements to backend/piska_raw.json")
                break
    except Exception as e:
        print(f"Error with {mirror}: {e}")
