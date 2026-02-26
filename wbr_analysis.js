const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile('C:/Users/chead/OneDrive/Documents/CCH_Files_clean.xlsx');

  // Helper: read a sheet into array of row objects
  function readSheet(name) {
    const ws = wb.getWorksheet(name);
    if (!ws) return null;
    const rows = [];
    ws.eachRow((row, rowNum) => {
      const vals = [];
      row.eachCell({ includeEmpty: true }, (cell, colNum) => {
        vals[colNum - 1] = cell.value;
      });
      rows.push(vals);
    });
    return rows;
  }

  // Read current and prior week
  const cur = readSheet('8wk');
  const prv = readSheet('7wk');

  console.log('=== 8wk: first 5 rows ===');
  cur.slice(0, 5).forEach((r, i) => console.log(`Row ${i+1}:`, JSON.stringify(r)));

  console.log('\n=== 7wk: first 5 rows ===');
  prv.slice(0, 5).forEach((r, i) => console.log(`Row ${i+1}:`, JSON.stringify(r)));

  console.log('\n=== 8wk total rows:', cur.length);
  console.log('=== 7wk total rows:', prv.length);

  // Also check the piv_CPP sheet
  const cpp = readSheet('piv_CPP');
  if (cpp) {
    console.log('\n=== piv_CPP: first 10 rows ===');
    cpp.slice(0, 10).forEach((r, i) => console.log(`Row ${i+1}:`, JSON.stringify(r)));
    console.log('piv_CPP total rows:', cpp.length);
  }

  // Check by Facility_wk sheet
  const facWk = readSheet('by Facility_wk');
  if (facWk) {
    console.log('\n=== by Facility_wk: first 10 rows ===');
    facWk.slice(0, 10).forEach((r, i) => console.log(`Row ${i+1}:`, JSON.stringify(r)));
    console.log('by Facility_wk total rows:', facWk.length);
  }

})();
