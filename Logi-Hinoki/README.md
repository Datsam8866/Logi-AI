# Logi-Hinoki

Hinoki 是一套 32-inch All-in-One Video Conferencing System 的概念機構與空間配置專案。目前已建立 **Concept CAD Iteration 02 Preliminary Review Baseline**：以可追溯市場候選取代部分 Iteration 01 假設，用來 review panel/touch、camera/shutter 與 stand/VESA 的初步包絡。

> Iteration 02 仍是概念 review 模型，不是 release geometry，也不代表量產設計已完成。

## 目前狀態

- 最新階段：Concept CAD Iteration 02 Preliminary Review Baseline
- CAD review：PassWithOpenRisks
- 顯示頭包絡：760 × 80 × 540 mm
- 顯示器 review proxy：One World Touch LM-3237-26B-4K，750.4 × 452.7 × 56.5 mm
- Camera baseline：Leopard Imaging LI-IMX477-MIPI-140H，140° HFOV
- Stand benchmark：Ergotron HX 45-475-224；VESA 200 × 200 mm
- 支架姿態：low / neutral / high
- Display-bottom height：370 / 430 / 490 mm
- Tilt：−5° / 0° / +20°
- STEP：尚未匯出

Iteration 02 preliminary review 顯示：display proxy 位於 head envelope 內，但左右各只剩 4.8 mm；上方 AV reserve 為 87.3 mm，深度 reserve 為 23.5 mm。Ergotron HX 對 14 kg display proxy 的理論剩餘載重為 5.1 kg，尚未計入 Hinoki AV、compute、thermal、cable 與結構重量。

## 專案結構

```text
Logi-Hinoki/
├─ cad/iteration-01/        # FreeCAD 模型、建模／預覽／review 腳本與 JSON 結果
├─ cad/iteration-02/        # 初步市場包絡 review CAD、預覽與 JSON 結果
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
| `cad/iteration-02/Hinoki_Iteration02_CAD_Review.json` | Iteration 02 自動 review 結果 |
| `tests/test_hinoki_iteration02.py` | Iteration 02 acceptance checks |
| `docs/reviews/2026-09-01-hinoki-iteration02-preliminary-review.md` | Iteration 02 初步 review 摘要 |
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
- 尚未建立正式 STEP deliverable。

## Next Action：Iteration 02 Review 02

1. 取得 bare 32-inch 4K panel、touch sensor、cover lens 與 controller 的可驗證 drawing，取代完整 display proxy。
2. 選定或設計 captive privacy shutter，補做 travel、retention 與 optical obscuration review。
3. 建立 Hinoki custom stand/base 的 load path、質量／重心、cable motion 與 tip-stability 模型。
4. 加入 camera ISP/carrier、connector insertion、thermal 與 cable bend keep-out。
5. 上述風險關閉或正式接受前，維持 STEP export blocked。

## Git 與資料注意事項

- 此資料夾位於共用 `Logi-AI` repository；提交時只 stage 本專案相關檔案。
- CAD 備份檔（`*.FCBak`）與預覽 PNG 目前未納入 Git，提交前應先確認是否需要保留。
- 不要把 API key、token、密碼或未授權的供應商機密資料加入 repository。
- 固定規則放在 repository 的 `AGENTS.md`；快速變動的進度記錄放在 Obsidian 工作筆記。
