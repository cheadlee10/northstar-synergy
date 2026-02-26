import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import os

OUT_DIR = r"C:\Users\chead\.openclaw\workspace\chart_output"
os.makedirs(OUT_DIR, exist_ok=True)

facilities = [
    {"name":"Dallas",      "rbs":2.2894,"stop":2.5677,"gap":0.2783,"savings":1598808,"vol":27866,"ppr":150.5,"miles":100.8},
    {"name":"Atlanta",     "rbs":2.7449,"stop":3.0666,"gap":0.3217,"savings":1444734,"vol":21779,"ppr":124.9,"miles":109.5},
    {"name":"Northern NJ", "rbs":1.9651,"stop":2.1371,"gap":0.1720,"savings":1151791,"vol":32489,"ppr":193.1,"miles":57.2},
    {"name":"Pittsburgh",  "rbs":2.1221,"stop":2.6804,"gap":0.5583,"savings":1143651,"vol":9935, "ppr":159.8,"miles":87.8},
    {"name":"Petaluma",    "rbs":2.2898,"stop":2.8387,"gap":0.5490,"savings":1050173,"vol":9278, "ppr":173.2,"miles":88.9},
    {"name":"Boise",       "rbs":2.0765,"stop":2.7071,"gap":0.6306,"savings":1007976,"vol":7753, "ppr":162.6,"miles":86.0},
    {"name":"Detroit",     "rbs":2.3432,"stop":2.6660,"gap":0.3228,"savings":867083, "vol":13027,"ppr":154.2,"miles":91.9},
    {"name":"Denver",      "rbs":2.1560,"stop":2.3277,"gap":0.1718,"savings":818971, "vol":23127,"ppr":171.8,"miles":72.5},
    {"name":"Toledo",      "rbs":2.3359,"stop":3.4872,"gap":1.1514,"savings":810087, "vol":3413, "ppr":150.0,"miles":124.7},
    {"name":"Tucson",      "rbs":1.9905,"stop":2.5824,"gap":0.5919,"savings":673984, "vol":5523, "ppr":173.0,"miles":81.9},
    {"name":"Miami",       "rbs":2.0036,"stop":2.1278,"gap":0.1242,"savings":483629, "vol":18887,"ppr":171.1,"miles":70.5},
    {"name":"Buckeye",     "rbs":2.1461,"stop":2.2317,"gap":0.0856,"savings":302364, "vol":17131,"ppr":166.6,"miles":86.4},
]

# Sort ASCENDING so largest gap (Toledo) appears at the TOP of horizontal bar chart
facs_sorted = sorted(facilities, key=lambda x: x['gap'])

NAVY   = "#1F3864"
ORANGE = "#C55A11"
TEAL   = "#2E75B6"
RED    = "#C00000"
LGREY  = "#F2F2F2"
TOTAL_SAV = sum(f['savings'] for f in facilities)

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1: Grouped Horizontal Bar — RBS vs Stop Payment CPP
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 8.5))
fig.patch.set_facecolor('white')
ax.set_facecolor(LGREY)
ax.set_axisbelow(True)
ax.xaxis.grid(True, color='white', linewidth=1.4, zorder=0)
ax.yaxis.grid(False)

names  = [f['name']     for f in facs_sorted]
rbs_v  = [f['rbs']      for f in facs_sorted]
stop_v = [f['stop']     for f in facs_sorted]
gaps   = [f['gap']      for f in facs_sorted]
savs   = [f['savings']  for f in facs_sorted]

y = np.arange(len(names))
h = 0.35

bars_stop = ax.barh(y + h/2, stop_v, h, label='Stop Payment (Current)', color=ORANGE, alpha=0.88, zorder=3)
bars_rbs  = ax.barh(y - h/2, rbs_v,  h, label='RBS (Proposed)',          color=NAVY,   alpha=0.92, zorder=3)

# CPP value labels inside bars
for bar, val in zip(bars_stop, stop_v):
    ax.text(val - 0.05, bar.get_y() + bar.get_height()/2,
            f'${val:.2f}', va='center', ha='right', fontsize=8.5, color='white', fontweight='bold')
for bar, val in zip(bars_rbs, rbs_v):
    ax.text(val - 0.05, bar.get_y() + bar.get_height()/2,
            f'${val:.2f}', va='center', ha='right', fontsize=8.5, color='white', fontweight='bold')

# Gap + savings annotation to the right of Stop bar
for i, (g, sv, stv) in enumerate(zip(gaps, savs, stop_v)):
    x_start = stv + 0.03
    sav_m = sv / 1e6
    ax.text(x_start, i, f'  Δ${g:.2f}/pkg  ·  ${sav_m:.2f}M saved',
            va='center', ha='left', fontsize=9,
            color=RED if g > 0.8 else '#375623',
            fontweight='bold')

ax.set_yticks(y)
ax.set_yticklabels(names, fontsize=11, fontweight='bold', color=NAVY)
ax.set_xlabel('Cost Per Package ($)', fontsize=11, color=NAVY, labelpad=8)
ax.set_title('RBS vs. Stop Payment — CPP by Facility\nSorted by savings opportunity: Toledo (top) has largest CPP gap',
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('$%.2f'))

# Extra room on the right for annotations
ax.set_xlim(0, max(stop_v) + 1.85)

# Legend
ax.legend(handles=[
    mpatches.Patch(color=ORANGE, label='Stop Payment CPP — current'),
    mpatches.Patch(color=NAVY,   label='RBS CPP — proposed'),
], loc='upper left', fontsize=10, framealpha=0.92, bbox_to_anchor=(0.01, 0.99))

# Total callout box — bottom LEFT so it doesn't clash with legend
ax.text(0.01, 0.01, f'Total Annual Savings (12 FACs)\n${TOTAL_SAV:,.0f}',
        transform=ax.transAxes, ha='left', va='bottom', fontsize=10, fontweight='bold',
        color='white', bbox=dict(boxstyle='round,pad=0.5', facecolor=NAVY, alpha=0.92))

# Subtitle note: arrow pointing to Toledo
ax.annotate('Largest gap:\n$1.15/pkg', xy=(3.49, 11), xytext=(3.7, 10.2),
            fontsize=8.5, color=RED, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=RED, lw=1.2))

plt.tight_layout()
p1 = os.path.join(OUT_DIR, 'chart1_cpp_comparison.png')
plt.savefig(p1, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Chart 1: {p1}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2: Bubble Chart — Route Density vs CPP Gap, sized by savings
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 9))
fig.patch.set_facecolor('white')
ax.set_facecolor(LGREY)
ax.grid(True, color='white', linewidth=1.4, zorder=0)
# Extra left/right margins
plt.subplots_adjust(left=0.1, right=0.88, top=0.88, bottom=0.10)

ppr_vals  = [f['ppr']     for f in facilities]
gap_vals  = [f['gap']     for f in facilities]
sav_vals  = [f['savings'] for f in facilities]
names_all = [f['name']    for f in facilities]

min_s, max_s = min(sav_vals), max(sav_vals)
bubble_sizes = [200 + 2000 * ((s - min_s) / (max_s - min_s)) for s in sav_vals]
gap_norm = [(g - min(gap_vals)) / (max(gap_vals) - min(gap_vals)) for g in gap_vals]

scatter = ax.scatter(ppr_vals, gap_vals, s=bubble_sizes,
                     c=gap_norm, cmap='RdYlGn_r',
                     alpha=0.82, edgecolors=NAVY, linewidths=1.5, zorder=4)

# Trend line (excl Toledo)
nt = [(p, g) for p, g, n in zip(ppr_vals, gap_vals, names_all) if n != 'Toledo']
px, gx = zip(*nt)
z = np.polyfit(px, gx, 1)
xfit = np.linspace(118, 200, 100)
ax.plot(xfit, np.poly1d(z)(xfit), '--', color=NAVY, alpha=0.45, linewidth=1.8,
        label='Trend (excl. Toledo outlier)', zorder=3)

# ── Labels: manually positioned to avoid overlaps ──
# Cluster issues: Pittsburgh(160,0.56), Boise(163,0.63), Petaluma(173,0.55), Tucson(173,0.59)
# Strategy: use directional offsets that push away from neighbors
label_cfg = {
    # name: (x_offset_pts, y_offset_pts, ha)
    'Dallas':      (-62, -28, 'right'),
    'Atlanta':     (-15, +22, 'right'),
    'Northern NJ': (+10, +16, 'left'),
    'Pittsburgh':  (-78, +10, 'right'),   # pushed far left away from Boise
    'Petaluma':    (+10, +22, 'left'),    # up more, right side
    'Boise':       (-78, -24, 'right'),   # far left, below Pittsburgh
    'Detroit':     (+10, -22, 'left'),
    'Denver':      (-15, +18, 'right'),   # left side to separate from Miami
    'Toledo':      (+10, +18, 'left'),
    'Tucson':      (-78, -22, 'right'),   # LEFT side to avoid right edge clip
    'Miami':       (+10, +16, 'left'),
    'Buckeye':     (-15, -24, 'right'),
}
for name, ppr, gap, sav in zip(names_all, ppr_vals, gap_vals, sav_vals):
    ox, oy, ha = label_cfg.get(name, (10, 10, 'left'))
    ax.annotate(f'{name}\n${sav/1e6:.2f}M',
                xy=(ppr, gap), xytext=(ox, oy), textcoords='offset points',
                fontsize=8.5, fontweight='bold', color=NAVY, ha=ha,
                arrowprops=dict(arrowstyle='->', color=NAVY, lw=0.8, connectionstyle='arc3,rad=0.1'))

# Toledo callout
ax.annotate('OUTLIER: Toledo\nVery high stop fee rate\nonly 3,413 pkgs/day\n→ $1.15 CPP gap',
            xy=(150, 1.15), xytext=(158, 0.82),
            fontsize=8.5, color=RED, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF2CC', alpha=0.9),
            arrowprops=dict(arrowstyle='->', color=RED, lw=1.3))

# Vertical divider at density = 165 (approx median)
ax.axvline(x=165, color='white', linestyle=':', linewidth=2, alpha=0.7)
ax.text(133, 0.03, '← Lower density\nBigger RBS advantage',
        fontsize=9, color='#7F0000', style='italic', alpha=0.85, ha='center')
ax.text(185, 0.03, 'Higher density →\nSavings from efficiency',
        fontsize=9, color='#1F4E79', style='italic', alpha=0.85, ha='center')

ax.set_xlabel('Route Density — Packages per Route  (lower = more RBS upside)',
              fontsize=11, color=NAVY, labelpad=8)
ax.set_ylabel('CPP Savings:  Stop Payment − RBS  ($)',
              fontsize=11, color=NAVY, labelpad=8)
ax.set_title("What Drives RBS Savings?\nRoute Density vs. CPP Gap  ·  Bubble size = Annual Savings",
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.2f'))
ax.set_xlim(112, 205)
ax.set_ylim(-0.05, 1.35)

# Bubble size legend (manual)
for sval, lbl in [(302364, '$302K'), (810087, '$810K'), (1598808, '$1.6M')]:
    sz = 200 + 2000 * ((sval - min_s) / (max_s - min_s))
    ax.scatter([], [], s=sz, color='#AAAAAA', alpha=0.6, edgecolors=NAVY, label=f'{lbl} saved/yr')

ax.legend(fontsize=8.5, loc='upper right', framealpha=0.92,
          title='Annual Savings', title_fontsize=9,
          markerscale=0.9)

plt.savefig(os.path.join(OUT_DIR, 'chart2_density_driver.png'),
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Chart 2 saved.")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3: Scatter — Daily Volume vs Annual Savings ("Two Paths")
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 9))
fig.patch.set_facecolor('white')
ax.set_facecolor(LGREY)
ax.grid(True, color='white', linewidth=1.4, zorder=0)
plt.subplots_adjust(left=0.10, right=0.90, top=0.88, bottom=0.10)

vol_vals  = [f['vol']     for f in facilities]
sav_vals2 = [f['savings'] for f in facilities]
gap_vals2 = [f['gap']     for f in facilities]
names2    = [f['name']    for f in facilities]

pt_sizes  = [180 + 1400 * (g / max(gap_vals2)) for g in gap_vals2]
colors2   = [g / max(gap_vals2) for g in gap_vals2]

sc = ax.scatter(vol_vals, sav_vals2, s=pt_sizes,
                c=colors2, cmap='RdYlGn_r',
                alpha=0.85, edgecolors=NAVY, linewidths=1.5, zorder=4)

cbar = plt.colorbar(sc, ax=ax, shrink=0.55, pad=0.02)
cbar.set_label('CPP Gap (relative to Toledo max $1.15)', fontsize=9, color=NAVY)
cbar.ax.tick_params(labelsize=8)

# Labels — manually positioned
lbl_cfg = {
    'Dallas':      (+14,  +10, 'left'),
    'Atlanta':     (+14,  +10, 'left'),
    'Northern NJ': (-14,  +12, 'right'),
    'Pittsburgh':  (+14,  +10, 'left'),   # right side, above Petaluma
    'Petaluma':    (-14,  -22, 'right'),  # left side, below Pittsburgh
    'Boise':       (-14,  +12, 'right'),
    'Detroit':     (+14,  +10, 'left'),
    'Denver':      (+14,  -22, 'left'),
    'Toledo':      (+14,  +10, 'left'),
    'Tucson':      (+14,  -22, 'left'),
    'Miami':       (+14,  +10, 'left'),
    'Buckeye':     (-14,  -22, 'right'),
}
for name, vol, sav, gap in zip(names2, vol_vals, sav_vals2, gap_vals2):
    ox, oy, ha = lbl_cfg.get(name, (12, 8, 'left'))
    ax.annotate(f'{name}  Δ${gap:.2f}',
                xy=(vol, sav), xytext=(ox, oy), textcoords='offset points',
                fontsize=9, fontweight='bold', color=NAVY, ha=ha,
                arrowprops=dict(arrowstyle='->', color=NAVY, lw=0.7))

# Quadrant dividers
med_vol = 15000
ax.axvline(x=med_vol, color='white', linestyle='--', linewidth=2, alpha=0.7, zorder=2)

# Quadrant labels — positioned well inside the plot
ax.text(med_vol + 1000, 1.52e6,
        'HIGH VOLUME PATH\nModerate CPP gap × big volume\n= large total savings\n(Dallas, NNJ, Atlanta)',
        fontsize=9, color='#1F4E79', style='italic', alpha=0.85,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6))

ax.text(500, 1.52e6,
        'HIGH GAP PATH\nSmall volume, large CPP gap\n= meaningful per-unit win\n(Toledo, Boise, Pittsburgh)',
        fontsize=9, color='#7F0000', style='italic', alpha=0.85,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6))

ax.set_xlabel('Daily Average Package Volume  (packages/day)', fontsize=11, color=NAVY, labelpad=8)
ax.set_ylabel('Annual Savings ($)', fontsize=11, color=NAVY, labelpad=8)
ax.set_title("Two Paths to RBS Savings\nHigh Volume (modest CPP gap)  vs.  High CPP Gap (low volume)"
             "  ·  Point size = CPP gap magnitude",
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.1f}M'))
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.set_xlim(-1000, 38000)
ax.set_ylim(0, 2.0e6)

# Total callout
ax.text(0.99, 0.01, f'12 Facilities\nTotal: ${TOTAL_SAV:,.0f}',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=10, fontweight='bold',
        color='white', bbox=dict(boxstyle='round,pad=0.5', facecolor=NAVY, alpha=0.92))

plt.savefig(os.path.join(OUT_DIR, 'chart3_volume_vs_savings.png'),
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Chart 3 saved.")
print("Done.")
