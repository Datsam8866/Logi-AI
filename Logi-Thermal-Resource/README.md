# Logi AI Thermal Resource Dashboard

Logitech 熱設計工程資源分析與 AI 問答工具。

---

## 最新進度（2026-05-14）

Dashboard 全功能完成，並套用 Logitech 品牌設計語言，與 VC Competitor Benchmarker 風格一致。

完成項目：
- ETL：`Logi Thermal Resource Dashboard.xlsx` → `data/thermal.db`（710 筆 loadings，2021–2027）
- 6 個 Streamlit 分頁：Overview / Engineer Load / Projects / AI 平衡建議 / AI 預測 / Ask AI
- Claude Sonnet 4.6 自然語言問答（tool use + SQLite SELECT-only gate）
- 資源過載/閒置自動偵測 + LLM 調配建議
- 基於 State 典型曲線的未來 6–12 個月負載預測
- **Logitech Brand Design**：
  - Poppins 字型（wght 400–800）
  - Breakthrough Bar（頁面頂端 4px `#0DFDCF` 色條）
  - 主色 `#00978A`，KPI 數字 2.2rem / 800 weight
  - Dark Mode toggle（sidebar 頂端，`#1B1B1B` 背景 + `#0DFDCF` 強調色）
  - `.streamlit/config.toml` 設定 Logitech 基底主題

---

## Next Action

1. **設定 `.env`**：複製 `.env.example` → `.env`，填入 `ANTHROPIC_API_KEY`，啟用 AI 三個分頁
2. **使用者驗收**：逐頁確認資料與 Excel 原檔一致（特別是 2026 年各工程師月負載數值）
3. **（選擇性）新增年度**：若 2027 年 Excel 加入，ETL 只需在 `YEAR_SHEETS` 加入 `"2027"` 並重跑

---

## 快速啟動

```bash
pip install -r requirements.txt
cp .env.example .env        # 填入 ANTHROPIC_API_KEY
python -m src.etl           # 建立資料庫
streamlit run app.py        # 啟動 Dashboard → http://localhost:8501
```

## 功能說明

| 分頁 | 功能 | 需 API Key |
|---|---|---|
| 📊 Overview | 年度 Heatmap、月負載趨勢、State 分布 | 否 |
| 👤 Engineer Load | 個人月度負載堆疊分解 | 否 |
| 📋 Projects | 專案 Gantt + 狀態表格 | 否 |
| ⚖️ AI 平衡建議 | 過載/閒置偵測 + Claude 調配建議 | 是 |
| 🔮 AI 預測 | State 曲線推算未來 3–12 月負載 | 否 |
| 💬 Ask AI | 中文自然語言問答 Claude | 是 |

## 資料更新

Excel 有修改時，點擊側邊欄「🔄 重新匯入 Excel」，或執行 `python -m src.etl`。

## 已知限制

- 預測曲線使用 hardcoded 參數（PA1/PB1/PQR 等），非從歷史資料回歸
- 支援格式：`Logi Thermal Resource Dashboard.xlsx`（2022–2026 年度表 + Sheet14 + Thermal loading Indicator）
