#!/usr/bin/env python3
"""
Simple standalone test for performance optimization features.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only the performance optimizer module directly
import importlib.util

spec = importlib.util.spec_from_file_location(
    "performance_optimizer",
    "src/codegenie/core/performance_optimizer.py"
)
perf_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(perf_module)

LRUCache = perf_module.LRUCache
ResultCache = perf_module.ResultCache
Profiler = perf_module.Profiler


def test_lru_cache():
    """Test LRU cache functionality."""
    print("\nTesting LRU Cache...")
    
    cache = LRUCache(max_size=3)
    
    # Test basic operations
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")
    
    assert cache.get("key1") == "value1", "Failed to retrieve key1"
    assert cache.get("key2") == "value2", "Failed to retrieve key2"
    assert cache.get("key3") == "value3", "Failed to retrieve key3"
    
    # Test eviction
    cache.put("key4", "value4")
    assert cache.get("key1") is None, "key1 should have been evicted"
    assert cache.get("key4") == "value4", "Failed to retrieve key4"
    
    # Test stats
    stats = cache.get_stats()
    assert stats.hits > 0, "Should have cache hits"
    assert stats.misses > 0, "Should have cache misses"
    assert stats.evictions > 0, "Should have evictions"
    
    print(f"  ✓ Cache stats: {stats.hits} hits, {stats.misses} misses, {stats.evictions} evictions")
    print(f"  ✓ Hit rate: {stats.hit_rate:.2%}")
    print("  ✓ LRU Cache tests passed")


def test_result_cache():
    """Test result caching."""
    print("\nTesting Result Cache...")
    
    cache = ResultCache(max_size=100)
    
    call_count = 0
    
    @cache.cache_result(ttl=60)
    def test_function(x):
        nonlocal call_count
        call_count += 1
        time.sleep(0.01)  # Simulate work
        return x * 2
    
    # First call
    start = time.time()
    result1 = test_function(5)
    time1 = time.time() - start
    assert result1 == 10, "Incorrect result"
    assert call_count == 1, "Function should be called once"
    
    # Second call (cached)
    start = time.time()
    result2 = test_function(5)
    time2 = time.time() - start
    assert result2 == 10, "Incorrect cached result"
    assert call_count == 1, "Function should not be called again"
    
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"  ✓ First call: {time1:.4f}s")
    print(f"  ✓ Cached call: {time2:.4f}s")
    print(f"  ✓ Speedup: {speedup:.1f}x")
    print("  ✓ Result Cache tests passed")


def test_profiler():
    """Test profiler functionality."""
    print("\nTesting Profiler...")
    
    profiler = Profiler()
    
    @profiler.profile
    def fast_func():
        time.sleep(0.01)
        return "fast"
    
    @profiler.profile
    def slow_func():
        time.sleep(0.03)
        return "slow"
    
    # Call functions multiple times
    for _ in range(3):
        fast_func()
        slow_func()
    
    # Check profiles
    fast_profile = profiler.get_profile("fast_func")
    slow_profile = profiler.get_profile("slow_func")
    
    assert fast_profile is not None, "Fast profile should exist"
    assert slow_profile is not None, "Slow profile should exist"
    assert fast_profile.call_count == 3, "Should have 3 calls"
    assert slow_profile.call_count == 3, "Should have 3 calls"
    
    print(f"  ✓ fast_func: {fast_profile.call_count} calls, avg {fast_profile.avg_time*1000:.2f}ms")
    print(f"  ✓ slow_func: {slow_profile.call_count} calls, avg {slow_profile.avg_time*1000:.2f}ms")
    print("  ✓ Profiler tests passed")


def test_cache_invalidation():
    """Test cache invalidation."""
    print("\nTesting Cache Invalidation...")
    
    cache = LRUCache(max_size=10)
    
    # Add items
    for i in range(5):
        cache.put(f"key_{i}", f"value_{i}")
    
    # Verify items exist
    assert cache.get("key_0") == "value_0", "Should retrieve key_0"
    
    # Invalidate
    success = cache.invalidate("key_0")
    assert success, "Should successfully invalidate"
    
    # Verify invalidated
    assert cache.get("key_0") is None, "key_0 should be invalidated"
    
    # Clear all
    cache.clear()
    assert cache.get("key_1") is None, "All keys should be cleared"
    
    print("  ✓ Cache Invalidation tests passed")


def test_cache_stats():
    """Test cache statistics."""
    print("\nTesting Cache Statistics...")
    
    cache = LRUCache(max_size=5)
    
    # Perform operations
    for i in range(10):
        cache.put(f"key_{i}", f"value_{i}")
    
    for i in range(15):
        cache.get(f"key_{i}")
    
    stats = cache.get_stats()
    
    print(f"  ✓ Total size: {stats.total_size}")
    print(f"  ✓ Hits: {stats.hits}")
    print(f"  ✓ Misses: {stats.misses}")
    print(f"  ✓ Evictions: {stats.evictions}")
    print(f"  ✓ Hit rate: {stats.hit_rate:.2%}")
    
    assert stats.total_size <= 5, "Size should not exceed max"
    assert stats.evictions > 0, "Should have evictions"
    
    print("  ✓ Cache Statistics tests passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Performance Optimization Tests (Standalone)")
    print("=" * 60)
    
    tests = [
        test_lru_cache,
        test_result_cache,
        test_profiler,
        test_cache_invalidation,
        test_cache_stats,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test_func.__name__} error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Tests Complete: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
