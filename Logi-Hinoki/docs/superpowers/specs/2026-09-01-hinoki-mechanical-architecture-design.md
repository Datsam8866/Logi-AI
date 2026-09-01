# Hinoki Mechanical Architecture and Internal Space Claim

## Purpose

Define the concept-level mechanical baseline for the 32-inch Hinoki desktop/focus-room all-in-one. This specification authorizes an architecture and a numerical internal space claim only. It does not authorize CAD, STEP, render, released dimensions, component selection, or tooling.

## Approved Baseline Freeze

The frozen baseline contains only direct product requirements and source-confirmed `Known` values from the Master Parameter Table. `Derived`, `Assumed`, and `TBD` entries remain change-controlled concept inputs and cannot become CAD-release authority.

Frozen requirements include:

- 32-inch 4K capacitive-touch display.
- QC7790 SOM.
- Integrated 4K camera with 134-140-degree FOV.
- Manual captive privacy shutter.
- Integrated microphones and upper-mounted left/right speakers.
- HDMI input, two USB-A ports, USB-C BYOD, Ethernet, and 3.5 mm audio output.
- USB-C charging of at least 90 W delivered to the laptop, with delivered laptop power excluded from Hinoki internal thermal dissipation.
- Wi-Fi 6, BLE, radar presence sensing, ambient-light-sensor provision, front lighting, VESA compatibility, and a height- and tilt-adjustable desktop stand.
- No uniform geometric scaling of Dixie 65 architecture into Hinoki.

The new `Frozen Baseline` sheet will cite the controlling Master Parameter IDs, state the frozen value, and use `Frozen` or `Conditional` status. Ambient-light sensing is conditional because the source requirement explicitly qualifies it as applicable only when needed.

## Selected Mechanical Architecture

### Head assembly

The head uses a layered architecture:

1. Front cover lens, capacitive-touch layer, and 32-inch display module.
2. A metal mid-frame that establishes panel flatness, carries the camera/acoustic bar, and collects heat from the compute module.
3. A rear equipment cavity, divided into compute, I/O, low-power PD-interface, VESA reinforcement, service, and vent zones.
4. A removable rear service cover that reaches I/O and the compute module without removing the display panel.

The concept envelope is an `Assumed` space-claim envelope of 760 W x 540 H x 80 D mm. It accommodates a 730 W x 420 H x 18 D mm assumed display/touch stack and an 85 mm high upper AV/acoustic bar. These dimensions are packaging reservations, not released product dimensions.

### Upper AV/acoustic bar

The upper AV/acoustic bar is the primary user-facing subsystem. Left and right speaker enclosures sit at the two ends. A top-center camera module with manual captive shutter occupies the center. Narrow front-light modules sit between camera and speaker zones. Microphone apertures distribute toward the outer portions of the bar; radar, ambient-light sensor, and antennas use separate front/upper keep-outs.

This arrangement protects the camera FOV, keeps front lighting near the camera optical axis, and directs sound toward the user. It is incompatible with a full-width lower soundbar and therefore reserves the lower head edge for I/O, cable exit, and ventilation.

### Compute, thermal, and mounting structure

The QC7790 compute module is centrally located behind the display, coupled to a local heat spreader and the metal mid-frame. It has a direct rear vent path and remains physically separated from the top AV bar and lower I/O service bay.

The rear central zone carries the VESA reinforcement and adjustable-stand interface. Compute and VESA zones may overlap in X/Y only when vertically separated by their Z-depth allocations. The claim will require at least 5 mm clearance between unrelated hard packages.

### Power and I/O architecture

The desktop-stand base houses the AC/DC conversion, bulk power stage, primary USB-C PD power stage, ballast, and cable storage. A protected DC trunk runs through the stand to the head.

The head retains a compact USB-C port-interface/protection board adjacent to the user-facing port. This minimizes high-current path length in the head, supports service access, and avoids placing AC/DC conversion heat next to the QC7790.

HDMI input, Ethernet, 3.5 mm audio, and service-oriented USB ports occupy the lower rear I/O bay. User-accessible USB-C BYOD and USB-A ports may use a lower-side or lower-front reach zone, recorded as an assumption until industrial-design review.

## Internal Space Claim Rules

The `Internal Space Claim` sheet will use a head-center Cartesian datum:

- X: left/right, positive to the user’s right.
- Y: bottom/top, positive upward.
- Z: front/rear, positive rearward.

Each claim records a center point, W/H/D bounding box, quantity, volume, containment status, type, associated Master Parameter IDs, assumption IDs, and CAD-driving status.

Claims are classified as:

- `Hard Package`: physical module or enclosure with its local assembly clearance.
- `Structural`: mid-frame, VESA reinforcement, or stand interface.
- `Keep-out`: optical, antenna, vent, service, or cable-bend reservation.

The numerical claim will start with these `Assumed` packaging reservations:

- Display/touch stack: 730 x 420 x 18 mm.
- Camera/shutter module: 120 x 55 x 42 mm.
- Each upper speaker enclosure: 170 x 55 x 40 mm.
- Each front-light module: 55 x 12 x 15 mm.
- QC7790 compute/heat-spreader module: 200 x 120 x 32 mm.
- Head USB-C port-interface/protection board: 120 x 75 x 24 mm.
- Rear I/O board: 220 x 60 x 24 mm.
- VESA reinforcement: 180 x 180 x 18 mm, supporting the separately assumed 100 x 100 mm VESA candidate.

The space-claim register must report a containment pass for every package and no hard-package overlaps. It will also report the claimed rear-cavity volume and the remaining reserve volume. A reserve below 25% is a review condition, not an automatic design failure.

## Verification Criteria

1. Every frozen row is traceable to a direct requirement or a source-confirmed Master Parameter and no assumption is marked `Frozen`.
2. Every required product subsystem has a space-claim zone and a mechanical/thermal/service rationale.
3. Hard-package claims fit inside their assigned envelope, have no unintended three-axis intersections, and retain the specified clearance.
4. Front camera, shutter, lighting, speakers, microphones, radar, and ambient-light-sensor provisions are represented in the upper AV/acoustic bar.
5. Head power claims exclude base AC/DC and bulk PD volume while retaining the head USB-C interface board.
6. The internal thermal boundary retains the existing rule: useful laptop-delivered power is not added to Hinoki internal dissipation.

## Open Control Points

The assumption log, rather than the frozen baseline, controls the final selected panel module, QC7790 thermal design data, exact VESA pattern, stand geometry, final port positions, external enclosure dimensions, optical keep-outs, speaker driver selection, and all released manufacturing dimensions.
