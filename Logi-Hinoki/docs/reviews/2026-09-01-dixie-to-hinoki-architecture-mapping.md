# Dixie 65 → Hinoki 32 Architecture Mapping

## Decision rule

Dixie 65 is a reference architecture, not a scale model. A Dixie feature may be retained only as a functional or construction principle; its geometry must be re-derived for the 32-inch desktop/focus-room product. A `Known` Hinoki requirement always overrides a Dixie reference.

## Mapping register

| Area | Dixie 65 reference | Hinoki direction | Classification | CAD / engineering consequence | Control |
|---|---|---|---|---|---|
| Product architecture | 65-inch large-room collaboration display | 32-inch desktop/focus-room all-in-one | Known | Re-package all mass, thermal, stand and service functions; no uniform 32/65 scaling. | MP-001, MP-002, MP-077 |
| Display and touch | 65-inch IR touch, passive stylus | 32-inch 4K capacitive touch; no stylus | Known / Assumed raster | Front stack, bezel and touch integration are redesigned around selected panel. | MP-002, MP-003, MP-008, MP-011; A-001, A-002 |
| Camera | Integrated IMX283, 110° FOV | Integrated 4K camera, 134–140° FOV | Known | Camera moves to upper center; a 140° optical keep-out governs the AV bar. Sensor and lens envelope remain open. | MP-020, MP-022; A-003 |
| Privacy | Automatic rotating shutter | Manual captive, non-removable shutter | Known | Add manual travel, positive stops and retained mechanism; Dixie shutter geometry does not transfer. | MP-024, MP-025 |
| Speakers and microphones | 2 × 70 mm + 2 × 31 mm speakers; 6 front / 2 rear microphones | Upper left/right speaker volumes; microphone configuration open | Known placement / TBD configuration | Reserve top AV/acoustic bar; no lower full-width soundbar. Driver count, apertures and acoustic volumes require selection. | MP-030; approved architecture |
| Compute | QC8550 TC SOM | QC7790 SOM | Known | Central rear compute zone with separate heat-spreader claim. Board outline, connector faces and thermal design data remain open. | MP-027, MP-080, MP-081; A-004 |
| Thermal | Heat sink + heat pipe + copper plate + pads coupled to rear structure; passive vents | Preserve conductive-spreading philosophy, not Dixie dimensions/load values | Known reference / Assumed architecture | QC7790 → spreader → metal mid-frame/rear path; top/lower vents held as keep-outs. Panel, SOM and PD losses need Hinoki inputs. | MP-093–MP-095; A-004, A-005 |
| Power | Display-centric power board inside large display | AC/DC and bulk USB-C PD in desktop stand base; protected DC trunk to head | Approved architecture | Base handles mass/heat; head keeps local USB-C port-interface board only. Laptop-delivered 90 W is excluded from head thermal dissipation. | MP-036, MP-063–MP-065; A-006, A-012 |
| I/O | HDMI in/out, 3 × USB-A, USB-C, Ethernet, 3.5 mm | HDMI in, 2 × USB-A, USB-C BYOD + ≥90 W delivery, Ethernet, 3.5 mm | Known | Lower rear service I/O plus lower-side/front user reach zone; connector sizes, cable bend and access paths remain open. | MP-033–MP-038; A-009 |
| Connectivity / antenna | Wi-Fi 6, BLE | Wi-Fi 6, BLE | Known | Separate upper/front antenna keep-outs; do not place inside speaker or metal heat-spreader volume. | MP-040, MP-041 |
| Sensors | Environmental/radar/ambient sensor | Radar required; ambient-light provision conditional | Known / Conditional | Reserve independent front/upper optical/RF paths, separated from speaker, camera and lighting. | MP-042–MP-044; A-007 |
| Lighting | No front lighting | Front video-fill lighting near camera | Known function / Assumed implementation | Two narrow light volumes between camera and speakers; optics and thermal inputs remain open. | MP-045, MP-046; A-011 |
| Mounting / stand | VESA, legs and cart | VESA with height- and tilt-adjustable desktop stand | Known | Central VESA reinforcement plus desktop base, travel and tilt claims. VESA pitch and motion ranges remain open. | MP-047–MP-051; A-010 |
| Service | Hatches, covers and interface rail | Removable rear service cover; ports accessible without panel removal | Assumed architecture | Define service removal, cable paths and component access before detailed CAD. | A-009; approved architecture |
| CMF / enclosure | Graphite/off-white family, PC/ABS enclosure strategy | Preserve product-family intent while redeveloping materials, wall, ribs and finish | Assumed | Do not transfer 65-inch wall or cosmetic dimensions. Material, wall and fastener system require ME/CMF selection. | MP-014–MP-016; A-008 |

## Pre-CAD gaps requiring control

| Gap | Status | CAD treatment before source closure |
|---|---|---|
| Selected 32-inch panel outline, active area, stack-up, mass and TCON location | TBD | Use an explicitly labelled display/touch space claim only; no production bezel or rear-cover release. |
| QC7790 SOM outline, connector locations, power and thermal data | TBD | Use a labelled compute envelope; no final PCB, heat spreader or mount pattern. |
| Camera lens/sensor, shutter mechanism and real 140° ray envelope | TBD | Use a 140° keep-out and an assumed camera package; no released optical window. |
| Speaker drivers, microphone array and acoustic targets | TBD | Use top-bar packaging claims only; no production grille/acoustic volume release. |
| USB-C/HDMI/Ethernet connector models and cable limits | TBD | Use named I/O and cable keep-outs; defer final port cut-outs and bend radii. |
| VESA pitch, stand load/mass, height travel and tilt angles | TBD | Use A-010 candidate and travel envelopes; defer load-rated mechanism geometry. |
| Hinoki power loads, PD topology and thermal limits | TBD | Maintain a preliminary budget and a heat-source-to-space-claim map; do not transfer Dixie wattages. |

## CAD readiness status

**Blocked.** This mapping supports Pre-CAD preparation only. CAD Iteration 01 can be considered only after the Master Parameter Table, Assumption Log, preliminary Power Budget, and internal space-claim register have been updated and pass the CAD Design Review Checklist entry gates.
