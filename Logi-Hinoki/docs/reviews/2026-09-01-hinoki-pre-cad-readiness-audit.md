# Hinoki Pre-CAD Readiness Audit

**Audit date:** 2026-09-01
**Scope:** Decide whether a complete Hinoki desktop-system CAD Iteration 01 can start. No CAD or STEP was created for this audit.

## Decision

**FULL-SYSTEM CAD ITERATION 01: BLOCKED.**

The head architecture, frozen requirements, power-to-space-claim mapping, and 18-item package register are internally consistent enough for a concept head layout. However, the required height- and tilt-adjustable desktop stand has no documented height travel, tilt-angle, base support polygon, or preliminary mass/center-of-gravity input. Without these, a full-system CAD model cannot demonstrate DR-18 through DR-21 and risks producing an arbitrary or unstable stand.

The block can be cleared by recording controlled assumptions or approved requirements for:

1. Height-adjustment travel and its reference point.
2. Neutral, maximum-forward, and maximum-rearward tilt angles.
3. Base support polygon / footprint and preliminary ballast allocation.
4. Preliminary head, stand and base mass allocation for a center-of-gravity check.

These inputs are `Assumed` until engineering validation; they must not change any Frozen parameter.

## Evidence checked

| Evidence | Result | Audit finding |
|---|---|---|
| Master Parameter Table and Frozen Baseline | Pass | 21 direct Known requirements frozen; ambient-light provision remains Conditional. |
| Assumption Log | Pass with open controls | A-013 through A-034 record package and preliminary-power inputs. No assumption is marked Frozen. |
| Dixie-to-Hinoki Architecture Mapping | Pass | Dixie principles are retained without geometric scaling. |
| Preliminary Power Budget | Pass | Power-to-CAD mapping passes: all 11 heat sources map to an SC-ID; laptop-delivered 90 W is separate from 7.8 W PD loss. |
| Internal Space-Claim Register | Pass | 18 claims; all contained; hard-package collision count = 0; hard-package reserve ratio = 74.9%. |
| Formula/error scan | Pass | No `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or `#N/A` entries. |

## Checklist disposition

`Pass` means the pre-CAD evidence is sufficient. `Exception` means the criterion is explicitly controlled by an open assumption and must be measured in CAD. `Pending CAD` means no model exists yet to perform the required measurement. `Blocker` prevents the complete system CAD iteration from starting.

| ID | Status | Pre-CAD audit disposition |
|---|---|---|
| DR-01 Overall dimensions | Pass | A-013 establishes the 760 × 540 × 80 mm head envelope. |
| DR-02 Panel geometry | Pass | A-014 provides 730 × 420 × 18 mm reservation and containment pass. |
| DR-03 Bezel | Exception | Panel active area and final stack-up are unselected; A-014 controls the reservation only. |
| DR-04 Camera location | Pass | SC-003 is top-center, X = 0, and fits A-016. |
| DR-05 Camera FOV clearance | Pending CAD | 134° and 140° ray studies require the CAD camera/shutter/front-bar geometry. |
| DR-06 Privacy shutter | Pending CAD | A-016 reserves the package; travel, end stops and captive retention require mechanism geometry. |
| DR-07 Speaker packaging | Pass | SC-004/005 reserve two upper 170 × 55 × 40 mm enclosures. |
| DR-08 Microphone locations | Exception | SC-008 reserves outer upper-bar regions; acoustic paths await detailed geometry. |
| DR-09 SOM packaging | Pass | SC-009 reserves central QC7790/spreader volume; A-019 controls it. |
| DR-10 PCB packaging | Exception | SC-010/011/012 provide named volumes; board outlines, mounts and service directions await EE data. |
| DR-11 USB-C PD section | Pass | Base bulk PD and head interface split is defined; SC-011 and A-020/A-030 are traceable. |
| DR-12 I/O accessibility | Pending CAD | All required interfaces have a claim; insertion and service sweeps require connector models. |
| DR-13 Cable clearance | Exception | SC-018 preserves a cable/service keep-out; selected cable bend radius is open under A-029. |
| DR-14 Radar | Exception | SC-014 provides separate module/field-path keep-out; field geometry awaits selected radar. |
| DR-15 Ambient-light sensor | Exception | SC-015 preserves a conditional optical path under A-025. |
| DR-16 Front lighting | Exception | SC-006/007 have package claims; 140° FOV non-intrusion awaits CAD ray overlay. |
| DR-17 VESA | Exception | SC-013 reserves reinforcement; A-010 100 × 100 mm pitch remains unconfirmed. |
| DR-18 Desktop stand | **Blocker** | Architecture calls for an adjustable stand, but no stand package, support footprint or load allocation exists. |
| DR-19 Height adjustment | **Blocker** | No travel range, end-state geometry or reference point is recorded. |
| DR-20 Tilt mechanism | **Blocker** | No neutral/forward/rearward angles or mechanism envelope is recorded. |
| DR-21 Center of gravity | **Blocker** | No preliminary component masses, base ballast mass or support polygon exists. |
| DR-22 Thermal architecture | Pass | Conduction path, vent keep-outs and power boundary are documented; load values remain explicitly preliminary. |
| DR-23 Component interference | Pass for package level | 18 claims contain; hard-package collision count is zero. Full solid/fastener/motion analysis awaits CAD. |
| DR-24 STEP integrity | Not applicable | Handoff-only gate; no CAD/STEP exists. |

## Required actions before re-audit

1. Add new Assumption Log rows for stand travel, tilt angles, base footprint and mass/ballast allocation.
2. Add a stand/base space-claim register with neutral and both end-motion states.
3. Re-run DR-18 through DR-21 against the new claims.
4. If those four items pass or have explicit approved exceptions, change this report to `Conditional approval for concept CAD Iteration 01`.

## Boundaries after approval

Even after the blockers are cleared, Iteration 01 may use only the `Known` frozen requirements and labelled `Assumed` packages. It may not release production dimensions, issue a STEP handoff, or score a final design until CAD-dependent checks (FOV, shutter motion, connector access, moving-interference, CG and STEP re-import) are completed.
