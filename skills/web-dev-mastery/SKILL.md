# WEB DEVELOPMENT MASTERY SKILL

**Owner:** Cliff (learning from John's patterns)  
**Purpose:** Build enterprise-grade P&L dashboard  
**Quality Focus:** Reusable, testable, performant components  

---

## AREAS TO MASTER

### 1. React Component Architecture
- **Composability**: Small, single-purpose components
- **Reusability**: Props-based, configuration-driven
- **Testability**: Pure components (no side effects)
- **Performance**: Memoization, lazy loading
- **Patterns**: Container/Presentational, Hooks, Context

**Learning:** Request John's React component library patterns

### 2. State Management
- **Redux pattern**: Predictable, debuggable state
- **Context API**: Lightweight alternative for global state
- **Local state**: Component-level state (useState)
- **Side effects**: useEffect patterns, async operations
- **DevTools**: Redux DevTools for debugging

**Learning:** Request John's state architecture for complex dashboards

### 3. Data Visualization
- **D3.js**: Low-level, highly customizable
- **Plotly**: High-level, rapid development
- **Chart.js**: Simple, performant
- **Heatmaps**: Specialized for trading/finance
- **Real-time updates**: Streaming data to charts

**Learning:** Research D3 heatmap patterns for Scalper dashboard

### 4. Performance Optimization
- **Code splitting**: Load only needed components
- **Lazy loading**: Images, data, components
- **Memoization**: React.memo, useMemo, useCallback
- **Bundle optimization**: Webpack/Vite
- **Query optimization**: <300ms latency (Stripe's standard)

**Learning:** Request John's performance audit patterns

### 5. CSS & Layout
- **CSS Grid**: Multi-column financial dashboards
- **Flexbox**: Responsive, adaptive layouts
- **Tailwind CSS**: Utility-first (if John uses it)
- **Dark theme**: Financial dashboards prefer dark mode
- **Mobile responsive**: Touch-friendly, zoom-aware

**Learning:** Request John's CSS patterns for responsive layouts

### 6. TypeScript** (if applicable)
- **Strong typing**: Catch errors at compile time
- **Interfaces**: For API responses, props
- **Generics**: Reusable, type-safe components
- **Enums**: For status values (WIN/LOSS/PENDING)

**Learning:** Check if John uses TypeScript, request patterns

---

## REFERENCE PATTERNS (From Research)

### Bloomberg Terminal Style
```jsx
// Hierarchical drill-down component
<PortfolioView>
  <SummaryMetrics />          // Top-level aggregates
  <PositionTable 
    onRowClick={drillDown}    // Click → expand detail
  />
  <AttributionChart />        // Why did P&L change?
</PortfolioView>
```

### Stripe Billing Dashboard
```jsx
// Real-time metric with sub-300ms latency
<MetricCard
  value={MRR}
  loading={isUpdating}        // Show loading while query executes
  trend={weekOverWeek}        // Trend arrow
  drillDown={filterUI}        // Quick filter options
/>
```

### TradesViz Trading Journal
```jsx
// Heatmap with drill-down
<PnLCalendar
  data={dayByDayResults}
  colorScale={greenToRed}     // Green=profit, Red=loss
  onClick={(day) => showDayDetails(day)}
/>
```

---

## IMPLEMENTATION CHECKLIST

**Phase 1 (This week):**
- [ ] Learn John's React patterns
- [ ] Study D3 heatmap library (or Plotly alternative)
- [ ] Design component hierarchy for dashboard
- [ ] Setup Redux store structure (if using Redux)
- [ ] Document component patterns

**Phase 2 (Next week):**
- [ ] Build reusable dashboard components
- [ ] Implement real-time data binding
- [ ] Performance testing (<300ms latency)
- [ ] Mobile responsiveness

**Phase 3 (Ongoing):**
- [ ] Optimize slow queries
- [ ] Refine visualization clarity
- [ ] Improve accessibility (a11y)

---

## SUCCESS CRITERIA

✅ Components are reusable (no copy-paste)  
✅ Components are testable (pure functions where possible)  
✅ Dashboard renders in <1s (first paint)  
✅ Data updates in real-time (<300ms latency)  
✅ Mobile + desktop both performant  
✅ Code is readable and well-documented  
✅ New features can be added without refactoring core  

---

**Waiting for John's patterns. Proceeding with research-based learning.**
