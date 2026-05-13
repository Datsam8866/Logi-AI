# Prisual TEM-4K30N PRO -- VC Device Benchmark Report
**Category**: PTZ Camera
**Date Researched**: 2026-05-13
**Data Sources**: https://www.prisual.us/products/prisual-4k-30x-ndi-ptz-camera

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | 170 x 228 x 181 mm |
| Weight | 2,000 g |
| Camera System | 4K/60fps; 1/1.8" UHD CMOS 8.42MP; 30x optical (f=7.1-210mm, F1.61-F5.19); 59.2 deg HFOV (wide) to 2.5 deg (tele) |
| Audio System | N/A (camera only) |
| Microphone | No |
| Video Inputs | N/A |
| Video Outputs | HDMI 2.0; 3G-SDI (BNC); USB 3.0 Type-B; 1GbE RJ45 (NDI) |
| Supported Apps | Zoom, Teams, Meet, NDI-compatible platforms (Official NDI 6 & NDI HX3 certified) |
| Wireless | N/A |
| Supported OS | Windows, macOS |
| Environmental | Operating: 0-40 C |
| Power Supply | DC 12V or PoE+ |
| Power Consumption | Max 18W |
| Mounting | Desktop, wall/ceiling bracket, tripod |
| Special Features | 30x optical zoom; 4K@60fps; Official NDI 6 & NDI HX2/HX3 certified; AI auto-tracking; tally light; 3D digital noise reduction; gravity sensor auto-flip; RS-232/RS-485 VISCA/Pelco |
| Pan Range | +/-170 deg |
| Tilt Range | +90 / -30 deg |
| Presets | 255 (0.1 deg accuracy) |
| IR Remote | Yes |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | Ambarella 4K 60FPS AI vision chip (model unconfirmed) |
| Thermal Solution | N/A |
| Thermal Design Observations | N/A |
| Key ICs | Ambarella SoC (ISP/AI, model unconfirmed); Sony 1/1.8" CMOS sensor |
| Build Quality | N/A |
| Source | N/A (SoC cited from Amazon product listing, not confirmed via physical teardown) |

---

## Notes & Gaps

Official NDI 6 & NDI HX3 certified. SoC reported as Ambarella 4K 60FPS AI chip (from Amazon listing -- not teardown-confirmed). 30x variant; same 1/1.8" 8.42MP sensor as 20x (TEM-4K20N PRO). Taller body (228mm H) vs 20x (142mm H).
