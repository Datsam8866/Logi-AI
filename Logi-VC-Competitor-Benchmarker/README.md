# Logi-VC-Competitor-Benchmarker

追蹤與分析 Logitech 競品（視訊會議 / VC 相關產品）的市場資訊工具。

## 最新進度

**2026-05-12**
- 初始化專案：建立 CLAUDE.md、SQLite 資料庫、reports 資料夾
- 安裝 `vc-device-benchmarker` skill（`.claude/skills/`）
- 完成首批 3 筆競品 benchmark：Mac Pro Trashcan、Nest Cam IQ、FLIR One Pro
- 資料庫：`vc_benchmark.db`（SQLite，含 devices 表）

## Next Action

- [ ] 新增更多競品（Logitech 直接競品：Jabra、Poly、Yealink、AVer 等 VC 裝置）
- [ ] 建立比較表匯出功能（從 SQLite 產生 Markdown 比較表）
- [ ] 補足 Nest Cam IQ 的 SoC 型號（TechInsights 付費資料）

## 資料夾結構

```
Logi-VC-Competitor-Benchmarker/
├── .claude/
│   └── skills/
│       └── vc-device-benchmarker/   # Benchmark workflow skill
├── reports/                          # 各產品 .md benchmark 報告
├── vc_benchmark.db                   # SQLite 資料庫
├── CLAUDE.md
└── README.md
```

## 使用方式

給產品名稱或 URL，skill 會自動：分類 → 搜尋規格 → 搜尋 teardown → 存 SQLite → 產出 `.md` 報告。
