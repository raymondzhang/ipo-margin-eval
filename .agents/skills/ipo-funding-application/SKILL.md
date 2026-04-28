---
name: ipo-funding-application
description: Generate internal funding application emails for HK IPO margin lending (孖展融資) based on ipo-scoring results. Use when the user has completed an IPO scoring evaluation and wants to draft an internal email to management requesting approval for margin lending allocation. Also use when the user mentions "孖展申請", "融資額度審批", "IPO funding application", or references the email template for Celine/management approval.
---

# IPO Funding Application Skill

Generate standardized internal emails requesting approval for IPO margin lending (孖展融資) allocation.

## Workflow

### Step 1: Gather Required Information

Extract from the user's scoring results or ask directly:

**Stock Information:**
- Stock code (e.g., 01879.HK)
- Company name (Chinese + English)
- Industry / business description
- Prospectus date
- HKEX announcement URL

**Funding Parameters:**
- Maximum funding available (致Celine的总额)
- Approved funding amount (预批额度)
- Funding rate (融资利率, e.g., 0%)
- Minimum units (最低申请数量, e.g., 15股)
- Leverage ratio (杠杆倍数, e.g., 10倍)
- Client ratio (客户出资%, e.g., 10%)
- Firm ratio (公司融资%, e.g., 90%)
- Fee per application (手续费, e.g., HKD 100)
- Cost of funds (资金成本率, e.g., 2.27%)

**Broker Comparison:**
- At least 2 competing brokers with their rates and fees
- Default: Futu (0%, HKD 100), Huasheng (0%, HKD 100)

**Scoring Results (optional but recommended):**
- Total score from ipo-scoring
- Classification (Whitelist/Greylist/Blacklist)
- Margin recommendation

### Step 2: Build JSON Input

Create a JSON file with all variables:

```json
{
  "stock_code": "01879.HK",
  "company_name": "曦智科技-P",
  "company_intro": "專注於光電混合算力領域...",
  "confirmed_with": "Emily",
  "max_funding_hkd": "港幣 50,000,000元",
  "approved_funding_hkd": "港幣 10,000,000元",
  "cost_rate": "2.27",
  "funding_rate": "0",
  "min_units": "15",
  "leverage": "10",
  "client_ratio": "10",
  "firm_ratio": "90",
  "fee_hkd": "HKD 100",
  "prospectus_date": "2026年4月20日",
  "hkex_url": "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0420/2026042000022_c.pdf",
  "broker_comparison": [
    {"name": "富途證券", "rate": "0", "fee": "HKD 100"},
    {"name": "華盛證券", "rate": "0", "fee": "HKD 100"}
  ],
  "include_scoring": true,
  "scoring": {
    "profitability": 30,
    "allocation": 10,
    "cornerstone": 15,
    "pricing": 20,
    "stabilization": 10,
    "break_rate": 15,
    "hsi": 10,
    "total": 110,
    "classification": "白名单",
    "recommendation": "建議開放孖展，槓桿10倍"
  }
}
```

### Step 3: Generate Email

```bash
cd /Users/rayzyp/Documents/运营流程/IPO孖展评估/.agents/skills/ipo-funding-application/scripts

# Markdown only
python generate_email.py --input data.json --output IPO_Funding_App_01879.md --format md

# Markdown + Word
python generate_email.py --input data.json --output IPO_Funding_App_01879 --format both
```

### Step 4: Review and Send

1. **Check consistency**: Ensure 预批融资额度 matches the amount confirmed with Celine
2. **Verify numbers**: Cross-check 融资利率 against 资金成本
3. **Add HKEX link**: Confirm the announcement URL is correct
4. **Copy to email client**: Markdown can be copied directly; Word can be attached

## Email Structure

The generated email contains two parts:

### Part 1: To Celine (审阅请求)
- Maximum funding capacity and cost of funds
- Broker comparison table
- Request for review before management submission

### Part 2: To Management (批核申请)
- **之光总、Jerry、Frank**
- Company and market introduction
- Margin lending arrangement table
- HKEX reference link
- Closing request for approval

### Optional Part 3: Scoring Reference
- 7-dimension score summary
- IPO classification
- Margin recommendation

## Output Files

| Format | File | Use Case |
|--------|------|----------|
| Markdown | `IPO_Funding_App_[CODE].md` | Copy-paste to email, easy to edit |
| Word | `IPO_Funding_App_[CODE].docx` | Formal attachment, print-friendly |

## Important Rules

1. **Flag inconsistencies**: Always highlight when 预批额度 differs from max funding — let user confirm.
2. **No automatic submission**: The generated email is a DRAFT. User must review before sending.
3. **Sensitive data**: Do not include actual client names or proprietary deal terms in the template.
4. **Language**: Generate in Traditional Chinese (繁體中文) to match existing company style.
5. **No git operations**: Do not commit or push any files.
