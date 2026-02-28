const logger = require('../lib/logger');
const { normalizeTimestamp } = require('../lib/utils');

/**
 * API Key validation middleware
 */
function validateApiKey(req, res, next) {
  const apiKey = req.headers['x-api-key'] || req.query.apiKey;
  const validKey = process.env.API_KEY || 'default-key-change-me';

  if (!apiKey) {
    logger.warn('API request without key', { path: req.path, ip: req.ip });
    return res.status(401).json({
      success: false,
      error: {
        message: 'Missing API key',
        hint: 'Provide x-api-key header or ?apiKey query parameter'
      },
      timestamp: normalizeTimestamp(new Date())
    });
  }

  if (apiKey !== validKey) {
    logger.warn('Invalid API key attempt', { path: req.path, ip: req.ip });
    return res.status(403).json({
      success: false,
      error: {
        message: 'Invalid API key'
      },
      timestamp: normalizeTimestamp(new Date())
    });
  }

  next();
}

/**
 * Socket.io authentication
 */
function socketAuthMiddleware(socket, next) {
  const apiKey = socket.handshake.auth.apiKey || socket.handshake.query.apiKey;
  const validKey = process.env.API_KEY || 'default-key-change-me';

  if (!apiKey || apiKey !== validKey) {
    logger.warn('Socket connection without valid API key', { 
      socketId: socket.id,
      ip: socket.handshake.address 
    });
    return next(new Error('Invalid or missing API key'));
  }

  socket.apiKey = apiKey;
  next();
}

/**
 * CORS validation
 */
function validateOrigin(origin) {
  const allowedOrigins = (process.env.ALLOWED_ORIGINS || '*').split(',').map(o => o.trim());
  
  if (allowedOrigins.includes('*')) {
    return true;
  }

  return allowedOrigins.includes(origin);
}

/**
 * Token refresh middleware (for JWT if needed)
 */
function tokenRefresh(req, res, next) {
  // This is a placeholder for JWT token refresh logic
  // Implement based on your auth strategy
  next();
}

module.exports = {
  validateApiKey,
  socketAuthMiddleware,
  validateOrigin,
  tokenRefresh
};
