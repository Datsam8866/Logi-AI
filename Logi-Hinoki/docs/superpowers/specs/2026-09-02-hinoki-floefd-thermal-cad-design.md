# Hinoki FLOEFD Natural-Convection Thermal CAD Design

Date: 2026-09-02  
Status: Approved design; pending written-spec acknowledgement

## Objective

Create a simplified multi-body CAD model for Simcenter FLOEFD conjugate heat-transfer analysis. The model represents solid conduction plus internal and external air convection for a fanless, naturally ventilated Hinoki head.

This deliverable is a thermal-analysis model. It is not industrial-design review geometry, manufacturing CAD, structural-release geometry, or a complete product assembly. The earlier Calm Crown publication/render/stand/motion plan is not a prerequisite for this thermal model.

## Frozen Analysis Inputs

- Solver target: Simcenter FLOEFD.
- Analysis type: conjugate heat transfer.
- Cooling architecture: passive natural convection; no fan.
- Orientation: head upright.
- Gravity: vertically downward in the product coordinate system.
- Ambient temperature: 35 °C.
- Operating case: Heavy Load.
- Total internal dissipation: 57 W.
- Vent direction: lower/rear-lower intake and rear-upper exhaust.
- External computational domain: created in FLOEFD, not as product CAD.

## Heavy-Load Heat Sources

The model shall retain separate named heat-source solids so FLOEFD loads can be edited independently.

| Heat-source body | Load |
|---|---:|
| `Heat_Panel_Backlight` | 20.0 W |
| `Heat_QC7790` | 12.0 W |
| `Heat_Memory` | 2.0 W |
| `Heat_Carrier_PMIC` | 5.0 W |
| `Heat_IO` | 5.0 W |
| `Heat_WiFi_BLE` | 1.5 W |
| `Heat_Camera` | 3.0 W |
| `Heat_Audio` | 4.0 W |
| `Heat_Radar_ALS` | 0.5 W |
| `Heat_Front_Lighting` | 4.0 W |
| **Total** | **57.0 W** |

USB-C laptop-delivered power is excluded from product dissipation. The Heavy Load case assigns no USB-C PD conversion loss.

Source: `outputs/2026-09-01-pre-cad-readiness/Hinoki_Preliminary_Power_Budget_and_Space_Claim.xlsx`, sheet `Preliminary Power Budget`, Heavy Load column.

## Simplified Geometry

### Product envelope

- Head envelope: 742 W × 492 H × 62 D mm.
- Cover glass: 3 mm nominal thickness.
- Rear enclosure: 2.5 mm equivalent wall thickness.
- Aluminum mid-frame: 2 mm nominal thickness.
- The model excludes stand, base, motion states, cosmetic reveals, shutters, buttons, screws, bosses, fine connector geometry, detailed vent grilles, logos, and publication surfaces.

### Thermal solids

The native model shall contain separate, named, valid solids for:

- cover glass;
- panel/backlight equivalent solid;
- aluminum mid-frame;
- rear PC/ABS enclosure;
- QC7790 package/source;
- TIM between QC7790 and heat spreader;
- aluminum heat spreader;
- carrier PCB/PMIC;
- memory;
- I/O electronics;
- Wi-Fi/BLE;
- camera electronics;
- left/right audio zones;
- radar/ALS;
- left/right front-light zones.

The conductive path is:

`QC7790 → TIM → aluminum heat spreader → aluminum mid-frame → enclosure/internal air/external ambient`

Intentional thermal interfaces shall touch without volumetric overlap. Unrelated solids shall not intersect.

### Fluid region and vents

- Create one named `Internal_Air_Volume` body representing the connected air space inside the head.
- Create a lower/rear-lower inlet opening of 400 × 15 mm, area 6,000 mm².
- Create a rear-upper outlet opening of 400 × 15 mm, area 6,000 mm².
- The internal air region shall connect to both openings with no blocking solid.
- Do not model grille webs in version 1; FLOEFD porous resistance may be added later when grille data exists.
- The external air domain and environmental pressure boundaries are configured in FLOEFD.

## Preliminary Materials

The FCStd metadata and setup map shall identify these preliminary material assignments:

| Body class | FLOEFD material intent |
|---|---|
| Cover glass | Generic glass |
| Rear enclosure | PC/ABS |
| Mid-frame and heat spreader | Aluminum 6061 |
| TIM | Isotropic equivalent, 3 W/m·K |
| PCB bodies | FLOEFD equivalent PCB material |
| Chip/source blocks | Effective isotropic solid; heat load applied volumetrically |
| Fluid region | Air |

These values are concept assumptions and must remain editable. They do not represent selected production grades.

## Deliverables

Create a dedicated folder `cad/thermal-simulation-01/` containing:

- `Hinoki_Thermal_CHT_Model.FCStd` — native named multi-body model.
- `Hinoki_Thermal_CHT_Solids.step` — solid bodies for FLOEFD import.
- `Hinoki_Thermal_Internal_Air.step` — internal air-region body exported separately.
- `Hinoki_Thermal_FLOEFD_Setup.json` — body names, material intents, heat loads, ambient, gravity, vent areas, units, and assumptions.
- `build_hinoki_thermal_cht.py` — deterministic FreeCAD builder.
- `export_hinoki_thermal_cht.py` — controlled STEP export.
- `review_hinoki_thermal_cht.py` — machine-readable geometry and thermal-input checks.
- `Hinoki_Thermal_CHT_Review.json` — generated review evidence.

Add one focused test module: `tests/test_hinoki_thermal_cht.py`.

## FLOEFD Import Boundary

The CAD deliverable provides named bodies and setup metadata. It does not create a proprietary FLOEFD project file. In FLOEFD:

1. Import `Hinoki_Thermal_CHT_Solids.step`.
2. Assign materials using `Hinoki_Thermal_FLOEFD_Setup.json`.
3. Apply the ten volumetric heat sources totaling 57 W.
4. Use air as the fluid.
5. Set ambient to 35 °C and enable gravity/natural convection.
6. Create an external computational domain around the upright head.
7. Use the lower and upper openings as the natural ventilation path.
8. Use `Hinoki_Thermal_Internal_Air.step` only when an explicit fluid-region body is useful for setup or diagnostics.

## Acceptance Criteria

The model is complete when automated checks prove:

1. Every required solid and the internal-air body exists, is valid, closed, and has finite positive volume.
2. The product envelope is 742 × 492 × 62 mm within 0.1 mm.
3. The lower inlet and upper outlet each have 6,000 mm² open area within 1%.
4. `Internal_Air_Volume` is connected to both vent openings.
5. Every heat-source solid lies inside the enclosure cavity and does not block either vent.
6. Intended thermal interfaces touch; unrelated solids have no volumetric overlap above 0.01 mm³.
7. The ten heat loads sum to exactly 57.0 W.
8. The setup JSON records 35 °C ambient, natural convection, no fan, gravity direction, material intent, and millimetre units.
9. Both STEP files re-import in FreeCAD with valid solids, correct scale, and the intended body counts.
10. Tests and review generation do not overwrite tracked artifacts unintentionally.

## Explicitly Out of Scope

- Product appearance scoring or publication renders.
- Stand/base/tilt/height motion.
- Structural, drop, tip-over, acoustic, optical, RF, compliance, or manufacturing validation.
- Detailed PCB copper, component packages, fasteners, ribs, bosses, cables, connectors, or vent grilles.
- A claim that the 57 W loads, material properties, contact resistances, or geometry are production-released.
- Final temperature limits or pass/fail thresholds; these require selected component specifications.

## Known Limitations

- Most heat-source dimensions and material properties remain preliminary.
- Contact resistance is represented only by the explicit TIM body in version 1.
- Radiation and surface emissivity are configured in FLOEFD rather than encoded in STEP.
- Vent pressure loss is not represented until grille/open-area data is available.
- A 62 mm head may require later vent-area or spreader changes if the 57 W passive case exceeds temperature limits.
