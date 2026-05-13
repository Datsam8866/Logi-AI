# -*- coding: utf-8-sig -*-
"""
批次插入 12 個競品 benchmark 資料（2026-05-13）
並生成對應的 .md 報告至 reports/
"""
import sqlite3, json, os

BASE   = os.path.dirname(os.path.abspath(__file__))
DB     = os.path.join(BASE, 'vc_benchmark.db')
RDIR   = os.path.join(BASE, 'reports')
TODAY  = '2026-05-13'

os.makedirs(RDIR, exist_ok=True)

DEVICES = [
  {
    "product_name": "Cisco Room Kit Pro",
    "category": "AIO System",
    "dimensions": "Codec Pro: 436 × 231 × 66 mm (W×D×H), 3.3 kg; Quad Camera: 950 × 103 × 120 mm, 4.8 kg",
    "weight": "Codec: 3.3 kg; Quad Camera: 4.8 kg",
    "camera_system": "Cisco Quad Camera — 80 MP total (4-lens: 1× 83° main + 3× 50° telephoto), 4K60, 7× digital zoom; simultaneous multi-lens capture for Frames AI mode",
    "audio_system": "External mic connectivity via Euroblock/Phoenix connectors; machine-learning noise removal; built-in speaker; PoE-powered accessories",
    "microphone_presence": "No built-in mic — requires external Cisco mics or third-party audio system via analog/AES67",
    "video_inputs": "3× HDMI in (4K30, 1× HDCP 1.4); 1× USB-C in (4K30, 15 W charging out)",
    "video_outputs": "Up to 3× HDMI out (3 simultaneous displays)",
    "supported_applications": "Cisco Webex (native); Microsoft Teams Rooms; Zoom; Google Meet (BYOD/certified)",
    "wireless_sharing": "Wi-Fi 6 (802.11ax); Bluetooth 5.0",
    "supported_os": "Cisco RoomOS; Microsoft Teams Rooms on Android",
    "environmental_specs": "Standard commercial indoor; 0–40°C operating",
    "power_supply": "External PSU; PoE++ IEEE 802.3bt per port (max 90 W combined for 4 ports)",
    "power_consumption": "—",
    "mounting_options": "1.5RU rack mount; optional rack-mounting accessory; Codec Pro standalone table placement",
    "special_features": "AI Frames (equitable multi-person framing); Speaker Tracking; People Count analytics; PresenterTrack; RoomOS cloud/on-prem registration",
    "dynamic_columns": json.dumps({
        "Room Size":        "Extra-large boardroom / auditorium / custom AV integration",
        "SoC (Codec)":      "Proprietary Cisco/Webex compute platform (not publicly disclosed)",
        "Display Support":  "Up to 3 external screens",
        "Camera Inputs":    "1× HDMI camera in; 1× USB camera in",
        "Audio I/O":        "4× Euroblock mic in; 2× Euroblock line out; Ethernet (AES67); analog",
        "Certifications":   "Webex cloud; MTR; BYOD"
    }),
    "teardown_pcb": "No public teardown found — Cisco proprietary compute platform (NVIDIA GPU confirmed in Room Kit EQ; likely similar lineage)",
    "teardown_thermal": "N/A — no public teardown found",
    "teardown_thermal_design": "1.5RU metal chassis; rack-mount form factor suggests active cooling (internal fan likely)",
    "teardown_key_ics": "Cisco proprietary SoC; Sony/OV image sensors (inferred); Codec Pro handles encoding/AI",
    "teardown_build_quality": "N/A — no public teardown",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/webex-room-series/datasheet-c78-741052.html",
    "notes": "Datasheet URL returned 403 — specs sourced from web search aggregation. Codec Pro is the original (Gen 1); Gen 2 = Codec Pro G2 (updated SoC). Weight includes Quad Camera bundle."
  },
  {
    "product_name": "Cisco Room Kit EQ",
    "category": "AIO System",
    "dimensions": "Codec EQ: 472 × 203 × 43 mm (W×D×H), 1.64 kg; Quad Camera: 950 × 103 × 120 mm",
    "weight": "Codec EQ: 1.64 kg; Quad Camera: 4.8 kg",
    "camera_system": "Cisco Quad Camera (80 MP, 4-lens: 83° main + 3× 50° telephoto), 4K60, 7× digital zoom; Frames AI mode; UHD image processing",
    "audio_system": "Built-in speaker; ML noise removal; distraction-free audio; supports directional Cisco mics + third-party systems via PoE/Ethernet",
    "microphone_presence": "No built-in mic — external directional Cisco mics or third-party audio required",
    "video_inputs": "3× HDMI in (4K30, 1× HDCP 1.4); 1× USB-C in (4K30, 15 W charging)",
    "video_outputs": "Up to 3× HDMI out (3 simultaneous displays)",
    "supported_applications": "Cisco Webex; Microsoft Teams Rooms; Zoom; Google Meet",
    "wireless_sharing": "Wi-Fi 6E; Bluetooth 5.2",
    "supported_os": "Cisco RoomOS; Microsoft Teams Rooms",
    "environmental_specs": "0–40°C operating; standard commercial indoor",
    "power_supply": "PoE++ IEEE 802.3bt (4 ports, max 90 W combined); external PSU option",
    "power_consumption": "—",
    "mounting_options": "Half-rack (1U) bracket optional; flat surface placement; camera mounted above/below display",
    "special_features": "NVIDIA AI chipset; Frames equitable framing; Speaker Tracking; People Count analytics; PresenterTrack; 4K content wireless sharing; USB passthrough for laptop",
    "dynamic_columns": json.dumps({
        "Room Size":        "Large conference room / boardroom / training room / auditorium",
        "SoC (Codec)":      "NVIDIA (specific model not publicly disclosed)",
        "Display Support":  "Up to 3 external screens",
        "Audio I/O":        "4× PoE Ethernet ports (cameras/mics/accessories); HDMI ARC; analog",
        "USB Passthrough":  "Yes — laptop integration",
        "Certifications":   "Cisco Webex; MTR on Android"
    }),
    "teardown_pcb": "NVIDIA AI chipset confirmed in datasheet; specific GPU/SoC model not disclosed publicly",
    "teardown_thermal": "N/A — no public teardown found",
    "teardown_thermal_design": "Low-profile half-rack chassis (43 mm H); likely passive or fan-assisted; NVIDIA chipset implies non-trivial thermal budget",
    "teardown_key_ics": "NVIDIA SoC (undisclosed); Cisco Quad Camera ISP; audio codec unconfirmed",
    "teardown_build_quality": "N/A — no public teardown",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/spark-room-kit-series/room-kit-eq-ds.html",
    "notes": "Cisco confirms NVIDIA chipset in marketing — model not specified. Codec EQ is newer/lighter than Codec Pro. Quad Camera weight sourced from earlier Quad Camera CAD data."
  },
  {
    "product_name": "Cisco Room Bar Pro",
    "category": "Room Bar",
    "dimensions": "~960 × 109 × 89 mm (W×H×D), ~4.5 kg",
    "weight": "~4.5 kg (9.85 lbs)",
    "camera_system": "Dual camera — 48 MP wide (112° HFOV) + 48 MP tele (70° HFOV) = 96 MP total; 1080p30 video; 4K content; AI-directed framing",
    "audio_system": "16-element beamforming mic array; 3-channel loudspeaker (stereo + center, directional in Webex); spatial audio; ML noise removal",
    "microphone_presence": "Yes — 16 MEMS elements built-in, beamforming",
    "video_inputs": "USB-C (DisplayPort alt mode); HDMI in; Ethernet",
    "video_outputs": "Up to 3× HDMI out",
    "supported_applications": "Cisco Webex (native); Microsoft Teams Rooms (Android); Zoom; Google Meet",
    "wireless_sharing": "Wi-Fi 6E (802.11ax 6 GHz); Bluetooth 5",
    "supported_os": "Cisco RoomOS; Microsoft Teams Rooms on Android",
    "environmental_specs": "0–40°C operating; standard commercial indoor",
    "power_supply": "Built-in auto-sensing PSU (100–240 V)",
    "power_consumption": "—",
    "mounting_options": "Wall mount; display/monitor mount (above or below); VESA compatible",
    "special_features": "NVIDIA AI chipset; dual-lens AI framing; spatial directional audio; >50% post-consumer recycled plastic; smart energy consumption; USB-C with charging",
    "dynamic_columns": json.dumps({
        "Room Size":        "Medium conference room",
        "SoC":              "NVIDIA (specific model not publicly disclosed)",
        "Display Support":  "Up to 3 screens",
        "Sustainability":   ">50% post-consumer recycled (PCR) plastic",
        "Certifications":   "Cisco Webex; MTR on Android; Zoom certified",
        "VESA Mount":       "Yes"
    }),
    "teardown_pcb": "NVIDIA AI chipset confirmed in Cisco marketing; model not disclosed",
    "teardown_thermal": "N/A — no public teardown found",
    "teardown_thermal_design": "Bar form factor ~960 mm wide; NVIDIA chipset suggests active or heat-pipe cooling within housing",
    "teardown_key_ics": "NVIDIA SoC (undisclosed); dual 48 MP image sensors (brand unconfirmed); audio codec unconfirmed",
    "teardown_build_quality": "N/A — no public teardown; >50% PCR plastic housing noted",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/webex-room-series/room-bar-pro-ds.html",
    "notes": "Dimensions ~approximate (converted from inches: 37.8 × 4.3 × 3.5 in). Cisco confirms NVIDIA but does not specify model. Weight from reseller listings."
  },
  {
    "product_name": "Huddly L1",
    "category": "PTZ Camera",
    "dimensions": "122 × 82 × 53 mm (W×D×H)",
    "weight": "600 g",
    "camera_system": "20.3 MP 1\" CMOS 6K sensor; 1080p30 / 720p30 output; 92° HFOV / 65° VFOV / 103° DFOV; f/2.9; 5× digital zoom; 180° auto-flip; wide-angle fixed lens (no optical PTZ)",
    "audio_system": "N/A — no built-in speaker or mic",
    "microphone_presence": "No",
    "video_inputs": "N/A",
    "video_outputs": "RJ45 (PoE, data via Ethernet); USB 3.2 Gen 1 Type-A via included USB adapter (also USB-C cable included)",
    "supported_applications": "Microsoft Teams certified; Zoom; Google Meet; plug-and-play USB (any platform)",
    "wireless_sharing": "N/A",
    "supported_os": "Plug-and-play — Windows, macOS, Linux, ChromeOS (USB UVC class)",
    "environmental_specs": "Standard indoor; 0–40°C operating",
    "power_supply": "Power over Ethernet (PoE IEEE 802.3af/at); or external AC/DC 5 V / 4 A adapter",
    "power_consumption": "~14 W (PoE); max 15 W",
    "mounting_options": "Includes wall-mount adapter; tripod 1/4\" screw; above/below display clip",
    "special_features": "Huddly VPU with neural compute engine; AI smart framing (software-based pan/tilt/zoom); room analytics; people count; 6K sensor for digital crop precision; MS Teams certified",
    "dynamic_columns": json.dumps({
        "Room Size":            "Medium to large meeting rooms",
        "Pan/Tilt Range":       "N/A (no mechanical PTZ — AI digital framing only)",
        "Optical Zoom":         "N/A (digital only, 5×)",
        "Connection Method":    "PoE Ethernet (primary); USB via included adapter (secondary)",
        "Cable Length":         "Up to 100 m Ethernet",
        "FCC ID":               "2ALRZ002",
        "Certifications":       "Microsoft Teams; CE; FCC; RoHS"
    }),
    "teardown_pcb": "Huddly proprietary VPU (Vision Processing Unit) with neural compute engine — FCC ID 2ALRZ002 internal photos exist but component labels not publicly detailed",
    "teardown_thermal": "N/A — no detailed public teardown; aluminum body likely serves as passive heatsink",
    "teardown_thermal_design": "Aluminum body construction — passive thermal dissipation through housing; no fan expected at 14 W TDP",
    "teardown_key_ics": "Huddly VPU (neural compute; vendor unconfirmed); 1\" CMOS sensor (brand unconfirmed); PoE controller IC",
    "teardown_build_quality": "Aluminum body; compact 122×82×53 mm; FCC internal photos accessible via fccid.io/2ALRZ002",
    "teardown_source": "FCC ID filing 2ALRZ002 — internal photos available at fccid.io; no iFixit/YouTube teardown found (as of 2026-05-13)",
    "datasheet_url": "https://www.huddly.com/conference-cameras/l1/",
    "notes": "Note: Huddly L1 is classified as PTZ Camera (standalone, no mic) but is technically a fixed wide-angle camera with AI-based digital framing — not mechanical PTZ. Category reflects 'camera-only' role in the taxonomy."
  },
  {
    "product_name": "Neat Bar Generation 2",
    "category": "Room Bar",
    "dimensions": "198 × 127 × 42 mm (W×D×H)",
    "weight": "520 g",
    "camera_system": "50 MP; f/2.8; 113° HFOV; 4× digital zoom; distortion correction; noise reduction; chromatic aberration correction; auto white balance; hardware-accelerated encode/decode; 1080p30 video; 4K30 / 1080p60 content",
    "audio_system": "5 mics + 4 tracking/sensor mics in end-fire array; opposing full-range drivers (vibration cancellation); echo cancellation; noise suppression; AGC; dereverberation",
    "microphone_presence": "Yes — 9 mics total (5 primary + 4 tracking), end-fire array",
    "video_inputs": "HDMI in (content sharing); USB-C",
    "video_outputs": "Up to 2× HDMI out",
    "supported_applications": "Microsoft Teams Rooms; Zoom Rooms",
    "wireless_sharing": "Wi-Fi 6; Bluetooth 5.0",
    "supported_os": "Neat OS (proprietary Android-based)",
    "environmental_specs": "0–35°C operating; 10–90% RH; -20–60°C storage",
    "power_supply": "100–240 V ~50/60 Hz 0.5 A (built-in PSU)",
    "power_consumption": "Network standby <8 W (after 20 min)",
    "mounting_options": "Wall/display mount above or below 1–2 monitors; automatic realignment on reorientation",
    "special_features": "Ultrasonic auto-wakeup/sleep; orientation sensor (accelerometer); ambient light sensor; compact 520 g form; automatic people framing; hardware video acceleration",
    "dynamic_columns": json.dumps({
        "Room Size":        "Small to medium, ≤10 people",
        "SoC":              "Not publicly disclosed (Neat proprietary platform)",
        "Display Support":  "Up to 2 screens",
        "Auto-Realignment": "Yes — accelerometer detects mount orientation",
        "Certifications":   "MTR; Zoom Rooms",
        "Form Factor Note": "Lightest bar in benchmark at 520 g"
    }),
    "teardown_pcb": "N/A — no public teardown found; Neat uses proprietary SoC platform",
    "teardown_thermal": "N/A — no public teardown",
    "teardown_thermal_design": "Ultra-compact 42 mm H form factor; passive thermal design likely; standby <8 W suggests low TDP",
    "teardown_key_ics": "Neat proprietary SoC (AI video/audio processing); 50 MP image sensor (brand unconfirmed); audio codec unconfirmed",
    "teardown_build_quality": "N/A — no public teardown; very compact and light (520 g) chassis",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://neat.no/bar-2/",
    "notes": "Bar 2 is the second generation (Gen 2). Significantly lighter and smaller than Neat Bar Pro. Neat OS is proprietary and not Android AOSP open platform."
  },
  {
    "product_name": "Jabra PanaCast 50 Video Bar System",
    "category": "Room Bar",
    "dimensions": "650 × 125 × 80 mm (W×D×H)",
    "weight": "2200 g",
    "camera_system": "3× 4K 13 MP cameras (39 MP total); 180° HFOV / 54° VFOV panoramic; 3840×1080 @ 30 fps panoramic 4K; 6× lossless digital zoom (IntelliZoom); Virtual Director AI auto-framing",
    "audio_system": "8-element beamforming mic array; 4 speakers — 2× 2\" (50 mm) woofer + 2× 3/4\" (20 mm) tweeter; 80 Hz–20 kHz; certified for rooms up to 4.5 m × 6 m; 100 Hz–16 kHz mic; -37 dBFS mic sensitivity",
    "microphone_presence": "Yes — 8 MEMS beamforming elements, rooms up to 4.5 m × 6 m",
    "video_inputs": "HDMI in; USB-C",
    "video_outputs": "HDMI out",
    "supported_applications": "Microsoft Teams Rooms (native); Zoom Rooms; Google Meet; RingCentral",
    "wireless_sharing": "Wi-Fi 5 (802.11ac); Bluetooth 5.0",
    "supported_os": "Android (AOSP, Jabra suite) / MTR on Android / Zoom Rooms on Android",
    "environmental_specs": "0–40°C operating; 20–80% RH; standard indoor",
    "power_supply": "100–240 V, 12 V / 5 A (60 W external PSU)",
    "power_consumption": "60 W (max)",
    "mounting_options": "Wall mount; display mount above or below; included wall-mount hardware",
    "special_features": "180° panoramic view (3-camera stitch); IntelliZoom (6× lossless); Virtual Director AI; Whiteboard Mode; BrightSense ambient sensor; Jabra Panoramic 4K video",
    "dynamic_columns": json.dumps({
        "Room Size":             "Medium rooms (up to 4.5 m × 6 m)",
        "SoC":                   "Qualcomm (specific model not publicly disclosed)",
        "Display Support":       "1 external screen (HDMI out)",
        "Panoramic Coverage":    "180° HFOV — 3-camera stitch",
        "Whiteboard Detection":  "Yes (BrightSense + Whiteboard Mode)",
        "Certifications":        "MTR; Zoom Rooms; Google Meet certified",
        "Content Sharing":       "HDMI in + USB-C content in"
    }),
    "teardown_pcb": "N/A — no public teardown found; Qualcomm platform confirmed by industry sources",
    "teardown_thermal": "N/A — no public teardown",
    "teardown_thermal_design": "650 mm bar housing, 60 W TDP — likely fan-assisted or heat-pipe cooling for the 3-camera ISP + Qualcomm SoC",
    "teardown_key_ics": "Qualcomm SoC (undisclosed model); 3× 13 MP image sensors (brand unconfirmed); audio codec for 4-speaker + 8-mic system",
    "teardown_build_quality": "N/A — no public teardown",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.jabra.com/business/video-conferencing/jabra-panacast-50-video-bar-system",
    "notes": "Specs from official Jabra tech spec PDF (RevA). 180° panoramic via 3-camera stitching is key differentiator vs single/dual-lens bars. VBS (Video Bar System) includes Android compute built-in; separate 'bar-only' SKU also exists."
  },
  {
    "product_name": "Neat Bar Pro",
    "category": "Room Bar",
    "dimensions": "890 × 80 × 80 mm (W×H×D)",
    "weight": "3100 g",
    "camera_system": "Dual 100 MP total — Wide: 50 MP f/2.8 113° HFOV; Tele: 50 MP f/1.8 70° HFOV; 16× hybrid zoom; 1080p30 video; 4K30 / 1080p60 content; AI auto-framing",
    "audio_system": "Pyramid-shaped 16-mic array; subwoofer with 2× opposing drivers (vibration cancel) + 3× full-range speakers; stereo direct sound; Neat Audio processing (no double-talk/echo)",
    "microphone_presence": "Yes — 16 mics, pyramid-shaped array",
    "video_inputs": "HDMI in (content); USB-C in",
    "video_outputs": "3× HDMI out (up to 3 screens; 3rd screen Zoom only)",
    "supported_applications": "Microsoft Teams Rooms; Zoom Rooms",
    "wireless_sharing": "Wi-Fi 6; Bluetooth 5.0",
    "supported_os": "Neat OS (proprietary)",
    "environmental_specs": "0–40°C operating; standard indoor",
    "power_supply": "100–240 V ~50/60 Hz 1.2 A (built-in PSU)",
    "power_consumption": "—",
    "mounting_options": "Table stand; wall/display mount above or below 1–3 screens; automatic orientation realignment",
    "special_features": "Ultrasonic auto-wakeup/sleep; accelerometer (auto-flip); ambient light sensor; USB-C input; dual-lens 16× hybrid zoom; vibration-cancelling speaker design",
    "dynamic_columns": json.dumps({
        "Room Size":        "Medium to large, >10 people",
        "SoC":              "Not publicly disclosed (Neat proprietary platform)",
        "Display Support":  "Up to 3 screens (3rd display Zoom Rooms only)",
        "Dual-Lens":        "Yes — 50 MP wide (113°) + 50 MP tele (70°), 16× hybrid zoom",
        "Speaker Design":   "Opposing drivers in subwoofer for vibration cancellation",
        "Certifications":   "MTR; Zoom Rooms"
    }),
    "teardown_pcb": "N/A — no public teardown found; Neat proprietary SoC platform",
    "teardown_thermal": "N/A — no public teardown",
    "teardown_thermal_design": "890 mm bar, 1.2 A @ 240 V (~288 W max draw but typical much lower); dual-lens + 16-mic array ISP suggests active compute; no fan noise reports in reviews",
    "teardown_key_ics": "Neat proprietary SoC; 2× 50 MP image sensors (brand unconfirmed); high-end audio DSP for 16-mic + 4-speaker system",
    "teardown_build_quality": "N/A — no public teardown; premium build noted in reviews; all-black aluminum/plastic composite",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://neat.no/bar-pro/",
    "notes": "Neat Bar Pro vs Neat Bar Gen2: Pro is ~4× longer (890 vs 198 mm), heavier (3.1 vs 0.52 kg), and targets larger rooms (>10 pax). Both run Neat OS. 3rd HDMI out requires Zoom Rooms — not available on MTR."
  },
  {
    "product_name": "Poly Studio X72",
    "category": "Room Bar",
    "dimensions": "840 × 136 × 118 mm (W×H×D)",
    "weight": "—",
    "camera_system": "Dual 4K 20 MP cameras — Wide: 120° HFOV / 140° DFOV; Narrow: 70° HFOV / 78° DFOV; 2160p UHD; 7.3× digital zoom; integrated lens privacy; DirectorAI: Group/People/Speaker/Presenter framing",
    "audio_system": "2× MEMS + 2× second-order beamforming mics; 25 ft (7.6 m) pickup; 2× 20 W RMS mid speakers; innovative acoustic chamber design; NoiseBlockAI; Acoustic Fence",
    "microphone_presence": "Yes — 4 mics (2 MEMS + 2 second-order), beamforming",
    "video_inputs": "HDMI in; USB-C in (laptop connection)",
    "video_outputs": "Up to 3× HDMI out",
    "supported_applications": "Microsoft Teams Rooms; Zoom Rooms; Poly Video Mode (native); Webex",
    "wireless_sharing": "Wi-Fi 6 (802.11ax); Bluetooth 5.0; wireless content sharing",
    "supported_os": "Poly OS (Android-based)",
    "environmental_specs": "0–40°C operating; 10–90% RH non-condensing",
    "power_supply": "—",
    "power_consumption": "—",
    "mounting_options": "Wall/display mount; VESA compatible; display clip; table stand",
    "special_features": "Qualcomm Snapdragon 865 SoC; dual-lens AI director; NoiseBlockAI; Acoustic Fence; People Count; local management via Poly Lens; 4K UHD video",
    "dynamic_columns": json.dumps({
        "Room Size":        "Large to extra-large boardroom",
        "SoC":              "Qualcomm Snapdragon 865",
        "Display Support":  "Up to 3 screens",
        "Dual-Lens":        "Yes — 120° wide + 70° narrow, AI-switched",
        "Mic Pickup":       "Up to 7.6 m (25 ft)",
        "Speaker Power":    "2× 20 W RMS",
        "VESA Mount":       "Yes",
        "Certifications":   "MTR; Zoom Rooms; Poly Video Mode native"
    }),
    "teardown_pcb": "Qualcomm Snapdragon 865 confirmed via Poly product documentation; FCC ID M72-STX72R — internal photos may be available at fcc.report",
    "teardown_thermal": "N/A — no detailed public teardown; FCC filing M72-STX72R may include internal photos",
    "teardown_thermal_design": "840 mm bar with Snapdragon 865 (10 nm) + dual 4K ISP — active cooling (fan) likely required; no specific teardown data",
    "teardown_key_ics": "Qualcomm Snapdragon 865; dual 4K 20 MP image sensors (brand unconfirmed); Poly audio DSP",
    "teardown_build_quality": "N/A — no public teardown; premium bar for large rooms",
    "teardown_source": "FCC ID M72-STX72R (internal photos may exist); no iFixit/YouTube teardown found (as of 2026-05-13)",
    "datasheet_url": "https://www.hp.com/us-en/poly/video-conferencing/all-in-one/studio-x72.html",
    "notes": "Successor to Poly Studio X70 (upgraded from Snapdragon 835 → 865). Weight not found in public datasheets. FCC internal photos may reveal heatsink/fan design."
  },
  {
    "product_name": "Poly Studio X52",
    "category": "Room Bar",
    "dimensions": "770 × 115 × 103 mm (W×H×D)",
    "weight": "2540 g (5.6 lbs)",
    "camera_system": "20 MP 4K; 95° HFOV / 110° DFOV; 5× digital zoom; 4K30 video; DirectorAI: Group Framing / People Framing (up to 6) / Speaker Framing / Presenter Tracking",
    "audio_system": "2× MEMS + 2× second-order beamforming mics; 20 ft (6 m) pickup; dual stereo speakers; full-duplex; NoiseBlockAI; Acoustic Fence",
    "microphone_presence": "Yes — 4 mics (2 MEMS + 2 second-order)",
    "video_inputs": "HDMI in; USB-C in (laptop)",
    "video_outputs": "HDMI out (up to 2 displays)",
    "supported_applications": "Microsoft Teams Rooms; Zoom Rooms; Poly Video Mode; Webex",
    "wireless_sharing": "Wi-Fi 6; Bluetooth 5.0; wireless content sharing",
    "supported_os": "Poly OS (Android-based)",
    "environmental_specs": "0–40°C operating; 10–90% RH non-condensing",
    "power_supply": "Auto-sensing 100–240 V ~50/60 Hz",
    "power_consumption": "Operating: 25 W; Idle/Sleep: 8 W",
    "mounting_options": "Wall/display mount; VESA compatible; display clip; table stand",
    "special_features": "Poly DirectorAI; NoiseBlockAI; Acoustic Fence; People Count; 4K single-lens; VESA mount; Poly Lens management",
    "dynamic_columns": json.dumps({
        "Room Size":        "Medium conference room (up to ~15 people)",
        "SoC":              "Qualcomm (specific model not publicly disclosed for X52)",
        "Display Support":  "Up to 2 screens",
        "Mic Pickup":       "Up to 6 m (20 ft)",
        "Speaker Config":   "Dual stereo",
        "VESA Mount":       "Yes",
        "Certifications":   "MTR; Zoom Rooms; Poly Video Mode native"
    }),
    "teardown_pcb": "Qualcomm platform (Poly X-series family uses Qualcomm); specific SoC for X52 not publicly confirmed",
    "teardown_thermal": "N/A — no public teardown",
    "teardown_thermal_design": "Operating 25 W, Idle 8 W — relatively low TDP; passive or small fan likely; 770 mm bar chassis",
    "teardown_key_ics": "Qualcomm SoC (model unconfirmed); 20 MP 4K image sensor (brand unconfirmed); Poly audio DSP",
    "teardown_build_quality": "N/A — no public teardown",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.hp.com/us-en/poly/video-conferencing/all-in-one/studio-x52.html",
    "notes": "Power consumption: 37 VA @120 V; 25 W operating; 8 W idle. X72 uses Snapdragon 865 (confirmed); X52 SoC not confirmed but likely same family."
  },
  {
    "product_name": "Yealink MeetingBar A30",
    "category": "Room Bar",
    "dimensions": "700 × 121 × 98 mm (W×D×H)",
    "weight": "4750 g (bar only, A30-010)",
    "camera_system": "Dual-eye system — (1) 4K panoramic/context camera (120° DFOV); (2) Optical 10× hybrid zoom main camera; AI auto-framing; Speaker Tracking; Smart Gallery (Zoom); simultaneous dual-stream",
    "audio_system": "8 MEMS mic array; beamforming; AI noise reduction; full-duplex; AEC; de-reverberation; AGC; expandable with external mics; Standby: 14.9 W, Average: 12.5 W",
    "microphone_presence": "Yes — 8 MEMS elements built-in; expandable",
    "video_inputs": "HDMI in; USB-C in",
    "video_outputs": "Up to 2× HDMI out",
    "supported_applications": "Microsoft Teams Rooms; Zoom Rooms",
    "wireless_sharing": "Wi-Fi 6 (802.11ax); Bluetooth 5.0",
    "supported_os": "Android 13",
    "environmental_specs": "0–40°C operating; -30–70°C storage",
    "power_supply": "External AC/DC adapter (100–240 V input)",
    "power_consumption": "Average: 12.5 W; Standby: 14.9 W",
    "mounting_options": "Wall/display mount; ceiling mount option; bracket included",
    "special_features": "Qualcomm Snapdragon 845 SoC; dual-eye camera (panoramic overview + optical zoom); Smart Gallery; optional CTP18 touch panel; enterprise management via Yealink Device Management",
    "dynamic_columns": json.dumps({
        "Room Size":        "Medium rooms (9–12 people)",
        "SoC":              "Qualcomm Snapdragon 845",
        "Display Support":  "Up to 2 screens",
        "Dual-Eye Camera":  "Yes — 120° context + optical 10× zoom main camera",
        "Mic Expandability":"Yes — external mic expansion supported",
        "Certifications":   "MTR; Zoom Rooms certified",
        "Touch Panel":      "Optional CTP18 (A30-020 SKU)"
    }),
    "teardown_pcb": "Qualcomm Snapdragon 845 confirmed in Yealink product documentation",
    "teardown_thermal": "N/A — no public teardown",
    "teardown_thermal_design": "700 mm bar housing; Snapdragon 845 (10 nm LPP) generates moderate heat; 12.5 W average power suggests passive or small fan cooling",
    "teardown_key_ics": "Qualcomm Snapdragon 845; dual-camera ISP (Qualcomm Spectra 280); audio codec for 8-mic beamforming",
    "teardown_build_quality": "N/A — no public teardown",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.yealink.com/en/product-detail/microsoft-teams-rooms-meetingbar-a30",
    "notes": "Weight varies by SKU: A30-010 (bar only) = 4.75 kg; A30-020 (bar + CTP18 panel) = 7.05 kg. Standby power (14.9 W) > average power (12.5 W) is unusual — may reflect display controller idle vs. active encoding."
  },
  {
    "product_name": "Yealink MeetingBar A40",
    "category": "Room Bar",
    "dimensions": "650 × 80 × 62 mm (W×H×D)",
    "weight": "5540 g",
    "camera_system": "Dual 48 MP (96 MP total); 120° DFOV / 110° HFOV / 54° VFOV; f/2.2–f/2.4; 6× digital zoom; 4K60 max; 10-bit HDR; electronic gimbal; 9 preset positions; IntelliFocus; Auto Framing; Speaker Tracking; electric lens cap",
    "audio_system": "2× 10 W speakers (112 dBSPL @ 0.1 m; 100 Hz–16 kHz); 8 MEMS mic array; 6 m pickup (3 m full-duplex); supports 2× expansion mics; AI noise reduction; AEC; AGC",
    "microphone_presence": "Yes — 8 MEMS built-in; expandable to +2 external",
    "video_inputs": "HDMI in",
    "video_outputs": "Up to 2× HDMI out",
    "supported_applications": "Microsoft Teams Rooms; Zoom Rooms",
    "wireless_sharing": "Wi-Fi 6; Bluetooth 5.0",
    "supported_os": "Android 13",
    "environmental_specs": "0–40°C operating; standard indoor",
    "power_supply": "—",
    "power_consumption": "—",
    "mounting_options": "Wall/display mount; bracket included",
    "special_features": "Electronic gimbal (motorized horizontal sweep); 10-bit HDR imaging; electric lens cap (auto privacy); 4K60; dual 48 MP lenses; IntelliFocus AI",
    "dynamic_columns": json.dumps({
        "Room Size":            "Small to medium premium (≤15 people)",
        "SoC":                  "Not publicly confirmed (Android 13 platform)",
        "Display Support":      "Up to 2 screens",
        "Electronic Gimbal":    "Yes — motorized horizontal movement",
        "HDR":                  "10-bit wide dynamic range",
        "Lens Cap":             "Electric auto privacy shutter",
        "Mic Expandability":    "Yes — up to 2 external expansion mics",
        "Certifications":       "MTR; Zoom Rooms"
    }),
    "teardown_pcb": "N/A — SoC not publicly disclosed; Android 13 platform; likely Qualcomm or MediaTek",
    "teardown_thermal": "N/A — no public teardown",
    "teardown_thermal_design": "Compact 62 mm H chassis with electronic gimbal motor + dual 48 MP ISP; thermal headroom likely tight; active cooling possible",
    "teardown_key_ics": "SoC unknown; 2× 48 MP image sensors; 2× 10 W audio amplifier ICs; gimbal motor controller",
    "teardown_build_quality": "N/A — no public teardown; electric lens cap and gimbal indicate complex mechanical integration",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.yealink.com/en/product-detail/microsoft-teams-rooms-meetingbar-a40",
    "notes": "Key differentiators: electronic gimbal + 10-bit HDR + electric lens cap. Weight 5.54 kg is heavy for a 650 mm bar — likely driven by gimbal mechanism. SoC not confirmed publicly."
  },
  {
    "product_name": "Yealink MeetingBar A10",
    "category": "Room Bar",
    "dimensions": "380 × 55 × 55 mm (W×H×D)",
    "weight": "—",
    "camera_system": "4K single camera; 120° DFOV / 105° HFOV; 4× e-PTZ (electronic pan-tilt-zoom); electric privacy shutter; 1080p30 / 720p30 output; Auto Framing; Speaker Tracking; Smart Gallery (Zoom only)",
    "audio_system": "5 W speaker (8 W max); 210 Hz–20 kHz; 4 Ω; 93 dBSPL @ 3 W @ 0.5 m; 8 MEMS mic array; 4.5 m pickup (3.5 m HD quality); AI noise cancellation; AEC; AGC; echo cancellation; THD <5% @5 W / 1 kHz",
    "microphone_presence": "Yes — 8 MEMS built-in",
    "video_inputs": "N/A (no content input)",
    "video_outputs": "1× HDMI out",
    "supported_applications": "Microsoft Teams Rooms; Zoom Rooms",
    "wireless_sharing": "Wi-Fi; Bluetooth",
    "supported_os": "Android",
    "environmental_specs": "Standard indoor; 0–40°C",
    "power_supply": "External power adapter (included; 100–240 V)",
    "power_consumption": "—",
    "mounting_options": "Wall/display mount; bracket included",
    "special_features": "Electric privacy shutter; e-PTZ (digital pan/tilt/zoom); compact 380 mm; entry-level price point; Smart Gallery (Zoom only); AI noise cancellation",
    "dynamic_columns": json.dumps({
        "Room Size":         "Huddle room / small room / home office",
        "SoC":               "Not publicly disclosed",
        "Display Support":   "1 screen only (1× HDMI out)",
        "e-PTZ":             "4× electronic (digital) pan-tilt-zoom",
        "Privacy Shutter":   "Yes — electric auto-close",
        "Speaker Power":     "5 W rated / 8 W max",
        "Certifications":    "MTR; Zoom Rooms"
    }),
    "teardown_pcb": "N/A — SoC not publicly disclosed; entry-level Android platform",
    "teardown_thermal": "N/A — no public teardown",
    "teardown_thermal_design": "Ultra-compact 380 × 55 × 55 mm; entry-level TDP — passive cooling very likely",
    "teardown_key_ics": "SoC unknown; 4K image sensor; 8-MEMS mic array; 5 W speaker amp",
    "teardown_build_quality": "N/A — no public teardown; small and lightweight form factor for huddle rooms",
    "teardown_source": "N/A (no public teardown as of 2026-05-13)",
    "datasheet_url": "https://www.yealink.com/en/product-detail/microsoft-teams-rooms-meetingbar-a10",
    "notes": "Entry-level bar — 1× HDMI out only (no dual screen support). Smart Gallery available on Zoom Rooms only. Weight not found in public sources. Most compact Yealink bar at 380 mm."
  },
]

# ── DB Insert ──────────────────────────────────────────────────────────────
con = sqlite3.connect(DB)
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS devices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_name TEXT NOT NULL,
  category TEXT NOT NULL,
  dimensions TEXT, weight TEXT,
  camera_system TEXT, audio_system TEXT, microphone_presence TEXT,
  video_inputs TEXT, video_outputs TEXT, supported_applications TEXT,
  wireless_sharing TEXT, supported_os TEXT, environmental_specs TEXT,
  power_supply TEXT, power_consumption TEXT, mounting_options TEXT,
  special_features TEXT, dynamic_columns TEXT,
  teardown_pcb TEXT, teardown_thermal TEXT, teardown_thermal_design TEXT,
  teardown_key_ics TEXT, teardown_build_quality TEXT, teardown_source TEXT,
  datasheet_url TEXT, date_added TEXT, notes TEXT
)''')

inserted, skipped = [], []
for d in DEVICES:
    cur.execute('SELECT id FROM devices WHERE product_name=?', (d['product_name'],))
    if cur.fetchone():
        skipped.append(d['product_name'])
        continue
    cur.execute('''INSERT INTO devices
      (product_name,category,dimensions,weight,camera_system,audio_system,
       microphone_presence,video_inputs,video_outputs,supported_applications,
       wireless_sharing,supported_os,environmental_specs,power_supply,
       power_consumption,mounting_options,special_features,dynamic_columns,
       teardown_pcb,teardown_thermal,teardown_thermal_design,teardown_key_ics,
       teardown_build_quality,teardown_source,datasheet_url,date_added,notes)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (d['product_name'],d['category'],d['dimensions'],d['weight'],
       d['camera_system'],d['audio_system'],d['microphone_presence'],
       d['video_inputs'],d['video_outputs'],d['supported_applications'],
       d['wireless_sharing'],d['supported_os'],d['environmental_specs'],
       d['power_supply'],d['power_consumption'],d['mounting_options'],
       d['special_features'],d['dynamic_columns'],
       d['teardown_pcb'],d['teardown_thermal'],d['teardown_thermal_design'],
       d['teardown_key_ics'],d['teardown_build_quality'],d['teardown_source'],
       d['datasheet_url'],TODAY,d['notes']))
    inserted.append(d['product_name'])

con.commit()
con.close()
print(f'DB: inserted {len(inserted)}, skipped {len(skipped)}')
if skipped: print('  Skipped (already exist):', skipped)

# ── Markdown Reports ───────────────────────────────────────────────────────
MD_TEMPLATE = '''# {name} — VC Device Benchmark Report

**Category**: {category}
**Date Researched**: {date}
**Data Sources**:
- {url}

---

## Specifications

| Field | Value |
|---|---|
| Dimensions | {dimensions} |
| Weight | {weight} |
| Camera System | {camera_system} |
| Audio System | {audio_system} |
| Microphone | {microphone_presence} |
| Video Inputs | {video_inputs} |
| Video Outputs | {video_outputs} |
| Supported Apps | {supported_applications} |
| Wireless | {wireless_sharing} |
| Supported OS | {supported_os} |
| Environmental | {environmental_specs} |
| Power Supply | {power_supply} |
| Power Consumption | {power_consumption} |
| Mounting | {mounting_options} |
| Special Features | {special_features} |

### Dynamic Columns

| Field | Value |
|---|---|
{dynamic_rows}

---

## Teardown Findings

| Field | Details |
|---|---|
| PCB / SoC | {teardown_pcb} |
| Thermal Solution | {teardown_thermal} |
| Thermal Design Observations | {teardown_thermal_design} |
| Key ICs | {teardown_key_ics} |
| Build Quality | {teardown_build_quality} |
| Source | {teardown_source} |

---

## Notes & Gaps

{notes}
'''

for d in DEVICES:
    dyn = json.loads(d.get('dynamic_columns') or '{}')
    dyn_rows = '\n'.join(f'| {k} | {v} |' for k, v in dyn.items())
    fname = d['product_name'].replace(' ', '_').replace('/', '-') + '_benchmark.md'
    fpath = os.path.join(RDIR, fname)
    content = MD_TEMPLATE.format(
        name=d['product_name'], category=d['category'], date=TODAY,
        url=d['datasheet_url'],
        dimensions=d['dimensions'], weight=d['weight'],
        camera_system=d['camera_system'], audio_system=d['audio_system'],
        microphone_presence=d['microphone_presence'],
        video_inputs=d['video_inputs'], video_outputs=d['video_outputs'],
        supported_applications=d['supported_applications'],
        wireless_sharing=d['wireless_sharing'], supported_os=d['supported_os'],
        environmental_specs=d['environmental_specs'],
        power_supply=d['power_supply'], power_consumption=d['power_consumption'],
        mounting_options=d['mounting_options'],
        special_features=d['special_features'],
        dynamic_rows=dyn_rows,
        teardown_pcb=d['teardown_pcb'], teardown_thermal=d['teardown_thermal'],
        teardown_thermal_design=d['teardown_thermal_design'],
        teardown_key_ics=d['teardown_key_ics'],
        teardown_build_quality=d['teardown_build_quality'],
        teardown_source=d['teardown_source'],
        notes=d['notes'],
    )
    with open(fpath, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print(f'MD: wrote {fname}')

print('Done.')
