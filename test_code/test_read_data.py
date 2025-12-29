import pandas as pd
import os

# 获取当前脚本的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 拼接处数据文件的绝对路径
# .. 表示返回上一级目录 (NL2Vis)，然后进入 data 目录
file_path = os.path.join(current_dir, '..', 'data', 'yellow_tripdata_2025-01.parquet')


def test_read():
    try:
        # 读取 Parquet 文件
        df = pd.read_parquet(file_path)

        # 打印前 10 行
        print("成功读取数据，前 10 行如下：")
        print(df.head(10))

        # 打印基础信息（可选，方便调试）
        print("\n数据形状:", df.shape)
        print("列名:", df.columns.tolist())

    except FileNotFoundError:
        print(f"错误：找不到文件，请检查路径是否正确: {file_path}")
    except Exception as e:
        print(f"读取过程中出现错误: {e}")


if __name__ == "__main__":
    test_read()