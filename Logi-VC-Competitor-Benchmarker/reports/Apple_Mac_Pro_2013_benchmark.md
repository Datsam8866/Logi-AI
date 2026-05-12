# Apple Mac Pro (Late 2013) — VC Device Benchmark Report

**Category**: Compute (user-defined)
**Date Researched**: 2026-05-12
**Data Sources**:
- [Apple Official Tech Specs](https://support.apple.com/en-us/112025)
- [iFixit Teardown](https://www.ifixit.com/Teardown/Mac+Pro+Late+2013+Teardown/20778)
- [Wikipedia: Mac Pro](https://en.wikipedia.org/wiki/Mac_Pro)

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | H: 251mm, Diameter: 168mm (cylinder) |
| Weight | 4.99 kg (11 lb) |
| Camera System | N/A |
| Audio System | N/A |
| Microphone | No |
| Video Inputs | N/A |
| Video Outputs | 6× Thunderbolt 2, 1× HDMI 1.4 Ultra HD |
| Supported Apps | macOS workstation apps |
| Wireless | 802.11ac Wi-Fi; Bluetooth 4.0 |
| Supported OS | macOS (up to macOS Catalina 10.15) |
| Environmental | Line voltage: 100–240V AC; ENERGY STAR 6; EPEAT Gold; BFR/PVC-free |
| Power Supply | 100–240V AC |
| Power Consumption | Max 450W continuous |
| Mounting | Desktop freestanding (no mount options) |
| Special Features | Unified triangular thermal core shared by dual GPUs + CPU; single impeller pulls air bottom-to-top |

### Category-Specific: Compute

| Field | Value |
|---|---|
| Processor Options | 3.7GHz Quad-Core / 3.5GHz 6-Core / 3.0GHz 8-Core / 2.7GHz 12-Core Intel Xeon E5 |
| GPU | Dual AMD FirePro D300/D500/D700 (2–6GB GDDR5 VRAM each) |
| Memory | Up to 64GB 1866MHz DDR3 ECC (4 DIMM slots) |
| Storage | 256GB–1TB PCIe SSD |
| Compute Form Factor | Cylinder — Unified Thermal Core design |
| Fan | Single impeller, Nidec brushless DC motor AG720K01 |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | Intel Xeon E5-1620 v2 (Quad-Core 3.7GHz, 10MB L3, socket-mounted); Dual AMD FirePro GPU modules on separate boards |
| Thermal Solution | Single centrifugal fan (Nidec AG720K01) + triangular passive heatsink core shared by CPU and both GPUs |
| Thermal Design Observations | Triangular "Unified Thermal Core": CPU mounts to one face, each GPU to the other two faces via thermal paste. Air is drawn from the bottom through the core and exhausted out the top. Eliminated multiple fans but locked GPU upgrade path. Known to cause thermal failures in field. |
| Key ICs | Fan motor controller: Allegro Microsystems A5940LPT (3-phase sensorless sinusoidal driver) |
| Build Quality | Torx screws throughout; modular design; CPU user-replaceable; RAM easily accessible; fan replaceable. iFixit repairability score: 8/10 |
| Source | [iFixit Teardown](https://www.ifixit.com/Teardown/Mac+Pro+Late+2013+Teardown/20778) (2013) |

---

## Notes & Gaps

- Category `Compute` is user-defined, not in default VC taxonomy
- Known design issue: Apple exec acknowledged "we designed ourselves into a bit of a thermal corner" — GPU failures due to heat buildup in sealed cylinder with no upgrade path
- GPU BOM (exact ASIC die details) not publicly available
- 12-core / 8-core GPU teardown details may differ from base quad-core config documented by iFixit
