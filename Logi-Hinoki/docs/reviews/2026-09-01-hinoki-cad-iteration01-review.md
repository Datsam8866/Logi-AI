# Hinoki Concept CAD Iteration 01 Review

**Review date:** 2026-09-01
**Decision:** Concept CAD Iteration 01 passes its initial space-claim review. It is not release geometry and no STEP has been exported.

## Deliverable and controlled scope

| Item | Result |
|---|---|
| CAD deliverable | `cad/iteration-01/Hinoki_Concept_CAD_Iteration01.FCStd` |
| Geometry type | Parametric concept assembly and motion envelopes |
| Neutral pose | VESA pivot Z = 430 mm; tilt = 0° |
| Low/forward review pose | VESA pivot Z = 370 mm; tilt = −5° |
| High/rearward review pose | VESA pivot Z = 490 mm; tilt = +20° |
| Export status | No STEP / release / tooling geometry exported |

All values inherited from A-013 through A-040 remain **Assumed** control values. The model includes the head, panel/touch stack, upper AV/acoustic bar, 4K camera and manual shutter, upper speakers, lights, microphone zones, radar and ALS provisions, compute/thermal package, I/O, VESA reinforcement, stand, base power/ballast package and motion keep-outs.

## Automated geometry review

| Check | Result | Evidence |
|---|---|---|
| Head package containment | Pass | All selected head packages are inside 760 W × 80 D × 540 H mm envelope. |
| Hard-package intersections | Pass | Zero unintended intersections among display, camera, speakers, lights, radar, ALS, compute, USB-C, I/O and VESA packages. |
| Panel / bezel concept | Pass — conditional | 730 mm display/touch stack creates 15 mm left/right bezel; 35 mm lower bezel; stack meets AV bar at 0 mm gap. |
| Camera location | Pass — conditional | Top-centre camera/shutter package is centred at X = 0 in upper AV bar. |
| Camera FOV | Pass — concept | 137° nominal keep-out is inside 134–140° requirement; front hardware is behind camera front datum. |
| Speaker placement | Pass — conditional | Two 170 × 40 × 55 mm upper speaker enclosures are retained at AV-bar ends. |
| Compute / VESA separation | Pass — concept | QC7790 package occupies Y = −10 to 22 mm; VESA reinforcement occupies Y = 22 to 40 mm, sharing only a boundary plane. |
| Stand/base space claim | Pass — conditional | 500 × 340 × 90 mm base contains 360 × 260 × 90 mm AC/DC + bulk PD + ballast reservation. |

The machine-readable result is `cad/iteration-01/Hinoki_Iteration01_CAD_Review.json`.

## Checklist status after Iteration 01

| CAD review item | Current state | Required Iteration 02 evidence |
|---|---|---|
| DR-03 Bezel | Concept geometry established | Selected panel, cover lens and touch-frame drawing |
| DR-05 Camera FOV clearance | Concept pass | Lens vendor ray model at all height/tilt states |
| DR-06 Privacy shutter | Package/closed state represented | Manual shutter travel, retention and optical-obscuration study |
| DR-08 Microphones | Aperture zones represented | Acoustic path and isolation validation |
| DR-10 PCB packaging | Space claims represented | Actual board outlines, connector and fastener keep-outs |
| DR-12 I/O accessibility | Pending | Plug insertion / finger access sweep |
| DR-13 Cable clearance | Motion keep-out represented | Cable bend radius, flex-life and strain-relief model |
| DR-17 VESA | Reinforcement package represented | Final pattern, fasteners and load calculation |
| DR-20 Tilt mechanism | Envelope represented | Selected hinge / lock mechanism and interference check |
| DR-21 Centre of gravity | v0.2 static screen retained | CAD/BOM mass properties and physical tip-test plan |
| DR-22 Thermal architecture | Package separation retained | Heat-spreader, vents and CFD / thermal validation |
| DR-23 Component interference | Initial hard-package screen passed | Full service / motion / fastener interference check |

## Next action

Iteration 02 should replace the highest-risk assumptions first: selected panel/touch stack, camera/lens/shutter module, QC7790 carrier and heat spreader, VESA pattern/fasteners, USB-C connector family, and stand hinge/column mechanism. Re-run the automated review after each replacement. Do not export STEP until the CAD Design Review Checklist has evidence for every applicable item.
