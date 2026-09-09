import urllib.request
import urllib.parse
import json

query = """[out:json][timeout:25];
(
  node["name"~"Piska|पिस्का|Hehal|Pandra",i](23.33,85.25,23.42,85.35);
  way["name"~"Piska|पिस्का|Hehal|Pandra|Ratu Road",i](23.33,85.25,23.42,85.35);
);
out center 25;
"""

try:
    req = urllib.request.Request(
        "https://lz4.overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
        headers={"User-Agent": "BhuSynchAI/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Found {len(elements)} elements matching Piska / Hehal / Pandra:")
        for el in elements:
            tags = el.get("tags", {})
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            name = tags.get("name", "Unnamed")
            tag_type = tags.get("highway") or tags.get("amenity") or tags.get("place") or tags.get("shop")
            print(f"- {name} @ [{lon}, {lat}] ({tag_type})")
except Exception as e:
    print(f"Error: {e}")
