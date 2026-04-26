# IPO Scoring Report Specification

Word document output requirements for `.docx` reports.

## Document Setup

- **Font**: Calibri for English, 微软雅黑 for Chinese
- **Default size**: 11pt
- **Language**: Simplified Chinese (primary) + Traditional Chinese (appended after page break)

## Section Structure

### 1. Title
- Text: "IPO 标的质量评分报告"
- Center aligned, 22pt, bold, dark blue (RGB 0x000080)

### 2. Basic Info
- Heading level 1: "标的：[Company Name]（[English Name]）"
- Bullet list:
  - 股份代号：XXXX.HK
  - 招股章程日期：YYYY-MM-DD
  - 发售价：每股H股 XX.XX港元
  - 全球发售规模：X,XXX,XXX股H股
  - 市值：约XX.XX亿港元
  - 行业：[Sector]

### 3. Scoring Sections (7 total)

Each dimension follows this structure:

#### Heading Level 1: "[N]. [Dimension Name]（满分[X]分）"

#### Subsection: "信息原文摘录"
- Block quote style (left indent 0.3in, italic, gray RGB 0x404040)
- Include exact Chinese text from prospectus with citation

#### Subsection: "评分规则对应依据"
- Bold label "评分标准："
- Bullet list of score bands
- Bold label "判定："
- Reasoning text. For pricing, show explicit calculation.

#### Subsection: "单项最终评分"
- Bold text, 14pt
- Color coding:
  - Green (0x008000): Full or near-full marks
  - Orange (0xFF6600): Partial marks
  - Red (0xCC0000): Zero or major deduction
- Add warning paragraph (same color) explaining deduction if score < max

### 4. Summary Table

8 rows + 1 header row, 4 columns:

| 评分维度 | 满分 | 得分 | 得分率 |
|----------|------|------|--------|
| [Dimension 1] | [Max] | [Score] | [Rate] |
| ... | ... | ... | ... |
| **合计** | **110** | **XX** | **XX.X%** |

- Table style: "Light Grid Accent 1"
- Total row: bold, score and rate in red if below 80%

Add note below table:
> 注：稳价机制为奖励分，不计入基础总分。若剔除稳价奖励分，基础满分为100分，本次得分XX分，基础得分率XX.X%。

### 5. IPO Classification

Heading: "IPO分类评估（白名单 / 灰名单 / 黑名单）"

#### Classification Standards Table
3 rows (Whitelist, Greylist, Blacklist), 2 columns.

#### Evaluation Subsection
For each of the 3 conditions in Blacklist, explicitly state:
- Whether the IPO triggers it
- Evidence or reasoning
- If conditionally close to threshold, flag as "需持续跟踪"

Final classification statement in bold, colored blue (0x0066CC).

### 6. Investment Recommendation

Heading: "标的总结与孖展额度决策建议"

#### Subsections
- **基本面评价**: 3-4 bullet highlights
- **发行结构评价**: Bullet list of structural strengths/weaknesses
- **宏观环境评价**: Bullet list of market conditions
- **风险因素提示**: Bullet list of key risks (include policy, litigation, channel, market risks)

#### Decision Table
5 rows × 2 columns:
| 建议维度 | 评估结论 |
|----------|----------|
| 是否开放孖展额度 | [Yes/No/Conditional] |
| 建议孖展杠杆倍数 | [X-X倍] |
| 理由 | [2-3 sentences] |
| 重点关注时点 | [Book-building signals, first day metrics] |

#### Final Rating
- 评分：XX/110（基础分XX/100）
- 得分率：XX.X%
- 评级：[BB+/BBB/etc.]
- IPO分类：[Classification result]

### 7. Disclaimer
- Italic, 9pt, gray (0x808080)
- State data sources: prospectus date, stock code, external data sources
- Note that industry PE is estimated if not directly disclosed

## Color Reference

| Usage | RGB |
|-------|-----|
| Main headings | 0x000080 (dark blue) |
| Full marks | 0x008000 (green) |
| Partial marks / warnings | 0xFF6600 (orange) |
| Zero / critical | 0xCC0000 (red) |
| Classification result | 0x0066CC (blue) |
| Quotes | 0x404040 (gray) |
| Disclaimer | 0x808080 (light gray) |

## Traditional Chinese Appendix

After the complete Simplified Chinese report, insert a page break and reproduce the entire report in Traditional Chinese (繁體中文).

**Key translation notes**:
- 标的 → 標的
- 信息/资讯 → 資訊
- 发售价 → 發售價
- 涨跌幅 → 漲跌幅
- 占 → 佔
- 后 → 後
- 账面 → 賬面
- 亏损 → 虧損
- 净利润 → 淨利潤
- 认购 → 認購
- 回拨 → 回撥
- 通过 → 通過

All section headings, tables, bullet points, and the disclaimer must be fully translated. Keep the same structure, color coding, and formatting.

## File Naming

`IPO_Score_Report_[STOCK_CODE].docx`

Example: `IPO_Score_Report_1609.docx`
