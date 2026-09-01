# Hinoki Pre-CAD Readiness Audit v0.2 — Stand Baseline Resolution

**Audit date:** 2026-09-01
**Scope:** Resolve the four full-system concept-CAD blockers recorded in the v0.1 audit.
**Decision:** **Conditional approval for Hinoki Concept CAD Iteration 01.** This is not a dimensional release, a tooling release, or authorization to export STEP.

## Evidence reviewed

| Evidence | Purpose |
|---|---|
| `docs/reviews/2026-09-01-hinoki-pre-cad-readiness-audit.md` | v0.1 audit and original four blockers |
| `docs/reviews/2026-09-01-hinoki-cad-design-review-checklist.md` | CAD acceptance criteria DR-01 through DR-24 |
| `outputs/2026-09-01-pre-cad-readiness/Hinoki_Preliminary_Power_Budget_and_Space_Claim.xlsx` | Preserved v0.1 frozen baseline, power budget and head space claims |
| `outputs/2026-09-01-pre-cad-readiness-v02/Hinoki_Pre_CAD_Readiness_v02_Stand_Baseline.xlsx` | v0.2 controlled stand assumptions, calculations and stand/base claims |

## Controlled additions (all Assumed; open)

| Assumption ID | Controlled concept value | Why it is sufficient for concept CAD | Release dependency |
|---|---|---|---|
| A-035 | VESA pivot 430 mm above desk; 120 mm travel; 370–490 mm sweep | Defines column, head and cable motion envelope. | Ergonomic study and mechanism selection |
| A-036 | −5° forward / 0° neutral / +20° rearward tilt | Defines three kinematic review states. | Hinge selection and motion-interference review |
| A-037 | 500 W × 340 D mm base contact polygon; Y = −140 / +200 mm from column | Provides a measurable first support polygon. | Mass model, tip test and ID approval |
| A-038 | Head 11.0 kg; moving stand 2.0 kg; base/power/ballast 10.0 kg; cable 0.5 kg; head CG sweep ±15 mm | Enables a first static CG screen while actual component masses are TBD. | BOM mass properties and physical tip test |
| A-039 | 500 W × 340 D × 90 H mm outer base; contains 360 × 260 × 90 mm power/PD/ballast package | Preserves the accepted base-versus-head power architecture. | Power architecture, thermal details and component drawings |
| A-040 | Static front/rear support-boundary margin ≥75 mm | Sets a transparent concept screen; it is not a compliance limit. | Load cases, test plan and physical tip test |

## Stand/stability calculation check

Local datum: column centre at desk plane; X = left/right, Y = rearward positive, Z = upward.

| Review state | Total mass | Assembly CG Y | Front margin | Rear margin | Side margin | Result |
|---|---:|---:|---:|---:|---:|---|
| Forward tilt; head CG Y = −15 mm | 23.5 kg | 13.8 mm | 153.8 mm | 186.2 mm | 250.0 mm | Pass |
| Neutral; head CG Y = 0 mm | 23.5 kg | 20.9 mm | 160.9 mm | 179.1 mm | 250.0 mm | Pass |
| Rearward tilt; head CG Y = +15 mm | 23.5 kg | 27.9 mm | 167.9 mm | 172.1 mm | 250.0 mm | Pass |

The minimum calculated front/rear margin is 153.8 mm, exceeding the A-040 concept screen by 78.8 mm. This result is conditional on A-037 and A-038; it must be recalculated when selected component mass properties are available.

## Checklist disposition update

| DR | v0.2 disposition | Rationale / required next check |
|---|---|---|
| DR-01 Overall dimensions | Pass — conditional | Head envelope remains an Assumed concept envelope; CAD must expose it as a parameter. |
| DR-02 Panel geometry | Pass — conditional | Preserve current stack claim; selected panel data must replace assumptions. |
| DR-03 Bezel | Pending CAD | Model-to-confirm against active-area and touch-stack data. |
| DR-04 Camera location | Pass — conditional | Top-centre architecture is maintained. |
| DR-05 Camera FOV clearance | Pending CAD | Ray-envelope clearance must be checked at all tilt states. |
| DR-06 Privacy shutter | Pending CAD | Manual, non-removable shutter motion and optical obscuration are CAD checks. |
| DR-07 Speaker packaging | Pass — conditional | Speakers remain in the upper AV bar; final acoustic volume/grille remains open. |
| DR-08 Microphone locations | Pass — conditional | Front mic-zone intent is retained; final locations require acoustic validation. |
| DR-09 SOM packaging | Pass — conditional | Central thermal-module claim retained; QC7790 carrier/module drawings remain open. |
| DR-10 PCB packaging | Pass — conditional | Board clearances and service removal are CAD checks. |
| DR-11 USB-C PD section | Pass — conditional | Head interface / base bulk-PD split retained; connector and protection parts TBD. |
| DR-12 I/O accessibility | Pending CAD | Port reach, insertion sweep and user-facing labels must be checked. |
| DR-13 Cable clearance | Pass — conditional | A-035/A-036 define the sweep; flex, bend radius and routing must be modeled. |
| DR-14 Radar | Pass — conditional | Front radar zone claim retained; final module, mask and RF clearance TBD. |
| DR-15 Ambient-light sensor | Approved exception | Optional feature remains conditionally applicable; use an approved blanking strategy if omitted. |
| DR-16 Lighting | Pass — conditional | Front-light zone retained; optical, thermal and diffuser details remain open. |
| DR-17 VESA | Pass — conditional | VESA interface is CAD-driving; pattern and fasteners require selection. |
| DR-18 Stand | Pass — conditional | A-035, A-037 and A-039 define a space-claim baseline. |
| DR-19 Height adjustment | Pass — conditional | A-035 provides 120 mm concept travel and 370–490 mm pivot sweep. |
| DR-20 Tilt mechanism | Pass — conditional | A-036 provides the three review states; mechanism hardware is not selected. |
| DR-21 Centre of gravity | Pass — conditional | Static screen passes all three states under A-038/A-040. |
| DR-22 Thermal architecture | Pass — conditional | Thermal split and v0.1 power model are retained; CFD/thermal validation remains required. |
| DR-23 Component interference | Pending CAD | Must be completed with the motion, cable and service envelopes in Iteration 01. |
| DR-24 STEP integrity | Not applicable | No CAD or STEP has been generated in this audit scope. |

## Entry conditions for Concept CAD Iteration 01

1. Keep A-035 through A-040 visible as **Assumed** parameters in the CAD master layout; do not convert them to Known values.
2. Model the head, stand, base and cables at low, neutral and high/tilt end states; run DR-05, DR-06, DR-12, DR-13 and DR-23 against those states.
3. Recalculate CG after panel, speakers, power hardware, ballast and stand mechanism have actual mass properties.
4. Do not issue release geometry, tooling data or STEP until all CAD-dependent checklist items have evidence and all conditional assumptions are resolved or formally accepted.

## Traceability and integrity checks

- v0.1 workbook remains unchanged; v0.2 is a separate, versioned deliverable.
- v0.2 includes all six expected sheets, assumptions A-035 through A-040, and the new `Stand & Stability` calculation/space-claim sheet.
- The three static stability states return `Pass`.
- Workbook formula-error scan found zero `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` or `#N/A` errors.
