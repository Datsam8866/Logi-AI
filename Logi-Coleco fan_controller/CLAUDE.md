# Logi-Coleco fan_controller — 專案指令

> 承接父專案 `../CLAUDE.md` 的規範（開工/收工/工作模式），本檔僅補充本工具的專案特定規則。

## 專案概覽

QCS8550 (Coleco 平台) Android 17 會議系統的風扇控制器參考實作。以 **C++17 vendor native daemon** 形式運行，將硬體存取隔離在 `HardwareInterface` 抽象後方；`FanController` 只負責熱控策略（雙曲線內插、10 s 平均、遲滯、100 RPM/s 斜率限制、fan-start 保護、TMP75B/thermistor failsafe → 100% PWM、I2C 9-clock recovery）。

## 資料來源與 Input

| 來源 | 說明 |
|------|------|
| TMP75B (I2C) | 環境溫度 T_AMB |
| 板上 thermistor (ADC/IIO) | CPU 附近溫度 T_CPU |
| Fan FG / tachometer | 實際 RPM |
| `config/fan_config.json` | 熱控參數（曲線、遲滯、斜率、failsafe 閾值） |

## 工具架構

| 檔案 | 說明 |
|------|------|
| `include/fan_controller.h` | `FanController`、`HardwareInterface`、`FanConfig`、`TemperatureFilter`、`MedianFilter` 宣告 |
| `src/fan_controller.cpp` | 熱控策略核心：讀感測 → 驗證 → 平均 → 雙曲線內插 → 遲滯 → 斜率限制 → 啟動偵測 → 閉迴路 PWM |
| `src/main.cpp` | Daemon entry point + `Qcs8550Hardware` demo stub（TMP75B/thermistor/PWM/FG/I2C recovery 皆為 TODO） |
| `config/fan_config.json` | 熱控參數（純參考，實作目前直接使用 `FanConfig` 預設值） |
| `Android.bp` | Soong 建置：`cc_binary` `qcs8550_fan_controller`，vendor partition，`-Wall -Wextra -Werror -std=c++17` |

## 開發原則（本專案專屬）

- **不要直接改 `FanController` 的演算法**，除非熱控策略本身改變；硬體綁定改動只放在 `HardwareInterface` 的實作。
- `Qcs8550Hardware` 目前是 demo stub（回傳固定值），所有 TMP75B/ADC/PWM/FG/pinmux/I2C GPIO recovery 都標記為 TODO，量產前必須由 BSP 團隊填入。
- `config/fan_config.json` 目前**沒有**被 code 讀取（`main.cpp` 直接寫死 `FanConfig`）— 若之後需要熱插拔調參，要補上 JSON 載入。
- I2C recovery 必須用 open-drain GPIO bit-bang 9 clocks + STOP，**不可**用 push-pull 驅動高電平。
- Failsafe 一律 100% PWM，且**不使用**當下可能無效的溫度資料。

## 父專案關係

- 開工/收工儀式、Obsidian 工作筆記路徑、commit 規範 → 見 `../CLAUDE.md`
- 對應工作筆記：`G:\其他電腦\我的電腦\Obsidian Vault\Logitech\Logi-Coleco fan_controller工作筆記.md`
