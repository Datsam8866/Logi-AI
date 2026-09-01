# Logi-Hinoki

Hinoki 是一套 32-inch All-in-One Video Conferencing System 的概念機構與空間配置專案。目前進度為 **Concept CAD Iteration 01**：以 FreeCAD 建立可重建的參數化概念裝配，用來追蹤產品包絡、顯示器、AV 元件、支架姿態與內部硬體空間聲明。

> Iteration 01 是概念驗證模型，不是 release geometry，也不代表量產設計已完成。

## 目前狀態

- 最新階段：Concept CAD Iteration 01
- CAD review：Pass
- 顯示頭包絡：760 × 80 × 540 mm
- 顯示器：32-inch 4K panel 概念包絡
- Camera horizontal FOV：137° nominal concept
- 支架姿態：low / neutral / high
- Display-bottom height：370 / 430 / 490 mm
- Tilt：−5° / 0° / +20°
- STEP：尚未匯出

Iteration 01 已包含 display、上方 AV bar、camera 與手動快門、speakers、microphones、radar、ambient light sensor、front lights、I/O、VESA、compute／thermal module、USB-C PD、base、height column，以及 cable／motion keep-out。

## 專案結構

```text
Logi-Hinoki/
├─ cad/iteration-01/        # FreeCAD 模型、建模／預覽／review 腳本與 JSON 結果
├─ docs/reviews/            # 架構映射、pre-CAD audit、checklist 與 CAD review
├─ docs/superpowers/        # 已核准的設計規格與執行計畫
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
python -m unittest tests.test_hinoki_iteration01 -v
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

## Review 通過範圍

目前自動 review 確認：

- 顯示頭內部硬體包絡位於 head envelope 內。
- 沒有偵測到非預期的硬體 bounding-box collision。
- Panel bezel 與 AV bar 幾何符合 Iteration 01 參數。
- Camera horizontal FOV 位於 134°～140° 的概念允收範圍。

這些檢查只證明概念空間配置一致，不等同於光學、結構、熱、聲學、法規或量產驗證。

## 已知假設與限制

- A-013 至 A-040 仍標示為 Assumed，需由實體零件資料取代。
- 尚未選定或導入完整 panel、camera、speaker、PCB、heatsink 與 stand 實體模型。
- FOV 目前是概念包絡，尚未完成真實光線淨空分析。
- 尚未驗證 shutter 運動、connector mating、cable bend radius 與 service access。
- 質量、重心、結構強度、傾倒穩定性與 thermal performance 尚未完成實測或高擬真分析。
- 尚未建立正式 STEP deliverable。

## Next Action：Iteration 02

1. 鎖定 panel、camera、speaker、PCB、heatsink 與 stand 候選零件。
2. 用供應商或量測所得的實體尺寸替換假設包絡。
3. 補做 FOV 光線淨空與 privacy shutter 運動驗證。
4. 檢查 connector insertion、cable routing、bend radius 與維修空間。
5. 建立真實質量與重心模型，確認 stand load 與 stability。
6. 加入 thermal architecture 與 vent／heatsink 空間驗證。
7. review 通過後再建立 STEP 匯出與交付規則。

## Git 與資料注意事項

- 此資料夾位於共用 `Logi-AI` repository；提交時只 stage 本專案相關檔案。
- CAD 備份檔（`*.FCBak`）與預覽 PNG 目前未納入 Git，提交前應先確認是否需要保留。
- 不要把 API key、token、密碼或未授權的供應商機密資料加入 repository。
- 固定規則放在 repository 的 `AGENTS.md`；快速變動的進度記錄放在 Obsidian 工作筆記。
