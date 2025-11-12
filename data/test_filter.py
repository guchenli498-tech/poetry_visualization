import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
COORDS_PATH = os.path.join(BASE_DIR, "geo_coordinates.json")

print("开始执行...")
print(f"BASE_DIR: {BASE_DIR}")
print(f"OUTPUT_DIR: {OUTPUT_DIR}")

try:
    with open(os.path.join(OUTPUT_DIR, "geo_stats.json"), encoding="utf-8") as f:
        geo_stats = json.load(f)
    print(f"成功加载 geo_stats.json，共 {len(geo_stats)} 条记录")
except Exception as e:
    print(f"加载 geo_stats.json 失败: {e}")
    sys.exit(1)

try:
    with open(COORDS_PATH, encoding="utf-8") as f:
        coords = json.load(f)
    print(f"成功加载 geo_coordinates.json，共 {len(coords)} 条记录")
except Exception as e:
    print(f"加载 geo_coordinates.json 失败: {e}")
    sys.exit(1)

# 统计缺少坐标的
missing = []
for entry in geo_stats[:100]:  # 先看前100个
    name = entry["名称"]
    if name not in coords:
        missing.append(name)

print(f"\n前100个中，缺少坐标的有 {len(missing)} 个")
print("示例：")
for name in missing[:10]:
    print(f"  - {name}")

