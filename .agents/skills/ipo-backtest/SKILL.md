---
name: ipo-backtest
description: Backtest, validate, and continuously monitor the effectiveness of the ipo-scoring model by comparing historical IPO scores against actual post-listing performance. Use when the user asks to backtest, validate, monitor, or verify the IPO scoring model against historical or ongoing data, or wants to generate a tracking / performance report for past or current HK IPOs.
---

# IPO Backtest & Monitoring Skill

Validate and continuously track the `ipo-scoring` model by comparing scores with actual IPO performance.

---

## 工作流总览：IPO全生命周期管理

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  发现新股   │ ──→ │  7维评分    │ ──→ │  上市监控   │ ──→ │  回测验证   │
│ (每周一)    │     │ (招股阶段)   │     │ (上市后)    │     │ (月度/季度) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                    │                   │                   │
      ▼                    ▼                   ▼                   ▼
  下载招股书           评分报告+          自动更新现价        更新回测报告
  搜索关键数据         资金申请邮件       登记首日表现        校准评分模型
```

---

## 阶段一：上市前 — 发现新股与评分

### 1.1 发现新股
每周一检查本周即将招股/上市的港股新股：

```bash
# 用 Kimi 搜索本周新股
"本周港股新股IPO 招股 上市"
"本周港股IPO 孖展"
```

关注来源：
- 金吾资讯 (ipo.jinwucj.com)
- AASTOCKS 新股频道
- 富途牛牛新股中心
- 新浪港股

### 1.2 7维度评分
对每只感兴趣的新股，按 `ipo-scoring` 框架评分：

| 维度 | 满分 | 数据来源 |
|------|------|----------|
| 盈利能力 | 30 | 招股书「财务资料」章节 / 新浪财经新股页面 |
| 配售结构 | 10 | 招股书「全球发售架构」/ 金吾资讯配发结果 |
| 基石投资者 | 15 | 招股书「基石投资者」章节 / 新浪财经 |
| 估值定价 | 20 | 招股书「概要」中的募资额 + 净利润计算PE |
| 稳定措施 | 10 | 招股书「全球发售架构」绿鞋条款 |
| 破发率 | 15 | `IPO_Backtest_Tracking.xlsx` → 宏观数据 |
| 恒指走势 | 10 | 恒生指数月度涨跌幅 |
| **基础分（前6维）** | **100** | — |
| **总分（7维合计）** | **110** | — |

> **重要规则**：
> - **基础分** = 盈利能力 + 配售结构 + 基石投资者 + 估值定价 + 破发率 + 恒指走势 = **100分制**
> - **奖励分** = 稳价机制 = **10分**
> - **总分** = 基础分 + 奖励分 = **110分制**
> - **Whitelist 门槛：基础分 ≥ 80**
> - 严禁在7维度框架外额外加分（如"赛道热门"、"概念溢价"等）。稳价机制的10分是框架内固定的奖励分，不是可随意追加的 bonus。

### 1.3 生成评分报告 + 资金申请
对评分 ≥60 或特别关注的标的，生成：
1. `IPO_Score_Report_XXXX.docx` — 放入 `Scorings/` 文件夹
2. 如需要资金申请，运行 `ipo-funding-application` skill

---

## 阶段二：上市日 — 登记首日表现

### 2.1 上市当晚操作
新股上市当日收盘后，搜索首日表现并登记到追踪表：

```bash
# 搜索格式
"{股票代码} 首日 收盘 涨幅"
"{股票代码} 暗盘 表现"
```

需要记录的数据：
- 上市日期
- 首日开盘价
- 首日收盘价
- 首日涨幅（%）
- 是否破发（收盘价 < 招股价）
- 公开发售认购倍数
- 一手中签率

### 2.2 更新追踪表
打开 `IPO_Backtest_Tracking.xlsx` → `追踪主表`，在末尾新增一行，或使用脚本注册：

```bash
cd /Users/rayzyp/Documents/运营流程/IPO孖展评估/.agents/skills/ipo-backtest/scripts
python update_tracking.py --register \
  --code 06656 \
  --name "思格新能" \
  --listing-date 2026-04-16 \
  --issue-price 324.2 \
  --scores '{"profitability":10,"allocation":10,"cornerstone":15,"pricing":15,"stabilization":10,"break_rate":15,"hsi":5}' \
  --classification "非白名单"
```

---

## 阶段三：上市后 — 持续监控（自动化）

### 3.1 监控频率
| 频率 | 操作 |
|------|------|
| **每周五收盘后** | 运行 `fetch_prices.py` 自动更新所有已上市股票的**现价**和**累积涨幅%** |
| **每月最后一个周五** | 生成月度监控摘要 |
| **每季度末** | 更新回测报告，纳入本季度新上市样本 |

### 3.2 自动更新现价和累积表现

**推荐方式：批量自动获取（`fetch_prices.py`）**

```bash
cd /Users/rayzyp/Documents/运营流程/IPO孖展评估/.agents/skills/ipo-backtest/scripts

# 更新追踪表中所有已上市股票的最新价格
python fetch_prices.py \
  --input /Users/rayzyp/Documents/运营流程/IPO孖展评估/IPO_Backtest_Tracking.xlsx
```

该脚本通过腾讯财经 API (`qt.gtimg.cn`) 批量查询港股实时行情，每批最多50只。支持代理环境。

**备用方式：手动搜索**
```bash
# 在浏览器搜索
"{代码}.HK 股价"
"{代码} 港股 最新"
```

**累积涨幅计算公式**：
```
最新累积涨幅% = (最新收盘价 - 招股价) / 招股价 × 100%
```

### 3.3 标记需要关注的股票

在追踪表中，对以下情况标记状态：
- **破发**：现价 < 招股价（累积涨幅 < 0）→ 状态改为 `已破发`
- **接近破发**：现价 < 上市价（从首日高点回落）→ 状态改为 `监控中-回落`
- **持续走强**：现价 > 上市价且趋势向上 → 状态保持 `监控中-走强`

### 3.4 已评分未上市股票的跟踪

对于已评分但尚未上市的股票：
1. 上市当晚记录首日表现
2. 与评分时的预测对比
3. 如有重大偏差，记录原因到 `monitoring_log.md`

使用脚本更新状态：
```bash
python update_tracking.py --update-status \
  --code 06810 \
  --status "监控中"
```

---

## 阶段四：回测验证 — 评分模型校准

### 4.1 何时做回测
- **每月末**：将本月新上市股票加入回测数据库
- **每季度末**：生成完整的季度回测报告
- **触发条件**：当样本量达到10只以上时

### 4.2 回测操作步骤

```bash
cd /Users/rayzyp/Documents/运营流程/IPO孖展评估/.agents/skills/ipo-backtest/scripts

# Step 1: 准备IPO数据（从追踪表提取或手动输入）
python fetch_ipo_data.py --output ipo_data.json

# Step 2: 准备评分数据（格式见下方「Scores JSON 格式」）

# Step 3: 生成回测报告
python generate_backtest_report.py \
  --input ipo_data.json \
  --scores scores.json \
  --output backtest_report_202604.xlsx
```

### 4.3 回测关键指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 白名单首日破发率 | <20% | 白名单股票不应该轻易破发 |
| 黑名单首日破发率 | >60% | 黑名单股票应该大概率破发 |
| 高分组平均涨幅 | >中分组 >低分组 | 分数越高，平均表现越好 |
| 评分-收益相关系数 | r > 0.3 | 正相关越显著，模型越有效 |

### 4.4 模型校准

当发现以下情况时，考虑调整评分权重：
- 白名单破发率持续 >30% → 收紧评分标准或提高白名单门槛
- 低分组反而涨幅最高 → 检查某一维度是否被系统性低估
- 定价维度失效 → 调整PE判断基准

---

## 核心数据文件

### 追踪主表：`IPO_Backtest_Tracking.xlsx`

独立工作簿，不修改用户的原始 `IPO Score_OKK.xlsx`。

| Sheet | 用途 |
|-------|------|
| `追踪主表` | **核心数据表** — 所有已上市/待上市IPO的字段：代码、名称、招股价、最新价、最新累积涨幅%、状态、分类、各维度得分 |
| `评分详情` | 每只新股的7维度逐项得分 + 评分理由 |
| `监控日志` | 更新操作日志（日期、动作、涉及股票、备注） |

`追踪主表` 关键字段：
- `招股价` — 最终定价（HKD）
- `最新价` — 通过 `fetch_prices.py` 自动更新
- `最新累积涨幅%` — (最新价-招股价)/招股价 × 100%
- `状态` — 待上市 / 监控中 / 已破发 / 已退市 / 监控结束
- `基础分` — 前6维度合计（满分100）
- `总分` — 7维度合计（满分110）
- `分类` — 白名单（基础分≥80）/ 灰名单（60-79）/ 黑名单（<60）

### 评分报告：`Scorings/IPO_Score_Report_XXXX.docx`

每只新股的完整评分报告，命名规则：`IPO_Score_Report_{代码}.docx`

### 回测报告：`backtest_report_YYYYMM.xlsx`

包含3个工作表：
1. **原始数据** — 样本IPO的评分+表现
2. **统计汇总** — 破发率、平均涨幅、白/黑名单命中率
3. **分组分析** — 按分数分组对比

### 评分详情：`.agents/skills/ipo-backtest/data/`

保存每只新股的详细评分依据，命名：`{YYYYMM}_scores.json`

---

## Scores JSON 格式

```json
{
  "06656": {
    "base_score": 70,
    "classification": "灰名单",
    "profitability_score": 10,
    "allocation_score": 10,
    "cornerstone_score": 15,
    "pricing_score": 15,
    "stabilization_score": 10,
    "macro_break_rate_score": 15,
    "macro_hsi_score": 5
  }
}
```

> 注意：`base_score` 为前 6 维度得分之和（满分 100），`total_score` = `base_score` + `stabilization_score`（满分 110）。

---

## 自动化脚本清单

| 脚本 | 功能 | 常用命令 |
|------|------|----------|
| `fetch_prices.py` | 批量获取港股最新价并更新Excel | `python fetch_prices.py --input IPO_Backtest_Tracking.xlsx` |
| `update_tracking.py` | 注册新股、更新状态、列出追踪表 | `python update_tracking.py --register ...` / `--list` / `--update-status ...` |
| `generate_backtest_report.py` | 生成回测Excel报告 | `python generate_backtest_report.py --input ipo_data.json --scores scores.json --output report.xlsx` |
| `fetch_ipo_data.py` | 从追踪表提取IPO数据为JSON | `python fetch_ipo_data.py --output ipo_data.json` |

---

## 快速操作清单

### ✅ 每周一：发现新股
- [ ] 搜索本周港股IPO
- [ ] 筛选感兴趣的标的
- [ ] 下载招股书到 `IPO_Docs/`

### ✅ 招股期间：评分
- [ ] 7维度评分（基础分100 + 稳价10 = 总分110，严禁框架外加分）
- [ ] 生成评分报告到 `Scorings/`
- [ ] 如需资金申请，生成邮件
- [ ] 注册到 `IPO_Backtest_Tracking.xlsx`（状态：`待上市`）

### ✅ 上市当晚：登记首日
- [ ] 搜索首日表现
- [ ] 更新 `IPO_Backtest_Tracking.xlsx` → 首日收盘价、首日涨幅%
- [ ] 状态从 `待上市` 改为 `监控中`
- [ ] 记录首日数据到JSON（如需回测）

### ✅ 每周五：监控更新
- [ ] 运行 `fetch_prices.py` 自动更新最新价
- [ ] 检查 `最新累积涨幅%` 列，标记破发/走强
- [ ] 更新 `monitoring_log.md` 如有重大偏差

### ✅ 每月末：月度摘要
- [ ] 统计本月新上市数量
- [ ] 统计本月破发率
- [ ] 更新宏观数据（恒指月度涨跌幅）

### ✅ 每季度末：回测更新
- [ ] 收集本季度所有新上市IPO的评分+表现
- [ ] 运行 `generate_backtest_report.py`
- [ ] 检查白/黑名单命中率
- [ ] 如有必要，调整评分权重

---

## Important Rules

1. **Exclude non-qualifying listings**: GEM transfers, introductions, ETFs, share consolidations are NOT true IPOs for backtesting.
2. **Data source transparency**: Always cite the source website for performance data.
3. **Conservative scoring**: Same as ipo-scoring — when in doubt, choose lower score band.
4. **No arbitrary bonus**: Only use the 7-dimension framework. Do not add extra points for "hot sectors", "concept stocks", or any reason outside the rubric.
5. **Regular updates**: The tracking sheet is only useful if updated regularly. Set a calendar reminder for Friday evenings.
6. **Do not modify user's original workbook**: `IPO Score_OKK.xlsx` is the user's master file. Use `IPO_Backtest_Tracking.xlsx` for all skill-managed tracking.
