# Logi-Hinoki 專案規則

## 開始工作前

- 本檔只適用 Logi-Hinoki；保留上層共用規則，但 Hinoki 進度來源以本檔指定的專屬筆記為準。
- 先讀本目錄 `README.md`，再讀 Obsidian：`G:\其他電腦\我的電腦\Obsidian Vault\Logitech\Logi-Hinoki工作筆記.md`。
- 不以 `Logi-MEBudget工作筆記.md` 作為 Hinoki 的進度或 Next Action 來源。
- 實作前檢查 Git branch、HEAD、status；目前有效工作目錄與交接基準記在專屬筆記，不假設桌面原始 checkout 已同步。
- 按任務閱讀 `docs/superpowers/specs/` 與 `docs/superpowers/plans/` 的對應設計／計畫；衝突或範圍不明時先釐清。

## 文件與變更邊界

- AGENTS 記固定規則與路徑；README 記現況／Next Action；Obsidian 記歷程；plan 記實作步驟。
- 每份 `AGENTS.md` 與 `README.md` 均不得超過 250 行，包含空白行；超過時保留必要資訊並將細節移至其他文件。
- 僅修改本次任務相關內容，保留既有工作；不自動 pull、merge、commit、push 或清理 worktree。
- 保留 inferred engineering prototype、not manufacturing release 的限制聲明；不得將推定值宣稱為已知供應商規格。
- 不擅自覆寫正式 CAD/JSON 或舊 Iteration 產物；先用臨時輸出完成驗證，正式替換須在已確認範圍內。
- 支架、線材、圖片或熱模擬衍生包等額外項目，以目前核准任務範圍為準，不因舊計畫仍有步驟就自動執行。
