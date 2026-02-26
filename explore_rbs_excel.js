const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.readFile(path.join('C:','Users','chead','.openclaw','workspace','RBS_unzipped','RBS Budget Impact CCH.xlsx'));
    
    console.log('Sheet count:', wb.worksheets.length);
    wb.worksheets.forEach(ws => {
        console.log(`  Sheet: "${ws.name}" | Rows: ${ws.rowCount} | Cols: ${ws.columnCount}`);
    });
    
    // Read first sheet more thoroughly
    const ws1 = wb.worksheets[0];
    console.log(`\n=== First sheet: "${ws1.name}" ===`);
    for (let r = 1; r <= Math.min(10, ws1.rowCount); r++) {
        const row = ws1.getRow(r);
        const vals = [];
        for (let c = 1; c <= Math.min(15, ws1.columnCount); c++) {
            const cell = row.getCell(c);
            vals.push(cell.value !== null && cell.value !== undefined ? String(cell.value).substring(0, 20) : '');
        }
        console.log(`Row ${r}: ${vals.join(' | ')}`);
    }
})();
