# Hinoki FLOEFD Thermal CAD

這是 Hinoki 32-inch 視訊協作系統的概念級 FLOEFD conjugate heat-transfer (CHT) handoff，不是量產設計、製造幾何或溫度性能承諾。

## 工作筆記

固定規則見本目錄 `AGENTS.md`；詳細進度與交接記錄見 [Logi-Hinoki工作筆記](<G:/其他電腦/我的電腦/Obsidian Vault/Logitech/Logi-Hinoki工作筆記.md>)，不沿用 MEBudget 筆記。

2026-09-04 更新：完成 Task 8 品質改善三輪迭代（Q-01 前後殼間隙、Q-02 panel 熱源細節、Q-03 rib 裝配）。獨立最終複審 93/100（未達 95 因缺 cross-section 影像）；三項使用者缺陷均以幾何與 metadata 證據解決；34/34 測試通過。

## LOD 3 inferred engineering prototype

LOD 3 master 位於 `cad/lod3-inferred-prototype-01/`。Task 8 品質改善後 head-only build：742 × 492 × 62 mm、96 semantic / 78 physical parts、13 個 heat sources 合計 57 W、Q-01/Q-02/Q-03 缺陷全解決。

**Q-01 前後殼間隙**：舊 15.8 mm 開放縫由 Metal_Mid_Frame 連續側壁（z=3.2..25）橋接；Rear_Enclosure 以 3 mm 台階搭接 mid-frame（lap 起點 z=22）。`enclosure_mating.remedied_gap_mm=0.0`；設計縫值 0.2 mm（前）與 0.3 mm（後）皆為明確 clearance。

**Q-02 Panel 細節**：舊單一 20 W Backlight_Unit 拆為 edge-lit stack — BLU_Optical_Films、Light_Guide_Plate、Panel_Backplate（含 LED_Bar cutout）、LED_Bar_Bottom（16 W）、TCON_IC（1.5 W）、BLU_Driver_PCB（2 W）、Panel_Gate_Source_Driver COF（0.5 W），Panel_Module = 20 W 守恆，總 57 W 不變。全部標為 EngineeringAssumption A-LOD3-PN-00[1-4]。

**Q-03 Rib/Boss 裝配**：6 個原懸空 rib 融入 Rear_Enclosure 為 fused features（RibFeatureCount=6, RibHostPart=Rear_Enclosure），4 corner bosses + 4 VESA bosses 各與 Metal_Mid_Frame 有 0.5 mm root engagement 並宣告為 authorized contact，8 顆 M3/M4 fastener 完整穿過 rear cover + 進入 boss tapped hole（M3 12 mm、M4 14 mm）。

**驗證**：14 個 hard gates 全通過（含新增 enclosure_mating_continuous、rib_host_attachment、fastener_engagement、unique_heat_source_mapping_and_budget、panel_module_budget_conserved）；19 個 authorized_contacts（3 AV + 8 boss root + 8 thermal path）幾何重疊全部 >0.01 mm³；2984 unauthorised pairs 全無碰撞。`python -B -m unittest tests.test_hinoki_lod3_inferred -v`：34/34 通過（≈240 s）。

**Review 檔位置**：`C:\Users\skuan1\.codex\visualizations\2026\09\04\task8-quality-remediation-iter3\`（FCStd + STEP + Manifest.json + Validation.json + logs）。iter1、iter2 保留為對比。

**獨立複審**：三代理平行審查（A/B/C 分工）+ 最終獨立複審（未參與實作）。iter1 綜合 73/100；iter2 綜合 80/100；iter3 綜合 **93/100**（A=17.5, B=28, C=19, D=19, E=9.5）。三大 Q-01/Q-02/Q-03 缺陷均已 CLOSED；未達 95 分的主因是 A 類別缺 rendered cross-section 影像（cap 92%），其餘為 minor：ExternalStandardID 未逐件填、ThermalConductivityWmK 未進 METADATA_KEYS 而未進 manifest JSON、assembly sequence tool-access 未完全記錄。

Next Action：若要達 95+ 需補 cross-section 影像（FreeCAD Draft.makeShapeString 或 GUI 匯出 8 張 PNG）、將 ThermalConductivityWmK 加入 METADATA_KEYS、補 ExternalStandardID。使用者可決定是否進一步 iter 4 或以 iter3 作為 LOD 3 交付基線。正式 62-part FCStd 尚未替換，iter3 review 檔留在本機；stand/base、full-product STEP、FLOEFD derivative 均 deferred。

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
