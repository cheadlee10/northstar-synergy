const path = require('path');
const ExcelJS = require(path.join('C:','Users','chead','AppData','Roaming','npm','node_modules','exceljs'));

(async () => {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile('C:/Users/chead/OneDrive/Documents/CCH_Files_clean.xlsx');

  // Helper to get cell value (handles formula results)
  function val(cell) {
    if (!cell) return null;
    const v = cell.value;
    if (v === null || v === undefined) return null;
    if (typeof v === 'object' && v.result !== undefined) {
      if (typeof v.result === 'object' && v.result !== null && v.result.error) return null;
      return v.result;
    }
    if (typeof v === 'object' && v.error) return null;
    if (typeof v === 'object' && v.richText) return v.richText.map(r => r.text).join('');
    if (typeof v === 'object' && v instanceof Date) return v;
    return v;
  }

  const ws = wb.getWorksheet('by Facility_wk');
  
  // Col indices (1-based): A=1,B=2,C=3,D=4,E=5,J=10,K=11,L=12,R=18,AA=27
  // D=FacilityName, C=Week, E=Commissions, J=B2C Volume, K=PowerBI CPP, L=East/West, R=B2C CPP, AA=TotalAdhoc
  
  const COL = {
    YEAR: 1, DATE: 2, WEEK: 3, FACILITY: 4,
    COMMISSIONS: 5,   // Sum of Commissions (total driver cost)
    B2B_COMM: 6,
    WEST_PU: 7,
    WEST_SP: 8,
    VOL_B2B: 9,
    VOL_B2C: 10,     // Sum of Volume_ECOM_RES (B2C stops)
    CPP: 11,          // Power BI CPP
    EW: 12,           // East/West
    GROUPS: 13,
    FAC_ADJ: 14,
    CODE: 15,
    CODE3: 16,
    CODE_NUM: 17,
    B2C_CPP: 18,      // Power BI B2C CPP
    ADJ_TOTAL: 27,    // AA: Total Adhoc/Adj/Special
  };

  // Read all facility rows: skip first 4 rows (header area), week summary rows have D=null
  const byFacility = {};
  
  ws.eachRow((row, rowNum) => {
    if (rowNum < 5) return;
    const wk = val(row.getCell(COL.WEEK));
    const fac = val(row.getCell(COL.FACILITY));
    if (!fac || !wk || typeof wk !== 'number') return;
    
    const comm = val(row.getCell(COL.COMMISSIONS));
    const volB2C = val(row.getCell(COL.VOL_B2C));
    const cpp = val(row.getCell(COL.CPP));
    const ew = val(row.getCell(COL.EW));
    const b2cCpp = val(row.getCell(COL.B2C_CPP));
    const adj = val(row.getCell(COL.ADJ_TOTAL));
    
    if (!byFacility[wk]) byFacility[wk] = {};
    byFacility[wk][fac] = {
      wk, fac, comm: comm || 0, volB2C: volB2C || 0,
      cpp: cpp || 0, ew: ew || '', b2cCpp: b2cCpp || 0,
      adj: adj || 0
    };
  });

  const weeks = Object.keys(byFacility).map(Number).sort((a,b) => a-b);
  console.log('Available weeks:', weeks);
  
  const curWk = 8;
  const prvWk = 7;
  
  const cur = byFacility[curWk] || {};
  const prv = byFacility[prvWk] || {};
  
  const curFacs = Object.keys(cur);
  const prvFacs = Object.keys(prv);
  
  console.log(`\nWk ${curWk} facilities: ${curFacs.length}`);
  console.log(`Wk ${prvWk} facilities: ${prvFacs.length}`);

  // ---- Budget file ----
  let budgetData = {};
  try {
    const wb2 = new ExcelJS.Workbook();
    await wb2.xlsx.readFile('C:/Users/chead/OneDrive/Documents/Craig_Budget_2026.xlsx');
    const sheets2 = wb2.worksheets.map(s => s.name);
    console.log('\nBudget sheets:', sheets2);
    // Try to find a CPP budget sheet
    const budSheet = wb2.getWorksheet('CPP') || wb2.getWorksheet('Budget') || wb2.worksheets[0];
    if (budSheet) {
      console.log('Using budget sheet:', budSheet.name);
      budSheet.eachRow((row, rn) => {
        if (rn < 2) return;
        const f = val(row.getCell(1));
        const c = val(row.getCell(2));
        if (f && c && typeof c === 'number') budgetData[f] = c;
      });
      console.log('Budget entries:', Object.keys(budgetData).length);
    }
  } catch(e) {
    console.log('Budget file not available:', e.message);
  }

  // ---- WoW Analysis ----
  const allFacs = [...new Set([...curFacs, ...prvFacs])];
  
  const wowData = allFacs.map(fac => {
    const c = cur[fac] || { comm:0, volB2C:0, cpp:0, adj:0 };
    const p = prv[fac] || { comm:0, volB2C:0, cpp:0, adj:0 };
    const cppWow = c.cpp - p.cpp;
    const commWow = c.comm - p.comm;
    const volWow = c.volB2C - p.volB2C;
    const budCpp = budgetData[fac] || null;
    const vsBudget = budCpp ? ((c.cpp - budCpp) / budCpp) : null;
    return { fac, ew: c.ew || p.ew,
      curComm: c.comm, prvComm: p.comm, commWow,
      curVol: c.volB2C, prvVol: p.volB2C, volWow,
      curCpp: c.cpp, prvCpp: p.cpp, cppWow,
      curAdj: c.adj, budCpp, vsBudget
    };
  }).filter(d => d.curComm > 0 || d.prvComm > 0);

  // Sort by commission $ for top 10
  const top10Cost = [...wowData].sort((a,b) => b.curComm - a.curComm).slice(0, 10);
  
  // Top WoW movers (CPP change)
  const top10CppWoW = [...wowData].filter(d => d.curCpp > 0 && d.prvCpp > 0)
    .sort((a,b) => Math.abs(b.cppWow) - Math.abs(a.cppWow)).slice(0, 10);
  
  // Over budget >5%
  const overBudget = wowData.filter(d => d.vsBudget !== null && d.vsBudget > 0.05)
    .sort((a,b) => b.vsBudget - a.vsBudget);
  
  // Totals
  const totCurComm = wowData.reduce((s,d) => s + d.curComm, 0);
  const totPrvComm = wowData.reduce((s,d) => s + d.prvComm, 0);
  const totCurVol = wowData.reduce((s,d) => s + d.curVol, 0);
  const totPrvVol = wowData.reduce((s,d) => s + d.prvVol, 0);
  const totCurCpp = totCurVol > 0 ? totCurComm / totCurVol : 0;
  const totPrvCpp = totPrvVol > 0 ? totPrvComm / totPrvVol : 0;

  const fmt$ = n => '$' + Number(n).toLocaleString('en-US', {maximumFractionDigits:0});
  const fmtPct = n => (n >= 0 ? '+' : '') + (n*100).toFixed(1) + '%';
  const fmtCpp = n => '$' + Number(n).toFixed(4);

  console.log('\n=== SUMMARY ===');
  console.log(`Wk${curWk} Total Driver Cost: ${fmt$(totCurComm)}`);
  console.log(`Wk${prvWk} Total Driver Cost: ${fmt$(totPrvComm)}`);
  console.log(`WoW Change: ${fmt$(totCurComm - totPrvComm)} (${fmtPct((totCurComm-totPrvComm)/totPrvComm)})`);
  console.log(`Wk${curWk} Total B2C Vol: ${Number(totCurVol).toLocaleString()}`);
  console.log(`Wk${prvWk} Total B2C Vol: ${Number(totPrvVol).toLocaleString()}`);
  console.log(`Wk${curWk} Avg CPP: ${fmtCpp(totCurCpp)}`);
  console.log(`Wk${prvWk} Avg CPP: ${fmtCpp(totPrvCpp)}`);
  console.log(`CPP WoW: ${fmtCpp(totCurCpp - totPrvCpp)} (${fmtPct((totCurCpp-totPrvCpp)/totPrvCpp)})`);

  console.log('\n=== TOP 10 FACILITIES BY WK8 DRIVER COST ===');
  top10Cost.forEach((d,i) => {
    const wow = d.prvComm ? fmtPct((d.curComm-d.prvComm)/d.prvComm) : 'N/A';
    console.log(`${i+1}. ${d.fac} (${d.ew}): ${fmt$(d.curComm)} | WoW ${wow} | CPP ${fmtCpp(d.curCpp)}`);
  });

  console.log('\n=== TOP 10 CPP MOVERS WoW (Wk7→Wk8) ===');
  top10CppWoW.forEach((d,i) => {
    const dir = d.cppWow > 0 ? '▲' : '▼';
    console.log(`${i+1}. ${d.fac} (${d.ew}): ${dir} ${fmtCpp(Math.abs(d.cppWow))} | Wk7: ${fmtCpp(d.prvCpp)} → Wk8: ${fmtCpp(d.curCpp)}`);
  });

  if (overBudget.length > 0) {
    console.log('\n=== FACILITIES > 5% OVER CPP BUDGET ===');
    overBudget.forEach((d,i) => {
      console.log(`${i+1}. ${d.fac}: Actual ${fmtCpp(d.curCpp)} vs Budget ${fmtCpp(d.budCpp)} = ${fmtPct(d.vsBudget)}`);
    });
  } else if (Object.keys(budgetData).length === 0) {
    console.log('\n[Budget comparison not available - budget data not loaded]');
  } else {
    console.log('\n=== NO FACILITIES > 5% OVER CPP BUDGET ===');
  }

  console.log('\n=== ALL WK8 FACILITIES (for commentary) ===');
  wowData.filter(d => d.curComm > 0).sort((a,b) => b.curComm - a.curComm).forEach(d => {
    const cppDir = d.cppWow > 0 ? '▲' : d.cppWow < 0 ? '▼' : '=';
    console.log(`${d.fac}|${d.ew}|${fmt$(d.curComm)}|${fmtCpp(d.curCpp)}|${cppDir}${fmtCpp(Math.abs(d.cppWow))}`);
  });

})();
