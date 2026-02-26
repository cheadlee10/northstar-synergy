# PLAYBOOK.md — How to Do Everything

_Step-by-step procedures. No thinking required — just follow the steps and deliver._

---

## TABLE OF CONTENTS
1. WBR Weekly Process
2. Monthly Waterfall Bridge
3. Variance Decomposition (Any Period)
4. Top 10 Facility Analysis
5. Ad Hoc Cost Analysis
6. Budget vs Actual Comparison
7. CPP Trend Analysis
8. Excel File Operations
9. Job Search Tasks
10. Email & Communication

---

## 1. WBR WEEKLY PROCESS

**Trigger:** Craig says anything about WBR, weekly review, weekly numbers, or drops a new week's data.

**Steps:**

1. Open `CCH_Files_clean.xlsx`
2. Find the latest week tab (highest number — e.g., `8wk` is newer than `7wk`)
3. Also open the prior week tab for comparison
4. Extract by facility:
   - Total cost
   - Total volume (packages)
   - CPP (cost ÷ volume)
   - Each cost component: Stop Fee, B2C, Weight, Ad Hoc, RBS, Pickup
5. Calculate WoW deltas for each metric
6. Open `Craig_Budget_2026.xlsx` and pull the budget targets for the matching period
7. Calculate vs-budget deltas
8. Rank facilities by absolute variance contribution (largest first)
9. Build the output:

**Output format — Excel workbook with 3 sheets:**

Sheet 1: `Summary`
- Total company: actual vs budget vs prior week
- CPP bridge: Budget CPP → Volume → Mix → Rate → Actual CPP
- Top 5 variance drivers (component + facility + dollar amount)

Sheet 2: `Facility Detail`
- Every facility: volume, cost, CPP, each component, WoW delta, vs-budget delta
- Conditional formatting: red if unfavorable >5%, green if favorable >5%
- Sorted by absolute total cost variance (biggest first)

Sheet 3: `Narrative`
- Auto-generated commentary (see narrative rules below)
- 2-3 sentences per major driver
- Ready to paste into email or slides

**Narrative Rules:**
```
Pattern: "[Component] was [$X] [favorable/unfavorable] vs budget, 
driven by [root cause] at [facility/facilities]. 
[Context if available — e.g., 'This reflects the new carrier 
contract effective Jan 15.']"

Example: "Stop fees were $28K unfavorable vs budget, driven by 
rate increases at LAX ($15K) and DFW ($9K) following the January 
contract reset. Remaining $4K spread across 6 facilities."
```

10. Save to `C:/Users/chead/OneDrive/Documents/WBR_[WEEKNUM]_analysis.xlsx`
11. Update MEMORY.md with key numbers
12. Tell Craig: "[Week] WBR done. CPP [up/down] [amount] WoW. Top driver: [X]. File saved to [path]."

---

## 2. MONTHLY WATERFALL BRIDGE

**Trigger:** Craig asks for a waterfall, bridge, monthly analysis, or variance walkthrough.

**Steps:**

1. Open `Craig_Budget_2026.xlsx` — get budget by component for the target month
2. Open actuals source (CCH_Files_clean.xlsx or whatever Craig specifies)
3. Aggregate weekly actuals into monthly totals by component
4. Build the bridge in this exact column order:

```
Budget | Volume | B2C | Stop Fee | Weight | Ad Hoc | RBS | Pickup | Actual
```

5. For each bridge component, calculate:
   - **Volume:** (Actual vol - Budget vol) × Budget CPP
   - **B2C:** Delta B2C % × Actual vol × B2C cost premium
   - **Stop Fee:** Delta stop rate × Actual stops
   - **Weight:** Delta weight charge × Affected volume
   - **Ad Hoc:** Sum of identified ad hoc items (must itemize)
   - **RBS:** Identified route savings
   - **Pickup:** Delta pickup rate × Pickup count

6. **VALIDATION CHECK:** Sum of all bridge components MUST equal (Actual - Budget). If it doesn't, the gap goes into "Unexplained" and you flag it to Craig with possible causes.

7. Build Excel output using `scripts/waterfall_bridge.js`:

Sheet 1: `Waterfall`
- The bridge table with formatting
- Running total column showing cumulative walk from budget to actual
- Color coding: green (favorable), red (unfavorable), gray (budget/actual endpoints)

Sheet 2: `Drivers`
- For each bridge component: top 5 facilities driving it
- Volume vs cost ratio for each facility
- WoW trend if multiple weeks of data exist

Sheet 3: `Top 10 Facilities`
- Ranked by absolute total variance contribution
- Columns: Facility, Budget Cost, Actual Cost, Delta, Budget Vol, Actual Vol, Delta, Budget CPP, Actual CPP, Delta CPP
- Flag: facilities where CPP increased AND volume decreased (double whammy)

Sheet 4: `Narrative`
- Executive summary (3-4 sentences covering the whole month)
- Component-by-component detail (2-3 sentences each)
- Recommended actions if patterns are clear

8. Save to `C:/Users/chead/OneDrive/Documents/Waterfall_[MONTH]_2026.xlsx`
9. Update MEMORY.md

---

## 3. VARIANCE DECOMPOSITION (ANY PERIOD)

**Trigger:** "Why did costs go up?", "What's driving the variance?", "Explain the delta", or any question about cost changes.

**Framework — Always decompose in this order:**

```
Total Variance
├── Volume Variance: (Actual vol - Budget vol) × Budget CPP
├── Site Mix Variance: Actual vol × (Weighted avg budget CPP at actual mix - Overall budget CPP)
├── Rate Variance: Actual vol × (Actual CPP - Weighted avg budget CPP at actual mix)
│   ├── Stop Fee delta
│   ├── B2C delta
│   ├── Weight delta
│   ├── Pickup delta
│   └── Other rate
├── Ad Hoc Variance: Sum of one-time items
└── Unexplained: Residual (should be <2% of total — if larger, dig deeper)
```

**Steps:**

1. Get budget and actual data for the period
2. Calculate total variance first (actual cost - budget cost)
3. Decompose using the tree above
4. For each component >$5K or >5%: identify the top 3 facilities driving it
5. Check for ad hoc items that should be isolated
6. Validate: sum of components = total variance (±$100 rounding tolerance)
7. Deliver as Excel with the tree structure + narrative

**Red flags to always check:**
- CPP increasing while volume is flat/up (rate problem)
- CPP flat but total cost up significantly (volume/mix problem)
- Single facility driving >40% of total variance (concentration risk)
- Ad hoc >10% of total variance (operational issue)
- Volume down but cost flat (fixed cost absorption problem)

---

## 4. TOP 10 FACILITY ANALYSIS

**Trigger:** Any variance analysis automatically includes this. Also when Craig asks about specific facilities.

**Output table:**

| Rank | Facility | Budget Cost | Actual Cost | Delta ($) | Delta (%) | Budget Vol | Actual Vol | Vol Delta | Budget CPP | Actual CPP | CPP Delta | Primary Driver |
|------|----------|-------------|-------------|-----------|-----------|------------|------------|-----------|------------|------------|-----------|---------------|

**Rules:**
- Always sort by absolute dollar delta (largest impact first)
- Include the "Primary Driver" column — one phrase explaining why (e.g., "New carrier rate +$0.12/pkg", "Holiday surge volume +22K pkgs")
- Flag any facility where CPP got worse AND volume dropped — this is the worst combination
- If top 3 facilities account for >60% of total variance, call it out explicitly
- Always include a "All Other" row summing the remaining facilities

---

## 5. AD HOC COST ANALYSIS

**Trigger:** Craig asks about one-time costs, unusual charges, or items that don't fit normal patterns.

**Steps:**

1. Pull all line items for the period
2. Flag anything that:
   - Didn't exist in the prior period
   - Is >2x the normal run-rate for that line item
   - Has a description containing: surge, one-time, adjustment, correction, reclassification, true-up
3. Categorize each ad hoc item:
   - Timing (expected to reverse next period)
   - Structural (permanent cost change)
   - Error (should be reclassified)
4. Total impact and % of total cost
5. Deliver: list of items with amounts, categories, and recommended treatment in the bridge

---

## 6. BUDGET VS ACTUAL COMPARISON

**Trigger:** Any "budget vs actual", "how are we tracking", or "are we on plan" question.

**Standard output — Executive summary format:**

```
January 2026: $X.XM actual vs $X.XM budget = $XXK [favorable/unfavorable] ([X.X]%)
CPP: $X.XX actual vs $X.XX budget = $X.XX [favorable/unfavorable]
Volume: XXK actual vs XXK budget = XK [above/below] plan

Top 3 drivers:
1. [Component] at [Facility]: [$XK] [fav/unfav] — [one line why]
2. [Component] at [Facility]: [$XK] [fav/unfav] — [one line why]  
3. [Component] at [Facility]: [$XK] [fav/unfav] — [one line why]

Outlook: [1-2 sentences on whether the trend is improving/worsening 
and what to watch]
```

Then the full detail in Excel.

---

## 7. CPP TREND ANALYSIS

**Trigger:** "How's CPP trending?", "Show me the CPP trend", or when you notice CPP moving and want to flag it proactively.

**Steps:**

1. Pull CPP by week (or month) for the available time range
2. Calculate: current, prior period, budget, 4-week moving average
3. Decompose CPP change into rate vs mix:
   - Hold mix constant (prior period facility weights) → "rate effect"
   - Hold rates constant (prior period CPP by facility) → "mix effect"
4. Chart: line chart with budget CPP as horizontal reference line
5. Table: week-by-week CPP with WoW delta and vs-budget delta
6. Flag: any facility where CPP trend is diverging from company average

---

## 8. EXCEL FILE OPERATIONS

### Reading Any Excel File

```javascript
// TEMPLATE: Read any Excel file
const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile('C:/Users/chead/OneDrive/Documents/FILENAME.xlsx');
    
    // List all sheets
    workbook.eachSheet((sheet, id) => {
        console.log(`Sheet ${id}: ${sheet.name} (${sheet.rowCount} rows x ${sheet.columnCount} cols)`);
    });
    
    // Read specific sheet
    const sheet = workbook.getWorksheet('SHEETNAME');
    
    // Read range
    for (let row = startRow; row <= endRow; row++) {
        const rowData = [];
        for (let col = startCol; col <= endCol; col++) {
            const cell = sheet.getCell(row, col);
            rowData.push(cell.value);
        }
        console.log(JSON.stringify(rowData));
    }
})();
```

### Writing a Formatted Workbook

```javascript
// TEMPLATE: Create formatted output workbook
const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
    const workbook = new ExcelJS.Workbook();
    const sheet = workbook.addWorksheet('Summary');
    
    // Header row
    const headers = ['Facility', 'Budget', 'Actual', 'Delta', 'Delta %'];
    const headerRow = sheet.addRow(headers);
    headerRow.font = { bold: true, color: { argb: 'FFFFFF' } };
    headerRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: '2F5496' } };
    headerRow.alignment = { horizontal: 'center' };
    
    // Data rows with conditional formatting
    data.forEach(item => {
        const row = sheet.addRow([
            item.facility,
            item.budget,
            item.actual,
            item.delta,
            item.deltaPct
        ]);
        // Color delta column
        const deltaCell = row.getCell(4);
        deltaCell.font = { 
            color: { argb: item.delta < 0 ? '008000' : 'CC0000' } 
        };
        deltaCell.numFmt = '$#,##0';
    });
    
    // Format currency columns
    sheet.getColumn(2).numFmt = '$#,##0';
    sheet.getColumn(3).numFmt = '$#,##0';
    sheet.getColumn(5).numFmt = '0.0%';
    
    // Auto-width columns
    sheet.columns.forEach(col => {
        col.width = Math.max(12, ...col.values
            .filter(v => v)
            .map(v => String(v).length + 2));
    });
    
    // Freeze top row
    sheet.views = [{ state: 'frozen', ySplit: 1 }];
    
    await workbook.xlsx.writeFile('C:/Users/chead/OneDrive/Documents/OUTPUT.xlsx');
    console.log('Done: OUTPUT.xlsx saved');
})();
```

### Waterfall Bridge Builder

```javascript
// TEMPLATE: Build waterfall bridge Excel output
// Expects: budgetData and actualData objects already populated

const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
    const workbook = new ExcelJS.Workbook();
    
    // --- SHEET 1: WATERFALL ---
    const ws = workbook.addWorksheet('Waterfall');
    
    const components = ['Budget', 'Volume', 'B2C', 'Stop Fee', 'Weight', 'Ad Hoc', 'RBS', 'Pickup', 'Actual'];
    const values = [
        budgetTotal,
        volumeVariance,
        b2cVariance,
        stopFeeVariance,
        weightVariance,
        adHocVariance,
        rbsVariance,
        pickupVariance,
        actualTotal
    ];
    
    // Header
    const hdr = ws.addRow(['Component', 'Amount ($)', 'Cumulative ($)', 'Fav/Unfav']);
    hdr.font = { bold: true, color: { argb: 'FFFFFF' } };
    hdr.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: '2F5496' } };
    
    let cumulative = 0;
    components.forEach((comp, i) => {
        const val = values[i];
        if (comp === 'Budget') {
            cumulative = val;
        } else if (comp === 'Actual') {
            cumulative = val;
        } else {
            cumulative += val;
        }
        
        const isEndpoint = (comp === 'Budget' || comp === 'Actual');
        const isFavorable = val < 0; // negative = favorable (cost decrease)
        
        const row = ws.addRow([
            comp,
            isEndpoint ? val : val,
            cumulative,
            isEndpoint ? '' : (isFavorable ? 'Favorable' : 'Unfavorable')
        ]);
        
        row.getCell(2).numFmt = '$#,##0';
        row.getCell(3).numFmt = '$#,##0';
        
        if (!isEndpoint) {
            row.getCell(2).font = { 
                color: { argb: isFavorable ? '008000' : 'CC0000' },
                bold: Math.abs(val) > 10000
            };
        }
    });
    
    // Validation row
    const checkVal = values.slice(1, -1).reduce((a, b) => a + b, 0);
    const expectedDelta = actualTotal - budgetTotal;
    ws.addRow([]);
    const valRow = ws.addRow([
        'VALIDATION',
        `Bridge sum: ${checkVal.toFixed(0)}`,
        `Actual-Budget: ${expectedDelta.toFixed(0)}`,
        Math.abs(checkVal - expectedDelta) < 100 ? '✓ TIES' : '✗ GAP: ' + (checkVal - expectedDelta).toFixed(0)
    ]);
    valRow.font = { bold: true };
    
    // Column widths
    ws.getColumn(1).width = 15;
    ws.getColumn(2).width = 18;
    ws.getColumn(3).width = 18;
    ws.getColumn(4).width = 14;
    ws.views = [{ state: 'frozen', ySplit: 1 }];
    
    await workbook.xlsx.writeFile('OUTPUT_PATH_HERE');
    console.log('Waterfall saved.');
})();
```

---

## 9. JOB SEARCH TASKS

### Resume Tailoring
1. Read the job posting carefully
2. Pull Craig's experience from MEMORY.md
3. For each job requirement, find Craig's matching experience
4. Write bullets: "[Action verb] [what you did] [quantified result] [for whom]"
5. Mirror the posting's language where natural
6. Output as Word doc using a clean professional template

### Networking Outreach
```
Pattern (keep under 75 words):
"Hi [Name], I'm [Craig / a supply chain finance leader] exploring 
[what you're looking for]. I noticed [something specific about them 
or their company]. [Specific connection point or question]. Would 
you have 15 minutes for a quick chat? Happy to work around your 
schedule. Best, Craig"
```

### Interview Prep
For each "tell me about a time" question, prep a STAR story:
- **S**ituation: 1 sentence setting the scene (company, role, context)
- **T**ask: What Craig needed to accomplish
- **A**ction: Specific steps Craig took (this is the longest part)
- **R**esult: Quantified outcome ($X saved, Y% improvement, Z time reduction)

---

## 10. EMAIL & COMMUNICATION

### Sending Email
- Use Gmail credentials from TOOLS.md
- Never ask Craig to send it himself
- Default: professional but not stiff
- Always include a clear subject line
- For internal emails: get to the point in sentence 1
- For external emails: brief warm opening, then the point

### Leadership Updates
```
Pattern:
Subject: [Month/Week] Cost Update: [headline number]

[One line summary with the key number]

Top drivers:
• [Driver 1]: [$X] — [one line why]
• [Driver 2]: [$X] — [one line why]
• [Driver 3]: [$X] — [one line why]

[One line on outlook/action items]

[Attachment reference if applicable]
```

---

## GENERAL RULES FOR ALL TASKS

1. **Always save output as Excel** unless Craig specifically asks for something else
2. **Always include a validation check** — do the numbers tie?
3. **Always include top facility drivers** — Craig's leadership always asks "which facilities?"
4. **Always update MEMORY.md** after completing a major deliverable
5. **Never deliver Markdown when Excel is possible** — Craig's world is Excel
6. **Never explain what you're about to do** — just do it and show the result
7. **If data is missing, say specifically what you need** — "I need the January actuals from CCH_Files_clean.xlsx, specifically the 4wk and 5wk tabs" not "I need more data"
8. **Round to whole dollars in summaries, keep cents in detail tabs**
9. **Favorable = green = negative cost delta. Unfavorable = red = positive cost delta.** Never get this backwards.
10. **Every deliverable should be ready for Craig's VP** — professional formatting, no raw data dumps, clear labels, proper number formats
