/**
 * CLIFF TOOL: Waterfall Bridge Builder
 * ======================================
 * Takes a JSON input file with budget/actual data and produces 
 * a fully formatted Excel waterfall bridge workbook.
 *
 * Input: JSON file path as argv[2] with structure:
 * {
 *   "period": "January 2026",
 *   "budget_total": 1500000,
 *   "actual_total": 1558000,
 *   "components": {
 *     "Volume": 25000,
 *     "B2C": 8000,
 *     "Stop Fee": 15000,
 *     "Weight": -3000,
 *     "Ad Hoc": 12000,
 *     "RBS": -5000,
 *     "Pickup": 6000
 *   },
 *   "facilities": [
 *     {"name": "LAX", "budget_cost": 200000, "actual_cost": 218000, "budget_vol": 50000, "actual_vol": 53000, "primary_driver": "Volume surge +6%"},
 *     ...
 *   ],
 *   "narrative": {
 *     "executive_summary": "...",
 *     "Volume": "...",
 *     "B2C": "...",
 *     ...
 *   }
 * }
 *
 * Output: argv[3] or default path — formatted Excel workbook
 */

const path = require('path');
const fs = require('fs');
const ExcelJS = require(path.join('C:', 'Users', 'chead', 'AppData', 'Roaming', 'npm', 'node_modules', 'exceljs'));

const INPUT_PATH = process.argv[2] || 'waterfall_input.json';
const OUTPUT_PATH = process.argv[3] || 'C:/Users/chead/OneDrive/Documents/Waterfall_Output.xlsx';

// Color palette
const COLORS = {
    headerBg: '2F5496',
    headerFont: 'FFFFFF',
    favorable: '008000',
    unfavorable: 'CC0000',
    neutral: '333333',
    endpointBg: 'D6E4F0',
    lightRow: 'F2F2F2',
    white: 'FFFFFF',
    validationOk: '008000',
    validationFail: 'CC0000',
};

function headerStyle() {
    return {
        font: { bold: true, color: { argb: COLORS.headerFont }, size: 11 },
        fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: COLORS.headerBg } },
        alignment: { horizontal: 'center', vertical: 'middle' },
        border: {
            bottom: { style: 'thin', color: { argb: '999999' } }
        }
    };
}

function currencyFmt(val) {
    return val >= 0 ? '$#,##0' : '-$#,##0';
}

(async () => {
    try {
        const input = JSON.parse(fs.readFileSync(INPUT_PATH, 'utf-8'));
        const workbook = new ExcelJS.Workbook();
        workbook.creator = 'Cliff - Craig\'s Financial Analyst';
        workbook.created = new Date();

        // ===== SHEET 1: WATERFALL =====
        const ws1 = workbook.addWorksheet('Waterfall', {
            views: [{ state: 'frozen', ySplit: 1 }]
        });

        // Title row
        ws1.mergeCells('A1:E1');
        const titleCell = ws1.getCell('A1');
        titleCell.value = `${input.period} — Cost Waterfall Bridge`;
        titleCell.font = { bold: true, size: 14, color: { argb: COLORS.headerBg } };
        titleCell.alignment = { horizontal: 'left' };

        ws1.addRow([]); // spacer

        // Column headers
        const hdr1 = ws1.addRow(['Component', 'Delta ($)', 'Cumulative ($)', 'Fav / Unfav', '% of Total Variance']);
        Object.assign(hdr1.getCell(1), headerStyle());
        Object.assign(hdr1.getCell(2), headerStyle());
        Object.assign(hdr1.getCell(3), headerStyle());
        Object.assign(hdr1.getCell(4), headerStyle());
        Object.assign(hdr1.getCell(5), headerStyle());

        const totalVariance = input.actual_total - input.budget_total;
        const componentOrder = ['Volume', 'B2C', 'Stop Fee', 'Weight', 'Ad Hoc', 'RBS', 'Pickup'];
        let cumulative = input.budget_total;

        // Budget row (endpoint)
        const budgetRow = ws1.addRow([
            'Budget', input.budget_total, input.budget_total, '', ''
        ]);
        budgetRow.getCell(1).font = { bold: true };
        budgetRow.getCell(2).numFmt = '$#,##0';
        budgetRow.getCell(3).numFmt = '$#,##0';
        budgetRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: COLORS.endpointBg } };

        // Component rows
        let bridgeSum = 0;
        for (const comp of componentOrder) {
            const val = input.components[comp] || 0;
            cumulative += val;
            bridgeSum += val;
            const isFav = val < 0;
            const pctOfTotal = totalVariance !== 0 ? Math.abs(val / totalVariance) : 0;

            const row = ws1.addRow([
                comp,
                val,
                cumulative,
                isFav ? 'Favorable' : (val === 0 ? '—' : 'Unfavorable'),
                pctOfTotal
            ]);

            row.getCell(2).numFmt = '$#,##0';
            row.getCell(3).numFmt = '$#,##0';
            row.getCell(5).numFmt = '0.0%';

            const color = val === 0 ? COLORS.neutral : (isFav ? COLORS.favorable : COLORS.unfavorable);
            row.getCell(2).font = { color: { argb: color }, bold: Math.abs(val) > 10000 };
            row.getCell(4).font = { color: { argb: color } };
        }

        // Actual row (endpoint)
        const actualRow = ws1.addRow([
            'Actual', input.actual_total, input.actual_total, '', ''
        ]);
        actualRow.getCell(1).font = { bold: true };
        actualRow.getCell(2).numFmt = '$#,##0';
        actualRow.getCell(3).numFmt = '$#,##0';
        actualRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: COLORS.endpointBg } };

        // Validation
        ws1.addRow([]);
        const gap = bridgeSum - totalVariance;
        const ties = Math.abs(gap) < 100;
        const valRow = ws1.addRow([
            'VALIDATION',
            `Bridge: $${bridgeSum.toLocaleString()}`,
            `Delta: $${totalVariance.toLocaleString()}`,
            ties ? '✓ TIES' : `✗ GAP: $${gap.toLocaleString()}`,
            ''
        ]);
        valRow.font = { bold: true, color: { argb: ties ? COLORS.validationOk : COLORS.validationFail } };

        // Column widths
        ws1.getColumn(1).width = 16;
        ws1.getColumn(2).width = 18;
        ws1.getColumn(3).width = 18;
        ws1.getColumn(4).width = 14;
        ws1.getColumn(5).width = 18;

        // ===== SHEET 2: TOP 10 FACILITIES =====
        if (input.facilities && input.facilities.length > 0) {
            const ws2 = workbook.addWorksheet('Top 10 Facilities', {
                views: [{ state: 'frozen', ySplit: 1 }]
            });

            const facHeaders = [
                'Rank', 'Facility', 'Budget Cost', 'Actual Cost', 'Delta ($)',
                'Delta (%)', 'Budget Vol', 'Actual Vol', 'Vol Delta',
                'Budget CPP', 'Actual CPP', 'CPP Delta', 'Primary Driver'
            ];
            const hdr2 = ws2.addRow(facHeaders);
            facHeaders.forEach((_, i) => Object.assign(hdr2.getCell(i + 1), headerStyle()));

            // Sort by absolute delta
            const sorted = [...input.facilities]
                .map(f => ({
                    ...f,
                    delta: f.actual_cost - f.budget_cost,
                    deltaPct: f.budget_cost ? (f.actual_cost - f.budget_cost) / f.budget_cost : 0,
                    volDelta: f.actual_vol - f.budget_vol,
                    budgetCpp: f.budget_vol ? f.budget_cost / f.budget_vol : 0,
                    actualCpp: f.actual_vol ? f.actual_cost / f.actual_vol : 0,
                }))
                .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
                .slice(0, 10);

            sorted.forEach((f, i) => {
                const cppDelta = f.actualCpp - f.budgetCpp;
                const row = ws2.addRow([
                    i + 1,
                    f.name,
                    f.budget_cost,
                    f.actual_cost,
                    f.delta,
                    f.deltaPct,
                    f.budget_vol,
                    f.actual_vol,
                    f.volDelta,
                    f.budgetCpp,
                    f.actualCpp,
                    cppDelta,
                    f.primary_driver || ''
                ]);

                // Formatting
                [3, 4, 5].forEach(c => { row.getCell(c).numFmt = '$#,##0'; });
                row.getCell(6).numFmt = '0.0%';
                [7, 8, 9].forEach(c => { row.getCell(c).numFmt = '#,##0'; });
                [10, 11, 12].forEach(c => { row.getCell(c).numFmt = '$#,##0.00'; });

                const deltaColor = f.delta > 0 ? COLORS.unfavorable : COLORS.favorable;
                row.getCell(5).font = { color: { argb: deltaColor }, bold: true };

                // Flag double whammy: CPP up AND volume down
                if (cppDelta > 0 && f.volDelta < 0) {
                    row.getCell(2).font = { bold: true, color: { argb: COLORS.unfavorable } };
                    row.getCell(13).value = (f.primary_driver || '') + ' ⚠ CPP↑ + Vol↓';
                }

                // Alternating rows
                if (i % 2 === 1) {
                    for (let c = 1; c <= 13; c++) {
                        row.getCell(c).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: COLORS.lightRow } };
                    }
                }
            });

            // Column widths
            const widths = [6, 14, 14, 14, 14, 10, 12, 12, 10, 12, 12, 12, 30];
            widths.forEach((w, i) => { ws2.getColumn(i + 1).width = w; });
        }

        // ===== SHEET 3: NARRATIVE =====
        if (input.narrative) {
            const ws3 = workbook.addWorksheet('Narrative');

            ws3.getColumn(1).width = 80;

            const titleRow3 = ws3.addRow([`${input.period} — Variance Commentary`]);
            titleRow3.font = { bold: true, size: 14, color: { argb: COLORS.headerBg } };

            ws3.addRow([]);

            if (input.narrative.executive_summary) {
                const esRow = ws3.addRow(['EXECUTIVE SUMMARY']);
                esRow.font = { bold: true, size: 11 };
                ws3.addRow([input.narrative.executive_summary]);
                ws3.addRow([]);
            }

            for (const comp of componentOrder) {
                if (input.narrative[comp]) {
                    const compRow = ws3.addRow([comp.toUpperCase()]);
                    compRow.font = { bold: true, size: 11 };
                    ws3.addRow([input.narrative[comp]]);
                    ws3.addRow([]);
                }
            }

            // Wrap text
            ws3.eachRow(row => {
                row.getCell(1).alignment = { wrapText: true, vertical: 'top' };
            });
        }

        // Save
        await workbook.xlsx.writeFile(OUTPUT_PATH);
        console.log(JSON.stringify({
            status: 'success',
            output: OUTPUT_PATH,
            sheets: workbook.worksheets.map(s => s.name),
            period: input.period,
            budget: input.budget_total,
            actual: input.actual_total,
            totalVariance: totalVariance,
            bridgeTies: Math.abs(bridgeSum - totalVariance) < 100
        }));

    } catch (err) {
        console.error(JSON.stringify({ error: err.message }));
        process.exit(1);
    }
})();
