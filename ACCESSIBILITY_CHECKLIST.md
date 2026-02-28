# Accessibility Checklist for Enterprise Financial Dashboard
**Date Created:** February 26, 2026  
**Purpose:** Ensure dashboard meets WCAG 2.1 Level AA standards  
**Status:** Pre-implementation template

---

## QUICK REFERENCE

| Category | Standard | Target |
|----------|----------|--------|
| Color Contrast | WCAG 2.1 AA | 4.5:1 (text), 3:1 (large) |
| Mobile | Touch targets | 44px × 44px minimum |
| Keyboard | Tab navigation | All interactive elements |
| Screen Readers | Semantic HTML | Proper ARIA labels |
| Motion | User preference | Respect `prefers-reduced-motion` |

---

## 1. COLOR & CONTRAST

### Contrast Ratios
- [ ] **Text color on background**: ≥ 4.5:1 (small text < 18pt)
- [ ] **Large text**: ≥ 3:1 (18pt+, bold or 14pt bold)
- [ ] **UI components** (borders, icons): ≥ 3:1 minimum
- [ ] **Focus indicators**: Visible, ≥ 3:1 contrast

**Testing Tools:**
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Chrome DevTools: Right-click element → Inspect → Computed → Check contrast
- Figma plugin: Color Blindness Simulator

**Evidence to collect:**
- [ ] Screenshot of WebAIM results for each color pair
- [ ] Contrast ratio spreadsheet (colors used in dashboard)

---

### Color Usage (Never Color Alone)

- [ ] **Gains** paired with: ✓ Icon (↑), text label ("Gain"), badge
- [ ] **Losses** paired with: ✗ Icon (↓), text label ("Loss"), badge
- [ ] **Alerts** paired with: ⚠ Icon, text label ("Alert"), border
- [ ] **Neutral** paired with: → Icon, text label, or status indicator

**Bad Example:**
```html
<!-- ❌ Color alone is not accessible -->
<span style="color: green;">+5%</span>

<!-- ✅ Good example -->
<span class="badge gain">
  <svg aria-hidden="true"><!-- Up arrow --></svg>
  Gain: +5%
</span>
```

**Colorblind Testing:**
- [ ] Tested with Chrome DevTools emulation (Protanopia, Deuteranopia, Tritanopia)
- [ ] Tested with Colorblindly browser extension
- [ ] Tested with ColorBrewer2 or Leonardo tool

---

## 2. KEYBOARD NAVIGATION

### Tab Order & Focus

- [ ] **All interactive elements are keyboard accessible** (buttons, links, inputs)
- [ ] **Tab order is logical**: left-to-right, top-to-bottom
- [ ] **Focus indicator is visible**: outline or other clear visual signal
  - Minimum: 2px outline, 2px offset
  - Test: Press Tab, see focus highlight on each element
- [ ] **No focus trap**: User can tab out of any modal/widget
- [ ] **Skip links present** (if applicable): Jump to main content

**Test Method:**
```bash
# Keyboard navigation test
1. Load dashboard
2. Press Tab 10+ times
3. Observe focus indicator
4. Try Escape to close modals
5. Verify all controls are reachable
```

**Common Issues:**
- [ ] Buttons styled but focus hidden
- [ ] Floating modals trap focus
- [ ] Links without tabindex can't be reached

---

## 3. SCREEN READERS (Semantic HTML + ARIA)

### Basic Structure
- [ ] **Headings hierarchical**: h1 → h2 → h3 (no skips)
- [ ] **Page title meaningful**: Not just "Dashboard"
- [ ] **Landmarks used**: `<header>`, `<main>`, `<nav>`, `<footer>`
- [ ] **Lists semantic**: `<ul>`, `<ol>`, not `<div>` with role="list"

**Test Command (VoiceOver on Mac):**
```bash
# Enable VoiceOver
Cmd + F5

# Navigate headings
VO + U  # Open rotor
Select "Headings"
```

### Form Accessibility
- [ ] **Every input has explicit label**: `<label for="inputId">`
  - Not placeholder-only
  - Label text describes input purpose
- [ ] **Required fields marked**: 
  - Visually (asterisk)
  - HTML: `<input required aria-required="true">`
- [ ] **Error messages linked**:
  ```html
  <input aria-describedby="error-msg" />
  <div id="error-msg" role="alert">Amount must be > 0</div>
  ```
- [ ] **Hint text associated**:
  ```html
  <label for="password">Password</label>
  <input id="password" aria-describedby="hint" />
  <div id="hint">Minimum 8 characters</div>
  ```

### Images & Icons
- [ ] **All images have alt text**
  ```html
  <!-- ✓ Decorative icon: hidden -->
  <svg aria-hidden="true">...</svg>
  
  <!-- ✓ Chart: meaningful description -->
  <img alt="Portfolio gain of $12,450 (+0.54%) in the last 24 hours" src="..." />
  
  <!-- ✓ Icon-only button: labeled -->
  <button aria-label="Download report"><svg>...</svg></button>
  ```
- [ ] **Charts include data summary**:
  ```html
  <svg>
    <title>Portfolio Performance (7D/30D/YTD)</title>
    <desc>+2.5% gain over 7 days, -1.2% over 30 days, +8.5% YTD</desc>
  </svg>
  <!-- Or include data table -->
  <table>
    <caption>Performance Metrics</caption>
    <!-- rows -->
  </table>
  ```
- [ ] **No image text conveying meaning**
  ```html
  <!-- ✗ Bad: text in image -->
  <img src="revenue-chart.png" alt="" />
  
  <!-- ✓ Good: text + alt -->
  <img src="revenue-chart.png" alt="Revenue: $1.2M (↑12%)" />
  <table>...</table>
  ```

### Tables
- [ ] **Proper table structure**:
  ```html
  <table>
    <caption>Holdings Summary</caption>
    <thead>
      <tr>
        <th scope="col">Ticker</th>
        <th scope="col">Shares</th>
        <th scope="col">P&L</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>AAPL</td>
        <td>432</td>
        <td>+$5,230</td>
      </tr>
    </tbody>
  </table>
  ```
- [ ] **Data table headers scoped**: `<th scope="col">` or `scope="row"`
- [ ] **Complex tables have summary**: `<table summary="...">`

### Links & Buttons
- [ ] **Link text descriptive**: Not "Click here" or "More"
  ```html
  <!-- ✗ Bad -->
  <a href="/reports">Click here</a> to download
  
  <!-- ✓ Good -->
  <a href="/reports">Download Q4 Performance Report</a>
  ```
- [ ] **Button purpose clear**: `aria-label` if icon-only
  ```html
  <button aria-label="Export portfolio as CSV">
    <svg><!-- download icon --></svg>
  </button>
  ```

### Custom Components
- [ ] **Dropdowns/selects have role**: `role="listbox"`, `role="option"`
- [ ] **Modals trapped focus**: Focus returns to trigger on close
- [ ] **Live regions used for updates**: `aria-live="polite"` for alerts
  ```html
  <div aria-live="polite" aria-atomic="true">
    Portfolio updated: +$250 (new data)
  </div>
  ```

**Screen Reader Testing (Free Tools):**
- NVDA (Windows): [nvaccess.org](https://www.nvaccess.org/)
- JAWS (commercial)
- VoiceOver (Mac/iOS): Built-in (Cmd+F5)
- TalkBack (Android): Built-in

---

## 4. MOBILE & TOUCH

### Viewport & Touch Targets
- [ ] **Viewport meta tag set**:
  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  ```
- [ ] **Touch targets ≥ 44px × 44px** (Apple, Google standard)
  - Test: Try clicking on buttons with thumb on phone
- [ ] **Text zoom not disabled**: `maximum-scale` ≥ 2
  ```html
  <!-- ✓ Good -->
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  
  <!-- ✗ Bad -->
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  ```
- [ ] **No horizontal scroll at 200% zoom**
- [ ] **Floating elements don't cover content** (no sticky headers blocking main area)

### Mobile Layout
- [ ] **Content reflows at narrow viewports** (< 480px)
- [ ] **Columns stack vertically** (not 3-column grid on phone)
- [ ] **Tables don't require horizontal scroll**
  - Option 1: Stack key columns
  - Option 2: Make table horizontally scrollable with scroll indicator
  - Option 3: Convert to card layout on mobile
- [ ] **Form fields full-width** on mobile (easier to tap)

**Test Device Sizes:**
- [ ] iPhone SE (375px)
- [ ] iPhone 14 (430px)
- [ ] Samsung Galaxy A (360px)
- [ ] iPad (768px)
- [ ] Desktop (1440px+)

**Browser Testing:**
- [ ] Chrome DevTools: Device Toolbar (Cmd+Shift+M)
- [ ] Firefox Responsive Design Mode (Cmd+Shift+M)
- [ ] Real devices (physical testing recommended)

---

## 5. ANIMATIONS & MOTION

### Motion Preferences
- [ ] **Respect `prefers-reduced-motion`**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
  ```
- [ ] **No autoplay animations** (especially video/sound)
- [ ] **No rapid flashing**: < 3 flashes per second (seizure risk)

**Test Method:**
- [ ] Open System Preferences → Accessibility → Display
- [ ] Enable "Reduce motion"
- [ ] Reload dashboard
- [ ] Verify animations are minimal/disabled

### Animation Guidelines
- [ ] **Animations have purpose**: Feedback, not distraction
- [ ] **Animation duration** 150–300ms (feels responsive)
- [ ] **Easing functions**: ease-out or ease-in-out (not linear)
- [ ] **No surprise movements**: Animations on user actions only

**Good Animation Examples:**
- ✓ Button hover: 200ms scale + color transition
- ✓ Alert toast slide-in: 300ms from top
- ✓ Loading skeleton shimmer: 2s infinite (subtle)
- ✗ Auto-scrolling content
- ✗ Blinking text (unless intentional alert)
- ✗ Parallax that triggers motion sickness

---

## 6. COLOR BLINDNESS SIMULATION

### Manual Testing Steps

1. **Chrome DevTools Method:**
   - Right-click dashboard → Inspect
   - Open DevTools → Rendering tab
   - Scroll to "Emulate CSS media feature prefers-color-scheme"
   - Select: Protanopia (Red-blind), Deuteranopia (Green-blind), Tritanopia (Blue-yellow)
   - Verify dashboard is still usable

2. **Colorblindly Extension:**
   - Install: [Colorblindly Chrome Extension](https://chrome.google.com/webstore)
   - Click icon → Select color blindness type
   - Verify all charts, status badges, tables are readable

3. **Manual Checklist:**
   - [ ] Red/Green pair: Use distinct shades or patterns
   - [ ] Blue/Yellow pair: Avoid together (rare but important)
   - [ ] Gain (green) vs. Loss (red): Add icons (↑ vs. ↓)
   - [ ] Alerts: Use orange + warning icon, not red alone
   - [ ] Charts: Use ColorBrewer2 "Safe" palette for production

**Example Accessible Color Pair:**
```css
/* ✓ Protanopia-safe (red-blind) */
--gain: #008B8B;   /* Dark cyan */
--loss: #FFB6C1;   /* Light pink */

/* ✓ Deuteranopia-safe (green-blind) */
--gain: #FFB6C1;   /* Light pink → gains */
--loss: #0000CD;   /* Blue → losses */

/* ✓ Universal (all types) */
--gain: #1B9E77;   /* Teal */
--loss: #D95F02;   /* Orange */
```

---

## 7. PERFORMANCE (Accessibility Impact)

- [ ] **First Contentful Paint < 3s** (faster = more accessible)
- [ ] **Lighthouse Accessibility score ≥ 90**
  ```bash
  # Run Lighthouse in Chrome DevTools
  Lighthouse tab → Accessibility → Run audit
  ```
- [ ] **No console errors blocking rendering**

**Lighthouse Accessibility Checks:**
- [ ] Background and foreground colors have sufficient contrast
- [ ] Document has a valid heading structure
- [ ] Buttons and links have an accessible name
- [ ] Images have alt text
- [ ] Form inputs have labels

---

## 8. TESTING CHECKLIST (Pre-Launch)

### Automated Testing
- [ ] **axe DevTools** (Chrome extension)
  - Install: [axe DevTools](https://www.deque.com/axe/devtools/)
  - Run on each page of dashboard
  - Fix all critical/serious issues
- [ ] **Lighthouse** in Chrome DevTools
  - Target: Accessibility score ≥ 90
- [ ] **WAVE** (WebAIM)
  - Install: [WAVE Extension](https://wave.webaim.org/extension/)
  - Check for errors and warnings

### Manual Testing
- [ ] **Keyboard-only navigation** (unplug mouse, test with Tab/Enter)
- [ ] **Screen reader testing** (NVDA or VoiceOver, 15+ min)
- [ ] **Colorblind simulation** (Chrome emulation + Colorblindly)
- [ ] **Mobile touch testing** (real iPhone/Android device)
- [ ] **Zoom testing** (browser zoom to 200%, verify layout)
- [ ] **Browser testing**:
  - [ ] Chrome
  - [ ] Firefox
  - [ ] Safari
  - [ ] Edge

### User Testing
- [ ] **Test with colorblind user** (if possible)
- [ ] **Test with power user (CEO)** for information hierarchy
- [ ] **Test with non-technical user** (understandable labels?)

---

## 9. DOCUMENTATION

### Files to Create/Update
- [ ] `ACCESSIBILITY_STATEMENT.md` (public-facing)
- [ ] `A11Y_TEST_RESULTS.md` (internal tracking)
- [ ] Accessibility scores spreadsheet (track over time)

### Accessibility Statement Template
```markdown
# Accessibility Statement

NorthStar Synergy is committed to ensuring digital accessibility to all users.

## Compliance
- Dashboard meets WCAG 2.1 Level AA standards
- Color contrast: 4.5:1 for text (AA standard)
- All interactive elements keyboard accessible
- Screen reader compatible (NVDA, JAWS, VoiceOver tested)

## Known Issues & Workarounds
- Charts may require table alternative on screen readers
- Mobile layout optimized for iOS 15+ and Android 12+

## Testing Tools Used
- axe DevTools, Lighthouse, WAVE
- Chrome emulation (Protanopia, Deuteranopia, Tritanopia)
- Screen readers: NVDA, VoiceOver

## Report Issues
Email: accessibility@northstarsynergy.com
```

---

## 10. ONGOING MAINTENANCE

### Monthly Checks
- [ ] Re-run Lighthouse audit
- [ ] Test new features with axe DevTools
- [ ] Update color system if palette changes

### Quarterly Deep Dive
- [ ] Screen reader re-test (NVDA or VoiceOver)
- [ ] Mobile device re-test (new OS versions)
- [ ] Colorblind re-test (Colorblindly extension)

### When Making Changes
- [ ] Test modified component with axe first
- [ ] Test keyboard navigation on modified areas
- [ ] Test mobile layout if responsive breakpoint changed
- [ ] Update alt text if images change

---

## RESOURCES

| Resource | Link | Purpose |
|----------|------|---------|
| WCAG 2.1 Spec | [w3.org/WAI/WCAG21/](https://www.w3.org/WAI/WCAG21/) | Official standard |
| WebAIM | [webaim.org](https://webaim.org/) | Best practices + tools |
| axe DevTools | [deque.com/axe/devtools/](https://www.deque.com/axe/devtools/) | Automated testing |
| ColorBrewer2 | [colorbrewer2.org](https://colorbrewer2.org/) | Accessible palettes |
| Lighthouse | Built into Chrome | Performance + A11y |
| NVDA | [nvaccess.org](https://www.nvaccess.org/) | Free screen reader |
| Colorblindly | [Chrome Store](https://chrome.google.com/webstore) | Color blindness sim |

---

## SIGN-OFF

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | TBD | — | — |
| QA/Tester | TBD | — | — |
| Accessibility Lead | TBD | — | — |
| CEO Approval | Craig | — | — |

---

**Document Version:** 1.0  
**Last Updated:** February 26, 2026  
**Next Review:** [Date TBD]
