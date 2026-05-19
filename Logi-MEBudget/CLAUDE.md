# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概覽

`Logi-MEBudget` 是 Logi AI 工具群的子資料夾，用於管理 Logitech ME 部門 FY27 預算。

目前狀態：初始化階段，僅有原始 Excel 來源資料 `FY27_ME_Budget.xlsx`，尚無自動化腳本或儀表板。

## 資料來源

- `FY27_ME_Budget.xlsx`：主要預算 Excel 檔，包含 FY27 各季度預算資料，為所有分析腳本的輸入。

## 工具架構（建置中）

本工具預計沿用 Logi AI 的標準模式：
- **資料擷取**：Python 腳本（`openpyxl` 或 `pandas`）讀取 Excel，輸出結構化資料
- **視覺化**：HTML dashboard（參考 `Logi-VC-Competitor-Benchmarker/reports/dashboard.html` 的 Logitech 品牌設計）
- **資料庫**：SQLite（參考 `Logi-VC-Competitor-Benchmarker/vc_benchmark.db` 的模式）

## 父專案關係

本資料夾位於 `C:\Users\skuan1\Desktop\Logi AI\`，共用同一個 git repo（`Datsam8866/Logi-AI`）。收工流程、commit 規範、品牌設計系統均與父專案一致，詳見 `../CLAUDE.md`。
