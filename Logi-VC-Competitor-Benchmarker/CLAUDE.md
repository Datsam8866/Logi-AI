# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案定位

這是 `Logi AI` 工作站下的子工具，用途是追蹤與分析 Logitech 競品（視訊會議設備 / VC 產品線）的市場資訊。
父專案位於 `C:\Users\skuan1\Desktop\Logi AI\`，GitHub repo 為 `Datsam8866/Logi-AI`。

## 開發慣例（繼承自父專案）

- 學生資料去識別化（只用座號 + 班級代號）；競品資料請確認是否含敏感商業資訊再 commit
- commit 訊息格式：`做了什麼 + 為什麼`
- 收工前說「收工」讓 Claude 同步 Obsidian 工作筆記與 GitHub

## 環境注意

- 平台：Windows 11，PowerShell
- 腳本一律以 UTF-8 BOM 儲存（避免中文亂碼）
- `.env` 已列入 `.gitignore`，API key 放 `.env`，不進 commit

## 架構（尚待建立）

> 此專案目前為空。首次建立架構後，請在此補充：
> - 技術棧（Python / Node / Streamlit…）
> - 資料來源（爬蟲、手動匯入、API…）
> - 資料夾結構說明
> - 常用指令（run / lint / test）
