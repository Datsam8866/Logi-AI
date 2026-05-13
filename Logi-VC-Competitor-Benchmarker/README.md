# Logi-VC-Competitor-Benchmarker

追蹤與分析 Logitech 競品（視訊會議 / VC 相關產品）的市場資訊工具。

## 最新進度

**2026-05-13（第四批）**
- 批次新增 9 筆 PTZ Camera / Table Camera 競品 benchmark（資料庫共 44 筆）：
  - PTZ Camera：AVer CAM520 Pro3、BenQ DVY23、BZBGear BG-ADAMO-4K、Poly Studio E70、Poly Studio E60、Legrand Vaddio RoboShot 12E HDBT、Yealink UVC86、Prisual TEM-4K30N PRO
  - Table Camera：Nuroum V403（含 5x 光學、motorized PTZ、built-in 雙麥，使用者指定分類）
- Prisual TEM-4K30N PRO：4K@60fps、30x 光學、Official NDI 6 & HX3 認證、Ambarella SoC（Amazon 聲稱，未 teardown 確認）
- Poly Studio E70 注意：無 motorized PTZ，僅 DirectorAI 電子幀取，分類為 PTZ Camera 係使用者指定
- 生成 9 個 `.md` 報告，存於 `reports/`；重新生成 dashboard.html（現共 44 筆）

**2026-05-13（第三批）**
- 批次新增 11 筆 Mic / Accessory 競品 benchmark（資料庫共 35 筆）：
  - Mic：Cisco Table Microphone Pro、Lenovo Google Meet Series One Mic Pod、Poly Studio A2、Sennheiser TeamConnect Ceiling Medium、Shure MXA901、Shure MXA310AL、Legrand Vaddio TableMIC、Legrand Vaddio CeilingMIC、Yealink CM20、Yealink VCM36-W
  - Accessory：Jabra PanaCast Meet Anywhere（搭配包，含 PanaCast 50 + Speak2 75）

**2026-05-13（第二批）**
- 批次新增 7 筆 Table Camera 競品 benchmark（資料庫共 24 筆）：
  - IPEVO TOTEM 360、Kandao Meeting Pro、Neat Center SE
  - Meeting Owl 4+、Panasonic TY-CSP1 (PressIT 360)、Poly Studio E360、Yealink MTowr
- Meeting Owl 4+ 確認 SoC：Qualcomm Snapdragon 8250（FCC ID 2ALXJ-MTW405，OpenQ865 SOM）
- 生成 7 個 `.md` 報告，存於 `reports/`；重新生成 dashboard.html（現共 24 筆）
- Neat Center SE、Poly Studio E360 為 companion-only 裝置（無法獨立運作）

**2026-05-13（第一批）**
- 修正 Dashboard tab 無法切換：修掉 inline JavaScript alert 字串換行造成的語法錯誤，並新增 `tests/check_dashboard.py` 防止回歸
- 修正「更新資料」會覆蓋回舊版 dashboard 的問題：server refresh 現在會重新載入最新版 generator，並改用 threaded server 避免單一連線卡住
- Dashboard 改為 light 背景與淺色卡片，保留既有資訊架構
- 修正 teardown 連結呈現：`N/A` 不再產生可點擊連結；Huddly L1、Poly Studio X72 改為 FCC ID 頁；FLIR One Pro 保留可開的 Hackaday teardown/repair 來源
- 批次新增 12 筆 VC 競品 benchmark（資料庫共 17 筆）：
  - AIO System：Cisco Room Kit Pro、Cisco Room Kit EQ
  - Room Bar：Cisco Room Bar Pro、Neat Bar Gen2、Jabra PanaCast 50 VBS、Neat Bar Pro、Poly Studio X72、Poly Studio X52、Yealink MeetingBar A30/A40/A10
  - PTZ Camera：Huddly L1
- 修正 Dashboard tab 切換 Bug：nav 與 header 改為共用 sticky 容器，tab 列現在永遠釘頂

**2026-05-12**
- 初始化專案，完成首批 5 筆競品 benchmark（Mac Pro Trashcan、Nest Cam IQ、FLIR One Pro、AVer VB370A、AVer VB350）
- 建立互動式 HTML dashboard + 本機伺服器（port 8765）

**已知注意事項**
- 若修改 `serve_dashboard.py` 本身，仍需重啟本機 server；單純修改 `generate_dashboard.py` 後可用「更新資料」重新產生 dashboard

## Next Action

- [ ] 補足 Neat/Cisco 的 SoC 型號（Neat 完全未公開；Cisco 確認 NVIDIA 但不揭露型號）
- [ ] 確認 Prisual TEM-4K30N PRO 的 Ambarella SoC 型號（目前僅 Amazon 聲稱，非 teardown 確認）
- [ ] 尋找 PTZ Camera 9 筆新品的公開 teardown 資料（目前全部 N/A）
- [ ] 尋找 Table Camera、Room Bar 現有各批新品的公開 teardown 資料
- [ ] 考慮加入 Logitech 自家基準欄位（Rally Bar、Rally Bar Mini 等作為比較基準線）
- [ ] 補足 Neat Center SE / Poly E360 的詳細尺寸與重量（目前未找到官方數值）
- [ ] 補足 Nest Cam IQ SoC 型號（TechInsights 付費資料）

## 資料夾結構

```
Logi-VC-Competitor-Benchmarker/
├── .claude/
│   └── skills/
│       └── vc-device-benchmarker/   # Benchmark workflow skill
├── reports/                          # .md benchmark 報告 + dashboard.html
├── vc_benchmark.db                   # SQLite 資料庫（44 筆）
├── generate_dashboard.py             # 生成 dashboard HTML
├── serve_dashboard.py                # 本機 HTTP 伺服器（port 8765）
├── CLAUDE.md
└── README.md
```

## 使用方式

**Benchmark 新競品**：給產品名稱或 URL，skill 會自動分類 → 搜尋規格 → 搜尋 teardown → 存 SQLite → 產出 `.md` 報告。

**啟動 Dashboard**：
```powershell
python serve_dashboard.py
# 開啟 http://localhost:8765/
```

**僅重新生成 HTML（不啟動伺服器）**：
```powershell
python generate_dashboard.py
```
