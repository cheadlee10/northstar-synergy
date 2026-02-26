"""
read_excel_highlights.py
========================
Reads cell highlight colors from any Excel (.xlsx) file without loading
the full workbook into memory. Parses the underlying XML directly.

Usage:
    python read_excel_highlights.py "path/to/file.xlsx" "Sheet Name"
    python read_excel_highlights.py "path/to/file.xlsx" "Sheet Name" --color FFFFFF00

Output:
    JSON array of highlighted rows: [{row, col_b_value, rgb, col_values...}]

Notes:
    - Reads styles.xml to build fill color index
    - Reads sheet XML row-by-row (memory efficient, works on 100MB+ files)
    - Returns ALL colored cells by default; filter by hex color with --color
    - Yellow highlight = FFFFFF00 (with alpha) or FFFF00 (without)
    - "00000000" and "FF000000" = no fill / default, skipped automatically
"""

import zipfile
import xml.etree.ElementTree as ET
import json
import sys
import argparse
import re

NS_SS   = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS_REL  = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def col_letter_to_index(col_str):
    """Convert Excel column letter(s) to 0-based index. A=0, B=1, AA=26 ..."""
    result = 0
    for ch in col_str.upper():
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result - 1


def cell_ref_to_row_col(ref):
    """'B7' -> (row=6, col=1)  (both 0-based)"""
    m = re.match(r'([A-Z]+)(\d+)', ref.upper())
    if not m:
        return None, None
    return int(m.group(2)) - 1, col_letter_to_index(m.group(1))


def build_fill_index(zf):
    """
    Parse styles.xml and return a dict: xf_index -> rgb_hex_string
    Only returns fills that are actual color fills (not default/none).
    """
    try:
        with zf.open('xl/styles.xml') as f:
            tree = ET.parse(f)
    except KeyError:
        return {}

    root = tree.getroot()
    tag = lambda name: f'{{{NS_SS}}}{name}'

    # Build fills list: index -> rgb
    fills = []
    fills_el = root.find(tag('fills'))
    if fills_el is not None:
        for fill_el in fills_el.findall(tag('fill')):
            rgb = None
            pf = fill_el.find(tag('patternFill'))
            if pf is not None:
                ptype = pf.get('patternType', 'none')
                fg = pf.find(tag('fgColor'))
                if fg is not None:
                    rgb = fg.get('rgb')  # e.g. "FFFFFF00"
                    if not rgb:
                        # theme color — not a simple hex, store as theme:N
                        theme = fg.get('theme')
                        tint  = fg.get('tint', '0')
                        if theme is not None:
                            rgb = f'theme:{theme}:{tint}'
                if ptype == 'none':
                    rgb = None  # no fill
            fills.append(rgb)

    # Build xf (cell format) list: index -> fill_id
    xfs = []
    cell_xfs = root.find(tag('cellXfs'))
    if cell_xfs is not None:
        for xf in cell_xfs.findall(tag('xf')):
            fill_id = int(xf.get('fillId', 0))
            xfs.append(fill_id)

    # Map xf_index -> rgb
    result = {}
    for i, fill_id in enumerate(xfs):
        if fill_id < len(fills) and fills[fill_id] is not None:
            result[i] = fills[fill_id]

    return result


def get_sheet_path(zf, sheet_name):
    """Find the XML path for the named sheet inside the zip."""
    # Read workbook.xml to get sheet rId
    try:
        with zf.open('xl/workbook.xml') as f:
            tree = ET.parse(f)
    except KeyError:
        return None

    root = tree.getroot()
    tag = lambda name: f'{{{NS_SS}}}{name}'
    tag_r = lambda name: f'{{{NS_REL}}}{name}'

    sheets = root.find(tag('sheets'))
    r_id = None
    if sheets is not None:
        for sh in sheets.findall(tag('sheet')):
            if sh.get('name') == sheet_name:
                r_id = sh.get(f'{{{NS_REL}}}id')
                break

    if r_id is None:
        return None

    # Read workbook.xml.rels to get the filename
    try:
        with zf.open('xl/_rels/workbook.xml.rels') as f:
            tree = ET.parse(f)
    except KeyError:
        return None

    for rel in tree.getroot():
        if rel.get('Id') == r_id:
            target = rel.get('Target')
            if not target.startswith('xl/'):
                target = 'xl/' + target
            return target

    return None


def read_highlighted_rows(filepath, sheet_name, filter_color=None, header_row=4, data_start_row=5, branch_col='B'):
    """
    Main function. Returns list of dicts for rows where branch_col cell is highlighted.
    filter_color: optional hex string to match (e.g. 'FFFFFF00' for yellow)
    """
    results = []
    branch_col_idx = col_letter_to_index(branch_col)

    with zipfile.ZipFile(filepath, 'r') as zf:
        fill_index = build_fill_index(zf)
        sheet_path = get_sheet_path(zf, sheet_name)
        if sheet_path is None:
            print(f"ERROR: Sheet '{sheet_name}' not found.", file=sys.stderr)
            return results

        with zf.open(sheet_path) as f:
            # Parse incrementally
            context = ET.iterparse(f, events=('start', 'end'))
            tag_row = f'{{{NS_SS}}}row'
            tag_c   = f'{{{NS_SS}}}c'
            tag_v   = f'{{{NS_SS}}}v'
            tag_t   = f'{{{NS_SS}}}t'  # inline string

            # Build shared strings for string lookups
            ss_list = []

        # Load shared strings
        with zf.open(filepath) if False else zf.open('xl/sharedStrings.xml') if 'xl/sharedStrings.xml' in zf.namelist() else open(os.devnull) as ssf:
            ss_tree = ET.parse(ssf)
            for si in ss_tree.getroot():
                parts = []
                for elem in si.iter():
                    if elem.tag == f'{{{NS_SS}}}t' and elem.text:
                        parts.append(elem.text)
                ss_list.append(''.join(parts))

        with zf.open(sheet_path) as f:
            context = ET.iterparse(f, events=('start', 'end'))
            current_row_num = 0
            current_row_cells = {}
            branch_cell_style = None

            for event, elem in context:
                if event == 'start' and elem.tag == tag_row:
                    r_attr = elem.get('r')
                    current_row_num = int(r_attr) if r_attr else 0
                    current_row_cells = {}
                    branch_cell_style = None

                elif event == 'end' and elem.tag == tag_c:
                    ref = elem.get('r', '')
                    row_idx, col_idx = cell_ref_to_row_col(ref)
                    style_idx = int(elem.get('s', 0))

                    # Get value
                    t_type = elem.get('t', '')
                    v_el = elem.find(tag_v)
                    val = None
                    if v_el is not None and v_el.text:
                        if t_type == 's':
                            try:
                                val = ss_list[int(v_el.text)]
                            except:
                                val = v_el.text
                        elif t_type == 'str' or t_type == 'inlineStr':
                            t_el = elem.find(tag_t)
                            val = t_el.text if t_el is not None else v_el.text
                        else:
                            try:
                                val = float(v_el.text)
                                if val == int(val):
                                    val = int(val)
                            except:
                                val = v_el.text

                    current_row_cells[col_idx] = val

                    # Track highlight on branch column
                    if col_idx == branch_col_idx:
                        rgb = fill_index.get(style_idx)
                        if rgb and rgb not in ('00000000', 'FF000000', 'FFFFFFFF'):
                            branch_cell_style = rgb

                    elem.clear()

                elif event == 'end' and elem.tag == tag_row:
                    if current_row_num >= data_start_row and branch_cell_style is not None:
                        branch_val = current_row_cells.get(branch_col_idx)
                        rgb = branch_cell_style
                        if filter_color is None or filter_color.upper() in rgb.upper():
                            results.append({
                                'row': current_row_num,
                                'branch': branch_val,
                                'highlight_rgb': rgb,
                                'cells': {str(k): v for k, v in current_row_cells.items()}
                            })
                    elem.clear()

    return results


def list_sheets(filepath):
    """List all sheet names in the workbook."""
    with zipfile.ZipFile(filepath, 'r') as zf:
        with zf.open('xl/workbook.xml') as f:
            tree = ET.parse(f)
    root = tree.getroot()
    tag = lambda name: f'{{{NS_SS}}}{name}'
    sheets = root.find(tag('sheets'))
    names = []
    if sheets:
        for sh in sheets.findall(tag('sheet')):
            names.append(sh.get('name'))
    return names


if __name__ == '__main__':
    import os
    parser = argparse.ArgumentParser(description='Read highlighted rows from Excel file')
    parser.add_argument('filepath', help='Path to .xlsx file')
    parser.add_argument('sheet', nargs='?', help='Sheet name (omit to list sheets)')
    parser.add_argument('--color', help='Filter by RGB hex (e.g. FFFFFF00 for yellow)')
    parser.add_argument('--header-row', type=int, default=4)
    parser.add_argument('--data-start', type=int, default=5)
    parser.add_argument('--branch-col', default='B')
    args = parser.parse_args()

    if not args.sheet:
        print("Available sheets:", list_sheets(args.filepath))
        sys.exit(0)

    rows = read_highlighted_rows(
        args.filepath, args.sheet,
        filter_color=args.color,
        header_row=args.header_row,
        data_start_row=args.data_start,
        branch_col=args.branch_col
    )

    print(json.dumps(rows, indent=2, default=str))
    print(f"\n# Highlighted rows found: {len(rows)}", file=sys.stderr)
