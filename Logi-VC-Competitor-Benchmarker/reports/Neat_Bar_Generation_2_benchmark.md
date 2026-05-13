# Neat Bar Generation 2 — VC Device Benchmark Report

**Category**: Room Bar
**Date Researched**: 2026-05-13
**Data Sources**:
- https://neat.no/bar-2/

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | 198 × 127 × 42 mm (W×D×H) |
| Weight | 520 g |
| Camera System | 50 MP; f/2.8; 113° HFOV; 4× digital zoom; distortion correction; noise reduction; chromatic aberration correction; auto white balance; hardware-accelerated encode/decode; 1080p30 video; 4K30 / 1080p60 content |
| Audio System | 5 mics + 4 tracking/sensor mics in end-fire array; opposing full-range drivers (vibration cancellation); echo cancellation; noise suppression; AGC; dereverberation |
| Microphone | Yes — 9 mics total (5 primary + 4 tracking), end-fire array |
| Video Inputs | HDMI in (content sharing); USB-C |
| Video Outputs | Up to 2× HDMI out |
| Supported Apps | Microsoft Teams Rooms; Zoom Rooms |
| Wireless | Wi-Fi 6; Bluetooth 5.0 |
| Supported OS | Neat OS (proprietary Android-based) |
| Environmental | 0–35°C operating; 10–90% RH; -20–60°C storage |
| Power Supply | 100–240 V ~50/60 Hz 0.5 A (built-in PSU) |
| Power Consumption | Network standby <8 W (after 20 min) |
| Mounting | Wall/display mount above or below 1–2 monitors; automatic realignment on reorientation |
| Special Features | Ultrasonic auto-wakeup/sleep; orientation sensor (accelerometer); ambient light sensor; compact 520 g form; automatic people framing; hardware video acceleration |

### Dynamic Columns

| Field | Value |
|---|---|
| Room Size | Small to medium, ≤10 people |
| SoC | Not publicly disclosed (Neat proprietary platform) |
| Display Support | Up to 2 screens |
| Auto-Realignment | Yes — accelerometer detects mount orientation |
| Certifications | MTR; Zoom Rooms |
| Form Factor Note | Lightest bar in benchmark at 520 g |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | N/A — no public teardown found; Neat uses proprietary SoC platform |
| Thermal Solution | N/A — no public teardown |
| Thermal Design Observations | Ultra-compact 42 mm H form factor; passive thermal design likely; standby <8 W suggests low TDP |
| Key ICs | Neat proprietary SoC (AI video/audio processing); 50 MP image sensor (brand unconfirmed); audio codec unconfirmed |
| Build Quality | N/A — no public teardown; very compact and light (520 g) chassis |
| Source | N/A (no public teardown as of 2026-05-13) |

---

## Notes & Gaps

Bar 2 is the second generation (Gen 2). Significantly lighter and smaller than Neat Bar Pro. Neat OS is proprietary and not Android AOSP open platform.
