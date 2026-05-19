use lru_cache::LRUCache;

#[test]
fn test_basic_put_get() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    assert_eq!(cache.get(1), Some(10));
}

#[test]
fn test_eviction() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(2, 20);
    cache.put(3, 30); // evicts key 1
    assert_eq!(cache.get(1), None);
    assert_eq!(cache.get(2), Some(20));
    assert_eq!(cache.get(3), Some(30));
}

#[test]
fn test_update_existing() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(1, 100);
    assert_eq!(cache.get(1), Some(100));
}

#[test]
fn test_lru_order() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(2, 20);
    cache.get(1); // makes 1 recently used
    cache.put(3, 30); // should evict 2
    assert_eq!(cache.get(2), None);
    assert_eq!(cache.get(1), Some(10));
}

#[test]
fn test_capacity_one() {
    let mut cache = LRUCache::new(1);
    cache.put(1, 10);
    cache.put(2, 20);
    assert_eq!(cache.get(1), None);
    assert_eq!(cache.get(2), Some(20));
}
