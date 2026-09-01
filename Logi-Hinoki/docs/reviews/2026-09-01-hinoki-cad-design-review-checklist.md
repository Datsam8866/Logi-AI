# Hinoki CAD Design Review Checklist — Iteration 01 Entry Gate

## Purpose and scope

This is the mandatory review checklist to complete **before CAD Iteration 01 begins**. It turns the approved product baseline and concept architecture into measurable CAD-entry acceptance checks. It does not release manufacturing dimensions, select components, or authorize STEP export.

**CAD entry decision:** CAD Iteration 01 may start only when every `Entry` item below is `Pass` or has a documented, approved exception that is explicitly recorded as an open assumption. A failed `Entry` item blocks CAD start.

## Reference hierarchy

1. Direct, frozen product requirements and source-confirmed `Known` Master Parameters.
2. [Mechanical Architecture and Internal Space Claim](../superpowers/specs/2026-09-01-hinoki-mechanical-architecture-design.md).
3. Hinoki Assumption Log, including A-010 VESA candidate and the pending architecture-package assumptions A-013 through A-021.

`Known` requirements govern function. Assumed package values are concept reservations only; they may be used for Iteration 01 envelopes only when shown with their assumption ID and shall not be released as production dimensions.

## Measurement rules

- Datum: head center. X = left/right (positive to user’s right); Y = bottom/top (positive upward); Z = front/rear (positive rearward).
- A hard package is acceptable only when it is contained within its claim envelope and has no unintended three-axis intersection with another hard package.
- Minimum unrelated hard-package clearance is **5.0 mm** unless a documented assembly, thermal-interface, or electrical-contact exception applies.
- “No interference” means minimum signed solid-to-solid clearance is **≥ 0.0 mm** for intentional mating features and **≥ 5.0 mm** for unrelated hard packages.
- Every CAD measurement must show its datum, measurement direction, nominal value, and result in millimetres unless otherwise stated.
- Numeric values marked `Assumed` must show the linked assumption ID in the model, review screenshot, or measurement report.

## CAD-entry checklist

| ID | Area | Measurable acceptance criterion | Evidence / measurement | Gate | Status |
|---|---|---|---|---|---|
| DR-01 | Overall dimensions | The Iteration 01 head envelope does not exceed the **760 W × 540 H × 80 D mm** concept reservation (A-013). Any change is recorded against A-013; no unlogged outer dimension is used. | Overall bounding-box measurement, datum noted. | Entry | ☐ |
| DR-02 | Panel geometry | Display/touch stack fits its **730 W × 420 H × 18 D mm** reservation (A-014), is fully contained, and has no intersection with mid-frame, rear cover, or AV bar. | Bounding box and section through panel stack. | Entry | ☐ |
| DR-03 | Bezel | Bezel is continuous around the panel, contains the touch/glass edge, and does not intrude into the derived active area. Each bezel width is measured and recorded; no final numerical target is inferred before panel selection. | Front elevation with four bezel dimensions; panel datum. | Entry | ☐ |
| DR-04 | Camera location | One integrated 4K camera is at the head top centerline: camera optical-axis X offset from head datum = **0.0 mm**. The full camera/shutter package stays within **120 × 55 × 42 mm** (A-016). | Front/top view plus camera package bounding box. | Entry | ☐ |
| DR-05 | Camera FOV clearance | For both **134° and 140° horizontal FOV** boundary rays, no head, light, speaker, shutter, bezel, or stand geometry intersects the forward optical keep-out. The resulting ray-intersection count is **0**. | Optical section/ray study referenced to camera optical axis. | Entry | ☐ |
| DR-06 | Privacy shutter | The shutter is manual and captive: no removal path exists without a tool/service disassembly step; open and closed positions both have ≥ **0.0 mm** interference clearance, with positive mechanical end stops in both positions. | Shutter travel section and exploded/retention view. | Entry | ☐ |
| DR-07 | Speaker packaging | Two independent upper speaker enclosures exist, left and right of the camera. Each fits **170 × 55 × 40 mm** (A-017); speaker-to-camera and speaker-to-light unrelated-package clearance is **≥5.0 mm**. No full-width lower soundbar is present. | Top-bar section and clearance report. | Entry | ☐ |
| DR-08 | Microphone locations | Microphone provisions are in the upper AV/acoustic bar, distributed toward its outer portions; no microphone port is hidden behind the display, speaker volume, camera package, or front-light hardware. Each aperture has a forward acoustic path with zero solid intersections. | Front view and acoustic-path section. | Entry | ☐ |
| DR-09 | SOM packaging | QC7790 SOM reservation is central behind the display, within **200 × 120 × 32 mm** (A-019), coupled to a local heat spreader/mid-frame path, and separated from the AV bar and lower I/O bay by **≥5.0 mm**. | Rear section, package bounding box, heat-path view. | Entry | ☐ |
| DR-10 | PCB packaging | Every head PCB has a named volume, mounting reference, service-removal direction, connector side, and non-overlapping keep-out. All head PCB packages are fully contained; any board with final outline unavailable is explicitly marked as an assumption. | PCB envelope register and exploded service view. | Entry | ☐ |
| DR-11 | USB-C PD section | AC/DC conversion and bulk USB-C PD power stage are located in the desktop stand base, not the head. Head retains only the local USB-C port-interface/protection board within **120 × 75 × 24 mm** (A-020); it has **≥5.0 mm** unrelated-package clearance. | Stand/base section and head I/O section. | Entry | ☐ |
| DR-12 | I/O accessibility | CAD contains HDMI input, 2 × USB-A, USB-C BYOD, Ethernet, and 3.5 mm audio output. Each user-accessible port has a direct external insertion/removal path with zero solid intersections; rear/service I/O is reachable after rear-cover removal without removing the panel. | I/O map and connector sweep/section. | Entry | ☐ |
| DR-13 | Cable clearance | Every cable route has defined entry/exit points and does not cross a vent, moving mechanism, sharp edge, or service-removal path. The required cable bend radius is taken from the selected cable/connector data; until then, preserve a labelled keep-out and report it as an open assumption. | Cable route model and keep-out list. | Entry | ☐ |
| DR-14 | Radar | Radar presence-sensor provision has a separate front/upper keep-out, a forward field path with zero solid intersections, and no co-location inside the speaker enclosure or camera package. | Radar keep-out section and interference report. | Entry | ☐ |
| DR-15 | Ambient-light sensor | A separate optical path/window provision exists near the front/upper region; it has a forward field path with zero solid intersections and is not obscured by lighting hardware. Requirement remains Conditional until product approval. | Front view and optical-path section. | Entry | ☐ |
| DR-16 | Front lighting | Two front-light modules sit between the camera and the two speaker zones. Each fits **55 × 12 × 15 mm** (A-018), has **≥5.0 mm** unrelated-package clearance, and does not enter the 140° camera FOV keep-out. | Top-bar layout and FOV overlay. | Entry | ☐ |
| DR-17 | VESA | The rear central zone contains a structural VESA reinforcement envelope of **180 × 180 × 18 mm**. The 100 × 100 mm VESA pattern is labelled A-010 / `Assumed`, not released. No compute, I/O, or cover service path blocks the stand interface. | Rear view, VESA dimensions, and stack section. | Entry | ☐ |
| DR-18 | Desktop stand | The model contains a height- and tilt-adjustable desktop stand, a protected DC trunk through the stand, and base volumes for AC/DC, bulk PD, ballast, and cable storage. Head and base power volumes shall not overlap. | Full assembly section and routed-cable view. | Entry | ☐ |
| DR-19 | Height adjustment | Define the head reference point and show the full intended height-adjustment travel. At both end positions, the head does not intersect base, desk plane, cable route, or any stand member; all measured clearances are **≥0.0 mm**. Final travel range is an open assumption until ergonomic requirement approval. | Two position configurations and interference report. | Entry | ☐ |
| DR-20 | Tilt mechanism | Define neutral, maximum forward, and maximum rearward tilt states. At all three states, the head avoids stand/base/desk/cable interference (clearance **≥0.0 mm**) and the camera FOV forward half-space is not blocked by the stand. Final angular limits remain an open assumption until ergonomic approval. | Three position configurations and section views. | Entry | ☐ |
| DR-21 | Center of gravity | CAD mass properties include the head, stand, base power stage, ballast, and representative cable load. The projected assembly center of gravity lies inside the desk-contact support polygon in neutral and all height/tilt end states. Safety margin and final mass values are not released until component masses are selected. | Mass-properties report and support-polygon overlays. | Entry | ☐ |
| DR-22 | Thermal architecture | QC7790 has a continuous declared conduction path: SOM → local heat spreader → metal mid-frame/rear structure. Top and lower ventilation keep-outs have zero obstruction. Head internal dissipation excludes laptop-delivered **≥90 W** USB-C power. | Thermal path section; vent-area and power-boundary annotations. | Entry | ☐ |
| DR-23 | Component interference | CAD interference analysis covers all hard packages, structures, fasteners, cable keep-outs, service-removal paths, and moving stand states. Unrelated hard-package pairs have **≥5.0 mm** clearance; intentional interfaces are documented. | Interference report with worst-clearance list. | Entry | ☐ |
| DR-24 | STEP integrity | Before any STEP handoff, every part/assembly is a valid solid or a deliberately identified reference surface; no empty components, duplicate coincident solids, unresolved external references, or non-manifold bodies are present. Assembly opens with all components resolved, and a neutral STEP re-import has solid-count change = **0** and interference-report availability. | Native-model audit and STEP export/re-import report. | Handoff | ☐ |

## Mandatory review output package

Before moving from CAD entry to an Iteration 01 review, prepare:

1. A completed copy of this checklist with Pass / Fail / Exception status and reviewer/date.
2. Overall, front, rear, top, side, and central-section measurements using the stated datum.
3. Camera 134° and 140° FOV keep-out views.
4. Top AV/acoustic-bar, central compute/VESA, lower I/O, and stand/base sections.
5. Component-interference and center-of-gravity reports for neutral and end-motion states.
6. An assumption/deviation register citing the controlling A-ID for every non-frozen dimension.

## CAD-start authorization

**Current state: BLOCKED — checklist created; CAD Iteration 01 has not started.**

Authorization requires the design reviewer to change this state to `Approved for CAD Iteration 01` after all Entry gates are passed or approved as explicit exceptions. STEP integrity is a handoff gate and is not evaluated until a CAD model exists.
