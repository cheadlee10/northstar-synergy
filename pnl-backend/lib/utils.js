/**
 * Utility functions for P&L streaming backend
 */

/**
 * Normalize timestamp to ISO 8601 UTC format
 * @param {Date|string|number} timestamp - Input timestamp
 * @returns {string} - ISO 8601 UTC timestamp
 */
function normalizeTimestamp(timestamp) {
  let date;
  
  if (timestamp instanceof Date) {
    date = timestamp;
  } else if (typeof timestamp === 'string') {
    date = new Date(timestamp);
  } else if (typeof timestamp === 'number') {
    date = new Date(timestamp);
  } else {
    date = new Date();
  }

  // Validate
  if (isNaN(date.getTime())) {
    return new Date().toISOString();
  }

  return date.toISOString();
}

/**
 * Calculate gross margin percentage
 * @param {number} revenue - Total revenue
 * @param {number} expenses - Total expenses
 * @returns {number} - Gross margin percentage (0-100)
 */
function calculateGrossMargin(revenue, expenses) {
  if (revenue === 0) return 0;
  const margin = ((revenue - expenses) / revenue) * 100;
  return Math.round(margin * 100) / 100; // 2 decimal places
}

/**
 * Round to 2 decimal places (currency)
 * @param {number} value - Value to round
 * @returns {number} - Rounded value
 */
function roundCurrency(value) {
  return Math.round(value * 100) / 100;
}

/**
 * Merge objects deeply
 * @param {object} target - Target object
 * @param {object} source - Source object
 * @returns {object} - Merged object
 */
function deepMerge(target, source) {
  const result = { ...target };
  
  for (const key in source) {
    if (source.hasOwnProperty(key)) {
      if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
        result[key] = deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
  }
  
  return result;
}

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise}
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Validate API response structure
 * @param {object} response - Response object
 * @param {array} requiredFields - Required field paths (dot notation)
 * @returns {boolean} - True if valid
 */
function isValidResponse(response, requiredFields = []) {
  if (!response || typeof response !== 'object') {
    return false;
  }

  for (const field of requiredFields) {
    const value = field.split('.').reduce((obj, key) => obj?.[key], response);
    if (value === undefined || value === null) {
      return false;
    }
  }

  return true;
}

/**
 * Safe JSON parse with fallback
 * @param {string} json - JSON string
 * @param {object} fallback - Fallback object
 * @returns {object} - Parsed object or fallback
 */
function safeJsonParse(json, fallback = {}) {
  try {
    return JSON.parse(json);
  } catch (error) {
    return fallback;
  }
}

/**
 * Create a unique cache key
 * @param {string} namespace - Cache namespace
 * @param {string} key - Cache key
 * @returns {string} - Full cache key
 */
function createCacheKey(namespace, key) {
  return `${namespace}:${key}`;
}

/**
 * Get current UTC timestamp in milliseconds
 * @returns {number} - Current UTC timestamp
 */
function getCurrentTimestampMs() {
  return Date.now();
}

/**
 * Format number as currency string
 * @param {number} value - Value to format
 * @param {string} currency - Currency code (default: USD)
 * @returns {string} - Formatted currency string
 */
function formatCurrency(value, currency = 'USD') {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
  return formatter.format(value);
}

/**
 * Calculate percentage change
 * @param {number} oldValue - Original value
 * @param {number} newValue - New value
 * @returns {number} - Percentage change
 */
function calculatePercentageChange(oldValue, newValue) {
  if (oldValue === 0) return newValue > 0 ? 100 : 0;
  return roundCurrency(((newValue - oldValue) / Math.abs(oldValue)) * 100);
}

/**
 * Truncate string to max length
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated string
 */
function truncateString(str, maxLength = 100) {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
}

module.exports = {
  normalizeTimestamp,
  calculateGrossMargin,
  roundCurrency,
  deepMerge,
  sleep,
  isValidResponse,
  safeJsonParse,
  createCacheKey,
  getCurrentTimestampMs,
  formatCurrency,
  calculatePercentageChange,
  truncateString
};
