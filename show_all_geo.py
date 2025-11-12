import json
import os
from poetey_analysis import EXCLUDED_NAMES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

path = os.path.join(OUTPUT_DIR, "geo_stats.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)

print("=" * 80)
print("所有山河意象统计（已排除通用词汇）")
print("=" * 80)
print(f"{'排名':<6} {'名称':<20} {'出现次数':<12} {'类型':<15} {'现代对应'}")
print("-" * 80)

# 过滤并排序
filtered = [item for item in data if item["名称"] not in EXCLUDED_NAMES]
filtered.sort(key=lambda x: x["总出现次数"], reverse=True)

for idx, item in enumerate(filtered, 1):
    name = item["名称"]
    count = item["总出现次数"]
    geo_type = item.get("类型", "未知")
    modern = item.get("现代对应", name)
    print(f"{idx:<6} {name:<20} {count:<12} {geo_type:<15} {modern}")

print("=" * 80)
print(f"总计：{len(filtered)} 个山河意象")
print("=" * 80)

