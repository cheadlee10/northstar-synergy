# Excel Handler Skill

This skill provides functionalities to interact with Excel files (.xlsx) using the exceljs Node.js package.

## Functions

- **read_workbook(filePath):** Reads the entire workbook and returns all sheets' data.
- **read_sheet(filePath, sheetName):** Reads data from a specific worksheet.
- **read_cell(filePath, sheetName, cellAddress):** Reads the value of a single cell (e.g., 'A1').
- **read_range(filePath, sheetName, startCell, endCell):** Reads a specified range of cells.
- **write_cell(filePath, sheetName, cellAddress, value):** Writes a value to a specific cell, overwriting if the cell exists. After writing, it saves the workbook.
- **add_row(filePath, sheetName, rowData):** Adds a new row of data to the end of a specified sheet and saves the workbook.
- **create_new_workbook(filePath):** Creates a new Excel workbook and saves it to the specified path.
- **list_sheet_names(filePath):** Lists all the names of the sheets within the workbook.

## Usage

When calling functions from this skill, provide the `filePath`, `sheetName` (if applicable), and other required parameters.

**Important:** The underlying scripts use Node.js with the `exceljs` package. Ensure that `exceljs` is correctly installed globally on the machine for these functions to execute. The scripts use the following `require` pattern:
```javascript
const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));
```
And are wrapped in an async IIFE `(async () => { ... })();`.

## Example Usage:

To list sheet names from a file:
```javascript
const skill = require('./excel_handler.js');

async function run() {
  try {
    const sheets = await skill.listSheetNames('C:\\Users\\chead\\Documents\\brewpupbizplan.xlsx');
    console.log('Sheet names:', sheets);
  } catch (error) {
    console.error('Error listing sheet names:', error);
  }
}

run();
```
