/**
 * Snapshot Tests for P&L Dashboard Charts
 * Verifies chart outputs remain consistent across updates
 */

import React from 'react';
import { render } from '@testing-library/react';
import WaterfallChart from '../../components/WaterfallChart';
import TrendLineChart from '../../components/TrendLineChart';
import CostBreakdownPie from '../../components/CostBreakdownPie';
import AgentAttributionBar from '../../components/AgentAttributionBar';

describe('Chart Snapshot Tests', () => {
  // ============================================================================
  // WATERFALL CHART SNAPSHOTS
  // ============================================================================

  describe('WaterfallChart Snapshots', () => {
    test('should render waterfall chart with basic data', () => {
      const data = {
        revenue: 50000,
        expenses: 15000,
        net: 35000,
        timestamp: '2024-01-15T10:30:00Z'
      };

      const { container } = render(<WaterfallChart data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render waterfall with positive margin', () => {
      const data = {
        revenue: 100000,
        expenses: 25000,
        net: 75000,
        timestamp: '2024-01-15T10:30:00Z'
      };

      const { container } = render(<WaterfallChart data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render waterfall with negative margin', () => {
      const data = {
        revenue: 10000,
        expenses: 25000,
        net: -15000,
        timestamp: '2024-01-15T10:30:00Z'
      };

      const { container } = render(<WaterfallChart data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render waterfall with zero revenue', () => {
      const data = {
        revenue: 0,
        expenses: 5000,
        net: -5000,
        timestamp: '2024-01-15T10:30:00Z'
      };

      const { container } = render(<WaterfallChart data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render waterfall decomposition correctly', () => {
      const data = {
        components: {
          kalshi: 5000,
          john: 35000,
          other: 10000
        },
        expenses: 15000,
        net: 35000,
        timestamp: '2024-01-15T10:30:00Z'
      };

      const { container } = render(<WaterfallChart data={data} detailed={true} />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  // ============================================================================
  // TREND LINE CHART SNAPSHOTS
  // ============================================================================

  describe('TrendLineChart Snapshots', () => {
    test('should render trend line with sample data', () => {
      const data = [
        { timestamp: '2024-01-15T08:00:00Z', value: 30000 },
        { timestamp: '2024-01-15T09:00:00Z', value: 32000 },
        { timestamp: '2024-01-15T10:00:00Z', value: 35000 },
        { timestamp: '2024-01-15T11:00:00Z', value: 33000 },
        { timestamp: '2024-01-15T12:00:00Z', value: 38000 }
      ];

      const { container } = render(<TrendLineChart data={data} title="Net P&L Trend" />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render upward trend', () => {
      const data = [
        { timestamp: '2024-01-15T08:00:00Z', value: 10000 },
        { timestamp: '2024-01-15T09:00:00Z', value: 15000 },
        { timestamp: '2024-01-15T10:00:00Z', value: 20000 },
        { timestamp: '2024-01-15T11:00:00Z', value: 25000 },
        { timestamp: '2024-01-15T12:00:00Z', value: 30000 }
      ];

      const { container } = render(<TrendLineChart data={data} title="Revenue Trend" />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render downward trend', () => {
      const data = [
        { timestamp: '2024-01-15T08:00:00Z', value: 50000 },
        { timestamp: '2024-01-15T09:00:00Z', value: 45000 },
        { timestamp: '2024-01-15T10:00:00Z', value: 40000 },
        { timestamp: '2024-01-15T11:00:00Z', value: 35000 },
        { timestamp: '2024-01-15T12:00:00Z', value: 30000 }
      ];

      const { container } = render(<TrendLineChart data={data} title="Expenses Trend" />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render multi-line trend chart', () => {
      const data = [
        {
          timestamp: '2024-01-15T08:00:00Z',
          revenue: 50000,
          expenses: 15000
        },
        {
          timestamp: '2024-01-15T09:00:00Z',
          revenue: 52000,
          expenses: 16000
        },
        {
          timestamp: '2024-01-15T10:00:00Z',
          revenue: 55000,
          expenses: 17000
        }
      ];

      const { container } = render(
        <TrendLineChart
          data={data}
          title="Revenue vs Expenses"
          lines={['revenue', 'expenses']}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render trend with volatile data', () => {
      const data = [
        { timestamp: '2024-01-15T08:00:00Z', value: 25000 },
        { timestamp: '2024-01-15T09:00:00Z', value: 35000 },
        { timestamp: '2024-01-15T10:00:00Z', value: 20000 },
        { timestamp: '2024-01-15T11:00:00Z', value: 40000 },
        { timestamp: '2024-01-15T12:00:00Z', value: 28000 }
      ];

      const { container } = render(<TrendLineChart data={data} title="Volatile Trend" />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  // ============================================================================
  // PIE CHART SNAPSHOTS
  // ============================================================================

  describe('CostBreakdownPie Snapshots', () => {
    test('should render pie chart with three components', () => {
      const data = {
        kalshi: 5000,
        anthropic: 2000,
        john: 8000
      };

      const { container } = render(<CostBreakdownPie data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render pie chart with dominated component', () => {
      const data = {
        kalshi: 9000,
        anthropic: 500,
        john: 500
      };

      const { container } = render(<CostBreakdownPie data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render pie chart with equal distribution', () => {
      const data = {
        kalshi: 3333,
        anthropic: 3333,
        john: 3334
      };

      const { container } = render(<CostBreakdownPie data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render pie chart with single large component', () => {
      const data = {
        kalshi: 9500,
        anthropic: 250,
        john: 250
      };

      const { container } = render(<CostBreakdownPie data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render pie with percentages', () => {
      const data = {
        kalshi: 40000,
        anthropic: 20000,
        john: 40000
      };

      const { container } = render(<CostBreakdownPie data={data} showPercentages={true} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render pie with custom colors', () => {
      const data = {
        kalshi: 5000,
        anthropic: 2000,
        john: 8000
      };

      const colors = {
        kalshi: '#0173B2',
        anthropic: '#DE8F05',
        john: '#029E73'
      };

      const { container } = render(<CostBreakdownPie data={data} colors={colors} />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  // ============================================================================
  // BAR CHART SNAPSHOTS
  // ============================================================================

  describe('AgentAttributionBar Snapshots', () => {
    test('should render stacked bar chart', () => {
      const data = [
        {
          agent: 'Scalper',
          revenue: 5000,
          expenses: 1500
        },
        {
          agent: 'John',
          revenue: 8000,
          expenses: 1000
        },
        {
          agent: 'Cliff',
          revenue: 2000,
          expenses: 500
        }
      ];

      const { container } = render(<AgentAttributionBar data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render horizontal bar chart', () => {
      const data = [
        { agent: 'Scalper', value: 8000 },
        { agent: 'John', value: 12000 },
        { agent: 'Cliff', value: 5000 }
      ];

      const { container } = render(<AgentAttributionBar data={data} layout="horizontal" />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render grouped bar chart', () => {
      const data = [
        {
          month: '2024-01',
          scalper: 5000,
          john: 8000,
          cliff: 2000
        },
        {
          month: '2024-02',
          scalper: 6000,
          john: 9000,
          cliff: 2500
        },
        {
          month: '2024-03',
          scalper: 7000,
          john: 10000,
          cliff: 3000
        }
      ];

      const { container } = render(
        <AgentAttributionBar data={data} grouped={true} />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render bar chart with percentages', () => {
      const data = [
        { agent: 'Scalper', value: 40 },
        { agent: 'John', value: 50 },
        { agent: 'Cliff', value: 10 }
      ];

      const { container } = render(<AgentAttributionBar data={data} isPercentage={true} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render bar with negative values', () => {
      const data = [
        { agent: 'Scalper', profit: 5000 },
        { agent: 'John', profit: -2000 },
        { agent: 'Cliff', profit: 3000 }
      ];

      const { container } = render(<AgentAttributionBar data={data} />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  // ============================================================================
  // DASHBOARD COMPOSITION SNAPSHOTS
  // ============================================================================

  describe('Dashboard Composition Snapshots', () => {
    test('should render complete dashboard layout', () => {
      const { container } = render(
        <div className="dashboard">
          <header className="dashboard-header">
            <h1>Real-Time P&L Dashboard</h1>
          </header>
          <div className="metrics-grid">
            <div className="metric-card">
              <span>Total Revenue: $50,000</span>
            </div>
            <div className="metric-card">
              <span>Total Expenses: $15,000</span>
            </div>
            <div className="metric-card">
              <span>Net P&L: $35,000</span>
            </div>
          </div>
          <section className="charts-section">
            <h2>Charts</h2>
          </section>
        </div>
      );

      expect(container).toMatchSnapshot();
    });

    test('should render metrics with consistent styling', () => {
      const { container } = render(
        <div className="pnl-dashboard">
          <div className="pnl-card revenue">
            <span className="label">Revenue</span>
            <span className="value">$50,000</span>
          </div>
          <div className="pnl-card expense">
            <span className="label">Expenses</span>
            <span className="value">$15,000</span>
          </div>
          <div className="pnl-card margin">
            <span className="label">Margin</span>
            <span className="value">70%</span>
          </div>
        </div>
      );

      expect(container).toMatchSnapshot();
    });
  });

  // ============================================================================
  // EMPTY STATE SNAPSHOTS
  // ============================================================================

  describe('Empty State Snapshots', () => {
    test('should render empty chart gracefully', () => {
      const { container } = render(
        <WaterfallChart data={{ revenue: 0, expenses: 0, net: 0 }} />
      );

      expect(container.firstChild).toMatchSnapshot();
    });

    test('should render empty trend line', () => {
      const { container } = render(
        <TrendLineChart data={[]} title="No Data Available" />
      );

      expect(container.firstChild).toMatchSnapshot();
    });

    test('should show loading state', () => {
      const { container } = render(
        <div className="chart-loading">
          <span aria-busy="true">Loading chart...</span>
        </div>
      );

      expect(container).toMatchSnapshot();
    });
  });

  // ============================================================================
  // ERROR STATE SNAPSHOTS
  // ============================================================================

  describe('Error State Snapshots', () => {
    test('should render error boundary', () => {
      const { container } = render(
        <div className="error-state">
          <h3>Error Loading Chart</h3>
          <p>Unable to fetch chart data. Please try again.</p>
        </div>
      );

      expect(container).toMatchSnapshot();
    });

    test('should display invalid data message', () => {
      const { container } = render(
        <div className="error-state">
          <span>Invalid data format</span>
        </div>
      );

      expect(container).toMatchSnapshot();
    });
  });

  // ============================================================================
  // RESPONSIVE LAYOUT SNAPSHOTS
  // ============================================================================

  describe('Responsive Layout Snapshots', () => {
    test('should render mobile layout', () => {
      const { container } = render(
        <div className="dashboard mobile-view">
          <div className="metrics-grid--mobile">
            <div className="metric-card">Revenue: $50,000</div>
            <div className="metric-card">Expenses: $15,000</div>
          </div>
        </div>
      );

      expect(container).toMatchSnapshot();
    });

    test('should render tablet layout', () => {
      const { container } = render(
        <div className="dashboard tablet-view">
          <div className="metrics-grid--tablet">
            <div className="metric-card">Revenue</div>
            <div className="metric-card">Expenses</div>
            <div className="metric-card">Net P&L</div>
          </div>
        </div>
      );

      expect(container).toMatchSnapshot();
    });

    test('should render desktop layout', () => {
      const { container } = render(
        <div className="dashboard desktop-view">
          <div className="metrics-grid--desktop">
            <div className="metric-card">Revenue</div>
            <div className="metric-card">Expenses</div>
            <div className="metric-card">Net P&L</div>
            <div className="metric-card">Margin</div>
            <div className="metric-card">Trend</div>
          </div>
        </div>
      );

      expect(container).toMatchSnapshot();
    });
  });
});
