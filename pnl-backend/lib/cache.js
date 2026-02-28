const redis = require('redis');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const logger = require('./logger');
const { createCacheKey, safeJsonParse } = require('./utils');

/**
 * 4-Tier Cache Manager
 * 1. Process cache (in-memory, fastest)
 * 2. Redis (distributed cache)
 * 3. SQLite (persistent cache)
 * 4. Fallback (null/defaults)
 */
class CacheManager {
  constructor(options = {}) {
    this.processCache = new Map();
    this.redisClient = null;
    this.db = null;
    
    this.config = {
      redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
      dbPath: options.dbPath || path.join(__dirname, '../data/cache.db'),
      ttl: options.ttl || 300000, // 5 minutes default
      maxProcessCacheSize: options.maxProcessCacheSize || 1000,
      enableRedis: options.enableRedis !== false,
      enableSqlite: options.enableSqlite !== false
    };

    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      errors: 0
    };
  }

  /**
   * Initialize cache manager (connect to Redis and SQLite)
   */
  async initialize() {
    try {
      // Initialize SQLite
      if (this.config.enableSqlite) {
        await this.initSqlite();
      }

      // Initialize Redis
      if (this.config.enableRedis) {
        await this.initRedis();
      }

      logger.info('Cache manager initialized successfully', {
        sqliteEnabled: this.config.enableSqlite,
        redisEnabled: this.config.enableRedis
      });
    } catch (error) {
      logger.error('Cache manager initialization failed', { error: error.message });
      // Continue with fallback mode
    }
  }

  /**
   * Initialize SQLite database
   */
  async initSqlite() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(this.config.dbPath, (err) => {
        if (err) {
          logger.error('SQLite initialization failed', { error: err.message });
          this.db = null;
          reject(err);
        } else {
          // Create cache table
          this.db.run(`
            CREATE TABLE IF NOT EXISTS cache (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              expiry INTEGER,
              created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
              updated_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
            )
          `, (err) => {
            if (err) {
              logger.error('Failed to create cache table', { error: err.message });
              reject(err);
            } else {
              logger.info('SQLite cache table ready');
              resolve();
            }
          });
        }
      });
    });
  }

  /**
   * Initialize Redis connection
   */
  async initRedis() {
    try {
      this.redisClient = redis.createClient({
        url: this.config.redisUrl,
        socket: {
          reconnectStrategy: (retries) => {
            const delay = Math.min(retries * 50, 500);
            return delay;
          }
        }
      });

      this.redisClient.on('error', (err) => {
        logger.warn('Redis connection error', { error: err.message });
        this.redisClient = null;
      });

      await this.redisClient.connect();
      logger.info('Redis connected');
    } catch (error) {
      logger.warn('Redis initialization failed', { error: error.message });
      this.redisClient = null;
    }
  }

  /**
   * Get value from cache (4-tier lookup)
   */
  async get(key) {
    try {
      // Tier 1: Process cache
      if (this.processCache.has(key)) {
        const cached = this.processCache.get(key);
        if (cached.expiry > Date.now()) {
          this.stats.hits++;
          logger.debug(`Cache hit (process): ${key}`);
          return cached.value;
        } else {
          this.processCache.delete(key);
        }
      }

      // Tier 2: Redis
      if (this.redisClient) {
        try {
          const value = await this.redisClient.get(key);
          if (value) {
            const parsed = safeJsonParse(value);
            this.cacheToProcessMemory(key, parsed);
            this.stats.hits++;
            logger.debug(`Cache hit (redis): ${key}`);
            return parsed;
          }
        } catch (error) {
          logger.warn(`Redis get error for ${key}`, { error: error.message });
        }
      }

      // Tier 3: SQLite
      if (this.db) {
        try {
          const value = await this.sqliteGet(key);
          if (value) {
            this.cacheToProcessMemory(key, value);
            if (this.redisClient) {
              await this.redisSet(key, value);
            }
            this.stats.hits++;
            logger.debug(`Cache hit (sqlite): ${key}`);
            return value;
          }
        } catch (error) {
          logger.warn(`SQLite get error for ${key}`, { error: error.message });
        }
      }

      // Tier 4: Miss
      this.stats.misses++;
      logger.debug(`Cache miss: ${key}`);
      return null;

    } catch (error) {
      logger.error(`Cache get error for ${key}`, { error: error.message });
      this.stats.errors++;
      return null;
    }
  }

  /**
   * Set value in cache (all tiers)
   */
  async set(key, value, ttl = null) {
    try {
      const ttlMs = (ttl || this.config.ttl);
      const expiry = Date.now() + ttlMs;

      // Tier 1: Process cache
      this.cacheToProcessMemory(key, value, expiry);

      // Tier 2: Redis
      if (this.redisClient) {
        try {
          await this.redisSet(key, value, ttl);
        } catch (error) {
          logger.warn(`Redis set error for ${key}`, { error: error.message });
        }
      }

      // Tier 3: SQLite
      if (this.db) {
        try {
          await this.sqliteSet(key, value, expiry);
        } catch (error) {
          logger.warn(`SQLite set error for ${key}`, { error: error.message });
        }
      }

      this.stats.sets++;
      logger.debug(`Cache set: ${key}`);
      return true;

    } catch (error) {
      logger.error(`Cache set error for ${key}`, { error: error.message });
      this.stats.errors++;
      return false;
    }
  }

  /**
   * Delete from cache (all tiers)
   */
  async delete(key) {
    try {
      // Tier 1: Process cache
      this.processCache.delete(key);

      // Tier 2: Redis
      if (this.redisClient) {
        try {
          await this.redisClient.del(key);
        } catch (error) {
          logger.warn(`Redis delete error for ${key}`, { error: error.message });
        }
      }

      // Tier 3: SQLite
      if (this.db) {
        try {
          await this.sqliteDelete(key);
        } catch (error) {
          logger.warn(`SQLite delete error for ${key}`, { error: error.message });
        }
      }

      this.stats.deletes++;
      logger.debug(`Cache delete: ${key}`);
      return true;

    } catch (error) {
      logger.error(`Cache delete error for ${key}`, { error: error.message });
      this.stats.errors++;
      return false;
    }
  }

  /**
   * Clear all cache
   */
  async clear() {
    try {
      // Clear process cache
      this.processCache.clear();

      // Clear Redis
      if (this.redisClient) {
        try {
          await this.redisClient.flushAll();
        } catch (error) {
          logger.warn('Redis flush error', { error: error.message });
        }
      }

      // Clear SQLite
      if (this.db) {
        try {
          await this.sqliteDeleteAll();
        } catch (error) {
          logger.warn('SQLite clear error', { error: error.message });
        }
      }

      logger.info('Cache cleared');
      return true;

    } catch (error) {
      logger.error('Cache clear error', { error: error.message });
      return false;
    }
  }

  /**
   * Get cache statistics
   */
  async getStats() {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? (this.stats.hits / total * 100).toFixed(2) : 0;

    return {
      ...this.stats,
      total,
      hitRate: `${hitRate}%`,
      processCacheSize: this.processCache.size,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get cache health status
   */
  async getHealth() {
    return {
      processCache: 'healthy',
      redis: this.redisClient ? 'connected' : 'disabled',
      sqlite: this.db ? 'connected' : 'disabled'
    };
  }

  /**
   * Helper: Cache to process memory
   */
  cacheToProcessMemory(key, value, expiry = null) {
    if (this.processCache.size >= this.config.maxProcessCacheSize) {
      // Simple eviction: remove oldest entry
      const firstKey = this.processCache.keys().next().value;
      this.processCache.delete(firstKey);
    }

    this.processCache.set(key, {
      value,
      expiry: expiry || Date.now() + this.config.ttl
    });
  }

  /**
   * Helper: Redis get
   */
  async redisSet(key, value, ttl = null) {
    const json = JSON.stringify(value);
    if (ttl) {
      await this.redisClient.setEx(key, Math.ceil(ttl / 1000), json);
    } else {
      await this.redisClient.set(key, json);
    }
  }

  /**
   * Helper: SQLite get
   */
  sqliteGet(key) {
    return new Promise((resolve) => {
      if (!this.db) {
        resolve(null);
        return;
      }

      this.db.get(
        'SELECT value, expiry FROM cache WHERE key = ? AND (expiry IS NULL OR expiry > ?)',
        [key, Date.now()],
        (err, row) => {
          if (err || !row) {
            resolve(null);
          } else {
            resolve(safeJsonParse(row.value));
          }
        }
      );
    });
  }

  /**
   * Helper: SQLite set
   */
  sqliteSet(key, value, expiry) {
    return new Promise((resolve) => {
      if (!this.db) {
        resolve();
        return;
      }

      const json = JSON.stringify(value);
      this.db.run(
        'INSERT OR REPLACE INTO cache (key, value, expiry) VALUES (?, ?, ?)',
        [key, json, expiry],
        (err) => {
          resolve();
        }
      );
    });
  }

  /**
   * Helper: SQLite delete
   */
  sqliteDelete(key) {
    return new Promise((resolve) => {
      if (!this.db) {
        resolve();
        return;
      }

      this.db.run('DELETE FROM cache WHERE key = ?', [key], () => {
        resolve();
      });
    });
  }

  /**
   * Helper: SQLite delete all
   */
  sqliteDeleteAll() {
    return new Promise((resolve) => {
      if (!this.db) {
        resolve();
        return;
      }

      this.db.run('DELETE FROM cache', () => {
        resolve();
      });
    });
  }

  /**
   * Disconnect databases
   */
  async disconnect() {
    if (this.redisClient) {
      await this.redisClient.quit();
      logger.info('Redis disconnected');
    }

    if (this.db) {
      this.db.close((err) => {
        if (err) {
          logger.error('SQLite close error', { error: err.message });
        } else {
          logger.info('SQLite disconnected');
        }
      });
    }
  }
}

module.exports = { CacheManager };
