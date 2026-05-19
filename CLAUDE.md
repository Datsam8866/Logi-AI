# Logi AI — 我的班級工具總專案

## 對話開始時請先讀
根據目前工作的子資料夾名稱，讀取對應的 Obsidian 工作筆記：
`G:\其他電腦\我的電腦\Obsidian Vault\Logitech\<資料夾名稱>工作筆記.md`

例如：在 `Logi-MEBudget/` 工作 → 讀 `Logi-MEBudget工作筆記.md`

## 工作模式
- **加新工具**：對 Claude 說「我想做一個 XXX 工具」→ Claude 會建對應子資料夾、初始化 CLAUDE.md 與工作筆記
- **結束工作**：對 Claude 說「**收工**」→ 自動 commit + push + 更新 `<資料夾名稱>工作筆記.md`
- **接續工作**：對 Claude 說「讀工作筆記、告訴我上次做到哪」→ 讀當前子資料夾對應的工作筆記

## 工作桌 + 三個家
- 💻 本機工作桌：`C:\Users\skuan1\Desktop\Logi AI\`
- 🐙 GitHub repo：`Datsam8866/Logi-AI`（公開，網頁的家）
- 📘 Obsidian 駕駛艙：`G:\其他電腦\我的電腦\Obsidian Vault\Logitech\`（各工具各自一份筆記）

## 工具清單
- `Logi-VC-Competitor-Benchmarker/`：VC 競品 benchmark dashboard（SQLite + HTML）
- `Logi-MEBudget/`：ME 部門 FY27 預算追蹤（Excel → SQLite + Business dashboard）
- `Logi-Thermal-Resource/`：Thermal 驗證資源整理
- `Logi-DBTemplate/`：資料庫模板

## 工作注意事項
- 學生資料一律去識別化（只用座號 + 班級代號）
- commit 訊息要寫清楚做了什麼 + 為什麼
- 收工前說「收工」讓 Claude 同步三方
