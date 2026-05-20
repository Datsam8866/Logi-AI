# Logi-MEBudget — ME 部門 FY27 預算追蹤工具

**最後更新：2026-05-20（Google OAuth + viewer/editor 權限；Cloudflare Tunnel 已可跨 Wi-Fi 登入）**

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

- **Q tab 交易 UX**：新增 Q2-Q4 未匯入 empty state、Cost 顯示 USD budget impact、刪除摘要確認視窗、Add Transaction SQLite 儲存提示
- **新增交易換算與排序**：Add Transaction 選 TWD 時自動以 `1 USD = 31.6 TWD` 換算為 USD budget impact；Q tab 交易表優先顯示 Will Expensify、Will PR
- **區網瀏覽支援**：`server.py` 改為綁定 `0.0.0.0`，同一個 Wi-Fi / LAN 內其他裝置可用本機 IP 加 port 5173 開啟 dashboard
- **Google OAuth 權限**：`server.py` 改用 Google 登入；`ALLOWED_VIEWERS` 可看 dashboard，`ALLOWED_EDITORS` 可新增/刪除，後端 API 會擋非 editor 操作
- **Dashboard 互動修復**：修正 `export_dashboard.py` 使用 `re.sub()` 寫回 JSON 時把 `\n` 轉成實際換行，導致 `dashboard.html` 出現 JavaScript SyntaxError、Tab/FAB/Dark mode 無反應的問題
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
$env:GOOGLE_CLIENT_ID="Google OAuth Client ID"
$env:GOOGLE_CLIENT_SECRET="Google OAuth Client Secret"
$env:ALLOWED_VIEWERS="viewer1@example.com,viewer2@example.com"
$env:ALLOWED_EDITORS="editor@example.com"
$env:MEBUDGET_SECRET_KEY="任意長隨機字串，重啟後 session 才能穩定；留空會自動產生臨時值"
python server.py
# 開瀏覽器 → http://localhost:5173
# 同一個 Wi-Fi / LAN 的其他裝置 → http://192.168.0.113:5173
# 注意：PowerShell 視窗不能關，server 才會持續運作
```

若其他裝置無法連線，先確認兩台裝置在同一個網路，並允許 Windows 防火牆讓 Python 使用私人網路。
若使用 Cloudflare Tunnel，公開網址會先導到 Google 登入；quick tunnel 網址改變時，Google OAuth Client 的 redirect URI 也要同步新增。callback 請使用 `https://<quick-tunnel-domain>/auth/google/callback`。

Cloudflare Tunnel 成功流程：

```powershell
# 視窗 1：啟動 Flask server，並保持視窗開啟
python server.py

# 視窗 2：啟動 tunnel，並保持視窗開啟
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5173
```

拿到新的 `https://xxxxx.trycloudflare.com` 後，必須在 Google OAuth Client 同步新增：

- Authorized JavaScript origins：`https://xxxxx.trycloudflare.com`
- Authorized redirect URIs：`https://xxxxx.trycloudflare.com/auth/google/callback`

若出現 `Error 1033`，代表 `cloudflared` 已停止或 quick tunnel 失效；重新啟動 tunnel 後會產生新網址，OAuth 設定也要跟著更新。若出現 `invalid_client`，代表 server 使用的 `GOOGLE_CLIENT_SECRET` 不正確，需重設 secret 並重啟 `server.py`。

**Google Cloud Run 部署：**

```powershell
gcloud config set project logi-mebudget-dashboard
gcloud run deploy logi-mebudget --source . --region asia-east1 --allow-unauthenticated
```

部署完成後，把 Cloud Run 產生的 `https://...run.app` 加到 Google OAuth Client：

- Authorized JavaScript origins：`https://...run.app`
- Authorized redirect URIs：`https://...run.app/auth/google/callback`

再設定 Cloud Run runtime env：

```powershell
gcloud run services update logi-mebudget --region asia-east1 `
  --update-env-vars GOOGLE_CLIENT_ID="..." `
  --update-env-vars GOOGLE_CLIENT_SECRET="..." `
  --update-env-vars ALLOWED_VIEWERS="viewer@example.com" `
  --update-env-vars ALLOWED_EDITORS="editor@example.com" `
  --update-env-vars MEBUDGET_SECRET_KEY="固定長隨機字串"
```

注意：目前雲端版仍使用 repo 內 SQLite 檔案，適合先驗證登入與瀏覽；若要多人長期新增/刪除，後續應改 Cloud SQL 或 Firestore。

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
