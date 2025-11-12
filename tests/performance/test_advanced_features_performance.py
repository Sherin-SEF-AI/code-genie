"""
Performance and scalability tests for advanced features.
"""

import pytest
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock
import statistics

from src.codegenie.core.end_to_end_workflows import (
    EndToEndWorkflowOrchestrator,
    WorkflowType
)
from src.codegenie.core.advanced_config import (
    AdvancedConfigurationManager,
    ConfigScope,
    UserPreferences
)
from src.codegenie.core.workflow_engine import WorkflowEngine
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.core.learning_engine import LearningEngine
from src.codegenie.agents.coordinator import AgentCoordinator


class PerformanceMetrics:
    """Helper class for collecting performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
        self.cpu_usage = []
        
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.memory_usage = []
        self.cpu_usage = []
        
    def record_metrics(self):
        """Record current system metrics."""
        process = psutil.Process()
        self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
        self.cpu_usage.append(process.cpu_percent())
        
    def stop_monitoring(self):
        """Stop monitoring and return results."""
        self.end_time = time.time()
        
        return {
            'execution_time': self.end_time - self.start_time,
            'avg_memory_mb': statistics.mean(self.memory_usage) if self.memory_usage else 0,
            'max_memory_mb': max(self.memory_usage) if self.memory_usage else 0,
            'avg_cpu_percent': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
            'max_cpu_percent': max(self.cpu_usage) if self.cpu_usage else 0
        }


class TestWorkflowPerformance:
    """Test workflow system performance."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        config.adaptive_learning = True
        return config
    
    @pytest.fixture
    def workflow_orchestrator(self, mock_config):
        """Create workflow orchestrator with mocked components."""
        
        workflow_engine = WorkflowEngine(mock_config)
        context_engine = ContextEngine(mock_config)
        learning_engine = LearningEngine(mock_config)
        agent_coordinator = AgentCoordinator(mock_config)
        
        # Mock fast execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.1)
        )
        agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="test", completed=True)]
        )
        agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        learning_engine.learn_from_workflow = AsyncMock()
        
        return EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
    
    @pytest.mark.asyncio
    async def test_single_workflow_performance(self, workflow_orchestrator):
        """Test performance of single workflow execution."""
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        # Create and execute workflow
        goal = "Performance test workflow"
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.AUTONOMOUS_DEVELOPMENT,
            goal,
            {}
        )
        
        metrics.record_metrics()
        
        result = await workflow_orchestrator.execute_workflow(workflow.id)
        
        performance_data = metrics.stop_monitoring()
        
        # Performance assertions
        assert result.success
        assert performance_data['execution_time'] < 5.0  # Should complete in under 5 seconds
        assert performance_data['max_memory_mb'] < 500  # Should use less than 500MB
        
        print(f"Single workflow performance: {performance_data}")
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, workflow_orchestrator):
        """Test performance with concurrent workflow execution."""
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        # Create multiple workflows
        workflows = []
        for i in range(20):
            workflow = await workflow_orchestrator.create_workflow(
                WorkflowType.LEARNING_ADAPTATION,
                f"Concurrent test {i}",
                {"test_id": i}
            )
            workflows.append(workflow)
        
        metrics.record_metrics()
        
        # Execute workflows concurrently
        tasks = [
            workflow_orchestrator.execute_workflow(workflow.id)
            for workflow in workflows
        ]
        
        results = await asyncio.gather(*tasks)
        
        performance_data = metrics.stop_monitoring()
        
        # Performance assertions
        assert all(result.success for result in results)
        assert performance_data['execution_time'] < 30.0  # Should complete 20 workflows in under 30 seconds
        assert performance_data['max_memory_mb'] < 1000  # Should use less than 1GB
        
        print(f"Concurrent workflow performance (20 workflows): {performance_data}")
    
    @pytest.mark.asyncio
    async def test_workflow_scaling_performance(self, workflow_orchestrator):
        """Test workflow performance scaling with different loads."""
        
        workflow_counts = [1, 5, 10, 20, 50]
        performance_results = []
        
        for count in workflow_counts:
            metrics = PerformanceMetrics()
            metrics.start_monitoring()
            
            # Create workflows
            workflows = []
            for i in range(count):
                workflow = await workflow_orchestrator.create_workflow(
                    WorkflowType.FEATURE_DEVELOPMENT,
                    f"Scaling test {i}",
                    {"batch_size": count}
                )
                workflows.append(workflow)
            
            # Execute workflows
            tasks = [
                workflow_orchestrator.execute_workflow(workflow.id)
                for workflow in workflows
            ]
            
            results = await asyncio.gather(*tasks)
            performance_data = metrics.stop_monitoring()
            
            # Record results
            performance_results.append({
                'workflow_count': count,
                'success_rate': sum(1 for r in results if r.success) / len(results),
                'execution_time': performance_data['execution_time'],
                'avg_memory_mb': performance_data['avg_memory_mb'],
                'max_memory_mb': performance_data['max_memory_mb']
            })
            
            print(f"Scaling test ({count} workflows): {performance_data}")
        
        # Analyze scaling characteristics
        for i in range(1, len(performance_results)):
            prev = performance_results[i-1]
            curr = performance_results[i]
            
            # Check that performance scales reasonably
            time_ratio = curr['execution_time'] / prev['execution_time']
            workflow_ratio = curr['workflow_count'] / prev['workflow_count']
            
            # Time should scale sub-linearly due to concurrency
            assert time_ratio < workflow_ratio * 1.5
            
            # Memory should scale reasonably
            memory_ratio = curr['max_memory_mb'] / prev['max_memory_mb']
            assert memory_ratio < workflow_ratio * 2
    
    @pytest.mark.asyncio
    async def test_workflow_step_performance(self, workflow_orchestrator):
        """Test performance of individual workflow steps."""
        
        # Create workflow with many steps
        goal = "Complex multi-step workflow"
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.COMPLETE_PROJECT_SETUP,
            goal,
            {}
        )
        
        # Measure step execution times
        step_times = []
        
        for step in workflow.steps:
            start_time = time.time()
            
            # Mock step execution
            step_result = await workflow_orchestrator._execute_workflow_step(step, workflow)
            
            step_time = time.time() - start_time
            step_times.append(step_time)
            
            assert step_result.success
        
        # Performance assertions
        avg_step_time = statistics.mean(step_times)
        max_step_time = max(step_times)
        
        assert avg_step_time < 2.0  # Average step should complete in under 2 seconds
        assert max_step_time < 5.0  # No step should take more than 5 seconds
        
        print(f"Step performance - Avg: {avg_step_time:.2f}s, Max: {max_step_time:.2f}s")


class TestConfigurationPerformance:
    """Test configuration system performance."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create configuration manager."""
        return AdvancedConfigurationManager(base_path=temp_dir)
    
    def test_configuration_write_performance(self, config_manager):
        """Test configuration write performance."""
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        # Write many configuration values
        config_count = 1000
        
        for i in range(config_count):
            config_manager.set_config(
                f"perf.test.section_{i // 100}.key_{i}",
                f"value_{i}",
                ConfigScope.USER,
                validate=False  # Skip validation for performance test
            )
            
            if i % 100 == 0:
                metrics.record_metrics()
        
        performance_data = metrics.stop_monitoring()
        
        # Performance assertions
        writes_per_second = config_count / performance_data['execution_time']
        
        assert writes_per_second > 50  # Should handle at least 50 writes per second
        assert performance_data['max_memory_mb'] < 200  # Should use less than 200MB
        
        print(f"Configuration write performance: {writes_per_second:.1f} writes/sec")
    
    def test_configuration_read_performance(self, config_manager):
        """Test configuration read performance."""
        
        # Pre-populate configuration
        config_count = 1000
        
        for i in range(config_count):
            config_manager.set_config(
                f"perf.read.key_{i}",
                f"value_{i}",
                ConfigScope.USER,
                validate=False
            )
        
        # Test read performance
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        for i in range(config_count):
            value = config_manager.get_config(f"perf.read.key_{i}")
            assert value == f"value_{i}"
            
            if i % 100 == 0:
                metrics.record_metrics()
        
        performance_data = metrics.stop_monitoring()
        
        # Performance assertions
        reads_per_second = config_count / performance_data['execution_time']
        
        assert reads_per_second > 500  # Should handle at least 500 reads per second (cached)
        
        print(f"Configuration read performance: {reads_per_second:.1f} reads/sec")
    
    def test_configuration_hierarchy_performance(self, config_manager, temp_dir):
        """Test configuration hierarchy resolution performance."""
        
        # Set up configuration hierarchy
        scopes = [ConfigScope.GLOBAL, ConfigScope.USER, ConfigScope.PROJECT]
        
        for scope in scopes:
            for i in range(100):
                config_manager.set_config(
                    f"hierarchy.key_{i}",
                    f"{scope.value}_value_{i}",
                    scope,
                    project_path=temp_dir if scope == ConfigScope.PROJECT else None,
                    validate=False
                )
        
        # Test hierarchy resolution performance
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        for i in range(100):
            # This should resolve through the hierarchy
            value = config_manager.get_config(
                f"hierarchy.key_{i}",
                project_path=temp_dir
            )
            # Project scope should win
            assert value == f"project_value_{i}"
            
            if i % 20 == 0:
                metrics.record_metrics()
        
        performance_data = metrics.stop_monitoring()
        
        # Performance assertions
        resolutions_per_second = 100 / performance_data['execution_time']
        
        assert resolutions_per_second > 100  # Should handle at least 100 resolutions per second
        
        print(f"Hierarchy resolution performance: {resolutions_per_second:.1f} resolutions/sec")
    
    def test_configuration_caching_performance(self, config_manager):
        """Test configuration caching performance."""
        
        # Set configuration value
        config_manager.set_config("cache.test", "cached_value", ConfigScope.USER)
        
        # Test cached read performance
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        read_count = 10000
        
        for i in range(read_count):
            value = config_manager.get_config("cache.test")
            assert value == "cached_value"
            
            if i % 1000 == 0:
                metrics.record_metrics()
        
        performance_data = metrics.stop_monitoring()
        
        # Performance assertions
        cached_reads_per_second = read_count / performance_data['execution_time']
        
        assert cached_reads_per_second > 5000  # Should handle at least 5000 cached reads per second
        
        print(f"Cached read performance: {cached_reads_per_second:.1f} reads/sec")


class TestMemoryUsagePerformance:
    """Test memory usage and garbage collection performance."""
    
    @pytest.fixture
    def workflow_orchestrator(self):
        """Create workflow orchestrator for memory testing."""
        
        config = Mock()
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        
        workflow_engine = WorkflowEngine(config)
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        # Mock lightweight execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.01)
        )
        
        return EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
    
    @pytest.mark.asyncio
    async def test_workflow_memory_usage(self, workflow_orchestrator):
        """Test memory usage during workflow execution."""
        
        import gc
        
        # Force garbage collection
        gc.collect()
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create and execute many workflows
        workflow_count = 100
        
        for i in range(workflow_count):
            workflow = await workflow_orchestrator.create_workflow(
                WorkflowType.LEARNING_ADAPTATION,
                f"Memory test {i}",
                {"iteration": i}
            )
            
            result = await workflow_orchestrator.execute_workflow(workflow.id)
            assert result.success
            
            # Periodic garbage collection
            if i % 20 == 0:
                gc.collect()
        
        # Force final garbage collection
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory assertions
        memory_per_workflow = memory_increase / workflow_count
        
        assert memory_per_workflow < 5.0  # Should use less than 5MB per workflow
        assert memory_increase < 200  # Total increase should be less than 200MB
        
        print(f"Memory usage: {memory_increase:.1f}MB total, {memory_per_workflow:.2f}MB per workflow")
    
    def test_configuration_memory_usage(self):
        """Test configuration system memory usage."""
        
        import gc
        
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Force garbage collection
            gc.collect()
            
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Create many configuration managers
            managers = []
            
            for i in range(50):
                manager = AdvancedConfigurationManager(base_path=temp_dir / f"config_{i}")
                
                # Add some configuration data
                for j in range(100):
                    manager.set_config(f"test.key_{j}", f"value_{j}", ConfigScope.USER, validate=False)
                
                managers.append(manager)
                
                # Periodic garbage collection
                if i % 10 == 0:
                    gc.collect()
            
            # Force final garbage collection
            gc.collect()
            
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory assertions
            memory_per_manager = memory_increase / len(managers)
            
            assert memory_per_manager < 10.0  # Should use less than 10MB per manager
            
            print(f"Configuration memory usage: {memory_increase:.1f}MB total, {memory_per_manager:.2f}MB per manager")
            
        finally:
            shutil.rmtree(temp_dir)


class TestConcurrencyPerformance:
    """Test concurrency and thread safety performance."""
    
    @pytest.fixture
    def config_manager(self):
        """Create configuration manager for concurrency testing."""
        temp_dir = Path(tempfile.mkdtemp())
        manager = AdvancedConfigurationManager(base_path=temp_dir)
        
        yield manager
        
        shutil.rmtree(temp_dir)
    
    def test_concurrent_configuration_access(self, config_manager):
        """Test concurrent configuration access performance."""
        
        # Pre-populate configuration
        for i in range(100):
            config_manager.set_config(f"concurrent.key_{i}", f"value_{i}", ConfigScope.USER, validate=False)
        
        def read_config_worker(worker_id, iterations):
            """Worker function for concurrent reads."""
            results = []
            
            for i in range(iterations):
                key = f"concurrent.key_{i % 100}"
                value = config_manager.get_config(key)
                results.append(value == f"value_{i % 100}")
            
            return all(results)
        
        # Test concurrent reads
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(read_config_worker, i, 1000)
                for i in range(10)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        execution_time = time.time() - start_time
        
        # Performance assertions
        total_operations = 10 * 1000
        operations_per_second = total_operations / execution_time
        
        assert all(results)  # All reads should be successful
        assert operations_per_second > 1000  # Should handle at least 1000 ops/sec
        
        print(f"Concurrent read performance: {operations_per_second:.1f} ops/sec")
    
    def test_concurrent_configuration_writes(self, config_manager):
        """Test concurrent configuration writes performance."""
        
        def write_config_worker(worker_id, iterations):
            """Worker function for concurrent writes."""
            success_count = 0
            
            for i in range(iterations):
                try:
                    config_manager.set_config(
                        f"concurrent.write.worker_{worker_id}.key_{i}",
                        f"worker_{worker_id}_value_{i}",
                        ConfigScope.USER,
                        validate=False
                    )
                    success_count += 1
                except Exception as e:
                    print(f"Write error: {e}")
            
            return success_count
        
        # Test concurrent writes
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(write_config_worker, i, 200)
                for i in range(5)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        execution_time = time.time() - start_time
        
        # Performance assertions
        total_writes = sum(results)
        expected_writes = 5 * 200
        
        assert total_writes == expected_writes  # All writes should succeed
        
        writes_per_second = total_writes / execution_time
        assert writes_per_second > 100  # Should handle at least 100 writes/sec
        
        print(f"Concurrent write performance: {writes_per_second:.1f} writes/sec")


class TestLoadTestingPerformance:
    """Test system performance under load."""
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self):
        """Test system performance under sustained load."""
        
        config = Mock()
        config.autonomous_workflows = True
        
        workflow_engine = WorkflowEngine(config)
        context_engine = ContextEngine(config)
        
        # Mock very fast execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.001)
        )
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine
        )
        
        # Sustained load test
        duration_seconds = 30
        start_time = time.time()
        completed_workflows = 0
        
        while time.time() - start_time < duration_seconds:
            # Create batch of workflows
            batch_size = 10
            workflows = []
            
            for i in range(batch_size):
                workflow = await orchestrator.create_workflow(
                    WorkflowType.LEARNING_ADAPTATION,
                    f"Load test {completed_workflows + i}",
                    {"batch": completed_workflows // batch_size}
                )
                workflows.append(workflow)
            
            # Execute batch
            tasks = [
                orchestrator.execute_workflow(workflow.id)
                for workflow in workflows
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Count successful completions
            completed_workflows += sum(1 for r in results if r.success)
            
            # Brief pause to prevent overwhelming
            await asyncio.sleep(0.1)
        
        actual_duration = time.time() - start_time
        workflows_per_second = completed_workflows / actual_duration
        
        # Performance assertions
        assert workflows_per_second > 10  # Should handle at least 10 workflows per second
        assert completed_workflows > 300  # Should complete at least 300 workflows in 30 seconds
        
        print(f"Sustained load performance: {workflows_per_second:.1f} workflows/sec over {actual_duration:.1f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])