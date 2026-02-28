const { CacheManager } = require('../lib/cache');

describe('CacheManager', () => {
  let cache;

  beforeEach(() => {
    cache = new CacheManager({
      enableRedis: false,
      enableSqlite: false
    });
  });

  describe('set and get', () => {
    test('should set and retrieve value', async () => {
      const key = 'test-key';
      const value = { data: 'test-value' };

      await cache.set(key, value);
      const result = await cache.get(key);

      expect(result).toEqual(value);
    });

    test('should return null for non-existent key', async () => {
      const result = await cache.get('non-existent');
      expect(result).toBeNull();
    });

    test('should respect TTL expiry', async () => {
      const key = 'ttl-test';
      const value = { data: 'test' };

      await cache.set(key, value, 100); // 100ms TTL

      // Immediately should work
      expect(await cache.get(key)).toEqual(value);

      // After expiry should be null
      await new Promise(resolve => setTimeout(resolve, 150));
      expect(await cache.get(key)).toBeNull();
    });
  });

  describe('delete', () => {
    test('should delete a key', async () => {
      const key = 'delete-test';
      await cache.set(key, { data: 'test' });

      expect(await cache.get(key)).toBeDefined();

      await cache.delete(key);
      expect(await cache.get(key)).toBeNull();
    });
  });

  describe('clear', () => {
    test('should clear all cache', async () => {
      await cache.set('key1', { data: 1 });
      await cache.set('key2', { data: 2 });

      expect(cache.processCache.size).toBe(2);

      await cache.clear();
      expect(cache.processCache.size).toBe(0);
    });
  });

  describe('getStats', () => {
    test('should return cache statistics', async () => {
      const key = 'stat-test';
      const value = { data: 'test' };

      await cache.set(key, value);
      await cache.get(key); // Hit
      await cache.get('non-existent'); // Miss

      const stats = await cache.getStats();

      expect(stats.hits).toBe(1);
      expect(stats.misses).toBe(1);
      expect(stats.hitRate).toBe('50.00%');
    });
  });

  describe('process memory eviction', () => {
    test('should evict oldest entry when max size reached', async () => {
      const smallCache = new CacheManager({
        maxProcessCacheSize: 2,
        enableRedis: false,
        enableSqlite: false
      });

      await smallCache.set('key1', { data: 1 });
      await smallCache.set('key2', { data: 2 });
      await smallCache.set('key3', { data: 3 });

      expect(smallCache.processCache.size).toBe(2);
      expect(await smallCache.get('key1')).toBeNull(); // Evicted
      expect(await smallCache.get('key2')).toBeDefined();
      expect(await smallCache.get('key3')).toBeDefined();
    });
  });
});
