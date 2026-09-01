import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const scriptPath = fileURLToPath(import.meta.url);
const projectRoot = path.resolve(path.dirname(scriptPath), "..");
const sourcePath = path.join(projectRoot, "data", "iteration-02", "component_candidates.json");
const outputDir = path.join(projectRoot, "outputs", "hinoki-iteration02-review");
const outputPath = path.join(outputDir, "Hinoki_Iteration02_Component_Candidates.xlsx");
const previewDir = path.join(os.tmpdir(), "codex-hinoki-iteration02-workbook-previews");
const source = JSON.parse(await fs.readFile(sourcePath, "utf8"));

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const candidates = workbook.worksheets.add("Candidates");
const requirements = workbook.worksheets.add("Requirements");
const envelopes = workbook.worksheets.add("CAD Envelopes");
const sources = workbook.worksheets.add("Sources");
const scoring = workbook.worksheets.add("Scoring Guide");

const colors = {
  navy: "#17324D",
  teal: "#0F766E",
  paleTeal: "#D9F0EC",
  paleBlue: "#E7F0F8",
  paleAmber: "#FFF3CD",
  paleRed: "#FCE8E6",
  paleGreen: "#DFF2E1",
  gray: "#667085",
  lightGray: "#E5E7EB",
  white: "#FFFFFF",
};

function titleBand(sheet, range, title, subtitle) {
  sheet.showGridLines = false;
  sheet.getRange(range).merge();
  const titleCell = sheet.getRange(range.split(":")[0]);
  titleCell.values = [[title]];
  titleCell.format = {
    fill: colors.navy,
    font: { bold: true, color: colors.white, size: 18 },
    verticalAlignment: "center",
  };
  titleCell.format.rowHeight = 34;
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format = { font: { color: colors.gray, italic: true, size: 10 } };
}

function styleHeader(range) {
  range.format = {
    fill: colors.teal,
    font: { bold: true, color: colors.white },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: colors.teal },
  };
  range.format.rowHeight = 30;
}

function addStatusFormatting(range) {
  range.conditionalFormats.add("containsText", { text: "Preferred", format: { fill: colors.paleGreen, font: { color: "#176B2C", bold: true } } });
  range.conditionalFormats.add("containsText", { text: "Alternate", format: { fill: colors.paleBlue, font: { color: "#1F4E79", bold: true } } });
  range.conditionalFormats.add("containsText", { text: "Hold", format: { fill: colors.paleAmber, font: { color: "#8A5A00", bold: true } } });
  range.conditionalFormats.add("containsText", { text: "Reject", format: { fill: colors.paleRed, font: { color: "#A61B1B", bold: true } } });
}

function textOrBlank(value) {
  return value === null || value === undefined ? "" : value;
}

titleBand(
  scoring,
  "A1:D1",
  "Hinoki Iteration 02 — Scoring Guide",
  "Visible weights and 0–5 definitions. A high score never overrides a hard requirement.",
);
scoring.getRange("A4:D4").values = [["Dimension", "Weight", "0 score", "5 score"]];
styleHeader(scoring.getRange("A4:D4"));
const scoringRows = [
  ["Hinoki specification fit", source.scoring_weights.specification_fit, "Hard mismatch or no evidence", "All required performance verified"],
  ["CAD / mechanical fit", source.scoring_weights.cad_mechanical_fit, "Does not fit", "Verified envelope, datums and keep-outs"],
  ["Electrical / interface fit", source.scoring_weights.electrical_interface_fit, "Incompatible interface", "Directly compatible and documented"],
  ["Thermal / power risk", source.scoring_weights.thermal_power_risk, "Unbounded or unacceptable risk", "Low risk with complete evidence"],
  ["Datasheet / CAD completeness", source.scoring_weights.documentation_completeness, "No usable documentation", "Official datasheet and CAD available"],
  ["Availability confidence", source.scoring_weights.availability_confidence, "No availability evidence", "Current manufacturer and channel evidence"],
];
scoring.getRange("A5:D10").values = scoringRows;
scoring.getRange("B5:B10").format.numberFormat = "0%";
scoring.getRange("A12:D12").merge();
scoring.getRange("A12").values = [["Weighted score = SUM(dimension score × weight) / 5 × 100"]];
scoring.getRange("A12").format = { fill: colors.paleTeal, font: { bold: true, color: colors.navy } };
scoring.getRange("A:D").format.wrapText = true;
scoring.getRange("A:A").format.columnWidth = 30;
scoring.getRange("B:B").format.columnWidth = 12;
scoring.getRange("C:D").format.columnWidth = 34;
scoring.freezePanes.freezeRows(4);

titleBand(
  candidates,
  "A1:Y1",
  "Hinoki Iteration 02 — Component Candidates",
  `Source access date: ${source.access_date}. Yellow score cells are review inputs; weighted score is formula-driven.`,
);
const candidateHeaders = [
  "Subsystem", "Manufacturer", "Part Number", "Candidate Type", "Width mm", "Height mm", "Depth mm", "Mass kg",
  "Resolution / Performance", "Touch / HFOV", "Interface / VESA", "CAD Availability", "Hard Gap", "Verification",
  "Recommendation", "Rationale", "Spec Fit", "CAD Fit", "Interface Fit", "Thermal / Power", "Docs", "Availability",
  "Weighted Score", "Source URL", "Access Date",
];
candidates.getRange("A4:Y4").values = [candidateHeaders];
styleHeader(candidates.getRange("A4:Y4"));
const candidateRows = source.candidates.map((candidate) => [
  candidate.subsystem,
  candidate.manufacturer,
  candidate.part_number,
  candidate.candidate_type,
  textOrBlank(candidate.width_mm),
  textOrBlank(candidate.height_mm),
  textOrBlank(candidate.depth_mm),
  textOrBlank(candidate.mass_kg),
  candidate.resolution,
  candidate.horizontal_fov_deg === null ? candidate.touch : `${candidate.horizontal_fov_deg}° HFOV`,
  [candidate.interface, candidate.vesa].filter(Boolean).join(" | "),
  candidate.cad_availability,
  candidate.hard_gap,
  candidate.verification_status,
  candidate.recommendation,
  candidate.rationale,
  ...candidate.scores,
  null,
  candidate.source_url,
  new Date(`${candidate.access_date}T00:00:00`),
]);
const candidateEndRow = candidateRows.length + 4;
candidates.getRange(`A5:Y${candidateEndRow}`).values = candidateRows;
for (let row = 5; row <= candidateEndRow; row += 1) {
  candidates.getRange(`W${row}`).formulas = [[
    `=(Q${row}*'Scoring Guide'!$B$5+R${row}*'Scoring Guide'!$B$6+S${row}*'Scoring Guide'!$B$7+T${row}*'Scoring Guide'!$B$8+U${row}*'Scoring Guide'!$B$9+V${row}*'Scoring Guide'!$B$10)/5*100`,
  ]];
}
candidates.getRange(`Q5:V${candidateEndRow}`).format = { fill: colors.paleAmber, numberFormat: "0" };
candidates.getRange(`Q5:V${candidateEndRow}`).dataValidation = { rule: { type: "whole", operator: "between", formula1: 0, formula2: 5 } };
candidates.getRange(`O5:O${candidateEndRow}`).dataValidation = { rule: { type: "list", values: ["Preferred", "Alternate", "Hold", "Reject"] } };
addStatusFormatting(candidates.getRange(`O5:O${candidateEndRow}`));
candidates.getRange(`W5:W${candidateEndRow}`).format.numberFormat = "0.0";
candidates.getRange(`W5:W${candidateEndRow}`).conditionalFormats.add("colorScale", {
  colors: ["#F8696B", "#FFEB84", "#63BE7B"],
  thresholds: ["min", "50%", "max"],
});
candidates.getRange(`E5:H${candidateEndRow}`).format.numberFormat = "0.00";
candidates.getRange(`Y5:Y${candidateEndRow}`).format.numberFormat = "yyyy-mm-dd";
candidates.getRange(`A4:Y${candidateEndRow}`).format.wrapText = true;
candidates.getRange(`A4:Y${candidateEndRow}`).format.borders = { preset: "inside", style: "thin", color: colors.lightGray };
candidates.getRange("A:A").format.columnWidth = 20;
candidates.getRange("B:B").format.columnWidth = 22;
candidates.getRange("C:C").format.columnWidth = 28;
candidates.getRange("D:D").format.columnWidth = 34;
candidates.getRange("E:H").format.columnWidth = 11;
candidates.getRange("I:I").format.columnWidth = 27;
candidates.getRange("J:K").format.columnWidth = 25;
candidates.getRange("L:N").format.columnWidth = 34;
candidates.getRange("O:O").format.columnWidth = 14;
candidates.getRange("P:P").format.columnWidth = 42;
candidates.getRange("Q:W").format.columnWidth = 12;
candidates.getRange("X:X").format.columnWidth = 48;
candidates.getRange("Y:Y").format.columnWidth = 13;
candidates.freezePanes.freezeRows(4);
candidates.freezePanes.freezeColumns(4);
candidates.tables.add(`A4:Y${candidateEndRow}`, true, "HinokiCandidates");

titleBand(
  requirements,
  "A1:E1",
  "Hinoki Iteration 02 — Requirements",
  "Hard requirements remain controlling even when a candidate receives a high weighted score.",
);
requirements.getRange("A4:E4").values = [["Requirement ID", "Subsystem", "Requirement", "Hard Requirement", "Current Review State"]];
styleHeader(requirements.getRange("A4:E4"));
const requirementRows = source.requirements.map((requirement) => [
  requirement.id,
  requirement.subsystem,
  requirement.requirement,
  requirement.hard_requirement,
  requirement.id === "R-DISPLAY-01" || requirement.id === "R-HEAD-01" || requirement.id === "R-CAMERA-01"
    ? "Review proxy available"
    : "Open risk / integration evidence required",
]);
requirements.getRange(`A5:E${requirementRows.length + 4}`).values = requirementRows;
requirements.getRange(`D5:D${requirementRows.length + 4}`).format = { fill: colors.paleRed, font: { bold: true, color: "#A61B1B" } };
requirements.getRange(`A4:E${requirementRows.length + 4}`).format.wrapText = true;
requirements.getRange("A:A").format.columnWidth = 18;
requirements.getRange("B:B").format.columnWidth = 22;
requirements.getRange("C:C").format.columnWidth = 58;
requirements.getRange("D:D").format.columnWidth = 16;
requirements.getRange("E:E").format.columnWidth = 36;
requirements.freezePanes.freezeRows(4);

titleBand(
  envelopes,
  "A1:N1",
  "Hinoki Iteration 02 — CAD Envelopes",
  "Only published dimensions are populated. Fit calculations use the current 760 × 80 × 540 mm concept head.",
);
const envelopeHeaders = [
  "Subsystem", "Manufacturer", "Part Number", "Source Status", "Width mm", "Height mm", "Depth mm", "Mass kg",
  "Side Margin mm", "Top Reserve mm", "Depth Reserve mm", "Head Fit", "CAD Adoption", "Open Keep-out",
];
envelopes.getRange("A4:N4").values = [envelopeHeaders];
styleHeader(envelopes.getRange("A4:N4"));
const envelopeCandidates = source.candidates.filter((candidate) => candidate.width_mm !== null && candidate.height_mm !== null && candidate.depth_mm !== null);
const envelopeRows = envelopeCandidates.map((candidate) => [
  candidate.subsystem,
  candidate.manufacturer,
  candidate.part_number,
  candidate.verification_status,
  candidate.width_mm,
  candidate.height_mm,
  candidate.depth_mm,
  textOrBlank(candidate.mass_kg),
  null,
  null,
  null,
  null,
  candidate.recommendation === "Preferred" ? "Review baseline" : "Not adopted",
  candidate.hard_gap,
]);
const envelopeEndRow = envelopeRows.length + 4;
envelopes.getRange(`A5:N${envelopeEndRow}`).values = envelopeRows;
for (let row = 5; row <= envelopeEndRow; row += 1) {
  envelopes.getRange(`I${row}:L${row}`).formulas = [[
    `=(760-E${row})/2`,
    `=540-F${row}`,
    `=80-G${row}`,
    `=IF(AND(E${row}<=760,F${row}<=540,G${row}<=80),"Fits","Does Not Fit")`,
  ]];
}
envelopes.getRange(`E5:K${envelopeEndRow}`).format.numberFormat = "0.00";
envelopes.getRange(`L5:L${envelopeEndRow}`).conditionalFormats.add("containsText", { text: "Fits", format: { fill: colors.paleGreen, font: { color: "#176B2C", bold: true } } });
envelopes.getRange(`L5:L${envelopeEndRow}`).conditionalFormats.add("containsText", { text: "Does Not Fit", format: { fill: colors.paleRed, font: { color: "#A61B1B", bold: true } } });
envelopes.getRange(`A4:N${envelopeEndRow}`).format.wrapText = true;
envelopes.getRange("A:A").format.columnWidth = 20;
envelopes.getRange("B:C").format.columnWidth = 24;
envelopes.getRange("D:D").format.columnWidth = 30;
envelopes.getRange("E:L").format.columnWidth = 14;
envelopes.getRange("M:M").format.columnWidth = 18;
envelopes.getRange("N:N").format.columnWidth = 46;
envelopes.freezePanes.freezeRows(4);

titleBand(
  sources,
  "A1:G1",
  "Hinoki Iteration 02 — Sources",
  "URLs are plain text for auditability. Access date reflects this review run.",
);
sources.getRange("A4:G4").values = [["Subsystem", "Manufacturer", "Part Number", "Source Type", "URL", "Access Date", "Verification Note"]];
styleHeader(sources.getRange("A4:G4"));
const sourceRows = source.candidates.map((candidate) => [
  candidate.subsystem,
  candidate.manufacturer,
  candidate.part_number,
  candidate.source_type,
  candidate.source_url,
  new Date(`${candidate.access_date}T00:00:00`),
  candidate.verification_status,
]);
const sourceEndRow = sourceRows.length + 4;
sources.getRange(`A5:G${sourceEndRow}`).values = sourceRows;
sources.getRange(`F5:F${sourceEndRow}`).format.numberFormat = "yyyy-mm-dd";
sources.getRange(`A4:G${sourceEndRow}`).format.wrapText = true;
sources.getRange("A:A").format.columnWidth = 20;
sources.getRange("B:C").format.columnWidth = 26;
sources.getRange("D:D").format.columnWidth = 24;
sources.getRange("E:E").format.columnWidth = 68;
sources.getRange("F:F").format.columnWidth = 14;
sources.getRange("G:G").format.columnWidth = 38;
sources.freezePanes.freezeRows(4);

titleBand(
  summary,
  "A1:H1",
  "Hinoki Iteration 02 — Preliminary Review Baseline",
  "Decision view for the first CAD-driving wave. This is concept evidence, not release authority.",
);
summary.getRange("A4:B4").values = [["Review Metric", "Formula Result"]];
styleHeader(summary.getRange("A4:B4"));
summary.getRange("A5:A12").values = [
  ["Total candidates"],
  ["Preferred"],
  ["Alternate"],
  ["Hold"],
  ["Reject"],
  ["Panel / Touch average score"],
  ["Camera / Shutter average score"],
  ["Stand / VESA average score"],
];
summary.getRange("B5:B12").formulas = [
  [`=COUNTA('Candidates'!$C$5:$C$${candidateEndRow})`],
  [`=COUNTIF('Candidates'!$O$5:$O$${candidateEndRow},"Preferred")`],
  [`=COUNTIF('Candidates'!$O$5:$O$${candidateEndRow},"Alternate")`],
  [`=COUNTIF('Candidates'!$O$5:$O$${candidateEndRow},"Hold")`],
  [`=COUNTIF('Candidates'!$O$5:$O$${candidateEndRow},"Reject")`],
  [`=AVERAGEIF('Candidates'!$A$5:$A$${candidateEndRow},"Panel / Touch",'Candidates'!$W$5:$W$${candidateEndRow})`],
  [`=AVERAGEIF('Candidates'!$A$5:$A$${candidateEndRow},"Camera / Shutter",'Candidates'!$W$5:$W$${candidateEndRow})`],
  [`=AVERAGEIF('Candidates'!$A$5:$A$${candidateEndRow},"Stand / VESA",'Candidates'!$W$5:$W$${candidateEndRow})`],
];
summary.getRange("B10:B12").format.numberFormat = "0.0";
summary.getRange("D4:H4").values = [["Subsystem", "Review Baseline", "Why", "CAD State", "Blocking Evidence"]];
styleHeader(summary.getRange("D4:H4"));
summary.getRange("D5:H7").values = [
  ["Panel / Touch", "One World Touch LM-3237-26B-4K", "750.4 × 452.7 × 56.5 mm published 4K PCAP envelope fits", "Adopted as external review proxy", "Bare panel/touch stack and internal decomposition"],
  ["Camera / Shutter", "Leopard Imaging LI-IMX477-MIPI-140H", "140° HFOV and dimensioned 38 mm module", "Camera adopted; shutter remains assumption", "ISP architecture, lens ray model, captive shutter travel"],
  ["Stand / VESA", "Ergotron HX 45-475-224 benchmark", "19.1 kg capacity and VESA 200 × 200 support", "Mechanism benchmark only", "Custom base, centre of gravity, tip stability and cable motion"],
];
summary.getRange("D9:H9").merge();
summary.getRange("D9").values = [["CAD Review Numbers"]];
summary.getRange("D9").format = { fill: colors.paleTeal, font: { bold: true, color: colors.navy } };
summary.getRange("D10:H12").values = [
  ["Side margin", "4.8 mm each side", "Top reserve", "87.3 mm", "Very tight width margin"],
  ["Depth reserve", "23.5 mm", "HX pre-AV mass headroom", "5.1 kg", "Display proxy already includes enclosure/electronics"],
  ["Decision", "Pass with open risks", "STEP export", "Blocked", "Keep all open risks visible in CAD review"],
];
summary.getRange("A4:B12").format.borders = { preset: "inside", style: "thin", color: colors.lightGray };
summary.getRange("D4:H12").format.borders = { preset: "inside", style: "thin", color: colors.lightGray };
summary.getRange("A4:H12").format.wrapText = true;
summary.getRange("A:A").format.columnWidth = 34;
summary.getRange("B:B").format.columnWidth = 16;
summary.getRange("C:C").format.columnWidth = 3;
summary.getRange("D:D").format.columnWidth = 21;
summary.getRange("E:E").format.columnWidth = 34;
summary.getRange("F:F").format.columnWidth = 42;
summary.getRange("G:G").format.columnWidth = 30;
summary.getRange("H:H").format.columnWidth = 46;
summary.getRange("D12:H12").format = { fill: colors.paleAmber, font: { bold: true, color: "#7A4D00" }, wrapText: true };
summary.freezePanes.freezeRows(4);

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const keyInspection = await workbook.inspect({
  kind: "table",
  range: "Summary!A1:H12",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 10,
  maxChars: 8000,
});
console.log("KEY_INSPECTION");
console.log(keyInspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
  maxChars: 4000,
});
console.log("FORMULA_ERROR_SCAN");
console.log(errors.ndjson);

for (const sheetName of ["Summary", "Candidates", "Requirements", "CAD Envelopes", "Sources", "Scoring Guide"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  const safeName = sheetName.replaceAll(" ", "_");
  await fs.writeFile(path.join(previewDir, `${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`WORKBOOK_SAVED ${outputPath}`);
console.log(`PREVIEWS_SAVED ${previewDir}`);
