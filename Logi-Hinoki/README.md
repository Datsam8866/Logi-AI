# Hinoki FLOEFD Thermal CAD

這是 Hinoki 32-inch 視訊協作系統的概念級 FLOEFD conjugate heat-transfer (CHT) handoff，不是量產設計、製造幾何或溫度性能承諾。

## LOD 3 inferred engineering prototype

LOD 3 master 正在 `cad/lod3-inferred-prototype-01/` 建立。Task 7 臨時 head-only build 包含 742 × 492 × 62 mm 頭部、五層 display stack、front/rear housing、metal mid-frame、實體上下 rear vent slots、ribs、bosses、fasteners、五張主要 PCB、shields/connectors、10 個總計 57 W heat sources、QC7790 到 rear hatch 的被動 thermal path，以及 Task 5 的 camera、lighting、sensor、audio、microphone 與六個 rear I/O connector proxies。

Task 7 head-only validation 使用臨時 build（97 個 semantic parts、79 個 physical collision parts），temporary validation：Pass。每一組 unique physical pair 的碰撞門檻為 0.01 mm³；僅允許 3 組 camera/front-light 與對應 heat source contacts，其餘 3,078 組均已檢查通過。獨立執行 `python -B -m unittest tests.test_hinoki_lod3_inferred -v`：28/28 通過（126.901 s，exit code 0）。正式 LOD 3 FCStd 仍是先前的 62-part checkpoint，待 Task 8 atomic publication 才更新，不代表臨時驗證模型已正式交付。

Next Action：Task 8 atomic publication。Task 6 stand/base、physical cable routes / bend validation、full-product STEP、review images 與 FLOEFD derivative 均 deferred；下列既有 thermal CHT handoff 不受影響。

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
