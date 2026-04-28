# IPO Funding Application Email Template

## 模板来源
基于 `/Users/rayzyp/知识库/P-01879-曦智科技-IPO孖展融資申請.md` 结构化整理。

## 邮件结构（两部分）

---

### Part 1: 致 Celine 的审阅请求

**收件人**: Celine
**主题**: 【审阅请求】[STOCK_CODE] [COMPANY_NAME] IPO孖展融資申請內容

```
Dear Celine,

我已與 [CONFIRMED_WITH] 確認，本次 **[STOCK_CODE] [COMPANY_NAME]** 我們最多可提供 **[MAX_FUNDING_HKD]** 作為IPO孖展融資總額，**資金成本為 [COST_RATE]%**。在向管理層申請審批前，想先請你協助審閱以下草擬申請內容，如有任何意見或建議（特別是有關孖展利率、手續費或預批融資額度部分），請指示：

### 其他券商融資利率及手續費參考

| 券商 | 銀行融資利率 | 手續費 |
|:---|:---|:---|
| 富途證券 | [RATE_1] | [FEE_1] |
| 華盛證券 | [RATE_2] | [FEE_2] |
| [OTHER_BROKER] | [RATE_3] | [FEE_3] |

以上，謝謝！
```

**变量说明**:

| 变量 | 说明 | 示例 |
|------|------|------|
| CONFIRMED_WITH | 已确认对象 | Emily |
| STOCK_CODE | 港股代码 | 01879.HK |
| COMPANY_NAME | 公司简称 | 曦智科技-P |
| MAX_FUNDING_HKD | 最大可提供融资总额 | 港幣 50,000,000元 |
| COST_RATE | 资金成本率 | 2.27 |
| RATE_1/FEE_1 | 竞品券商利率/手续费 | 0 / HKD 100 |

---

### Part 2: 致管理层的批核申请

**收件人**: 之光总、Jerry、Frank
**主题**: 【批核申請】[STOCK_CODE] [COMPANY_NAME] IPO孖展融資服務

```
致之光總、Jerry及 Frank:

**[STOCK_CODE] [COMPANY_NAME]** 已通過香港交易所批准，已進入首次公開募股（IPO）階段。為配合本次IPO，本公司計劃向客戶提供新股認購貸款預約服務，現正式提交批核申請。申請詳情如下：

### 一、公司及市場簡介

[COMPANY_INTRO]

### 二、孖展融資安排

[STOCK_CODE] [COMPANY_NAME] 首次公開招股，本公司將推出相關孖展融資服務，具體安排如下：

| 項目 | 安排 |
|:---|:---|
| **融資利率** | **[FUNDING_RATE]%** |
| 最低申請數量 | [MIN_UNITS]股起 |
| 融資認購槓桿 | [LEVERAGE]倍（客戶需支付[CLIENT_RATIO]%，公司提供[FIRM_RATIO]%融資） |
| **融資認購手續費** | **[FEE_HKD]** |
| **預批融資額度** | **[APPROVED_FUNDING_HKD]**（作為本次IPO的孖展融資總額） |

> ⚠️ **注意**：此處預批融資額度為 **[APPROVED_FUNDING_HKD]**，與第一部分致 Celine 的 **[MAX_FUNDING_HKD]** 是否一致，請確認最終額度。

### 三、其他

有關該公司最新財務數據，可參考以下連結：

📎 [港交所公告 - [PROSPECTUS_DATE]]([HKEX_URL])

---

## 申請結語

懇請營運部依照上述內容完成系統配置，並批核本申請。

敬請審核批准。
```

**变量说明**:

| 变量 | 说明 | 示例 |
|------|------|------|
| COMPANY_INTRO | 公司及市场简介段落 | 公司專注於XX領域... |
| FUNDING_RATE | 对客户融资利率 | 0 |
| MIN_UNITS | 最低申请股数 | 15 |
| LEVERAGE | 杠杆倍数 | 10 |
| CLIENT_RATIO | 客户出资比例 | 10 |
| FIRM_RATIO | 公司融资比例 | 90 |
| FEE_HKD | 手续费 | HKD 100 |
| APPROVED_FUNDING_HKD | 预批额度 | 港幣 10,000,000元 |
| PROSPECTUS_DATE | 招股书日期 | 2026年4月20日 |
| HKEX_URL | 港交所公告链接 | https://www1.hkexnews.hk/... |

---

## 评分结果引用规范

在邮件中可简要引用 `ipo-scoring` 评分结果作为决策依据：

```
### 四、IPO標的質量評估（參考）

經內部評分模型評估，[COMPANY_NAME] 的IPO質量評分如下：

| 評分維度 | 得分 |
|:---|:---|
| 過往3年盈利情況 | [SCORE_PROFIT]/30 |
| 分配機制 | [SCORE_ALLOC]/10 |
| 基石投資人 | [SCORE_CORNER]/15 |
| 定價情況（靜態PE） | [SCORE_PRICING]/20 |
| 穩價機制 | [SCORE_STAB]/10 |
| 市場宏觀—新股破發率 | [SCORE_BREAK]/15 |
| 市場宏觀—恒生指數 | [SCORE_HSI]/10 |
| **合計** | **[TOTAL_SCORE]/110** |

IPO分類：**[CLASSIFICATION]**
孖展建議：**[MARGIN_RECOMMENDATION]**
```

---

## 输出格式

- 默认输出 Markdown (`.md`)
- 可选输出 Word (`.docx`) — 使用 `python-docx` 格式化

文件名规范: `IPO_Funding_App_[STOCK_CODE].md`
