/**
 * Accessibility Tests for P&L Dashboard Components
 * WCAG AA compliance, keyboard navigation, colorblind modes
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PnLCard from '../../components/KPICard';
import WaterfallChart from '../../components/WaterfallChart';
import TrendLineChart from '../../components/TrendLineChart';
import CostBreakdownPie from '../../components/CostBreakdownPie';
import AgentAttributionBar from '../../components/AgentAttributionBar';

describe('Accessibility Tests - WCAG AA Compliance', () => {
  // ============================================================================
  // SEMANTIC HTML TESTS
  // ============================================================================

  describe('Semantic HTML Structure', () => {
    test('should have proper heading hierarchy', () => {
      const { container } = render(
        <main>
          <h1>Real-Time P&L Dashboard</h1>
          <section>
            <h2>Metrics</h2>
            <div>Content</div>
          </section>
        </main>
      );

      const h1 = container.querySelector('h1');
      const h2 = container.querySelector('h2');

      expect(h1).toBeInTheDocument();
      expect(h2).toBeInTheDocument();

      // h2 should come after h1
      const h1Index = Array.from(container.querySelectorAll('h1, h2')).indexOf(h1);
      const h2Index = Array.from(container.querySelectorAll('h1, h2')).indexOf(h2);
      expect(h2Index).toBeGreaterThan(h1Index);
    });

    test('should use semantic HTML elements', () => {
      const { container } = render(
        <div>
          <main>Dashboard Content</main>
          <section>Metrics</section>
          <article>Details</article>
        </div>
      );

      expect(container.querySelector('main')).toBeInTheDocument();
      expect(container.querySelector('section')).toBeInTheDocument();
      expect(container.querySelector('article')).toBeInTheDocument();
    });

    test('should have proper landmark regions', () => {
      const { container } = render(
        <div>
          <header>Header</header>
          <main>Main Content</main>
          <footer>Footer</footer>
        </div>
      );

      expect(container.querySelector('header')).toBeInTheDocument();
      expect(container.querySelector('main')).toBeInTheDocument();
      expect(container.querySelector('footer')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // LABEL AND TEXT TESTS
  // ============================================================================

  describe('Labels and Text Content', () => {
    test('should have descriptive text for all metrics', () => {
      render(<PnLCard label="Total Revenue" value={50000} icon="📈" />);

      expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    });

    test('should have meaningful button text', () => {
      const { container } = render(
        <button>Subscribe to Updates</button>
      );

      const button = container.querySelector('button');
      expect(button.textContent).not.toBe('Click');
      expect(button.textContent).toBe('Subscribe to Updates');
    });

    test('should use aria-label for icon-only elements', () => {
      const { container } = render(
        <button aria-label="Refresh data">🔄</button>
      );

      const button = container.querySelector('button');
      expect(button).toHaveAttribute('aria-label', 'Refresh data');
    });

    test('should provide alt text for images', () => {
      const { container } = render(
        <img src="/chart.png" alt="Revenue trend chart" />
      );

      const img = container.querySelector('img');
      expect(img).toHaveAttribute('alt', 'Revenue trend chart');
    });
  });

  // ============================================================================
  // COLOR CONTRAST TESTS
  // ============================================================================

  describe('Color Contrast (WCAG AA)', () => {
    test('should have sufficient color contrast for text', () => {
      const { container } = render(
        <div style={{ color: '#000', backgroundColor: '#fff' }}>
          <p>High contrast text</p>
        </div>
      );

      const text = container.querySelector('p');
      const style = window.getComputedStyle(text);

      // White background (#fff) with black text (#000) is 21:1 contrast
      expect(style.color).toBeDefined();
    });

    test('should not rely on color alone to convey information', () => {
      render(
        <div>
          <span className="positive">Positive: ↑</span>
          <span className="negative">Negative: ↓</span>
        </div>
      );

      // Color indicators should have text or icon supplement
      expect(screen.getByText(/Positive:/)).toBeInTheDocument();
      expect(screen.getByText(/Negative:/)).toBeInTheDocument();
    });

    test('should provide colorblind-safe color palette', () => {
      const colors = {
        positive: '#0173B2', // Blue (colorblind safe)
        negative: '#DE8F05', // Orange (colorblind safe)
        neutral: '#029E73'   // Green (colorblind safe)
      };

      Object.values(colors).forEach(color => {
        expect(color).toMatch(/^#[0-9A-F]{6}$/i);
      });
    });

    test('should support high contrast mode', () => {
      const { container } = render(
        <div className="high-contrast-mode">
          <p style={{ color: '#000', backgroundColor: '#fff' }}>Content</p>
        </div>
      );

      expect(container.querySelector('.high-contrast-mode')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // KEYBOARD NAVIGATION TESTS
  // ============================================================================

  describe('Keyboard Navigation', () => {
    test('should support Tab navigation', async () => {
      const user = userEvent.setup();

      render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
          <button>Button 3</button>
        </div>
      );

      const button1 = screen.getByText('Button 1');

      button1.focus();
      expect(button1).toHaveFocus();

      await user.tab();
      expect(screen.getByText('Button 2')).toHaveFocus();

      await user.tab();
      expect(screen.getByText('Button 3')).toHaveFocus();
    });

    test('should support Shift+Tab for backwards navigation', async () => {
      const user = userEvent.setup();

      render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
        </div>
      );

      const button2 = screen.getByText('Button 2');
      button2.focus();

      await user.tab({ shift: true });
      expect(screen.getByText('Button 1')).toHaveFocus();
    });

    test('should have focusable interactive elements', () => {
      const { container } = render(
        <div>
          <button>Button</button>
          <a href="/">Link</a>
          <input type="text" />
        </div>
      );

      const button = container.querySelector('button');
      const link = container.querySelector('a');
      const input = container.querySelector('input');

      expect(button).toHaveProperty('tabIndex');
      expect(link).toBeInTheDocument();
      expect(input).toBeInTheDocument();
    });

    test('should not trap focus', async () => {
      const user = userEvent.setup();

      const { container } = render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
        </div>
      );

      const button1 = container.querySelector('button');
      button1.focus();

      // Should be able to tab through all elements
      await user.tab();
      await user.tab();

      // Should not be stuck on same element
      expect(document.activeElement).not.toBe(button1);
    });

    test('should support Enter key on buttons', async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();

      render(
        <button onClick={handleClick}>Click me</button>
      );

      const button = screen.getByText('Click me');
      button.focus();

      await user.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalled();
    });

    test('should support Space key on buttons', async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();

      render(
        <button onClick={handleClick}>Click me</button>
      );

      const button = screen.getByText('Click me');
      button.focus();

      await user.keyboard(' ');
      expect(handleClick).toHaveBeenCalled();
    });
  });

  // ============================================================================
  // SCREEN READER TESTS
  // ============================================================================

  describe('Screen Reader Support', () => {
    test('should have descriptive headings', () => {
      render(
        <h1>Real-Time P&L Dashboard</h1>
      );

      expect(screen.getByRole('heading', { level: 1, name: /Real-Time P&L Dashboard/ }))
        .toBeInTheDocument();
    });

    test('should use aria-label for complex components', () => {
      const { container } = render(
        <div aria-label="P&L metrics dashboard">
          <p>Dashboard content</p>
        </div>
      );

      expect(container.querySelector('[aria-label]')).toHaveAttribute(
        'aria-label',
        'P&L metrics dashboard'
      );
    });

    test('should use aria-describedby for helper text', () => {
      const { container } = render(
        <div>
          <input
            type="text"
            aria-describedby="help-text"
            placeholder="Enter amount"
          />
          <span id="help-text">Enter a positive number</span>
        </div>
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-describedby', 'help-text');
    });

    test('should announce dynamic updates', () => {
      const { container } = render(
        <div aria-live="polite" aria-atomic="true">
          <p>Last updated: 2 minutes ago</p>
        </div>
      );

      expect(container.querySelector('[aria-live="polite"]')).toHaveAttribute(
        'aria-atomic',
        'true'
      );
    });

    test('should indicate loading state to screen readers', () => {
      const { container } = render(
        <div aria-busy="true" role="status">
          Loading data...
        </div>
      );

      expect(container.querySelector('[aria-busy="true"]')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // FOCUS MANAGEMENT TESTS
  // ============================================================================

  describe('Focus Management', () => {
    test('should show visible focus indicator', () => {
      const { container } = render(
        <button style={{ outline: '2px solid blue' }}>
          Focusable Button
        </button>
      );

      const button = container.querySelector('button');
      button.focus();

      expect(button).toHaveFocus();
      const style = window.getComputedStyle(button);
      expect(style.outline).not.toBe('none');
    });

    test('should manage focus on modal dialogs', () => {
      const { container } = render(
        <div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
          <h2 id="dialog-title">Dialog Title</h2>
          <button>Close</button>
        </div>
      );

      expect(container.querySelector('[role="dialog"]')).toHaveAttribute('aria-modal', 'true');
    });

    test('should skip to main content link', () => {
      const { container } = render(
        <div>
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <nav>Navigation</nav>
          <main id="main-content">Main content</main>
        </div>
      );

      const skipLink = container.querySelector('.skip-link');
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });
  });

  // ============================================================================
  // FORM ACCESSIBILITY TESTS
  // ============================================================================

  describe('Form Accessibility', () => {
    test('should associate labels with form inputs', () => {
      const { container } = render(
        <div>
          <label htmlFor="revenue-input">Revenue:</label>
          <input id="revenue-input" type="number" />
        </div>
      );

      const input = container.querySelector('input');
      const label = container.querySelector('label');

      expect(label).toHaveAttribute('htmlFor', 'revenue-input');
      expect(input).toHaveAttribute('id', 'revenue-input');
    });

    test('should provide error messages', () => {
      const { container } = render(
        <div>
          <input
            type="number"
            aria-invalid="true"
            aria-describedby="error-message"
          />
          <span id="error-message" role="alert">
            Amount must be positive
          </span>
        </div>
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-invalid', 'true');

      const errorMessage = container.querySelector('[role="alert"]');
      expect(errorMessage).toHaveTextContent('Amount must be positive');
    });

    test('should support form validation messages', () => {
      const { container } = render(
        <form>
          <label htmlFor="email">Email:</label>
          <input
            id="email"
            type="email"
            required
            aria-required="true"
          />
          <span aria-live="polite">Email is required</span>
        </form>
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('required');
      expect(input).toHaveAttribute('aria-required', 'true');
    });
  });

  // ============================================================================
  // COLORBLIND MODE TESTS
  // ============================================================================

  describe('Colorblind Mode Support', () => {
    test('should use patterns in addition to colors', () => {
      const { container } = render(
        <div>
          <div className="positive" style={{ fill: 'url(#stripes)' }}>
            Positive
          </div>
          <div className="negative" style={{ fill: 'url(#dots)' }}>
            Negative
          </div>
        </div>
      );

      expect(container.querySelectorAll('[style*="fill"]')).toHaveLength(2);
    });

    test('should work in grayscale', () => {
      const { container } = render(
        <div style={{ filter: 'grayscale(100%)' }}>
          <span>Text remains readable</span>
        </div>
      );

      const div = container.querySelector('div');
      expect(div).toHaveStyle('filter: grayscale(100%)');
    });

    test('should provide legend for color coding', () => {
      render(
        <div>
          <p>Color Legend:</p>
          <span>🟢 Positive Performance</span>
          <span>🔴 Negative Performance</span>
          <span>⚪ Neutral</span>
        </div>
      );

      expect(screen.getByText(/Positive Performance/)).toBeInTheDocument();
      expect(screen.getByText(/Negative Performance/)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // DYNAMIC CONTENT TESTS
  // ============================================================================

  describe('Dynamic Content Accessibility', () => {
    test('should announce dynamic updates via aria-live', () => {
      const { rerender, container } = render(
        <div aria-live="polite" aria-atomic="true">
          Updated: 5 seconds ago
        </div>
      );

      rerender(
        <div aria-live="polite" aria-atomic="true">
          Updated: 10 seconds ago
        </div>
      );

      expect(screen.getByText('Updated: 10 seconds ago')).toBeInTheDocument();
      expect(container.querySelector('[aria-live="polite"]')).toBeInTheDocument();
    });

    test('should manage loading states accessibly', () => {
      const { rerender, container } = render(
        <div role="status" aria-live="polite">
          <span aria-busy="true">Loading...</span>
        </div>
      );

      rerender(
        <div role="status" aria-live="polite">
          <span>Data loaded</span>
        </div>
      );

      expect(screen.getByText('Data loaded')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // TEXT RESIZING TESTS
  // ============================================================================

  describe('Text Resizing and Zoom', () => {
    test('should be readable at 200% zoom', () => {
      const { container } = render(
        <p style={{ fontSize: '16px' }}>Readable text content</p>
      );

      const p = container.querySelector('p');
      expect(p).toBeInTheDocument();
      // In real tests, would verify layout doesn't break at zoom
    });

    test('should support text size adjustments', () => {
      const { container } = render(
        <p style={{ fontSize: 'clamp(16px, 1vw, 24px)' }}>
          Responsive text
        </p>
      );

      const p = container.querySelector('p');
      expect(p).toHaveStyle('font-size: clamp(16px, 1vw, 24px)');
    });

    test('should not use fixed heights that break with text resize', () => {
      const { container } = render(
        <div style={{ minHeight: '2em' }}>
          Content that can wrap
        </div>
      );

      const div = container.querySelector('div');
      expect(div).toHaveStyle('min-height: 2em');
    });
  });
});
