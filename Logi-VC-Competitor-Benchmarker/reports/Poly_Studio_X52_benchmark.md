# Poly Studio X52 — VC Device Benchmark Report

**Category**: Room Bar
**Date Researched**: 2026-05-13
**Data Sources**:
- https://www.hp.com/us-en/poly/video-conferencing/all-in-one/studio-x52.html

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | 770 × 115 × 103 mm (W×H×D) |
| Weight | 2540 g (5.6 lbs) |
| Camera System | 20 MP 4K; 95° HFOV / 110° DFOV; 5× digital zoom; 4K30 video; DirectorAI: Group Framing / People Framing (up to 6) / Speaker Framing / Presenter Tracking |
| Audio System | 2× MEMS + 2× second-order beamforming mics; 20 ft (6 m) pickup; dual stereo speakers; full-duplex; NoiseBlockAI; Acoustic Fence |
| Microphone | Yes — 4 mics (2 MEMS + 2 second-order) |
| Video Inputs | HDMI in; USB-C in (laptop) |
| Video Outputs | HDMI out (up to 2 displays) |
| Supported Apps | Microsoft Teams Rooms; Zoom Rooms; Poly Video Mode; Webex |
| Wireless | Wi-Fi 6; Bluetooth 5.0; wireless content sharing |
| Supported OS | Poly OS (Android-based) |
| Environmental | 0–40°C operating; 10–90% RH non-condensing |
| Power Supply | Auto-sensing 100–240 V ~50/60 Hz |
| Power Consumption | Operating: 25 W; Idle/Sleep: 8 W |
| Mounting | Wall/display mount; VESA compatible; display clip; table stand |
| Special Features | Poly DirectorAI; NoiseBlockAI; Acoustic Fence; People Count; 4K single-lens; VESA mount; Poly Lens management |

### Dynamic Columns

| Field | Value |
|---|---|
| Room Size | Medium conference room (up to ~15 people) |
| SoC | Qualcomm (specific model not publicly disclosed for X52) |
| Display Support | Up to 2 screens |
| Mic Pickup | Up to 6 m (20 ft) |
| Speaker Config | Dual stereo |
| VESA Mount | Yes |
| Certifications | MTR; Zoom Rooms; Poly Video Mode native |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | Qualcomm platform (Poly X-series family uses Qualcomm); specific SoC for X52 not publicly confirmed |
| Thermal Solution | N/A — no public teardown |
| Thermal Design Observations | Operating 25 W, Idle 8 W — relatively low TDP; passive or small fan likely; 770 mm bar chassis |
| Key ICs | Qualcomm SoC (model unconfirmed); 20 MP 4K image sensor (brand unconfirmed); Poly audio DSP |
| Build Quality | N/A — no public teardown |
| Source | N/A (no public teardown as of 2026-05-13) |

---

## Notes & Gaps

Power consumption: 37 VA @120 V; 25 W operating; 8 W idle. X72 uses Snapdragon 865 (confirmed); X52 SoC not confirmed but likely same family.
