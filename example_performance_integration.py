#!/usr/bin/env python3
"""
Example: Integrating Performance Optimization with CodeGenie Features

This example demonstrates how to use performance optimization features
with existing CodeGenie components for maximum efficiency.
"""

from pathlib import Path
import time

# Configure performance optimizer first
from src.codegenie.core.performance_optimizer import configure_optimizer, get_optimizer

# Configure for production use
optimizer = configure_optimizer(
    enable_caching=True,
    enable_profiling=False,  # Disable in production
    cache_size=2000
)

print("=" * 60)
print("Performance Optimization Integration Example")
print("=" * 60)

# Example 1: Optimized File Operations
print("\n1. Optimized File Operations")
print("-" * 60)

from src.codegenie.core.optimized_operations import create_optimized_file_creator

file_creator = create_optimized_file_creator()

# Create multiple files - file type detection is cached
files_to_create = [
    ("script1.py", "# Python script 1"),
    ("script2.py", "# Python script 2"),
    ("config.json", '{"key": "value"}'),
    ("readme.md", "# README"),
]

print("Creating files with optimized file creator...")
for filename, content in files_to_create:
    file_type = file_creator.detect_file_type(Path(filename))
    print(f"  {filename}: {file_type}")

# Check cache stats
result_cache_stats = optimizer.get_result_cache().get_stats()
print(f"\nCache performance:")
print(f"  Hits: {result_cache_stats.hits}")
print(f"  Misses: {result_cache_stats.misses}")
print(f"  Hit rate: {result_cache_stats.hit_rate:.2%}")

# Example 2: Optimized Diff Generation
print("\n2. Optimized Diff Generation")
print("-" * 60)

from src.codegenie.core.optimized_operations import create_optimized_diff_engine

diff_engine = create_optimized_diff_engine()

original = """def hello():
    print("Hello")
    return True"""

modified = """def hello(name):
    print(f"Hello, {name}")
    return True"""

print("Generating diffs (first call)...")
start = time.time()
diff1 = diff_engine.generate_diff(original, modified, "hello.py")
time1 = time.time() - start
print(f"  Time: {time1:.6f}s")
print(f"  Changes: +{diff1.additions} -{diff1.deletions}")

print("\nGenerating same diff (cached)...")
start = time.time()
diff2 = diff_engine.generate_diff(original, modified, "hello.py")
time2 = time.time() - start
print(f"  Time: {time2:.6f}s")
print(f"  Speedup: {time1/time2:.1f}x" if time2 > 0 else "  Instant!")

# Example 3: Optimized Context Analysis
print("\n3. Optimized Context Analysis")
print("-" * 60)

from src.codegenie.core.optimized_operations import create_optimized_context_analyzer

analyzer = create_optimized_context_analyzer()

# Analyze current project
project_path = Path(".")

print("Analyzing project (first time)...")
start = time.time()
context1 = analyzer.analyze_project(project_path)
time1 = time.time() - start
print(f"  Time: {time1:.4f}s")
if context1.language:
    print(f"  Language: {context1.language.name}")
print(f"  Frameworks: {len(context1.frameworks)}")

print("\nAnalyzing project (cached)...")
start = time.time()
context2 = analyzer.analyze_project(project_path)
time2 = time.time() - start
print(f"  Time: {time2:.4f}s")
print(f"  Speedup: {time1/time2:.1f}x" if time2 > 0 else "  Instant!")

# Example 4: Lazy Loading for Expensive Resources
print("\n4. Lazy Loading")
print("-" * 60)

from src.codegenie.core.optimized_operations import LazyLoader

def load_expensive_config():
    """Simulate loading expensive configuration."""
    print("  Loading expensive configuration...")
    time.sleep(0.1)
    return {"setting1": "value1", "setting2": "value2"}

# Create lazy loader - doesn't load yet
config_loader = LazyLoader(load_expensive_config)
print("Lazy loader created (not loaded yet)")
print(f"  Is loaded: {config_loader.is_loaded()}")

# Access when needed
print("\nAccessing configuration (triggers loading)...")
config = config_loader.value
print(f"  Configuration: {config}")
print(f"  Is loaded: {config_loader.is_loaded()}")

# Access again - no loading
print("\nAccessing configuration again (no loading)...")
config = config_loader.value
print(f"  Configuration: {config}")

# Example 5: Batch Processing
print("\n5. Batch Processing")
print("-" * 60)

from src.codegenie.core.optimized_operations import BatchProcessor

processor = BatchProcessor(batch_size=10)

# Simulate processing many files
files = [Path(f"file_{i}.txt") for i in range(35)]

def process_file(file_path):
    """Simulate file processing."""
    return f"Processed: {file_path.name}"

print(f"Processing {len(files)} files in batches of 10...")
start = time.time()
results = processor.process_files(files, process_file)
elapsed = time.time() - start

print(f"  Processed: {len(results)} files")
print(f"  Time: {elapsed:.4f}s")
print(f"  Rate: {len(results)/elapsed:.1f} files/sec")

# Example 6: Memory Optimization
print("\n6. Memory Optimization")
print("-" * 60)

from src.codegenie.core.optimized_operations import MemoryOptimizer

mem_optimizer = MemoryOptimizer()

# Limit large collections
large_collection = list(range(5000))
print(f"Original collection size: {len(large_collection)}")

limited = mem_optimizer.limit_collection_size(large_collection, max_size=1000)
print(f"Limited collection size: {len(limited)}")
print(f"Memory saved: ~{(len(large_collection) - len(limited)) * 8 / 1024:.1f} KB")

# Example 7: Performance Monitoring
print("\n7. Performance Monitoring")
print("-" * 60)

# Get comprehensive statistics
stats = optimizer.get_stats()

print("Cache Statistics:")
print(f"  Result Cache:")
print(f"    Hits: {stats['result_cache']['hits']}")
print(f"    Misses: {stats['result_cache']['misses']}")
print(f"    Hit Rate: {stats['result_cache']['hit_rate']:.2%}")
print(f"    Size: {stats['result_cache']['total_size']}")

print(f"\n  Template Cache:")
print(f"    Hits: {stats['template_cache']['hits']}")
print(f"    Misses: {stats['template_cache']['misses']}")
print(f"    Hit Rate: {stats['template_cache']['hit_rate']:.2%}")
print(f"    Size: {stats['template_cache']['total_size']}")

print(f"\n  Analysis Cache:")
print(f"    Hits: {stats['analysis_cache']['hits']}")
print(f"    Misses: {stats['analysis_cache']['misses']}")
print(f"    Hit Rate: {stats['analysis_cache']['hit_rate']:.2%}")
print(f"    Size: {stats['analysis_cache']['total_size']}")

# Example 8: Custom Caching
print("\n8. Custom Function Caching")
print("-" * 60)

from src.codegenie.core.performance_optimizer import ResultCache

custom_cache = ResultCache(max_size=100)

@custom_cache.cache_result(ttl=300)  # Cache for 5 minutes
def expensive_calculation(x, y):
    """Simulate expensive calculation."""
    time.sleep(0.05)
    return x ** y

print("First calculation (not cached)...")
start = time.time()
result1 = expensive_calculation(2, 10)
time1 = time.time() - start
print(f"  Result: {result1}")
print(f"  Time: {time1:.4f}s")

print("\nSecond calculation (cached)...")
start = time.time()
result2 = expensive_calculation(2, 10)
time2 = time.time() - start
print(f"  Result: {result2}")
print(f"  Time: {time2:.4f}s")
print(f"  Speedup: {time1/time2:.1f}x" if time2 > 0 else "  Instant!")

# Final Summary
print("\n" + "=" * 60)
print("Summary")
print("=" * 60)

print("\nPerformance Improvements:")
print("  ✓ File operations optimized with caching")
print("  ✓ Diff generation cached for repeated operations")
print("  ✓ Context analysis cached with automatic invalidation")
print("  ✓ Lazy loading defers expensive operations")
print("  ✓ Batch processing improves throughput")
print("  ✓ Memory optimization reduces footprint")
print("  ✓ Custom caching for application-specific needs")

print("\nBest Practices Applied:")
print("  ✓ Caching enabled for production")
print("  ✓ Profiling disabled for production")
print("  ✓ Appropriate cache sizes configured")
print("  ✓ Monitoring and statistics available")
print("  ✓ Resource optimization strategies in place")

print("\n" + "=" * 60)
print("Integration Example Complete!")
print("=" * 60)
