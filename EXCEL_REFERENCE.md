# EXCEL_REFERENCE.md — Cliff's ExcelJS Cheat Sheet
*Practical patterns for reading, analyzing, and building Craig's WBR outputs.*

---

## REQUIRE PATTERN (ALWAYS USE THIS)
```javascript
const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));
(async () => {
  // all code here
})();
```

---

## READING FILES

### Open a workbook
```javascript
const workbook = new ExcelJS.Workbook();
await workbook.xlsx.readFile('C:/Users/chead/OneDrive/Documents/CCH_Files_clean.xlsx');
```

### List all worksheets
```javascript
workbook.eachSheet((sheet, id) => {
  console.log(`${id}: "${sheet.name}" — ${sheet.rowCount} rows x ${sheet.columnCount} cols`);
});
```

### Get a sheet by name
```javascript
const ws = workbook.getWorksheet('by Wk,facility');
// NOTE: getWorksheet(1) is NOT the same as worksheets[0] — sheet IDs can be non-sequential
// Safest approach: always get by name
```

### Read a specific cell
```javascript
const cell = ws.getCell('A1');
console.log(cell.value);       // raw value
console.log(cell.text);        // string representation
console.log(cell.type);        // ExcelJS.ValueType enum
```

### Read a row
```javascript
const row = ws.getRow(2);
row.eachCell({ includeEmpty: false }, (cell, colNum) => {
  console.log(`Col ${colNum}: ${cell.value}`);
});
// OR access as sparse array (index starts at 1):
const vals = row.values; // vals[1] is col A, vals[2] is col B, etc.
```

### Iterate all data rows efficiently
```javascript
ws.eachRow({ includeEmpty: false }, (row, rowNum) => {
  if (rowNum === 1) return; // skip header
  const vals = row.values;  // sparse array, index 1-based
  // process vals...
});
```

### Read a range of rows (efficient for large sheets)
```javascript
// Read rows 1-100 only
for (let r = 1; r <= 100; r++) {
  const row = ws.getRow(r);
  const vals = row.values;
  if (!vals || vals.length === 0) continue;
  console.log(JSON.stringify(vals));
}
```

### Get column headers from row 1
```javascript
const headers = [];
const headerRow = ws.getRow(1);
headerRow.eachCell({ includeEmpty: true }, (cell, colNum) => {
  headers[colNum] = cell.value ? String(cell.value).trim() : `col_${colNum}`;
});
console.log(headers.filter(Boolean)); // remove nulls from sparse array
```

---

## CELL VALUE TYPES

ExcelJS returns different value types — handle them:

```javascript
function getCellValue(cell) {
  if (!cell || cell.value === null || cell.value === undefined) return null;
  
  // Formula cell — get the cached result, not the formula
  if (cell.value && typeof cell.value === 'object' && cell.value.result !== undefined) {
    return cell.value.result;  // the calculated value Excel stored
  }
  // Shared formula
  if (cell.value && typeof cell.value === 'object' && cell.value.sharedFormula) {
    return cell.value.result;
  }
  // Date
  if (cell.value instanceof Date) {
    return cell.value.toISOString().slice(0, 10);
  }
  // Rich text
  if (cell.value && typeof cell.value === 'object' && cell.value.richText) {
    return cell.value.richText.map(r => r.text).join('');
  }
  return cell.value;
}
```

**Value type constants:**
- `ExcelJS.ValueType.Null` = 0
- `ExcelJS.ValueType.Merge` = 1
- `ExcelJS.ValueType.Number` = 2
- `ExcelJS.ValueType.String` = 3
- `ExcelJS.ValueType.Date` = 4
- `ExcelJS.ValueType.Hyperlink` = 5
- `ExcelJS.ValueType.Formula` = 6
- `ExcelJS.ValueType.SharedString` = 7
- `ExcelJS.ValueType.RichText` = 8
- `ExcelJS.ValueType.Boolean` = 9
- `ExcelJS.ValueType.Error` = 10

---

## READING LARGE FILES (Craig's 70+ tab workbooks)

### Performance tips for 11,000+ row sheets:
```javascript
// DON'T iterate every cell — use row.values (sparse array, much faster)
// DON'T use getCell() in a loop — it creates cell objects even for empties
// DO build a column index from the header row, then use row.values[colIndex]

const ws = workbook.getWorksheet('by Wk,facility');

// Step 1: build column map from header row
const colMap = {};
const hdr = ws.getRow(1).values; // sparse array
hdr.forEach((name, idx) => {
  if (name) colMap[String(name).trim()] = idx;
});
console.log('Columns:', colMap);

// Step 2: read data using the map
const results = [];
ws.eachRow({ includeEmpty: false }, (row, rowNum) => {
  if (rowNum === 1) return;
  const vals = row.values;
  results.push({
    facility: vals[colMap['Facility']],
    week:     vals[colMap['Week']],
    cpp:      vals[colMap['CPP']],
    cost:     vals[colMap['Total Cost']],
    volume:   vals[colMap['Volume']],
  });
});
```

### Streaming reader (for very large files, read-only):
```javascript
// Use when you just need to scan data without building the full workbook in memory
const { Workbook } = ExcelJS;
const workbookReader = new ExcelJS.stream.xlsx.WorkbookReader('filepath.xlsx');

for await (const worksheetReader of workbookReader) {
  if (worksheetReader.name !== 'TargetSheet') {
    worksheetReader.destroy(); // skip other sheets
    continue;
  }
  for await (const row of worksheetReader) {
    console.log(row.values);
  }
}
```

---

## WRITING OUTPUT FILES

### Create a formatted workbook
```javascript
const wb = new ExcelJS.Workbook();
wb.creator = 'Cliff';
wb.created = new Date();

const ws = wb.addWorksheet('Summary', {
  views: [{ state: 'frozen', ySplit: 1 }], // freeze header row
  properties: { tabColor: { argb: 'FF2F5496' } }
});
```

### Add headers with formatting
```javascript
const headers = ['Facility', 'Week', 'Budget CPP', 'Actual CPP', 'Delta CPP', 'Total Cost', 'Variance'];
const headerRow = ws.addRow(headers);
headerRow.font = { bold: true, color: { argb: 'FFFFFFFF' }, size: 11 };
headerRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF2F5496' } };
headerRow.alignment = { horizontal: 'center', vertical: 'middle' };
headerRow.height = 18;
```

### Add a data row with conditional coloring
```javascript
function addDataRow(ws, rowData) {
  const row = ws.addRow(rowData);
  
  // Color the variance cell: green = favorable (negative), red = unfavorable (positive)
  const varCell = row.getCell(7); // column G = Variance
  const varVal = rowData[6];
  if (varVal !== null && varVal !== undefined) {
    varCell.font = { 
      color: { argb: varVal < 0 ? 'FF008000' : 'FFCC0000' },
      bold: Math.abs(varVal) > 10000
    };
  }
  return row;
}
```

### Number formats
```javascript
// Currency
cell.numFmt = '$#,##0';           // $1,234
cell.numFmt = '$#,##0.00';        // $1,234.56
cell.numFmt = '$#,##0.0000';      // CPP: $2.7734

// Percentage
cell.numFmt = '0.0%';             // 12.3%
cell.numFmt = '0.00%';            // 12.34%

// Number
cell.numFmt = '#,##0';            // 1,234
cell.numFmt = '#,##0.0';          // 1,234.5

// Favorable/Unfavorable display: use parentheses for negatives
cell.numFmt = '$#,##0;($#,##0)';  // negative in parens

// Date
cell.numFmt = 'MM/DD/YYYY';
```

### Set column widths and formats in bulk
```javascript
// Define columns with width and format
ws.columns = [
  { header: 'Facility',    key: 'facility', width: 20 },
  { header: 'Week',        key: 'week',     width: 8  },
  { header: 'Budget CPP',  key: 'bCpp',     width: 14, style: { numFmt: '$#,##0.0000' } },
  { header: 'Actual CPP',  key: 'aCpp',     width: 14, style: { numFmt: '$#,##0.0000' } },
  { header: 'Delta CPP',   key: 'dCpp',     width: 14, style: { numFmt: '$#,##0.0000' } },
  { header: 'Total Cost',  key: 'cost',     width: 16, style: { numFmt: '$#,##0'      } },
  { header: 'Variance',    key: 'variance', width: 16, style: { numFmt: '$#,##0'      } },
];
```

### Auto-width columns (after data is added)
```javascript
ws.columns.forEach(col => {
  let maxLen = col.header ? String(col.header).length : 10;
  col.eachCell({ includeEmpty: false }, cell => {
    const len = cell.text ? cell.text.length : 0;
    if (len > maxLen) maxLen = len;
  });
  col.width = Math.min(maxLen + 2, 40); // cap at 40
});
```

---

## CONDITIONAL FORMATTING

```javascript
// Red fill for unfavorable variance (positive = cost overrun)
ws.addConditionalFormatting({
  ref: 'G2:G1000',
  rules: [
    {
      type: 'cellIs',
      operator: 'greaterThan',
      formulae: ['0'],
      style: {
        fill: { type: 'pattern', pattern: 'solid', bgColor: { argb: 'FFFFCCCC' } },
        font: { color: { argb: 'FFCC0000' } }
      }
    },
    {
      type: 'cellIs',
      operator: 'lessThan',
      formulae: ['0'],
      style: {
        fill: { type: 'pattern', pattern: 'solid', bgColor: { argb: 'FFCCFFCC' } },
        font: { color: { argb: 'FF008000' } }
      }
    }
  ]
});

// Data bar (visual bar in cell)
ws.addConditionalFormatting({
  ref: 'E2:E1000',
  rules: [{
    type: 'dataBar',
    minValue: 0,
    maxValue: 100,
    color: { argb: 'FF638EC6' }
  }]
});
```

---

## BORDERS AND STYLING

```javascript
// Thin border around a range (apply to each cell)
const borderStyle = {
  top:    { style: 'thin', color: { argb: 'FF000000' } },
  left:   { style: 'thin', color: { argb: 'FF000000' } },
  bottom: { style: 'thin', color: { argb: 'FF000000' } },
  right:  { style: 'thin', color: { argb: 'FF000000' } }
};

// Thick bottom border (for subtotal rows)
const subtotalBorder = {
  bottom: { style: 'medium', color: { argb: 'FF000000' } },
  top:    { style: 'thin' }
};

// Apply to a row
row.eachCell({ includeEmpty: false }, cell => { cell.border = borderStyle; });
```

---

## WATERFALL / BRIDGE PATTERN

```javascript
// Build a waterfall table (Budget → components → Actual)
// Columns: Label | Base | Variance | Running Total | Fav/Unfav
function buildWaterfallRow(ws, label, variance, runningTotal, isEndpoint = false) {
  const isFav = variance < 0; // negative cost variance = favorable
  const row = ws.addRow([
    label,
    isEndpoint ? variance : null,
    isEndpoint ? null : variance,
    runningTotal,
    isEndpoint ? '' : (isFav ? 'FAV' : 'UNFAV')
  ]);
  
  // Format variance cell
  const varCell = row.getCell(3);
  varCell.numFmt = '$#,##0;($#,##0)';
  if (!isEndpoint) {
    varCell.font = { color: { argb: isFav ? 'FF008000' : 'FFCC0000' } };
  }
  
  // Total column
  row.getCell(4).numFmt = '$#,##0';
  
  return row;
}
```

---

## EXCEL FORMULA HANDLING

When reading Craig's file, formulas return cached results — this is what you want:

```javascript
// A formula cell's value object looks like:
// { formula: '=A1+B1', result: 42, date1904: false }
// OR for shared formulas:
// { sharedFormula: 'B2', result: 42 }

// Safe extraction:
function extractNumeric(cell) {
  if (!cell) return null;
  const v = cell.value;
  if (v === null || v === undefined) return null;
  if (typeof v === 'number') return v;
  if (typeof v === 'object' && v.result !== undefined) {
    return typeof v.result === 'number' ? v.result : null;
  }
  if (typeof v === 'string') {
    const n = parseFloat(v.replace(/[$,%]/g, ''));
    return isNaN(n) ? null : n;
  }
  return null;
}
```

---

## SAVING OUTPUT

```javascript
// Save to file
await workbook.xlsx.writeFile('C:/Users/chead/OneDrive/Documents/WBR_analysis.xlsx');
console.log('Saved.');

// Protect a sheet from editing (read-only for Craig's presentation copy)
ws.protect('password', {
  selectLockedCells: true,
  selectUnlockedCells: true
});
```

---

## COMMON GOTCHAS (WINDOWS / CRAIG'S SETUP)

1. **Forward slashes in paths** — always. Backslashes cause issues.
2. **Row.values is 1-indexed and sparse** — `vals[0]` is always undefined; data starts at `vals[1]`.
3. **getWorksheet() by ID is unreliable** when sheets have been deleted — always use name.
4. **Formula cells** — `cell.value.result` is the cached value. If Excel didn't recalculate before save, result may be stale. Watch for this on complex workbooks.
5. **Merged cells** — reading a merged cell range: only the top-left cell has the value; others return type=Merge with value=null.
6. **Large workbooks** — CCH_Files_clean.xlsx has 72 tabs and 11K+ row sheets. Always `await` the read before accessing sheets. Takes ~5-15 seconds on Craig's machine.
7. **Tab names with special chars** — 'by Wk,facility' has a comma. Pass the exact string to `getWorksheet()`.
8. **Number format vs value** — cell.numFmt is the display format; cell.value is the raw number. CPP of 2.7734 displays as "$2.77" but cell.value = 2.7734. Always use raw value for math.
9. **Pivot tabs (piv_*)** — these are calculation helper sheets that feed presentation tabs. Their structure may be volatile/formulaic. Read carefully.

---

## WBR-SPECIFIC PATTERNS

### Extract all facilities from Bible tab
```javascript
const ws = workbook.getWorksheet('by Wk,facility'); // Craig confirmed this is the name
const colMap = {};
ws.getRow(1).values.forEach((v, i) => { if (v) colMap[String(v).trim()] = i; });

const facilityData = {};
ws.eachRow({ includeEmpty: false }, (row, rowNum) => {
  if (rowNum === 1) return;
  const vals = row.values;
  const facility = String(vals[colMap['Facility']] || '').trim();
  const week = vals[colMap['Week']];
  if (!facility || !week) return;
  
  if (!facilityData[facility]) facilityData[facility] = {};
  facilityData[facility][week] = {
    cost:     extractNumeric(row.getCell(colMap['Total Cost'])),
    volume:   extractNumeric(row.getCell(colMap['Volume'])),
    cpp:      extractNumeric(row.getCell(colMap['CPP'])),
    stopFee:  extractNumeric(row.getCell(colMap['Stop Fee'])),
    baseFee:  extractNumeric(row.getCell(colMap['Base Fee'])),
    weightFee:extractNumeric(row.getCell(colMap['Weight Fee'])),
    adHoc:    extractNumeric(row.getCell(colMap['Ad Hoc'])),
    pickup:   extractNumeric(row.getCell(colMap['Pickup'])),
    peakInc:  extractNumeric(row.getCell(colMap['Peak Incentive'])),
  };
});
```

### CPP Calculation (always verify against source)
```javascript
// CPP = Total Cost / Total Volume
// If the file provides CPP directly, use it.
// If calculating yourself, verify it ties:
const calcCPP = totalCost / totalVolume;
const fileCPP = extractNumeric(row.getCell(colMap['CPP']));
const gap = Math.abs(calcCPP - fileCPP);
if (gap > 0.001) console.warn(`CPP mismatch at row ${rowNum}: calc=${calcCPP}, file=${fileCPP}`);
```

### Variance color logic (NEVER get this backwards)
```javascript
// In Craig's world:
// Favorable = cost BELOW budget = negative variance = GREEN
// Unfavorable = cost ABOVE budget = positive variance = RED

function varianceColor(actual, budget) {
  const delta = actual - budget;
  return delta < 0 ? 'FF008000' : 'FFCC0000'; // green : red
}
```

---

## QUICK REFERENCE: ARGB COLORS
| Color | ARGB |
|-------|------|
| OnTrac Blue (header) | FF2F5496 |
| White text | FFFFFFFF |
| Favorable green (dark) | FF008000 |
| Favorable green (light fill) | FFCCFFCC |
| Unfavorable red (dark) | FFCC0000 |
| Unfavorable red (light fill) | FFFFCCCC |
| Gray (neutral) | FF808080 |
| Light gray (alt rows) | FFF2F2F2 |
| Yellow (warning) | FFFFFF00 |
| Dark gray (subtotal) | FF404040 |

---

## SCRIPT TEMPLATE (COPY-PASTE STARTER)

```javascript
const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
  try {
    // --- READ ---
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.readFile('C:/Users/chead/OneDrive/Documents/CCH_Files_clean.xlsx');
    
    const ws = wb.getWorksheet('by Wk,facility');
    if (!ws) throw new Error('Sheet not found');
    
    // Build column map
    const colMap = {};
    ws.getRow(1).values.forEach((v, i) => { if (v) colMap[String(v).trim()] = i; });
    console.log('Columns:', JSON.stringify(colMap));
    
    // --- PROCESS ---
    const data = [];
    ws.eachRow({ includeEmpty: false }, (row, rowNum) => {
      if (rowNum === 1) return;
      const vals = row.values;
      // ... extract what you need
    });
    
    // --- OUTPUT ---
    const outWb = new ExcelJS.Workbook();
    const outWs = outWb.addWorksheet('Results', {
      views: [{ state: 'frozen', ySplit: 1 }]
    });
    // ... build output
    
    await outWb.xlsx.writeFile('C:/Users/chead/OneDrive/Documents/OUTPUT.xlsx');
    console.log('Done.');
    
  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
})();
```

---
*Last updated: 2026-02-23 | Source: ExcelJS docs + Craig's WBR patterns*
