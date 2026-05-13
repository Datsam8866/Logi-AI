# Cisco Room Kit EQ — VC Device Benchmark Report

**Category**: AIO System
**Date Researched**: 2026-05-13
**Data Sources**:
- https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/spark-room-kit-series/room-kit-eq-ds.html

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | Codec EQ: 472 × 203 × 43 mm (W×D×H), 1.64 kg; Quad Camera: 950 × 103 × 120 mm |
| Weight | Codec EQ: 1.64 kg; Quad Camera: 4.8 kg |
| Camera System | Cisco Quad Camera (80 MP, 4-lens: 83° main + 3× 50° telephoto), 4K60, 7× digital zoom; Frames AI mode; UHD image processing |
| Audio System | Built-in speaker; ML noise removal; distraction-free audio; supports directional Cisco mics + third-party systems via PoE/Ethernet |
| Microphone | No built-in mic — external directional Cisco mics or third-party audio required |
| Video Inputs | 3× HDMI in (4K30, 1× HDCP 1.4); 1× USB-C in (4K30, 15 W charging) |
| Video Outputs | Up to 3× HDMI out (3 simultaneous displays) |
| Supported Apps | Cisco Webex; Microsoft Teams Rooms; Zoom; Google Meet |
| Wireless | Wi-Fi 6E; Bluetooth 5.2 |
| Supported OS | Cisco RoomOS; Microsoft Teams Rooms |
| Environmental | 0–40°C operating; standard commercial indoor |
| Power Supply | PoE++ IEEE 802.3bt (4 ports, max 90 W combined); external PSU option |
| Power Consumption | — |
| Mounting | Half-rack (1U) bracket optional; flat surface placement; camera mounted above/below display |
| Special Features | NVIDIA AI chipset; Frames equitable framing; Speaker Tracking; People Count analytics; PresenterTrack; 4K content wireless sharing; USB passthrough for laptop |

### Dynamic Columns

| Field | Value |
|---|---|
| Room Size | Large conference room / boardroom / training room / auditorium |
| SoC (Codec) | NVIDIA (specific model not publicly disclosed) |
| Display Support | Up to 3 external screens |
| Audio I/O | 4× PoE Ethernet ports (cameras/mics/accessories); HDMI ARC; analog |
| USB Passthrough | Yes — laptop integration |
| Certifications | Cisco Webex; MTR on Android |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | NVIDIA AI chipset confirmed in datasheet; specific GPU/SoC model not disclosed publicly |
| Thermal Solution | N/A — no public teardown found |
| Thermal Design Observations | Low-profile half-rack chassis (43 mm H); likely passive or fan-assisted; NVIDIA chipset implies non-trivial thermal budget |
| Key ICs | NVIDIA SoC (undisclosed); Cisco Quad Camera ISP; audio codec unconfirmed |
| Build Quality | N/A — no public teardown |
| Source | N/A (no public teardown as of 2026-05-13) |

---

## Notes & Gaps

Cisco confirms NVIDIA chipset in marketing — model not specified. Codec EQ is newer/lighter than Codec Pro. Quad Camera weight sourced from earlier Quad Camera CAD data.
