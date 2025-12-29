```
NL2Vis/                          # 项目根目录
├── data/                        # 原始数据文件夹
│   ├── yellow_tripdata_2025-01.parquet  # 纽约出租车行程数据
│   ├── taxi_zones.shp           # 区域边界形状文件 (ESRI Shapefile)
│   ├── taxi_zone_lookup.csv     # 区域 ID 与名称对照表
│   └── ...                      # 其他地图关联文件 (.dbf, .shx, .prj)
│
├── NL-STV/                      # 核心源代码包 (Core Package)
│   ├── __init__.py              # 使其成为一个可导入的 Python 包
│   ├── component/               # 组件模块：存放底层处理逻辑
│   │   ├── __init__.py
│   │   ├── data_loader.py       # 封装数据读取与预处理逻辑 (Geopandas/Pandas)
│   │   ├── nl_processor.py      # 将自然语言指令解析为过滤/分析条件的逻辑
│   │   └── spatial_utils.py     # 坐标转换、中心点计算、多边形合并逻辑
│   │
│   └── web/                     # Web 展示模块：基于 Streamlit 的仪表盘
│       ├── __init__.py
│       ├── dashboard.py         # 仪表盘主程序 (整合时空趋势图)
│       └── flow_visualizer.py   # 轨迹流向图的展示逻辑
│
├── test_code/                   # 测试与实验脚本 (Sandbox)
│   ├── test_read_data.py        # 初始读取测试
│   ├── test_graph.py            # 基础热力图测试
│   ├── test_dashboard.py        # 联动仪表盘原型
│   ├── test_link_mode.py        # 模型连接测试
│   └── test_flow_map.py         # 轨迹流向图原型
│
├── README.md                    # 项目说明文档 (简介、安装、运行指南)
├── Structure.md                 # 项目详细架构与技术栈描述
└── requirements.txt             # 项目依赖清单 (pandas, streamlit, plotly, geopandas等)
```
