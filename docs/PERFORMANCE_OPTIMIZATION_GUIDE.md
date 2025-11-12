# Performance Optimization Guide

This guide covers the performance optimization features in CodeGenie, including caching, profiling, and resource optimization.

## Overview

CodeGenie includes comprehensive performance optimization features:

- **Result Caching**: Cache expensive computation results
- **Template Caching**: Cache template content with automatic invalidation
- **Analysis Caching**: Cache project analysis results
- **Performance Profiling**: Track execution times and identify bottlenecks
- **Lazy Loading**: Defer expensive operations until needed
- **Batch Processing**: Process multiple items efficiently
- **Memory Optimization**: Reduce memory footprint

## Quick Start

### Basic Usage

```python
from src.codegenie.core.performance_optimizer import configure_optimizer

# Configure the global optimizer
optimizer = configure_optimizer(
    enable_caching=True,
    enable_profiling=True,
    cache_size=1000
)

# Use optimized operations
from src.codegenie.core.optimized_operations import (
    create_optimized_file_creator,
    create_optimized_diff_engine,
    create_optimized_context_analyzer
)

file_creator = create_optimized_file_creator()
diff_engine = create_optimized_diff_engine()
context_analyzer = create_optimized_context_analyzer()
```

## Caching

### LRU Cache

Thread-safe Least Recently Used cache with automatic eviction:

```python
from src.codegenie.core.performance_optimizer import LRUCache

cache = LRUCache(max_size=1000, max_memory_mb=100)

# Store values
cache.put("key1", "value1")
cache.put("key2", "value2")

# Retrieve values
value = cache.get("key1")  # Returns "value1"

# Check statistics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Hits: {stats.hits}, Misses: {stats.misses}")
```

### Result Cache

Automatically cache function results:

```python
from src.codegenie.core.performance_optimizer import ResultCache

cache = ResultCache(max_size=500)

@cache.cache_result(ttl=3600)  # Cache for 1 hour
def expensive_computation(x, y):
    # Expensive operation
    return x * y

# First call - executes function
result1 = expensive_computation(10, 20)

# Second call - returns cached result
result2 = expensive_computation(10, 20)  # Much faster!
```

### Template Cache

Cache template content with automatic invalidation on file changes:

```python
from src.codegenie.core.performance_optimizer import TemplateCache
from pathlib import Path

cache = TemplateCache(max_size=100)

template_path = Path("templates/my_template.txt")

# First access - reads from file
content = cache.get_template(template_path)
if content is None:
    content = template_path.read_text()
    cache.put_template(template_path, content)

# Second access - returns cached content
content = cache.get_template(template_path)  # Fast!
```

### Analysis Cache

Cache project analysis results with automatic invalidation on project changes:

```python
from src.codegenie.core.performance_optimizer import AnalysisCache
from pathlib import Path

cache = AnalysisCache(max_size=50)

project_path = Path("my_project")

# First analysis - performs full analysis
analysis = cache.get_analysis(project_path)
if analysis is None:
    analysis = perform_analysis(project_path)
    cache.put_analysis(project_path, analysis)

# Second access - returns cached analysis
analysis = cache.get_analysis(project_path)  # Fast!
```

## Performance Profiling

### Basic Profiling

Track function execution times:

```python
from src.codegenie.core.performance_optimizer import Profiler

profiler = Profiler()

@profiler.profile
def my_function():
    # Function code
    pass

# Call function multiple times
for i in range(100):
    my_function()

# Get profile results
profile = profiler.get_profile("my_function")
print(f"Calls: {profile.call_count}")
print(f"Average time: {profile.avg_time * 1000:.2f}ms")
print(f"Total time: {profile.total_time:.4f}s")

# Generate report
print(profiler.get_report())
```

### Profiling Report

```
================================================================================
Performance Profile Report
================================================================================

Function                                     Calls    Total (s)     Avg (ms)
--------------------------------------------------------------------------------
expensive_operation                            100       5.2341        52.34
moderate_operation                             200       2.1234        10.62
fast_operation                                1000       0.5123         0.51
================================================================================
```

## Optimized Operations

### Optimized File Creator

File creator with caching and profiling:

```python
from src.codegenie.core.optimized_operations import create_optimized_file_creator

file_creator = create_optimized_file_creator()

# File type detection is cached
file_type = file_creator.detect_file_type("script.py")

# Diff generation is profiled
diff = file_creator.generate_diff(original, modified, "file.py")
```

### Optimized Diff Engine

Diff engine with result caching:

```python
from src.codegenie.core.optimized_operations import create_optimized_diff_engine

diff_engine = create_optimized_diff_engine()

# First call - generates diff
diff1 = diff_engine.generate_diff(original, modified, "file.py")

# Second call with same content - returns cached diff
diff2 = diff_engine.generate_diff(original, modified, "file.py")  # Fast!
```

### Optimized Context Analyzer

Context analyzer with comprehensive caching:

```python
from src.codegenie.core.optimized_operations import create_optimized_context_analyzer
from pathlib import Path

analyzer = create_optimized_context_analyzer()

# First analysis - performs full analysis
context = analyzer.analyze_project(Path("my_project"))

# Second analysis - returns cached result if project unchanged
context = analyzer.analyze_project(Path("my_project"))  # Fast!
```

## Lazy Loading

Defer expensive operations until needed:

```python
from src.codegenie.core.optimized_operations import LazyLoader

def expensive_loader():
    # Expensive operation
    return load_large_dataset()

# Create lazy loader - doesn't execute yet
loader = LazyLoader(expensive_loader)

# Check if loaded
if not loader.is_loaded():
    print("Not loaded yet")

# Access value - triggers loading
data = loader.value  # Loads now

# Subsequent accesses don't reload
data = loader.value  # Fast!
```

## Batch Processing

Process multiple items efficiently:

```python
from src.codegenie.core.optimized_operations import BatchProcessor
from pathlib import Path

processor = BatchProcessor(batch_size=50)

files = list(Path("src").rglob("*.py"))

def process_file(file_path):
    # Process single file
    return analyze_file(file_path)

# Process all files in batches
results = processor.process_files(files, process_file)
```

## Memory Optimization

### Stream Large Files

Process large files without loading entire content:

```python
from src.codegenie.core.optimized_operations import MemoryOptimizer
from pathlib import Path

optimizer = MemoryOptimizer()

# Stream file in chunks
for chunk in optimizer.stream_large_file(Path("large_file.txt"), chunk_size=8192):
    process_chunk(chunk)

# Process large file in chunks
results = optimizer.process_large_file(
    Path("large_file.txt"),
    process_chunk_func,
    chunk_size=8192
)
```

### Limit Collection Size

Prevent memory issues with large collections:

```python
from src.codegenie.core.optimized_operations import MemoryOptimizer

optimizer = MemoryOptimizer()

# Large collection
large_list = list(range(10000))

# Limit size to prevent memory issues
limited = optimizer.limit_collection_size(large_list, max_size=1000)
```

## Performance Monitoring

### Get Statistics

```python
from src.codegenie.core.performance_optimizer import get_optimizer

optimizer = get_optimizer()

# Get comprehensive stats
stats = optimizer.get_stats()
print(f"Result cache hit rate: {stats['result_cache']['hit_rate']:.2%}")
print(f"Template cache size: {stats['template_cache']['total_size']}")
print(f"Analysis cache hits: {stats['analysis_cache']['hits']}")
```

### Generate Report

```python
from src.codegenie.core.performance_optimizer import get_optimizer

optimizer = get_optimizer()

# Generate comprehensive report
report = optimizer.get_report()
print(report)
```

Example report:

```
================================================================================
Performance Optimization Report
================================================================================

Cache Statistics:
--------------------------------------------------------------------------------
Result Cache:
  Hits: 1234
  Misses: 567
  Hit Rate: 68.52%
  Size: 450

Template Cache:
  Hits: 89
  Misses: 23
  Hit Rate: 79.46%
  Size: 45

Analysis Cache:
  Hits: 34
  Misses: 12
  Hit Rate: 73.91%
  Size: 18

================================================================================
Performance Profile Report
================================================================================

Function                                     Calls    Total (s)     Avg (ms)
--------------------------------------------------------------------------------
analyze_project                                 12       8.4521       704.34
generate_diff                                  234       2.3456        10.02
detect_language                                156       0.8912         5.71
================================================================================
```

## Best Practices

### 1. Enable Caching for Production

```python
from src.codegenie.core.performance_optimizer import configure_optimizer

# Production configuration
optimizer = configure_optimizer(
    enable_caching=True,
    enable_profiling=False,  # Disable in production
    cache_size=2000
)
```

### 2. Use Profiling for Development

```python
# Development configuration
optimizer = configure_optimizer(
    enable_caching=True,
    enable_profiling=True,  # Enable for development
    cache_size=500
)
```

### 3. Clear Caches When Needed

```python
optimizer = get_optimizer()

# Clear all caches
optimizer.clear_all_caches()

# Clear specific cache
optimizer.get_result_cache().clear()
```

### 4. Use Lazy Loading for Expensive Resources

```python
from src.codegenie.core.optimized_operations import LazyLoader

# Defer loading until needed
config = LazyLoader(load_config_file, "config.yaml")
database = LazyLoader(connect_to_database, connection_string)

# Only load when accessed
if need_config:
    cfg = config.value
```

### 5. Batch Process Large Collections

```python
from src.codegenie.core.optimized_operations import BatchProcessor

processor = BatchProcessor(batch_size=100)

# Process in batches for better performance
results = processor.process_files(large_file_list, process_func)
```

## Performance Tips

### 1. Cache Expensive Operations

Cache results of expensive operations like:
- Project analysis
- File parsing
- Diff generation
- Template rendering

### 2. Use Appropriate Cache Sizes

- Small projects: 500-1000 items
- Medium projects: 1000-2000 items
- Large projects: 2000-5000 items

### 3. Monitor Cache Hit Rates

Aim for:
- Result cache: >70% hit rate
- Template cache: >80% hit rate
- Analysis cache: >60% hit rate

### 4. Profile in Development

Use profiling to identify bottlenecks:
- Enable profiling in development
- Disable profiling in production
- Focus on functions with high total time

### 5. Optimize Memory Usage

- Stream large files
- Limit collection sizes
- Use lazy loading
- Clear caches periodically

## Troubleshooting

### High Memory Usage

```python
# Reduce cache sizes
optimizer = configure_optimizer(cache_size=500)

# Clear caches
optimizer.clear_all_caches()

# Use streaming for large files
optimizer = MemoryOptimizer()
for chunk in optimizer.stream_large_file(large_file):
    process_chunk(chunk)
```

### Low Cache Hit Rate

```python
# Check cache statistics
stats = optimizer.get_stats()
print(f"Hit rate: {stats['result_cache']['hit_rate']:.2%}")

# Increase cache size
optimizer = configure_optimizer(cache_size=2000)

# Check for cache invalidation issues
# Ensure cache keys are consistent
```

### Slow Performance

```python
# Enable profiling
optimizer = configure_optimizer(enable_profiling=True)

# Run operations
# ...

# Check profiling report
print(optimizer.get_report())

# Identify slow functions and optimize
```

## API Reference

### PerformanceOptimizer

Main optimizer class coordinating all optimization strategies.

**Methods:**
- `get_result_cache()`: Get result cache instance
- `get_template_cache()`: Get template cache instance
- `get_analysis_cache()`: Get analysis cache instance
- `get_profiler()`: Get profiler instance
- `get_stats()`: Get comprehensive statistics
- `get_report()`: Generate performance report
- `clear_all_caches()`: Clear all caches
- `reset_profiler()`: Reset profiler data

### LRUCache

Thread-safe LRU cache with automatic eviction.

**Methods:**
- `get(key)`: Get value from cache
- `put(key, value)`: Put value in cache
- `invalidate(key)`: Invalidate cache entry
- `clear()`: Clear all entries
- `get_stats()`: Get cache statistics

### ResultCache

Cache for function results with automatic key generation.

**Methods:**
- `cache_result(ttl)`: Decorator to cache function results
- `clear()`: Clear all cached results
- `get_stats()`: Get cache statistics

### Profiler

Performance profiler for tracking execution times.

**Methods:**
- `profile(func)`: Decorator to profile function
- `get_profile(func_name)`: Get profile for function
- `get_all_profiles()`: Get all profiles
- `get_report()`: Generate profiling report
- `reset()`: Reset profiling data
- `enable()`: Enable profiling
- `disable()`: Disable profiling

## Examples

See the following files for complete examples:
- `demo_performance_optimization.py`: Comprehensive demo
- `test_performance_simple.py`: Test examples
- `test_performance_optimization.py`: Full test suite

## Conclusion

The performance optimization features in CodeGenie provide comprehensive tools for improving application performance through caching, profiling, and resource optimization. Use these features to build faster, more efficient applications.
