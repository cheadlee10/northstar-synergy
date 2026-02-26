"""
Compare R18:V35 formulas between 8wk tab and Templates tab.
Look for structural differences, wrong column/row references, mismatched sources.
"""
import zipfile, xml.etree.ElementTree as ET, re, sys

NS  = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def col_idx(col_str):
    r = 0
    for ch in col_str.upper():
        r = r * 26 + ord(ch) - 64
    return r - 1

def cell_to_rc(ref):
    m = re.match(r'([A-Z]+)(\d+)', ref.upper())
    if not m: return None, None
    return int(m.group(2)), col_idx(m.group(1))

def get_sheet_path(zf, name):
    with zf.open('xl/workbook.xml') as f:
        root = ET.parse(f).getroot()
    for sh in root.find(f'{{{NS}}}sheets').findall(f'{{{NS}}}sheet'):
        if sh.get('name') == name:
            rid = sh.get(f'{{{REL}}}id')
            break
    else:
        return None
    with zf.open('xl/_rels/workbook.xml.rels') as f:
        for rel in ET.parse(f).getroot():
            if rel.get('Id') == rid:
                t = rel.get('Target')
                return t if t.startswith('xl/') else 'xl/' + t

def load_ss(zf):
    ss = []
    if 'xl/sharedStrings.xml' not in zf.namelist(): return ss
    with zf.open('xl/sharedStrings.xml') as f:
        root = ET.parse(f).getroot()
    for si in root:
        parts = [el.text for el in si.iter() if el.tag==f'{{{NS}}}t' and el.text]
        ss.append(''.join(parts))
    return ss

def read_cells(zf, sheet_name, min_row, max_row, min_col_letter, max_col_letter):
    """Returns dict: 'A1' -> {'formula': str|None, 'value': any}"""
    ss = load_ss(zf)
    path = get_sheet_path(zf, sheet_name)
    if not path:
        return {}
    min_c = col_idx(min_col_letter)
    max_c = col_idx(max_col_letter)
    result = {}
    with zf.open(path) as f:
        for event, el in ET.iterparse(f, events=('end',)):
            if el.tag == f'{{{NS}}}c':
                ref = el.get('r','')
                row, col = cell_to_rc(ref)
                if row is None: continue
                if not (min_row <= row <= max_row): continue
                if not (min_c <= col <= max_c): continue
                t_type = el.get('t','')
                f_el = el.find(f'{{{NS}}}f')
                v_el = el.find(f'{{{NS}}}v')
                formula = f_el.text if f_el is not None else None
                value = None
                if v_el is not None and v_el.text is not None:
                    if t_type == 's':
                        try: value = ss[int(v_el.text)]
                        except: value = v_el.text
                    else:
                        try:
                            fv = float(v_el.text)
                            value = int(fv) if fv == int(fv) else round(fv, 6)
                        except: value = v_el.text
                result[ref] = {'formula': formula, 'value': value}
                el.clear()
    return result

# ── Load both sheets ──────────────────────────────────────────────────────────
FILE = 'CCH_new.xlsx'
with zipfile.ZipFile(FILE, 'r') as zf:
    wk8  = read_cells(zf, '8wk',      18, 35, 'R', 'V')
    tmpl = read_cells(zf, 'Templates', 1, 60, 'R', 'V')

# ── Helper: normalize formula for comparison ─────────────────────────────────
def norm(f):
    if f is None: return None
    return re.sub(r'\s+', ' ', f).strip().upper()

def col_refs(formula):
    """Extract all column letter references from formula (e.g., $BK:$BK → BK)"""
    if not formula: return set()
    return set(re.findall(r'\$([A-Z]+):\$\1', formula.upper()))

def row_refs_in_range(formula):
    """Extract row numbers in INDEX range refs like $D$65:$I$65"""
    if not formula: return set()
    return set(re.findall(r'\$[A-Z]+\$(\d+):\$[A-Z]+\$\1', formula.upper()))

def source_workbook(formula):
    """Extract workbook reference like [6]Output_Summary or '[1]Monthly Data'"""
    if not formula: return None
    m = re.search(r"\[(\d+)\]([^!']+)", formula)
    return m.group(0) if m else None

# ── Validation ────────────────────────────────────────────────────────────────
ROWS  = range(18, 36)
COLS  = ['R','S','T','U','V']
issues = []

def flag(sev, cell, desc):
    issues.append((sev, cell, desc))

print("=" * 80)
print("WBR FORMULA VALIDATION — R18:V35 (8wk vs Templates)")
print("=" * 80)

for row in ROWS:
    for col in COLS:
        ref = f'{col}{row}'
        w8_cell  = wk8.get(ref, {})
        tm_cell  = tmpl.get(ref, {})
        w8_f  = w8_cell.get('formula')
        tm_f  = tm_cell.get('formula')
        w8_v  = w8_cell.get('value')
        tm_v  = tm_cell.get('value')

        # Only validate cells that have formulas in at least one tab
        if w8_f is None and tm_f is None:
            continue

        # Both have formulas — compare structure
        if w8_f and tm_f:
            w8_cols = col_refs(w8_f)
            tm_cols = col_refs(tm_f)
            w8_rows = row_refs_in_range(w8_f)
            tm_rows = row_refs_in_range(tm_f)
            w8_src  = source_workbook(w8_f)
            tm_src  = source_workbook(tm_f)

            if w8_cols != tm_cols and w8_cols and tm_cols:
                flag('🔴 CRITICAL', ref,
                     f"Column mismatch: 8wk={w8_cols} vs Templates={tm_cols}")

            if w8_rows != tm_rows and w8_rows and tm_rows:
                flag('🔴 CRITICAL', ref,
                     f"Row range mismatch: 8wk=row{w8_rows} vs Templates=row{tm_rows}")

            if w8_src and tm_src and w8_src.lower() != tm_src.lower():
                flag('🔴 CRITICAL', ref,
                     f"Source workbook mismatch:\n"
                     f"        8wk:      {w8_src}\n"
                     f"        Templates:{tm_src}")

        # 8wk has formula, Templates has hardcoded value (frozen prior week)
        if w8_f and tm_f is None and tm_v is not None:
            pass  # expected — Templates column T is frozen

        # Templates has formula, 8wk has hardcoded value — unexpected
        if tm_f and w8_f is None and w8_v is not None:
            flag('🟡 WARN', ref,
                 f"Templates has formula but 8wk has hardcoded value={w8_v}")

# ── Check for hardcoded cross-column date references in U-column formulas ──────
# U-column formulas should reference U$16/U$17, not V$16/V$17
for row in ROWS:
    for col in ['U','V']:
        ref = f'{col}{row}'
        for tab, cells in [('8wk', wk8), ('Templates', tmpl)]:
            f = cells.get(ref, {}).get('formula')
            if not f: continue
            wrong_cols = []
            for other in ['T','U','V','W']:
                if other == col: continue
                pattern = rf'\${other}\${row}|\${other}\$16|\${other}\$17'
                # Check for absolute wrong-column date references
                if col == 'U' and re.search(r'\$V\$16|\$V\$17', f, re.I):
                    wrong_cols.append('$V$16/$V$17 in a U-column formula')
                if col == 'V' and re.search(r'\$U\$16|\$U\$17', f, re.I):
                    wrong_cols.append('$U$16/$U$17 in a V-column formula')
            if wrong_cols:
                flag('🟡 WARN', f'{tab}!{ref}',
                     f"Cross-column absolute date ref: {'; '.join(set(wrong_cols))}")

# ── Print results ─────────────────────────────────────────────────────────────
if not issues:
    print("\n✅ No structural formula discrepancies found in R18:V35")
else:
    crit = [x for x in issues if x[0].startswith('🔴')]
    warn = [x for x in issues if x[0].startswith('🟡')]
    print(f"\nFound {len(crit)} CRITICAL issues and {len(warn)} warnings:\n")
    for sev, cell, desc in issues:
        print(f"{sev}  {cell}")
        print(f"        {desc}")
        print()

# ── Also print side-by-side for all cells with formulas ──────────────────────
print("\n" + "=" * 80)
print("SIDE-BY-SIDE FORMULA COMPARISON (cells with formulas in either tab)")
print("=" * 80)
for row in ROWS:
    for col in COLS:
        ref = f'{col}{row}'
        w8_f = wk8.get(ref,{}).get('formula')
        tm_f = tmpl.get(ref,{}).get('formula')
        if w8_f or tm_f:
            match = '✅' if norm(w8_f) == norm(tm_f) else ('⚠️ ' if (w8_f and tm_f) else '📌')
            print(f"\n{match} {ref}")
            if w8_f:  print(f"   8wk:       {w8_f[:120]}")
            if tm_f:  print(f"   Templates: {tm_f[:120]}")
            if not w8_f and wk8.get(ref,{}).get('value') is not None:
                print(f"   8wk VALUE: {wk8[ref]['value']}")
            if not tm_f and tmpl.get(ref,{}).get('value') is not None:
                print(f"   Tmpl VALUE:{tmpl[ref]['value']}")
