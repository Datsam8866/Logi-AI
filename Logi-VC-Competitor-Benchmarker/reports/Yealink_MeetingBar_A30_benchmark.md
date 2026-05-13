# Yealink MeetingBar A30 — VC Device Benchmark Report

**Category**: Room Bar
**Date Researched**: 2026-05-13
**Data Sources**:
- https://www.yealink.com/en/product-detail/microsoft-teams-rooms-meetingbar-a30

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | 700 × 121 × 98 mm (W×D×H) |
| Weight | 4750 g (bar only, A30-010) |
| Camera System | Dual-eye system — (1) 4K panoramic/context camera (120° DFOV); (2) Optical 10× hybrid zoom main camera; AI auto-framing; Speaker Tracking; Smart Gallery (Zoom); simultaneous dual-stream |
| Audio System | 8 MEMS mic array; beamforming; AI noise reduction; full-duplex; AEC; de-reverberation; AGC; expandable with external mics; Standby: 14.9 W, Average: 12.5 W |
| Microphone | Yes — 8 MEMS elements built-in; expandable |
| Video Inputs | HDMI in; USB-C in |
| Video Outputs | Up to 2× HDMI out |
| Supported Apps | Microsoft Teams Rooms; Zoom Rooms |
| Wireless | Wi-Fi 6 (802.11ax); Bluetooth 5.0 |
| Supported OS | Android 13 |
| Environmental | 0–40°C operating; -30–70°C storage |
| Power Supply | External AC/DC adapter (100–240 V input) |
| Power Consumption | Average: 12.5 W; Standby: 14.9 W |
| Mounting | Wall/display mount; ceiling mount option; bracket included |
| Special Features | Qualcomm Snapdragon 845 SoC; dual-eye camera (panoramic overview + optical zoom); Smart Gallery; optional CTP18 touch panel; enterprise management via Yealink Device Management |

### Dynamic Columns

| Field | Value |
|---|---|
| Room Size | Medium rooms (9–12 people) |
| SoC | Qualcomm Snapdragon 845 |
| Display Support | Up to 2 screens |
| Dual-Eye Camera | Yes — 120° context + optical 10× zoom main camera |
| Mic Expandability | Yes — external mic expansion supported |
| Certifications | MTR; Zoom Rooms certified |
| Touch Panel | Optional CTP18 (A30-020 SKU) |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | Qualcomm Snapdragon 845 confirmed in Yealink product documentation |
| Thermal Solution | N/A — no public teardown |
| Thermal Design Observations | 700 mm bar housing; Snapdragon 845 (10 nm LPP) generates moderate heat; 12.5 W average power suggests passive or small fan cooling |
| Key ICs | Qualcomm Snapdragon 845; dual-camera ISP (Qualcomm Spectra 280); audio codec for 8-mic beamforming |
| Build Quality | N/A — no public teardown |
| Source | N/A (no public teardown as of 2026-05-13) |

---

## Notes & Gaps

Weight varies by SKU: A30-010 (bar only) = 4.75 kg; A30-020 (bar + CTP18 panel) = 7.05 kg. Standby power (14.9 W) > average power (12.5 W) is unusual — may reflect display controller idle vs. active encoding.
