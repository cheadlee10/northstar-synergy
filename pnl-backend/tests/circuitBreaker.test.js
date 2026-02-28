const { CircuitBreaker } = require('../lib/circuitBreaker');

describe('CircuitBreaker', () => {
  let breaker;

  beforeEach(() => {
    breaker = new CircuitBreaker({
      failureThreshold: 3,
      resetTimeout: 1000,
      monitoringInterval: 500
    });
  });

  afterEach(() => {
    breaker.destroy();
  });

  describe('execute', () => {
    test('should execute function on success', async () => {
      const fn = jest.fn().mockResolvedValue('success');
      const result = await breaker.execute('test-service', fn);

      expect(result).toBe('success');
      expect(fn).toHaveBeenCalled();
    });

    test('should return fallback on error when provided', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('Failed'));
      const fallback = { cached: true };

      const result = await breaker.execute('test-service', fn, fallback);

      expect(result).toEqual(fallback);
    });

    test('should open circuit after threshold failures', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('Failed'));
      const fallback = { cached: true };

      // Trigger multiple failures
      for (let i = 0; i < 3; i++) {
        await breaker.execute('test-service', fn, fallback);
      }

      const service = breaker.getOrCreateService('test-service');
      expect(service.state).toBe('OPEN');
    });

    test('should use fallback when circuit is open', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('Failed'));
      const fallback = { cached: true };

      // Open the circuit
      for (let i = 0; i < 3; i++) {
        await breaker.execute('test-service', fn, fallback);
      }

      // Reset mock
      fn.mockClear();

      // Try to execute - should use fallback without calling fn
      const result = await breaker.execute('test-service', fn, fallback);

      expect(result).toEqual(fallback);
      expect(fn).not.toHaveBeenCalled();
    });

    test('should recover on half-open success', async () => {
      const fn = jest.fn()
        .mockRejectedValueOnce(new Error('Failed'))
        .mockRejectedValueOnce(new Error('Failed'))
        .mockRejectedValueOnce(new Error('Failed'))
        .mockResolvedValueOnce('success'); // Recovery

      const fallback = { cached: true };

      // Open the circuit
      for (let i = 0; i < 3; i++) {
        await breaker.execute('test-service', fn, fallback);
      }

      // Wait for reset timeout
      await new Promise(resolve => setTimeout(resolve, 1100));

      // Try again - should attempt execution (HALF_OPEN)
      const result = await breaker.execute('test-service', fn, fallback);

      expect(result).toBe('success');
      const service = breaker.getOrCreateService('test-service');
      expect(service.state).toBe('CLOSED');
    });
  });

  describe('reset', () => {
    test('should reset specific service', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('Failed'));

      // Open circuit
      for (let i = 0; i < 3; i++) {
        await breaker.execute('test-service', fn, {});
      }

      const service = breaker.getOrCreateService('test-service');
      expect(service.state).toBe('OPEN');

      // Reset
      breaker.reset('test-service');
      expect(service.state).toBe('CLOSED');
      expect(service.failureCount).toBe(0);
    });

    test('should reset all services', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('Failed'));

      // Open multiple circuits
      for (let i = 0; i < 3; i++) {
        await breaker.execute('service1', fn, {});
        await breaker.execute('service2', fn, {});
      }

      // Reset all
      breaker.reset();

      const service1 = breaker.getOrCreateService('service1');
      const service2 = breaker.getOrCreateService('service2');

      expect(service1.state).toBe('CLOSED');
      expect(service2.state).toBe('CLOSED');
    });
  });

  describe('getStatus', () => {
    test('should return circuit breaker status', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('Failed'));

      await breaker.execute('test-service', fn, {});

      const status = breaker.getStatus();

      expect(status.services).toBeDefined();
      expect(status.services['test-service']).toBeDefined();
      expect(status.services['test-service'].failureCount).toBe(1);
      expect(status.config).toBeDefined();
    });
  });
});
