# Hinoki Iteration 02 Preliminary Review

**Review date:** 2026-09-01  
**Decision:** `PassWithOpenRisks` for preliminary market-envelope review. A simplified STEP is available for concept review only; it is not release geometry.

## Review baseline

| Subsystem | Review baseline | Decision | Source-backed evidence | Blocking evidence |
|---|---|---|---|---|
| Panel / touch | One World Touch `LM-3237-26B-4K` | Preferred review proxy | 32-inch, 3840 × 2160, 10-point PCAP; 750.4 × 452.7 × 56.5 mm; 14 kg; VESA 200 × 200 mm | This is a complete commercial display, not a bare panel/touch stack. Internal electronics, connector and thermal decomposition are unknown. |
| Camera / shutter | Leopard Imaging `LI-IMX477-MIPI-140H` | Preferred camera module | 4056 × 3040 sensor, 140° horizontal FOV, 38 × 38 mm board and 25.78 mm published maximum profile | Module has no ISP and no integrated shutter. Lens ray clearance, shutter travel, retention and optical obscuration remain open. |
| Stand / VESA | Ergotron `45-475-224` HX | Preferred mechanism benchmark | 9.1–19.1 kg capacity, 292 mm lift, −5°/+70° tilt class, VESA 200 × 200 support and official CAD download | It is an external monitor arm, not Hinoki industrial design. Custom base, cable motion, centre of gravity and tip stability remain open. |

Sources:

- https://oneworldtouch.com/wp-content/mediafiles/2025/02/LM-3237-26B-4K-Data-Sheet.pdf
- https://leopardimaging.com/wp-content/uploads/2024/04/LI-IMX477-MIPI-140H_Datasheet.pdf
- https://www.ergotron.com/en-ca/products/product-details/45-475

## Automated CAD findings

| Check | Result | Evidence |
|---|---|---|
| Verified component containment | Pass | Display proxy and camera module remain inside the 760 × 80 × 540 mm assumed head envelope. |
| Display width margin | Pass — high risk | 4.8 mm per side. This leaves very little allowance for cosmetic enclosure, tolerance, sealing and assembly clearance. |
| Upper AV reserve | Pass — conditional | 87.3 mm remains above the integrated display proxy. Camera and shutter packages fit in the current concept location. |
| Display depth reserve | Pass — conditional | 23.5 mm remains behind the complete display proxy, but that proxy already includes enclosure and electronics. The reserve is not a bare-module depth budget. |
| Camera FOV value | Pass — conditional | Published 140° HFOV is at the upper Hinoki requirement limit. No lens ray model or motion-state occlusion study has been completed. |
| Stand mass headroom | Pass — high risk | HX maximum capacity minus the 14 kg display proxy is 5.1 kg before Hinoki AV, compute, thermal, cable and structural additions. |
| VESA interface | Pass — concept | Selected display proxy and HX benchmark both support 200 × 200 mm. Fastener stack, reinforcement and load paths remain open. |

Machine-readable evidence is in `cad/iteration-02/Hinoki_Iteration02_CAD_Review.json`.

## CAD content and visual language

- Dark blue: verified One World Touch external display review proxy.
- Black: verified Leopard Imaging camera module envelope.
- Amber: assumed upper AV reserve and privacy-shutter package.
- Blue: VESA 200 × 200 interface and camera FOV keep-out.
- Green: simplified Ergotron HX mechanism benchmark, not copied vendor industrial design.
- Transparent blue/red: retained low/forward and high/rearward motion envelopes.

## Open risks controlling the next review

1. Replace the integrated display proxy with a bare panel, touch sensor, cover lens, controller and mounting-stack drawing.
2. Select or design a manual captive shutter and verify travel, retention, optical obscuration and user access.
3. Establish the Hinoki-specific stand/base load path, centre of gravity, cable motion and tip-stability model.
4. Add camera ISP/carrier, connector insertion, thermal and cable keep-outs before treating the remaining 23.5 mm as usable depth.
5. Treat the STEP as concept-review geometry only until these items are closed or explicitly accepted as controlled assumptions.

## Deliverables

| Deliverable | Path |
|---|---|
| Candidate workbook | `outputs/hinoki-iteration02-review/Hinoki_Iteration02_Component_Candidates.xlsx` |
| Preliminary FreeCAD review file | `cad/iteration-02/Hinoki_Concept_CAD_Iteration02_Review.FCStd` |
| Concept-review STEP | `cad/iteration-02/Hinoki_Concept_CAD_Iteration02_Concept.stp` |
| Preview image | `cad/iteration-02/Hinoki_Concept_CAD_Iteration02_Review_Preview.png` |
| Machine-readable CAD review | `cad/iteration-02/Hinoki_Iteration02_CAD_Review.json` |
| Candidate source data | `data/iteration-02/component_candidates.json` |
