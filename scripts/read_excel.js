/**
 * CLIFF TOOL: Universal Excel Reader
 * ====================================
 * Reads any Excel file and outputs structured JSON data.
 * Cliff uses this as the first step for any Excel task.
 * 
 * Usage: Set FILE_PATH and optionally SHEET_NAME, then run with node.
 * Output: JSON to stdout with sheet names, dimensions, headers, and data.
 */

const path = require('path');
const ExcelJS = require(path.join('C:', 'Users', 'chead', 'AppData', 'Roaming', 'npm', 'node_modules', 'exceljs'));

// ===== CONFIGURE THESE =====
const FILE_PATH = process.argv[2] || 'C:/Users/chead/OneDrive/Documents/CHANGE_ME.xlsx';
const SHEET_NAME = process.argv[3] || null;  // null = read all sheets
const MAX_ROWS = parseInt(process.argv[4]) || 500;  // limit for large files
// ============================

(async () => {
    try {
        const workbook = new ExcelJS.Workbook();
        await workbook.xlsx.readFile(FILE_PATH);

        const result = {
            file: FILE_PATH,
            sheetCount: workbook.worksheets.length,
            sheets: {}
        };

        const sheetsToRead = SHEET_NAME
            ? [workbook.getWorksheet(SHEET_NAME)]
            : workbook.worksheets;

        for (const sheet of sheetsToRead) {
            if (!sheet) continue;

            const sheetData = {
                name: sheet.name,
                rowCount: sheet.rowCount,
                columnCount: sheet.columnCount,
                headers: [],
                data: [],
                summary: {}
            };

            // Read headers (row 1)
            const headerRow = sheet.getRow(1);
            for (let col = 1; col <= sheet.columnCount; col++) {
                const cell = headerRow.getCell(col);
                sheetData.headers.push(cell.value ? String(cell.value).trim() : `Col${col}`);
            }

            // Read data rows (up to MAX_ROWS)
            const rowLimit = Math.min(sheet.rowCount, MAX_ROWS + 1);
            for (let row = 2; row <= rowLimit; row++) {
                const rowObj = {};
                const sheetRow = sheet.getRow(row);
                let hasData = false;

                for (let col = 1; col <= sheet.columnCount; col++) {
                    const cell = sheetRow.getCell(col);
                    let value = cell.value;

                    // Handle formula cells — use the result
                    if (value && typeof value === 'object' && value.result !== undefined) {
                        value = value.result;
                    }
                    // Handle rich text
                    if (value && typeof value === 'object' && value.richText) {
                        value = value.richText.map(rt => rt.text).join('');
                    }
                    // Handle dates
                    if (value instanceof Date) {
                        value = value.toISOString().split('T')[0];
                    }

                    if (value !== null && value !== undefined && value !== '') {
                        hasData = true;
                    }

                    rowObj[sheetData.headers[col - 1]] = value;
                }

                if (hasData) {
                    sheetData.data.push(rowObj);
                }
            }

            // Summary stats for numeric columns
            for (const header of sheetData.headers) {
                const values = sheetData.data
                    .map(r => r[header])
                    .filter(v => typeof v === 'number');
                if (values.length > 0) {
                    sheetData.summary[header] = {
                        count: values.length,
                        sum: values.reduce((a, b) => a + b, 0),
                        min: Math.min(...values),
                        max: Math.max(...values),
                        avg: values.reduce((a, b) => a + b, 0) / values.length
                    };
                }
            }

            if (sheet.rowCount > MAX_ROWS) {
                sheetData.truncated = true;
                sheetData.truncatedAt = MAX_ROWS;
                sheetData.totalRows = sheet.rowCount;
            }

            result.sheets[sheet.name] = sheetData;
        }

        console.log(JSON.stringify(result, null, 2));

    } catch (err) {
        console.error(JSON.stringify({ error: err.message, file: FILE_PATH }));
        process.exit(1);
    }
})();
