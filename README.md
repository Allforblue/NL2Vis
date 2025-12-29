### 功能需求
- 上传文件
- 输入文字需求
- 模型返回图表

### 项目架构
- 前后端：fastapi
- 数据主要处理流程
  - 数据总结
  - 信息处理
  - 代码生成及沙箱测试
  - 风格化处理

### 所需要的功能部件
1. 地图绘制工具
2. 数据过滤器
3. 数据总结器
4. 目标分析器
5. 代码执行器
6. 图表修改器
7. 风格处理器
8. 框架管理器


### 实现思路
1. 本地模型部署 √ 
    - deepseek-r1:8b    部署完成
    - llama3.1:latest   部署完成
    - gmini-2.5-flash   API可调用
    - 
2. 开发mapbox或相关绘图工具接口
    -接口测试已完成，可以正确绘制图表（静态热力图绘制测试完成、动态热力图绘制测试完成、dashboard测试部分完成）
3. 训练模型能够调用已有接口（需要部署沙箱避免代码错误导致系统崩溃）
4. 训练模型处理用户需求
   - 数据分析需求，如：请给我上车地点发分布图，不同时间段乘车人数对比等（注意这里是时空数据，具体的一点的需求还没有确定）
   - 图表需求，如：更横纵轴颜色、以--为横轴、
5. 模型实现风格化处理（可选）


### Data（NYC Taxi）
这些数据来自于纽约市出租车和利木津委员会（NYC TLC）发布的公开数据集。这份数据详细记录了 2025 年 1 月份纽约“黄色出租车”（Yellow Taxi）的每笔行程信息。

以下是这 20 列数据的详细含义解析：

#### 1. 基础信息（供应商与时间）
*   **VendorID**: 提供该条记录的供应商代码。
    *   `1` = Creative Mobile Technologies, LLC
    *   `2` = VeriFone Inc.
*   **tpep_pickup_datetime**: 乘客上车的日期和时间。
*   **tpep_dropoff_datetime**: 乘客下车的日期和时间。

#### 2. 行程属性
*   **passenger_count**: 车上的乘客人数。这是由司机手动输入的，因此可能存在少量的 0 或异常值。
*   **trip_distance**: 行程距离，单位为**英里**（Miles）。
*   **RatecodeID**: 本次行程采用的费率标准。
    *   `1` = 标准费率 (Standard rate)
    *   `2` = JFK 机场 (JFK)
    *   `3` = 纽瓦克 (Newark)
    *   `4` = 拿骚/威彻斯特 (Nassau/Westchester)
    *   `5` = 协商费率 (Negotiated fare)
    *   `6` = 团体行程 (Group ride)
*   **store_and_fwd_flag**: 该记录是否在车辆发送到服务器前先存储在内存中（因为没信号等原因）。
    *   `Y` = 存储后转发
    *   `N` = 实时发送

#### 3. 位置信息
*   **PULocationID**: 上车地点的 TLC 出租车区域 ID（TLC Taxi Zone）。
*   **DOLocationID**: 下车地点的 TLC 出租车区域 ID（TLC Taxi Zone）。
    *   *注：这些 ID 对应的具体地名（如上西区、时代广场等）需要查阅专门的 Taxi Zone Lookup 表。*

#### 4. 费用构成（单位均为美元 USD）
*   **payment_type**: 支付方式的代码。
    *   `1` = 信用卡 (Credit card)
    *   `2` = 现金 (Cash)
    *   `3` = 免费 (No charge)
    *   `4` = 争议 (Dispute)
    *   `5` = 未知 (Unknown)
    *   `6` = 作废行程 (Voided trip)
*   **fare_amount**: 计程表金额。根据时间和距离计算的基础费用。
*   **extra**: 杂项附加费。目前包括：
    *   $0.50 或 $1.00 的高峰期附加费（Rush hour）和深夜附加费（Overnight）。
*   **mta_tax**: 纽约大都会运输署（MTA）税费，通常为 $0.50。
*   **tip_amount**: **小费**。
    *   *特别注意：该列仅包含信用卡支付的小费，现金支付的小费通常记录为 0。*
*   **tolls_amount**: 过路费、桥梁费。
*   **improvement_surcharge**: 改善附加费。通常为 $0.30 或 $1.00（用于资助无障碍出租车等）。
*   **congestion_surcharge**: 拥堵附加费（主要针对进入曼哈顿南部的行程）。
*   **Airport_fee**: 机场费。通常是在拉瓜迪亚 (LGA) 或肯尼迪 (JFK) 机场上车时收取的 $1.25 或 $1.75 费用。
*   **cbd_congestion_fee**: 中央商务区（CBD）拥堵费。这是纽约近期实施的曼哈顿 60 街以下区域的专项收费。
*   **total_amount**: **总金额**。是上述所有费用项的加和（基础费+附加费+税+小费+路桥费等）。


### 给 NL2Vis项目的建议(来自gmini)：
如果你在做 NL2Vis 项目，这些列可以分成以下几类进行分析：
1.  **时间分析**：利用 `tpep_pickup_datetime` 分析订单量随小时、周、天的变化。
2.  **地理分析**：利用 `PULocationID` 和 `DOLocationID` 分析热门区域或通勤路线。
3.  **收入分析**：分析 `total_amount`、`fare_amount` 或 `tip_amount`（小费比例通常是用户非常感兴趣的指标）。
4.  **关联分析**：例如 `trip_distance` 与 `fare_amount` 的线性关系，或者不同 `payment_type` 下 `tip_amount` 的差异。