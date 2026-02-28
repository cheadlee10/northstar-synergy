/**
 * Data Transformation Layer
 * Utilities for normalizing timestamps, formatting currency, and data validation
 */

/**
 * Format currency value to USD string
 * @param {number} value - Amount in dollars
 * @param {Object} options - Formatting options
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (value, options = {}) => {
  const {
    locale = 'en-US',
    currency = 'USD',
    minimumFractionDigits = 0,
    maximumFractionDigits = 2,
  } = options;

  if (typeof value !== 'number' || isNaN(value)) {
    return '$0.00';
  }

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(value);
};

/**
 * Parse currency string back to number
 * @param {string} currencyStr - Currency formatted string (e.g., "$1,234.56")
 * @returns {number} Numeric value
 */
export const parseCurrency = (currencyStr) => {
  if (typeof currencyStr !== 'string') return 0;
  // Remove currency symbols, commas, and whitespace
  const cleaned = currencyStr.replace(/[$,\s]/g, '');
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
};

/**
 * Normalize timestamp to ISO string or Date object
 * Handles multiple input formats:
 * - ISO strings: "2026-02-25T22:30:00Z"
 * - Unix timestamps: 1740527400000
 * - Date objects
 * - Null/undefined (returns current time)
 *
 * @param {string|number|Date|null} timestamp - Raw timestamp
 * @param {string} format - 'iso' or 'date' (default: 'iso')
 * @returns {string|Date} Normalized timestamp
 */
export const normalizeTimestamp = (timestamp, format = 'iso') => {
  let date;

  if (!timestamp) {
    date = new Date();
  } else if (typeof timestamp === 'string') {
    date = new Date(timestamp);
  } else if (typeof timestamp === 'number') {
    // Could be milliseconds or seconds
    date = new Date(timestamp > 10000000000 ? timestamp : timestamp * 1000);
  } else if (timestamp instanceof Date) {
    date = timestamp;
  } else {
    date = new Date();
  }

  // Validate the date
  if (isNaN(date.getTime())) {
    console.warn('[normalizeTimestamp] Invalid date:', timestamp);
    date = new Date();
  }

  return format === 'iso' ? date.toISOString() : date;
};

/**
 * Format date for display
 * @param {string|number|Date} timestamp - Raw timestamp
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export const formatDate = (
  timestamp,
  options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }
) => {
  const date = normalizeTimestamp(timestamp, 'date');
  return new Intl.DateTimeFormat('en-US', options).format(date);
};

/**
 * Calculate percentage with safe handling
 * @param {number} numerator - Numerator value
 * @param {number} denominator - Denominator value
 * @param {number} decimalPlaces - Decimal places to round to
 * @returns {number} Percentage value
 */
export const calculatePercentage = (numerator, denominator, decimalPlaces = 2) => {
  if (!denominator || denominator === 0) return 0;
  const percentage = (numerator / denominator) * 100;
  return Math.round(percentage * Math.pow(10, decimalPlaces)) / Math.pow(10, decimalPlaces);
};

/**
 * Normalize P&L data from backend
 * Ensures all required fields exist with correct types
 *
 * @param {Object} rawData - Raw P&L data from backend
 * @returns {Object} Normalized P&L data
 */
export const normalizePnLData = (rawData = {}) => {
  const {
    revenue = 0,
    expenses = 0,
    net = revenue - expenses,
    margin_percent = calculatePercentage(net, revenue),
    updated_at = new Date().toISOString(),
  } = rawData;

  return {
    revenue: Number(revenue) || 0,
    expenses: Number(expenses) || 0,
    net: Number(net) || 0,
    margin_percent: Number(margin_percent) || 0,
    updated_at: normalizeTimestamp(updated_at),
  };
};

/**
 * Normalize trends data array
 * @param {Array} trendPoints - Array of trend data points
 * @returns {Object} Normalized trends object with arrays
 */
export const normalizeTrendsData = (trendPoints = []) => {
  const revenue = [];
  const expenses = [];
  const net = [];
  const dates = [];

  trendPoints.forEach((point) => {
    const normalized = normalizePnLData(point);
    revenue.push(normalized.revenue);
    expenses.push(normalized.expenses);
    net.push(normalized.net);
    dates.push(normalized.updated_at);
  });

  return { revenue, expenses, net, dates };
};

/**
 * Validate P&L data structure
 * @param {Object} data - Data to validate
 * @returns {Object} { isValid: boolean, errors: string[] }
 */
export const validatePnLData = (data) => {
  const errors = [];

  if (!data || typeof data !== 'object') {
    errors.push('Data must be an object');
    return { isValid: false, errors };
  }

  // Revenue validation
  if (data.revenue !== undefined) {
    if (typeof data.revenue !== 'number' || isNaN(data.revenue)) {
      errors.push('Revenue must be a valid number');
    }
    if (data.revenue < 0) {
      errors.push('Revenue cannot be negative');
    }
  }

  // Expenses validation
  if (data.expenses !== undefined) {
    if (typeof data.expenses !== 'number' || isNaN(data.expenses)) {
      errors.push('Expenses must be a valid number');
    }
    if (data.expenses < 0) {
      errors.push('Expenses cannot be negative');
    }
  }

  // Margin validation
  if (data.margin_percent !== undefined) {
    if (typeof data.margin_percent !== 'number' || isNaN(data.margin_percent)) {
      errors.push('Margin percent must be a valid number');
    }
    if (data.margin_percent < -100 || data.margin_percent > 100) {
      errors.push('Margin percent must be between -100 and 100');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Compare two P&L snapshots and return deltas
 * Useful for change detection and analytics
 *
 * @param {Object} current - Current P&L state
 * @param {Object} previous - Previous P&L state
 * @returns {Object} Delta values
 */
export const calculatePnLDeltas = (current, previous) => {
  const revenueChange = current.revenue - (previous?.revenue || 0);
  const expensesChange = current.expenses - (previous?.expenses || 0);
  const netChange = current.net - (previous?.net || 0);
  const marginChange = current.marginPercent - (previous?.marginPercent || 0);

  return {
    revenueChange,
    revenueChangePercent: calculatePercentage(revenueChange, previous?.revenue || 1),
    expensesChange,
    expensesChangePercent: calculatePercentage(expensesChange, previous?.expenses || 1),
    netChange,
    netChangePercent: calculatePercentage(netChange, previous?.net || 1),
    marginChange,
  };
};

/**
 * Generate mock P&L data for testing/development
 * Creates realistic trend data
 *
 * @param {Object} options - Configuration
 * @returns {Object} Mock P&L data with trends
 */
export const generateMockPnL = (options = {}) => {
  const {
    baseRevenue = 50000,
    baseExpenses = 30000,
    trendPoints = 30,
    volatility = 0.1,
  } = options;

  const trends = [];
  let currentRevenue = baseRevenue;
  let currentExpenses = baseExpenses;

  const now = new Date();

  for (let i = trendPoints - 1; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 24 * 60 * 60 * 1000); // Days back

    // Add random volatility
    const revenueVariation = currentRevenue * (1 + (Math.random() - 0.5) * volatility);
    const expensesVariation = currentExpenses * (1 + (Math.random() - 0.5) * volatility);

    trends.push({
      revenue: Math.max(0, revenueVariation),
      expenses: Math.max(0, expensesVariation),
      net: Math.max(0, revenueVariation) - Math.max(0, expensesVariation),
      timestamp: timestamp.toISOString(),
    });

    currentRevenue = Math.max(0, revenueVariation);
    currentExpenses = Math.max(0, expensesVariation);
  }

  const latestTrend = trends[trends.length - 1];

  return {
    current: {
      revenue: latestTrend.revenue,
      expenses: latestTrend.expenses,
      net: latestTrend.net,
      margin_percent: calculatePercentage(latestTrend.net, latestTrend.revenue),
      updated_at: latestTrend.timestamp,
    },
    trends: normalizeTrendsData(trends),
  };
};

/**
 * Aggregate P&L data (sum, average) for period comparisons
 *
 * @param {Array} dataPoints - Array of P&L data points
 * @param {string} aggregation - 'sum' or 'average'
 * @returns {Object} Aggregated P&L
 */
export const aggregatePnL = (dataPoints = [], aggregation = 'sum') => {
  if (!dataPoints.length) {
    return { revenue: 0, expenses: 0, net: 0, margin_percent: 0 };
  }

  const count = dataPoints.length;
  const totals = dataPoints.reduce(
    (acc, point) => ({
      revenue: acc.revenue + (point.revenue || 0),
      expenses: acc.expenses + (point.expenses || 0),
      net: acc.net + (point.net || 0),
    }),
    { revenue: 0, expenses: 0, net: 0 }
  );

  if (aggregation === 'average') {
    return {
      revenue: totals.revenue / count,
      expenses: totals.expenses / count,
      net: totals.net / count,
      margin_percent: calculatePercentage(totals.net / count, totals.revenue / count),
    };
  }

  return {
    revenue: totals.revenue,
    expenses: totals.expenses,
    net: totals.net,
    margin_percent: calculatePercentage(totals.net, totals.revenue),
  };
};
