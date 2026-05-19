# Logi-MEBudget — ME 部門 FY27 預算追蹤工具

**最後更新：2026-05-19（Dashboard 大幅升級：Q1-Q4 季度切換 + Overview 跨季視覺化 + UX 改善）**

---

## 專案概覽

Logi-MEBudget 是 ME 部門 FY27 預算管理工具，將 Excel 原始預算表解析為 SQLite 資料庫，並以 Business Light/Dark Dashboard 視覺化各季度預算分配與消費進度。

| Quarter | Budget Codes | 有預算筆數 | Transactions | 總預算 | 剩餘 | 狀態 |
|---------|-------------|-----------|-------------|--------|------|------|
| **Q1** | 24 | 16 | 15 筆 | $213K | $168.7K | Dashboard 完成；27287/27303 Overbudget |
| Q2 | 24 | — | 0 筆 | — | — | 尚未填入 |
| Q3 | 24 | — | 0 筆 | — | — | 尚未填入 |
| Q4 | 24 | — | 0 筆 | — | — | 尚未填入 |

---

## 最新進度

### 2026-05-19：Dashboard 大幅升級

- **5 Tab 架構**：Overview + Q1 / Q2 / Q3 / Q4（JS 動態渲染，data-driven）
- **Overview Tab**：
  - 3 張 KPI（FY27 Total Budget / Overbudget Alerts / Active Quarters）
  - Horizontal Stacked Bar：Q1–Q4 預算規模比較 + Budget Utilization 標示
  - Budget Code 表格：跨季 Q1/Q2/Q3/Q4 欄位，狀態 badge 顏色示警（Overbudget / Near Limit / In Pipeline / Active / Pending）
- **Q1–Q4 Tabs**：3 張 KPI + Deadline chips + 利用率進度條 + Transactions 表格
- **UX 改善**：Overview Drawer 加季度下拉選單（預設 Q1）、Q1 tab Active badge、進度條最小可見寬度、Header 日期動態顯示、Business design token 修正

### 2026-05-19：初始化

- 解析 `FY27_ME_Budget.xlsx` 雙區塊結構，建立 SQLite DB（96 + 15 筆），Business Light/Dark Dashboard

---

## Next Action

| 優先 | 項目 | 狀態 |
|------|------|------|
| **A** | 把 ACC_Q1~Q4 匯入 DB（目前只有 ME） | 待辦 |
| **B** | 整合 `dump_data.py` / `verify_db.py` / `dump_quarters.py` → 合入 `import_to_db.py` | 待辦 |
| **C** | Deadline 截止日倒數提示（days left + 顏色示警） | 待辦 |

---

## Dashboard 使用方式

直接用瀏覽器開啟（單一 HTML 檔，無需伺服器）：

```
Logi-MEBudget/dashboard.html
```

- **Overview tab**：所有 Budget Code 的預算 / 消耗 / 剩餘總覽；點 row 開右側 Drawer 看明細
- **Q1 ME Transactions tab**：Deadline 截止日提醒 + KPI 摘要 + 所有交易紀錄

---

## 主要檔案

| 路徑 | 說明 |
|------|------|
| `FY27_ME_Budget.xlsx` | 原始預算 Excel，13 個 sheet（ME_Q1~Q4、ACC_Q1~Q4 等） |
| `import_to_db.py` | 解析 Excel → SQLite，執行一次即匯入全部 ME 四個季度 |
| `me_budget.db` | SQLite 資料庫；`budget_overview`（96筆）+ `transactions`（15筆） |
| `dashboard.html` | Business Light/Dark 單頁 Dashboard |

---

## 注意事項

- `me_budget.db` 已納入 git 追蹤（體積小，約 24 KB）
- `remaining = null` 代表 Overbudget（Excel 原始 `-` 值），非資料缺失
- Dashboard 資料為靜態 JSON（inline），需重新執行 `import_to_db.py` + 手動更新 `dashboard.html` 的 `OV` / `TX` 陣列後才會刷新
- ACC（Accessories）系列 Q1~Q4 尚未匯入，DB 只含 ME 部門
