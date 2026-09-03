# Hinoki LOD 3 Inferred Engineering Prototype Design

**Date:** 2026-09-02  
**Status:** User-approved design  
**Primary CAD:** FreeCAD FCStd with STEP exchange outputs  
**Thermal target:** Simcenter FLOEFD conjugate heat transfer

## 1. Purpose and authority

Build a complete 32-inch Hinoki head, internal assembly, adjustable stand, and base at LOD 3 geometric complexity. The result is explicitly an **inferred engineering prototype**. It supports packaging review, detailed part review, mobile-image review, and generation of a controlled FLOEFD model.

The result is not manufacturing-release CAD. It has no authority for tooling, GD&T, supplier release, structural certification, safety certification, or production temperature claims. Every inferred part remains marked `ManufacturingAuthority = false`.

## 2. Approved modelling approach

Use **subsystem transplant plus parametric rebuild**:

1. Hinoki requirements and approved parameters control the product envelope, features, power, and use case.
2. Dixie provides part architecture, materials, assembly logic, DFM proportions, shields, brackets, thermal interfaces, service features, and standard hardware patterns.
3. Dixie 65-inch global coordinates must not be uniformly scaled. Master Parameter `MP-077` prohibits uniform 32/65 scaling.
4. Official competitor data fills public product-envelope, VESA, stand-motion, and feature benchmarks.
5. Engineering assumptions fill remaining gaps and are recorded with source, confidence, derivation, tolerance, and release limitation.

Rejected approaches:

- Uniformly scaling the Dixie 65-inch assembly.
- Treating the existing LOD 1 thermal proxy as simulation-quality product geometry.
- Claiming that inferred geometry is manufacturing-release geometry.

## 3. Source authority

Use this precedence order:

1. **Hinoki Known:** user-approved requirements, `Hinoki_Master_Parameters_and_Assumption_Log.xlsx`, the 57 W preliminary power budget, and already-approved 35 °C natural-convection case.
2. **Hinoki Derived:** dimensions or values deterministically derived from known Hinoki inputs.
3. **Dixie Reference:** `Dixie/3D/001_dixie65_set_asm_20250425_asm.stp`, Dixie BOM, Dixie 2D drawings, panel data, power tables, and thermal-pad drawings.
4. **Competitor Official:** current manufacturer pages and device sheets. The primary 32-inch benchmark is Neat Board 32.
5. **Engineering Assumption:** standard hardware, DFM ratios, packaging rules, stability calculation, or conservative geometry where no stronger source exists.

Conflicting values are never averaged or silently substituted. The contradiction is recorded and the lower-authority value is rejected. For example, the Dixie `14498.4 mm` housing-width literal conflicts with the product and glass envelope and must not drive CAD.

Primary competitor references:

- https://us.neat.no/board-32/?nr=US
- https://cdn-stories.neat.no/1/2025/10/Neat_Board_32_Device_Sheet.pdf
- https://support.neat.no/device/neat-board-32/

## 4. Dual-model architecture

### 4.1 LOD 3 master assembly

Current approved scope is a head-only Task 5 checkpoint. It includes the camera, lighting, sensors, audio, microphones, and six rear I/O connector proxies. It deliberately excludes physical cable-route solids and cable-bend validation; connector cutouts and rear service clearances remain explicit. Task 6 stand/base is deferred, so this checkpoint is not a full product assembly or full-product STP.

The LOD 3 master contains 80–120 named semantic parts in these top-level groups:

1. `01_Display_Stack`
2. `02_Housing_Structure`
3. `03_Electronics_Thermal`
4. `04_Camera_Lighting_Sensors`
5. `05_Audio_IO_Cables`
6. `06_Stand_Base_Kinematics`
7. `07_Fasteners_Seals_Consumables`
8. `08_Reference_Datums_Keepouts`

The master preserves wall, rib, boss, bend, hole, hatch, fastener, connector, shielding, thermal-contact, and support features that materially affect packaging or review. Cable-routing solids are outside the approved Task 5 checkpoint scope.

### 4.2 FLOEFD derived model

Generate the FLOEFD model from the validated master by a controlled suppression map. Suppress logo geometry, helical threads, cosmetic rounds, tiny chamfers, adhesive liners, and fasteners that do not alter a thermal path. Preserve:

- actual enclosure wall thicknesses;
- vent holes and open-area ratio;
- display stack and metal frames;
- major PCB and package envelopes;
- shields, speakers, and other airflow obstructions;
- heat spreaders, heat pipes, TIM footprints, and conductive contacts;
- service hatches that form secondary heat paths;
- one connected internal-air region;
- the lower/rear-lower inlet and upper-rear outlet topology.

## 5. Product control geometry

### 5.1 Head and display

| Parameter | Design value | Authority |
|---|---:|---|
| Head envelope | 742 W × 492 H × 62 D mm | Approved Hinoki baseline |
| Nominal display | 32 in, 16:9, 3840 × 2160 | Hinoki requirement and approved assumption |
| Active area | 708.4 W × 398.5 H mm | Derived from 32-inch 16:9 |
| Cover glass | 726 W × 446 H × 3.2 T mm | Engineering assumption based on active area and Dixie glass construction |
| PCAP sensor | 724 W × 444 H × 0.8 T mm | Engineering assumption |
| Optical bond | 0.5 mm | Engineering assumption |
| LCD cell | 712 W × 402 H × 2.5 T mm | Engineering assumption |
| Backlight unit | 716 W × 406 H × 12 T mm | Engineering assumption |
| Rear housing nominal wall | 2.8 mm | Dixie DFM-informed Hinoki assumption |
| Structural rib thickness | 1.7 mm | 0.6× nominal-wall DFM rule |
| Primary boss system | M3, nominal 7 mm OD | Dixie DFM-informed standard |

The front is visually clean and contains a top-centre camera zone, captive manual privacy shutter, camera-status indication, front lighting, microphone apertures, radar/ALS windows, acoustic treatment, and no stylus provision.

### 5.2 Vents

Create two physical perforated fields:

- lower/rear-lower inlet field: 400 × 25 mm gross zone;
- upper-rear outlet field: 400 × 25 mm gross zone;
- target open-area ratio: 60%;
- minimum open area per field: 6000 mm²;
- slot or hole geometry must be explicit in the LOD 3 master;
- the FLOEFD derivative may replace repeated holes with an equivalent opening only when the setup manifest records the same area and impedance intent.

### 5.3 Stand and base

| Parameter | Design value | Authority |
|---|---:|---|
| Head interface | VESA 100 × 100 mm, 4 × M4 | Neat Board 32 official benchmark |
| Overall width | 742 mm | Hinoki head |
| Overall height | 521–621 mm | Hinoki head plus 100 mm travel benchmark |
| Overall depth envelope | 225 mm | Derived from 219 mm competitor envelope |
| Height adjustment | 100 mm | Neat Board 32 official benchmark |
| Tilt | ±10° | Neat Board 32 official benchmark |
| Swivel | ±20° | Neat Board 32 official benchmark |
| Base footprint | 520 W × 225 D mm | Engineering assumption for stability study |
| Base structural plate | 500 W × 205 D × 6 T mm steel | Engineering assumption |
| VESA plate | 140 × 140 × 4 mm steel | Engineering assumption |

The stand contains a VESA plate, tilt yoke, swivel joint, 100 mm lift carriage, dual linear guides, spring or gas-assist proxy, hard stops, cable path, cosmetic covers, structural base, and non-slip feet. Helical threads are not modelled; nominal fastener solids and correct clearance/thread holes are modelled.

Extreme height, tilt, and swivel configurations must not self-interfere. At every extreme posture the projected centre of mass must remain inside the support polygon with at least a 25 mm static margin in the assumed no-touch-load case. This is a packaging gate, not a safety certification.

## 6. Subsystem design

### 6.1 Display and housing

Model cover glass, PCAP sensor, optical-bond layer, LCD cell, BLU, T-con board, display carrier, front frame, rear housing, metal mid-frame, perimeter retainers, hatches, vent grilles, rear I/O cover, VESA reinforcement, ribs, bosses, and fasteners.

### 6.2 Electronics and I/O

Create separate carrier, compute/SOM, power, I/O, Wi-Fi/BLE, camera, sensor, lighting, and audio PCBs. Include board outlines, thickness, mounting holes, main connectors, shielding cans, and major IC packages. Use these controlled inferred starting envelopes:

- carrier PCB: 250 × 140 × 1.6 mm;
- compute/SOM PCB: 90 × 70 × 1.6 mm;
- power PCB: 160 × 100 × 1.6 mm;
- I/O PCB: 180 × 30 × 1.6 mm;
- Wi-Fi/BLE module: 30 × 20 × 3 mm.

I/O provision includes one HDMI input, two USB-A, one USB-C with display/data and ≥90 W PD, Ethernet, and 3.5 mm line output. Create a serviceable rear I/O zone with explicit connector cutouts and service clearances. Cable-route solids are deferred.

### 6.3 Camera, lighting, and sensors

Use a 38 × 38 × 25.78 mm 4K-class 140° camera-module envelope as the starting reference. Package it at the top centre with an inferred 104 × 46 × 32 mm barrel assembly, a captive manual slider shutter, camera glass, LED/status guide, and optical keep-out.

Create two symmetric front-light bars, each 120 × 8 × 8 mm, totalling the approved 4 W load. Create a 59.8 × 18 × 16.3 mm radar-holder envelope and a separate ALS optical path.

### 6.4 Audio

Create two 40 mm full-range speaker assemblies, two 50 × 25 mm passive-radiator proxies, acoustic chambers, fabric/grille impedance zones, and two wide-angle microphone modules. The geometry is a competitor-informed packaging assumption and is not an acoustic-performance claim.

### 6.5 Thermal path

Use a dual-path passive conduction architecture derived from Dixie:

- QC7790 package proxy: 35 × 35 × 2 mm;
- package TIM: 35 × 35 × 1 mm, initial `k = 3 W/m·K`;
- copper spreader: 100 × 80 × 2 mm;
- two 6 mm heat-pipe proxies routed to an aluminium spreader/chassis zone;
- aluminium chassis interface: 220 × 120 × 2.5 mm;
- secondary rear-hatch TIM: 80 × 40 × 1.5 mm, initial `k = 8 W/m·K`.

Preserve the approved natural-convection, fanless baseline at 35 °C and the existing ten-source Heavy Load budget totalling exactly 57 W. Delivered laptop charging power is not added to the internal thermal load; only conversion and conduction loss may be added in a separately identified case.

## 7. Materials

Use these baseline material intents:

- rear/front polymer structure: PCR PC/ABS, UL94 V-0 intent;
- display glass: generic soda-lime/aluminosilicate equivalent;
- aluminium mid-frame/spreaders: Al 6061;
- die-cast stand joints: ADC12 equivalent;
- sheet brackets/shields: SECC/SGCC, 0.8–1.2 mm;
- stand structural plate: carbon steel;
- heat pipes/spreader inserts: copper;
- PCB: orthotropic or FLOEFD equivalent FR-4 stack;
- speaker magnets and fasteners: simplified steel equivalents;
- internal fluid: air.

Exact production grades remain assumptions until supplier selection and qualification.

## 8. Part metadata and data flow

Every semantic part must carry or map to:

- `PartID`
- `PartName`
- `ParentAssembly`
- `MaterialIntent`
- `SourceClass` (`Known`, `Derived`, `DixieReference`, `CompetitorOfficial`, `EngineeringAssumption`)
- `SourceReference`
- `Confidence`
- `ManufacturingAuthority` (always `false` for this prototype)
- `ThermalDisposition` (`Keep`, `Aggregate`, `Suppress`)
- `HeatLoadW`
- `Revision`

The parameter module is the source of truth. Builders consume parameters; review scripts produce evidence; exporters only publish artifacts after validation. No builder may hard-code an unrecorded product dimension.

## 9. Outputs

Create a dedicated `cad/lod3-inferred-prototype-01/` package containing:

1. `Hinoki_LOD3_Inferred_Master.FCStd`
2. `Hinoki_LOD3_Full_Assembly.step`
3. `Hinoki_LOD3_Head.step`
4. `Hinoki_LOD3_Display.step`
5. `Hinoki_LOD3_Electronics_Thermal.step`
6. `Hinoki_LOD3_Stand_Base.step`
7. `Hinoki_LOD3_Part_Manifest.json`
8. `Hinoki_LOD3_Validation.json`
9. front, rear, isometric, exploded, and airflow-cutaway PNG review images
10. derived FLOEFD solid STEP, internal-air STEP, setup JSON, and review JSON
11. parameter, builder, review, preview, derivation, and export scripts

## 10. Validation and failure handling

### 10.1 LOD 3 master hard gates

- 80–120 uniquely named semantic parts.
- Every exported physical part has valid non-null geometry and positive volume, except explicit sheet/reference objects.
- No unauthorised solid intersections above 0.01 mm³.
- All parts belong to the required top-level assembly group.
- Overall head and stand envelopes match the approved dimensions within 0.1 mm.
- VESA pitch, stand travel, tilt, and swivel match approved values.
- Extreme stand positions do not self-interfere.
- Wall, rib, boss, bend, hole, hatch, fastener, vent, and thermal-contact evidence is present.
- Every semantic part has complete metadata and a non-empty source reference.
- All official STEP outputs reopen successfully with preserved millimetre scale and expected semantic-body counts.

### 10.2 FLOEFD derivative hard gates

- one connected internal-air solid;
- internal air disjoint from every retained solid within 0.01 mm³;
- inlet and outlet connected to the air region and unobstructed;
- each vent preserves at least 6000 mm² opening area or an explicitly recorded impedance-equivalent opening;
- all retained solids are valid and closed;
- ten heat sources sum to exactly 57 W;
- material map covers every retained solid and air region;
- derived geometry remains within the master envelope;
- no stand/base solids are included in the internal head airflow domain unless intentionally designated as external thermal boundaries.

### 10.3 Atomic publication

FCStd, STEP, JSON, and PNG artifacts are staged to same-directory temporary paths. Reopen and validate all members of an output set before replacement. On any exception or failed hard gate:

- emit only the failure sentinel;
- preserve every pre-existing formal output byte-for-byte;
- remove temporary files;
- close every FreeCAD document;
- return a failing process status.

## 11. Review images

Generate non-rendered, shaded-with-edges images on a white background:

- front assembly;
- rear assembly with service zones;
- isometric translucent-housing view;
- exploded assembly;
- airflow cutaway showing inlet, outlet, obstruction, and thermal path.

Images are review aids only and must not be used as evidence that hidden geometry passed validation.

## 12. Testing strategy

Implement tests before each builder/exporter feature. Tests use temporary output paths and may never overwrite formal artifacts. Cover:

- frozen parameter and source-authority contract;
- required assembly hierarchy and metadata;
- geometry/body validity and envelope;
- authorised-contact and unauthorised-overlap matrices;
- stand kinematic extrema and non-interference;
- vent opening and air connectivity;
- heat-load total and material coverage;
- master-to-FLOEFD suppression map;
- atomic publication, rollback, cleanup, and unique sentinels;
- formal FCStd and STEP reopen probes;
- review-image existence and dimensions.

Do not run or rewrite superseded Iteration 01/02 product-review artifacts as part of LOD 3 verification.

## 13. Completion criteria

The design is complete only when:

1. all master and derived hard gates pass;
2. all formal artifacts reopen independently;
3. the LOD 3 part manifest contains 80–120 traceable semantic parts;
4. stand motion and interference evidence pass;
5. the derived FLOEFD package preserves the approved 35 °C, 57 W, fanless natural-convection case;
6. all review images are readable on a phone;
7. the validation report says `Pass` while clearly retaining the inferred-prototype and non-release limitations;
8. targeted tests and `git diff --check` pass with no unrelated Iteration artifact changes.
