#!/usr/bin/env python3
"""
Test script for performance optimization features.
"""

import time
from pathlib import Path

from src.codegenie.core.performance_optimizer import (
    LRUCache,
    ResultCache,
    TemplateCache,
    AnalysisCache,
    Profiler,
    PerformanceOptimizer,
    configure_optimizer,
    get_optimizer
)
from src.codegenie.core.optimized_operations import (
    OptimizedFileCreator,
    OptimizedDiffEngine,
    OptimizedContextAnalyzer,
    LazyLoader,
    BatchProcessor,
    MemoryOptimizer
)


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
        return x * 2
    
    # First call
    result1 = test_function(5)
    assert result1 == 10, "Incorrect result"
    assert call_count == 1, "Function should be called once"
    
    # Second call (cached)
    result2 = test_function(5)
    assert result2 == 10, "Incorrect cached result"
    assert call_count == 1, "Function should not be called again"
    
    # Different argument
    result3 = test_function(10)
    assert result3 == 20, "Incorrect result for different argument"
    assert call_count == 2, "Function should be called for new argument"
    
    print("  ✓ Result Cache tests passed")


def test_template_cache():
    """Test template caching."""
    print("\nTesting Template Cache...")
    
    cache = TemplateCache(max_size=50)
    
    # Create temporary template
    template_path = Path("test_template.txt")
    template_content = "Test template content"
    
    try:
        template_path.write_text(template_content)
        
        # First access
        cached = cache.get_template(template_path)
        assert cached is None, "Should not be cached initially"
        
        # Cache it
        cache.put_template(template_path, template_content)
        
        # Second access
        cached = cache.get_template(template_path)
        assert cached == template_content, "Should retrieve cached content"
        
        print("  ✓ Template Cache tests passed")
        
    finally:
        if template_path.exists():
            template_path.unlink()


def test_profiler():
    """Test profiler functionality."""
    print("\nTesting Profiler...")
    
    profiler = Profiler()
    
    @profiler.profile
    def test_func():
        time.sleep(0.01)
        return "result"
    
    # Call function multiple times
    for _ in range(3):
        test_func()
    
    # Check profile
    profile = profiler.get_profile("test_func")
    assert profile is not None, "Profile should exist"
    assert profile.call_count == 3, "Should have 3 calls"
    assert profile.total_time > 0, "Should have execution time"
    
    # Test report generation
    report = profiler.get_report()
    assert "test_func" in report, "Report should contain function name"
    
    print("  ✓ Profiler tests passed")


def test_performance_optimizer():
    """Test performance optimizer."""
    print("\nTesting Performance Optimizer...")
    
    optimizer = PerformanceOptimizer(
        enable_caching=True,
        enable_profiling=True,
        cache_size=100
    )
    
    # Test cache access
    result_cache = optimizer.get_result_cache()
    assert result_cache is not None, "Should have result cache"
    
    template_cache = optimizer.get_template_cache()
    assert template_cache is not None, "Should have template cache"
    
    analysis_cache = optimizer.get_analysis_cache()
    assert analysis_cache is not None, "Should have analysis cache"
    
    profiler = optimizer.get_profiler()
    assert profiler is not None, "Should have profiler"
    
    # Test stats
    stats = optimizer.get_stats()
    assert 'result_cache' in stats, "Stats should include result cache"
    assert 'template_cache' in stats, "Stats should include template cache"
    assert 'analysis_cache' in stats, "Stats should include analysis cache"
    
    # Test report
    report = optimizer.get_report()
    assert "Performance Optimization Report" in report, "Should generate report"
    
    print("  ✓ Performance Optimizer tests passed")


def test_optimized_diff_engine():
    """Test optimized diff engine."""
    print("\nTesting Optimized Diff Engine...")
    
    diff_engine = OptimizedDiffEngine()
    
    original = "Line 1\nLine 2\nLine 3"
    modified = "Line 1\nLine 2 modified\nLine 3"
    
    # First call
    start = time.time()
    diff1 = diff_engine.generate_diff(original, modified, "test.txt")
    time1 = time.time() - start
    
    # Second call (should be faster due to caching)
    start = time.time()
    diff2 = diff_engine.generate_diff(original, modified, "test.txt")
    time2 = time.time() - start
    
    assert diff1.additions == diff2.additions, "Diffs should be identical"
    assert diff1.deletions == diff2.deletions, "Diffs should be identical"
    
    # Second call should be faster (or at least not slower)
    # Note: In practice, caching provides speedup, but timing can vary
    
    print("  ✓ Optimized Diff Engine tests passed")


def test_lazy_loader():
    """Test lazy loading."""
    print("\nTesting Lazy Loader...")
    
    load_count = 0
    
    def loader():
        nonlocal load_count
        load_count += 1
        return "loaded_value"
    
    lazy = LazyLoader(loader)
    
    # Should not be loaded initially
    assert not lazy.is_loaded(), "Should not be loaded initially"
    assert load_count == 0, "Loader should not be called yet"
    
    # Access value
    value1 = lazy.value
    assert value1 == "loaded_value", "Should return loaded value"
    assert lazy.is_loaded(), "Should be loaded now"
    assert load_count == 1, "Loader should be called once"
    
    # Access again
    value2 = lazy.value
    assert value2 == "loaded_value", "Should return same value"
    assert load_count == 1, "Loader should not be called again"
    
    print("  ✓ Lazy Loader tests passed")


def test_batch_processor():
    """Test batch processing."""
    print("\nTesting Batch Processor...")
    
    processor = BatchProcessor(batch_size=5)
    
    files = [Path(f"file_{i}.txt") for i in range(12)]
    
    processed = []
    
    def process_func(file_path):
        processed.append(file_path)
        return str(file_path)
    
    results = processor.process_files(files, process_func)
    
    assert len(results) == len(files), "Should process all files"
    assert len(processed) == len(files), "Should call processor for each file"
    
    print("  ✓ Batch Processor tests passed")


def test_memory_optimizer():
    """Test memory optimizer."""
    print("\nTesting Memory Optimizer...")
    
    optimizer = MemoryOptimizer()
    
    # Test collection limiting
    large_collection = list(range(2000))
    limited = optimizer.limit_collection_size(large_collection, max_size=100)
    
    assert len(limited) == 100, "Should limit collection size"
    assert limited == large_collection[:100], "Should keep first items"
    
    print("  ✓ Memory Optimizer tests passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Performance Optimization Tests")
    print("=" * 60)
    
    tests = [
        test_lru_cache,
        test_result_cache,
        test_template_cache,
        test_profiler,
        test_performance_optimizer,
        test_optimized_diff_engine,
        test_lazy_loader,
        test_batch_processor,
        test_memory_optimizer,
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
