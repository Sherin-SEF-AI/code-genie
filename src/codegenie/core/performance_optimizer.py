"""
Performance Optimizer for CodeGenie core operations.

Provides caching, profiling, and resource optimization for:
- File operations
- Diff generation
- Context analysis
- Template processing
"""

import functools
import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import threading

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'total_size': self.total_size,
            'hit_rate': self.hit_rate,
        }


@dataclass
class ProfileResult:
    """Result of a profiling operation."""
    function_name: str
    execution_time: float
    call_count: int = 1
    total_time: float = 0.0
    avg_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'function_name': self.function_name,
            'execution_time': self.execution_time,
            'call_count': self.call_count,
            'total_time': self.total_time,
            'avg_time': self.avg_time,
        }


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache implementation.
    
    Provides efficient caching with automatic eviction of least recently used items.
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items in cache
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict = OrderedDict()
        self.stats = CacheStats()
        self.lock = threading.RLock()
        
        logger.info(f"LRUCache initialized: max_size={max_size}, max_memory={max_memory_mb}MB")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats.hits += 1
                return self.cache[key]
            
            self.stats.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        """
        Put value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            # Update existing key
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key] = value
                return
            
            # Add new key
            self.cache[key] = value
            self.cache.move_to_end(key)
            
            # Update size
            self.stats.total_size = len(self.cache)
            
            # Evict if necessary
            while len(self.cache) > self.max_size:
                self._evict_oldest()
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if key was found and removed
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.total_size = len(self.cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.stats.total_size = 0
            logger.info("Cache cleared")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self.lock:
            return self.stats
    
    def _evict_oldest(self) -> None:
        """Evict the oldest (least recently used) item."""
        if self.cache:
            self.cache.popitem(last=False)
            self.stats.evictions += 1
            self.stats.total_size = len(self.cache)


class ResultCache:
    """
    Specialized cache for function results with automatic key generation.
    """
    
    def __init__(self, max_size: int = 500):
        """
        Initialize result cache.
        
        Args:
            max_size: Maximum number of cached results
        """
        self.cache = LRUCache(max_size=max_size)
        logger.info(f"ResultCache initialized: max_size={max_size}")
    
    def cache_result(
        self,
        ttl: Optional[int] = None
    ) -> Callable:
        """
        Decorator to cache function results.
        
        Args:
            ttl: Time to live in seconds (None for no expiration)
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(func.__name__, args, kwargs)
                
                # Check cache
                cached = self.cache.get(cache_key)
                if cached is not None:
                    if ttl is None or time.time() - cached['timestamp'] < ttl:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cached['value']
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                self.cache.put(cache_key, {
                    'value': result,
                    'timestamp': time.time()
                })
                
                return result
            
            return wrapper
        return decorator
    
    def _generate_key(self, func_name: str, args: Tuple, kwargs: Dict) -> str:
        """Generate cache key from function name and arguments."""
        # Create a string representation of arguments
        key_parts = [func_name]
        
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, Path):
                key_parts.append(str(arg))
            else:
                # Use type name for complex objects
                key_parts.append(type(arg).__name__)
        
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}={v}")
            elif isinstance(v, Path):
                key_parts.append(f"{k}={v}")
        
        # Hash the key for consistent length
        key_str = '|'.join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.cache.get_stats()


class TemplateCache:
    """
    Specialized cache for template content and compiled templates.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize template cache.
        
        Args:
            max_size: Maximum number of cached templates
        """
        self.cache = LRUCache(max_size=max_size)
        self.file_mtimes: Dict[str, float] = {}
        logger.info(f"TemplateCache initialized: max_size={max_size}")
    
    def get_template(self, template_path: Path) -> Optional[str]:
        """
        Get template content from cache.
        
        Args:
            template_path: Path to template file
            
        Returns:
            Template content or None if not cached or stale
        """
        key = str(template_path)
        
        # Check if file has been modified
        try:
            current_mtime = template_path.stat().st_mtime
            cached_mtime = self.file_mtimes.get(key)
            
            if cached_mtime and current_mtime > cached_mtime:
                # File modified, invalidate cache
                self.cache.invalidate(key)
                del self.file_mtimes[key]
                return None
        except Exception:
            return None
        
        return self.cache.get(key)
    
    def put_template(self, template_path: Path, content: str) -> None:
        """
        Cache template content.
        
        Args:
            template_path: Path to template file
            content: Template content
        """
        key = str(template_path)
        
        try:
            mtime = template_path.stat().st_mtime
            self.file_mtimes[key] = mtime
        except Exception:
            pass
        
        self.cache.put(key, content)
    
    def clear(self) -> None:
        """Clear template cache."""
        self.cache.clear()
        self.file_mtimes.clear()


class AnalysisCache:
    """
    Specialized cache for context analysis results.
    """
    
    def __init__(self, max_size: int = 50):
        """
        Initialize analysis cache.
        
        Args:
            max_size: Maximum number of cached analyses
        """
        self.cache = LRUCache(max_size=max_size)
        self.project_hashes: Dict[str, str] = {}
        logger.info(f"AnalysisCache initialized: max_size={max_size}")
    
    def get_analysis(self, project_path: Path) -> Optional[Any]:
        """
        Get cached analysis for a project.
        
        Args:
            project_path: Path to project
            
        Returns:
            Cached analysis or None if not cached or stale
        """
        key = str(project_path)
        
        # Check if project structure has changed
        current_hash = self._compute_project_hash(project_path)
        cached_hash = self.project_hashes.get(key)
        
        if cached_hash and current_hash != cached_hash:
            # Project changed, invalidate cache
            self.cache.invalidate(key)
            del self.project_hashes[key]
            return None
        
        return self.cache.get(key)
    
    def put_analysis(self, project_path: Path, analysis: Any) -> None:
        """
        Cache analysis result.
        
        Args:
            project_path: Path to project
            analysis: Analysis result
        """
        key = str(project_path)
        
        # Compute and store project hash
        project_hash = self._compute_project_hash(project_path)
        self.project_hashes[key] = project_hash
        
        self.cache.put(key, analysis)
    
    def _compute_project_hash(self, project_path: Path) -> str:
        """
        Compute hash of project structure for change detection.
        
        Args:
            project_path: Path to project
            
        Returns:
            Hash string
        """
        hash_parts = []
        
        try:
            # Hash key files and directories
            for item in sorted(project_path.iterdir()):
                if item.name.startswith('.'):
                    continue
                
                hash_parts.append(f"{item.name}:{item.stat().st_mtime}")
                
                # Limit depth to avoid performance issues
                if item.is_dir() and item.name not in ['node_modules', 'venv', '__pycache__']:
                    for subitem in sorted(item.iterdir())[:10]:
                        hash_parts.append(f"{subitem.name}:{subitem.stat().st_mtime}")
        except Exception as e:
            logger.debug(f"Error computing project hash: {e}")
            return str(time.time())
        
        hash_str = '|'.join(hash_parts)
        return hashlib.md5(hash_str.encode()).hexdigest()
    
    def clear(self) -> None:
        """Clear analysis cache."""
        self.cache.clear()
        self.project_hashes.clear()


class Profiler:
    """
    Performance profiler for tracking execution times.
    """
    
    def __init__(self):
        """Initialize profiler."""
        self.profiles: Dict[str, ProfileResult] = {}
        self.enabled = True
        self.lock = threading.RLock()
        logger.info("Profiler initialized")
    
    def profile(self, func: Callable) -> Callable:
        """
        Decorator to profile function execution.
        
        Args:
            func: Function to profile
            
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                self._record_execution(func.__name__, execution_time)
        
        return wrapper
    
    def _record_execution(self, func_name: str, execution_time: float) -> None:
        """Record function execution time."""
        with self.lock:
            if func_name in self.profiles:
                profile = self.profiles[func_name]
                profile.call_count += 1
                profile.total_time += execution_time
                profile.avg_time = profile.total_time / profile.call_count
                profile.execution_time = execution_time
            else:
                self.profiles[func_name] = ProfileResult(
                    function_name=func_name,
                    execution_time=execution_time,
                    call_count=1,
                    total_time=execution_time,
                    avg_time=execution_time
                )
    
    def get_profile(self, func_name: str) -> Optional[ProfileResult]:
        """Get profile for a specific function."""
        with self.lock:
            return self.profiles.get(func_name)
    
    def get_all_profiles(self) -> List[ProfileResult]:
        """Get all profiles sorted by total time."""
        with self.lock:
            return sorted(
                self.profiles.values(),
                key=lambda p: p.total_time,
                reverse=True
            )
    
    def get_report(self) -> str:
        """Generate profiling report."""
        with self.lock:
            lines = [
                "=" * 80,
                "Performance Profile Report",
                "=" * 80,
                "",
                f"{'Function':<40} {'Calls':>8} {'Total (s)':>12} {'Avg (ms)':>12}",
                "-" * 80,
            ]
            
            for profile in self.get_all_profiles():
                lines.append(
                    f"{profile.function_name:<40} "
                    f"{profile.call_count:>8} "
                    f"{profile.total_time:>12.4f} "
                    f"{profile.avg_time * 1000:>12.2f}"
                )
            
            lines.append("=" * 80)
            
            return '\n'.join(lines)
    
    def reset(self) -> None:
        """Reset all profiling data."""
        with self.lock:
            self.profiles.clear()
            logger.info("Profiler reset")
    
    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False


class PerformanceOptimizer:
    """
    Main performance optimizer coordinating all optimization strategies.
    """
    
    def __init__(
        self,
        enable_caching: bool = True,
        enable_profiling: bool = False,
        cache_size: int = 1000
    ):
        """
        Initialize performance optimizer.
        
        Args:
            enable_caching: Whether to enable caching
            enable_profiling: Whether to enable profiling
            cache_size: Maximum cache size
        """
        self.enable_caching = enable_caching
        self.enable_profiling = enable_profiling
        
        # Initialize caches
        self.result_cache = ResultCache(max_size=cache_size)
        self.template_cache = TemplateCache(max_size=cache_size // 10)
        self.analysis_cache = AnalysisCache(max_size=cache_size // 20)
        
        # Initialize profiler
        self.profiler = Profiler()
        if not enable_profiling:
            self.profiler.disable()
        
        logger.info(
            f"PerformanceOptimizer initialized: "
            f"caching={enable_caching}, profiling={enable_profiling}"
        )
    
    def get_result_cache(self) -> ResultCache:
        """Get result cache instance."""
        return self.result_cache
    
    def get_template_cache(self) -> TemplateCache:
        """Get template cache instance."""
        return self.template_cache
    
    def get_analysis_cache(self) -> AnalysisCache:
        """Get analysis cache instance."""
        return self.analysis_cache
    
    def get_profiler(self) -> Profiler:
        """Get profiler instance."""
        return self.profiler
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            'result_cache': self.result_cache.get_stats().to_dict(),
            'template_cache': self.template_cache.cache.get_stats().to_dict(),
            'analysis_cache': self.analysis_cache.cache.get_stats().to_dict(),
            'profiling_enabled': self.profiler.enabled,
            'profile_count': len(self.profiler.profiles),
        }
    
    def get_report(self) -> str:
        """Generate comprehensive performance report."""
        lines = [
            "=" * 80,
            "Performance Optimization Report",
            "=" * 80,
            "",
            "Cache Statistics:",
            "-" * 80,
        ]
        
        # Result cache stats
        result_stats = self.result_cache.get_stats()
        lines.extend([
            f"Result Cache:",
            f"  Hits: {result_stats.hits}",
            f"  Misses: {result_stats.misses}",
            f"  Hit Rate: {result_stats.hit_rate:.2%}",
            f"  Size: {result_stats.total_size}",
            "",
        ])
        
        # Template cache stats
        template_stats = self.template_cache.cache.get_stats()
        lines.extend([
            f"Template Cache:",
            f"  Hits: {template_stats.hits}",
            f"  Misses: {template_stats.misses}",
            f"  Hit Rate: {template_stats.hit_rate:.2%}",
            f"  Size: {template_stats.total_size}",
            "",
        ])
        
        # Analysis cache stats
        analysis_stats = self.analysis_cache.cache.get_stats()
        lines.extend([
            f"Analysis Cache:",
            f"  Hits: {analysis_stats.hits}",
            f"  Misses: {analysis_stats.misses}",
            f"  Hit Rate: {analysis_stats.hit_rate:.2%}",
            f"  Size: {analysis_stats.total_size}",
            "",
        ])
        
        # Profiling report
        if self.profiler.enabled and self.profiler.profiles:
            lines.append("")
            lines.append(self.profiler.get_report())
        
        return '\n'.join(lines)
    
    def clear_all_caches(self) -> None:
        """Clear all caches."""
        self.result_cache.clear()
        self.template_cache.clear()
        self.analysis_cache.clear()
        logger.info("All caches cleared")
    
    def reset_profiler(self) -> None:
        """Reset profiler data."""
        self.profiler.reset()


# Global optimizer instance
_optimizer: Optional[PerformanceOptimizer] = None


def get_optimizer() -> PerformanceOptimizer:
    """Get global optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def configure_optimizer(
    enable_caching: bool = True,
    enable_profiling: bool = False,
    cache_size: int = 1000
) -> PerformanceOptimizer:
    """
    Configure global optimizer.
    
    Args:
        enable_caching: Whether to enable caching
        enable_profiling: Whether to enable profiling
        cache_size: Maximum cache size
        
    Returns:
        Configured optimizer instance
    """
    global _optimizer
    _optimizer = PerformanceOptimizer(
        enable_caching=enable_caching,
        enable_profiling=enable_profiling,
        cache_size=cache_size
    )
    return _optimizer
