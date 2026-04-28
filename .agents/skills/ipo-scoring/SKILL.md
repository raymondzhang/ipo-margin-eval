---
name: ipo-scoring
description: Evaluate Hong Kong IPO prospectuses for margin lending (孖展额度) decisions using a standardized 7-dimension scoring framework. Use when the user provides an IPO prospectus PDF (or stock code) and asks for a scoring report, quality assessment, 孖展额度 evaluation, or IPO analysis. Also use when the user mentions IPO Score Guidelines, cornerstone investor analysis, pricing evaluation, stabilization mechanism review, or market macro environment assessment for Hong Kong IPOs.
---

# IPO Scoring Skill

Evaluate Hong Kong IPOs for margin lending decisions using a standardized scoring framework.

## Scoring Framework Overview

7 dimensions, total 110 points (100 base + 10 bonus):

| Dimension | Max | Type |
|-----------|-----|------|
| Profitability (3-year audit) | 30 | Base |
| Allocation Mechanism | 10 | Base |
| Cornerstone Investors | 15 | Base |
| Pricing (Static PE) | 20 | Base |
| Stabilization Mechanism | 10 | Bonus |
| Market Macro: Q1 Break Rate | 15 | Base |
| Market Macro: HSI Monthly Change | 10 | Base |

**Base total: 100. With bonus: 110.**

For classification thresholds:
- **Whitelist**: Base score ≥ 80/100
- **Greylist**: 18A or 18C listings
- **Blacklist**: Any of (1) ≤3 cornerstones or ≤20% coverage; (2) Static PE > industry leader by 20%+; (3) Major negative sentiment during IPO period

## Workflow

### Step 1: Identify the IPO
- Stock code, company name (Chinese + English), listing board
- Prospectus date, issue price, offer size, market cap
- Industry sector

### Step 2: Extract Data from Prospectus PDF
Read the prospectus thoroughly. Extract evidence for each dimension:

**Profitability**: Look for "综合损益及其他全面收益表" or "历史财务资料摘要". Extract net profit for the latest 3 audited fiscal years.

**Allocation**: Look for "全球发售的架构" section. Find public offer vs international offer split (typically 10%/90%).

**Cornerstones**: Look for "基石投资者" section. Extract: number of investors, names, investment amounts, total cornerstone coverage % of international tranche. Identify "star investors" (top-tier PE/VC, sovereign wealth, strategic blue-chips).

**Pricing**: Look for "发售统计资料" for market cap and shares outstanding. Calculate static PE = Issue Price / (Latest Year Net Profit × FX Rate / Total Shares). Use RMB/HKD ≈ 1.075 unless specified otherwise.

**Stabilization**: Look for "超额配股权" / "Over-allotment Option" / "绿鞋". Also check "稳定价格行动". If explicitly stated "并无超额配股权", score 0.

**Patent/Litigation Risks**: Note any ongoing IP disputes or major contingent liabilities.

### Step 3: Score Each Dimension
Apply rubric from `references/scoring-rubric.md`. For each dimension:
1. Quote exact text from prospectus as evidence
2. State the scoring rule applied
3. Show calculation where applicable
4. State final score with clear reasoning

**Scoring discipline**: When in doubt between two score bands, choose the **conservative** (lower) band.

### Step 4: Fetch External Market Data

Two external inputs are required. Attempt automatic fetch first; if data is ambiguous, prompt user for confirmation.

#### A. Hang Seng Index (HSI) Monthly Change
- **Metric**: HSI month-over-month return for the month immediately preceding the prospectus start date.
- **Method**: Use `SearchWeb` to find reliable financial news source (e.g., 东方财富, 财联社, Sina Finance) reporting the monthly close. Search query pattern: "恒生指数 [YYYY]年[M]月 累计涨跌幅" or "HSI monthly return [YYYY]-[MM]".
- **Fallback**: If search yields conflicting numbers or no clear monthly summary, ask user: "请提供恒生指数[YYYY]年[M]月的月度涨跌幅（%）。"
- **Reliability**: High. Major Chinese financial media consistently reports monthly HSI summaries.

#### B. Prior Quarter IPO First-Day Break Rate
- **Metric**: First-day break rate of HKEX IPOs in the quarter immediately preceding the prospectus quarter.
- **Definition**: (# of IPOs closing below issue price on listing day) / (total # of IPOs in that quarter). Exclude introduction listings (介绍上市) and GEM listings if possible.
- **Data Quality Warning**: This metric has **medium reliability** because:
  - Different sources use different denominators (with/without introduction listings, with/without GEM)
  - Some sources report "cumulative break rate since listing" instead of "first-day break rate"
  - Quarterly summaries typically appear 1-7 days after quarter-end
- **Strategy** (in priority order):
  1. **Ask user first**: "请提供[YYYY]年Q[X]港股新股首日破发率（%），或告知我应采用的数值（如'低于10%'）。"
  2. **If user provides a value**: Use it directly without question. Accept qualitative answers (e.g., "低于10%") and map to the appropriate score band.
  3. **If user does not provide data**: Use `SearchWeb` with queries like "[YYYY]年Q[X] 港股新股 首日破发率" or "HK IPO first day break rate [quarter]". Look for Wind, LiveReport, or major brokerage research.
  4. **If search yields conflicting sources** (>5 percentage points difference), present the range to the user and ask for confirmation before scoring.

### Step 5: Compute Totals and Classification
- Sum base scores and bonus separately
- Calculate base score rate (base_score / 100)
- Apply Whitelist/Greylist/Blacklist rules
- Note any "watch" items (e.g., conditionally near blacklist threshold)

### Step 6: Generate Investment Recommendation
Based on the score and classification, provide:
- **Open margin lending?** Yes/No/Conditional
- **Recommended leverage**: Conservative (3-5x) / Moderate (5-10x) / Aggressive (10x+)
- **Rationale**: 2-3 sentence summary linking score to decision
- **Key watch items**: Specific events/metrics to monitor during book-building and first trading day

### Step 7: Output as Word Document
Generate a professionally formatted `.docx` report using `python-docx`.

**Report structure** (see `references/report-spec.md` for detailed formatting):
1. Title page: "IPO 标的质量评分报告"
2. Basic Info (stock code, price, offer size, market cap, industry)
3. Seven scoring sections (each with: evidence quote, scoring rule, calculation, final score)
4. Summary table (all dimensions, totals)
5. IPO Classification (Whitelist/Greylist/Blacklist evaluation)
6. Investment Recommendation (decision table, risk factors, leverage guidance)
7. Disclaimer

**Color coding for scores**:
- Full or near-full marks: Green (RGB 0x008000)
- Partial marks: Orange (RGB 0xFF6600)
- Zero or critical deduction: Red (RGB 0xCC0000)

Save the file with naming convention: `IPO_Score_Report_[STOCK_CODE].docx` in the user's working directory.

## Important Rules

1. **Always cite prospectus page/section** for every factual claim.
2. **Show your work**: PE calculations, percentage computations, and comparisons must be explicit.
3. **Conservative bias**: When data is incomplete or ambiguous, prefer lower score bands.
4. **Do not hallucinate industry benchmarks**: If prospectus does not provide industry average PE, state the assumption source (e.g., "general HK medical device sector median ~25-35x") and note the uncertainty.
5. **External data transparency**: Always state the source and date for HSI and break rate data. If multiple sources exist, mention the range.
6. **Language**: Generate the report in **Simplified Chinese (简体中文)** first. Append a **Traditional Chinese (繁體中文)** version after the Simplified version, sharing the same structure and content. Separate the two versions with a page break. Use 繁體中文用詞習慣 (e.g., 標的→標的, 資訊→資訊, 發售→發售, 漲跌幅→漲跌幅, 佔→佔, 後→後).
7. **No git operations**: Do not commit or push any files.
