# AVer VB370A — VC Device Benchmark Report

**Category**: Room Bar
**Date Researched**: 2026-05-12
**Data Sources**:
- [Wavesat product page](https://wavesat.net/product/aver-vb370a-android-based-4k-dual-lens-video-bar/) — primary spec source
- [AVer USA Datasheet PDF](https://averusa.com/business/downloads/datasheet-brochure/vb370a-datasheet.pdf)
- [Qualcomm IoT Device Finder](https://www.qualcomm.com/products/internet-of-things/device-finder/vb370a) — SoC platform confirmation
- [AVer official product page](https://communication.aver.com/model/vb370a)

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | W: 790mm × H: 129mm × D: 138mm |
| Weight | 3.7 ± 0.1 kg |
| Camera System | **Dual-lens:** (1) PTZ — 1/2.8" Sony 4K Exmor CMOS 8MP, 4K/30fps, 92° diagonal / 81° H / 50° V FOV, 18x total zoom (4.5x optical + 4x digital), pan ±141°, tilt 78°, 128 presets; (2) Fixed — 1/2.5" Sony 4K Exmor CMOS 8MP, 4K/30fps, 120° diagonal / 110° H / 75° V FOV; Min illumination 0.46 lux (F1.6); S/N ≥50 dB |
| Audio System | Speaker: 96 dB SPL peak at 0.5m, 81±2 dB sensitivity, 110Hz–20kHz; Mic: 14 beamforming elements, 10m pickup range, -35±1 dB FS, 100Hz–12kHz; AEC, AGC, Noise Suppression, Audio Fence; RJ-45 audio line in/out |
| Microphone | Yes — 14 beamforming MEMS elements, 10m pickup range; expandable with up to 2 daisy-chain mics + 1 expansion speakerphone |
| Video Inputs | 1× HDMI in; 3× USB-A; 1× USB 3.0 Type-C (DisplayPort alt mode); RJ-45 Ethernet; RJ-45 audio line in |
| Video Outputs | 2× HDMI out (dual screen simultaneous) |
| Supported Apps | Zoom Rooms (embedded, certified), Microsoft Teams, Google Meet, Skype, Cisco WebEx, RingCentral, BlueJeans, GoToMeeting, TrueConf, Adobe Connect, Fuze, Intel Unite, Vidyo, WebRTC, and more |
| Wireless | 802.11 a/b/g/n/ac Wi-Fi; Bluetooth Low Energy |
| Supported OS | Android 13 (built-in; no external PC required) |
| Environmental | Operating: 0–40°C; Humidity: 20–80%; Storage: -20–60°C; Indoor use only |
| Power Supply | AC 100–240V → DC 12V / 6.25A |
| Power Consumption | 90W |
| Mounting | Wall-mount bracket (included); Kensington security slot; Tripod screw (1/4") |
| Special Features | AI smart composition; Auto-framing; Voice tracking (firmware upgrade); Audio fence; Dual 4K lens simultaneous capture; Onboard AI processing; VISCA/CGI over IP; IR remote; AVer CP10 G2 compatible |

### Dynamic Columns (Room Bar)

| Field | Value |
|---|---|
| PTZ Pan/Tilt Range | 141° pan / 78° tilt; 128 preset positions |
| PTZ Zoom | 4.5× optical + 4× digital = 18× total |
| Fixed Lens FOV | 120° diagonal / 110° H / 75° V |
| Dual Screen Output | 2× HDMI out (simultaneous) |
| Control Methods | IR remote; VISCA/CGI over IP; USB; AVer CP10 G2 touch panel |
| Mic Expandability | Up to 2× daisy-chain mics + 1× expansion speakerphone |
| Certifications | Zoom Rooms certified; Android 13 |
| SoC Platform | Qualcomm (exact model undisclosed; confirmed via qualcomm.com IoT device finder) |

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | Qualcomm SoC (model not publicly disclosed; device listed on qualcomm.com IoT device finder — likely QCS series). Sony IMX sensors (inferred from Exmor branding on both lenses). |
| Thermal Solution | N/A — no public teardown found |
| Thermal Design Observations | Unknown. Runs Android 13 with onboard AI processing and dual 4K ISP — active thermal management (fan or heat pipe) likely present in the bar housing. 90W TDP is significant for a bar form factor. |
| Key ICs | Qualcomm SoC (undisclosed model); Sony IMX sensors ×2 (inferred); audio codec and PMIC unconfirmed |
| Build Quality | N/A — no teardown available. Bar form factor with wall-mount bracket; likely modular PTZ camera head assembly. |
| Source | N/A (no public teardown found as of 2026-05-12) |

---

## Competitive Context (vs. Logitech)

| Dimension | AVer VB370A | Logitech Rally Bar (reference) |
|---|---|---|
| Camera | Dual-lens (fixed 120° + PTZ 18×) | Single-lens, 4K, 90° H, 15× zoom |
| Mic elements | 14 beamforming, 10m range | 10 beamforming, ~7.5m range |
| OS | Android 13 embedded | Android embedded |
| Power | 90W | ~130W |
| PTZ | Yes (18× total) | No |
| Dual screen out | Yes (2× HDMI) | Yes |

---

## Notes & Gaps

- **SoC model**: AVer does not publicly disclose the specific Qualcomm chip. Qualcomm device finder listing confirms the platform. Likely QCS6490 or QCS8550 based on Android 13 + AI feature set — unconfirmed.
- **Teardown**: No public teardown as of 2026-05-12. 90W at a bar form factor suggests non-trivial thermal design.
- **Microphone count discrepancy**: Wavesat (primary source) says 14 beamforming elements; VideoConferenceGear says "up to 6 meters" — likely refers to a different variant (VB350/VB342). Used 10m from Wavesat as primary.
- **Voice Tracking**: Listed as requiring a future firmware upgrade — may not be available at time of purchase.
