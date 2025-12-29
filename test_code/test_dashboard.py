import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import os
import json
import numpy as np

# 设置页面宽度
st.set_page_config(layout="wide", page_title="NYC Taxi Spatiotemporal Dashboard")

# 1. 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(current_dir, '..', 'data'))
parquet_path = os.path.join(data_dir, 'yellow_tripdata_2025-01.parquet')
shp_path = os.path.join(data_dir, 'taxi_zones.shp')
lookup_path = os.path.join(data_dir, 'taxi_zone_lookup.csv')


@st.cache_data
def load_data():
    try:
        # A. 加载地理数据
        if not os.path.exists(shp_path):
            st.error(f"找不到文件: {shp_path}")
            return None, None, None, None

        gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
        geojson = json.loads(gdf.to_json())

        # B. 加载行程数据
        df = pd.read_parquet(parquet_path, columns=['tpep_pickup_datetime', 'PULocationID'])
        df['hour'] = pd.to_datetime(df['tpep_pickup_datetime']).dt.hour

        # C. 加载名字对照表并清理
        lookup = pd.read_csv(lookup_path)
        lookup['Zone'] = lookup['Zone'].fillna("Unknown").astype(str)
        lookup['Borough'] = lookup['Borough'].fillna("Unknown").astype(str)
        lookup['LocationID'] = lookup['LocationID'].astype(int)

        return gdf, geojson, df, lookup
    except Exception as e:
        st.error(f"加载数据时发生错误: {e}")
        return None, None, None, None


# 执行加载
gdf, geojson, df, lookup = load_data()

if gdf is None:
    st.stop()

# 2. 仪表盘标题
st.title("🚖 NYC 出租车时空联动仪表盘")

# 3. 侧边栏交互
st.sidebar.header("筛选器")
all_zones = sorted(lookup['Zone'].unique())
selected_zone = st.sidebar.selectbox(
    "选择要分析的区域 (Zone):",
    all_zones,
    index=all_zones.index("Upper East Side South") if "Upper East Side South" in all_zones else 0
)

selected_id = lookup[lookup['Zone'] == selected_zone]['LocationID'].values[0]

# --- 数据聚合与处理 ---
# A. 全局热力图数据聚合
map_data = df['PULocationID'].value_counts().reset_index(name='total_pickups')
map_data.columns = ['LocationID', 'total_pickups']
map_data = map_data.merge(lookup, on='LocationID')

# 【关键改进】计算对数列，用于颜色映射
map_data['log_pickups'] = np.log10(map_data['total_pickups'] + 1)

# B. 选中区域的时间趋势数据聚合
zone_hourly_data = df[df['PULocationID'] == selected_id].groupby('hour').size().reset_index(name='count')
full_hours = pd.DataFrame({'hour': range(24)})
zone_hourly_data = full_hours.merge(zone_hourly_data, on='hour', how='left').fillna(0)

# 4. 页面布局
col1, col2 = st.columns([1.2, 0.8])  # 调整比例让地图大一点

with col1:
    st.subheader(f"📍 区域热力分布 (对数缩放)")

    # 颜色轴范围
    max_log = map_data['log_pickups'].max()

    fig_map = px.choropleth_map(
        map_data,
        geojson=geojson,
        locations='LocationID',
        featureidkey="properties.LocationID",
        color='log_pickups',  # 使用对数列着色
        color_continuous_scale="Viridis",  # 使用 Viridis 色系 (翠绿-黄)
        range_color=[0, max_log],  # 锁定颜色范围
        map_style="carto-positron",
        zoom=10,
        center={"lat": 40.7128, "lon": -74.0060},
        opacity=0.7,
        hover_name='Zone',
        hover_data={
            'log_pickups': False,  # 隐藏对数数值，不误导用户
            'total_pickups': ':,d',  # 显示带千分位的原始数值
            'Borough': True,
            'LocationID': True
        },
        labels={'log_pickups': '热度指数'}
    )

    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_showscale=True
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    st.subheader(f"📈 {selected_zone} 24小时趋势")
    fig_line = px.line(
        zone_hourly_data,
        x='hour',
        y='count',
        markers=True,
        labels={'hour': '小时 (0-23)', 'count': '接单量'},
        template="plotly_white"
    )
    fig_line.update_traces(line_color='#FF4B4B', line_width=3)
    fig_line.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=4))
    st.plotly_chart(fig_line, use_container_width=True)

    # 统计指标卡片
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric("该区域全月总单量", f"{int(zone_hourly_data['count'].sum()):,}")
    m2.metric("高峰期单量 (Max)", f"{int(zone_hourly_data['count'].max()):,}")

    st.info("💡 提示：在左侧侧边栏切换区域，或缩放地图查看细节。")