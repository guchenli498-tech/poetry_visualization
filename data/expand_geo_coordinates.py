import json
import os

# 基础目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COORDINATES_PATH = os.path.join(BASE_DIR, "geo_coordinates.json")
ENTITIES_PATH = os.path.join(BASE_DIR, "geo_entities.json")

def load_existing_coordinates():
    """加载现有坐标"""
    with open(COORDINATES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_entities():
    """加载现有地理实体"""
    with open(ENTITIES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def expand_coordinates():
    """扩充坐标数据库"""
    coordinates = load_existing_coordinates()
    entities = load_existing_entities()
    
    # 额外的地理位置坐标（历史地理位置）
    additional_coords = {
        # 重要历史城市
        "平城": {"lat": 40.0, "lng": 113.0},  # 北魏都城
        "大同": {"lat": 40.0, "lng": 113.3},
        "汴京": {"lat": 34.8, "lng": 114.3},  # 宋朝都城
        "临安": {"lat": 30.2, "lng": 120.2},  # 南宋都城（杭州）
        "金陵": {"lat": 32.1, "lng": 118.8},  # 南京历史名称
        "建康": {"lat": 32.1, "lng": 118.8},
        
        # 重要关隘
        "居庸关": {"lat": 40.4, "lng": 116.0},
        "山海关": {"lat": 40.4, "lng": 119.8},
        "函谷关": {"lat": 34.6, "lng": 110.5},
        
        # 重要山脉
        "武夷山": {"lat": 27.9, "lng": 118.0},
        "黄山": {"lat": 30.1, "lng": 118.2},
        "天台山": {"lat": 29.1, "lng": 121.2},
        "青城山": {"lat": 30.9, "lng": 103.6},
        
        # 重要湖泊
        "鄱阳湖": {"lat": 29.1, "lng": 116.3},
        "洞庭湖": {"lat": 29.2, "lng": 112.9},
        "太湖": {"lat": 31.2, "lng": 120.2},
        
        # 其他重要地理位置
        "凉州": {"lat": 37.9, "lng": 102.6},
        "益州": {"lat": 30.7, "lng": 104.1},
        "荆州": {"lat": 30.4, "lng": 112.2},
        "交州": {"lat": 22.8, "lng": 108.3},
        "幽州": {"lat": 39.9, "lng": 116.4},
        "青州": {"lat": 36.7, "lng": 118.5},
        "徐州": {"lat": 34.3, "lng": 117.3},
        "冀州": {"lat": 37.5, "lng": 115.5},
        
        # 诗词中常见地理意象
        "瀛洲": {"lat": 37.5, "lng": 121.4},  # 山东半岛
        "蓬莱": {"lat": 37.5, "lng": 121.4},
        "仙山": {"lat": 29.7, "lng": 118.3},
        "蓬山": {"lat": 36.3, "lng": 120.4},
    }
    
    # 合并坐标，优先使用现有坐标
    for name, coords in additional_coords.items():
        if name not in coordinates:
            coordinates[name] = coords
    
    # 保存更新后的坐标文件
    with open(COORDINATES_PATH, 'w', encoding='utf-8') as f:
        json.dump(coordinates, f, ensure_ascii=False, indent=2)
    
    print(f"已扩充坐标数据库，新增 {len(additional_coords)} 个地理位置")
    print("新增地理位置：")
    for name in additional_coords:
        print(f"- {name}: {coordinates[name]}")

if __name__ == "__main__":
    expand_coordinates()
