# Logi-Hinoki

Hinoki 是一套 32-inch All-in-One Video Conferencing System 的概念機構與空間配置專案。目前正以 **Calm Crown Concept CAD Iteration 03** 從外觀架構重新建模；Iteration 02 保留為被否決的 preliminary proxy baseline，不再作為產品外觀方向。

> Iteration 02 仍是概念 review 模型，不是 release geometry，也不代表量產設計已完成。

## 目前狀態（2026-09-02）

- 最新階段：Calm Crown Concept CAD Iteration 03，Task 2 品質修正已完成，待重新審核
- 分支：`codex/hinoki-iteration02-review`
- Iteration 03 頭部：742 × 492 × 62 mm，72 mm AV crown
- 正面原生 CAD：已建立 13 個獨立可視零件與五個頂層 group
- Agent review：Task 1 通過；Task 2 規格通過，兩個 Important 品質修正已完成，待重新審核放行
- Concept delivery gate：所有 hard gates 通過且加權分數至少 80/100
- Release／製造 gate：至少 90/100；本階段不宣稱達成
- Iteration 02 CAD review：PassWithOpenRisks，但只代表 proxy 空間配置
- Iteration 02 顯示頭包絡：760 × 80 × 540 mm
- 顯示器 review proxy：One World Touch LM-3237-26B-4K，750.4 × 452.7 × 56.5 mm
- Camera baseline：Leopard Imaging LI-IMX477-MIPI-140H，140° HFOV
- Stand benchmark：Ergotron HX 45-475-224；VESA 200 × 200 mm
- 支架姿態：low / neutral / high
- Display-bottom height：370 / 430 / 490 mm
- Tilt：−5° / 0° / +20°
- STEP：已匯出概念審查版；非 release／製造幾何

Iteration 02 preliminary review 顯示：display proxy 位於 head envelope 內，但左右各只剩 4.8 mm；上方 AV reserve 為 87.3 mm，深度 reserve 為 23.5 mm。Ergotron HX 對 14 kg display proxy 的理論剩餘載重為 5.1 kg，尚未計入 Hinoki AV、compute、thermal、cable 與結構重量。

## 專案結構

```text
Logi-Hinoki/
├─ cad/iteration-01/        # FreeCAD 模型、建模／預覽／review 腳本與 JSON 結果
├─ cad/iteration-02/        # 初步市場包絡 review CAD、預覽與 JSON 結果
├─ cad/iteration-03/        # Calm Crown 受控參數、原生 CAD 與建模腳本
├─ data/iteration-02/       # 候選料號與來源資料
├─ docs/reviews/            # 架構映射、pre-CAD audit、checklist 與 CAD review
├─ docs/superpowers/        # 已核准的設計規格與執行計畫
├─ outputs/hinoki-iteration02-review/ # Iteration 02 候選工作簿
├─ tests/                   # Iteration 01 acceptance tests
├─ Dixie/                   # Dixie 參考資料（目前未納入 Git）
├─ outputs/                 # 工作輸出
└─ Hinoki_Master_Parameters_and_Assumption_Log.xlsx
```

重要檔案：

| 檔案 | 用途 |
|---|---|
| `cad/iteration-01/Hinoki_Concept_CAD_Iteration01.FCStd` | Iteration 01 FreeCAD 裝配 |
| `cad/iteration-01/build_hinoki_iteration01.py` | 從參數重建概念 CAD |
| `cad/iteration-01/preview_hinoki_iteration01.py` | 在 FreeCAD GUI 套用 review view 並輸出 PNG |
| `cad/iteration-01/review_iteration01.py` | 執行包絡、碰撞、panel geometry 與 FOV 檢查 |
| `cad/iteration-01/Hinoki_Iteration01_CAD_Review.json` | CAD review 結果 |
| `tests/test_hinoki_iteration01.py` | CAD 重建與必要物件／參數 acceptance checks |
| `docs/reviews/2026-09-01-hinoki-cad-iteration01-review.md` | Iteration 01 review 摘要 |
| `outputs/hinoki-iteration02-review/Hinoki_Iteration02_Component_Candidates.xlsx` | 公式驅動候選矩陣、CAD 包絡與來源 |
| `cad/iteration-02/Hinoki_Concept_CAD_Iteration02_Review.FCStd` | Iteration 02 初步 review CAD |
| `cad/iteration-02/Hinoki_Concept_CAD_Iteration02_Concept.stp` | Iteration 02 概念審查用 STP |
| `cad/iteration-02/export_iteration02_step.py` | 從 FCStd 匯出概念審查 STEP |
| `cad/iteration-02/Hinoki_Iteration02_CAD_Review.json` | Iteration 02 自動 review 結果 |
| `tests/test_hinoki_iteration02.py` | Iteration 02 acceptance checks |
| `docs/reviews/2026-09-01-hinoki-iteration02-preliminary-review.md` | Iteration 02 初步 review 摘要 |
| `docs/superpowers/specs/2026-09-01-hinoki-calm-crown-concept-design.md` | Calm Crown 設計凍結與交付 gate |
| `docs/superpowers/plans/2026-09-01-hinoki-calm-crown-cad-plan.md` | Iteration 03 八階段實作與審核計畫 |
| `cad/iteration-03/hinoki_calm_crown_parameters.py` | Iteration 03 受控尺寸、物件 manifest 與評分契約 |
| `cad/iteration-03/build_hinoki_calm_crown.py` | Calm Crown FreeCAD 建模腳本 |
| `cad/iteration-03/Hinoki_CalmCrown_Concept.FCStd` | Task 2 正面外觀原生 CAD；尚未通過品質 gate |
| `tests/test_hinoki_iteration03.py` | Iteration 03 參數與原生 CAD 契約測試 |
| `Hinoki_Master_Parameters_and_Assumption_Log.xlsx` | 主參數與假設追蹤表（目前未納入 Git） |

## 環境需求

- Windows PowerShell
- FreeCAD 1.1，需可執行 `freecadcmd.exe`
- Python `unittest`（由 FreeCAD Python runtime 執行 CAD 相關工作）

測試預設使用：

```text
C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe
```

若 FreeCAD 安裝位置不同，先設定：

```powershell
$env:FREECAD_CMD = "C:\path\to\FreeCAD\bin\freecadcmd.exe"
```

## 重建與驗證

在 `Logi-Hinoki` 根目錄執行 acceptance test；測試會呼叫 FreeCAD、重建 FCStd，並驗證必要物件與主參數：

```powershell
python -m unittest tests.test_hinoki_iteration01 tests.test_hinoki_iteration02 -v
```

執行幾何 review：

```powershell
Get-Content -Raw .\cad\iteration-01\review_iteration01.py |
  & $env:FREECAD_CMD -c
```

review 會更新：

```text
cad/iteration-01/Hinoki_Iteration01_CAD_Review.json
```

若要輸出預覽圖：

1. 用 FreeCAD GUI 開啟 `cad/iteration-01/Hinoki_Concept_CAD_Iteration01.FCStd`。
2. 在 FreeCAD Python console 執行 `preview_hinoki_iteration01.py`。
3. 確認輸出 `Hinoki_Concept_CAD_Iteration01_Preview.png`。

## Iteration 02 Review 通過範圍

目前自動 review 確認：

- LM-3237 完整顯示器 proxy 與 LI-IMX477 camera 包絡位於 head envelope 內。
- Panel/touch proxy、camera 與 stand benchmark 均保留來源料號、URL 與分類。
- Camera 140° HFOV 位於 134°～140° 概念允收範圍。
- VESA 200 × 200 mm 可同時對應 LM-3237 proxy 與 Ergotron HX benchmark。
- Review 狀態為 `PassWithOpenRisks`，不是無條件通過。

這些檢查只證明概念空間配置一致，不等同於光學、結構、熱、聲學、法規或量產驗證。

## 已知假設與限制

- Head envelope、privacy shutter、custom stand/base 與多數內部硬體仍為 Assumed。
- LM-3237 是完整商用 display review proxy，不是 bare panel/touch stack。
- LI-IMX477 尚未包含 ISP、carrier、connector、線材與 shutter。
- FOV 目前是概念包絡，尚未完成真實光線淨空分析。
- 尚未驗證 shutter 運動、connector mating、cable bend radius 與 service access。
- 5.1 kg stand 載重餘量尚未計入完整 AV／compute／thermal／結構重量。
- 重心、結構強度、傾倒穩定性與 thermal performance 尚未完成實測或高擬真分析。
- 已建立概念審查用 STEP；尚未建立正式 release／製造 STEP deliverable。

## Next Action：Calm Crown Iteration 03

1. 重跑 Task 2 規格與品質雙重審核；確認受控參數引用與 temporary FCStd 測試品質 gate 放行後才進入 Task 3。
2. Task 3 建立 rear pillow、260 × 220 mm service cover、vent、I/O recess 與全部 internal space claims。
3. Task 4 建立 stand、420 × 285 × 68 mm base、120 mm travel 與 −5°／0°／+20° motion states。
4. 完成 machine review、碰撞／評分、出版級渲染、產品 STP 交叉驗證與五領域 Agent Team 最終審核。

目前尚未輸出可交付的 Iteration 03 STP 或出版級渲染；Iteration 02 STEP 只供舊 proxy 概念審查。

## Git 與資料注意事項

- 此資料夾位於共用 `Logi-AI` repository；提交時只 stage 本專案相關檔案。
- CAD 備份檔（`*.FCBak`）與預覽 PNG 目前未納入 Git，提交前應先確認是否需要保留。
- 不要把 API key、token、密碼或未授權的供應商機密資料加入 repository。
- 固定規則放在 repository 的 `AGENTS.md`；快速變動的進度記錄放在 Obsidian 工作筆記。
