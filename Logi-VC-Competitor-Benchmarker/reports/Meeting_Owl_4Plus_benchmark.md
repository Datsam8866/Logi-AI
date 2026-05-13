# Meeting Owl 4+ — VC Device Benchmark Report
**Category**: Table Camera
**Date Researched**: 2026-05-13
**Data Sources**: https://owllabs.com/products/meeting-owl-4-plus

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | 116×116×275mm |
| Weight | 1,500g |
| Camera System | 64MP 4K 360° fisheye camera; AI auto-framing (speaker + group modes); 4K UHD 30fps output |
| Audio System | 8 omnidirectional microphones, 5.5m (18ft) pickup range; 2x speakers 79dBSPL; AI noise equalization |
| Microphone | Yes — 8x omnidirectional |
| Video Inputs | N/A |
| Video Outputs | USB-C (UVC) |
| Supported Apps | Zoom, Teams, Meet, WebEx, and more (USB plug-and-play) |
| Wireless | Wi-Fi 2.4/5GHz (802.11ac), Bluetooth 4.2; Ethernet via USB-C hub accessory |
| Supported OS | Windows, macOS, ChromeOS |
| Environmental | — |
| Power Supply | AC/DC 100–240V / 1.6A → 20V/3A; PoE-capable |
| Power Consumption | ~60W max |
| Mounting | Desktop (tabletop owl form factor) |
| Special Features | Qualcomm Snapdragon 8250 SoC (OpenQ865 SOM), AI speaker tracking, K-Lock security slot, Whiteboard Owl addon support, OwlCare AI subscription features |
| Coverage Method | Single 64MP fisheye (360°) |
| SoC | Qualcomm Snapdragon 8250 (OpenQ865 SOM) |
| FCC ID | 2ALXJ-MTW405 |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | OpenQ865 SOM (Qualcomm Snapdragon 865/8250 platform), Main Carrier Board, USB-C Board, Top Audio Board; multiple flexible PCBs (button, mute LED, video indicator, isolated mic) |
| Thermal Solution | N/A (no consumer teardown — FCC filing only) |
| Thermal Design Observations | N/A (thermal solution not visible from FCC internal photos) |
| Key ICs | OpenQ865 SOM (Qualcomm Snapdragon 865 compute + RF); flexible PCBs for mute/LED/mic isolation |
| Build Quality | N/A (FCC photos only — build quality not assessed) |
| Source | https://fccid.io/2ALXJ-MTW405 (FCC internal photos, available 2024-06-30) |

---

## Notes & Gaps

SoC confirmed via FCC filing: OpenQ865 SOM = Qualcomm Snapdragon 865/8250. FCC ID 2ALXJ-MTW405 contains schematics and internal board layout. Supports PoE via accessory hub.
