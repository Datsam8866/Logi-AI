# Huddly L1 — VC Device Benchmark Report

**Category**: PTZ Camera
**Date Researched**: 2026-05-13
**Data Sources**:
- https://www.huddly.com/conference-cameras/l1/

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | 122 × 82 × 53 mm (W×D×H) |
| Weight | 600 g |
| Camera System | 20.3 MP 1" CMOS 6K sensor; 1080p30 / 720p30 output; 92° HFOV / 65° VFOV / 103° DFOV; f/2.9; 5× digital zoom; 180° auto-flip; wide-angle fixed lens (no optical PTZ) |
| Audio System | N/A — no built-in speaker or mic |
| Microphone | No |
| Video Inputs | N/A |
| Video Outputs | RJ45 (PoE, data via Ethernet); USB 3.2 Gen 1 Type-A via included USB adapter (also USB-C cable included) |
| Supported Apps | Microsoft Teams certified; Zoom; Google Meet; plug-and-play USB (any platform) |
| Wireless | N/A |
| Supported OS | Plug-and-play — Windows, macOS, Linux, ChromeOS (USB UVC class) |
| Environmental | Standard indoor; 0–40°C operating |
| Power Supply | Power over Ethernet (PoE IEEE 802.3af/at); or external AC/DC 5 V / 4 A adapter |
| Power Consumption | ~14 W (PoE); max 15 W |
| Mounting | Includes wall-mount adapter; tripod 1/4" screw; above/below display clip |
| Special Features | Huddly VPU with neural compute engine; AI smart framing (software-based pan/tilt/zoom); room analytics; people count; 6K sensor for digital crop precision; MS Teams certified |

### Dynamic Columns

| Field | Value |
|---|---|
| Room Size | Medium to large meeting rooms |
| Pan/Tilt Range | N/A (no mechanical PTZ — AI digital framing only) |
| Optical Zoom | N/A (digital only, 5×) |
| Connection Method | PoE Ethernet (primary); USB via included adapter (secondary) |
| Cable Length | Up to 100 m Ethernet |
| FCC ID | 2ALRZ002 |
| Certifications | Microsoft Teams; CE; FCC; RoHS |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | Huddly proprietary VPU (Vision Processing Unit) with neural compute engine — FCC ID 2ALRZ002 internal photos exist but component labels not publicly detailed |
| Thermal Solution | N/A — no detailed public teardown; aluminum body likely serves as passive heatsink |
| Thermal Design Observations | Aluminum body construction — passive thermal dissipation through housing; no fan expected at 14 W TDP |
| Key ICs | Huddly VPU (neural compute; vendor unconfirmed); 1" CMOS sensor (brand unconfirmed); PoE controller IC |
| Build Quality | Aluminum body; compact 122×82×53 mm; FCC internal photos accessible via fccid.io/2ALRZ002 |
| Source | FCC ID filing 2ALRZ002 — internal photos available at fccid.io; no iFixit/YouTube teardown found (as of 2026-05-13) |

---

## Notes & Gaps

Note: Huddly L1 is classified as PTZ Camera (standalone, no mic) but is technically a fixed wide-angle camera with AI-based digital framing — not mechanical PTZ. Category reflects 'camera-only' role in the taxonomy.
