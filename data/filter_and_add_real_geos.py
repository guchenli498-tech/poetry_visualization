import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
COORDS_PATH = os.path.join(BASE_DIR, "geo_coordinates.json")
ENTITIES_PATH = os.path.join(BASE_DIR, "geo_entities.json")

# 从poetey_analysis导入排除词
import sys
sys.path.append(ROOT_DIR)
from poetey_analysis import EXCLUDED_NAMES

# 泛指词和抽象概念词（需要排除）
GENERIC_WORDS = {
    "山", "湖", "江", "河", "海", "城", "州", "郡", "县", "关", "谷", "川", "溪", 
    "岭", "峰", "台", "洲", "岛", "湾", "坡", "洞", "泉", "原", "津", "南", "北",
    "东", "西", "中", "内", "外", "上", "下", "前", "后", "左", "右", "东西", "南北",
    "深山", "深淵", "碧海", "澄潭", "石橋", "都城", "郡城", "梵宮", "雲中",
    "江中", "湖中", "山中", "谷中", "城內", "城外", "東西", "南北", "入洛遊梁",
    "卧雲", "希夷", "圖南", "賀厦", "檀那", "滿舊山", "無夕陽", "入夏", "半山",
    "半陽湖", "潮溝", "桐陰", "石岡", "岡頭", "北渠", "黑龍湖徹鳳池", "五城",
    # 更多泛指词
    "東山", "溪山", "江城", "北山", "江海", "雲山", "湖山", "南泉", "山寺", 
    "甘泉", "三山", "百川", "滄海", "遠山", "登山", "十洲", "江北", "平湖", 
    "南州", "古寺", "故山", "清溪", "大海", "湖海", "丹山", "西州", "玉山",
    "西江", "九江", "江河", "澄江", "百城", "德山", "平江", "山城", "高山",
    "君山", "名山", "仙山", "蓬山", "靈山", "空山", "寒山", "秋山", "春山",
    "夏山", "冬山", "青山", "綠山", "紅山", "白山", "黑山", "黃山", "紫山"
}

# 单字词（除非是特定地名）
SINGLE_CHAR_EXCEPTIONS = {"華"}  # 可能指华山

def is_generic_word(name):
    """判断是否为泛指词"""
    if not name or len(name) == 0:
        return True
    
    # 排除词列表中的词
    if name in EXCLUDED_NAMES:
        return True
    
    # 单字词（除非是例外）
    if len(name) == 1 and name not in SINGLE_CHAR_EXCEPTIONS:
        return True
    
    # 通用词列表
    if name in GENERIC_WORDS:
        return True
    
    # 包含明显泛指成分的词
    if any(gw in name for gw in ["中", "内", "外", "上", "下", "前", "后", "東西", "南北"]):
        if len(name) <= 3:  # 短词更可能是泛指
            return True
    
    # 抽象概念词（包含特定模式）
    abstract_patterns = [
        r"^入\w+$",  # 入洛、入夏等
        r"^卧\w+$",  # 卧云等
        r"^希\w+$",  # 希夷等
        r"^圖\w+$",  # 图南等
        r"^賀\w+$",  # 贺厦等
    ]
    for pattern in abstract_patterns:
        if re.match(pattern, name):
            return True
    
    return False

def is_real_geographic_location(name, geo_type, count):
    """判断是否为真正的地理位置"""
    # 如果出现次数太少，可能是误识别
    if count < 3:
        return False
    
    # 必须是具体的地名格式
    # 包含常见地名后缀
    geo_suffixes = ["山", "江", "河", "湖", "海", "州", "郡", "县", "城", "关", 
                    "岭", "峰", "台", "洲", "岛", "湾", "溪", "谷", "川", "泉",
                    "亭", "楼", "寺", "观", "庙", "祠", "陵", "墓", "园", "苑"]
    
    # 至少包含一个地理后缀
    has_suffix = any(name.endswith(suffix) for suffix in geo_suffixes)
    
    if not has_suffix:
        return False
    
    # 如果类型不是"未知"，更可能是真正的地理位置
    if geo_type != "未知":
        return True
    
    # 对于类型为"未知"的，需要更严格的判断
    # 排除明显的泛指词模式
    generic_patterns = [
        r"^[東西南北][山江湖海]$",  # 东山、西山等（但西湖是特例）
        r"^[百千萬][山江湖海川城]$",  # 百山、千山等
        r"^[遠近高低大小][山江湖海]$",  # 远山、近山等
        r"^[清澄碧][江湖溪]$",  # 清江、澄江等
        r"^[古故舊][山城寺]$",  # 古山、故山等
        r"^[名仙靈空][山]$",  # 名山、仙山等
    ]
    
    # 特殊例外：西湖是真正的地理位置
    if name == "西湖":
        return True
    
    for pattern in generic_patterns:
        if re.match(pattern, name):
            return False
    
    # 如果通过了所有检查，且出现次数较多，可能是真正的地理位置
    if count >= 10:
        return True
    
    return False

def load_existing_data():
    """加载现有数据"""
    with open(os.path.join(OUTPUT_DIR, "geo_stats.json"), encoding="utf-8") as f:
        geo_stats = json.load(f)
    with open(COORDS_PATH, encoding="utf-8") as f:
        coords = json.load(f)
    return geo_stats, coords

def find_real_geographic_locations():
    """找出真正的地理位置"""
    geo_stats, coords = load_existing_data()
    
    real_geos = []
    for entry in geo_stats:
        name = entry["名称"]
        modern = entry.get("现代对应", name)
        geo_type = entry.get("类型", "未知")
        count = entry.get("总出现次数", 0)
        
        # 如果已有坐标，跳过
        if name in coords or modern in coords:
            continue
        
        # 排除泛指词
        if is_generic_word(name):
            continue
        
        # 判断是否为真正的地理位置
        if is_real_geographic_location(name, geo_type, count):
            real_geos.append({
                "名称": name,
                "现代对应": modern,
                "类型": geo_type,
                "出现次数": count
            })
    
    # 按出现次数排序
    real_geos.sort(key=lambda x: x["出现次数"], reverse=True)
    
    return real_geos

def add_coordinates_for_real_geos(real_geos, limit=100):
    """为真正的地理位置添加坐标（使用网络搜索或已知数据）"""
    # 这里我们手动添加一些常见的历史地理位置坐标
    # 实际应用中可以使用地理编码API
    
    known_coords = {
        # 常见历史地名
        "洛陽": {"lat": 34.6167, "lng": 112.4537},  # 洛阳
        "長安": {"lat": 34.3416, "lng": 108.9398},  # 长安
        "長江": {"lat": 30.6, "lng": 114.0},  # 长江
        "華山": {"lat": 34.4826, "lng": 110.1001},  # 华山
        "華陰": {"lat": 34.5653, "lng": 110.0923},  # 华阴
        "渭濱": {"lat": 34.3333, "lng": 109.0},  # 渭滨（渭河沿岸）
        "巫峽": {"lat": 31.1, "lng": 109.8},  # 巫峡
        "西湖": {"lat": 30.2741, "lng": 120.1551},  # 杭州西湖
        "揚州": {"lat": 32.3942, "lng": 119.4127},  # 扬州
        "蘇州": {"lat": 31.2989, "lng": 120.5853},  # 苏州
        "廬山": {"lat": 29.5649, "lng": 115.9859},  # 庐山
        "廬陵": {"lat": 27.11, "lng": 114.98},  # 庐陵（吉安）
        "湘江": {"lat": 28.2, "lng": 112.9},  # 湘江
        "南昌": {"lat": 28.682, "lng": 115.857},  # 南昌
        "建业": {"lat": 32.0603, "lng": 118.7969},  # 建业（南京）
        "汝州": {"lat": 34.1674, "lng": 112.8458},  # 汝州
        "柳州": {"lat": 24.3146, "lng": 109.4281},  # 柳州
        "房州": {"lat": 32.0583, "lng": 110.725},  # 房州（房县）
        "九江": {"lat": 29.705, "lng": 115.992},  # 九江
        "巴陵": {"lat": 29.3572, "lng": 113.1289},  # 巴陵（岳阳）
    }
    
    coords = load_existing_data()[1]
    added = 0
    
    for geo in real_geos[:limit]:
        name = geo["名称"]
        modern = geo["现代对应"]
        
        # 检查已知坐标
        if name in known_coords:
            coords[name] = known_coords[name]
            added += 1
            print(f"添加坐标: {name} -> {known_coords[name]}")
        elif modern in known_coords:
            coords[name] = known_coords[modern]
            added += 1
            print(f"添加坐标: {name} (现代: {modern}) -> {known_coords[modern]}")
    
    # 保存更新后的坐标
    if added > 0:
        with open(COORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(coords, f, ensure_ascii=False, indent=2)
        print(f"\n已添加 {added} 个地理位置的坐标")
    
    return added

if __name__ == "__main__":
    print("正在筛选真正的地理位置...")
    real_geos = find_real_geographic_locations()
    
    print(f"\n找到 {len(real_geos)} 个真正的地理位置（排除泛指词后）")
    print("\n前50个地理位置：")
    for i, geo in enumerate(real_geos[:50], 1):
        print(f"{i}. {geo['名称']} ({geo['类型']}) - {geo['出现次数']} 次")
    
    print(f"\n是否要为这些地理位置添加坐标？")
    print("（当前脚本会为部分已知位置添加坐标）")
    
    added = add_coordinates_for_real_geos(real_geos, limit=50)
    
    if added > 0:
        print(f"\n已更新 geo_coordinates.json，新增 {added} 个坐标")
    else:
        print("\n未添加新坐标（可能需要手动查找或使用地理编码API）")

