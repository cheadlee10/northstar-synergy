const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

async function readWorkbook(filePath) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const sheetNames = workbook.SheetNames;
    const sheetsData = {};
    sheetNames.forEach(sheetName => {
        const worksheet = workbook.getWorksheet(sheetName);
        sheetsData[sheetName] = [];
        worksheet.eachRow({ includeEmpty: true }, (row, rowNumber) => {
            const rowData = [];
            row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
                rowData.push(cell.value);
            });
            sheetsData[sheetName].push(rowData);
        });
    });
    return sheetsData;
}

async function readSheet(filePath, sheetName) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const worksheet = workbook.getWorksheet(sheetName);
    if (!worksheet) {
        throw new Error(`Sheet "${sheetName}" not found.`);
    }
    const sheetData = [];
    worksheet.eachRow({ includeEmpty: true }, (row, rowNumber) => {
        const rowData = [];
        row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
            rowData.push(cell.value);
        });
        sheetData.push(rowData);
    });
    return sheetData;
}

async function readCell(filePath, sheetName, cellAddress) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const worksheet = workbook.getWorksheet(sheetName);
    if (!worksheet) {
        throw new Error(`Sheet "${sheetName}" not found.`);
    }
    const cell = worksheet.getCell(cellAddress);
    return cell.value;
}

async function readRange(filePath, sheetName, startCell, endCell) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const worksheet = workbook.getWorksheet(sheetName);
    if (!worksheet) {
        throw new Error(`Sheet "${sheetName}" not found.`);
    }
    const rangeData = [];
    const range = worksheet.getRange(startCell, endCell);
    range.eachRow({ includeEmpty: true }, (row, rowNumber) => {
        const rowData = [];
        row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
            rowData.push(cell.value);
        });
        rangeData.push(rowData);
    });
    return rangeData;
}

async function writeCell(filePath, sheetName, cellAddress, value) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const worksheet = workbook.getWorksheet(sheetName);
    if (!worksheet) {
        throw new Error(`Sheet "${sheetName}" not found.`);
    }
    worksheet.getCell(cellAddress).value = value;
    await workbook.xlsx.writeFile(filePath);
    return `Cell ${cellAddress} in sheet ${sheetName} updated to ${value}.`;
}

async function addRow(filePath, sheetName, rowData) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    const worksheet = workbook.getWorksheet(sheetName);
    if (!worksheet) {
        throw new Error(`Sheet "${sheetName}" not found.`);
    }
    worksheet.addRow(rowData);
    await workbook.xlsx.writeFile(filePath);
    return `Row added to sheet ${sheetName}.`;
}

async function createNewWorkbook(filePath) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.writeFile(filePath);
    return `New workbook created at ${filePath}.`;
}

async function listSheetNames(filePath) {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);
    return workbook.SheetNames;
}

module.exports = {
    readWorkbook,
    readSheet,
    readCell,
    readRange,
    writeCell,
    addRow,
    createNewWorkbook,
    listSheetNames
};
