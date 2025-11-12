import json
import os
from typing import List, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 常见的山河后缀，便于快速排查明显不合格的地名
GEO_SUFFIXES = [
    "山", "岳", "岭", "峰", "河", "江", "湖", "海", "川", "溪", "涧", "湾",
    "坡", "洲", "州", "郡", "城", "关", "谷", "洞", "泉", "台", "岛"
]

EXCLUDED_NAMES = {"千山","江山","山林","青山", "四海", "江湖", "山川","山河","西山","东山","天下", "九州", "五湖", "六合", "八荒", "九域", "四方", "宇内", "寰中", "江表", "河朔", "塞北", "岭南", "漠北", "中原", "南疆", "北疆", "关内", "关外", "河东", "河西", "山南", "山北", "淮左", "淮右", "山水", "四面山", "山河大地", "山阜", "峽山", "峡山", "河明", "浮川", "居海", "如海", "福海", "海陽", "海國", "海霧江", "湖江", "北湖", "青草湖", "柳邊湖", "明河", "陂湖", "好山", "山開南國", "莫指雲山", "中峰", "中台", "陽洲", "花洲", "四海九州"}


def load_geo_stats() -> List[Dict]:
    path = os.path.join(OUTPUT_DIR, "geo_stats.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到 geo_stats.json，路径：{path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("geo_stats.json 内容格式异常，应为列表。")

    return data


def is_valid_geo(name: str) -> bool:
    if not name:
        return False

    if len(name) <= 1:
        return False

    for suffix in GEO_SUFFIXES:
        if suffix in name:
            return True

    return False


def audit_geo_entities():
    geo_stats = load_geo_stats()
    geo_stats_sorted = sorted(
        geo_stats, key=lambda item: item.get("总出现次数", 0), reverse=True
    )

    valid_items = []
    suspect_items = []

    for entry in geo_stats_sorted:
        name = entry.get("名称", "")
        if name in EXCLUDED_NAMES:
            continue
        if is_valid_geo(name):
            valid_items.append(entry)
        else:
            suspect_items.append(entry)

    print("=== 合格的山河意象（按出现次数排序） ===")
    for item in valid_items:
        print(
            f"{item['名称']}\t{item['总出现次数']} 次\t类型：{item.get('类型', '未知')}"
        )

    print("\n=== 需人工确认或排除的词条 ===")
    for item in suspect_items:
        print(
            f"{item['名称']}\t{item['总出现次数']} 次\t类型：{item.get('类型', '未知')}"
        )

    # 额外导出一个仅保留“合格地名”的 JSON 供后续可视化使用
    filtered_path = os.path.join(OUTPUT_DIR, "geo_stats_filtered.json")
    with open(filtered_path, "w", encoding="utf-8") as f:
        json.dump(valid_items, f, ensure_ascii=False, indent=2)

    print(f"\n已生成过滤后的 geo_stats_filtered.json，位置：{filtered_path}")


if __name__ == "__main__":
    audit_geo_entities()

