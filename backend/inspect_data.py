import os
import json

data_dir = r"C:\Users\rajab\Desktop\Data"
print("Scanning Data Directory:", data_dir)

summary = {}
for fname in sorted(os.listdir(data_dir)):
    if fname.endswith(".geojson") or fname.endswith(".json"):
        fpath = os.path.join(data_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if "features" in data:
                        summary[fname] = f"FeatureCollection ({len(data['features'])} features)"
                    else:
                        summary[fname] = f"Dict with keys: {list(data.keys())[:6]}"
                elif isinstance(data, list):
                    summary[fname] = f"List ({len(data)} items)"
        except Exception as e:
            summary[fname] = f"Error: {e}"

for k, v in summary.items():
    print(f"  {k:50s} -> {v}")
