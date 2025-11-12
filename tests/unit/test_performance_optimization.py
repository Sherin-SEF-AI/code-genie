"""
Unit tests for the performance optimization system.
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.codegenie.core.performance_optimization import (
    PerformanceOptimizer,
    IntelligentCache,
    ResourceManager,
    ParallelProcessor,
    PerformanceMonitor,
    CacheLevel,
    ResourceType,
    OptimizationStrategy,
    PerformanceMetrics,
    ResourceAllocation,
    CacheEntry
)


class TestIntelligentCache:
    """Test intelligent caching system."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def cache(self, temp_dir):
        config = {
            'disk_cache_dir': temp_dir / 'cache',
            'max_memory_size': 1024 * 1024,  # 1MB
            'max_disk_size': 10 * 1024 * 1024,  # 10MB
            'default_ttl': 3600
        }
        return IntelligentCache(config)
    
    @pytest.mark.asyncio
    async def test_memory_cache_operations(self, cache):
        """Test basic memory cache operations."""
        # Set value
        await cache.set("test_key", "test_value", level=CacheLevel.MEMORY)
        
        # Get value
        value = await cache.get("test_key")
        assert value == "test_value"
        
        # Cache hit should be recorded
        stats = cache.get_stats()
        assert stats['hit_rate'] > 0
    
    @pytest.mark.asyncio
    async def test_disk_cache_operations(self, cache):
        """Test disk cache operations."""
        # Set large value to disk
        large_value = "x" * (2 * 1024 * 1024)  # 2MB
        await cache.set("large_key", large_value, level=CacheLevel.DISK)
        
        # Get value
        value = await cache.get("large_key")
        assert value == large_value
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """Test cache TTL expiration."""
        # Set value with short TTL
        await cache.set("expire_key", "expire_value", ttl=1)
        
        # Should be available immediately
        value = await cache.get("expire_key")
        assert value == "expire_value"
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be expired
        value = await cache.get("expire_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache):
        """Test cache invalidation."""
        # Set values with tags
        await cache.set("key1", "value1", tags={"group1", "type_a"})
        await cache.set("key2", "value2", tags={"group1", "type_b"})
        await cache.set("key3", "value3", tags={"group2", "type_a"})
        
        # Invalidate by tags
        invalidated = await cache.invalidate_by_tags({"group1"})
        assert invalidated >= 2
        
        # Check values
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        assert await cache.get("key3") == "value3"
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache):
        """Test LRU eviction when memory is full."""
        # Fill cache beyond capacity
        for i in range(100):
            large_value = "x" * 50000  # 50KB each
            await cache.set(f"key_{i}", large_value, level=CacheLevel.MEMORY)
        
        # Some entries should be evicted
        stats = cache.get_stats()
        assert stats['evictions'] > 0
    
    def test_cache_statistics(self, cache):
        """Test cache statistics."""
        stats = cache.get_stats()
        
        assert 'hit_rate' in stats
        assert 'total_requests' in stats
        assert 'memory_entries' in stats
        assert 'memory_usage_bytes' in stats
        assert 'evictions' in stats


class TestResourceManager:
    """Test resource management system."""
    
    @pytest.fixture
    def resource_manager(self):
        config = {
            'max_threads': 5,
            'max_processes': 2
        }
        return ResourceManager(config)
    
    @pytest.mark.asyncio
    async def test_resource_allocation(self, resource_manager):
        """Test resource allocation and deallocation."""
        requirements = ResourceAllocation(
            cpu_cores=1,
            memory_mb=256,
            max_concurrent_tasks=5
        )
        
        # Allocate resources
        success = await resource_manager.allocate_resources("task1", requirements)
        assert success
        
        # Check allocation exists
        assert "task1" in resource_manager.allocations
        assert "task1" in resource_manager.active_tasks
        
        # Deallocate resources
        await resource_manager.deallocate_resources("task1")
        
        # Check allocation removed
        assert "task1" not in resource_manager.allocations
        assert "task1" not in resource_manager.active_tasks
    
    @pytest.mark.asyncio
    async def test_resource_availability_check(self, resource_manager):
        """Test resource availability checking."""
        # Large resource requirement
        large_requirements = ResourceAllocation(
            cpu_cores=1000,  # Impossible requirement
            memory_mb=1000000  # 1TB
        )
        
        # Should fail allocation
        success = await resource_manager.allocate_resources("impossible_task", large_requirements)
        assert not success
    
    def test_resource_statistics(self, resource_manager):
        """Test resource usage statistics."""
        stats = resource_manager.get_resource_stats()
        
        assert 'active_tasks' in stats
        assert 'total_allocations' in stats
        assert 'current_cpu' in stats
        assert 'current_memory' in stats
        assert 'current_disk' in stats


class TestParallelProcessor:
    """Test parallel processing system."""
    
    @pytest.fixture
    def processor(self):
        config = {
            'max_threads': 4,
            'max_processes': 2,
            'num_workers': 2,
            'batch_size': 5
        }
        return ParallelProcessor(config)
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self, processor):
        """Test parallel task processing."""
        def cpu_task(x):
            return x * x
        
        async def async_task(x):
            await asyncio.sleep(0.1)
            return x + 1
        
        tasks = [
            (cpu_task, (i,), {}) for i in range(5)
        ] + [
            (async_task, (i,), {}) for i in range(5)
        ]
        
        start_time = time.time()
        results = await processor.process_parallel(tasks)
        end_time = time.time()
        
        # Should complete faster than sequential execution
        assert end_time - start_time < 2.0
        assert len(results) == 10
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, processor):
        """Test batch processing optimization."""
        def simple_task(x):
            return x * 2
        
        tasks = [(simple_task, (i,), {}) for i in range(20)]
        
        results = await processor.process_parallel(
            tasks, 
            strategy=OptimizationStrategy.BATCH_PROCESSING
        )
        
        assert len(results) == 20
        assert results[0] == 0
        assert results[19] == 38
    
    @pytest.mark.asyncio
    async def test_task_queue(self, processor):
        """Test task queue submission and retrieval."""
        def test_task(x):
            return x ** 2
        
        # Submit task
        await processor.submit_task("test_task_1", test_task, 5)
        
        # Get result
        result = await processor.get_result("test_task_1", timeout=5.0)
        assert result == 25
    
    @pytest.mark.asyncio
    async def test_task_timeout(self, processor):
        """Test task timeout handling."""
        def slow_task():
            time.sleep(10)  # Very slow task
            return "done"
        
        await processor.submit_task("slow_task", slow_task)
        
        # Should timeout
        with pytest.raises(TimeoutError):
            await processor.get_result("slow_task", timeout=1.0)


class TestPerformanceMonitor:
    """Test performance monitoring system."""
    
    @pytest.fixture
    def monitor(self):
        config = {
            'thresholds': {
                'cpu_usage': 80.0,
                'memory_usage': 80.0,
                'response_time': 2.0,
                'error_rate': 0.1
            }
        }
        return PerformanceMonitor(config)
    
    @pytest.mark.asyncio
    async def test_metrics_recording(self, monitor):
        """Test performance metrics recording."""
        metrics = PerformanceMetrics(
            cpu_usage=50.0,
            memory_usage=60.0,
            response_time=1.5,
            error_rate=0.05
        )
        
        await monitor.record_metrics(metrics)
        
        assert len(monitor.metrics_history) == 1
        assert monitor.metrics_history[0] == metrics
    
    @pytest.mark.asyncio
    async def test_threshold_alerts(self, monitor):
        """Test threshold-based alerting."""
        # High CPU usage
        high_cpu_metrics = PerformanceMetrics(
            cpu_usage=90.0,  # Above threshold
            memory_usage=50.0,
            response_time=1.0,
            error_rate=0.02
        )
        
        await monitor.record_metrics(high_cpu_metrics)
        
        # Should generate alert
        assert len(monitor.alerts) > 0
        cpu_alert = next((a for a in monitor.alerts if a['type'] == 'cpu_high'), None)
        assert cpu_alert is not None
        assert cpu_alert['severity'] == 'warning'
    
    def test_performance_summary(self, monitor):
        """Test performance summary generation."""
        # Add some metrics
        for i in range(10):
            metrics = PerformanceMetrics(
                cpu_usage=50.0 + i,
                memory_usage=40.0 + i,
                response_time=1.0 + i * 0.1
            )
            monitor.metrics_history.append(metrics)
        
        summary = monitor.get_performance_summary(hours=1)
        
        assert 'avg_cpu_usage' in summary
        assert 'avg_memory_usage' in summary
        assert 'avg_response_time' in summary
        assert summary['metrics_count'] == 10


class TestPerformanceOptimizer:
    """Test main performance optimizer."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def optimizer(self, temp_dir):
        config = {
            'cache': {
                'disk_cache_dir': temp_dir / 'cache',
                'max_memory_size': 1024 * 1024
            },
            'resources': {
                'max_threads': 4,
                'max_processes': 2
            },
            'parallel': {
                'max_threads': 4,
                'num_workers': 2
            },
            'monitoring': {
                'thresholds': {
                    'response_time': 5.0
                }
            }
        }
        return PerformanceOptimizer(config)
    
    @pytest.mark.asyncio
    async def test_caching_optimization(self, optimizer):
        """Test caching optimization strategy."""
        call_count = 0
        
        async def expensive_operation(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x * x
        
        # First call - should execute and cache
        result1 = await optimizer.optimize_operation(
            expensive_operation,
            args=(5,),
            strategies=[OptimizationStrategy.CACHING]
        )
        assert result1 == 25
        assert call_count == 1
        
        # Second call - should use cache
        result2 = await optimizer.optimize_operation(
            expensive_operation,
            args=(5,),
            strategies=[OptimizationStrategy.CACHING]
        )
        assert result2 == 25
        assert call_count == 1  # Should not increment
    
    @pytest.mark.asyncio
    async def test_parallel_optimization(self, optimizer):
        """Test parallel processing optimization."""
        async def parallelizable_operation(x):
            await asyncio.sleep(0.1)
            return x * 2
        
        # Mark as parallelizable
        parallelizable_operation._parallelizable = True
        
        start_time = time.time()
        result = await optimizer.optimize_operation(
            parallelizable_operation,
            args=(10,),
            strategies=[OptimizationStrategy.PARALLEL_PROCESSING]
        )
        end_time = time.time()
        
        assert result == 20
        # Should complete quickly due to parallel processing
        assert end_time - start_time < 1.0
    
    @pytest.mark.asyncio
    async def test_resource_pooling_optimization(self, optimizer):
        """Test resource pooling optimization."""
        async def resource_intensive_operation():
            await asyncio.sleep(0.1)
            return "completed"
        
        result = await optimizer.optimize_operation(
            resource_intensive_operation,
            strategies=[OptimizationStrategy.RESOURCE_POOLING]
        )
        
        assert result == "completed"
    
    @pytest.mark.asyncio
    async def test_multiple_strategies(self, optimizer):
        """Test combining multiple optimization strategies."""
        call_count = 0
        
        async def complex_operation(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return x ** 2
        
        # Apply multiple strategies
        result = await optimizer.optimize_operation(
            complex_operation,
            args=(7,),
            strategies=[
                OptimizationStrategy.CACHING,
                OptimizationStrategy.RESOURCE_POOLING
            ]
        )
        
        assert result == 49
        assert call_count == 1
        
        # Second call should use cache
        result2 = await optimizer.optimize_operation(
            complex_operation,
            args=(7,),
            strategies=[
                OptimizationStrategy.CACHING,
                OptimizationStrategy.RESOURCE_POOLING
            ]
        )
        
        assert result2 == 49
        assert call_count == 1  # Should not increment due to caching
    
    def test_optimization_statistics(self, optimizer):
        """Test optimization statistics."""
        stats = optimizer.get_optimization_stats()
        
        assert 'cache_stats' in stats
        assert 'resource_stats' in stats
        assert 'performance_summary' in stats
        assert 'active_optimizations' in stats


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_cache_performance_benchmark(self, temp_dir):
        """Benchmark cache performance."""
        config = {
            'disk_cache_dir': temp_dir / 'cache',
            'max_memory_size': 10 * 1024 * 1024  # 10MB
        }
        cache = IntelligentCache(config)
        
        # Benchmark memory cache
        start_time = time.time()
        
        async def benchmark_memory():
            for i in range(1000):
                await cache.set(f"key_{i}", f"value_{i}")
            
            for i in range(1000):
                value = await cache.get(f"key_{i}")
                assert value == f"value_{i}"
        
        asyncio.run(benchmark_memory())
        
        memory_time = time.time() - start_time
        assert memory_time < 2.0  # Should complete in under 2 seconds
        
        # Check hit rate
        stats = cache.get_stats()
        assert stats['hit_rate'] > 0.9  # Should have high hit rate
    
    def test_parallel_processing_benchmark(self):
        """Benchmark parallel processing performance."""
        config = {
            'max_threads': 8,
            'num_workers': 4
        }
        processor = ParallelProcessor(config)
        
        def cpu_intensive_task(n):
            # Simulate CPU-intensive work
            result = 0
            for i in range(n * 1000):
                result += i
            return result
        
        # Sequential execution
        start_time = time.time()
        sequential_results = []
        for i in range(10):
            sequential_results.append(cpu_intensive_task(100))
        sequential_time = time.time() - start_time
        
        # Parallel execution
        start_time = time.time()
        tasks = [(cpu_intensive_task, (100,), {}) for _ in range(10)]
        parallel_results = asyncio.run(processor.process_parallel(tasks))
        parallel_time = time.time() - start_time
        
        # Parallel should be faster (allowing for overhead)
        assert parallel_time < sequential_time * 0.8
        assert len(parallel_results) == len(sequential_results)
        
        processor.shutdown()
    
    @pytest.mark.asyncio
    async def test_monitoring_overhead_benchmark(self):
        """Benchmark monitoring system overhead."""
        config = {}
        monitor = PerformanceMonitor(config)
        
        # Measure overhead of metrics recording
        start_time = time.time()
        
        for i in range(1000):
            metrics = PerformanceMetrics(
                cpu_usage=50.0,
                memory_usage=60.0,
                response_time=1.0
            )
            await monitor.record_metrics(metrics)
        
        overhead_time = time.time() - start_time
        
        # Should have minimal overhead
        assert overhead_time < 1.0  # Under 1 second for 1000 recordings
        assert len(monitor.metrics_history) == 1000


# Load testing
class TestPerformanceLoadTesting:
    """Load testing for performance components."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_cache_load_test(self, temp_dir):
        """Load test for cache system."""
        config = {
            'disk_cache_dir': temp_dir / 'cache',
            'max_memory_size': 50 * 1024 * 1024  # 50MB
        }
        cache = IntelligentCache(config)
        
        # Concurrent cache operations
        async def cache_worker(worker_id):
            for i in range(100):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}" * 100  # Larger values
                
                await cache.set(key, value)
                retrieved = await cache.get(key)
                assert retrieved == value
        
        # Run multiple workers concurrently
        start_time = time.time()
        workers = [cache_worker(i) for i in range(10)]
        await asyncio.gather(*workers)
        load_time = time.time() - start_time
        
        # Should handle load efficiently
        assert load_time < 10.0  # Complete in under 10 seconds
        
        # Check cache statistics
        stats = cache.get_stats()
        assert stats['hit_rate'] > 0.5  # Reasonable hit rate under load
    
    @pytest.mark.asyncio
    async def test_resource_manager_load_test(self):
        """Load test for resource manager."""
        config = {
            'max_threads': 20,
            'max_processes': 5
        }
        resource_manager = ResourceManager(config)
        
        # Simulate many concurrent resource requests
        async def resource_worker(worker_id):
            for i in range(10):
                task_id = f"worker_{worker_id}_task_{i}"
                requirements = ResourceAllocation(
                    cpu_cores=1,
                    memory_mb=128
                )
                
                success = await resource_manager.allocate_resources(task_id, requirements)
                if success:
                    # Simulate work
                    await asyncio.sleep(0.1)
                    await resource_manager.deallocate_resources(task_id)
        
        # Run multiple workers
        start_time = time.time()
        workers = [resource_worker(i) for i in range(20)]
        await asyncio.gather(*workers)
        load_time = time.time() - start_time
        
        # Should handle concurrent requests efficiently
        assert load_time < 15.0  # Complete in reasonable time
        
        # All resources should be deallocated
        stats = resource_manager.get_resource_stats()
        assert stats['active_tasks'] == 0


if __name__ == "__main__":
    pytest.main([__file__])