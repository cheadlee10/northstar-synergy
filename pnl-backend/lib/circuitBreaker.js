const logger = require('./logger');

/**
 * Circuit Breaker Pattern for handling external API failures
 * States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing) -> CLOSED
 */
class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5; // failures before opening
    this.resetTimeout = options.resetTimeout || 60000; // 60 seconds
    this.monitoringInterval = options.monitoringInterval || 5000;
    
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = null;
    this.nextAttemptTime = null;
    
    // Track per-service circuit breakers
    this.services = new Map();
    
    this.startMonitoring();
  }

  /**
   * Execute function with circuit breaker protection
   */
  async execute(serviceName, fn, fallback = null) {
    const service = this.getOrCreateService(serviceName);
    
    // Check if circuit is open
    if (service.state === 'OPEN') {
      if (Date.now() < service.nextAttemptTime) {
        logger.warn(`Circuit breaker OPEN for ${serviceName}, using fallback`);
        if (fallback) return fallback;
        throw new Error(`Circuit breaker OPEN for service: ${serviceName}`);
      }
      // Try to transition to HALF_OPEN
      service.state = 'HALF_OPEN';
      logger.info(`Circuit breaker HALF_OPEN for ${serviceName}, testing...`);
    }

    try {
      const result = await fn();
      
      // Success - reset counter
      if (service.state === 'HALF_OPEN') {
        service.state = 'CLOSED';
        service.failureCount = 0;
        service.successCount = 0;
        logger.info(`Circuit breaker CLOSED for ${serviceName}`);
      } else if (service.state === 'CLOSED') {
        service.failureCount = 0;
      }
      
      service.lastSuccessTime = Date.now();
      return result;
      
    } catch (error) {
      service.failureCount++;
      service.lastFailureTime = Date.now();
      
      logger.warn(`Service ${serviceName} failed (${service.failureCount}/${this.failureThreshold})`, {
        error: error.message
      });

      // Check if we should open the circuit
      if (service.failureCount >= this.failureThreshold) {
        service.state = 'OPEN';
        service.nextAttemptTime = Date.now() + this.resetTimeout;
        logger.error(`Circuit breaker OPEN for ${serviceName}`, {
          failureCount: service.failureCount,
          resetIn: this.resetTimeout
        });
      }

      // Use fallback if provided
      if (fallback) {
        logger.info(`Using fallback for ${serviceName}`);
        return fallback;
      }

      throw error;
    }
  }

  /**
   * Get or create service circuit breaker
   */
  getOrCreateService(serviceName) {
    if (!this.services.has(serviceName)) {
      this.services.set(serviceName, {
        name: serviceName,
        state: 'CLOSED',
        failureCount: 0,
        successCount: 0,
        lastFailureTime: null,
        lastSuccessTime: null,
        nextAttemptTime: null
      });
    }
    return this.services.get(serviceName);
  }

  /**
   * Get circuit breaker status
   */
  getStatus() {
    const services = {};
    
    for (const [name, service] of this.services.entries()) {
      services[name] = {
        state: service.state,
        failureCount: service.failureCount,
        lastFailureTime: service.lastFailureTime,
        lastSuccessTime: service.lastSuccessTime,
        nextAttemptTime: service.nextAttemptTime
      };
    }

    return {
      timestamp: new Date().toISOString(),
      services,
      config: {
        failureThreshold: this.failureThreshold,
        resetTimeout: this.resetTimeout
      }
    };
  }

  /**
   * Reset service circuit breaker
   */
  reset(serviceName = null) {
    if (serviceName) {
      const service = this.services.get(serviceName);
      if (service) {
        service.state = 'CLOSED';
        service.failureCount = 0;
        service.successCount = 0;
        service.lastFailureTime = null;
        service.nextAttemptTime = null;
        logger.info(`Circuit breaker reset for ${serviceName}`);
      }
    } else {
      // Reset all
      for (const service of this.services.values()) {
        service.state = 'CLOSED';
        service.failureCount = 0;
        service.successCount = 0;
        service.lastFailureTime = null;
        service.nextAttemptTime = null;
      }
      logger.info('All circuit breakers reset');
    }
  }

  /**
   * Start monitoring circuit breaker health
   */
  startMonitoring() {
    this.monitoringLoop = setInterval(() => {
      for (const [name, service] of this.services.entries()) {
        // Auto-reset if in OPEN state and timeout has passed
        if (service.state === 'OPEN' && Date.now() >= service.nextAttemptTime) {
          logger.info(`Auto-resetting circuit breaker for ${name}`);
          this.reset(name);
        }
      }
    }, this.monitoringInterval);
  }

  /**
   * Stop monitoring
   */
  stopMonitoring() {
    if (this.monitoringLoop) {
      clearInterval(this.monitoringLoop);
    }
  }

  /**
   * Destroy circuit breaker
   */
  destroy() {
    this.stopMonitoring();
    this.services.clear();
  }
}

module.exports = { CircuitBreaker };
