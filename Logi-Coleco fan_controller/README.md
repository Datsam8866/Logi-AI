# Logi-Coleco fan_controller — QCS8550 Android 17 風扇控制器

**最後更新：2026-08-25（首次提交上線，commit `90c09d9`）**

---

## 專案概覽

QCS8550 (Coleco) Android 17 會議系統的風扇控制器參考實作。C++17 vendor native daemon，硬體存取隔離在 `HardwareInterface` 之後，`FanController` 只負責熱控策略。

| 項目 | 狀態 |
|------|------|
| 熱控策略核心 (`FanController`) | ✅ 完成參考實作 |
| 硬體抽象層 (`HardwareInterface`) | ✅ 介面完成 |
| QCS8550 硬體後端 (`Qcs8550Hardware`) | ⚠️ Demo stub，待 BSP 團隊實作 |
| `config/fan_config.json` 熱載入 | ❌ 尚未接線（目前使用 `FanConfig` 預設值） |
| 單元測試 | ❌ 未建立 |
| CI / Soong 建置驗證 | ❌ 未驗證 |

---

## 最新進度

### 2026-08-25：首次提交上線

- 將本專案首次納入 `Datsam8866/Logi-AI` git 追蹤，commit `90c09d9`（7 檔案、+945 行）
- 已推送至 GitHub `master`

### 2026-08-24：專案初始化

- 建立本專案 `CLAUDE.md`（父專案規範 + 本工具專屬架構說明）
- 重寫 `README.md`，加入「最新進度 / Next Action / 主要檔案」等標準區塊
- 建立 Obsidian 工作筆記 `Logi-Coleco fan_controller工作筆記.md`
- 盤點現有原始碼：`Android.bp`、`include/fan_controller.h`、`src/main.cpp`、`src/fan_controller.cpp`、`config/fan_config.json`

---

## Next Action

| 優先 | 項目 | 狀態 |
|------|------|------|
| A | 讓 `main.cpp` 讀取 `config/fan_config.json` 而非寫死 `FanConfig`（`nlohmann/json` 或簡易 parser） | 待辦 |
| A | 補加最高 CPU 溫度保護點（warning / critical / max RPM clamp / fan-stall failsafe） | 待辦 |
| B | 建立 `FanController` 單元測試：曲線內插、遲滯、斜率限制、failsafe 觸發 | 待辦 |
| B | 建立 RPM → 初始 duty 校準表（取代目前的 KP=0.00020 純 PI 控制） | 待辦 |
| C | 將 `Qcs8550Hardware` 替換為 Thundercomm/QCS8550 實際 I2C / ADC / PWM / FG / pinmux 實作 | 待 BSP |
| C | 驗證 Soong 建置（`mm` in Android tree）與 vendor partition 安裝 | 待辦 |

---

## 主要檔案

| 路徑 | 說明 |
|------|------|
| `Android.bp` | Soong `cc_binary` 建置：`qcs8550_fan_controller`，vendor: true，C++17 |
| `include/fan_controller.h` | 公開 API：`FanController`、`HardwareInterface`、`FanConfig`、`TemperatureFilter`、`MedianFilter` |
| `src/fan_controller.cpp` | 熱控策略：雙曲線內插、10 s 平均、遲滯、斜率限制、fan-start 偵測、failsafe |
| `src/main.cpp` | Daemon entry point；`Qcs8550Hardware` 為 demo stub（TMP75B/thermistor/PWM/FG/I2C recovery 皆 TODO） |
| `config/fan_config.json` | 熱控參數 (ambient / curves / control / fan_start / sensor_protection / i2c / fg)；**目前尚未被 code 讀取** |

---

## 控制流程摘要

每 500 ms：

```
TMP75B  -> validate -> 10 s 平均 -> T_AMB
Thermistor -> validate -> 10 s 平均 -> T_CPU
FG      -> median filter -> actual RPM

T_CPU 對 Curve_T_CPU_L_Amb / Curve_T_CPU_H_Amb 分別內插
兩結果依 T_AMB 線性內插 → requested_rpm

requested_rpm → clamp → 遲滯 → 100 RPM/s 斜率限制 → target_rpm
target_rpm + actual_rpm → fan-start 偵測 → PI 校正 → PWM duty
```

## Failsafe 規則

- TMP75B 通訊失敗 → **立即 100% PWM**
- TMP75B 連續 5 次失敗 → 呼叫 `resetTmp75bI2cBus()`（9-clock SCL release）
- CPU thermistor 失敗 / 溫度超出 [-40, 125] °C / 500 ms 內跳變 >10 °C → **100% PWM**

## 已知風險（來自原設計 review）

- 目前曲線在 T_CPU > 46 °C 會線性外推，僅由 `max_rpm` 硬性夾住 → 需補明確的 warning / critical 溫度點與行為
- Duty ↔ RPM 沒有普遍關係 → 目前是 KP=0.00020 純 PI，量產應改成校準表 + FG 修正
- 硬體 API（Qualcomm/Thundercomm pinmux、PWM 頻率、FG GPIO、ADC/IIO channel、I2C bus/addr）皆為 TODO，`Qcs8550Hardware` 只是回傳固定值的 demo

---

## 注意事項

- 依 Android 17 vendor HAL 邊界原則：Java/Kotlin **不可**直接碰硬體節點，一律經此 daemon（或未來改成 AIDL vendor service）
- I2C recovery 必須以 **open-drain GPIO bit-bang**，不可 push-pull 驅動高電平（會反灌損壞週邊）
- 修改熱控演算法時只動 `FanController`；硬體綁定改動只動 `HardwareInterface` 的實作
- 收工同步儀式與 commit 規範沿用父專案 `../CLAUDE.md`
