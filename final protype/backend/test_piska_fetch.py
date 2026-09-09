import urllib.request
import urllib.parse
import json

PISKA_BBOX = (23.3720, 85.2820, 23.3900, 85.3080)

query = f"""[out:json][timeout:35];
(
  way["building"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
  way["highway"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
  node["amenity"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
  node["shop"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
);
out body geom 800;
"""

mirrors = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]

for m in mirrors:
    try:
        print(f"Trying {m} ...")
        req = urllib.request.Request(
            m,
            data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
            headers={"User-Agent": "BhuSynchAI/1.0"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elements = data.get("elements", [])
            print(f"Success from {m}! Retrieved {len(elements)} elements.")
            buildings = [e for e in elements if "building" in e.get("tags", {})]
            highways = [e for e in elements if "highway" in e.get("tags", {})]
            amenities = [e for e in elements if "amenity" in e.get("tags", {}) or "shop" in e.get("tags", {})]
            print(f"Buildings: {len(buildings)}, Highways/Roads: {len(highways)}, Amenities/Shops: {len(amenities)}")
            if buildings:
                break
    except Exception as e:
        print(f"Failed {m}: {e}")
