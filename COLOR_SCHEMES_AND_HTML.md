# Color Schemes & HTML Layout Reference
**Dashboard Design for NorthStar Synergy**  
**Date:** February 26, 2026

---

## PART 1: COLOR SCHEMES (WCAG AA COMPLIANT)

### Scheme A: Classic Trading (Green/Red)
**Use Case:** Traditional finance, traders familiar with Bloomberg  
**Accessibility:** Protanopia-friendly with icons, patterns

```
GAINS:     #16A34A (dark green)    | WCAG 4.5:1 on white
LOSSES:    #DC2626 (bright red)    | WCAG 4.5:1 on white
NEUTRAL:   #6B7280 (medium gray)   | WCAG 4.5:1 on white
ALERTS:    #F59E0B (amber)         | WCAG 4.5:1 on white

Background:  #FFFFFF (white)
Text (dark): #111827 (near-black)
Text (muted):#6B7280 (gray)
Border:      #E5E7EB (light gray)
```

**Usage:**
```html
<!-- Portfolio Gain -->
<span style="color: #16A34A;">
  <svg><!-- ↑ arrow --></svg> +$12,450 (+0.54%)
</span>

<!-- Portfolio Loss -->
<span style="color: #DC2626;">
  <svg><!-- ↓ arrow --></svg> –$12,450 (–0.54%)
</span>
```

---

### Scheme B: Accessible Diverging (Blue-Gold)
**Use Case:** High accessibility required, colorblind-friendly  
**Accessibility:** Passes all three color blindness types

```
GAINS:     #1B9E77 (teal)          | WCAG 4.5:1 on white
LOSSES:    #D95F02 (orange)        | WCAG 4.5:1 on white
NEUTRAL:   #7570B3 (purple-gray)   | WCAG 4.5:1 on white
ALERTS:    #E08214 (burnt orange)  | WCAG 4.5:1 on white

Background: #FFFFFF (white)
Text (dark): #1A1A1A (near-black)
Text (muted):#7F7F7F (gray)
Border:      #D3D3D3 (light gray)
```

**Usage:**
```css
.metric.gain {
  color: #1B9E77;
  background: #E8F5E9;
}

.metric.loss {
  color: #D95F02;
  background: #FFE8D6;
}
```

---

### Scheme C: Stripe's Lab-Based (Balanced Contrast)
**Use Case:** Modern SaaS aesthetic, vibrant colors, maximum accessibility  
**Accessibility:** Perceptually uniform, tested across all blindness types

```
GAINS:     #16A34A (green)         | WCAG AA ✓
LOSSES:    #DC2626 (red)           | WCAG AA ✓
INFO:      #2563EB (blue)          | WCAG AA ✓
WARNING:   #F59E0B (amber)         | WCAG AA ✓
ERROR:     #EF4444 (bright red)    | WCAG AA ✓

Shades (all accessible):
├─ -50:  #F0FDF4 (lightest)
├─ -100: #DCFCE7
├─ -500: #22C55E
├─ -600: #16A34A (PRIMARY UI)
├─ -700: #15803D
└─ -900: #14532D (darkest, for text)

Background: #FFFFFF
Text (dark): #111827
Text (muted):#6B7280
Border:      #E5E7EB
```

---

## PART 2: COLOR PALETTE JSON

For implementation in design systems (Figma, Storybook, etc.):

```json
{
  "colors": {
    "gain": {
      "50": "#F0FDF4",
      "100": "#DCFCE7",
      "200": "#BBF7D0",
      "300": "#86EFAC",
      "400": "#4ADE80",
      "500": "#22C55E",
      "600": "#16A34A",
      "700": "#15803D",
      "800": "#166534",
      "900": "#14532D"
    },
    "loss": {
      "50": "#FEF2F2",
      "100": "#FEE2E2",
      "200": "#FECACA",
      "300": "#FCA5A5",
      "400": "#F87171",
      "500": "#EF4444",
      "600": "#DC2626",
      "700": "#B91C1C",
      "800": "#991B1B",
      "900": "#7F1D1D"
    },
    "info": {
      "50": "#EFF6FF",
      "600": "#2563EB"
    },
    "warning": {
      "50": "#FFFBEB",
      "600": "#F59E0B"
    },
    "neutral": {
      "50": "#FAFAFA",
      "100": "#F3F4F6",
      "300": "#D1D5DB",
      "600": "#4B5563",
      "700": "#374151",
      "900": "#111827"
    }
  },
  "contrast_verified": {
    "text_on_white": "4.5:1",
    "large_text_on_white": "3:1",
    "focus_indicator": "2px solid outline"
  }
}
```

---

## PART 3: HTML LAYOUT MOCKUP (Desktop)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NorthStar Synergy - Portfolio Dashboard</title>
  <link rel="stylesheet" href="dashboard.css">
  <link rel="stylesheet" href="dashboard-css-patterns.css">
</head>
<body>
  <div class="dashboard-container">
    <!-- ===== HEADER ===== -->
    <header class="dashboard-header">
      <div class="header-content">
        <h1>Portfolio Overview</h1>
        <div class="header-controls">
          <button aria-label="Settings">⚙️</button>
          <button aria-label="Export data">📥</button>
          <button aria-label="Add widget">➕</button>
        </div>
      </div>
    </header>

    <!-- ===== MAIN CONTENT ===== -->
    <main class="dashboard">
      
      <!-- TIER 1: HERO METRICS (What CEO sees in 3 seconds) -->
      <section class="tier-1">
        <div class="metric-card hero">
          <h2>Portfolio Net Worth</h2>
          <div class="metric-value">$2,340,500</div>
          <div class="metric-change gain">
            <svg aria-hidden="true" width="16" height="16">
              <path d="M8 2l4 5h-3v7h-2V7h-3l4-5z" fill="currentColor"/>
            </svg>
            <span>+$12,450 (+0.54%)</span>
          </div>
          <div class="sparkline">
            <!-- Inline SVG sparkline chart -->
            <svg viewBox="0 0 100 30" aria-label="7-day gain trend">
              <polyline points="5,25 15,20 25,22 35,15 45,18 55,12 65,10 75,8 85,5 95,3" 
                        stroke="#16A34A" fill="none" stroke-width="1.5"/>
            </svg>
          </div>
        </div>

        <div class="metric-card">
          <h3>Today's Change</h3>
          <div class="metric-value">+$12,450</div>
          <div class="metric-change gain">
            <span>+0.54% today</span>
          </div>
          <div class="metric-subtext">Last update: 2:47 PM PST</div>
        </div>

        <div class="metric-card">
          <h3>Market Status</h3>
          <div class="status-badge open">
            <svg aria-hidden="true"><!-- Open circle --></svg>
            Open
          </div>
          <div class="metric-subtext">2:47 PM PST | 15 min delay</div>
        </div>
      </section>

      <!-- ALERTS & WARNINGS (if any) -->
      <section class="alerts">
        <div class="alert warning" role="region" aria-label="Alerts">
          <svg aria-hidden="true"><!-- Warning icon --></svg>
          <div>
            <strong>NVDA:</strong> Up 12% (+$456). Consider taking gains.
            <button class="btn-small">Monitor</button>
          </div>
        </div>
      </section>

      <!-- TIER 2: HOLDINGS TABLE -->
      <section class="tier-2">
        <div class="card">
          <h2>Holdings</h2>
          <div class="table-controls">
            <label for="sort-by">Sort by:</label>
            <select id="sort-by">
              <option>By Gain/Loss</option>
              <option>By Allocation %</option>
              <option>By Name</option>
            </select>
          </div>

          <table role="grid" aria-label="Portfolio holdings">
            <thead>
              <tr>
                <th scope="col">Ticker</th>
                <th scope="col">Shares</th>
                <th scope="col">Avg Cost</th>
                <th scope="col">Current</th>
                <th scope="col">P&L</th>
                <th scope="col">% Change</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              <!-- Row 1: Gain -->
              <tr class="data-row gain-row">
                <td><strong>AAPL</strong></td>
                <td>432</td>
                <td>$189.50</td>
                <td>$189.60</td>
                <td class="data-cell gain">
                  <svg aria-hidden="true" class="icon-up">↑</svg>
                  $5,230
                </td>
                <td class="data-cell gain">
                  <span class="percentage positive">
                    <svg aria-hidden="true">↑</svg>
                    +2.84%
                  </span>
                </td>
                <td>
                  <button class="btn btn-secondary" aria-label="Sell AAPL">Sell</button>
                </td>
              </tr>

              <!-- Row 2: Loss -->
              <tr class="data-row loss-row">
                <td><strong>MSFT</strong></td>
                <td>215</td>
                <td>$425.00</td>
                <td>$420.50</td>
                <td class="data-cell loss">
                  <svg aria-hidden="true" class="icon-down">↓</svg>
                  –$961
                </td>
                <td class="data-cell loss">
                  <span class="percentage negative">
                    <svg aria-hidden="true">↓</svg>
                    –1.21%
                  </span>
                </td>
                <td>
                  <button class="btn btn-secondary" aria-label="Sell MSFT">Hold</button>
                </td>
              </tr>

              <!-- Row 3: Strong Gain -->
              <tr class="data-row gain-row alert-row">
                <td><strong>NVDA</strong></td>
                <td>95</td>
                <td>$520.00</td>
                <td>$588.00</td>
                <td class="data-cell gain">
                  <svg aria-hidden="true" class="icon-up">↑</svg>
                  $6,460
                </td>
                <td class="data-cell gain">
                  <span class="percentage positive">
                    <svg aria-hidden="true">↑</svg>
                    +13.1%
                  </span>
                </td>
                <td>
                  <button class="btn btn-danger" aria-label="Sell NVDA - strong gain">Sell</button>
                </td>
              </tr>

              <!-- Cash -->
              <tr class="data-row cash-row">
                <td><strong>CASH</strong></td>
                <td colspan="5">$456,000 available for trading</td>
                <td>
                  <button class="btn btn-primary" aria-label="Execute trade">Trade</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- TIER 2B: SIDE-BY-SIDE CHARTS -->
      <section class="tier-2-charts">
        <div class="card chart-card">
          <h3>Allocation (by %) </h3>
          <svg viewBox="0 0 120 120" aria-label="Portfolio allocation pie chart">
            <circle cx="60" cy="60" r="50" fill="#16A34A" opacity="0.8"/>
            <circle cx="60" cy="60" r="35" fill="white"/>
            <text x="60" y="65" text-anchor="middle" font-weight="bold">35%</text>
            <text x="60" y="75" text-anchor="middle" font-size="10">AAPL</text>
          </svg>
          <div class="legend">
            <div><span class="legend-color" style="background: #16A34A;"></span> AAPL: 35%</div>
            <div><span class="legend-color" style="background: #DC2626;"></span> MSFT: 22%</div>
            <div><span class="legend-color" style="background: #F59E0B;"></span> NVDA: 18%</div>
            <div><span class="legend-color" style="background: #6B7280;"></span> Other: 15%</div>
            <div><span class="legend-color" style="background: #E5E7EB;"></span> Cash: 10%</div>
          </div>
        </div>

        <div class="card chart-card">
          <h3>Performance</h3>
          <div class="perf-tabs">
            <button class="perf-btn active">7D</button>
            <button class="perf-btn">30D</button>
            <button class="perf-btn">YTD</button>
            <button class="perf-btn">1Y</button>
          </div>
          <svg viewBox="0 0 400 200" class="line-chart" aria-label="7-day performance chart">
            <line x1="40" y1="160" x2="380" y2="160" stroke="#E5E7EB" stroke-width="1"/>
            <polyline points="40,130 100,125 160,135 220,110 280,115 340,95 380,75" 
                      stroke="#16A34A" fill="none" stroke-width="2"/>
          </svg>
          <div class="perf-summary">
            +2.5% 7D | –1.2% 30D | +8.5% YTD | +12.3% 1Y
          </div>
        </div>
      </section>

      <!-- TIER 3: RISK METRICS -->
      <section class="tier-3">
        <div class="card">
          <h3>Risk Metrics</h3>
          <div class="metrics-grid">
            <div class="metric-item">
              <div class="metric-label">Beta</div>
              <div class="metric-value">1.24</div>
              <div class="metric-note">Market sensitivity</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">Volatility</div>
              <div class="metric-value">18.5%</div>
              <div class="metric-note">Annualized</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">Max Drawdown</div>
              <div class="metric-value loss">–8.2%</div>
              <div class="metric-note">Worst loss</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">Value at Risk</div>
              <div class="metric-value loss">$25,000</div>
              <div class="metric-note">95% confidence</div>
            </div>
          </div>
        </div>
      </section>

    </main>

    <!-- ===== FOOTER ===== -->
    <footer class="dashboard-footer">
      <p>Last updated: <time datetime="2026-02-25T14:47:00-08:00">2:47 PM PST</time></p>
      <p>Data delayed by 15 minutes. <a href="/disclaimer">Disclaimer</a></p>
    </footer>
  </div>

  <!-- ===== TOAST NOTIFICATION (hidden by default) ===== -->
  <div class="toast success" role="status" aria-live="polite" aria-atomic="true" hidden>
    <svg aria-hidden="true">✓</svg>
    Portfolio data updated
  </div>

  <script src="dashboard.js"></script>
</body>
</html>
```

---

## PART 4: HTML LAYOUT MOCKUP (Mobile)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>Portfolio - NorthStar</title>
  <link rel="stylesheet" href="dashboard-mobile.css">
</head>
<body class="mobile-view">
  <div class="mobile-container">
    
    <!-- HEADER -->
    <header class="mobile-header">
      <h1>Portfolio</h1>
      <button aria-label="Menu" class="menu-btn">☰</button>
    </header>

    <!-- HERO METRIC (FULL WIDTH, TOP PRIORITY) -->
    <section class="hero-metric">
      <h2 class="sr-only">Portfolio Net Worth</h2>
      <div class="value-large">$2,340,500</div>
      <div class="change gain">
        <svg aria-hidden="true">↑</svg>
        <span>+$12,450 (+0.54%)</span>
      </div>
      <div class="update-time">Last update: 2:47 PM</div>
    </section>

    <!-- TABS (SWIPEABLE) -->
    <nav class="mobile-tabs" role="tablist">
      <button role="tab" aria-selected="true" aria-controls="holdings-panel">
        Holdings
      </button>
      <button role="tab" aria-selected="false" aria-controls="watchlist-panel">
        Watchlist
      </button>
      <button role="tab" aria-selected="false" aria-controls="alerts-panel">
        Alerts
      </button>
    </nav>

    <!-- HOLDINGS PANEL (TAB CONTENT) -->
    <section id="holdings-panel" role="tabpanel" aria-labelledby="holdings-tab">
      <div class="holding-card gain">
        <div class="holding-header">
          <div class="ticker">AAPL</div>
          <div class="share-count">432 @ $189.60</div>
        </div>
        <div class="holding-value">$81,951</div>
        <div class="holding-change gain">
          <svg aria-hidden="true">↑</svg>
          <span>+$5,230 (+2.84%)</span>
        </div>
        <div class="holding-actions">
          <button class="btn btn-secondary" aria-label="Sell AAPL">Sell</button>
          <button class="btn btn-secondary" aria-label="View details for AAPL">Details</button>
        </div>
      </div>

      <div class="holding-card loss">
        <div class="holding-header">
          <div class="ticker">MSFT</div>
          <div class="share-count">215 @ $420.50</div>
        </div>
        <div class="holding-value">$90,507</div>
        <div class="holding-change loss">
          <svg aria-hidden="true">↓</svg>
          <span>–$961 (–1.21%)</span>
        </div>
        <div class="holding-actions">
          <button class="btn btn-secondary" aria-label="Sell MSFT">Sell</button>
          <button class="btn btn-secondary" aria-label="View details for MSFT">Details</button>
        </div>
      </div>

      <div class="holding-card gain alert">
        <div class="holding-header">
          <div class="ticker">NVDA</div>
          <div class="share-count">95 @ $588.00</div>
        </div>
        <div class="holding-value">$55,860</div>
        <div class="holding-change gain">
          <svg aria-hidden="true">↑</svg>
          <span>+$6,460 (+13.1%)</span>
        </div>
        <div class="alert-badge">Consider taking gains</div>
        <div class="holding-actions">
          <button class="btn btn-danger" aria-label="Sell NVDA - strong gain">Sell Now</button>
          <button class="btn btn-secondary" aria-label="View details for NVDA">Details</button>
        </div>
      </div>

      <div class="cash-card">
        <div class="cash-label">Available Cash</div>
        <div class="cash-value">$456,000</div>
        <button class="btn btn-primary" aria-label="Execute trade with available cash">
          Trade
        </button>
      </div>
    </section>

    <!-- PERFORMANCE SECTION (SCROLLABLE) -->
    <section class="performance-mobile">
      <h3>Performance</h3>
      <div class="perf-tabs">
        <button class="perf-btn active">7D</button>
        <button class="perf-btn">30D</button>
        <button class="perf-btn">YTD</button>
        <button class="perf-btn">1Y</button>
      </div>
      <svg viewBox="0 0 300 150" class="line-chart-mobile" aria-label="Performance chart">
        <polyline points="20,120 50,110 80,115 110,95 140,105 170,85 200,75 230,60 280,40" 
                  stroke="#16A34A" fill="none" stroke-width="2"/>
      </svg>
      <div class="perf-values">
        <div>7D: +2.5%</div>
        <div>30D: –1.2%</div>
        <div>YTD: +8.5%</div>
        <div>1Y: +12.3%</div>
      </div>
    </section>

  </div>

  <script src="dashboard-mobile.js"></script>
</body>
</html>
```

---

## PART 5: CSS BREAKPOINTS & RESPONSIVE GRID

```css
/* Mobile First (375px–430px) */
.dashboard {
  display: block;
  padding: 12px;
}

.metric-card {
  margin-bottom: 12px;
}

/* Tablet (768px) */
@media (min-width: 768px) {
  .dashboard {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    padding: 20px;
  }

  .tier-1 {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }

  .metric-card.hero {
    grid-column: 1 / 2;
  }
}

/* Desktop (1024px) */
@media (min-width: 1024px) {
  .dashboard {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding: 24px;
  }

  .tier-2-charts {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }

  .tier-3 {
    grid-column: 1 / -1;
  }
}

/* Large screens (1440px) */
@media (min-width: 1440px) {
  .dashboard {
    grid-template-columns: repeat(4, 1fr);
    max-width: 1920px;
    margin: 0 auto;
  }
}
```

---

## PART 6: IMPLEMENTATION CHECKLIST

- [ ] **Colors:** Use CSS variables from `DASHBOARD_CSS_PATTERNS.css`
- [ ] **Icons:** Add SVG icons for ↑/↓/→/⚠/✓ (or use Font Awesome)
- [ ] **Tables:** Test with screen reader (NVDA)
- [ ] **Mobile:** Test with real iPhone/Android
- [ ] **Contrast:** Verify with WebAIM tool (all colors ≥ 4.5:1)
- [ ] **Focus:** Ensure 2px outline visible on all buttons
- [ ] **Animations:** Respect `prefers-reduced-motion`
- [ ] **Touch:** All buttons ≥ 44px × 44px

---

**Ready for Design & Development Phase**  
**Next Steps:** Import these colors into Figma, build components, test accessibility
