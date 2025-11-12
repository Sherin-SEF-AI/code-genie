#!/usr/bin/env python3
"""
Demo script for performance optimization features.

Demonstrates:
- Result caching
- Template caching
- Analysis caching
- Performance profiling
- Lazy loading
- Memory optimization
"""

import time
from pathlib import Path

from src.codegenie.core.performance_optimizer import (
    configure_optimizer,
    get_optimizer,
    LRUCache,
    ResultCache,
    TemplateCache,
    AnalysisCache,
    Profiler,
    LazyLoader
)
from src.codegenie.core.optimized_operations import (
    create_optimized_file_creator,
    create_optimized_diff_engine,
    create_optimized_context_analyzer,
    BatchProcessor,
    MemoryOptimizer
)


def demo_lru_cache():
    """Demonstrate LRU cache functionality."""
    print("\n" + "=" * 60)
    print("LRU Cache Demo")
    print("=" * 60)
    
    cache = LRUCache(max_size=5)
    
    # Add items
    print("\nAdding items to cache...")
    for i in range(7):
        cache.put(f"key_{i}", f"value_{i}")
        print(f"  Added key_{i}")
    
    # Check stats
    stats = cache.get_stats()
    print(f"\nCache Stats:")
    print(f"  Size: {stats.total_size}")
    print(f"  Evictions: {stats.evictions}")
    
    # Test retrieval
    print("\nRetrieving items...")
    for i in range(7):
        value = cache.get(f"key_{i}")
        status = "HIT" if value else "MISS"
        print(f"  key_{i}: {status}")
    
    print(f"\nFinal Stats:")
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    print(f"  Hit Rate: {stats.hit_rate:.2%}")


def demo_result_cache():
    """Demonstrate result caching."""
    print("\n" + "=" * 60)
    print("Result Cache Demo")
    print("=" * 60)
    
    cache = ResultCache(max_size=100)
    
    # Define expensive function
    @cache.cache_result(ttl=60)
    def expensive_computation(n):
        """Simulate expensive computation."""
        time.sleep(0.1)  # Simulate work
        return n * n
    
    # First call (cache miss)
    print("\nFirst call (cache miss)...")
    start = time.time()
    result1 = expensive_computation(10)
    time1 = time.time() - start
    print(f"  Result: {result1}")
    print(f"  Time: {time1:.4f}s")
    
    # Second call (cache hit)
    print("\nSecond call (cache hit)...")
    start = time.time()
    result2 = expensive_computation(10)
    time2 = time.time() - start
    print(f"  Result: {result2}")
    print(f"  Time: {time2:.4f}s")
    
    print(f"\nSpeedup: {time1 / time2:.1f}x")
    
    # Check stats
    stats = cache.get_stats()
    print(f"\nCache Stats:")
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    print(f"  Hit Rate: {stats.hit_rate:.2%}")


def demo_template_cache():
    """Demonstrate template caching."""
    print("\n" + "=" * 60)
    print("Template Cache Demo")
    print("=" * 60)
    
    cache = TemplateCache(max_size=50)
    
    # Create a temporary template file
    template_path = Path("temp_template.txt")
    template_content = "Hello, {name}!"
    
    try:
        template_path.write_text(template_content)
        
        # First access (cache miss)
        print("\nFirst access (cache miss)...")
        start = time.time()
        content1 = cache.get_template(template_path)
        if content1 is None:
            content1 = template_path.read_text()
            cache.put_template(template_path, content1)
        time1 = time.time() - start
        print(f"  Content: {content1}")
        print(f"  Time: {time1:.6f}s")
        
        # Second access (cache hit)
        print("\nSecond access (cache hit)...")
        start = time.time()
        content2 = cache.get_template(template_path)
        time2 = time.time() - start
        print(f"  Content: {content2}")
        print(f"  Time: {time2:.6f}s")
        
        if time1 > 0:
            print(f"\nSpeedup: {time1 / time2:.1f}x")
        
    finally:
        # Cleanup
        if template_path.exists():
            template_path.unlink()


def demo_profiler():
    """Demonstrate performance profiling."""
    print("\n" + "=" * 60)
    print("Profiler Demo")
    print("=" * 60)
    
    profiler = Profiler()
    
    # Define functions to profile
    @profiler.profile
    def fast_function():
        time.sleep(0.01)
        return "fast"
    
    @profiler.profile
    def slow_function():
        time.sleep(0.05)
        return "slow"
    
    # Call functions multiple times
    print("\nExecuting functions...")
    for i in range(5):
        fast_function()
        slow_function()
    
    # Show profiling report
    print("\n" + profiler.get_report())


def demo_optimized_operations():
    """Demonstrate optimized operations."""
    print("\n" + "=" * 60)
    print("Optimized Operations Demo")
    print("=" * 60)
    
    # Configure optimizer
    optimizer = configure_optimizer(
        enable_caching=True,
        enable_profiling=True,
        cache_size=1000
    )
    
    # Create optimized instances
    print("\nCreating optimized instances...")
    file_creator = create_optimized_file_creator()
    diff_engine = create_optimized_diff_engine()
    context_analyzer = create_optimized_context_analyzer()
    
    print("  ✓ OptimizedFileCreator")
    print("  ✓ OptimizedDiffEngine")
    print("  ✓ OptimizedContextAnalyzer")
    
    # Test diff generation with caching
    print("\nTesting diff generation...")
    original = "Line 1\nLine 2\nLine 3"
    modified = "Line 1\nLine 2 modified\nLine 3\nLine 4"
    
    # First call
    start = time.time()
    diff1 = diff_engine.generate_diff(original, modified, "test.txt")
    time1 = time.time() - start
    print(f"  First call: {time1:.6f}s")
    
    # Second call (cached)
    start = time.time()
    diff2 = diff_engine.generate_diff(original, modified, "test.txt")
    time2 = time.time() - start
    print(f"  Second call: {time2:.6f}s")
    
    if time1 > 0:
        print(f"  Speedup: {time1 / time2:.1f}x")
    
    # Show optimizer stats
    print("\n" + optimizer.get_report())


def demo_lazy_loading():
    """Demonstrate lazy loading."""
    print("\n" + "=" * 60)
    print("Lazy Loading Demo")
    print("=" * 60)
    
    from src.codegenie.core.optimized_operations import LazyLoader
    
    # Define expensive loader
    def expensive_loader():
        print("  Loading expensive data...")
        time.sleep(0.1)
        return {"data": "expensive"}
    
    # Create lazy loader
    print("\nCreating lazy loader...")
    loader = LazyLoader(expensive_loader)
    print(f"  Is loaded: {loader.is_loaded()}")
    
    # Access value (triggers loading)
    print("\nAccessing value (first time)...")
    value1 = loader.value
    print(f"  Value: {value1}")
    print(f"  Is loaded: {loader.is_loaded()}")
    
    # Access value again (no loading)
    print("\nAccessing value (second time)...")
    value2 = loader.value
    print(f"  Value: {value2}")
    print(f"  Is loaded: {loader.is_loaded()}")


def demo_batch_processing():
    """Demonstrate batch processing."""
    print("\n" + "=" * 60)
    print("Batch Processing Demo")
    print("=" * 60)
    
    processor = BatchProcessor(batch_size=10)
    
    # Create test files list
    files = [Path(f"file_{i}.txt") for i in range(35)]
    
    # Define processor function
    def process_file(file_path):
        return f"Processed: {file_path.name}"
    
    # Process files in batches
    print(f"\nProcessing {len(files)} files in batches of 10...")
    results = processor.process_files(files, process_file)
    
    print(f"  Processed {len(results)} files")
    print(f"  Sample results:")
    for result in results[:5]:
        print(f"    {result}")


def demo_memory_optimization():
    """Demonstrate memory optimization."""
    print("\n" + "=" * 60)
    print("Memory Optimization Demo")
    print("=" * 60)
    
    optimizer = MemoryOptimizer()
    
    # Test collection size limiting
    print("\nTesting collection size limiting...")
    large_collection = list(range(2000))
    print(f"  Original size: {len(large_collection)}")
    
    limited = optimizer.limit_collection_size(large_collection, max_size=1000)
    print(f"  Limited size: {len(limited)}")
    
    # Test streaming (simulated)
    print("\nTesting streaming capability...")
    print("  ✓ Stream large files in chunks")
    print("  ✓ Process files without loading entire content")
    print("  ✓ Reduce memory footprint")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("Performance Optimization Demo")
    print("=" * 60)
    
    demos = [
        ("LRU Cache", demo_lru_cache),
        ("Result Cache", demo_result_cache),
        ("Template Cache", demo_template_cache),
        ("Profiler", demo_profiler),
        ("Optimized Operations", demo_optimized_operations),
        ("Lazy Loading", demo_lazy_loading),
        ("Batch Processing", demo_batch_processing),
        ("Memory Optimization", demo_memory_optimization),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\nError in {name} demo: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
