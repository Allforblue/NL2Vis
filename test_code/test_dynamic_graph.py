import pandas as pd
import geopandas as gpd
import plotly.express as px
import os
import json
import numpy as np

# 1. 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
parquet_path = os.path.join(current_dir, '..', 'data', 'yellow_tripdata_2025-01.parquet')
shp_path = os.path.join(current_dir, '..', 'data', 'taxi_zones.shp')
lookup_path = os.path.join(current_dir, '..', 'data', 'taxi_zone_lookup.csv')


def create_animated_map():
    # --- A. 加载地理边界 ---
    print("正在加载地理数据...")
    gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
    geojson = json.loads(gdf.to_json())

    # --- B. 加载并处理行程数据 ---
    print("正在处理行程数据（提取小时并聚合）...")
    # 只读取需要的列，节省内存
    df = pd.read_parquet(parquet_path, columns=['tpep_pickup_datetime', 'PULocationID'])

    # 提取小时
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['hour'] = df['tpep_pickup_datetime'].dt.hour

    # 按 小时 和 区域 聚合
    hourly_data = df.groupby(['hour', 'PULocationID']).size().reset_index(name='pickup_count')

    # 合并区域名称
    lookup = pd.read_csv(lookup_path)
    hourly_data = hourly_data.merge(lookup, left_on='PULocationID', right_on='LocationID')

    # --- C. 数据平滑处理（关键） ---
    # 1. 确保所有小时、所有区域都有记录（即便没有订单也填0），防止动画闪烁
    all_hours = pd.DataFrame({'hour': range(24)})
    all_zones = lookup[['LocationID', 'Zone', 'Borough']]
    grid = all_hours.assign(key=1).merge(all_zones.assign(key=1), on='key').drop('key', axis=1)

    final_df = grid.merge(hourly_data[['hour', 'LocationID', 'pickup_count']],
                          on=['hour', 'LocationID'], how='left').fillna(0)

    # 2. 对数处理：让颜色变化在全天都明显
    final_df['log_count'] = np.log10(final_df['pickup_count'] + 1)

    # --- D. 生成动画地图 ---
    print("正在生成动画渲染图...")

    # 计算全局颜色范围，确保动画过程中颜色刻度是统一的
    max_log = final_df['log_count'].max()

    fig = px.choropleth_map(
        final_df,
        geojson=geojson,
        locations='LocationID',
        featureidkey="properties.LocationID",
        color='log_count',
        animation_frame='hour',  # 动画帧：按小时切换
        color_continuous_scale="Viridis",
        range_color=[0, max_log],  # 锁定颜色轴范围
        map_style="carto-positron",
        zoom=10,
        center={"lat": 40.7128, "lon": -74.0060},
        opacity=0.7,
        hover_name='Zone',
        hover_data={
            'hour': True,
            'LocationID': False,
            'log_count': False,
            'pickup_count': ':,d',
            'Borough': True
        },
        title="NYC Taxi Hourly Pulse (Jan 2025)"
    )

    # --- 关键修正：删除之前手动添加的 updatemenus ---
    # 下面的代码用于调整【自带】动画按钮的速度，而不会产生重复按钮
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 800  # 播放速度(毫秒)
    fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 400  # 平滑过渡时间

    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})

    output_file = "taxi_animated_pulse.html"
    fig.write_html(output_file)
    print(f"完成！动画地图已保存至: {output_file}")
    fig.show()


if __name__ == "__main__":
    create_animated_map()