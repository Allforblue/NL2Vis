import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import os
import numpy as np
import json
import plotly.express as px

# 页面配置
st.set_page_config(layout="wide", page_title="NYC Taxi Flow Shading Map")

# 1. 路径与数据加载
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(current_dir, '..', 'data'))
parquet_path = os.path.join(data_dir, 'yellow_tripdata_2025-01.parquet')
shp_path = os.path.join(data_dir, 'taxi_zones.shp')
lookup_path = os.path.join(data_dir, 'taxi_zone_lookup.csv')


@st.cache_data
def load_flow_data():
    # A. 处理地理数据
    gdf_raw = gpd.read_file(shp_path)
    # 合并重复 ID 并修复投影
    gdf = gdf_raw.dissolve(by='LocationID').reset_index()
    gdf_projected = gdf.to_crs(epsg=2263)
    centroids = gdf_projected.geometry.centroid.to_crs(epsg=4326)
    gdf['lon'] = centroids.x
    gdf['lat'] = centroids.y
    gdf = gdf.to_crs(epsg=4326)
    geojson = json.loads(gdf.to_json())

    # 坐标字典
    coords_dict = gdf.set_index('LocationID')[['lon', 'lat']].to_dict('index')

    # B. 加载业务数据
    df = pd.read_parquet(parquet_path, columns=['PULocationID', 'DOLocationID'])
    df['PULocationID'] = df['PULocationID'].astype(int)
    df['DOLocationID'] = df['DOLocationID'].astype(int)
    df = df[(df['PULocationID'] <= 263) & (df['DOLocationID'] <= 263)]

    # 全局 OD 聚合
    flow_agg = df.groupby(['PULocationID', 'DOLocationID']).size().reset_index(name='flow_count')

    # C. 加载名字映射
    lookup = pd.read_csv(lookup_path)
    lookup['Zone'] = lookup['Zone'].fillna("Unknown")
    lookup['LocationID'] = lookup['LocationID'].astype(int)

    return flow_agg, coords_dict, lookup, gdf, geojson


flow_df, coords, lookup, gdf, geojson = load_flow_data()

# 2. 界面设计
st.title("🏹 NYC 出租车流向着色图 (OD Choropleth)")
st.sidebar.header("筛选器")

all_zones = sorted(lookup['Zone'].unique())
selected_origin_name = st.sidebar.selectbox("选择起点区域 (Origin):", all_zones,
                                            index=all_zones.index("JFK Airport") if "JFK Airport" in all_zones else 0)

origin_id = int(lookup[lookup['Zone'] == selected_origin_name]['LocationID'].values[0])

# --- 数据准备 ---
# 找出从该起点出发的所有流向数据
dest_flows = flow_df[flow_df['PULocationID'] == origin_id].copy()

# 为了让地图完整显示所有区域，我们将流向数据合并到完整的区域列表中
# 这样没有去往的区域会显示为 0，而有去往的区域会着色
full_map_data = lookup[['LocationID', 'Zone']].merge(dest_flows, left_on='LocationID', right_on='DOLocationID',
                                                     how='left')
full_map_data['flow_count'] = full_map_data['flow_count'].fillna(0)

# 对数处理：用于颜色轴
full_map_data['log_flow'] = np.log10(full_map_data['flow_count'] + 1)

# --- 修改部分：计算原始数据刻度逻辑 ---
max_raw = full_map_data['flow_count'].max()
# 定义一组候选的原始数值刻度
candidate_ticks = [0, 1, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
# 筛选出小于最大值的刻度，并加上最大值
raw_ticks = [t for t in candidate_ticks if t < max_raw]
raw_ticks.append(int(max_raw))
# 转换为对数空间的位置
tick_vals = [np.log10(x + 1) for x in raw_ticks]
# 转换为显示的文本标签
tick_text = [str(x) for x in raw_ticks]
# ------------------------------------

# 3. 构建 Plotly 图表
fig = go.Figure()

# A. 核心图层：对去向区域进行着色 (Choropleth)
fig.add_trace(go.Choroplethmap(
    geojson=geojson,
    locations=full_map_data['LocationID'],
    z=full_map_data['log_count'] if 'log_count' in full_map_data else full_map_data['log_flow'],
    featureidkey="properties.LocationID",
    colorscale="Plasma",  # 紫-橙色系
    zmin=0,
    zmax=full_map_data['log_flow'].max(),
    marker_opacity=0.7,
    marker_line_width=0.5,
    # 修改此处 colorbar 配置
    colorbar=dict(
        title="订单量",
        tickvals=tick_vals,
        ticktext=tick_text
    ),
    # 悬停内容
    text=full_map_data['Zone'] + "<br>前往该地订单数: " + full_map_data['flow_count'].astype(int).astype(str),
    hoverinfo="text"
))

# # B. 辅助图层：绘制流向线 (Lines)
# # 仅展示前 30 条主要流线，避免遮挡颜色
# top_30_flows = dest_flows.sort_values(by='flow_count', ascending=False).head(30)
# if origin_id in coords:
#     o_lon, o_lat = coords[origin_id]['lon'], coords[origin_id]['lat']
#     lons, lats = [], []
#     for _, row in top_30_flows.iterrows():
#         d_id = int(row['DOLocationID'])
#         if d_id in coords:
#             lons.extend([o_lon, coords[d_id]['lon'], None])
#             lats.extend([o_lat, coords[d_id]['lat'], None])
#
#     fig.add_trace(go.Scattermap(
#         lon=lons, lat=lats,
#         mode='lines',
#         line=dict(width=5, color='white'),  # 在彩色背景上用白色细线效果最好
#         opacity=0.4,
#         hoverinfo='skip'
#     ))

# B. 辅助图层：绘制流向线 (Lines) 与 箭头 (Arrows)
top_30_flows = dest_flows.sort_values(by='flow_count', ascending=False).head(30)

if origin_id in coords:
    o_lon, o_lat = coords[origin_id]['lon'], coords[origin_id]['lat']

    # 获取红色系颜色列表 (从浅红到深红)
    red_colors = px.colors.sequential.Reds

    # 获取当前 30 条流向的最大最小值，用于颜色映射
    if not top_30_flows.empty:
        max_f = top_30_flows['flow_count'].max()
        min_f = top_30_flows['flow_count'].min()

        for _, row in top_30_flows.iterrows():
            d_id = int(row['DOLocationID'])
            if d_id in coords:
                d_lon, d_lat = coords[d_id]['lon'], coords[d_id]['lat']
                count = row['flow_count']

                # 1. 对数值进行对数转换 (使用 np.log10，+1 是为了处理 0 的情况)
                log_count = np.log10(count + 1)
                log_min = np.log10(min_f + 1)
                log_max = np.log10(max_f + 1)

                # 2. 对数归一化 (计算在对数空间中的 0-1 比例)
                # 防止除以 0 (当 max_f == min_f 时)
                if log_max > log_min:
                    norm_val = (log_count - log_min) / (log_max - log_min)
                else:
                    norm_val = 1.0  # 如果只有一个值，默认取最深色

                # 3. 映射到红色系索引
                # 同样，通过 int(norm_val * (len - 1)) 选色
                color_idx = int(norm_val * (len(red_colors) - 1))
                line_color = red_colors[color_idx]

                # 1. 绘制线条
                fig.add_trace(go.Scattermap(
                    lon=[o_lon, d_lon],
                    lat=[o_lat, d_lat],
                    mode='lines',
                    line=dict(width=2, color=line_color),
                    opacity=0.8,
                    showlegend=False,
                    hoverinfo='skip'
                ))

                # 2. 绘制箭头 (在终点位置放一个三角形)
                # 注：Scattermap 无法自动根据线条旋转三角形，
                # 但我们可以使用标记来增强“终点”的视觉感受
                fig.add_trace(go.Scattermap(
                    lon=[d_lon],
                    lat=[d_lat],
                    mode='markers',
                    marker=dict(
                        size=10,
                        symbol='triangle',  # 三角形符号
                        color=line_color,
                    ),
                    showlegend=False,
                    # 终点悬停时显示信息
                    text=f"去往: {lookup[lookup['LocationID'] == d_id]['Zone'].values[0]}<br>数量: {int(count)}",
                    hoverinfo="text"
                ))

# 4. 布局设置
fig.update_layout(
    map=dict(
        style="carto-positron",  # 亮色底图，方便看清边界
        center={"lat": 40.7128, "lon": -74.0060},
        zoom=10
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

# 5. 展示
col1, col2 = st.columns([3, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.write(f"### {selected_origin_name} 去向排行")
    display_df = top_30_flows.head(15).merge(lookup[['LocationID', 'Zone']], left_on='DOLocationID',
                                             right_on='LocationID')
    st.dataframe(display_df[['Zone', 'flow_count']], hide_index=True)
    st.info("地图颜色代表该区域作为目的地的订单密度（对数缩放）。直线标注了前 30 个最热门的去向。")