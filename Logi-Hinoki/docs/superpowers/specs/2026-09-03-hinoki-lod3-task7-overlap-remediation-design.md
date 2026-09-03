# Hinoki LOD 3 Task 7 Overlap Remediation Design

## 1. Purpose

Task 7 must validate the complete head-only Task 5 checkpoint without hiding
pre-existing solid intersections. The current 79-part physical collision domain
contains 28 unauthorised overlaps above the 0.01 mm3 hard-gate threshold. This
remediation corrects those geometries while preserving the approved product
envelope, primary electronics placement, VESA interface, and passive thermal
contact chain.

The result remains an LOD 3 inferred engineering prototype; not manufacturing
release. It does not create authority for tooling, GD&T, supplier release,
certification, or production temperature claims.

## 2. Approved approach

Use local clearance and proxy-shape corrections instead of moving the major
assemblies:

1. Keep the 742 x 492 x 62 mm head envelope unchanged.
2. Keep board dimensions and nominal board positions unchanged.
3. Keep the VESA 100 x 100 mm interface unchanged.
4. Keep the QC7790-to-rear-hatch passive thermal contact chain unchanged.
5. Do not authorise volumetric penetration merely because two parts have a
   mechanical or thermal relationship.
6. Do not raise the 0.01 mm3 threshold or reduce the physical collision domain.

Moving primary boards or the thermal assembly is rejected because it would
invalidate the existing packaging and thermal assumptions. Adding the 28 pairs
to the authorised-contact matrix is rejected because it would convert geometry
errors into false validation passes.

## 3. Geometry remediation

### 3.1 VESA reinforcement, bosses, and fasteners

- Cut four clearance holes through the VESA reinforcement at the existing
  100 x 100 mm boss and fastener locations.
- Keep the reinforcement's outer envelope and material intent unchanged.
- Reshape the four VESA-region bosses so they retain positive structural proxy
  volume without penetrating the Carrier PCB or aluminium interface.
- Keep fasteners as separate physical solids and require zero volumetric overlap
  with the reinforcement.

### 3.2 Structural ribs

- Add local reliefs to ribs 01, 03, and 04 at the affected connector, heat-source,
  heat-pipe, and aluminium-interface volumes.
- Preserve the controlled 1.7 mm rib thickness wherever the rib remains.
- Keep each rib a valid positive solid and preserve its existing semantic
  identity, metadata, and parent assembly.
- Do not move the boards, connectors, heat pipes, or aluminium interface to make
  the test pass.

### 3.3 Shield and heat-source proxies

- Replace the Power and I/O shield solid boxes with thin-wall open-bottom shield
  shapes so their connectors can occupy the intended openings without
  volumetric penetration.
- Separate Heat_IO from the I/O harness connector by reducing or locally
  relieving the heat-source proxy while preserving its 5 W heat-load metadata.
- Add a local clearance to the copper spreader for the carrier board-to-board
  connector while preserving the QC7790/TIM/spreader/heat-pipe/interface thermal
  path.
- Proxy corrections must retain the same semantic names, source classes,
  material intents, heat loads, and ManufacturingAuthority=false.

## 4. Validation contract

The validator must:

- inspect every physical semantic part in the head-only checkpoint;
- exclude only reference/keep-out objects and objects explicitly marked
  non-colliding by the established contract;
- calculate every unique unordered physical-part pair;
- exempt only the three approved camera/front-light heat contacts;
- report every remaining intersection above 0.01 mm3;
- return status and overall equal to Pass only when every active hard gate passes;
- keep stand envelope, stand motion, cable routing, and full-product gates
  deferred;
- prevent FCStd publication on failure and emit one failure sentinel with a
  non-zero process exit status.

The authorised-contact matrix remains exactly:

- Camera_Module <-> Heat_Camera
- Front_Light_Left <-> Heat_Front_Lighting
- Front_Light_Right <-> Heat_Front_Lighting

## 5. Test strategy

1. Preserve the existing independent 79-part pairwise test as the RED proof.
2. Remediate one collision category at a time and rerun the targeted test after
   each category.
3. Require the independent oracle and validator to report zero forbidden
   overlaps.
4. Re-run the complete LOD 3 suite and existing subsystem assertions.
5. Verify all physical parts retain valid, non-null, positive-volume geometry;
   eight-group ownership and complete metadata remain unchanged.
6. Verify head envelope tolerance remains +/-0.1 mm and the exact authorised
   contact set is unchanged.
7. Run git diff --check and confirm only approved Task 7 remediation files are
   included.

## 6. Scope

Files may be modified only where needed to correct the confirmed overlaps:

- cad/lod3-inferred-prototype-01/hinoki_lod3_display_housing.py
- cad/lod3-inferred-prototype-01/hinoki_lod3_electronics_thermal.py
- cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py, only if a controlled
  clearance dimension is required
- cad/lod3-inferred-prototype-01/review_hinoki_lod3.py
- cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py
- tests/test_hinoki_lod3_inferred.py

This remediation does not add stand/base geometry, cable-route solids,
full-product STEP, review images, or FLOEFD derivatives. It does not modify or
regenerate Iteration 01, Iteration 02, or formal output artifacts.

## 7. Completion criteria

Task 7 is complete only when:

- the independent full-pairwise probe finds zero unauthorised overlaps above
  0.01 mm3 across all head physical parts;
- the validator reports the same zero-overlap result and overall Pass;
- the exact three-pair authorised-contact matrix remains unchanged;
- all Task 7 and full LOD 3 tests pass from temporary output paths;
- failure paths stop publication with one sentinel and a non-zero exit status;
- no formal FCStd or JSON artifact is rewritten before all gates pass.
