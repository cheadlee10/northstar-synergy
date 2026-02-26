"""
Read raw cell formulas from a sheet by parsing XML directly.
Returns both formula and cached value for each cell.
"""
import zipfile, xml.etree.ElementTree as ET, json, sys, re

NS  = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def col_idx(col_str):
    r = 0
    for ch in col_str.upper():
        r = r*26 + ord(ch) - 64
    return r - 1

def cell_to_rc(ref):
    m = re.match(r'([A-Z]+)(\d+)', ref.upper())
    if not m: return None, None
    return int(m.group(2)), col_idx(m.group(1))

def get_sheet_path(zf, sheet_name):
    with zf.open('xl/workbook.xml') as f:
        root = ET.parse(f).getroot()
    for sh in root.find(f'{{{NS}}}sheets').findall(f'{{{NS}}}sheet'):
        if sh.get('name') == sheet_name:
            rid = sh.get(f'{{{REL}}}id')
            break
    else:
        return None
    with zf.open('xl/_rels/workbook.xml.rels') as f:
        for rel in ET.parse(f).getroot():
            if rel.get('Id') == rid:
                t = rel.get('Target')
                return t if t.startswith('xl/') else 'xl/' + t
    return None

def load_shared_strings(zf):
    ss = []
    if 'xl/sharedStrings.xml' not in zf.namelist():
        return ss
    with zf.open('xl/sharedStrings.xml') as f:
        root = ET.parse(f).getroot()
    for si in root:
        parts = []
        for el in si.iter():
            if el.tag == f'{{{NS}}}t' and el.text:
                parts.append(el.text)
        ss.append(''.join(parts))
    return ss

def read_sheet_formulas(filepath, sheet_name, min_row=1, max_row=999, min_col=1, max_col=100):
    """Returns dict: {(row, col): {'ref': 'A1', 'formula': ..., 'value': ...}}"""
    result = {}
    with zipfile.ZipFile(filepath, 'r') as zf:
        ss = load_shared_strings(zf)
        path = get_sheet_path(zf, sheet_name)
        if not path:
            print(f"ERROR: sheet '{sheet_name}' not found", file=sys.stderr)
            return result

        with zf.open(path) as f:
            for event, el in ET.iterparse(f, events=('end',)):
                if el.tag == f'{{{NS}}}c':
                    ref = el.get('r','')
                    row, col = cell_to_rc(ref)
                    if row is None: continue
                    if not (min_row <= row <= max_row): continue
                    if not (min_col <= col+1 <= max_col): continue

                    t_type = el.get('t','')
                    f_el   = el.find(f'{{{NS}}}f')
                    v_el   = el.find(f'{{{NS}}}v')

                    formula = f_el.text if f_el is not None else None
                    value   = None
                    if v_el is not None and v_el.text is not None:
                        if t_type == 's':
                            try: value = ss[int(v_el.text)]
                            except: value = v_el.text
                        else:
                            try:
                                fv = float(v_el.text)
                                value = int(fv) if fv == int(fv) else fv
                            except: value = v_el.text

                    result[(row, col)] = {'ref': ref, 'formula': formula, 'value': value}
                    el.clear()

    return result

if __name__ == '__main__':
    filepath   = sys.argv[1] if len(sys.argv)>1 else 'CCH_new.xlsx'
    sheet_name = sys.argv[2] if len(sys.argv)>2 else '8wk'
    min_row    = int(sys.argv[3]) if len(sys.argv)>3 else 1
    max_row    = int(sys.argv[4]) if len(sys.argv)>4 else 50

    data = read_sheet_formulas(filepath, sheet_name, min_row=min_row, max_row=max_row)
    # Print as table
    rows_seen = sorted(set(r for r,c in data))
    cols_seen = sorted(set(c for r,c in data))
    print(f"Sheet: {sheet_name}  |  Rows {min_row}-{max_row}  |  {len(data)} cells\n")
    for row in rows_seen:
        for col in cols_seen:
            if (row, col) in data:
                cell = data[(row, col)]
                ref  = cell['ref']
                frm  = cell['formula']
                val  = cell['value']
                if frm:
                    print(f"  {ref:6}  formula={frm[:120]}")
                elif val is not None:
                    print(f"  {ref:6}  value={str(val)[:60]}")
