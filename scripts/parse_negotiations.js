const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
  try {
    // Try reading the negotiations tracker - it's .xlsb so ExcelJS may not support it
    // Fall back to CCH file which is .xlsx
    const cchPath = 'C:/Users/chead/OneDrive/Documents/CCH_Files_clean.xlsx';
    console.log('=== READING CCH_Files_clean.xlsx ===');
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.readFile(cchPath);
    
    console.log(`\nTotal sheets: ${wb.worksheets.length}`);
    console.log('\nSheet names:');
    wb.worksheets.forEach((ws, i) => {
      console.log(`  ${i+1}. "${ws.name}" — rows: ${ws.rowCount}, cols: ${ws.columnCount}`);
    });
    
    // Find the "by facility week" or similar tab
    const facilitySheet = wb.worksheets.find(ws => 
      ws.name.toLowerCase().includes('facility') && ws.name.toLowerCase().includes('week')
    ) || wb.worksheets.find(ws => 
      ws.name.toLowerCase().includes('facility')
    );
    
    if (facilitySheet) {
      console.log(`\n=== FACILITY SHEET: "${facilitySheet.name}" ===`);
      // Print first 3 rows to understand structure
      for (let r = 1; r <= Math.min(5, facilitySheet.rowCount); r++) {
        const row = facilitySheet.getRow(r);
        const vals = [];
        row.eachCell({includeEmpty: true}, (cell, colNum) => {
          if (colNum <= 20) vals.push(`[${colNum}]${cell.value}`);
        });
        console.log(`Row ${r}: ${vals.join(' | ')}`);
      }
    } else {
      console.log('\nNo facility-week sheet found. Printing first 5 rows of each sheet:');
      wb.worksheets.forEach(ws => {
        console.log(`\n--- Sheet: "${ws.name}" ---`);
        for (let r = 1; r <= Math.min(3, ws.rowCount); r++) {
          const row = ws.getRow(r);
          const vals = [];
          row.eachCell({includeEmpty: true}, (cell, colNum) => {
            if (colNum <= 15) vals.push(`[${colNum}]${cell.value}`);
          });
          console.log(`  Row ${r}: ${vals.join(' | ')}`);
        }
      });
    }
  } catch(e) {
    console.error('Error:', e.message);
  }
})();
