# Hinoki Calm Crown — External Concept CAD Design

Date: 2026-09-01
Status: Approved design freeze; pending written-spec acknowledgement

## Objective

Replace the Iteration 02 packaging-box model with a complete, reviewable 32-inch all-in-one video-collaboration product concept. The new model must support industrial-design review, preserve the approved Hinoki mechanical architecture, generate publication-ready renders, and export a product-only neutral STEP file.

This is external concept-review geometry. It is not tooling, tolerance, structural-release, or manufacturing geometry.

## Design Basis

The selected direction is **A2 — Balanced Calm Crown**. It combines:

- Dixie construction and service principles without scaling Dixie 65 geometry.
- Logitech-family quiet form, soft transitions, controlled seams, and low visual noise.
- A screen-first front with an integrated but legible upper AV/acoustic crown.
- A shallow rear pillow shell, central service island, concealed telescoping stand, and rear-weighted soft-plinth base.

Official competitive references establish category boundaries but do not authorize copied surfaces or dimensions:

- Neat Board 32: https://neat.no/board-32/
- Logitech Rally Board 65: https://www.logitech.com/en-us/products/video-conferencing/room-solutions/rally-board-65.html
- Cisco Desk Pro: https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/webex-desk-pro/datasheet-c78-743105.html
- Google Meet Series One Desk 27 by Avocor: https://www.avocor.com/products/google-series-one-desk-27/

## Product and Architecture Requirements

The model must visibly and structurally represent:

- A 32-inch 4K capacitive-touch display.
- One integrated top-centre 4K camera with 134–140-degree horizontal FOV.
- A manual, captive, non-removable privacy shutter with visible open and closed states.
- Independent upper-left and upper-right speaker zones; no lower full-width soundbar.
- Upper microphone apertures, two front-fill light windows, radar provision, and an ambient-light-sensor provision.
- Central rear QC7790 compute and heat-spreader space claims with a declared conductive path to the mid-frame/rear structure.
- HDMI input, two USB-A ports, USB-C BYOD with at least 90 W laptop charging, Ethernet, and 3.5 mm audio output.
- Wi-Fi 6, BLE, VESA compatibility, service access, and controlled cable routing.
- A desktop stand with 120 mm height adjustment, −5-degree forward tilt, and +20-degree rearward tilt.
- AC/DC, bulk PD, ballast, and cable storage in the stand base; only the local USB-C interface/protection function remains in the head.

## Coordinate System and Model Structure

Use the approved head-centre datum:

- X: left/right, positive to the user's right.
- Y: bottom/top, positive upward.
- Z: front/rear, positive rearward.

The native CAD tree must separate:

1. `Datums_and_Motion`
2. `Internal_Space_Claims`
3. `Structure`
4. `Visible_ID_Surfaces`
5. `Review_Metadata`

Product-review views show `Structure` and `Visible_ID_Surfaces`. Packaging-review views may additionally show datums and internal claims. Keep-outs, motion sweeps, benchmark products, and assumed packages must never be exported as product solids.

## Concept Dimensions

All values in this section are controlled concept assumptions, not released dimensions.

| Feature | Concept target | Control |
|---|---:|---|
| Finished head envelope | 742 W × 492 H × 62 D mm | Proposed A-041 |
| Front outer corner radius | 18 mm | Proposed A-042 |
| Upper AV/acoustic crown height | 72 mm | Proposed A-043 |
| 32-inch 16:9 active-area reference | 708.4 W × 398.5 H mm | Derived category reference; selected panel governs |
| Rear service island | 260 W × 220 H mm within the 62 mm depth | Proposed A-044 |
| VESA pattern | 100 × 100 mm | Proposed A-045; final fastener/load selection remains open |
| Stand height travel | 120 mm | Retains A-035 intent |
| Stand tilt | −5° / 0° / +20° | Retains A-036 intent |
| Base envelope | 420 W × 285 D × 68 H mm | Proposed A-046 |
| Base power/PD reservation | 360 W × 240 D × 45 H mm | Proposed A-047 |
| Ballast plate reservation | 380 W × 250 D × 8 H mm | Proposed A-048 |

The selected bare panel/touch/cover-glass stack will replace the active-area reference before any released bezel or glass dimension is created.

## Visible Industrial-Design Geometry

### Front head

- A single 742 × 492 mm soft-rectangle silhouette with consistent 18 mm outer corner radii.
- A display field with cover glass, printed black mask, active-area boundary, side/bottom bezel, and a controlled glass-to-crown reveal.
- No visible supplier-monitor bezel or housing.
- Edge breaks and side-wall transitions must be modeled as real rounds/chamfers, not render-only effects.

### Balanced AV crown

- A 72 mm-high crown with a slightly recessed or softly crowned front surface.
- Two independent acoustic zones, each preserving the 170 × 55 × 40 mm speaker space claim.
- A centred camera package preserving the 120 × 55 × 42 mm camera/shutter claim.
- A visible pill-shaped camera bezel, lens window, manual slider/tab, red closed-state indicator, white/neutral open-state indicator, and positive end positions.
- Two narrow front-light windows between the camera and speaker zones.
- Microphone apertures toward the outer crown regions plus separate radar and ambient-light windows.
- At least 5 mm unrelated-package clearance among camera, speaker, lighting, and sensor claims.

### Side and rear head

- A shallow pillow-back profile with controlled depth growth toward the centre.
- A central 260 × 220 mm service island that visually organizes the QC7790, heat spreader, VESA reinforcement, stand interface, and removable service cover.
- Vent fields integrated into rear/lower shadow lines.
- Lower-rear service I/O plus a lower-side user reach zone with visible connector openings and insertion direction.
- A protected cable exit aligned to the stand spine.

### Stand and base

- A central D-profile telescoping spine with distinct fixed and moving members.
- A soft-square pivot pod with a defined rotation axis, joint cover, head-back clearance, and concealed VESA interface.
- Real low, neutral, and high positions plus forward, neutral, and rearward tilt states; copied ghost head boxes are not sufficient.
- A 420 × 285 × 68 mm rear-weighted soft plinth with a visually thin front edge, upper/lower shells, feet, rear cable exit, and cable-storage access.
- Base internal claims include AC/DC, bulk PD, ballast, and cable storage without being exported as visible product solids.

## Internal Space Claims

Restore the complete Iteration 01 architecture as hidden, traceable references:

- Panel/touch/cover-glass stack.
- Left/right speakers and acoustic volumes.
- Camera, lens, ISP/carrier, shutter, lights, microphones, radar, ambient-light sensor, and antenna keep-outs.
- QC7790 SOM/carrier, heat spreader, VESA reinforcement, USB-C interface/protection board, rear I/O board, cable bends, and vents.
- Stand carriage, pivot, DC trunk, base power/PD, ballast, and cable storage.

Every claim must carry its requirement IDs, assumption IDs, classification, source, and review status. The LM-3237 and Ergotron HX remain benchmark references only and must not appear as Hinoki product geometry.

## CMF and Render Design

The first published concept uses the Graphite colourway:

- Display cover glass: near-black, low-gloss anti-glare appearance.
- AV crown: warm graphite acoustic textile or micro-perforated insert.
- Camera pill and shutter: dark graphite with restrained red privacy indication.
- Rear shell, stand, and base: graphite polymer appearance with a slightly warmer/lighter service island.
- Pivot and structural accents: dark neutral metallic finish.

Required publication-ready outputs:

1. Front three-quarter hero render, 2400 × 1600 px.
2. Rear three-quarter render, 2400 × 1600 px.
3. Side motion board showing low/neutral/high and tilt states.
4. Internal architecture overlay with a visible legend and assumption markings.
5. Clean front and rear orthographic review images.

All renders must be regenerated from the same native CAD revision used for STEP export.

## STEP Deliverable

Target file:

`cad/iteration-03/Hinoki_CalmCrown_Concept_Review.stp`

The STEP contains only intended physical product parts:

- Front glass/mask representation.
- Crown shell and acoustic inserts.
- Camera bezel, lens window, shutter parts, light and sensor windows.
- Rear and side shells, service cover, vents, and I/O openings.
- Stand fixed/moving members, pivot/yoke, interface cover, base shells, and feet.

It excludes FOV geometry, motion envelopes, internal package boxes, datums, axes, planes, and competitor benchmarks.

## Review and Scoring Gate

No STEP may be presented as the deliverable until every hard gate passes.

### Hard gates

1. Artifact revision/hash consistency.
2. Scope and maturity truthfulness.
3. Complete hard-requirement coverage.
4. Architecture and datum consistency.
5. Finite, positive-volume, valid, closed/manifold product solids.
6. Zero unauthorized overlaps; intentional interfaces use a reviewed whitelist.
7. Camera FOV, shutter, stand motion, cable, connector, service, and CG evidence.
8. Native-to-STEP re-import parity and successful second-importer check.
9. Complete, current visual evidence.
10. Risk/status integrity.

### Weighted concept score

| Category | Weight | Minimum |
|---|---:|---:|
| External design completeness | 15 | 3/5 |
| Architecture consistency | 20 | 4/5 |
| Visual communication | 10 | 3/5 |
| Geometry health | 20 | 4/5 |
| STEP portability | 10 | 4/5 |
| Requirement traceability | 15 | 4/5 |
| Risk integrity | 10 | 3/5 |

The total concept-review score must be at least 80/100. A release/manufacturing claim would require at least 90/100 and is outside this scope.

## Independent Agent Review

The model author cannot self-approve the final deliverable. Before presentation:

1. Requirements/Architecture reviewer may veto missing hard requirements or unapproved architecture drift.
2. Industrial Design/Product reviewer may veto generic-box geometry, incoherent proportions, or incomplete visible product parts.
3. Geometry/Mechanism reviewer may veto invalid solids, unauthorized collisions, missing motion evidence, or unsupported stability.
4. STEP Portability reviewer may veto count, unit, axis, hierarchy, naming, or second-importer failures.
5. Traceability/Risk reviewer may veto unsupported promotion, missing risks, or status/evidence mismatch.
6. QA integrator may aggregate only signed frozen reviews and may not remove another reviewer's veto.

Any category-score difference greater than 1/5 requires adjudication rather than averaging.

## Acceptance Criteria

The concept is complete only when:

- A non-author can identify a complete Hinoki AIO in front, rear, side, and three-quarter views without enabling internal proxies.
- Every required visible subsystem and user interaction is modeled.
- Internal space claims retain complete requirement/assumption traceability.
- Low/neutral/high and forward/neutral/rearward positions are real kinematic states with no unauthorized product, desk, base, stand, or cable collision.
- The product-only STEP re-imports with exact intended leaf/solid parity, finite bounds, correct millimetre scale, correct axes, and no invalid/duplicate bodies.
- The render package, review evidence, scorecard, and STEP share one revision/hash manifest.
- All independent reviewers remove vetoes, all hard gates pass, and the weighted score is at least 80/100.
