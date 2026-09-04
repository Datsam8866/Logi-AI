# Hinoki FLOEFD Thermal CAD

這是 Hinoki 32-inch 視訊協作系統的概念級 FLOEFD conjugate heat-transfer (CHT) handoff，不是量產設計、製造幾何或溫度性能承諾。

## 工作筆記

固定規則見本目錄 `AGENTS.md`；詳細進度與交接記錄見 [Logi-Hinoki工作筆記](<G:/其他電腦/我的電腦/Obsidian Vault/Logitech/Logi-Hinoki工作筆記.md>)，不沿用 MEBudget 筆記。

2026-09-04 收工：Task 8 匯出能力完成；已記錄三項 CAD 品質缺陷與改善計畫，提供中英文 Claude 交接 prompt。使用者將交由 Claude 試作；本次尚未修改問題幾何或執行95分迴圈，九點排程維持停用。

## LOD 3 inferred engineering prototype

LOD 3 master 正在 `cad/lod3-inferred-prototype-01/` 建立。Task 7 臨時 head-only build 包含 742 × 492 × 62 mm 頭部、五層 display stack、front/rear housing、metal mid-frame、實體上下 rear vent slots、ribs、bosses、fasteners、五張主要 PCB、shields/connectors、10 個總計 57 W heat sources、QC7790 到 rear hatch 的被動 thermal path，以及 Task 5 的 camera、lighting、sensor、audio、microphone 與六個 rear I/O connector proxies。

Task 7 head-only validation 使用臨時 build（97 個 semantic parts、79 個 physical collision parts），temporary validation：Pass。每一組 unique physical pair 的碰撞門檻為 0.01 mm³；僅允許 3 組 camera/front-light 與對應 heat source contacts，其餘 3,078 組均已檢查通過。獨立執行 `python -B -m unittest tests.test_hinoki_lod3_inferred -v`：28/28 通過（126.901 s，exit code 0）。正式 LOD 3 FCStd 仍是先前的 62-part checkpoint，尚未更新；Task 8 建立並驗證 head-only STEP 匯出能力，原始計畫的整套正式交付列於 Task 11。

Next Action：先依 [Head品質改善計畫草案](docs/superpowers/plans/2026-09-04-hinoki-head-quality-remediation-plan.md) 解決使用者指出的前後殼間隙、panel熱源細節與rib裝配問題；Task 8測試通過不代表產品品質達標。先確認接合剖面／裝配方向與panel功率邊界，再修改CAD並進行多Agent評分回圈。正式替換範圍另確認；若省略 Task 9／10，先同步調整 Task 11 的發布依賴。Task 6 stand/base、physical cable routes / bend validation、full-product STEP、review images 與 FLOEFD derivative 均 deferred；下列既有 thermal CHT handoff 不受影響。

### Task 8 使用與驗證

- 匯出器：`cad/lod3-inferred-prototype-01/export_hinoki_lod3.py`，使用乾淨的 FreeCADCmd session。
- 讀入已通過 Task 7 的 master，STEP 匯出 79 個 physical semantic parts；manifest 保留全部 97 筆 metadata、原 label、stable name 與 exported 標記。Compound 保留為一個語意零件。
- 精確輸出：`Hinoki_LOD3_Head.step`、`Hinoki_LOD3_Part_Manifest.json`、`Hinoki_LOD3_Validation.json`；來源 FCStd 不改寫。
- 每件重讀核對 name、positive/valid solid、solid count、volume 與 bbox（0.1 mm）；兩份 JSON 重讀比對後才依序替換。
- 發生可處理例外時回復先前檔案；這不是跨檔案的斷電／process-crash transaction。若 rollback 本身遇持續 I/O 錯誤，保留 recovery backups 並回報失敗。
- 暫存 build/review 包：[task8-review](<C:/Users/skuan1/.codex/visualizations/2026/09/03/01a0690e-862b-7c00-b5c3-80b9117a174f/task8-review/>)，含 97-part FCStd 與三個匯出檔；不等於 repository 正式發布。
- 完整 `python -B -m unittest tests.test_hinoki_lod3_inferred -v`：34/34 通過（164.778 s，exit code 0）；Task 8 六項測試已確認 RED → GREEN。Python 語法與 `git diff --check` 通過。
- 獨立程式審查無 Critical/Important。既有同名 GUI document 可能使 wrapper 名稱加尾碼而被拒絕，請用乾淨 CLI session。

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestAtomicExport -v
```

手動產生另一份 review package 時，先指定 `HINOKI_LOD3_MODEL_OUT` 為暫存 FCStd 路徑，以本文下方 compile launcher 執行 `cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py`。再設定 `HINOKI_LOD3_MODEL_PATH` 指向該檔，以及 `HINOKI_LOD3_EXPORT_DIR` 為輸出資料夾，以相同 launcher 執行 `export_hinoki_lod3.py`。Exporter 未指定輸出資料夾時會失敗，不預設覆蓋正式產物；成功 sentinel 為 `HINOKI_LOD3_EXPORT_OK`。

這一版明確是 LOD 3 inferred engineering prototype; not manufacturing release，不可用於 tooling、GD&T、supplier release、certification 或 production temperature claim。

## FLOEFD handoff

下列五個檔案構成目前的最小 FLOEFD 匯入交付：

- `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Model.FCStd`：原生 FreeCAD CHT 模型。
- `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Solids.step`：16 個受控實體 body 的 STEP handoff。
- `cad/thermal-simulation-01/Hinoki_Thermal_Internal_Air.step`：一個連通 internal-air body 的 STEP handoff。
- `cad/thermal-simulation-01/Hinoki_Thermal_FLOEFD_Setup.json`：FLOEFD setup map。
- `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Review.json`：最低幾何與 metadata hard-gate evidence。

概念輸入為 35 °C ambient、57 W 總發熱與 natural convection；沒有 fan。材料意圖、十個 heat load 與兩個 400 × 15 mm rear vent opening 都由受控參數產生。

## Build、review、export、test

需要 Windows PowerShell、FreeCAD 1.1 的 `freecadcmd.exe`，以及 Python `unittest`。若安裝位置不同：

```powershell
$env:FREECAD_CMD = "C:\path\to\FreeCAD\bin\freecadcmd.exe"
```

建模、review、STEP export 都可由完整 thermal test 執行；測試一律寫到系統 temporary directory，不會覆寫正式 artifacts：

```powershell
python -B -m unittest tests.test_hinoki_thermal_cht -v
```

若要個別執行任一 FreeCAD script，請從專案根目錄使用同一 compile launcher（將 `$script` 改為 build、review 或 export script）：

```powershell
$script = (Resolve-Path .\cad\thermal-simulation-01\build_hinoki_thermal_cht.py).Path
$source = Get-Content -Raw $script
$launcher = "source = " + ($source | ConvertTo-Json -Compress) + "; exec(compile(source, " + ($script | ConvertTo-Json -Compress) + ", 'exec'))"
$launcher | & $env:FREECAD_CMD -c
```

正式 publication 前可明確指定輸出路徑；預設則寫入上述正式五個檔案。rebuild model 後，將 `$script` 改為 `export_hinoki_thermal_cht.py`，即可 atomic publish 兩個 STEP 檔。

## FLOEFD import

1. 在 FLOEFD 建立新的 CHT project，單位設為 mm、W、degC。
2. 匯入 `Hinoki_Thermal_CHT_Solids.step` 與 `Hinoki_Thermal_Internal_Air.step`，確認 solids 與 air 為分離 region。
3. 依 `Hinoki_Thermal_FLOEFD_Setup.json` 指派每個 solid 的 material intent 與十個 heat load，總計 57 W。
4. 以 35 °C ambient、natural convection 與 `(0, -9810, 0) mm/s²` gravity 建立 case；two rear vents 作為開口參考。

Surface radiation / emissivity、external computational domain、pressure boundaries，以及 result limits 都必須在 FLOEFD 內設定。目前沒有 production temperature limits；任何求解結果只可作概念比較，不能宣稱量產熱性能。

## 範圍與限制

- Current Task 7 head-only validation scope excludes physical cable routes and cable-bend validation. Connector cutouts/service clearances remain explicit and are validated through the rear service zone.
- Task 6 stand/base is deferred; this checkpoint must not be described as a full product assembly or full-product STP.
- 模型是受控概念 proxy，非製造 CAD、散熱器細節或完整 electronics stack。
- STEP export 會經 FreeCAD 重新匯入驗證：16 個語意 solids、1 個 air body 與 mm-scale bounding boxes。
- JSON review 記錄的是最低幾何 hard gates，不是 CFD convergence、熱像量測或可靠度驗證。
- 不使用舊 Iteration 01/02 的 appearance、stand、render 或 active Next Action 作為本交付依據。
