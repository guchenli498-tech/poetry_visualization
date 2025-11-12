import json
import os
from collections import defaultdict
from datetime import datetime

from pyecharts import options as opts
from pyecharts.charts import Bar, Geo, Pie, WordCloud, Line, Graph
from pyecharts.commons.utils import JsCode
from pyecharts.globals import GeoType, CurrentConfig, ThemeType
from jinja2 import Environment, FileSystemLoader


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
EXCLUDED_NAMES = {"千山","江山","山林","青山", "四海", "江湖", "山川","山河","西山","东山","天下", "九州", "五湖", "六合", "八荒", "九域", "四方", "宇内", "寰中", "江表", "河朔", "塞北", "岭南", "漠北", "中原", "南疆", "北疆", "关内", "关外", "河东", "河西", "山南", "山北", "淮左", "淮右", "山水", "四面山", "山河大地", "山阜", "峽山", "峡山", "河明", "浮川", "居海", "如海", "福海", "海陽", "海國", "海霧江", "湖江", "北湖", "青草湖", "柳邊湖", "明河", "陂湖", "好山", "山開南國", "莫指雲山", "中峰", "中台", "陽洲", "花洲", "四海九州"}


def load_json(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_dynasty_bar(sentiment_trend_data) -> Bar:
    dynasty_counter = defaultdict(int)
    for entry in sentiment_trend_data:
        for record in entry["数据"]:
            dynasty = record["朝代"]
            dynasty_counter[dynasty] += record["出现次数"]

    dynasties = []
    counts = []
    for dynasty, count in sorted(dynasty_counter.items(), key=lambda x: x[1], reverse=True):
        if dynasty == "未知":
            continue
        dynasties.append(dynasty)
        counts.append(count)

    bar = (
        Bar(init_opts=opts.InitOpts(width="100%", height="320px", theme=ThemeType.DARK))
        .add_xaxis(dynasties)
        .add_yaxis("诗词提及次数", counts, category_gap="35%")
        .set_global_opts(
            title_opts=opts.TitleOpts(title="各朝代地理意象提及次数"),
            yaxis_opts=opts.AxisOpts(name="次数"),
            xaxis_opts=opts.AxisOpts(name="朝代"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )
    return bar


def build_geo_map(geo_stats_data) -> Geo:
    # 过滤出有坐标的地理实体
    valid_geo_data = []
    coordinate_map = {}
    for entry in geo_stats_data:
        coords = entry.get("坐标")
        if isinstance(coords, dict):
            lng, lat = coords.get("lng"), coords.get("lat")
        elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
            lng, lat = coords[0], coords[1]
        else:
            continue
        if lng is None or lat is None:
            continue
        name = entry["名称"]
        count = entry.get("总出现次数", 0)
        if count <= 0:
            continue
        valid_geo_data.append((name, count))
        coordinate_map[name] = (lng, lat)

    valid_geo_data.sort(key=lambda x: x[1], reverse=True)
    
    # 创建地图
    geo = Geo(
        init_opts=opts.InitOpts(
            width="100%",
            height="480px",
            theme=ThemeType.DARK,
            bg_color="rgba(0,0,0,0)",
        )
    )
    geo.chart_id = "geo_chart"
    geo.add_schema(
        maptype="china",
        is_roam=True,
        itemstyle_opts=opts.ItemStyleOpts(area_color="#102347", border_color="#4b8ad3"),
        emphasis_itemstyle_opts=opts.ItemStyleOpts(area_color="#1c3d68"),
        label_opts=opts.LabelOpts(is_show=False),
    )

    for name, _ in valid_geo_data[:150]:
        lng, lat = coordinate_map[name]
        geo.add_coordinate(name, lng, lat)

    if valid_geo_data:
        geo.add(
            "山河热度",
            valid_geo_data[:150],
            type_=GeoType.EFFECT_SCATTER,
            symbol_size=JsCode("function (data) { return Math.max(12, Math.min(data[2] / 3, 32)); }"),
            itemstyle_opts=opts.ItemStyleOpts(color="#ffd166"),
        )
        geo.set_series_opts(
            label_opts=opts.LabelOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode(
                    "function (params) { return params.name + '<br/>提及次数：' + params.value[2]; }"
                )
            ),
        )
        geo.set_global_opts(
            title_opts=opts.TitleOpts(is_show=False),
            visualmap_opts=opts.VisualMapOpts(
                max_=max(v for _, v in valid_geo_data),
                pos_right="3%",
                pos_top="middle",
                dimension=2,
                range_color=["#6c93ff", "#2ad9ff", "#ffe470"],
                textstyle_opts=opts.TextStyleOpts(color="#d3e8ff"),
            ),
        )
    else:
        geo.set_global_opts(title_opts=opts.TitleOpts(title="诗词中的山河热度图"))
    
    return geo


def build_sentiment_pie(sentiment_stats, location_name: str) -> Pie:
    data_pairs = (
        [(label, value) for label, value in sentiment_stats.items()]
        if sentiment_stats
        else [("暂无数据", 1)]
    )
    pie = Pie(init_opts=opts.InitOpts(width="100%", height="320px", theme=ThemeType.DARK))
    pie.chart_id = "sentiment_pie"
    pie.add(
        "",
        data_pairs,
        radius=["35%", "65%"],
        center=["42%", "55%"],
        rosetype="radius",
    )
    pie.set_global_opts(
        title_opts=opts.TitleOpts(title=f"{location_name} 情感分布", pos_left="center"),
        legend_opts=opts.LegendOpts(
            orient="vertical",
            pos_right="6%",
            pos_top="20%",
            textstyle_opts=opts.TextStyleOpts(color="#d3e8ff"),
        ),
    )
    pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
    return pie


def build_keyword_cloud(keyword_items, location_name: str) -> WordCloud:
    if keyword_items:
        data = [(item["word"], item["weight"]) for item in keyword_items]
    else:
        data = [("暂无数据", 1.0)]
    wordcloud = WordCloud(
        init_opts=opts.InitOpts(width="100%", height="320px", theme=ThemeType.DARK)
    )
    wordcloud.chart_id = "keyword_cloud"
    wordcloud.add("", data, word_size_range=[12, 60], shape="circle")
    wordcloud.set_global_opts(title_opts=opts.TitleOpts(title=f"{location_name} 关键词云"))
    return wordcloud


def build_poet_graph(poet_list, location_name: str) -> Graph:
    nodes = [{"name": location_name, "symbolSize": 42, "category": 0, "draggable": False}]
    links = []

    for poet in poet_list[:10]:
        poet_name = poet["name"]
        count = poet.get("count", 1)
        nodes.append(
            {
                "name": poet_name,
                "symbolSize": max(18, min(18 + count * 2, 38)),
                "category": 1,
                "draggable": False,
            }
        )
        links.append({"source": location_name, "target": poet_name, "value": count})

    if len(nodes) == 1:
        nodes.append({"name": "数据不足", "symbolSize": 18, "category": 1, "draggable": False})
        links.append({"source": location_name, "target": "数据不足", "value": 0})

    graph = Graph(init_opts=opts.InitOpts(width="100%", height="320px", theme=ThemeType.DARK))
    graph.chart_id = "poet_graph"
    graph.add(
        series_name="诗人共吟网络",
        nodes=nodes,
        links=links,
        categories=[{"name": "地点"}, {"name": "诗人"}],
        layout="circular",
        is_rotate_label=True,
    )
    graph.set_global_opts(
        title_opts=opts.TitleOpts(title=f"{location_name} 共吟网络", pos_left="center"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    graph.set_series_opts(
        label_opts=opts.LabelOpts(position="right"),
        linestyle_opts=opts.LineStyleOpts(color="#67c5ff", width=1.2, opacity=0.7),
    )
    return graph


def compute_overview_stats(geo_stats_data):
    total_mentions = sum(entry["总出现次数"] for entry in geo_stats_data)
    unique_geos = len(geo_stats_data)
    poets = set()
    for entry in geo_stats_data:
        poets.update(entry.get("出现诗人", []))
    unique_poets = len(poets)
    return {
        "total_mentions": total_mentions,
        "unique_geos": unique_geos,
        "unique_poets": unique_poets
    }


def select_hot_geos(geo_stats, limit=8):
    keywords = ["山", "江", "河", "湖", "州", "岭", "川", "溪", "峡", "关", "台", "洲", "海", "泉", "峰", "谷"]
    excluded = {"山水"} | EXCLUDED_NAMES
    filtered = []
    for entry in sorted(geo_stats, key=lambda x: x["总出现次数"], reverse=True):
        name = entry["名称"]
        if len(name) < 2:
            continue
        if not any(k in name for k in keywords):
            continue
        if name in excluded:
            continue
        if name in EXCLUDED_NAMES:
            continue
        filtered.append(entry)
        if len(filtered) >= limit:
            break
    if len(filtered) < limit:
        filtered.extend(entry for entry in geo_stats if entry not in filtered)
        filtered = filtered[:limit]
    return filtered


def prepare_location_details(geo_stats, keyword_clouds, sentiment_trend, poet_paths):
    keyword_map = {entry["名称"]: entry.get("关键词", []) for entry in keyword_clouds}
    trend_map = {entry["名称"]: entry.get("数据", []) for entry in sentiment_trend}

    poet_counter = defaultdict(lambda: defaultdict(int))
    for poet in poet_paths:
        author = poet.get("作者")
        for stat in poet.get("诗歌地统计", []):
            loc_name = stat.get("地点")
            count = stat.get("出现次数", 0)
            if loc_name and author and loc_name not in EXCLUDED_NAMES:
                poet_counter[loc_name][author] += count

    location_details = {}
    for entry in geo_stats:
        name = entry["名称"]
        if name in EXCLUDED_NAMES:
            continue
        poets_detail = [
            {"name": poet_name, "count": count}
            for poet_name, count in sorted(
                poet_counter.get(name, {}).items(), key=lambda x: x[1], reverse=True
            )
        ]
        location_details[name] = {
            "type": entry.get("类型"),
            "modern": entry.get("现代对应"),
            "total": entry.get("总出现次数", 0),
            "avg_score": entry.get("平均情感得分"),
            "sentiments": entry.get("情感统计", {}),
            "timeline": trend_map.get(name) or entry.get("朝代统计", []),
            "keywords": keyword_map.get(name, []),
            "poets": poets_detail,
        }

    return location_details


def collect_dependencies(charts):
    deps = []
    for chart in charts.values():
        # 尝试获取 js_dependencies，如果是 OrderedSet 则转换为列表
        chart_deps = chart.js_dependencies if hasattr(chart, 'js_dependencies') else []
        if hasattr(chart_deps, '__iter__') and not isinstance(chart_deps, str):
            deps.extend(list(chart_deps))
        elif chart_deps:
            deps.append(chart_deps)
    return list(set(deps))  # 去重并转换为列表


def render_dashboard(template_name, context, output_path):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(template_name)
    html = template.render(**context)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"可视化页面已生成：{output_path}")


def build_dashboard():
    geo_stats = [
        entry for entry in load_json("geo_stats.json")
        if entry.get("名称") not in EXCLUDED_NAMES
    ]
    sentiment_trend = [
        entry for entry in load_json("sentiment_trend.json")
        if entry.get("名称") not in EXCLUDED_NAMES
    ]
    keyword_clouds = [
        entry for entry in load_json("keyword_clouds.json")
        if entry.get("名称") not in EXCLUDED_NAMES
    ]
    poet_paths_raw = load_json("poet_paths.json")
    poet_paths = []
    for poet in poet_paths_raw:
        filtered_stats = [
            stat for stat in poet.get("诗歌地统计", [])
            if stat.get("地点") not in EXCLUDED_NAMES
        ]
        filtered_sequence = [
            occ for occ in poet.get("出现顺序", [])
            if occ.get("地点") not in EXCLUDED_NAMES
        ]
        poet_paths.append(
            {
                **poet,
                "诗歌地统计": filtered_stats,
                "出现顺序": filtered_sequence
            }
        )

    location_details = prepare_location_details(
        geo_stats, keyword_clouds, sentiment_trend, poet_paths
    )

    # 默认地点：优先选择有坐标的出现频率最高地点
    default_location = None
    for entry in geo_stats:
        coords = entry.get("坐标")
        if coords:
            default_location = entry["名称"]
            break
    if not default_location and geo_stats:
        default_location = geo_stats[0]["名称"]
    if not default_location:
        default_location = "未指定"

    default_detail = location_details.get(default_location, {
        "sentiments": {},
        "keywords": [],
        "timeline": [],
        "poets": [],
        "total": 0,
    })

    charts = {
        "map_chart": build_geo_map(geo_stats),
        "pie_chart": build_sentiment_pie(default_detail.get("sentiments", {}), default_location),
        "wordcloud_chart": build_keyword_cloud(default_detail.get("keywords", []), default_location),
        "network_chart": build_poet_graph(default_detail.get("poets", []), default_location),
    }

    chart_embeds = {name: chart.render_embed() for name, chart in charts.items()}
    
    # 生成脚本标签
    scripts = "\n".join(
        f'<script src="{CurrentConfig.ONLINE_HOST}{dep}.js"></script>' 
        for dep in collect_dependencies(charts)
    )

    overview = compute_overview_stats(geo_stats)
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    context = {
        "scripts": scripts,
        **chart_embeds,
        "overview": overview,
        "current_time": now_str,
        "default_location": default_location,
        "location_details": json.dumps(location_details, ensure_ascii=False),
        "hot_geos": select_hot_geos(geo_stats, limit=8)
    }

    output_path = os.path.join(OUTPUT_DIR, "poetry_dashboard.html")
    render_dashboard("dashboard_template.html", context, output_path)


if __name__ == "__main__":
    build_dashboard()

