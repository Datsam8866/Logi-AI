# AVer VB350 — VC Device Benchmark Report

**Category**: Room Bar
**Date Researched**: 2026-05-12
**Data Sources**:
- [VideoConferenceGear product page](https://www.videoconferencegear.com/aver-vb350-dual-lens-enterprise-grade-4k-ptz-videobar-for-medium-and-large-rooms/) — primary spec source
- [AVer USA Datasheet PDF](https://www.averusa.com/business/downloads/datasheet-brochure/vb350-datasheet.pdf)
- [AVer official product page](https://communication.aver.com/model/vb350)

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | L: 791mm × W: 128mm × H: 126mm |
| Weight | 3.3 kg |
| Camera System | **Dual-lens:** (1) PTZ — Sony 4K, 18× hybrid zoom, 92° diagonal / 81° H / 50° V FOV, pan 165°, tilt 101°, 10 presets; (2) Fixed — Sony 4K, 113° diagonal / 105° H / 71° V FOV; Resolutions: 4K/3264×1836, 2560×1440, 1920×1080, lower res at 15/30fps; 1280×720 at 60fps |
| Audio System | 14 beamforming elements, 10m pickup range (33ft); 96 dB SPL at 0.5m; AEC, AI Noise Suppression, Audio Fence; 3.5mm line in/speaker out; RJ-45 audio expansion port |
| Microphone | Yes — 14 beamforming elements, 10m pickup; RJ-45 expansion mic port |
| Video Inputs | 1× USB 3.1 Type-C (primary host connection); 3× USB-A; 2× RJ-45 (1× Ethernet + 1× audio expansion); Mini DIN 6 RS-232 |
| Video Outputs | HDMI (via USB Display Adapter); 3.5mm speaker out |
| Supported Apps | Zoom Rooms (certified), Microsoft Teams, Google Meet, Skype, Cisco WebEx, Adobe Connect, and others (USB UVC/UAC device) |
| Wireless | N/A — USB-connected device; no built-in wireless |
| Supported OS | Windows, macOS, ChromeOS (USB UVC/UAC plug-and-play; host-OS agnostic) |
| Environmental | Not publicly specified |
| Power Supply | DC 12V / 5A |
| Power Consumption | 60W |
| Mounting | Wall-mount bracket (included); Tripod screw (1/4") |
| Special Features | AI auto-framing; AI noise suppression; Audio fence; Dual 4K lens seamless switching; VISCA/RS-232 control; IR remote; USB UVC/UAC plug-and-play |

### Dynamic Columns (Room Bar)

| Field | Value |
|---|---|
| PTZ Pan/Tilt | 165° pan / 101° tilt; 10 preset positions |
| PTZ Lens FOV | 92° diagonal / 81° H / 50° V; 18× hybrid zoom |
| Fixed Lens FOV | 113° diagonal / 105° H / 71° V |
| Connection Type | USB 3.1 Type-C (requires external PC — no built-in OS) |
| Audio Expansion Port | 1× RJ-45 for expansion mic/speakerphone; 3.5mm line in/out |
| Serial Control | Mini DIN 6 RS-232 |
| Min Focus Distance | ~1m (3.2 ft) |
| Host OS Supported | Windows, macOS, ChromeOS |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | N/A — no built-in compute SoC (USB peripheral device); Sony 4K sensors ×2 confirmed from spec sheets |
| Thermal Solution | N/A — no public teardown found |
| Thermal Design Observations | Unknown. USB-powered at 60W; likely passive or light active cooling in bar housing. Lower thermal load than VB370A (60W vs 90W) due to absence of Android compute platform. |
| Key ICs | Sony 4K sensors ×2 (confirmed); ISP, audio codec, PMIC unconfirmed |
| Build Quality | N/A — no teardown available. Similar bar form factor to VB370A; likely shared mechanical/optical platform without the Android compute module. |
| Source | N/A (no public teardown found as of 2026-05-12) |

---

## VB350 vs VB370A Comparison (AVer internal lineup)

| Dimension | VB350 | VB370A |
|---|---|---|
| Built-in OS | None (USB peripheral) | Android 13 (standalone) |
| Requires PC | Yes | No |
| Camera | Dual Sony 4K, 18× | Dual Sony 4K, 18× |
| Mic | 14 beamforming, 10m | 14 beamforming, 10m |
| HDMI Out | 1× (via USB adapter) | 2× native |
| Power | 60W | 90W |
| PTZ Presets | 10 | 128 |
| Wireless | N/A | 802.11ac + BLE |
| Price tier | Lower | Higher |

---

## Notes & Gaps

- **No built-in OS**: VB350 is a USB peripheral — it requires an external PC running Zoom/Teams software. This is the primary differentiator vs VB370A (Android standalone).
- **Wireless**: No built-in Wi-Fi or Bluetooth. Ethernet via RJ-45 is the network connection for IP control (VISCA), not for conferencing stream.
- **Environmental specs**: Not publicly listed in available sources — marked as N/A.
- **Dimensions source**: 791mm × 128mm × 126mm from B&H listing (J&M Eastern / search result); package dimensions 872 × 197 × 260mm, pkg weight 7.4 kg.
- **Teardown**: No public teardown found. Lower-risk thermal profile than VB370A given no compute SoC inside.
