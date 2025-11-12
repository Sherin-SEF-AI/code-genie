"""
Parallel Executor for concurrent task processing in workflows.

This module provides:
- Parallel execution of independent tasks
- Resource management for parallel operations
- Synchronization for dependent tasks
- Progress tracking for parallel workflows
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class TaskState(Enum):
    """State of a task in parallel execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParallelTask:
    """Represents a task for parallel execution."""
    id: str
    name: str
    execute_fn: Callable
    dependencies: List[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: int = 0


@dataclass
class ExecutionBatch:
    """Represents a batch of tasks that can run in parallel."""
    batch_id: int
    tasks: List[ParallelTask]
    dependencies: Set[int] = field(default_factory=set)  # Batch IDs this batch depends on


@dataclass
class ParallelExecutionResult:
    """Result of parallel execution."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    total_duration: float
    task_results: Dict[str, Any]
    errors: Dict[str, str]
    success: bool


class ResourceManager:
    """Manages resources for parallel task execution."""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        """
        Initialize resource manager.
        
        Args:
            max_concurrent_tasks: Maximum number of tasks to run concurrently
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.active_tasks: Set[str] = set()
        self.resource_usage: Dict[str, Any] = {}
        
        logger.info(f"Initialized ResourceManager with max {max_concurrent_tasks} concurrent tasks")
    
    async def acquire(self, task_id: str) -> bool:
        """
        Acquire resources for a task.
        
        Args:
            task_id: ID of the task requesting resources
            
        Returns:
            True if resources acquired successfully
        """
        await self.semaphore.acquire()
        self.active_tasks.add(task_id)
        logger.debug(f"Task {task_id} acquired resources. Active tasks: {len(self.active_tasks)}")
        return True
    
    def release(self, task_id: str) -> None:
        """
        Release resources for a task.
        
        Args:
            task_id: ID of the task releasing resources
        """
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
            self.semaphore.release()
            logger.debug(f"Task {task_id} released resources. Active tasks: {len(self.active_tasks)}")
    
    def get_active_task_count(self) -> int:
        """Get number of currently active tasks."""
        return len(self.active_tasks)
    
    def is_at_capacity(self) -> bool:
        """Check if resource manager is at capacity."""
        return len(self.active_tasks) >= self.max_concurrent_tasks


class DependencyResolver:
    """Resolves task dependencies for parallel execution."""
    
    def __init__(self):
        """Initialize dependency resolver."""
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        
    def build_dependency_graph(self, tasks: List[ParallelTask]) -> None:
        """
        Build dependency graph from tasks.
        
        Args:
            tasks: List of tasks to analyze
        """
        self.dependency_graph.clear()
        self.reverse_dependencies.clear()
        
        # Build forward and reverse dependency graphs
        for task in tasks:
            self.dependency_graph[task.id] = set(task.dependencies)
            
            for dep_id in task.dependencies:
                if dep_id not in self.reverse_dependencies:
                    self.reverse_dependencies[dep_id] = set()
                self.reverse_dependencies[dep_id].add(task.id)
    
    def get_ready_tasks(
        self,
        tasks: List[ParallelTask],
        completed_task_ids: Set[str]
    ) -> List[ParallelTask]:
        """
        Get tasks that are ready to execute (all dependencies met).
        
        Args:
            tasks: List of all tasks
            completed_task_ids: Set of completed task IDs
            
        Returns:
            List of tasks ready to execute
        """
        ready_tasks = []
        
        for task in tasks:
            if task.state != TaskState.PENDING:
                continue
            
            # Check if all dependencies are completed
            dependencies_met = all(
                dep_id in completed_task_ids
                for dep_id in task.dependencies
            )
            
            if dependencies_met:
                ready_tasks.append(task)
        
        return ready_tasks
    
    def create_execution_batches(self, tasks: List[ParallelTask]) -> List[ExecutionBatch]:
        """
        Create batches of tasks that can run in parallel.
        
        Args:
            tasks: List of tasks to batch
            
        Returns:
            List of execution batches
        """
        self.build_dependency_graph(tasks)
        
        batches = []
        task_to_batch: Dict[str, int] = {}
        processed_tasks: Set[str] = set()
        batch_id = 0
        
        while len(processed_tasks) < len(tasks):
            # Find tasks with no unprocessed dependencies
            batch_tasks = []
            
            for task in tasks:
                if task.id in processed_tasks:
                    continue
                
                # Check if all dependencies are processed
                dependencies_processed = all(
                    dep_id in processed_tasks
                    for dep_id in task.dependencies
                )
                
                if dependencies_processed:
                    batch_tasks.append(task)
                    processed_tasks.add(task.id)
                    task_to_batch[task.id] = batch_id
            
            if not batch_tasks:
                # Circular dependency or error
                logger.error("Circular dependency detected or no tasks ready")
                break
            
            # Determine batch dependencies
            batch_deps = set()
            for task in batch_tasks:
                for dep_id in task.dependencies:
                    if dep_id in task_to_batch:
                        batch_deps.add(task_to_batch[dep_id])
            
            batch = ExecutionBatch(
                batch_id=batch_id,
                tasks=batch_tasks,
                dependencies=batch_deps
            )
            batches.append(batch)
            batch_id += 1
        
        return batches


class ProgressTracker:
    """Tracks progress of parallel execution."""
    
    def __init__(self, total_tasks: int):
        """
        Initialize progress tracker.
        
        Args:
            total_tasks: Total number of tasks to track
        """
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.running_tasks = 0
        self.task_progress: Dict[str, float] = {}
        self.callbacks: List[Callable] = []
        
    def register_callback(self, callback: Callable) -> None:
        """
        Register a progress callback.
        
        Args:
            callback: Function to call on progress updates
        """
        self.callbacks.append(callback)
    
    def update_task_started(self, task_id: str) -> None:
        """Mark a task as started."""
        self.running_tasks += 1
        self.task_progress[task_id] = 0.0
        self._notify_callbacks()
    
    def update_task_progress(self, task_id: str, progress: float) -> None:
        """
        Update progress for a specific task.
        
        Args:
            task_id: Task ID
            progress: Progress percentage (0.0 to 1.0)
        """
        self.task_progress[task_id] = progress
        self._notify_callbacks()
    
    def update_task_completed(self, task_id: str, success: bool) -> None:
        """
        Mark a task as completed.
        
        Args:
            task_id: Task ID
            success: Whether task completed successfully
        """
        self.running_tasks -= 1
        self.task_progress[task_id] = 1.0
        
        if success:
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1
        
        self._notify_callbacks()
    
    def get_overall_progress(self) -> float:
        """Get overall progress percentage."""
        if self.total_tasks == 0:
            return 100.0
        
        return (self.completed_tasks / self.total_tasks) * 100.0
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of execution status."""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'running_tasks': self.running_tasks,
            'overall_progress': self.get_overall_progress(),
            'task_progress': self.task_progress.copy()
        }
    
    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks of progress update."""
        status = self.get_status_summary()
        for callback in self.callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")


class ParallelExecutor:
    """
    Main parallel executor for concurrent task processing.
    """
    
    def __init__(self, max_concurrent_tasks: int = 5):
        """
        Initialize parallel executor.
        
        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks
        """
        self.resource_manager = ResourceManager(max_concurrent_tasks)
        self.dependency_resolver = DependencyResolver()
        self.progress_tracker: Optional[ProgressTracker] = None
        
        logger.info(f"Initialized ParallelExecutor with max {max_concurrent_tasks} concurrent tasks")
    
    async def execute_tasks(
        self,
        tasks: List[ParallelTask],
        progress_callback: Optional[Callable] = None
    ) -> ParallelExecutionResult:
        """
        Execute tasks in parallel respecting dependencies.
        
        Args:
            tasks: List of tasks to execute
            progress_callback: Optional callback for progress updates
            
        Returns:
            ParallelExecutionResult with execution details
        """
        start_time = datetime.now()
        
        # Initialize progress tracker
        self.progress_tracker = ProgressTracker(len(tasks))
        if progress_callback:
            self.progress_tracker.register_callback(progress_callback)
        
        # Create execution batches
        batches = self.dependency_resolver.create_execution_batches(tasks)
        
        logger.info(f"Executing {len(tasks)} tasks in {len(batches)} batches")
        
        # Execute batches sequentially, tasks within batch in parallel
        task_results = {}
        errors = {}
        completed_task_ids = set()
        
        for batch in batches:
            logger.info(f"Executing batch {batch.batch_id} with {len(batch.tasks)} tasks")
            
            # Execute all tasks in batch concurrently
            batch_tasks = [
                self._execute_task_with_resources(task, task_results, errors)
                for task in batch.tasks
            ]
            
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Update completed tasks
            for task in batch.tasks:
                if task.state == TaskState.COMPLETED:
                    completed_task_ids.add(task.id)
        
        # Calculate results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        completed_count = sum(1 for t in tasks if t.state == TaskState.COMPLETED)
        failed_count = sum(1 for t in tasks if t.state == TaskState.FAILED)
        cancelled_count = sum(1 for t in tasks if t.state == TaskState.CANCELLED)
        
        result = ParallelExecutionResult(
            total_tasks=len(tasks),
            completed_tasks=completed_count,
            failed_tasks=failed_count,
            cancelled_tasks=cancelled_count,
            total_duration=duration,
            task_results=task_results,
            errors=errors,
            success=failed_count == 0
        )
        
        logger.info(f"Parallel execution completed: {completed_count}/{len(tasks)} successful in {duration:.2f}s")
        
        return result
    
    async def _execute_task_with_resources(
        self,
        task: ParallelTask,
        results: Dict[str, Any],
        errors: Dict[str, str]
    ) -> None:
        """
        Execute a single task with resource management.
        
        Args:
            task: Task to execute
            results: Dictionary to store results
            errors: Dictionary to store errors
        """
        try:
            # Acquire resources
            await self.resource_manager.acquire(task.id)
            
            # Update state
            task.state = TaskState.RUNNING
            task.started_at = datetime.now()
            
            if self.progress_tracker:
                self.progress_tracker.update_task_started(task.id)
            
            logger.debug(f"Executing task: {task.name}")
            
            # Execute task
            result = await task.execute_fn()
            
            # Store result
            task.result = result
            task.state = TaskState.COMPLETED
            task.completed_at = datetime.now()
            results[task.id] = result
            
            if self.progress_tracker:
                self.progress_tracker.update_task_completed(task.id, True)
            
            logger.debug(f"Task completed successfully: {task.name}")
            
        except Exception as e:
            # Handle error
            task.state = TaskState.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            errors[task.id] = str(e)
            
            if self.progress_tracker:
                self.progress_tracker.update_task_completed(task.id, False)
            
            logger.error(f"Task failed: {task.name} - {e}")
            
        finally:
            # Release resources
            self.resource_manager.release(task.id)
    
    async def execute_batch(
        self,
        tasks: List[ParallelTask]
    ) -> Dict[str, Any]:
        """
        Execute a batch of independent tasks in parallel.
        
        Args:
            tasks: List of tasks to execute (should have no dependencies)
            
        Returns:
            Dictionary mapping task IDs to results
        """
        results = {}
        errors = {}
        
        # Execute all tasks concurrently
        task_coroutines = [
            self._execute_task_with_resources(task, results, errors)
            for task in tasks
        ]
        
        await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        return results
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.progress_tracker:
            return {}
        
        return self.progress_tracker.get_status_summary()
