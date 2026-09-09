import urllib.request
import urllib.parse
import json

# Search western Ranchi: Piska More, Kathal More, Ratu, Hehal, Pandra, ITI
WEST_RANCHI_BBOX = (23.3450, 85.2500, 23.4100, 85.3250)

query = f"""[out:json][timeout:35];
(
  way["building"]({WEST_RANCHI_BBOX[0]},{WEST_RANCHI_BBOX[1]},{WEST_RANCHI_BBOX[2]},{WEST_RANCHI_BBOX[3]});
);
out center 500;
"""

req = urllib.request.Request(
    "https://lz4.overpass-api.de/api/interpreter",
    data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
    headers={"User-Agent": "BhuSynchAI/1.0"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Total building elements in West Ranchi: {len(elements)}")
        if elements:
            # Let's see bounding boxes of these buildings
            lats = [e.get("center", {}).get("lat") for e in elements if "center" in e]
            lons = [e.get("center", {}).get("lon") for e in elements if "center" in e]
            if lats and lons:
                print(f"Lat range: {min(lats):.4f} to {max(lats):.4f}")
                print(f"Lon range: {min(lons):.4f} to {max(lons):.4f}")
                sample = elements[:10]
                for s in sample:
                    print(s.get("tags", {}).get("name"), s.get("center"))
except Exception as e:
    print(f"Error: {e}")
