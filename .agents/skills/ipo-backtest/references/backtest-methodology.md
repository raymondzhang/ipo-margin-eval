# IPO Backtest Methodology

## 1. 目的

验证 `ipo-scoring` 评分模型对港股新股上市后实际表现的预测有效性。

## 2. 回溯范围

- **时间窗口**：可自定义，如"2026年4月1日-4月24日"
- **标的范围**：港交所主板新上市IPO（排除GEM转板、介绍上市、ETF、股本重组等）

## 3. 数据字段

### 3.1 评分数据（由 ipo-scoring 提供或人工回溯）

| 字段 | 说明 |
|------|------|
| stock_code | 港股代码 |
| company_name | 公司名称 |
| base_score | 基础分（满分100），前6维度之和（不含稳价机制） |
| total_score | 总分（满分110），7维度之和 = base_score + stabilization_score |
| classification | 白名单（基础分≥80）/ 灰名单（60-79）/ 黑名单（<60） |
| profitability_score | 盈利维度得分（0-30） |
| allocation_score | 分配机制得分（0-10） |
| cornerstone_score | 基石投资人得分（0-15） |
| pricing_score | 定价得分（0-20） |
| stabilization_score | 稳价机制得分（0-10） |
| macro_break_rate_score | 破发率得分（0-15） |
| macro_hsi_score | 恒生指数得分（0-10） |

> **基础分 = 100分制**（前6维度），**奖励分 = 稳价机制 = 10分**，**总分 = 110分制**。白名单门槛为基础分 ≥ 80。

### 3.2 实际表现数据（通过公开渠道获取）

| 字段 | 说明 |
|------|------|
| listing_date | 上市日期 |
| issue_price | 发行价（港元） |
| first_day_open | 首日开盘价 |
| first_day_close | 首日收盘价 |
| first_day_high | 首日最高价 |
| first_day_low | 首日最低价 |
| first_day_return | 首日涨跌幅（%）= (首日收盘-发行价)/发行价 |
| first_day_broke | 首日是否破发（收盘<发行价则为true） |
| week_return | 上市首周涨跌幅（%） |
| cum_return | 截至统计日的累积涨跌幅（%） |
| public_subscription | 公开发售认购倍数 |
| international_subscription | 国际配售认购倍数 |

## 4. 统计指标

### 4.1 基础统计

- **样本数**：N
- **首日破发率**：首日破发数 / N
- **首日平均涨幅**：mean(first_day_return)
- **首日涨幅中位数**：median(first_day_return)
- **正收益比例**：first_day_return > 0 的占比

### 4.2 评分有效性验证

| 指标 | 计算方法 | 解读 |
|------|---------|------|
| 白名单命中率 | 白名单中首日未破发占比 | 越高越好，目标>80% |
| 黑名单命中率 | 黑名单中首日破发占比 | 越高越好，目标>60% |
| 评分-收益相关系数 | Pearson(total_score, first_day_return) | 正值且显著则有效 |
| 高分组收益 | 总分前50%的平均首日涨幅 | 应显著高于低分组 |
| 低分组收益 | 总分后50%的平均首日涨幅 | — |

### 4.3 分组对比表

按**总分**划分为三组：
- **高分组**：总分 >= 80（白名单）
- **中分组**：60 <= 总分 < 80（灰名单）
- **低分组**：总分 < 60（黑名单）

对比三组的：
- 首日平均涨幅
- 首日破发率
- 一周平均涨幅

## 5. 报告格式

输出为 Excel 文件，包含三个sheet：

1. **Raw Data**：每只新股的完整数据（评分+实际表现）
2. **Statistics**：汇总统计指标
3. **Group Analysis**：分组对比分析

## 6. 持续监控机制

对已评估但未上市的新股，在上市后：
1. 自动获取其实际表现数据（通过 `fetch_prices.py` 批量更新最新价）
2. 对比事前评分与实际表现
3. 记录偏差原因，用于模型迭代

### 6.1 自动化更新流程

```
每周五收盘后
    │
    ▼
运行 fetch_prices.py
    │
    ▼
自动更新 IPO_Backtest_Tracking.xlsx
    │
    ▼
人工检查：标记破发/走强股票
    │
    ▼
如有重大偏差 → 记录到 monitoring_log.md
```

### 6.2 监控停止条件

股票从追踪表中移除或状态改为 `监控结束` 的条件：
- 上市后满 30 个交易日且累积涨幅已稳定
- 已破发且连续 10 个交易日无反弹迹象
- 用户手动决定停止跟踪
