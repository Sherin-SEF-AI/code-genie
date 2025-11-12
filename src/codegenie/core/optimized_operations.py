"""
Optimized versions of core operations with caching and lazy loading.

Provides performance-optimized wrappers for:
- File operations
- Diff generation
- Context analysis
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .performance_optimizer import get_optimizer
from .file_creator import FileCreator, FileOperation
from .diff_engine import DiffEngine, Diff, FileDiff
from .context_analyzer import ContextAnalyzer, ProjectContext

logger = logging.getLogger(__name__)


class OptimizedFileCreator(FileCreator):
    """
    Optimized file creator with result caching and lazy loading.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize optimized file creator."""
        super().__init__(*args, **kwargs)
        self.optimizer = get_optimizer()
        self.profiler = self.optimizer.get_profiler()
        logger.info("OptimizedFileCreator initialized")
    
    @property
    def _cached_detect_file_type(self):
        """Cached version of detect_file_type."""
        if not hasattr(self, '_detect_file_type_cached'):
            cache = self.optimizer.get_result_cache()
            self._detect_file_type_cached = cache.cache_result(ttl=3600)(
                super().detect_file_type
            )
        return self._detect_file_type_cached
    
    def detect_file_type(self, path) -> str:
        """Optimized file type detection with caching."""
        return self._cached_detect_file_type(path)
    
    def generate_diff(self, original: str, modified: str, filename: str = "file"):
        """Optimized diff generation with profiling."""
        @self.profiler.profile
        def _generate_diff():
            return super(OptimizedFileCreator, self).generate_diff(
                original, modified, filename
            )
        
        return _generate_diff()


class OptimizedDiffEngine(DiffEngine):
    """
    Optimized diff engine with caching and lazy evaluation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize optimized diff engine."""
        super().__init__(*args, **kwargs)
        self.optimizer = get_optimizer()
        self.profiler = self.optimizer.get_profiler()
        self._diff_cache: Dict[str, Diff] = {}
        logger.info("OptimizedDiffEngine initialized")
    
    def generate_diff(
        self,
        original: str,
        modified: str,
        filename: str = "file",
        format=None
    ) -> Diff:
        """
        Optimized diff generation with caching.
        
        Caches diff results based on content hash to avoid regenerating
        identical diffs.
        """
        @self.profiler.profile
        def _generate_diff():
            # Generate cache key from content
            import hashlib
            content_hash = hashlib.md5(
                f"{original}|{modified}|{filename}".encode()
            ).hexdigest()
            
            # Check cache
            if content_hash in self._diff_cache:
                logger.debug(f"Diff cache hit for {filename}")
                return self._diff_cache[content_hash]
            
            # Generate diff
            diff = super(OptimizedDiffEngine, self).generate_diff(
                original, modified, filename, format
            )
            
            # Cache result (limit cache size)
            if len(self._diff_cache) > 100:
                # Remove oldest entry
                self._diff_cache.pop(next(iter(self._diff_cache)))
            
            self._diff_cache[content_hash] = diff
            
            return diff
        
        return _generate_diff()
    
    def generate_batch_diff(
        self,
        file_changes: Dict[Path, Tuple[str, str]]
    ) -> List[FileDiff]:
        """
        Optimized batch diff generation with parallel processing hints.
        
        Processes diffs efficiently by reusing the diff engine and caching.
        """
        @self.profiler.profile
        def _generate_batch():
            return super(OptimizedDiffEngine, self).generate_batch_diff(file_changes)
        
        return _generate_batch()
    
    def clear_cache(self) -> None:
        """Clear diff cache."""
        self._diff_cache.clear()
        logger.info("Diff cache cleared")


class OptimizedContextAnalyzer(ContextAnalyzer):
    """
    Optimized context analyzer with caching and lazy loading.
    """
    
    def __init__(self):
        """Initialize optimized context analyzer."""
        super().__init__()
        self.optimizer = get_optimizer()
        self.profiler = self.optimizer.get_profiler()
        self.analysis_cache = self.optimizer.get_analysis_cache()
        self._lazy_loaded: Dict[str, Any] = {}
        logger.info("OptimizedContextAnalyzer initialized")
    
    def analyze_project(self, project_path: Path) -> ProjectContext:
        """
        Optimized project analysis with caching.
        
        Caches analysis results and only re-analyzes if project structure changes.
        """
        @self.profiler.profile
        def _analyze_project():
            # Check cache
            cached_analysis = self.analysis_cache.get_analysis(project_path)
            if cached_analysis is not None:
                logger.info(f"Using cached analysis for {project_path}")
                return cached_analysis
            
            # Perform analysis
            logger.info(f"Analyzing project (cache miss): {project_path}")
            context = super(OptimizedContextAnalyzer, self).analyze_project(project_path)
            
            # Cache result
            self.analysis_cache.put_analysis(project_path, context)
            
            return context
        
        return _analyze_project()
    
    def detect_language(self, path: Path):
        """Optimized language detection with caching."""
        @self.profiler.profile
        def _detect_language():
            # Use result cache for file-level detection
            cache = self.optimizer.get_result_cache()
            
            @cache.cache_result(ttl=3600)
            def _cached_detect(p: Path):
                return super(OptimizedContextAnalyzer, self).detect_language(p)
            
            return _cached_detect(path)
        
        return _detect_language()
    
    def detect_framework(self, project_path: Path, language: str = None):
        """Optimized framework detection with caching."""
        @self.profiler.profile
        def _detect_framework():
            cache = self.optimizer.get_result_cache()
            
            @cache.cache_result(ttl=3600)
            def _cached_detect(p: Path, lang: Optional[str]):
                return super(OptimizedContextAnalyzer, self).detect_framework(p, lang)
            
            return _cached_detect(project_path, language)
        
        return _detect_framework()
    
    def extract_conventions(self, project_path: Path):
        """Optimized convention extraction with caching."""
        @self.profiler.profile
        def _extract_conventions():
            cache = self.optimizer.get_result_cache()
            
            @cache.cache_result(ttl=3600)
            def _cached_extract(p: Path):
                return super(OptimizedContextAnalyzer, self).extract_conventions(p)
            
            return _cached_extract(project_path)
        
        return _extract_conventions()
    
    def _analyze_file_structure(self, project_path: Path):
        """Optimized file structure analysis with lazy loading."""
        @self.profiler.profile
        def _analyze_structure():
            # Use lazy loading for large directory trees
            return super(OptimizedContextAnalyzer, self)._analyze_file_structure(
                project_path
            )
        
        return _analyze_structure()


class LazyLoader:
    """
    Lazy loader for expensive operations.
    
    Defers loading of data until it's actually needed.
    """
    
    def __init__(self, loader_func, *args, **kwargs):
        """
        Initialize lazy loader.
        
        Args:
            loader_func: Function to call when loading data
            *args: Arguments for loader function
            **kwargs: Keyword arguments for loader function
        """
        self._loader_func = loader_func
        self._args = args
        self._kwargs = kwargs
        self._loaded = False
        self._value = None
    
    def load(self):
        """Load the value if not already loaded."""
        if not self._loaded:
            self._value = self._loader_func(*self._args, **self._kwargs)
            self._loaded = True
        return self._value
    
    @property
    def value(self):
        """Get the loaded value."""
        return self.load()
    
    def is_loaded(self) -> bool:
        """Check if value has been loaded."""
        return self._loaded
    
    def reset(self) -> None:
        """Reset the loader."""
        self._loaded = False
        self._value = None


class BatchProcessor:
    """
    Batch processor for efficient bulk operations.
    """
    
    def __init__(self, batch_size: int = 50):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items to process in each batch
        """
        self.batch_size = batch_size
        self.profiler = get_optimizer().get_profiler()
    
    def process_files(
        self,
        files: List[Path],
        processor_func,
        *args,
        **kwargs
    ) -> List[Any]:
        """
        Process files in batches for better performance.
        
        Args:
            files: List of files to process
            processor_func: Function to process each file
            *args: Additional arguments for processor
            **kwargs: Additional keyword arguments for processor
            
        Returns:
            List of processing results
        """
        @self.profiler.profile
        def _process_batch():
            results = []
            
            for i in range(0, len(files), self.batch_size):
                batch = files[i:i + self.batch_size]
                logger.debug(f"Processing batch {i // self.batch_size + 1}")
                
                for file_path in batch:
                    try:
                        result = processor_func(file_path, *args, **kwargs)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        results.append(None)
            
            return results
        
        return _process_batch()


class MemoryOptimizer:
    """
    Memory optimizer for reducing memory footprint.
    """
    
    def __init__(self):
        """Initialize memory optimizer."""
        self.profiler = get_optimizer().get_profiler()
    
    def stream_large_file(self, file_path: Path, chunk_size: int = 8192):
        """
        Stream large file in chunks to reduce memory usage.
        
        Args:
            file_path: Path to file
            chunk_size: Size of each chunk in bytes
            
        Yields:
            File chunks
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def process_large_file(
        self,
        file_path: Path,
        processor_func,
        chunk_size: int = 8192
    ) -> Any:
        """
        Process large file in chunks.
        
        Args:
            file_path: Path to file
            processor_func: Function to process each chunk
            chunk_size: Size of each chunk
            
        Returns:
            Processing result
        """
        @self.profiler.profile
        def _process():
            results = []
            for chunk in self.stream_large_file(file_path, chunk_size):
                result = processor_func(chunk)
                if result is not None:
                    results.append(result)
            return results
        
        return _process()
    
    def limit_collection_size(
        self,
        collection: List[Any],
        max_size: int = 1000
    ) -> List[Any]:
        """
        Limit collection size to prevent memory issues.
        
        Args:
            collection: Collection to limit
            max_size: Maximum size
            
        Returns:
            Limited collection
        """
        if len(collection) > max_size:
            logger.warning(
                f"Collection size {len(collection)} exceeds limit {max_size}, truncating"
            )
            return collection[:max_size]
        return collection


# Factory functions for creating optimized instances

def create_optimized_file_creator(**kwargs) -> OptimizedFileCreator:
    """
    Create an optimized file creator instance.
    
    Args:
        **kwargs: Arguments for FileCreator
        
    Returns:
        OptimizedFileCreator instance
    """
    return OptimizedFileCreator(**kwargs)


def create_optimized_diff_engine(**kwargs) -> OptimizedDiffEngine:
    """
    Create an optimized diff engine instance.
    
    Args:
        **kwargs: Arguments for DiffEngine
        
    Returns:
        OptimizedDiffEngine instance
    """
    return OptimizedDiffEngine(**kwargs)


def create_optimized_context_analyzer() -> OptimizedContextAnalyzer:
    """
    Create an optimized context analyzer instance.
    
    Returns:
        OptimizedContextAnalyzer instance
    """
    return OptimizedContextAnalyzer()
