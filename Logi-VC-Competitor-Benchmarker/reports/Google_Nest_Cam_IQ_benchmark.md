# Google Nest Cam IQ Indoor/Outdoor — VC Device Benchmark Report

**Category**: Security Camera (user-defined)
**Date Researched**: 2026-05-12
**Data Sources**:
- [Google Nest Tech Specs](https://support.google.com/googlenest/answer/9259110)
- [iFixit IQ Outdoor Disassembly](https://www.ifixit.com/Guide/Nest+IQ+Outdoor+Camera+Module+Disassembly/148782)
- [B&H Photo Specs](https://www.bhphotovideo.com/c/product/1365625-REG/nest_nc4100us_cam_iq_outdoor_security.html/specs)

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | Indoor: 124×74×74mm \| Outdoor: 93×93×128mm |
| Weight | Indoor: 357g \| Outdoor: 568g |
| Camera System | 8MP 1/2.5" sensor, 1920×1080 @ 30fps, 130° FOV, 12× digital zoom, HDR |
| Audio System | Built-in speaker; 3-mic array with noise + echo suppression; two-way audio |
| Microphone | Yes — 3-mic array (MEMS) |
| Video Inputs | N/A |
| Video Outputs | N/A (streams via Wi-Fi to app) |
| Supported Apps | Google Home, Nest app |
| Wireless | 802.11a/b/g/n/ac Wi-Fi; Bluetooth LE |
| Supported OS | iOS, Android (Google Home app) |
| Environmental | Indoor: 0–40°C \| Outdoor: −40 to 45°C; Outdoor IP66 rated |
| Power Supply | USB-C, 15V DC 1.87A |
| Power Consumption | ~28W (15V × 1.87A) |
| Mounting | Indoor: tabletop / magnetic mount \| Outdoor: wall mount with weatherproof cable |
| Special Features | On-device person + face detection; HDR; IR night vision (8× IR LEDs indoor); Hexa-core Qualcomm SoC |

### Category-Specific: Security Camera

| Field | Value |
|---|---|
| IP Rating | IP66 (Outdoor only; Indoor: indoor use only) |
| Night Vision | 8× IR LEDs (Indoor) / IR LEDs (Outdoor) |
| Zoom | 12× digital zoom |
| AI Features | Familiar Face detection, person/object detection, Google Assistant integration |
| Cloud | Requires Google Home app + Nest Aware subscription for full features |
| Cable Length | Indoor: 3m USB-C \| Outdoor: 7.5m USB-C |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | Hexa-core Qualcomm SoC (exact model in TechInsights deep dive, not public); 8MP image sensor |
| Thermal Solution | Passive; compact sealed housing; no fan |
| Thermal Design Observations | Sealed plastic housing acts as passive heat spreader. No active cooling. Outdoor version IP66-sealed. |
| Key ICs | — (full BOM in TechInsights subscription teardown only) |
| Build Quality | Outdoor: modular camera module replaceable per iFixit guide; ribbon cables for mic ring lightly attached with double-sided tape. 3 ribbon cables on LED light ring (2× mic, 1× status LED). Motherboard held by 4 long screws. |
| Source | [iFixit IQ Outdoor Disassembly](https://www.ifixit.com/Guide/Nest+IQ+Outdoor+Camera+Module+Disassembly/148782) \| [TechInsights Deep Dive (paywalled)](https://www.techinsights.com/products/ddt-1806-806) |

---

## Notes & Gaps

- Category `Security Camera` is user-defined, not in default VC taxonomy
- Indoor (NC3100US) and Outdoor (NC4100US) are separate SKUs — same 8MP sensor, different housing/IP rating; researched together as one entry per user request
- Exact Qualcomm SoC model not publicly disclosed; TechInsights teardown contains it but requires paid access
- Full IC BOM marked `—` due to unavailability of public teardown at component level
