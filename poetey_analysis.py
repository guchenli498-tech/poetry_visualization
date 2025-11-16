import os
import json
import re
import random
import jieba
import jieba.posseg as pseg
import jieba.analyse as jieba_analyse
from snownlp import SnowNLP
from collections import defaultdict, Counter
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCLUDED_NAMES = {
    # 抽象概念和通用词
    "千山","江山","山林","青山", "四海", "江湖", "山川","山河","西山","东山","天下", 
    "九州", "五湖", "六合", "八荒", "九域", "四方", "宇内", "寰中", "江表", "河朔", 
    "塞北", "岭南", "漠北", "中原", "南疆", "北疆", "关内", "关外", "河东", "河西", 
    "山南", "山北", "淮左", "淮右", "山水", "四面山", "山河大地", "山阜", "峽山", 
    "峡山", "河明", "浮川", "居海", "如海", "福海", "海陽", "海國", "海霧江", "湖江", 
    "北湖", "青草湖", "柳邊湖", "明河", "陂湖", "好山", "山開南國", "莫指雲山", 
    "中峰", "中台", "陽洲", "花洲", "四海九州",
    # 单字通用词（这些不应该作为具体地名）
    "山", "城", "州", "溪", "湖", "川", "谷", "原", "津", "郡", "海", "江", "河",
    "香", "華", "東", "西", "南", "北", "中", "上", "下", "大", "小", "新", "舊",
    # 抽象概念
    "千古", "太平", "南北", "東西", "雲水", "東坡",
    # 误识别的通用词（从数据分析中发现）
    "東山", "牡丹", "雲", "南國", "河漢", "中興", "溪山", "四壁", "漠漠", "江城",
    "英雄", "青春", "北山", "江海", "美", "雲山", "西北", "湖山", "印", "南泉",
    "山寺", "江西", "甘泉", "重陽", "三山", "西園", "陰陽", "江水", "池塘", "雲門"
}

class PoetryAnalyzer:
    def __init__(self):
        # 加载地理名词词典
        self.geo_entities, self.geo_alias_map = self._load_geo_entities()
        self.geo_patterns = self._build_geo_patterns()
        self.geo_coordinates = self._load_geo_coordinates()
        
        # 情感词典（多维度）
        self.sentiment_dict = self._build_sentiment_dictionary()
        
        # 诗歌主题关键词
        self.theme_keywords = self._build_theme_keywords()

        # 作者资料
        self.author_profiles = self._load_author_profiles()

    def _load_geo_entities(self):
        """
        从 data/geo_entities.json 加载地理词典，如果不存在则使用内置基础词表
        """
        default_entities = {
            "长安": {
                "type": "城市",
                "aliases": ["京兆", "镐京", "大兴城"],
                "modern_name": "西安"
            },
            "洛阳": {
                "type": "城市",
                "aliases": ["东都"],
                "modern_name": "洛阳"
            },
            "会稽山": {
                "type": "山脉",
                "aliases": ["会稽"],
                "modern_name": "浙江绍兴会稽山"
            },
            "洞庭湖": {
                "type": "湖泊",
                "aliases": ["洞庭", "八百里洞庭"],
                "modern_name": "湖南岳阳洞庭湖"
            },
            "黄河": {
                "type": "河流",
                "aliases": ["河", "大河"],
                "modern_name": "黄河"
            },
            "长江": {
                "type": "河流",
                "aliases": ["江", "大江", "扬子江"],
                "modern_name": "长江"
            },
            "巴蜀": {
                "type": "地区",
                "aliases": ["蜀中", "成都府"],
                "modern_name": "四川盆地"
            },
            "江南": {
                "type": "地区",
                "aliases": ["吴地", "三吴", "江东"],
                "modern_name": "长江中下游南岸"
            },
            "潼关": {
                "type": "关隘",
                "aliases": ["潼闕"],
                "modern_name": "陕西潼关县"
            },
            "终南山": {
                "type": "山脉",
                "aliases": ["太乙山"],
                "modern_name": "陕西西安终南山"
            }
        }

        path = os.path.join(DATA_DIR, "geo_entities.json")
        entities = default_entities

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        entities = loaded
            except Exception as exc:
                print(f"读取地理词典失败，使用内置词表。错误：{exc}")

        alias_map = {}
        for canonical, info in entities.items():
            alias_map[canonical] = {
                "canonical": canonical,
                "type": info.get("type", "未知"),
                "modern_name": info.get("modern_name", canonical)
            }
            for alias in info.get("aliases", []):
                alias_map[alias] = {
                    "canonical": canonical,
                    "type": info.get("type", "未知"),
                    "modern_name": info.get("modern_name", canonical)
                }

        return entities, alias_map

    def _build_geo_patterns(self):
        """
        常见地名后缀模式，用于正则补充
        """
        suffixes = ["山", "江", "河", "湖", "川", "州", "郡", "县", "城", "关", "岭", "湾", "溪", "谷", "岛", "原", "津"]
        pattern = rf"[一-龥]{{1,4}}({'|'.join(suffixes)})"
        return re.compile(pattern)

    def _load_geo_coordinates(self):
        """
        加载地理坐标信息，返回名称到经纬度的映射
        """
        default_coords = {
            "长安": {"lat": 34.3416, "lng": 108.9398},
            "洛阳": {"lat": 34.6167, "lng": 112.4537},
            "扬州": {"lat": 32.3942, "lng": 119.4127},
            "苏州": {"lat": 31.2989, "lng": 120.5853},
            "杭州": {"lat": 30.2741, "lng": 120.1551},
            "成都": {"lat": 30.5728, "lng": 104.0668},
            "重庆": {"lat": 29.563, "lng": 106.5516},
            "南京": {"lat": 32.0603, "lng": 118.7969},
            "北京": {"lat": 39.9042, "lng": 116.4074},
            "潼关": {"lat": 34.5442, "lng": 110.2467},
            "终南山": {"lat": 34.0165, "lng": 108.7514},
            "华山": {"lat": 34.4826, "lng": 110.1001},
            "泰山": {"lat": 36.2699, "lng": 117.1046},
            "衡山": {"lat": 27.2503, "lng": 112.7083},
            "嵩山": {"lat": 34.5123, "lng": 112.9403},
            "会稽山": {"lat": 30.04, "lng": 120.64},
            "庐山": {"lat": 29.5649, "lng": 115.9859},
            "长江": {"lat": 30.6, "lng": 114.0},
            "黄河": {"lat": 35.0, "lng": 111.0},
            "洞庭湖": {"lat": 29.22, "lng": 112.88},
            "太湖": {"lat": 31.15, "lng": 120.1},
            "鄱阳湖": {"lat": 29.0833, "lng": 116.2333},
            "青海湖": {"lat": 36.8833, "lng": 99.1},
            "江南": {"lat": 31.0, "lng": 118.0},
            "关中": {"lat": 34.2667, "lng": 108.9},
            "巴蜀": {"lat": 30.6667, "lng": 103.9667},
            "岭南": {"lat": 23.1291, "lng": 113.2644},
            "襄阳": {"lat": 32.0089, "lng": 112.1229},
            "荆州": {"lat": 30.3527, "lng": 112.19},
            "长沙": {"lat": 28.2282, "lng": 112.9388},
            "桂林": {"lat": 25.2736, "lng": 110.29},
            "泉州": {"lat": 24.8741, "lng": 118.6759},
            "广州": {"lat": 23.1291, "lng": 113.2644},
            "福州": {"lat": 26.0745, "lng": 119.2965},
            "开封": {"lat": 34.7973, "lng": 114.3076},
            "太原": {"lat": 37.8706, "lng": 112.5489},
            "玉门关": {"lat": 40.35, "lng": 94.87},
            "嘉峪关": {"lat": 39.802, "lng": 98.294},
            "雁门关": {"lat": 39.2284, "lng": 112.8939},
            "兰亭": {"lat": 29.997, "lng": 120.582},
            "桃花源": {"lat": 28.9025, "lng": 110.9429},
            "岳阳楼": {"lat": 29.3746, "lng": 113.0975},
            "石鼓": {"lat": 26.9018, "lng": 112.614},
            "宣州": {"lat": 30.9449, "lng": 118.7587},
            "池州": {"lat": 30.664, "lng": 117.4914},
            "建昌": {"lat": 27.9187, "lng": 116.3318},
            "齐云山": {"lat": 29.7844, "lng": 117.7937},
            "泗州": {"lat": 33.483, "lng": 118.7034},
            "奉节": {"lat": 31.0185, "lng": 109.4648},
            "庐陵": {"lat": 27.11, "lng": 114.98},
            "眉山": {"lat": 30.075, "lng": 103.85},
            "济南": {"lat": 36.6512, "lng": 117.1201},
            "夔州": {"lat": 31.05, "lng": 109.6333},
            "惠州": {"lat": 23.1115, "lng": 114.4158},
            "鄱阳": {"lat": 29.0, "lng": 116.667},
            "上饶": {"lat": 28.4546, "lng": 117.9434},
            "金华": {"lat": 29.0792, "lng": 119.6474}
        }

        path = os.path.join(DATA_DIR, "geo_coordinates.json")
        coords = default_coords

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        coords = loaded
            except Exception as exc:
                print(f"读取坐标文件失败，使用默认坐标。错误：{exc}")

        return coords

    def _load_author_profiles(self):
        """
        加载作者资料，包含籍贯与主要行迹
        """
        default_profiles = {
            "李白": {
                "籍贯": "绵州昌隆县（今四川江油）",
                "主要行迹": [
                    {"地点": "长安", "时期": "开元二十三年"},
                    {"地点": "扬州", "时期": "天宝三载"},
                    {"地点": "庐山", "时期": "天宝十四载"}
                ]
            },
            "杜甫": {
                "籍贯": "河南巩县（今河南巩义）",
                "主要行迹": [
                    {"地点": "长安", "时期": "开元二十九年"},
                    {"地点": "奉节", "时期": "广德二年"},
                    {"地点": "成都", "时期": "宝应元年"}
                ]
            }
        }

        path = os.path.join(DATA_DIR, "author_profiles.json")
        profiles = default_profiles

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        profiles = loaded
            except Exception as exc:
                print(f"读取作者资料失败，使用内置资料。错误：{exc}")

        return profiles

    def _build_sentiment_dictionary(self):
        """
        构建多维度、更细致的情感词典
        """
        return {
            # 豪放词
            '豪放': {
                'keywords': ['壮志', '豪情', '激昂', '雄心', '豪迈', '气吞万里', '气势磅礴', '英雄', '慷慨'],
                'score': 0.8
            },
            
            # 婉约词
            '婉约': {
                'keywords': ['柔情', '细腻', '温柔', '轻盈', '娇羞', '纤细', '温婉', '含蓄', '委婉'],
                'score': 0.6
            },
            
            # 忧愁词
            '忧愁': {
                'keywords': ['哀愁', '悲伤', '惆怅', '凄凉', '寂寞', '孤独', '伤感', '悲凉', '萧瑟'],
                'score': 0.2
            },
            
            # 积极词
            '积极': {
                'keywords': ['希望', '光明', '美好', '温暖', '快乐', '喜悦', '激动', '振奋', '欢欣'],
                'score': 0.9
            },
            
            # 消极词
            '消极': {
                'keywords': ['绝望', '黑暗', '痛苦', '悲观', '失落', '压抑', '无助', '哀叹', '绝望'],
                'score': 0.1
            }
        }

    def _build_theme_keywords(self):
        """
        构建诗歌主题关键词
        """
        return {
            '战争': ['战', '战地', '战亡', '征', '破', '军', '兵', '将'],
            '自然': ['山', '水', '云', '雨', '雪', '风', '月', '天', '地'],
            '季节': ['春', '夏', '秋', '冬', '初春', '初夏', '晚秋'],
            '情感': ['思', '怀', '志', '感', '意', '心', '情'],
            '历史': ['汉', '唐', '宋', '志', '续', '古', '今']
        }

    def _normalize_geo_name(self, name):
        """
        地名标准化，返回统一信息
        """
        info = self.geo_alias_map.get(name)
        if info:
            return {
                "名称": info["canonical"],
                "类型": info.get("type", "未知"),
                "现代对应": info.get("modern_name", info["canonical"]),
                "原文名称": name
            }
        return {
            "名称": name,
            "类型": "未知",
            "现代对应": name,
            "原文名称": name
        }

    def extract_geo_entities(self, text, title=""):
        """
        提取地理实体（增强版）
        """
        # 合并文本和标题
        content = text if isinstance(text, str) else "".join(text)
        full_text = f"{title} {content}"

        entities = {}

        # 通过词典匹配（包含别名）
        for name in self.geo_alias_map.keys():
            if name and name in full_text:
                normalized = self._normalize_geo_name(name)
                entry = entities.setdefault(
                    normalized["名称"],
                    {
                        "名称": normalized["名称"],
                        "类型": normalized["类型"],
                        "现代对应": normalized["现代对应"],
                        "原文出现": set()
                    }
                )
                entry["原文出现"].add(normalized["原文名称"])

        # 正则补充常见地名模式
        for match in self.geo_patterns.findall(full_text):
            normalized = self._normalize_geo_name(match)
            entry = entities.setdefault(
                normalized["名称"],
                {
                    "名称": normalized["名称"],
                    "类型": normalized["类型"],
                    "现代对应": normalized["现代对应"],
                    "原文出现": set()
                }
            )
            entry["原文出现"].add(normalized["原文名称"])

        # 结巴分词补充
        for word, flag in pseg.cut(full_text):
            if flag == "ns":
                normalized = self._normalize_geo_name(word)
                entry = entities.setdefault(
                    normalized["名称"],
                    {
                        "名称": normalized["名称"],
                        "类型": normalized["类型"],
                        "现代对应": normalized["现代对应"],
                        "原文出现": set()
                    }
                )
                entry["原文出现"].add(normalized["原文名称"])

        # 转换集合为列表
        return [
            {
                "名称": data["名称"],
                "类型": data["类型"],
                "现代对应": data["现代对应"],
                "原文出现": sorted(data["原文出现"])
            }
            for data in entities.values()
            if data["名称"] not in EXCLUDED_NAMES
        ]

    def analyze_sentiment(self, text, title=""):
        """
        多维度、更智能的情感分析
        """
        # 合并文本和标题
        content = text if isinstance(text, str) else "".join(text)
        full_text = f"{title} {content}"
        
        # 如果文本为空或太短，返回默认情感
        if not full_text or len(full_text) < 5:
            return {
                '基础得分': 0.5,
                '情感类型': '中性',
                '情感维度': {}
            }
        
        # 使用SnowNLP基础得分
        try:
            base_sentiment = SnowNLP(full_text).sentiments
        except Exception:
            base_sentiment = 0.5
        
        # 多维度情感分析
        sentiment_details = {
            '基础得分': base_sentiment,
            '情感维度': {}
        }
        
        # 检查各种情感维度
        for sentiment_type, sentiment_info in self.sentiment_dict.items():
            # 计算关键词匹配程度
            keyword_score = sum(full_text.count(keyword) * 0.2 for keyword in sentiment_info['keywords'])
            
            # 如果有匹配的关键词
            if keyword_score > 0:
                sentiment_details['情感维度'][sentiment_type] = {
                    '关键词匹配分': keyword_score,
                    '情感权重': sentiment_info['score']
                }
                
                # 调整基础得分
                if sentiment_type in ['豪放', '积极']:
                    base_sentiment += keyword_score * 0.1
                elif sentiment_type in ['忧愁', '消极']:
                    base_sentiment -= keyword_score * 0.1
        
        # 检查诗歌主题
        for theme, keywords in self.theme_keywords.items():
            theme_score = sum(full_text.count(keyword) * 0.1 for keyword in keywords)
            if theme_score > 0:
                sentiment_details['情感维度'][theme] = theme_score
        
        # 确保得分在0-1范围
        base_sentiment = max(0, min(1, base_sentiment))
        
        # 综合情感类型判断
        if base_sentiment > 0.7:
            sentiment_details['情感类型'] = '非常正面'
        elif base_sentiment > 0.4:
            sentiment_details['情感类型'] = '中性偏正面'
        elif base_sentiment > 0.3:
            sentiment_details['情感类型'] = '中性'
        elif base_sentiment > 0.1:
            sentiment_details['情感类型'] = '中性偏负面'
        else:
            sentiment_details['情感类型'] = '非常负面'
        
        sentiment_details['基础得分'] = base_sentiment
        
        return sentiment_details

    def analyze_poetry_collection(self, poems):
        """
        分析诗词集合
        """
        analysis_results = []
        author_mentions = defaultdict(list)

        for idx, poem in enumerate(tqdm(poems, desc="正在解析诗词")):
            title = poem.get("title", "未知")
            author = poem.get("author", "未知")
            raw_content = poem.get("content", "")
            content = raw_content if isinstance(raw_content, str) else "".join(raw_content)

            geo_entities = self.extract_geo_entities(content, title)
            sentiment_details = self.analyze_sentiment(content, title)

            result = {
                "title": title,
                "author": author,
                "geo_entities": geo_entities,
                "sentiment": sentiment_details,
                "content": content,
                "dynasty": poem.get("dynasty", "未知"),
                "source_path": poem.get("source_path")
            }
            analysis_results.append(result)

            if author and geo_entities:
                author_mentions[author].append(
                    {
                        "title": title,
                        "order": idx,
                        "geo_entities": geo_entities,
                        "dynasty": poem.get("dynasty", "未知")
                    }
                )

        author_trajectories = self.build_author_trajectories(author_mentions)

        return {
            "poems": analysis_results,
            "author_trajectories": author_trajectories
        }

    def build_author_trajectories(self, author_mentions):
        """
        根据诗歌出现的地名和作者资料生成简易轨迹
        """
        trajectories = {}

        for author, mentions in author_mentions.items():
            profile = self.author_profiles.get(author, {})
            geo_counter = Counter()
            occurrence_sequence = []

            for item in sorted(mentions, key=lambda x: x["order"]):
                for geo in item["geo_entities"]:
                    if geo["名称"] in EXCLUDED_NAMES:
                        continue
                    name = geo["名称"]
                    geo_counter[name] += 1
                    coords = self.geo_coordinates.get(name) or self.geo_coordinates.get(geo["现代对应"])
                    occurrence_sequence.append(
                        {
                            "地点": name,
                            "原文出现": geo["原文出现"],
                            "首次出现诗篇": item["title"],
                            "类型": geo["类型"],
                            "现代对应": geo["现代对应"],
                            "经纬度": coords
                        }
                    )

            if geo_counter:
                profile_routes = []
                for entry in profile.get("主要行迹", []):
                    coords = self.geo_coordinates.get(entry.get("地点"))
                    profile_routes.append(
                        {
                            "时期": entry.get("时期"),
                            "地点": entry.get("地点"),
                            "经纬度": coords
                        }
                    )

                trajectories[author] = {
                    "籍贯": profile.get("籍贯"),
                    "主要行迹（资料）": profile_routes,
                    "诗歌出现地统计": [
                        {"地点": place, "出现次数": count}
                        for place, count in geo_counter.most_common()
                    ],
                    "出现顺序": occurrence_sequence
                }

        return trajectories


def infer_dynasty_from_path(path):
    """
    根据文件路径推断朝代
    """
    if not path:
        return "未知"
    if "全唐诗" in path:
        return "唐"
    if "五代" in path:
        return "五代"
    if "宋词" in path:
        return "宋"
    if "元曲" in path:
        return "元"
    return "未知"


def load_poetry_from_local(max_poems=10000):
    """
    从本地 JSON 文件加载诗词数据，并统一内容格式
    """
    poems = []

    poetry_folders = [
        os.path.join(BASE_DIR, "chinese-poetry", "全唐诗"),
        os.path.join(BASE_DIR, "chinese-poetry", "宋词")
    ]

    for folder in poetry_folders:
        if not os.path.exists(folder):
            print(f"警告：未找到目录 {folder}")
            continue

        for root, _, files in os.walk(folder):
            for filename in files:
                if filename.endswith(".json"):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        items = data if isinstance(data, list) else [data]

                        for item in items:
                            if not isinstance(item, dict):
                                continue

                            content = item.get(
                                "content",
                                item.get(
                                    "text",
                                    item.get(
                                        "paragraphs",
                                        item.get("poem", "")
                                    )
                                )
                            )

                            if isinstance(content, list):
                                content = "".join(content)

                            if content and len(content) > 10:
                                poems.append(
                                    {
                                        "title": item.get("title", "未知标题"),
                                        "author": item.get("author", "未知作者"),
                                        "content": content,
                                        "dynasty": item.get("dynasty")
                                        or item.get("era")
                                        or item.get("period")
                                        or infer_dynasty_from_path(filepath),
                                        "source_path": filepath
                                    }
                                )

                                if len(poems) >= max_poems:
                                    break
                    except Exception as exc:
                        print(f"读取文件错误：{filepath}")
                        print(f"错误信息：{exc}")

                if len(poems) >= max_poems:
                    break
            if len(poems) >= max_poems:
                break

    print(f"总共加载 {len(poems)} 首诗")
    return poems


def extract_poetry_quote_with_geo(poem_content, geo_name, geo_aliases, title, author):
    """
    提取包含地名的诗句片段
    
    Args:
        poem_content: 诗词内容（字符串）
        geo_name: 地名
        geo_aliases: 地名的别名列表
        title: 诗名
        author: 诗人
    
    Returns:
        包含地名的诗句片段列表，格式：[{"诗句": "...", "诗人": "...", "诗名": "..."}]
    """
    quotes = []
    if not poem_content or not geo_name:
        return quotes
    
    # 构建所有可能的名称（包括别名），按长度从长到短排序，优先匹配长名称
    all_names = [geo_name] + (geo_aliases if geo_aliases else [])
    all_names = sorted(set(all_names), key=len, reverse=True)  # 去重并按长度排序
    
    # 按句分割（逗号、句号、问号、感叹号等）
    sentences = re.split(r'[，。！？；\n]', poem_content)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # 检查是否包含地名（包括别名），优先匹配长名称
        found_geo = None
        for name in all_names:
            # 对于单字别名（如"河"、"江"），需要更严格的匹配
            # 只有当它是原文中出现的形式时，才匹配（避免误匹配）
            if len(name) == 1:
                # 单字匹配：检查是否是原文中出现的形式
                # 如果all_names中包含这个单字，说明它是原文中出现的形式，可以匹配
                if name in sentence:
                    found_geo = name
                    break
            else:
                # 多字匹配：直接匹配（已经按长度排序，优先匹配长名称）
                if name in sentence:
                    found_geo = name
                    break
        
        if found_geo:
            # 提取包含地名的半句
            # 如果地名在句子中间，取整句；如果在开头或结尾，取包含地名的部分
            quote_text = sentence
            
            # 去重：检查是否已存在相同的诗句
            is_duplicate = False
            for existing in quotes:
                if existing["诗句"] == quote_text and existing["诗人"] == author and existing["诗名"] == title:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                quotes.append({
                    "诗句": quote_text,
                    "诗人": author,
                    "诗名": title
                })
    
    return quotes


def aggregate_geo_statistics(poem_results, coordinate_map, geo_entities_dict=None):
    """
    汇总地理实体统计数据，同时收集诗句片段
    
    Args:
        poem_results: 诗词分析结果列表
        coordinate_map: 坐标映射字典
        geo_entities_dict: 地理实体字典，用于获取别名信息
    """
    stats = {}
    poetry_quotes_by_geo = defaultdict(list)  # 存储每个地名对应的诗句
    
    # 加载地理实体字典（如果未提供）
    if geo_entities_dict is None:
        geo_entities_path = os.path.join(DATA_DIR, "geo_entities.json")
        if os.path.exists(geo_entities_path):
            try:
                with open(geo_entities_path, "r", encoding="utf-8") as f:
                    geo_entities_dict = json.load(f)
            except Exception:
                geo_entities_dict = {}

    for poem in poem_results:
        dynasty = poem.get("dynasty", "未知")
        author = poem.get("author", "未知")
        sentiment_label = poem["sentiment"]["情感类型"]
        base_score = poem["sentiment"]["基础得分"]
        content = poem.get("content", "")
        title = poem.get("title", "未知")

        for geo in poem.get("geo_entities", []):
            name = geo["名称"]
            if name in EXCLUDED_NAMES:
                continue
            
            # 获取别名，包括原文中出现的形式
            # 如果原文中出现的是别名（如"河"），我们也需要匹配它
            geo_aliases = []
            if geo_entities_dict and name in geo_entities_dict:
                raw_aliases = geo_entities_dict[name].get("aliases", [])
                # 保留所有别名，包括单字别名（因为如果原文中出现"河"被识别为"黄河"，我们也需要提取它）
                geo_aliases = raw_aliases.copy()
            
            # 同时，如果原文中出现的形式不是主名称，也要加入别名列表
            original_forms = list(geo.get("原文出现", []))
            for orig_form in original_forms:
                if orig_form != name and orig_form not in geo_aliases:
                    geo_aliases.append(orig_form)
            
            # 提取包含地名的诗句片段（匹配主名称和所有别名，包括原文中出现的形式）
            quotes = extract_poetry_quote_with_geo(content, name, geo_aliases, title, author)
            for quote in quotes:
                # 去重：检查是否已存在相同的诗句
                is_duplicate = False
                for existing in poetry_quotes_by_geo[name]:
                    if (existing["诗句"] == quote["诗句"] and 
                        existing["诗人"] == quote["诗人"] and 
                        existing["诗名"] == quote["诗名"]):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    poetry_quotes_by_geo[name].append(quote)
            
            entry = stats.setdefault(
                name,
                {
                    "名称": name,
                    "类型": geo["类型"],
                    "现代对应": geo["现代对应"],
                    "总出现次数": 0,
                    "情感统计": defaultdict(int),
                    "出现诗人": set(),
                    "情感分数累计": 0.0,
                    "情感样本数": 0,
                    "朝代统计": {},
                    "文本集合": []
                }
            )

            entry["总出现次数"] += 1
            entry["情感统计"][sentiment_label] += 1
            if author:
                entry["出现诗人"].add(author)
            if content:
                entry["文本集合"].append(content)
            entry["情感分数累计"] += base_score
            entry["情感样本数"] += 1

            dynasty_stat = entry["朝代统计"].setdefault(
                dynasty,
                {
                    "出现次数": 0,
                    "情感分数累计": 0.0,
                    "情感样本数": 0,
                    "情感统计": defaultdict(int)
                }
            )
            dynasty_stat["出现次数"] += 1
            dynasty_stat["情感分数累计"] += base_score
            dynasty_stat["情感样本数"] += 1
            dynasty_stat["情感统计"][sentiment_label] += 1

    geo_stats = []
    sentiment_trend = []
    keyword_clouds = []

    # 改进坐标匹配：处理繁体字、别名等
    def find_coordinates(geo_name, modern_name, coord_map):
        """智能查找坐标，支持繁体字、别名等"""
        # 1. 直接匹配
        if geo_name in coord_map:
            return coord_map[geo_name]
        if modern_name and modern_name in coord_map:
            return coord_map[modern_name]
        
        # 2. 繁体字转换匹配（常见繁体字映射）
        traditional_to_simplified = {
            "長": "长", "安": "安", "揚": "扬", "蘇": "苏", "廬": "庐",
            "華": "华", "東": "东", "嶺": "岭", "關": "关", "縣": "县",
            "陽": "阳", "陰": "阴", "雲": "云", "風": "风", "龍": "龙"
        }
        simplified_name = geo_name
        for trad, simp in traditional_to_simplified.items():
            simplified_name = simplified_name.replace(trad, simp)
        if simplified_name != geo_name and simplified_name in coord_map:
            return coord_map[simplified_name]
        
        # 3. 通过别名匹配（如果geo_entities中有别名信息）
        # 这里可以扩展，从geo_entities中查找别名
        
        return None
    
    for name, entry in stats.items():
        coords = find_coordinates(name, entry["现代对应"], coordinate_map)
        avg_score = (
            entry["情感分数累计"] / entry["情感样本数"]
            if entry["情感样本数"]
            else None
        )

        dynasty_data = []
        for dynasty, data in entry["朝代统计"].items():
            dynasty_avg = (
                data["情感分数累计"] / data["情感样本数"]
                if data["情感样本数"]
                else None
            )
            dynasty_data.append(
                {
                    "朝代": dynasty,
                    "出现次数": data["出现次数"],
                    "平均情感得分": dynasty_avg,
                    "情感统计": dict(data["情感统计"])
                }
            )

        text_corpus = "\n".join(entry["文本集合"])
        keywords = []
        if text_corpus.strip():
            for word, weight in jieba_analyse.extract_tags(
                text_corpus, topK=30, withWeight=True
            ):
                keywords.append({"word": word, "weight": weight})

        geo_stats.append(
            {
                "名称": name,
                "类型": entry["类型"],
                "现代对应": entry["现代对应"],
                "总出现次数": entry["总出现次数"],
                "情感统计": dict(entry["情感统计"]),
                "平均情感得分": avg_score,
                "出现诗人": sorted(entry["出现诗人"]),
                "坐标": coords,
                "朝代统计": dynasty_data
            }
        )

        sentiment_trend.append(
            {
                "名称": name,
                "数据": dynasty_data
            }
        )

        keyword_clouds.append(
            {
                "名称": name,
                "关键词": keywords
            }
        )

    # 对每个地名的诗句进行随机排序
    for name in poetry_quotes_by_geo:
        random.shuffle(poetry_quotes_by_geo[name])
    
    # 转换为普通字典并过滤掉没有诗句的地名
    poetry_quotes_dict = {
        name: quotes 
        for name, quotes in poetry_quotes_by_geo.items() 
        if quotes  # 只保留有诗句的地名
    }
    
    # 过滤geo_stats，只保留有诗句的地名
    geo_names_with_quotes = set(poetry_quotes_dict.keys())
    geo_stats_filtered = [stat for stat in geo_stats if stat["名称"] in geo_names_with_quotes]
    sentiment_trend_filtered = [trend for trend in sentiment_trend if trend["名称"] in geo_names_with_quotes]
    keyword_clouds_filtered = [cloud for cloud in keyword_clouds if cloud["名称"] in geo_names_with_quotes]

    return geo_stats_filtered, sentiment_trend_filtered, keyword_clouds_filtered, poetry_quotes_dict


def build_poet_paths(author_trajectories, coordinate_map):
    """
    构建诗人轨迹数据
    """
    poet_paths = []

    for author, data in author_trajectories.items():
        path_points = []
        for occ in data.get("出现顺序", []):
            coords = occ.get("经纬度")
            if not coords:
                coords = coordinate_map.get(occ.get("地点")) or coordinate_map.get(occ.get("现代对应"))
            if not coords:
                continue
            path_points.append(
                {
                    "地点": occ.get("地点"),
                    "lat": coords.get("lat"),
                    "lng": coords.get("lng"),
                    "原文出现": occ.get("原文出现"),
                    "首次出现诗篇": occ.get("首次出现诗篇"),
                    "类型": occ.get("类型"),
                    "现代对应": occ.get("现代对应")
                }
            )

        reference_routes = []
        for route in data.get("主要行迹（资料）", []):
            coords = route.get("经纬度")
            if not coords:
                coords = coordinate_map.get(route.get("地点"))
            if not coords:
                continue
            reference_routes.append(
                {
                    "地点": route.get("地点"),
                    "lat": coords.get("lat"),
                    "lng": coords.get("lng"),
                    "时期": route.get("时期")
                }
            )

        poet_paths.append(
            {
                "作者": author,
                "籍贯": data.get("籍贯"),
                "诗歌轨迹": path_points,
                "资料行迹": reference_routes,
                "诗歌地统计": data.get("诗歌出现地统计", [])
            }
        )

    return poet_paths


def export_analysis_outputs(poem_results, author_trajectories, coordinate_map):
    """
    导出分析结果到 JSON 文件
    """
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    # 加载地理实体字典以获取别名信息
    geo_entities_path = os.path.join(DATA_DIR, "geo_entities.json")
    geo_entities_dict = {}
    if os.path.exists(geo_entities_path):
        try:
            with open(geo_entities_path, "r", encoding="utf-8") as f:
                geo_entities_dict = json.load(f)
        except Exception:
            pass
    
    geo_stats, sentiment_trend, keyword_clouds, poetry_quotes_by_geo = aggregate_geo_statistics(
        poem_results, coordinate_map, geo_entities_dict
    )
    poet_paths = build_poet_paths(author_trajectories, coordinate_map)

    outputs = {
        "geo_stats.json": geo_stats,
        "sentiment_trend.json": sentiment_trend,
        "keyword_clouds.json": keyword_clouds,
        "poet_paths.json": poet_paths,
        "poetry_quotes_by_geo.json": poetry_quotes_by_geo
    }

    for filename, data in outputs.items():
        path = os.path.join(output_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"写入 {filename} 时出错：{exc}")

    print(f"已导出数据文件至 {output_dir}")


def main():
    # 加载诗词数据
    poems = load_poetry_from_local(max_poems=500)

    if not poems:
        print("未找到诗词数据，请确认数据集是否已下载。")
        return

    analyzer = PoetryAnalyzer()

    # 分析全部诗词
    analysis = analyzer.analyze_poetry_collection(poems)

    poem_results = analysis["poems"]
    author_trajectories = analysis["author_trajectories"]

    # 导出数据文件
    export_analysis_outputs(poem_results, author_trajectories, analyzer.geo_coordinates)

    print("=== 诗词分析示例（随机5首） ===")
    sample_display = random.sample(poem_results, min(5, len(poem_results)))
    for result in sample_display:
        print(f"标题：{result['title']}")
        print(f"作者：{result['author']}")
        print("地理实体：")
        if result["geo_entities"]:
            for geo in result["geo_entities"]:
                print(
                    f"  - {geo['名称']}（类型：{geo['类型']}，现代对应：{geo['现代对应']}，原文：{','.join(geo['原文出现'])}）"
                )
        else:
            print("  - 未识别到地理实体")
        print(f"情感分析：{result['sentiment']}")
        print("-" * 60)

    print("\n=== 作者轨迹示例 ===")
    if not author_trajectories:
        print("未提取到包含地理实体的诗人轨迹，请尝试扩大样本或补充词典。")
    else:
        for author, info in list(author_trajectories.items())[:5]:
            print(f"作者：{author}")
            print(f"籍贯：{info.get('籍贯', '未知')}")
            print("资料中的主要行迹：")
            if info.get("主要行迹（资料）"):
                for entry in info["主要行迹（资料）"]:
                    print(f"  - {entry.get('时期', '未知时期')}：{entry.get('地点')}")
            else:
                print("  - 未提供资料")

            print("诗歌出现地统计：")
            for stat in info.get("诗歌出现地统计", [])[:5]:
                print(f"  - {stat['地点']}：{stat['出现次数']} 次")

            print("诗歌出现顺序（前5条）：")
            for occ in info.get("出现顺序", [])[:5]:
                print(
                    f"  - {occ['地点']}（原文：{','.join(occ['原文出现'])}，首次出现于《{occ['首次出现诗篇']}》，类型：{occ['类型']}）"
                )
            print("-" * 60)


if __name__ == "__main__":
    main()