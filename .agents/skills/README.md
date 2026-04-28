# IPO Margin Eval — Skill Registry

This directory contains all Kimi skills for the IPO margin evaluation workflow.

## Skills

### 1. `ipo-scoring` (Original)
**Purpose**: Evaluate HK IPO prospectuses using a 7-dimension scoring framework.
**Output**: `IPO_Score_Report_[CODE].docx` (bilingual Simplified + Traditional Chinese)
**Trigger**: "评估这份招股书", "对这个IPO做孖展评分", "按IPO Score Guidelines给这个新股打分"

### 2. `ipo-backtest` (NEW)
**Purpose**: Backtest and validate the effectiveness of ipo-scoring against historical IPO performance.
**Output**: `backtest_report_YYYYMM.xlsx` (3 sheets: raw data, statistics, group analysis)
**Trigger**: "回溯验证评分模型", "看看历史IPO评分是否有效", "生成回溯统计报告"

### 3. `ipo-funding-application` (NEW)
**Purpose**: Generate internal funding application emails for management approval.
**Output**: `IPO_Funding_App_[CODE].md` (+ optional `.docx`)
**Trigger**: "写孖展申请邮件", "生成融资额度审批邮件", "IPO funding application"

## Quick Reference

| Skill | Input | Output | Key File |
|-------|-------|--------|----------|
| ipo-scoring | Prospectus PDF | Word report | `SKILL.md` |
| ipo-backtest | Time period + scores JSON | Excel report | `scripts/generate_backtest_report.py` |
| ipo-funding-application | JSON with stock/funding params | Markdown/Word email | `scripts/generate_email.py` |

## Workflow Diagram

```
[Prospectus PDF]
      |
      v
[ipo-scoring] ---> IPO_Score_Report.docx
      |
      v
[ipo-backtest] ---> backtest_report.xlsx (validate model)
      |
      v
[ipo-funding-application] ---> IPO_Funding_App.md (request approval)
```
