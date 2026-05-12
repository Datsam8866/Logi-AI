# Logi-VC-Competitor-Benchmarker

追蹤與分析 Logitech 競品（視訊會議 / VC 相關產品）的市場資訊工具。

## 最新進度

**2026-05-12**
- 初始化專案，完成首批 3 筆競品 benchmark：Mac Pro Trashcan、Nest Cam IQ、FLIR One Pro
- 新增 AVer VB370A、AVer VB350（Room Bar 類）benchmark，資料庫共 5 筆
- 建立互動式 HTML dashboard（`reports/dashboard.html`）：
  - KPI 卡片、Category tabs（Overview + 各類別一個 tab）
  - 功能比較矩陣、拆解分析面板、Dynamic Columns 手風琴
  - Markdown 匯出按鈕
  - 更新資料鍵（呼叫本機伺服器 `/api/refresh` 重讀 SQLite）
- 建立本機伺服器 `serve_dashboard.py`（`http://localhost:8765/`）
- 修正 tab 切換 Bug：根本原因為 Python import cache，修改程式後須重啟伺服器才能生效

**已知注意事項**
- 修改 `generate_dashboard.py` 後，需重啟 `serve_dashboard.py`（不能只用「更新資料」鍵）

## Next Action

- [ ] 新增更多 VC 競品（Jabra PanaCast、Poly Studio、Yealink UVC84 等）
- [ ] 補足 Nest Cam IQ SoC 型號（TechInsights 付費資料）
- [ ] 考慮在 dashboard 加 Logitech 自家基準欄位（作為比較基準線）

## 資料夾結構

```
Logi-VC-Competitor-Benchmarker/
├── .claude/
│   └── skills/
│       └── vc-device-benchmarker/   # Benchmark workflow skill
├── reports/                          # .md benchmark 報告 + dashboard.html
├── vc_benchmark.db                   # SQLite 資料庫（5 筆）
├── generate_dashboard.py             # 生成 dashboard HTML
├── serve_dashboard.py                # 本機 HTTP 伺服器（port 8765）
├── CLAUDE.md
└── README.md
```

## 使用方式

**Benchmark 新競品**：給產品名稱或 URL，skill 會自動分類 → 搜尋規格 → 搜尋 teardown → 存 SQLite → 產出 `.md` 報告。

**啟動 Dashboard**：
```powershell
python serve_dashboard.py
# 開啟 http://localhost:8765/
```

**僅重新生成 HTML（不啟動伺服器）**：
```powershell
python generate_dashboard.py
```
