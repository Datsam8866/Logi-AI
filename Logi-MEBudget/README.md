# Logi-MEBudget — ME 部門 FY27 預算追蹤工具

**最後更新：2026-05-20（修正 server.py charset 問題；dashboard 可正常在 http://localhost:5173 使用）**

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

### 2026-05-20：CRUD + SQLite 雙模式架構

- **Deadline 倒數示警**：每個 Quarter tab 的 Deadline chip 自動計算 days left，顏色分級（綠 >21d / 橘 8–21d / 紅 ≤7d / 暗紅 overdue）
- **Add Transaction**：右下 FAB（＋）開 Modal，輸入 Item 自動建議 Budget Code，支援 Project 選擇
- **Delete Transaction**：每筆交易右側 ✕ 按鈕，confirm 後刪除
- **SQLite 雙模式**：
  - `python server.py` → `http://localhost:5173`：新增/刪除直接寫入 SQLite，自動重新匯出 dashboard.html
  - 直接開 .html：localStorage 暫存（離線用）
- **`server.py`（新）**：Flask local server，`POST/DELETE /api/txn`
- **`export_dashboard.py`（新）**：從 SQLite 讀取最新資料，重寫 QUARTERS JSON block

### 2026-05-19：Dashboard 大幅升級

- 5 Tab 架構（Overview + Q1–Q4）、跨季 Stacked Bar、Drawer 季度選單、UX 修正

---

## Next Action

| 優先 | 項目 | 狀態 |
|------|------|------|
| **A** | 把 ACC_Q1~Q4 匯入 DB（目前只有 ME） | 待辦 |
| **B** | 整合 `dump_data.py` / `verify_db.py` / `dump_quarters.py` → 合入 `import_to_db.py` | 待辦 |
| ~~C~~ | ~~Deadline 截止日倒數提示~~ | ✅ 完成 |

---

## Dashboard 使用方式

**Server mode（推薦，支援新增/刪除寫入 SQLite）：**

```powershell
cd "C:\Users\skuan1\Desktop\Logi AI\Logi-MEBudget"
python server.py
# 開瀏覽器 → http://localhost:5173
# 注意：PowerShell 視窗不能關，server 才會持續運作
```

**Static mode（離線，僅 localStorage）：**
```
直接開 Logi-MEBudget/dashboard.html
```

- **Overview tab**：所有 Budget Code 的預算 / 消耗 / 剩餘總覽；點 row 開右側 Drawer 看明細
- **Q1–Q4 tab**：Deadline 倒數 + KPI 摘要 + 交易紀錄（可新增 ＋ / 刪除 ✕）

---

## 主要檔案

| 路徑 | 說明 |
|------|------|
| `FY27_ME_Budget.xlsx` | 原始預算 Excel，13 個 sheet（ME_Q1~Q4、ACC_Q1~Q4 等） |
| `import_to_db.py` | 解析 Excel → SQLite，執行一次即匯入全部 ME 四個季度 |
| `me_budget.db` | SQLite 資料庫；`budget_overview`（96筆）+ `transactions`（15筆起） |
| `dashboard.html` | Business Light/Dark 單頁 Dashboard（inline QUARTERS JSON） |
| `server.py` | Flask local server（port 5173），提供 CRUD API |
| `export_dashboard.py` | 從 SQLite 重新產生 dashboard.html 的 QUARTERS block |

---

## 注意事項

- `me_budget.db` 已納入 git 追蹤（體積小，約 24 KB）
- `remaining = null` 代表 Overbudget（Excel 原始 `-` 值），非資料缺失
- Dashboard 資料為靜態 JSON（inline），需重新執行 `import_to_db.py` + 手動更新 `dashboard.html` 的 `OV` / `TX` 陣列後才會刷新
- ACC（Accessories）系列 Q1~Q4 尚未匯入，DB 只含 ME 部門
