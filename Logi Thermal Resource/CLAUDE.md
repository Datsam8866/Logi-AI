# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用指令

```bash
# 首次或 Excel 更新後，重建 SQLite 資料庫
python -m src.etl

# 確認 ETL 結果（row count、工程師、年度）
python -m src.etl --check

# 啟動 Streamlit Dashboard
streamlit run app.py
```

## 架構概覽

### 資料流

```
Excel (.xlsx)
  └─ src/etl.py (parse_year_sheet / parse_projects_sheet / parse_indicator_sheet)
       └─ data/thermal.db (SQLite)
            └─ src/db.py (query helpers)
                 ├─ src/viz.py (Plotly 圖表元件)
                 └─ src/ai/*.py (AI 功能)
                      └─ app.py (Streamlit 入口)
```

### 關鍵設計決策

**ETL schema 自動偵測**（`src/etl.py:_detect_schema`）：Excel 在 2025 年新增了 Sub-Category 欄，使總欄數從 28 變為 29。ETL 透過掃描 header row 動態定位 `Project`、`Engineer`、`Jan` 欄位，而非寫死欄號。2022 sheet 有額外的年份 band header（row 0 = "2021" / "2022"），也在此處處理。

**兩組 Jan–Dec block**：每張年度表有兩組 Jan–Dec（block 1 / block 2）。B2B 類別資料落在 block 2，L4B Vision 類別落在 block 1。`loadings` 表保留 `block` 欄，查詢時 `SUM(load)` 即可得總負載（無需區分 block）。

**Vision 前瞻列**：L4B Vision Project Planning 類別的列沒有 engineer，ETL 將其歸入 `"Unassigned (Vision)"`，保留數據不丟失。

**AI 問答**（`src/ai/nl_query.py`）：使用 Claude tool use agentic loop（最多 4 輪），工具 `run_sql` 透過 `db.safe_select()` 強制 SELECT-only，並自動補 `LIMIT 1000`。system prompt 用 `cached_system()` 包裝以啟用 prompt caching。

**資源平衡**（`src/ai/balancer.py`）：先用規則層計算 overload（>1.0）/ idle（<0.3）月份，再把摘要送給 Claude 產生中文調配建議。

**負載預測**（`src/ai/forecaster.py`）：對 `target_mp` 仍在未來的活躍專案，從今天起套用各 State 的 hardcoded 典型曲線（`STATE_CURVES`），疊加後得未來 N 個月的預測負載。

### SQLite schema 摘要

- `engineers(id, name)` — 工程師
- `projects(id, name, sub_category, state, go_date, target_mp, ...)` — 從 Sheet14 匯入
- `loadings(engineer_id, project_id, category, year, month, block, load, ...)` — 主要負載資料，含反正規化欄位（project_name / sub_category / vendor）便於過濾
- `thermal_indicator(score, description, applies_to)` — 評分字典

### 環境設定

需要 `.env` 檔（從 `.env.example` 複製）才能使用 AI 功能：
```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6   # 可選，預設即此值
```

不設定 API Key 時，Overview / Engineer Load / Projects 三個分頁仍可正常使用。
