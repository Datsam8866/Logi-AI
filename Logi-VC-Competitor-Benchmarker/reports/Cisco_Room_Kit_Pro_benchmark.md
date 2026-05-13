# Cisco Room Kit Pro — VC Device Benchmark Report

**Category**: AIO System
**Date Researched**: 2026-05-13
**Data Sources**:
- https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/webex-room-series/datasheet-c78-741052.html

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | Codec Pro: 436 × 231 × 66 mm (W×D×H), 3.3 kg; Quad Camera: 950 × 103 × 120 mm, 4.8 kg |
| Weight | Codec: 3.3 kg; Quad Camera: 4.8 kg |
| Camera System | Cisco Quad Camera — 80 MP total (4-lens: 1× 83° main + 3× 50° telephoto), 4K60, 7× digital zoom; simultaneous multi-lens capture for Frames AI mode |
| Audio System | External mic connectivity via Euroblock/Phoenix connectors; machine-learning noise removal; built-in speaker; PoE-powered accessories |
| Microphone | No built-in mic — requires external Cisco mics or third-party audio system via analog/AES67 |
| Video Inputs | 3× HDMI in (4K30, 1× HDCP 1.4); 1× USB-C in (4K30, 15 W charging out) |
| Video Outputs | Up to 3× HDMI out (3 simultaneous displays) |
| Supported Apps | Cisco Webex (native); Microsoft Teams Rooms; Zoom; Google Meet (BYOD/certified) |
| Wireless | Wi-Fi 6 (802.11ax); Bluetooth 5.0 |
| Supported OS | Cisco RoomOS; Microsoft Teams Rooms on Android |
| Environmental | Standard commercial indoor; 0–40°C operating |
| Power Supply | External PSU; PoE++ IEEE 802.3bt per port (max 90 W combined for 4 ports) |
| Power Consumption | — |
| Mounting | 1.5RU rack mount; optional rack-mounting accessory; Codec Pro standalone table placement |
| Special Features | AI Frames (equitable multi-person framing); Speaker Tracking; People Count analytics; PresenterTrack; RoomOS cloud/on-prem registration |

### Dynamic Columns

| Field | Value |
|---|---|
| Room Size | Extra-large boardroom / auditorium / custom AV integration |
| SoC (Codec) | Proprietary Cisco/Webex compute platform (not publicly disclosed) |
| Display Support | Up to 3 external screens |
| Camera Inputs | 1× HDMI camera in; 1× USB camera in |
| Audio I/O | 4× Euroblock mic in; 2× Euroblock line out; Ethernet (AES67); analog |
| Certifications | Webex cloud; MTR; BYOD |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | No public teardown found — Cisco proprietary compute platform (NVIDIA GPU confirmed in Room Kit EQ; likely similar lineage) |
| Thermal Solution | N/A — no public teardown found |
| Thermal Design Observations | 1.5RU metal chassis; rack-mount form factor suggests active cooling (internal fan likely) |
| Key ICs | Cisco proprietary SoC; Sony/OV image sensors (inferred); Codec Pro handles encoding/AI |
| Build Quality | N/A — no public teardown |
| Source | N/A (no public teardown as of 2026-05-13) |

---

## Notes & Gaps

Datasheet URL returned 403 — specs sourced from web search aggregation. Codec Pro is the original (Gen 1); Gen 2 = Codec Pro G2 (updated SoC). Weight includes Quad Camera bundle.
