"""
Task monitoring and progress tracking system.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TaskMonitor:
    """Monitors task execution and provides progress tracking."""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
        self.failed_tasks: List[Dict[str, Any]] = []
        self.callbacks: List[Callable] = []
    
    def start_task(
        self,
        task_id: str,
        task_type: str,
        description: str,
        estimated_duration: Optional[float] = None,
    ) -> None:
        """Start monitoring a task."""
        
        task_info = {
            "task_id": task_id,
            "task_type": task_type,
            "description": description,
            "start_time": time.time(),
            "estimated_duration": estimated_duration,
            "status": "running",
            "progress": 0.0,
            "current_step": None,
            "steps": [],
            "metadata": {},
        }
        
        self.active_tasks[task_id] = task_info
        
        logger.info(f"Started monitoring task: {task_id} - {description}")
        self._notify_callbacks("task_started", task_info)
    
    def update_task_progress(
        self,
        task_id: str,
        progress: float,
        current_step: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update task progress."""
        
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return
        
        task_info = self.active_tasks[task_id]
        task_info["progress"] = min(max(progress, 0.0), 1.0)
        
        if current_step:
            task_info["current_step"] = current_step
        
        if metadata:
            task_info["metadata"].update(metadata)
        
        logger.debug(f"Updated progress for task {task_id}: {progress:.1%}")
        self._notify_callbacks("task_progress", task_info)
    
    def add_task_step(
        self,
        task_id: str,
        step_description: str,
        step_type: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a step to a task."""
        
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return
        
        step = {
            "description": step_description,
            "type": step_type,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        
        self.active_tasks[task_id]["steps"].append(step)
        
        logger.debug(f"Added step to task {task_id}: {step_description}")
        self._notify_callbacks("task_step", self.active_tasks[task_id])
    
    def complete_task(
        self,
        task_id: str,
        success: bool = True,
        result: Optional[Any] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Mark a task as completed."""
        
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return
        
        task_info = self.active_tasks[task_id]
        task_info["end_time"] = time.time()
        task_info["duration"] = task_info["end_time"] - task_info["start_time"]
        task_info["status"] = "completed" if success else "failed"
        task_info["progress"] = 1.0
        task_info["result"] = result
        task_info["error_message"] = error_message
        
        # Move to appropriate list
        if success:
            self.completed_tasks.append(task_info)
        else:
            self.failed_tasks.append(task_info)
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        logger.info(f"Completed task: {task_id} - Success: {success}")
        self._notify_callbacks("task_completed", task_info)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific task."""
        
        # Check active tasks first
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].copy()
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task["task_id"] == task_id:
                return task.copy()
        
        # Check failed tasks
        for task in self.failed_tasks:
            if task["task_id"] == task_id:
                return task.copy()
        
        return None
    
    def get_all_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all tasks grouped by status."""
        
        return {
            "active": list(self.active_tasks.values()),
            "completed": self.completed_tasks.copy(),
            "failed": self.failed_tasks.copy(),
        }
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about task execution."""
        
        total_tasks = len(self.completed_tasks) + len(self.failed_tasks)
        successful_tasks = len(self.completed_tasks)
        failed_tasks = len(self.failed_tasks)
        
        success_rate = (successful_tasks / total_tasks) if total_tasks > 0 else 0.0
        
        # Calculate average duration
        durations = [task["duration"] for task in self.completed_tasks + self.failed_tasks if "duration" in task]
        average_duration = sum(durations) / len(durations) if durations else 0.0
        
        # Calculate task type distribution
        task_types = {}
        for task in self.completed_tasks + self.failed_tasks:
            task_type = task["task_type"]
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": success_rate,
            "average_duration": average_duration,
            "task_type_distribution": task_types,
        }
    
    def add_callback(self, callback: Callable) -> None:
        """Add a callback for task events."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> None:
        """Remove a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, event_type: str, task_info: Dict[str, Any]) -> None:
        """Notify all callbacks of a task event."""
        
        for callback in self.callbacks:
            try:
                callback(event_type, task_info)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def clear_history(self) -> None:
        """Clear task history."""
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        logger.info("Cleared task history")
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tasks."""
        
        all_tasks = self.completed_tasks + self.failed_tasks
        all_tasks.sort(key=lambda x: x.get("end_time", 0), reverse=True)
        
        return all_tasks[:limit]


class TestMonitor:
    """Specialized monitor for test execution."""
    
    def __init__(self, task_monitor: TaskMonitor):
        self.task_monitor = task_monitor
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.test_history: List[Dict[str, Any]] = []
    
    def start_test_run(
        self,
        test_id: str,
        test_type: str,
        description: str,
        test_files: List[str],
    ) -> None:
        """Start monitoring a test run."""
        
        self.task_monitor.start_task(
            task_id=test_id,
            task_type=f"test_{test_type}",
            description=description,
        )
        
        self.test_results[test_id] = {
            "test_id": test_id,
            "test_type": test_type,
            "description": description,
            "test_files": test_files,
            "start_time": time.time(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "coverage": None,
            "errors": [],
            "warnings": [],
        }
        
        logger.info(f"Started test run: {test_id}")
    
    def update_test_progress(
        self,
        test_id: str,
        tests_run: int,
        tests_passed: int,
        tests_failed: int,
        tests_skipped: int = 0,
        current_test: Optional[str] = None,
    ) -> None:
        """Update test execution progress."""
        
        if test_id not in self.test_results:
            logger.warning(f"Test run {test_id} not found")
            return
        
        test_result = self.test_results[test_id]
        test_result["tests_run"] = tests_run
        test_result["tests_passed"] = tests_passed
        test_result["tests_failed"] = tests_failed
        test_result["tests_skipped"] = tests_skipped
        
        total_tests = tests_run + tests_skipped
        progress = tests_run / total_tests if total_tests > 0 else 0.0
        
        self.task_monitor.update_task_progress(
            task_id=test_id,
            progress=progress,
            current_step=current_test,
        )
        
        logger.debug(f"Updated test progress for {test_id}: {tests_run} tests run")
    
    def add_test_error(
        self,
        test_id: str,
        test_name: str,
        error_message: str,
        error_type: str = "error",
    ) -> None:
        """Add a test error."""
        
        if test_id not in self.test_results:
            logger.warning(f"Test run {test_id} not found")
            return
        
        error = {
            "test_name": test_name,
            "error_message": error_message,
            "error_type": error_type,
            "timestamp": time.time(),
        }
        
        self.test_results[test_id]["errors"].append(error)
        
        self.task_monitor.add_task_step(
            task_id=test_id,
            step_description=f"Test failed: {test_name}",
            step_type="error",
            metadata=error,
        )
        
        logger.warning(f"Test error in {test_id}: {test_name} - {error_message}")
    
    def add_test_warning(
        self,
        test_id: str,
        test_name: str,
        warning_message: str,
    ) -> None:
        """Add a test warning."""
        
        if test_id not in self.test_results:
            logger.warning(f"Test run {test_id} not found")
            return
        
        warning = {
            "test_name": test_name,
            "warning_message": warning_message,
            "timestamp": time.time(),
        }
        
        self.test_results[test_id]["warnings"].append(warning)
        
        self.task_monitor.add_task_step(
            task_id=test_id,
            step_description=f"Test warning: {test_name}",
            step_type="warning",
            metadata=warning,
        )
        
        logger.warning(f"Test warning in {test_id}: {test_name} - {warning_message}")
    
    def complete_test_run(
        self,
        test_id: str,
        success: bool = True,
        coverage: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Complete a test run."""
        
        if test_id not in self.test_results:
            logger.warning(f"Test run {test_id} not found")
            return
        
        test_result = self.test_results[test_id]
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        test_result["success"] = success
        test_result["coverage"] = coverage
        
        # Move to history
        self.test_history.append(test_result.copy())
        
        # Complete the task
        self.task_monitor.complete_task(
            task_id=test_id,
            success=success,
            result=test_result,
        )
        
        # Remove from active results
        del self.test_results[test_id]
        
        logger.info(f"Completed test run: {test_id} - Success: {success}")
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get test execution statistics."""
        
        if not self.test_history:
            return {
                "total_test_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "total_tests_run": 0,
                "total_tests_passed": 0,
                "total_tests_failed": 0,
                "total_tests_skipped": 0,
            }
        
        total_runs = len(self.test_history)
        successful_runs = sum(1 for run in self.test_history if run.get("success", False))
        failed_runs = total_runs - successful_runs
        
        success_rate = successful_runs / total_runs if total_runs > 0 else 0.0
        
        durations = [run.get("duration", 0) for run in self.test_history]
        average_duration = sum(durations) / len(durations) if durations else 0.0
        
        total_tests_run = sum(run.get("tests_run", 0) for run in self.test_history)
        total_tests_passed = sum(run.get("tests_passed", 0) for run in self.test_history)
        total_tests_failed = sum(run.get("tests_failed", 0) for run in self.test_history)
        total_tests_skipped = sum(run.get("tests_skipped", 0) for run in self.test_history)
        
        return {
            "total_test_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": success_rate,
            "average_duration": average_duration,
            "total_tests_run": total_tests_run,
            "total_tests_passed": total_tests_passed,
            "total_tests_failed": total_tests_failed,
            "total_tests_skipped": total_tests_skipped,
        }
    
    def get_recent_test_runs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent test runs."""
        
        recent_runs = sorted(
            self.test_history,
            key=lambda x: x.get("end_time", 0),
            reverse=True
        )
        
        return recent_runs[:limit]
    
    def get_failing_tests(self) -> List[Dict[str, Any]]:
        """Get information about failing tests."""
        
        failing_tests = []
        
        for test_run in self.test_history:
            if not test_run.get("success", True):
                for error in test_run.get("errors", []):
                    failing_tests.append({
                        "test_run_id": test_run["test_id"],
                        "test_name": error["test_name"],
                        "error_message": error["error_message"],
                        "error_type": error["error_type"],
                        "timestamp": error["timestamp"],
                    })
        
        return failing_tests
