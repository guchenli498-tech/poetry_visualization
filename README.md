# 中华诗词山河文化地图可视化系统

一个基于Python的数据可视化项目，用于分析和展示中华古诗词中的地理意象分布、情感趋势以及相关诗句。

## 📋 项目简介

本项目通过分析全唐诗、宋词等古诗词数据，提取其中的地理实体（山川、河流、城市等），并进行情感分析、关键词提取等处理，最终生成交互式的可视化仪表板。系统支持：

- 🗺️ 地理热度地图：展示诗词中提及的地理位置分布
- 📊 情感分析：分析不同地理意象的情感倾向
- 📈 朝代统计：统计各朝代对地理意象的提及情况
- ☁️ 关键词云：展示与地理意象相关的关键词
- 🔗 诗人网络：展示诗人与地理意象的关联关系
- 📝 诗句展示：显示包含特定地理意象的诗句，支持分页浏览

## 📁 项目结构

```
poetry_visualization/
├── chinese-poetry/          # 诗词数据目录
│   ├── 全唐诗/              # 全唐诗数据
│   ├── 宋词/                # 宋词数据
│   └── ...                  # 其他诗词数据
│
├── data/                    # 数据配置文件
│   ├── geo_entities.json    # 地理实体词典（地名、别名、类型）
│   ├── geo_coordinates.json # 地理坐标数据
│   ├── author_profiles.json # 诗人资料
│   └── ...                  # 其他数据文件
│
├── templates/              # HTML模板
│   └── dashboard_template.html  # 仪表板模板
│
├── output/                  # 输出文件目录
│   ├── poetry_dashboard.html    # 生成的可视化页面
│   ├── geo_stats.json           # 地理统计结果
│   ├── sentiment_trend.json     # 情感趋势数据
│   ├── keyword_clouds.json      # 关键词云数据
│   ├── poet_paths.json          # 诗人轨迹数据
│   └── poetry_quotes_by_geo.json # 诗句数据
│
├── docs/                    # GitHub Pages部署目录
│   └── index.html           # 部署用的HTML文件
│
├── poetey_analysis.py       # 主分析脚本：提取地理实体、情感分析
├── visual_dashboard.py      # 可视化生成脚本：生成交互式仪表板
├── generate_geo_only.py     # 地理可视化专用脚本
└── show_all_geo.py          # 地理数据展示脚本
```

## 🚀 快速开始

### 环境要求

- Python 3.7+
- 依赖包（见下方）

### 安装依赖

```bash
pip install jieba snownlp pyecharts jinja2 tqdm
```

### 使用步骤

1. **准备数据**
   - 确保 `chinese-poetry/` 目录下有诗词数据文件（JSON格式）

2. **运行分析**
   ```bash
   python poetey_analysis.py
   ```
   - 这会分析诗词数据，提取地理实体、进行情感分析
   - 生成统计结果文件到 `output/` 目录
   - 默认分析50000首诗（可在 `poetey_analysis.py` 中修改 `max_poems` 参数）

3. **生成可视化**
   ```bash
   python visual_dashboard.py
   ```
   - 读取分析结果，生成交互式可视化页面
   - 输出文件：`output/poetry_dashboard.html`

4. **查看结果**
   - 在浏览器中打开 `output/poetry_dashboard.html`
   - 或访问 GitHub Pages：https://guchenli498-tech.github.io/poetry_visualization/

## 🎯 核心功能

### 1. 地理实体提取
- 从诗词文本中识别地理实体（城市、山川、河流等）
- 支持别名匹配（如"长江"的别名"大江"、"扬子江"）
- 过滤抽象概念和通用词

### 2. 情感分析
- 使用SnowNLP进行基础情感分析
- 多维度情感分类：非常正面、中性偏正面、中性、中性偏负面、非常负面
- 按朝代统计情感分布

### 3. 诗句提取
- 提取包含特定地理意象的诗句片段
- 支持分页浏览（每页10首，左右分栏显示）
- 显示格式：诗句-诗人《诗名》

### 4. 交互式可视化
- **地图点击**：点击地图上的点，查看该地名的详细信息
- **热门榜点击**：点击热门山河意象榜中的地名，切换显示
- **动态更新**：所有图表和诗句列表会同步更新

## 📊 数据文件说明

### 输入数据
- `data/geo_entities.json`: 地理实体词典，定义地名、类型、别名
- `data/geo_coordinates.json`: 地理坐标数据，用于地图定位
- `data/author_profiles.json`: 诗人资料，包含籍贯、行迹等信息

### 输出数据
- `geo_stats.json`: 地理统计结果（出现次数、情感统计、朝代分布等）
- `sentiment_trend.json`: 情感趋势数据（按朝代）
- `keyword_clouds.json`: 关键词云数据
- `poet_paths.json`: 诗人轨迹数据
- `poetry_quotes_by_geo.json`: 每个地名对应的诗句列表

## 🔧 配置说明

### 修改分析数量
在 `poetey_analysis.py` 的 `main()` 函数中修改：
```python
poems = load_poetry_from_local(max_poems=50000)  # 修改这里的数字
```

### 添加地理实体
编辑 `data/geo_entities.json`，添加新的地理实体：
```json
{
  "地名": {
    "type": "类型（城市/山脉/河流等）",
    "aliases": ["别名1", "别名2"],
    "modern_name": "现代对应名称"
  }
}
```

### 添加坐标数据
编辑 `data/geo_coordinates.json`，添加坐标：
```json
{
  "地名": {
    "lat": 纬度,
    "lng": 经度
  }
}
```

## 🌐 GitHub Pages 部署

项目已配置 GitHub Pages，部署步骤：

1. 确保 `docs/index.html` 是最新的可视化页面
2. 在 GitHub 仓库设置中：
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: /docs
3. 访问：https://guchenli498-tech.github.io/poetry_visualization/

## 👥 制作组

**14组**
- 朱宝仪 2024301021152
- 张健楠 2024301021053
- 杨智明 2024301021157
- 杨淇超 2024301021098

## 📝 技术栈

- **数据处理**: Python, jieba, SnowNLP
- **可视化**: PyECharts
- **模板引擎**: Jinja2
- **前端**: HTML, CSS, JavaScript

## 📄 许可证

本项目使用开放数据集，数据来源：
- 全唐诗
- 宋词
- 其他开放诗词数据集

## 🔗 相关链接

- GitHub仓库: https://github.com/guchenli498-tech/poetry_visualization
- 在线演示: https://guchenli498-tech.github.io/poetry_visualization/

## 📌 注意事项

- 首次运行需要下载jieba词典（会自动下载）
- 分析大量数据（如50000首）可能需要较长时间
- 确保有足够的内存处理大型数据集
- 输出文件会覆盖之前的分析结果

## 🐛 问题反馈

如有问题或建议，请在GitHub仓库提交Issue。

