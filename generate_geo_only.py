import json
import os
from poetey_analysis import EXCLUDED_NAMES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 山河意象关键词（用于筛选）
GEO_KEYWORDS = ["山", "江", "河", "湖", "州", "岭", "川", "溪", "峡", "关", "台", "洲", "海", "泉", "峰", "谷", "岳", "湾", "坡", "洞"]

def is_geo_entity(item):
    """
    判断是否为山河意象
    """
    name = item["名称"]
    
    # 排除通用词汇
    if name in EXCLUDED_NAMES:
        return False
    
    # 长度至少为2
    if len(name) < 2:
        return False
    
    # 必须包含山河相关关键词
    if not any(keyword in name for keyword in GEO_KEYWORDS):
        return False
    
    return True

def generate_geo_only_json():
    """
    生成只包含山河意象的 JSON 文件
    """
    input_path = os.path.join(OUTPUT_DIR, "geo_stats.json")
    output_path = os.path.join(OUTPUT_DIR, "geo_stats_mountains_rivers_only.json")
    
    print(f"正在读取：{input_path}")
    with open(input_path, encoding="utf-8") as f:
        all_data = json.load(f)
    
    print(f"原始数据总数：{len(all_data)}")
    
    # 过滤出山河意象
    geo_only = [item for item in all_data if is_geo_entity(item)]
    
    # 按出现次数排序
    geo_only.sort(key=lambda x: x["总出现次数"], reverse=True)
    
    print(f"过滤后山河意象数量：{len(geo_only)}")
    
    # 保存到文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geo_only, f, ensure_ascii=False, indent=2)
    
    print(f"已生成山河意象 JSON 文件：{output_path}")
    print(f"\n前10名山河意象：")
    for idx, item in enumerate(geo_only[:10], 1):
        print(f"{idx}. {item['名称']} - {item['总出现次数']} 次 - {item.get('类型', '未知')}")
    
    return output_path

if __name__ == "__main__":
    generate_geo_only_json()

