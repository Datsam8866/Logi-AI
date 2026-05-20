const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'dashboard.html'), 'utf8');

const checks = [
  ['empty import state', /not imported yet/i],
  ['split cost display', /USD budget impact/i],
  ['delete summary modal', /deleteSummary/i],
  ['trash delete control', /Delete transaction/i],
  ['SQLite save mode hint', /save to SQLite/i],
  ['TWD to USD conversion helper', /function convertCostToUsd/i],
  ['exchange rate shown in form', /1 USD = 31\.6 TWD/i],
  ['status sort helper', /function statusSortRank/i],
  ['Will Expensify sorted first', /Will Expensify['"]\s*:\s*0/i],
  ['Will PR sorted second', /Will PR['"]\s*:\s*1/i],
  ['current user endpoint consumed', /\/api\/me/i],
  ['viewer hides edit controls', /body\.viewer \.del-btn|fab\.hidden/i],
];

const missing = checks.filter(([, pattern]) => !pattern.test(html)).map(([label]) => label);

if (missing.length) {
  console.error(`Missing UX requirements: ${missing.join(', ')}`);
  process.exit(1);
}

if (/needs-attention|Needs Attention/i.test(html)) {
  console.error('Needs Attention section should be removed');
  process.exit(1);
}

console.log('UX assertions OK');
