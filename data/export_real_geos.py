import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
COORDS_PATH = os.path.join(BASE_DIR, "geo_coordinates.json")

# 排除词（从poetey_analysis导入，这里直接定义避免导入问题）
EXCLUDED_NAMES = {"千山","江山","山林","青山", "四海", "江湖", "山川","山河","西山","东山","天下", "九州", "五湖", "六合", "八荒", "九域", "四方", "宇内", "寰中", "江表", "河朔", "塞北", "岭南", "漠北", "中原", "南疆", "北疆", "关内", "关外", "河东", "河西", "山南", "山北", "淮左", "淮右", "山水", "四面山", "山河大地", "山阜", "峽山", "峡山", "河明", "浮川", "居海", "如海", "福海", "海陽", "海國", "海霧江", "湖江", "北湖", "青草湖", "柳邊湖", "明河", "陂湖", "好山", "山開南國", "莫指雲山", "中峰", "中台", "陽洲", "花洲", "四海九州"}

# 泛指词
GENERIC_WORDS = {
    "山", "湖", "江", "河", "海", "城", "州", "郡", "县", "关", "谷", "川", "溪", 
    "岭", "峰", "台", "洲", "岛", "湾", "坡", "洞", "泉", "原", "津", "南", "北",
    "东", "西", "中", "内", "外", "上", "下", "前", "后", "左", "右", "东西", "南北",
    "深山", "深淵", "碧海", "澄潭", "石橋", "都城", "郡城", "梵宮", "雲中",
    "江中", "湖中", "山中", "谷中", "城內", "城外", "東西", "南北", "入洛遊梁",
    "卧雲", "希夷", "圖南", "賀厦", "檀那", "滿舊山", "無夕陽", "入夏", "半山",
    "半陽湖", "潮溝", "桐陰", "石岡", "岡頭", "北渠", "黑龍湖徹鳳池", "五城",
    "東山", "溪山", "江城", "北山", "江海", "雲山", "湖山", "南泉", "山寺", 
    "甘泉", "三山", "百川", "滄海", "遠山", "登山", "十洲", "江北", "平湖", 
    "南州", "古寺", "故山", "清溪", "大海", "湖海", "丹山", "西州", "玉山",
    "西江", "江河", "澄江", "百城", "德山", "平江", "山城", "高山",
    "君山", "名山", "仙山", "蓬山", "靈山", "空山", "寒山", "秋山", "春山",
    "夏山", "冬山", "綠山", "紅山", "白山", "黑山", "紫山"
}

def is_generic_word(name):
    """判断是否为泛指词"""
    if not name or len(name) == 0:
        return True
    if name in EXCLUDED_NAMES:
        return True
    if len(name) == 1:
        return True
    if name in GENERIC_WORDS:
        return True
    if any(gw in name for gw in ["中", "内", "外", "上", "下", "前", "后", "東西", "南北"]):
        if len(name) <= 3:
            return True
    abstract_patterns = [
        r"^入\w+$", r"^卧\w+$", r"^希\w+$", r"^圖\w+$", r"^賀\w+$",
    ]
    for pattern in abstract_patterns:
        if re.match(pattern, name):
            return True
    return False

def is_real_geographic_location(name, geo_type, count):
    """判断是否为真正的地理位置"""
    if count < 3:
        return False
    
    geo_suffixes = ["山", "江", "河", "湖", "海", "州", "郡", "县", "城", "关", 
                    "岭", "峰", "台", "洲", "岛", "湾", "溪", "谷", "川", "泉",
                    "亭", "楼", "寺", "观", "庙", "祠", "陵", "墓", "园", "苑"]
    
    has_suffix = any(name.endswith(suffix) for suffix in geo_suffixes)
    if not has_suffix:
        return False
    
    if geo_type != "未知":
        return True
    
    # 排除泛指词模式
    generic_patterns = [
        r"^[東西南北][山江湖海]$",
        r"^[百千萬][山江湖海川城]$",
        r"^[遠近高低大小][山江湖海]$",
        r"^[清澄碧][江湖溪]$",
        r"^[古故舊][山城寺]$",
        r"^[名仙靈空][山]$",
    ]
    
    if name == "西湖":
        return True
    
    for pattern in generic_patterns:
        if re.match(pattern, name):
            return False
    
    if count >= 10:
        return True
    
    return False

# 加载数据
print("正在加载数据...")
with open(os.path.join(OUTPUT_DIR, "geo_stats.json"), encoding="utf-8") as f:
    geo_stats = json.load(f)
with open(COORDS_PATH, encoding="utf-8") as f:
    coords = json.load(f)

print(f"已加载 {len(geo_stats)} 个地理实体，{len(coords)} 个已有坐标")

# 筛选真正的地理位置
real_geos = []
for entry in geo_stats:
    name = entry["名称"]
    modern = entry.get("现代对应", name)
    geo_type = entry.get("类型", "未知")
    count = entry.get("总出现次数", 0)
    
    if name in coords or modern in coords:
        continue
    
    if is_generic_word(name):
        continue
    
    if is_real_geographic_location(name, geo_type, count):
        real_geos.append({
            "名称": name,
            "现代对应": modern,
            "类型": geo_type,
            "出现次数": count
        })

real_geos.sort(key=lambda x: x["出现次数"], reverse=True)

print(f"\n找到 {len(real_geos)} 个真正的地理位置（排除泛指词后）")
print("\n前50个地理位置：")
for i, geo in enumerate(real_geos[:50], 1):
    print(f"{i}. {geo['名称']} ({geo['类型']}) - {geo['出现次数']} 次")

# 保存到文件
output_file = os.path.join(BASE_DIR, "real_geographic_locations.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(real_geos, f, ensure_ascii=False, indent=2)

print(f"\n已保存到: {output_file}")

