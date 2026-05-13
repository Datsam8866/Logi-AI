# FLIR One Pro — VC Device Benchmark Report

**Category**: IR Camera (user-defined)
**Date Researched**: 2026-05-12
**Data Sources**:
- [FLIR One Pro Product Page](https://www.flir.com/products/flir-one-pro/)
- [Hackaday Repair/Teardown](https://hackaday.io/project/177952-flir-one-pro-repair/details)

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | 68×34×14mm |
| Weight | 36.5g |
| Camera System | Thermal: 160×120 native / 480×360 super-res; Visual: 1440×1080; Frame rate: 8.7Hz |
| Audio System | N/A |
| Microphone | No |
| Video Inputs | N/A |
| Video Outputs | N/A (streams via USB to smartphone) |
| Supported Apps | FLIR One app (iOS / Android) |
| Wireless | N/A (wired to smartphone via Lightning / USB-C) |
| Supported OS | iOS, Android |
| Environmental | Operating: 0–35°C ambient |
| Power Supply | Female USB-C 5V/1A (charging); powered via smartphone connector |
| Power Consumption | Smartphone-powered (no standalone draw spec published) |
| Mounting | Attaches to smartphone via Lightning or USB-C; no standalone mount |
| Special Features | MSX image enhancement (thermal + visual overlay); drop-resistant 1.5m; dual-range temp measurement up to 400°C; internal shutter for auto-calibration |

### Category-Specific: IR Camera

| Field | Value |
|---|---|
| Thermal Resolution | 160×120 native; 480×360 super resolution |
| Visual Resolution | 1440×1080 |
| Temperature Range | −20 to 120°C and 0 to 400°C (two selectable ranges) |
| Accuracy | ±3°C or ±5%, typical (60s after startup, ambient 15–35°C, scene 5–120°C) |
| NETD | 70 mK |
| Spectral Range | 8–14 µm, 12 µm pixel pitch |
| Frame Rate | 8.7 Hz |
| Drop Resistance | 1.5m |
| Battery Life | ~1 hour; 40-minute charge time |
| Connectivity | Lightning (iOS) / USB-C (Android/Apple) + female USB-C charging (5V/1A) |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | FLIR Lepton 3.5 thermal module (160×120, 12µm pitch); main PCB with rigid-flex design; small internal battery; Lepton 3.5 is extractable and hackable with PureThermal 2 breakout board |
| Thermal Solution | Passive; no fan; sealed compact body; Lepton 3.5 self-calibrates via internal motorized shutter |
| Thermal Design Observations | Lepton 3.5 shutter wrapped in copper foil; MAX31725 temperature sensor on flex cable taped to shutter for calibration reference. Known ~5°C thermal gradient across shutter surface; thermal coupling to sensor only through thin copper foil — identified as calibration accuracy limitation. |
| Key ICs | FLIR Lepton 3.5 (thermal core); MAX31725 temperature sensor; TI BQ24295 battery management (confirmed in earlier gen; likely similar in Pro); Sonix SN9C270 camera interface (earlier gen reference — Pro exact BOM not fully public) |
| Build Quality | Main vulnerability: USB-C host connector is fragile, fails on drop despite 1.5m drop-resistance rating. Phillips screws + metal plate hold PCB in body. Lepton 3.5 module extractable after peeling copper foil + removing SLA bracket. Rigid-flex PCB design. |
| Source | [Hackaday Teardown/Repair](https://hackaday.io/project/177952-flir-one-pro-repair/details) |

---

## Notes & Gaps

- Category `IR Camera` is user-defined, not in default VC taxonomy
- Selected variant: FLIR One **Pro** (160×120 thermal, up to 400°C) — not Gen 3 Standard or Pro LT
- IC list partially inferred from earlier FLIR One gen teardowns; exact Pro PCB BOM not fully public
- Power consumption not independently specified — fully dependent on connected smartphone
- FLIR One Pro is now available in Lightning / USB-C / USB-C for Apple variants; connector type should be specified at purchase
