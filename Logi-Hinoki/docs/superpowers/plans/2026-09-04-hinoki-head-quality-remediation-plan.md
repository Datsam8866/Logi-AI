# Hinoki Head 品質改善與多 Agent 審查計畫草案

日期：2026-09-04。狀態：依使用者三項缺陷回饋建立，設計選擇尚待確認；未開始 CAD 修改。

## 1. 目標與基準

- 對目前 head-only 工程原型修正前後殼間隙、panel 細節／熱源及不可裝配的 inner ribs。
- Task 8 匯出能力已完成；其 34/34 測試不代表機構可裝配或產品品質達 95 分。
- 基準：branch `codex/hinoki-lod3-task7`，HEAD `46b50e6`，加本次尚未提交的 Task 8 exporter/tests/README。
- 實際基準模型：`C:/Users/skuan1/.codex/visualizations/2026/09/03/01a0690e-862b-7c00-b5c3-80b9117a174f/task8-review/Hinoki_LOD3_Inferred_Master.FCStd`。
- 維持 742 × 492 × 62 mm head、head-only 與 inferred prototype 限制；stand/base、實體整機 cable routing 及自動 FLOEFD 衍生包不在本輪。
- 新增必要的接合剖面、局部裝配圖、爆炸圖及每輪前後比較，用作審查證據。

## 2. 已確認缺陷（唯讀 native CAD 量測）

| ID | 使用者回饋 | 2026-09-04 基準證據 | 必須新增的 gate |
|---|---|---|---|
| Q-01 | FRONT PANEL 與 BACK COVER 存在間隙 | Front_Frame z=0–3.2 mm；Rear_Enclosure z=19–62 mm；兩者最小距離 15.8 mm | 周邊接合剖面、封閉／搭接、受控設計縫與公差 |
| Q-02 | PANEL 缺乏 backlight／driver IC 細節 | BLU 是 716×406×12 mm 單一實體；20 W 全掛在 BLU；TCON 僅推定 PCB | 可追溯的 display 結構及逐熱源功率／接觸對應 |
| Q-03 | INNER RIB 位置形狀不可組裝 | 六條 rib 都在 z=32–54 mm，距 rear shell 5.2 mm、距 mid-frame 約16.553 mm | 母體連接、結構支撐關係、裝配／拆卸路徑 |

量測針對目前提供的 native review model，不是從截圖像素估算。Q-01 的距離描述前框與後殼，不把所有 panel/cover 界面混成同一條接縫。

## 3. 建議設計方向

### 3.1 前後殼接合

- 先定義 front assembly、glass、rear shell 與可拆 I/O cover 各自邊界。
- 建議保留 front assembly 為定位基準，建立連續側壁與 rear cover 的受控搭接／定位結構；後蓋沿後方裝入／拆出。
- 比較台階搭接與止口方案，依空間、固定及拆卸需求選定；接縫值、搭接深度與公差由剖面和來源資料決定，不直接把所有配合設為零間隙。
- 先檢視四邊及四角的剖面，確認沒有未設計的外殼開口。保留明確指定的 vent、I/O、camera、speaker 等功能開口。
- 相鄰 solids 接觸與母體融合要分清楚；不能單靠放大部件並增加「允許碰撞」項目消除視覺縫隙。

### 3.2 Panel 結構與熱源

- 先盤點既有 Hinoki panel/power 表與 Dixie panel/2D/3D；Dixie 在原始工作桌，不能假定有效 worktree 有完整參考檔。
- 保留既有 cover glass／PCAP／optical bond／LCD，將 BLU 細化成有依據的背板、反射／導光／光學層、LED 安裝基板與必要散熱接觸。
- 先確認 edge-lit 或 direct-lit 架構；沒有料號資料時選一個明示為推定的方案，不混用兩種架構的零件。
- 區分 backlight driver、T-CON IC、source/gate driver。零件若整合在同一模組或為 COF/COG，依來源反映，不能為湊細節虛構獨立 PCB。
- 每個熱源記錄 HeatSourceID、BudgetGroup、實際掛載零件、位置、功率來源／狀態及導熱接口；同一功率只計一次。
- 先核對既有 `Heat_Panel_Backlight=20 W` 的功率邊界。若包含 driver/TCON，按有依據的分配拆成 child sources；若不包含，列新增功率與57 W總預算變更供確認。
- 不為保住57 W而任意降低LED／backlight功率；缺少分配數據時明示未定量，不以零瓦或任意比例冒充驗證。

### 3.3 Rib／boss 與裝配

- 先定義部件歸屬、裝配順序、進出方向、定位面、鎖附點及工具通道，再重建 rib。
- 後蓋成型 rib 應與後蓋形成連續母體；若是獨立支撐件，必須有實際固定／承載方式。
- 不保留六條固定位置長牆再逐塊挖避空的做法；根據支撐位置、零件安裝與後蓋拆卸路徑決定短 rib、局部筋或支撐結構。
- Rib 不得懸空、只作點／線連接，或切割後殘留無固定的碎片；不得阻擋板件、panel、後蓋及必要工具的裝入／拆卸。
- 連帶核對角落boss固定與VESA承壓／夾持路徑：原角落boss z=27–57 mm，rear內表面z=59.2 mm；現有簡化螺絲未表達螺頭承壓與完整夾持堆疊。
- 先用既有1.7 mm名義厚度作起點；根部、圓角、高度、拔模與成型方向需有來源或明示工程假設，不能據此宣稱量產DFM驗證。
- 移動主要PCB或改變既有熱路若無法避免，先提出具體干涉證據及影響，不受舊「位置永不變」規則強迫產生不可裝配結構。

## 4. 實作順序與驗收

1. 凍結基準與缺陷紀錄 → 驗證：原始FCStd／STEP保留、每個缺陷有零件、視圖、量測及來源。
2. 提交接合剖面／裝配順序方案 → 驗證：母體、固定點、配合及拆卸方向清楚，使用者確認方向。
3. 建立會失敗的接合／支撐／裝配測試 → 驗證：目前15.8 mm縫隙、懸空rib與裝入受阻案例確實被拒絕。
4. 重建外殼接合與rib／boss → 驗證：局部及整體幾何有效，必要支撐連續，裝配掃掠／工具通道無未授權干涉。
5. 細化panel與熱源 → 驗證：零件來源、heat mapping、功率邊界、溫度分析所需接觸均可追溯。
6. 更新實體／特徵／預算對應 → 驗證：模型manifest與STEP逐件一致，來源熱功率僅計一次，無漏件與重複實體。
7. 重建FCStd、STEP、JSON及審查視圖 → 驗證：Task8匯出與rollback仍通過，正式產物維持不變。
8. 進行多Agent評分與缺陷回圈 → 驗證：同版本證據、逐項扣分、修正前後對照及獨立最終複審。

## 5. 驗證規則必須一起改

- 保留不同實體間的未授權干涉檢查，增加「必須連接」「必須可裝入／拆出」的正向條件。
- 成型rib／boss若融入母體，改為母體上的可追溯feature；STEP不得同時匯出整體母體和重複的rib volume。
- 更新固定97 semantic／79 physical與十個heat-source斷言，依核准新manifest及budget對應精確檢查；不能刪掉斷言後無替代驗證。
- 80–120零件數是舊模型規劃範圍，不是品質證據；若合理架構改變數量，先修訂契約並保留追溯，不能拆假零件湊數。
- 熱源可以從budget group細化成多個實際source；總功率採有依據的新預算，不將「數量仍為十」作為正確性的替代指標。
- 必須有負向案例：平移rib產生浮空、keepout切出孤島、移除支撐接點、螺絲未穿夾持件、終態無干涉但裝入中途撞rib。若路徑採離散採樣，記錄步距與漏檢控制，不把少數姿態檢查宣稱為連續路徑保證。
- 驗證涵蓋：殼體接合、part/feature ownership、結構連接、裝配／工具路徑、幾何有效性、干涉、熱源mapping與功率守恆、STEP往返。

## 6. Agent 分工與95分回圈（建議評分規則）

- Agent A：外觀／殼體接合與實際剖面。
- Agent B：機構／rib／固定／裝配路徑。
- Agent C：panel／功率來源／熱路／CAD交付證據。
- 主代理負責修改、測試、缺陷追蹤；最後由未參與修改的獨立Agent核對同一版成果。
- 維持最多三位並行審查者；獨立最終複審在完成修改後執行。

建議權重：外觀配置20、機構裝配30、零件與來源20、散熱配置20、CAD交付10，總計100。

每一評分項先固定滿分證據、扣分條件與權重；缺證據不可拿滿分。同一領域的審查分歧須以零件或量測裁決，不能直接平均消除阻擋缺陷。

每輪輸出：版本／artifact hashes、分項得分、未關閉缺陷、採納／退回理由、修正差異、驗證結果與下輪工作。

停止條件：加權≥95，每個領域≥90，Q-01／02／03全部通過，無Critical／Important，完整必要測試通過，獨立最終複審達標，使用者接受外觀／細節方向。

先安排三輪；若連續兩輪無實質進展，列明資料缺口或設計決策，再處理阻塞原因。不保證靠迭代必然達95，不降低標準或回填高分。

## 7. 預計涉及檔案

- `cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py`：接合、裝配、panel與功率契約。
- `cad/lod3-inferred-prototype-01/hinoki_lod3_display_housing.py`：殼體、panel、rib／boss。
- `cad/lod3-inferred-prototype-01/hinoki_lod3_electronics_thermal.py`：panel熱源及必要接觸。
- `cad/lod3-inferred-prototype-01/review_hinoki_lod3.py`：接合／支撐／裝配與功率驗證。
- `tests/test_hinoki_lod3_inferred.py`：新失敗案例及更新後manifest驗證。
- `cad/lod3-inferred-prototype-01/export_hinoki_lod3.py`：僅在母體feature／part對應需要時修改。
- `docs/reviews/`：版本缺陷、視圖索引與評分證據；`README.md`與Obsidian更新狀態。

這份文件是設計改善計畫草案，不是已完成的CAD修改或已取得的95分審查報告。

## 8. 本次獨立診斷採納與保留

- Panel Agent確認：已有BLU等效熱源與TCON板，缺分佈式LED／driver／TCON IC及來源對應；採納先區分不同driver、優先直接掛載熱源與避免重複計熱。
- Rib Agent確認：舊gate只有positive geometry與static overlap，缺host connection、clamping與assembly path；採納連接圖、幾何接觸證據及負向測試。
- 不採納「無條件把新增driver塞入20 W／57 W」：功率來源邊界未核對前，不能任意重分配或宣稱已包含。
- 目前確認rib未接到rear shell；尚未做全裝配路徑分析，不宣稱已證明所有可能組裝順序都不可行。
- 本次未改模型，未重跑既有34項測試，未進行數值品質評分；工作是native geometry唯讀診斷與改善計畫。
