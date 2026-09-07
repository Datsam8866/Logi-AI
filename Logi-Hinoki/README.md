# Hinoki LOD 3 Inferred Engineering Prototype

Hinoki 是一套 32-inch All-in-One Video Conferencing System 的概念機構與熱管理專案。本 repository 提供的是 **LOD 3 inferred engineering prototype**，不是 release geometry、量產設計、tooling 授權或熱性能保證。所有幾何、材料、熱負載、支架姿態皆由受控參數推導，非供應商實體零件。

> 本交付不得用於 tooling、GD&T、supplier release、certification 或 production temperature claim。

## 工作筆記與規則

- 固定規則：本目錄 `AGENTS.md`
- 詳細進度與交接記錄：[Logi-Hinoki工作筆記](<G:/其他電腦/我的電腦/Obsidian Vault/Logitech/Logi-Hinoki工作筆記.md>)
- 設計 spec 與計畫：`docs/superpowers/plans/`、`docs/superpowers/specs/`

## 正式交付檔案

### LOD 3 head + stand master

| 檔案 | 說明 |
|---|---|
| `cad/lod3-inferred-prototype-01/Hinoki_LOD3_Inferred_Master.FCStd` | 唯一正式 FreeCAD master（112 semantic / 91 physical parts、head + stand + kinematic contract） |
| `cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py` | 從參數重建 master 的 headless 建模腳本 |
| `cad/lod3-inferred-prototype-01/review_hinoki_lod3.py` | 16 個 hard-gate 幾何/metadata 驗證 |
| `cad/lod3-inferred-prototype-01/export_hinoki_lod3.py` | STEP + Manifest.json + Validation.json 原子匯出 |
| `cad/lod3-inferred-prototype-01/preview_hinoki_lod3.py` | 5 張 1600×1200 review PNG（Front / Rear / Iso / Exploded / AirflowCutaway） |
| `cad/lod3-inferred-prototype-01/emit_section_evidence.py` | 8 張 canonical cross-section SVG + JSON |
| `cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py` | 所有幾何、熱負載、metadata schema 的單一來源；含 `PROTOTYPE_LIMITATION` |

### FLOEFD conjugate heat-transfer handoff

| 檔案 | 說明 |
|---|---|
| `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Model.FCStd` | 原生 FreeCAD CHT 模型 |
| `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Solids.step` | 16 個受控實體 body 的 STEP handoff |
| `cad/thermal-simulation-01/Hinoki_Thermal_Internal_Air.step` | 一個連通 internal-air body 的 STEP handoff |
| `cad/thermal-simulation-01/Hinoki_Thermal_FLOEFD_Setup.json` | FLOEFD material/heat-load setup map |
| `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Review.json` | 最低幾何與 metadata hard-gate evidence |

概念熱輸入：35 °C ambient、57 W 總發熱、natural convection、no fan。材料意圖、13 個 heat source 與 rear vents 皆由 `hinoki_lod3_parameters.py` 生成。

## LOD 3 master 幾何與品質基線

- Head-only bbox：742 × 492 × 62 mm
- Head + stand overall：depth ≤ 280 mm（含 base）
- Semantic parts：112 個，命名唯一
- Physical STEP bodies：91 個
- Heat sources：13 個，budget 守恆 57 W（Panel_Module = BLU_LED 16 W + BLU_Driver 2 W + TCON 1.5 W + Panel_Gate_Source 0.5 W = 20 W）
- Authorized contact matrix：20 對，全部幾何重疊 > 0.01 mm³
- Forbidden overlaps：0
- `ManufacturingAuthority`：全部 False
- 16 個 hard gates 全通過（含 enclosure mating、rib host attachment、fastener engagement、heat-source uniqueness、stand envelope、stand kinematics contract）
- 完整測試套件：`python -B -m unittest tests.test_hinoki_lod3_inferred -v`

## 環境需求

- Windows PowerShell
- FreeCAD 1.1，需可執行 `freecadcmd.exe`（預設路徑 `C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe`）
- 若安裝位置不同：

```powershell
$env:FREECAD_CMD = "C:\path\to\FreeCAD\bin\freecadcmd.exe"
```

## Build、review、export、preview

所有 FreeCAD 腳本以同一 compile launcher 於專案根目錄執行；`$script` 換成對應腳本即可：

```powershell
$script = (Resolve-Path .\cad\lod3-inferred-prototype-01\build_hinoki_lod3_master.py).Path
$source = Get-Content -Raw $script
$launcher = "source = " + ($source | ConvertTo-Json -Compress) + "; exec(compile(source, " + ($script | ConvertTo-Json -Compress) + ", 'exec'))"
$launcher | & $env:FREECAD_CMD -c
```

sentinel：`HINOKI_LOD3_BUILD_OK`（build）、`HINOKI_LOD3_REVIEW_OK`（review）、`HINOKI_LOD3_EXPORT_OK`（export）、`HINOKI_LOD3_PREVIEW_OK`（preview）、`HINOKI_LOD3_SECTIONS_OK`（section evidence）。

匯出時可設定：

```powershell
$env:HINOKI_LOD3_MODEL_PATH = (Resolve-Path .\cad\lod3-inferred-prototype-01\Hinoki_LOD3_Inferred_Master.FCStd).Path
$env:HINOKI_LOD3_EXPORT_DIR = "C:\temp\hinoki-lod3-export"
```

Exporter 未指定輸出資料夾時會失敗，不覆蓋正式產物。成功後產生 `Hinoki_LOD3_Head.step` + `Hinoki_LOD3_Part_Manifest.json` + `Hinoki_LOD3_Validation.json`。

## 測試

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred -v
```

主要測試類別：

- `TestSemanticContract`：112/91/13 契約
- `TestHardGates`：16 個 hard gates
- `TestAtomicExport`：STEP + JSON 原子匯出與 rollback
- `TestReviewImages`：5 張 PNG 尺寸/白底/edge stroke
- `TestSectionEvidence`：8 張 SVG + JSON
- `TestStandKinematics`：STAND 契約與 head↔stand 分離
- `TestFormalArtifactRelease`：正式 FCStd 存在、獨立 reopen 通過、無 ManufacturingAuthority、`PROTOTYPE_LIMITATION` 保留

FLOEFD 迴歸：

```powershell
python -B -m unittest tests.test_hinoki_thermal_cht -v
```

## Simcenter FLOEFD 匯入步驟

1. 在 FLOEFD 建立新的 CHT project，單位 mm / W / degC。
2. 匯入 `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Solids.step` 與 `Hinoki_Thermal_Internal_Air.step`，確認 solids 與 air 為分離 region。
3. 依 `Hinoki_Thermal_FLOEFD_Setup.json` 對每個 solid 指派 material intent 與對應 heat source（總計 57 W）。
4. 建立 case：35 °C ambient、natural convection、gravity `(0, -9810, 0) mm/s²`；rear vent 開口為兩個 400 × 15 mm 參考。
5. 在 FLOEFD 內另外設定 surface radiation / emissivity、external computational domain、pressure boundaries 與 result limits——本 handoff 未內含這些設定。

任何求解結果僅供概念比較，不得作為量產熱性能承諾。

## Source hierarchy

Metadata 對每個 semantic part 記錄下列欄位，可由 `Hinoki_LOD3_Part_Manifest.json` 查詢：

- `SourceClass`：`ExternalReference` / `VendorDatasheet` / `EngineeringAssumption` / `ProxyGeometry`
- `SourceReference`：文件、URL、datasheet 版本或 assumption id
- `ExternalSourceStatus`：`Verified` / `Unverified` / `NotApplicable`
- `ExternalStandardID`：VESA MIS-D 100、LI-IMX477-MIPI-140H、ISO 4762 等
- `Confidence`：`High` / `Medium` / `Low`
- `ThermalDisposition`：`Keep` / `Aggregate` / `Suppress`
- `ThermalConductivityWmK`：material intent 熱傳導係數
- `ManufacturingAuthority`：一律 `False`
- `Revision`：語意零件版本

任何被標為 `EngineeringAssumption` 或 `ProxyGeometry` 的零件在採 tooling 或量產前，必須以 vendor datasheet 或量測 STEP 取代。

## 專案結構

```text
Logi-Hinoki/
├─ cad/lod3-inferred-prototype-01/   # LOD 3 head + stand 正式 master 與工具鏈
├─ cad/thermal-simulation-01/        # FLOEFD CHT handoff（16 solids + 1 air）
├─ cad/iteration-01/                 # 舊 Iteration 01 概念模型（保留供比對，非本交付）
├─ docs/reviews/                     # Review 記錄
├─ docs/superpowers/                 # Spec 與執行計畫
├─ tests/                            # LOD 3 + thermal acceptance tests
├─ AGENTS.md                         # 固定作業規則
└─ README.md                         # 本檔
```

## 範圍與非釋出限制

- 這一版明確是 **LOD 3 inferred engineering prototype; not manufacturing release**，不可用於 tooling、GD&T、supplier release、certification 或 production temperature claim。
- 幾何是受控概念 proxy，並非最終量產外觀、供應商實體零件、散熱器細節或完整 electronics stack。
- Panel 拆分（BLU_LED / BLU_Driver / TCON / Panel_Gate_Source）為工程假設，非 Dixie-derived。
- Stand kinematics 契約由參數凍結；8-posture 完整幾何碰撞驗證 deferred（需 Assembly4）。
- 目前 review 僅記錄最低幾何 hard gates，不代表 CFD 收斂、熱像量測、EMC、聲學、法規或可靠度驗證。
- 舊 Iteration 01/02 appearance / stand / render 不作為本交付依據。
- Task 6 stand/base 於 iter 8 完成 Ateam 重做（column-integrated yoke + visible trunnion + D80 column + 280 mm base）；獨立 Ateam Round 2 驗收 99/100。
- Head 品質改善 iter1→iter4：獨立最終複審 98/100，Q-01（enclosure gap）/ Q-02（panel detail）/ Q-03（rib host）三大缺陷 CLOSED。

## 已知假設清單

- A-013 至 A-040 仍標示為 Assumed，未由實體零件資料取代。
- Panel、camera、speaker、PCB、heatsink 為 proxy geometry；VESA MIS-D 100 為外部標準參照。
- Mass、centre of gravity、tipping stability 未做高擬真分析。
- Connector mating、cable bend radius、service access 未完整驗證。

## Git 與資料

- 本資料夾位於共用 `Logi-AI` repository；提交時只 stage 本專案相關檔案。
- CAD 備份檔（`*.FCBak`）與臨時 preview PNG 未納入 Git。
- 不得將 API key、token、密碼或未授權供應商機密資料加入 repository。
