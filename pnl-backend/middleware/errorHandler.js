const logger = require('../lib/logger');
const { normalizeTimestamp } = require('../lib/utils');

/**
 * Centralized error handler middleware
 */
function errorHandler(err, req, res, next) {
  const errorId = Math.random().toString(36).substring(7);
  const timestamp = normalizeTimestamp(new Date());

  // Log error
  logger.error(`[${errorId}] Request error`, {
    path: req.path,
    method: req.method,
    statusCode: err.statusCode || 500,
    message: err.message,
    stack: err.stack
  });

  // Determine status code
  let statusCode = err.statusCode || 500;
  if (err.response) {
    statusCode = err.response.status || 500;
  }

  // Don't leak error details in production
  const isProduction = process.env.NODE_ENV === 'production';
  const errorMessage = isProduction && statusCode === 500 
    ? 'Internal server error'
    : err.message || 'Unknown error';

  // Send error response
  res.status(statusCode).json({
    success: false,
    error: {
      id: errorId,
      message: errorMessage,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    },
    timestamp
  });
}

/**
 * Async error wrapper
 */
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

/**
 * Validation error handler
 */
function validationErrorHandler(schema) {
  return (req, res, next) => {
    try {
      const { error, value } = schema.validate(req.body);
      
      if (error) {
        return res.status(400).json({
          success: false,
          error: {
            message: 'Validation failed',
            details: error.details.map(d => ({
              field: d.path.join('.'),
              message: d.message
            }))
          },
          timestamp: normalizeTimestamp(new Date())
        });
      }

      req.validatedData = value;
      next();
    } catch (err) {
      next(err);
    }
  };
}

/**
 * Rate limiter middleware
 */
function rateLimiter(options = {}) {
  const maxRequests = options.maxRequests || 100;
  const windowMs = options.windowMs || 60000; // 1 minute
  const requests = new Map();

  return (req, res, next) => {
    const clientId = req.ip || req.connection.remoteAddress;
    const now = Date.now();

    if (!requests.has(clientId)) {
      requests.set(clientId, []);
    }

    const clientRequests = requests.get(clientId);
    const windowStart = now - windowMs;

    // Remove old requests
    const recentRequests = clientRequests.filter(t => t > windowStart);
    requests.set(clientId, recentRequests);

    if (recentRequests.length >= maxRequests) {
      return res.status(429).json({
        success: false,
        error: {
          message: 'Too many requests',
          retryAfter: Math.ceil((recentRequests[0] + windowMs - now) / 1000)
        },
        timestamp: normalizeTimestamp(new Date())
      });
    }

    recentRequests.push(now);
    next();
  };
}

module.exports = {
  errorHandler,
  asyncHandler,
  validationErrorHandler,
  rateLimiter
};
