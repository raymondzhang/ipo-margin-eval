# IPO Scoring Rubric

Complete scoring standards for all 7 dimensions.

## 一、过往3个审计年度盈利情况（满分30分）

| 得分 | 标准 |
|------|------|
| 30 | 连续三年一期(如涉及)盈利 |
| 20 | 连续两年一期(如涉及)盈利，且最近一年非亏损 |
| 10 | 最近一年一期(如涉及)盈利 |
| 5 | 其余情况 |

**Extraction targets**:
- Net profit (年内溢利 / 净利润) for latest 3 audited fiscal years
- Growth rates between years
- Check if any year is negative

**Tip**: Look in "概要—历史财务资料摘要" and "附录一—综合损益及其他全面收益表".

---

## 二、分配机制（满分10分）

| 得分 | 标准 |
|------|------|
| 10 | 机制A |
| 10 | 机制B，公开部分比例 ≤ 10%（含） |
| 5 | 机制B，公开部分比例 > 10% |

**Extraction targets**:
- Public offer shares / Total offer shares
- Re-allocation mechanism reference (《新上市申请人指南》第4.14章 / 《上市规则》第18项应用指引)

**Tip**: Look in "全球发售的架构—全球发售" and "全球发售的架构—重新分配".

---

## 三、基石投资人（满分15分）

| 得分 | 标准 |
|------|------|
| 15 | ≥10家，且有 ≥2家明星投资人，基石占国际配售 ≥50% |
| 10 | 5-10家，且有1-2家明星投资人，基石占国际配售 ≥35% |
| 5 | 3-5家，且至少1家明星投资人，基石占国际配售 ≥25% |

**Definitions**:
- **Star investor**: Top-tier global PE/VC (e.g., OrbiMed, Sequoia, Hillhouse, GIC, Temasek), sovereign wealth fund, Fortune 500 strategic investor, or major state-owned enterprise backed by central/provincial government.
- **Coverage %**: Total cornerstone shares / International offer shares

**Extraction targets**:
- Number of cornerstone investors
- Name of each investor and ultimate beneficial owner
- Investment amount (USD or HKD)
- Total cornerstone shares and % of international tranche

**Tip**: Look in "基石投资者" section and "基石投资者资料" subsection.

---

## 四、定价情况（满分20分）

| 得分 | 标准 |
|------|------|
| 20 | 静态PE低于行业平均 |
| 15 | 静态PE高于行业平均不超过25% |
| 10 | 静态PE高于行业平均不超过50%，或无静态PE值（亏损） |

**Calculation**:
```
Static PE = Issue Price / EPS
EPS (HKD) = Latest Year Net Profit (RMB) × FX Rate / Total Shares Outstanding
```

Default FX rate: RMB/HKD ≈ 1.075 unless prospectus specifies otherwise.

**Extraction targets**:
- Issue price per share
- Total shares outstanding post-IPO
- Latest audited net profit
- Market cap at issue price

**Industry benchmark**:
- If prospectus provides direct peer comparison: use that.
- If not: use general market knowledge of HK sector median. Always state the assumed benchmark and note uncertainty.

**Tip**: Look in "概要—发售统计资料" for market cap and shares. Use "附录一—综合损益表" for net profit.

---

## 五、稳价机制（奖励分，满分10分）

| 得分 | 标准 |
|------|------|
| 10 | 有稳价机制（超额配售权 / 绿鞋 / 稳定价格行动） |
| 0 | 无稳价机制（奖励分，无则不加分） |

**Extraction targets**:
- Explicit statement about over-allotment option (超额配股权)
- Stabilization agent appointment
- Greenshoe terms

**Tip**: Search for keywords: "超额配股权", "Over-allotment", "绿鞋", "稳定价格", "stabilization". If prospectus says "并无超额配股权", score is definitively 0.

---

## 六、市场宏观环境—过往一季度新股上市首日破发率（满分15分）

| 得分 | 标准 |
|------|------|
| 15 | ≤10%（含） |
| 10 | 10%-20%（含） |
| 5 | 20%-30%（含） |

**Definition**: In the quarter immediately preceding the current prospectus quarter, count HKEX IPOs that closed below issue price on their listing day, divided by total IPOs in that quarter.

**Data quality notes**:
- Exclude introduction listings (介绍上市) if possible
- Use first-day break rate, NOT cumulative break rate since listing
- If data spans partial quarter, note the date cutoff

---

## 七、市场宏观环境—恒生指数近1个月涨跌幅（满分10分）

| 得分 | 标准 |
|------|------|
| 10 | ≥ -5%（含） |
| 5 | ≥ -10%（含）且 < -5% |

**Definition**: HSI month-over-month percentage change for the full calendar month immediately before the prospectus start date.

**Example**: If prospectus starts 2026-04-24, use March 2026 HSI return.
