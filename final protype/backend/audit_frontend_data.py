import json
from pathlib import Path

data_dir = Path("frontend/data")
files = sorted(list(data_dir.glob("*.*")))

print(f"Auditing {len(files)} files in {data_dir}...\n")

results = []

for f in files:
    size_kb = round(f.stat().st_size / 1024, 2)
    name = f.name
    ext = f.suffix.lower()
    
    info = {
        "filename": name,
        "size_kb": size_kb,
        "extension": ext,
        "valid_json": False,
        "type": "Unknown",
        "feature_count": 0,
        "geom_types": set(),
        "bbox": None,
        "sample_properties": [],
        "provenance": "Unknown"
    }
    
    try:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            info["valid_json"] = True
            
            if isinstance(data, dict):
                info["type"] = data.get("type", "Dict")
                features = data.get("features", [])
                info["feature_count"] = len(features)
                
                min_lon, min_lat, max_lon, max_lat = 180, 90, -180, -90
                has_coords = False
                
                for feat in features:
                    geom = feat.get("geometry") or {}
                    gtype = geom.get("type")
                    if gtype:
                        info["geom_types"].add(gtype)
                        
                    coords = geom.get("coordinates")
                    # Recursive coordinate extraction for bbox
                    def extract_pts(c):
                        pts = []
                        if isinstance(c, list):
                            if len(c) >= 2 and isinstance(c[0], (int, float)) and isinstance(c[1], (int, float)):
                                pts.append((c[0], c[1]))
                            else:
                                for sub in c:
                                    pts.extend(extract_pts(sub))
                        return pts
                    
                    pts = extract_pts(coords)
                    for lon, lat in pts:
                        if -180 <= lon <= 180 and -90 <= lat <= 90:
                            has_coords = True
                            if lon < min_lon: min_lon = lon
                            if lon > max_lon: max_lon = lon
                            if lat < min_lat: min_lat = lat
                            if lat > max_lat: max_lat = lat
                            
                    props = feat.get("properties") or {}
                    if not info["sample_properties"] and props:
                        info["sample_properties"] = list(props.keys())[:8]
                        
                if has_coords:
                    info["bbox"] = [round(min_lon, 4), round(min_lat, 4), round(max_lon, 4), round(max_lat, 4)]
                    
            elif isinstance(data, list):
                info["type"] = "Array"
                info["feature_count"] = len(data)
                if data and isinstance(data[0], dict):
                    info["sample_properties"] = list(data[0].keys())[:8]
                    
    except Exception as e:
        info["error"] = str(e)
        
    info["geom_types"] = list(info["geom_types"])
    results.append(info)

# Output summary table
print(f"{'Filename':<45} | {'Size (KB)':<10} | {'Type':<18} | {'Count':<7} | {'Geometries':<22} | {'BBox [minX, minY, maxX, maxY]'}")
print("-" * 140)
for r in results:
    bbox_str = str(r['bbox']) if r['bbox'] else "N/A"
    geom_str = ",".join(r['geom_types']) if r['geom_types'] else "N/A"
    print(f"{r['filename']:<45} | {r['size_kb']:<10} | {r['type']:<18} | {r['feature_count']:<7} | {geom_str:<22} | {bbox_str}")

with open("backend/audit_results.json", "w", encoding="utf-8") as out:
    json.dump(results, out, indent=2)
print("\nSaved full audit to backend/audit_results.json")
