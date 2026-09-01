# Hinoki Iteration 02 — Market Component Candidate Design

Date: 2026-09-01
Status: Approved for planning

## Objective

Use Dixie as the architectural and component baseline, then evaluate current market components against Hinoki requirements. Produce a source-traceable candidate set that can replace Iteration 01 assumed CAD envelopes without presenting unverified data as release authority.

## Scope

### Wave 1 — CAD-driving components

1. 32-inch 4K panel and projected-capacitive touch stack
2. Camera sensor, lens and privacy-shutter envelope
3. Speakers and microphones
4. QC7790 SOM / compute thermal envelope
5. Articulating stand and VESA interface
6. USB-C PD and primary I/O connector envelopes

### Wave 2 — Deferred until Wave 1 review

1. Radar
2. Ambient-light sensor
3. Front video-fill lighting
4. Detailed thermal components

Wave 2 is excluded from the first candidate workbook unless a Wave 1 dependency requires an early placeholder.

## Source Hierarchy

Use sources in this order:

1. Manufacturer datasheet or official technical documentation
2. Manufacturer product page or official CAD portal
3. Authorized distributor technical page
4. Reputable component database, clearly marked as secondary

Every researched candidate must include a source URL and access date. Values that cannot be verified from an acceptable source must be marked `Unverified`; they must not be inferred from photographs, family-level specifications or neighboring part numbers.

## Candidate Set

Retain two to four viable market part numbers per subsystem when sufficient verified options exist. Each candidate record must include:

- Subsystem
- Manufacturer
- Exact part number
- Lifecycle / availability evidence when published
- Key performance specifications
- Mechanical envelope and mass when published
- Power and electrical interface
- Required companion parts
- Datasheet and CAD / STEP availability
- Dixie reference or inherited design intent
- Hinoki requirement mapping
- Open compliance gaps
- Source URLs and access date
- Verification status
- Weighted score
- Recommendation: Preferred / Alternate / Hold / Reject
- Selection or rejection rationale

Do not fill a numerical field with an estimate unless it is explicitly labeled as an engineering assumption and linked to a new or existing assumption ID.

## Scoring Model

| Dimension | Weight | Interpretation |
|---|---:|---|
| Hinoki specification fit | 35% | Required function and performance compliance |
| CAD / mechanical fit | 25% | Envelope, mounting, keep-out and serviceability |
| Electrical / interface fit | 15% | SOM, display, camera, audio, PD and I/O compatibility |
| Thermal / power risk | 10% | Dissipation, supply requirement and cooling burden |
| Datasheet / STEP completeness | 10% | Quality of dimensional evidence and CAD availability |
| Availability confidence | 5% | Published lifecycle and authorized-channel evidence |

Each dimension uses a 0–5 score. The weighted total is calculated as:

`SUM(dimension score × dimension weight) / 5 × 100`

A high score does not override a hard requirement. Any hard mismatch must be recorded and may force `Hold` or `Reject` regardless of total score.

## Deliverables

1. `Hinoki_Iteration02_Component_Candidates.xlsx`
2. Iteration 02 component selection and risk review in `docs/reviews/`
3. Proposed Master Parameter / Assumption Log updates, without silently overwriting user-owned assumptions
4. Preferred, alternate and rejected candidates with explicit rationale
5. A CAD envelope table for preferred candidates, including source status and unresolved keep-outs

## Workbook Design

The workbook will contain:

- `Summary`: preferred candidates, subsystem status, hard gaps and next decisions
- `Candidates`: auditable candidate rows and formula-driven weighted scores
- `Requirements`: Hinoki requirements and Dixie reference mapping
- `CAD Envelopes`: dimensions, datums, mounting interfaces and keep-outs
- `Sources`: source type, URL, access date and verification notes
- `Scoring Guide`: visible 0–5 scoring definitions and weights

Scores, status summaries and rankings must be formula-driven. Candidate facts remain source-backed inputs. Formula errors and missing required sources must be surfaced as quality-control exceptions.

## Research and Decision Rules

- Prefer a slightly lower-scoring candidate with verified dimensions over a higher-scoring candidate whose envelope is undocumented.
- Separate a bare component from its required module, carrier, lens holder, amplifier, cable or thermal solution.
- Do not treat a sensor-only part number as a complete camera solution.
- Do not treat a panel active area as the module outline.
- Do not claim QC7790 mechanical dimensions without a public SOM or vendor document.
- Preserve Dixie architecture only where Hinoki requirements do not invalidate it.
- Record conflicts between marketing pages and datasheets; the latest official datasheet governs unless revision context shows otherwise.

## Verification and Success Criteria

Wave 1 is complete when:

1. Every subsystem has two to four verified candidates, or a documented evidence gap explains why it does not.
2. Every retained candidate has at least one acceptable primary or authorized-distributor source.
3. Every preferred candidate has a usable mechanical envelope or is explicitly blocked from CAD adoption.
4. Weighted scores calculate without spreadsheet errors and hard mismatches remain visible.
5. The review identifies which Iteration 01 assumptions can close, which remain open and which new assumptions are required.
6. No CAD geometry is promoted to release authority solely from an unverified source.

## Known Risks

- Current commercial availability may differ by region or customer agreement.
- Panel, camera module and SOM details may be NDA-controlled.
- Public distributor dimensions may omit connector, cable and thermal keep-outs.
- A market part number can support concept CAD but still require vendor confirmation before sourcing or release.
