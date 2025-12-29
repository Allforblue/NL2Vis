import pandas as pd
import geopandas as gpd
import plotly.express as px
import os
import json
import numpy as np  # 导入 numpy 处理对数

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
parquet_path = os.path.join(current_dir, '..', 'data', 'yellow_tripdata_2025-01.parquet')
shp_path = os.path.join(current_dir, '..', 'data', 'taxi_zones.shp')
lookup_path = os.path.join(current_dir, '..', 'data', 'taxi_zone_lookup.csv')


def create_optimized_map():
    # 1. 加载地理数据
    print("加载地图形状...")
    gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
    geojson = json.loads(gdf.to_json())

    # 2. 加载行程数据
    print("处理业务数据...")
    df = pd.read_parquet(parquet_path)
    lookup = pd.read_csv(lookup_path)

    # 统计上车人数
    pickup_counts = df['PULocationID'].value_counts().reset_index()
    pickup_counts.columns = ['LocationID', 'pickup_count']

    # 合并区域名称 (让悬停信息更有意义)
    pickup_counts = pickup_counts.merge(lookup, on='LocationID', how='left')

    # --- 核心改进：对数处理 ---
    # 使用 log10 缩放。+1 是为了防止 log(0) 出错
    pickup_counts['log_pickup_count'] = np.log10(pickup_counts['pickup_count'] + 1)

    print("生成优化后的地图...")

    # 3. 绘图
    fig = px.choropleth_map(
        pickup_counts,
        geojson=geojson,
        locations='LocationID',
        featureidkey="properties.LocationID",
        color='log_pickup_count',  # 使用对数列决定颜色
        color_continuous_scale="Viridis",  # Viridis 或 Plasma 在对数下视觉效果更好
        map_style="carto-positron",
        zoom=10,
        center={"lat": 40.7128, "lon": -74.0060},
        opacity=0.7,
        # 关键：悬停显示原始数据，而不是对数
        hover_name='Zone',
        hover_data={
            'LocationID': True,
            'log_pickup_count': False,  # 隐藏对数数值
            'pickup_count': ':,d',  # 显示格式化后的原始计数值
            'Borough': True
        },
        labels={'log_pickup_count': 'Order Intensity (Log)'},
        title="NYC Taxi Pickup Hotspots (Jan 2025) - Logarithmic Scale"
    )

    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})

    fig.write_html("optimized_taxi_map.html")
    print("完成！请查看 optimized_taxi_map.html")
    fig.show()


if __name__ == "__main__":
    create_optimized_map()