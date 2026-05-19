# Logi-MEBudget — ME 部門 FY27 預算追蹤工具

**最後更新：2026-05-19（初始化：Excel → SQLite + Business Dashboard 雙 Tab）**

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

### 2026-05-19：初始化

- 解析 `FY27_ME_Budget.xlsx` 雙區塊結構（左：Transactions B–S；右：Budget Overview U–AE）
- `import_to_db.py` 建立 `me_budget.db`（SQLite）：
  - `budget_overview`：96 筆（4 quarters × 24 budget codes）
  - `transactions`：15 筆（Q1 已填入）
- `dashboard.html`：Business Light/Dark 雙模式，兩 Tab
  - **Overview tab**：24 Budget Code 總覽表（可排序 / 搜尋 / 右側 Drawer 細節）
  - **Q1 ME Transactions tab**：Deadline chips + Q1 Summary KPI + 利用率進度條 + 15 筆交易表

---

## Next Action

| 優先 | 項目 | 狀態 |
|------|------|------|
| **A** | 把 ACC_Q1~Q4 匯入 DB（目前只有 ME） | 待辦 |
| **B** | Q2/Q3/Q4 有資料後，dashboard 加季度切換 Tab | 待辦 |
| **C** | 整合 `dump_data.py` / `verify_db.py` → 合入 `import_to_db.py` | 待辦 |

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
