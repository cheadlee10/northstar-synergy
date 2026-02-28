/**
 * Unit Tests for P&L Utility Functions
 */

const {
  normalizeTimestamp,
  calculateGrossMargin,
  roundCurrency,
  deepMerge,
  isValidResponse,
  safeJsonParse,
  createCacheKey,
  formatCurrency,
  calculatePercentageChange,
  truncateString
} = require('../../lib/utils');

describe('Utils - P&L Calculations', () => {
  
  // ============================================================================
  // TIMESTAMP TESTS
  // ============================================================================

  describe('normalizeTimestamp', () => {
    test('should handle Date object', () => {
      const date = new Date('2024-01-15T10:30:00Z');
      const result = normalizeTimestamp(date);
      expect(result).toMatch(/^2024-01-15T10:30:00/);
      expect(result).toContain('Z');
    });

    test('should handle ISO string', () => {
      const isoString = '2024-01-15T10:30:00Z';
      const result = normalizeTimestamp(isoString);
      expect(result).toMatch(/^2024-01-15T10:30:00/);
    });

    test('should handle timestamp number (milliseconds)', () => {
      const timestamp = 1705318200000; // 2024-01-15T10:30:00Z
      const result = normalizeTimestamp(timestamp);
      expect(result).toMatch(/^2024-01-15T10:30:00/);
    });

    test('should return current time for invalid input', () => {
      const result = normalizeTimestamp('invalid');
      expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });
  });

  // ============================================================================
  // MARGIN CALCULATION TESTS
  // ============================================================================

  describe('calculateGrossMargin', () => {
    test('should calculate positive margin correctly', () => {
      // Revenue: $1000, Expenses: $400, Expected margin: 60%
      const result = calculateGrossMargin(1000, 400);
      expect(result).toBe(60);
    });

    test('should calculate negative margin correctly', () => {
      // Revenue: $400, Expenses: $1000, Expected margin: -150%
      const result = calculateGrossMargin(400, 1000);
      expect(result).toBe(-150);
    });

    test('should handle zero revenue', () => {
      const result = calculateGrossMargin(0, 500);
      expect(result).toBe(0);
    });

    test('should handle zero expenses', () => {
      // Revenue: $1000, Expenses: $0, Expected margin: 100%
      const result = calculateGrossMargin(1000, 0);
      expect(result).toBe(100);
    });

    test('should round to 2 decimal places', () => {
      // Revenue: $3, Expenses: $1, Expected: 66.67%
      const result = calculateGrossMargin(3, 1);
      expect(result).toBe(66.67);
    });

    test('should handle real P&L scenario', () => {
      // Real example: Revenue $50K, Expenses $15K = 70% margin
      const result = calculateGrossMargin(50000, 15000);
      expect(result).toBe(70);
    });
  });

  // ============================================================================
  // CURRENCY ROUNDING TESTS
  // ============================================================================

  describe('roundCurrency', () => {
    test('should round to 2 decimal places', () => {
      expect(roundCurrency(123.456)).toBe(123.46);
      expect(roundCurrency(123.454)).toBe(123.45);
    });

    test('should handle exact values', () => {
      expect(roundCurrency(123.45)).toBe(123.45);
      expect(roundCurrency(100)).toBe(100);
    });

    test('should handle small values', () => {
      expect(roundCurrency(0.001)).toBe(0);
      expect(roundCurrency(0.005)).toBe(0.01);
    });

    test('should handle negative values', () => {
      expect(roundCurrency(-123.456)).toBe(-123.46);
      expect(roundCurrency(-0.005)).toBe(-0.01);
    });

    test('should prevent floating point errors', () => {
      expect(roundCurrency(0.1 + 0.2)).toBe(0.3);
      expect(roundCurrency(0.3 + 0.3 + 0.3)).toBe(0.9);
    });
  });

  // ============================================================================
  // MERGE TESTS
  // ============================================================================

  describe('deepMerge', () => {
    test('should merge simple objects', () => {
      const target = { a: 1, b: 2 };
      const source = { b: 3, c: 4 };
      const result = deepMerge(target, source);
      
      expect(result).toEqual({ a: 1, b: 3, c: 4 });
    });

    test('should merge nested objects', () => {
      const target = { a: { x: 1, y: 2 } };
      const source = { a: { y: 3, z: 4 } };
      const result = deepMerge(target, source);
      
      expect(result).toEqual({ a: { x: 1, y: 3, z: 4 } });
    });

    test('should not mutate original objects', () => {
      const target = { a: 1 };
      const source = { b: 2 };
      const result = deepMerge(target, source);
      
      expect(target).toEqual({ a: 1 });
      expect(source).toEqual({ b: 2 });
    });

    test('should handle null and undefined in source', () => {
      const target = { a: 1, b: 2 };
      const source = { b: null, c: undefined };
      const result = deepMerge(target, source);
      
      expect(result.b).toBeNull();
      expect(result.c).toBeUndefined();
    });
  });

  // ============================================================================
  // VALIDATION TESTS
  // ============================================================================

  describe('isValidResponse', () => {
    test('should validate valid response', () => {
      const response = {
        success: true,
        data: { balance: 1000 }
      };
      const result = isValidResponse(response, ['success', 'data']);
      expect(result).toBe(true);
    });

    test('should validate nested field paths', () => {
      const response = {
        data: { user: { id: 123 } }
      };
      const result = isValidResponse(response, ['data.user.id']);
      expect(result).toBe(true);
    });

    test('should reject missing required fields', () => {
      const response = { success: true };
      const result = isValidResponse(response, ['success', 'data']);
      expect(result).toBe(false);
    });

    test('should reject invalid response', () => {
      expect(isValidResponse(null)).toBe(false);
      expect(isValidResponse(undefined)).toBe(false);
      expect(isValidResponse('string')).toBe(false);
    });
  });

  // ============================================================================
  // JSON PARSING TESTS
  // ============================================================================

  describe('safeJsonParse', () => {
    test('should parse valid JSON', () => {
      const result = safeJsonParse('{"a": 1, "b": 2}');
      expect(result).toEqual({ a: 1, b: 2 });
    });

    test('should return fallback for invalid JSON', () => {
      const fallback = { default: true };
      const result = safeJsonParse('invalid json', fallback);
      expect(result).toEqual(fallback);
    });

    test('should use empty object as default fallback', () => {
      const result = safeJsonParse('invalid');
      expect(result).toEqual({});
    });

    test('should parse arrays', () => {
      const result = safeJsonParse('[1, 2, 3]');
      expect(result).toEqual([1, 2, 3]);
    });
  });

  // ============================================================================
  // CACHE KEY TESTS
  // ============================================================================

  describe('createCacheKey', () => {
    test('should create namespaced cache key', () => {
      const result = createCacheKey('pnl', 'current');
      expect(result).toBe('pnl:current');
    });

    test('should handle complex keys', () => {
      const result = createCacheKey('kalshi', 'balance-20240115');
      expect(result).toBe('kalshi:balance-20240115');
    });
  });

  // ============================================================================
  // CURRENCY FORMATTING TESTS
  // ============================================================================

  describe('formatCurrency', () => {
    test('should format USD currency', () => {
      const result = formatCurrency(1234.56, 'USD');
      expect(result).toContain('1,234.56');
      expect(result).toContain('$');
    });

    test('should format with 2 decimal places', () => {
      const result = formatCurrency(100, 'USD');
      expect(result).toContain('100.00');
    });

    test('should handle negative values', () => {
      const result = formatCurrency(-500, 'USD');
      expect(result).toContain('-');
      expect(result).toContain('500');
    });

    test('should support different currencies', () => {
      const result = formatCurrency(1000, 'EUR');
      expect(result).toBeDefined();
    });
  });

  // ============================================================================
  // PERCENTAGE CHANGE TESTS
  // ============================================================================

  describe('calculatePercentageChange', () => {
    test('should calculate positive percentage change', () => {
      const result = calculatePercentageChange(100, 150);
      expect(result).toBe(50);
    });

    test('should calculate negative percentage change', () => {
      const result = calculatePercentageChange(100, 50);
      expect(result).toBe(-50);
    });

    test('should handle zero old value', () => {
      const result = calculatePercentageChange(0, 100);
      expect(result).toBe(100);
    });

    test('should round to 2 decimal places', () => {
      const result = calculatePercentageChange(100, 133.33);
      expect(result).toBe(33.33);
    });
  });

  // ============================================================================
  // STRING TRUNCATION TESTS
  // ============================================================================

  describe('truncateString', () => {
    test('should not truncate short strings', () => {
      const result = truncateString('hello', 10);
      expect(result).toBe('hello');
    });

    test('should truncate long strings', () => {
      const result = truncateString('hello world this is a long string', 10);
      expect(result).toBe('hello w...');
      expect(result.length).toBe(10);
    });

    test('should use default max length of 100', () => {
      const long = 'a'.repeat(150);
      const result = truncateString(long);
      expect(result.length).toBe(100);
      expect(result.endsWith('...')).toBe(true);
    });
  });
});
