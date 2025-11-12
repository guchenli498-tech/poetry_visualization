import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
COORDS_PATH = os.path.join(BASE_DIR, "geo_coordinates.json")

with open(os.path.join(OUTPUT_DIR, "geo_stats.json"), encoding="utf-8") as f:
    geo_stats = json.load(f)
with open(COORDS_PATH, encoding="utf-8") as f:
    coords = json.load(f)

missing = []
for entry in geo_stats:
    name = entry["名称"]
    modern = entry.get("现代对应")
    if name not in coords and (not modern or modern not in coords):
        missing.append(name)

print(f"总共 {len(geo_stats)} 个地理实体，缺少坐标的有 {len(missing)} 个")
print("示例缺失：")
for name in missing[:50]:
    print(f"- {name}")
