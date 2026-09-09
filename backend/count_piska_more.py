import urllib.request
import urllib.parse
import json

# Bounding box for Piska More (Hehal, Pandra, ITI, Ratu Road junction, Sukhdeonagar)
PISKA_BBOX = (23.3650, 85.2750, 23.3950, 85.3200)

query = f"""[out:json][timeout:30];
(
  way["building"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
  way["highway"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
  node["amenity"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
  node["shop"]({PISKA_BBOX[0]},{PISKA_BBOX[1]},{PISKA_BBOX[2]},{PISKA_BBOX[3]});
);
out count;
"""

try:
    req = urllib.request.Request(
        "https://lz4.overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
        headers={"User-Agent": "BhuSynchAI/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("Count in Piska More BBOX:", json.dumps(data.get("elements", []), indent=2))
except Exception as e:
    print(f"Error: {e}")
