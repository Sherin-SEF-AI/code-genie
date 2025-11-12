"""
Scalability tests for the CodeGenie system.
Tests system behavior under increasing load and data volume.
"""

import pytest
import asyncio
import time
import psutil
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile
import shutil
import statistics

from src.codegenie.core.workflow_engine import WorkflowEngine, WorkflowPlan
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.core.learning_engine import LearningEngine
from src.codegenie.agents.coordinator import AgentCoordinator
from src.codegenie.core.end_to_end_workflows import (
    EndToEndWorkflowOrchestrator,
    WorkflowType
)
from src.codegenie.core.advanced_config import (
    AdvancedConfigurationManager,
    ConfigScope
)


class TestWorkflowScalability:
    """Test workflow system scalability."""
    
    @pytest.fixture
    def workflow_system(self):
        """Create workflow system for scalability testing."""
        config = Mock()
        config.autonomous_workflows = True
        
        workflow_engine = WorkflowEngine(config)
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        # Mock fast execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.01)
        )
        agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="test", completed=True)]
        )
        agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_workflow_count_scalability(self, workflow_system):
        """Test scalability with increasing workflow count."""
        
        workflow_counts = [10, 50, 100, 200]
        results = []
        
        for count in workflow_counts:
            start_time = time.time()
            
            # Create workflows
            workflows = []
            for i in range(count):
                workflow = await workflow_system.create_workflow(
                    WorkflowType.FEATURE_DEVELOPMENT,
                    f"Scalability test {i}",
                    {"test_id": i}
                )
                workflows.append(workflow)
            
            # Execute workflows concurrently
            tasks = [
                workflow_system.execute_workflow(w.id)
                for w in workflows
            ]
            
            execution_results = await asyncio.gather(*tasks)
            
            elapsed_time = time.time() - start_time
            
            results.append({
                'count': count,
                'time': elapsed_time,
                'success_rate': sum(1 for r in execution_results if r.success) / count,
                'throughput': count / elapsed_time
            })
            
            print(f"Workflows: {count}, Time: {elapsed_time:.2f}s, Throughput: {results[-1]['throughput']:.1f} workflows/s")
        
        # Verify scalability characteristics
        for result in results:
            assert result['success_rate'] >= 0.95  # At least 95% success rate
            assert result['throughput'] > 5  # At least 5 workflows per second
    
    @pytest.mark.asyncio
    async def test_workflow_complexity_scalability(self, workflow_system):
        """Test scalability with increasing workflow complexity."""
        
        step_counts = [5, 10, 20, 50]
        results = []
        
        for step_count in step_counts:
            start_time = time.time()
            
            # Create complex workflow
            workflow = await workflow_system.create_workflow(
                WorkflowType.COMPLETE_PROJECT_SETUP,
                f"Complex workflow with {step_count} steps",
                {"complexity": step_count}
            )
            
            # Simulate steps
            workflow.steps = [
                Mock(name=f"step_{i}", completed=False)
                for i in range(step_count)
            ]
            
            # Execute workflow
            result = await workflow_system.execute_workflow(workflow.id)
            
            elapsed_time = time.time() - start_time
            
            results.append({
                'steps': step_count,
                'time': elapsed_time,
                'success': result.success,
                'time_per_step': elapsed_time / step_count
            })
            
            print(f"Steps: {step_count}, Time: {elapsed_time:.2f}s, Time/step: {results[-1]['time_per_step']:.3f}s")
        
        # Verify complexity scaling
        for result in results:
            assert result['success']
            assert result['time_per_step'] < 1.0  # Each step should take less than 1 second


class TestContextScalability:
    """Test context engine scalability."""
    
    @pytest.fixture
    def context_engine(self):
        """Create context engine for testing."""
        config = Mock()
        return ContextEngine(config)
    
    @pytest.mark.asyncio
    async def test_context_storage_scalability(self, context_engine):
        """Test scalability of context storage."""
        
        interaction_counts = [100, 500, 1000, 2000]
        results = []
        
        for count in interaction_counts:
            start_time = time.time()
            
            # Store many interactions
            for i in range(count):
                await context_engine.store_interaction({
                    'type': 'scalability_test',
                    'content': f'Interaction {i}',
                    'timestamp': f'2024-01-01T00:{i//60:02d}:{i%60:02d}'
                })
            
            elapsed_time = time.time() - start_time
            
            results.append({
                'count': count,
                'time': elapsed_time,
                'throughput': count / elapsed_time
            })
            
            print(f"Interactions: {count}, Time: {elapsed_time:.2f}s, Throughput: {results[-1]['throughput']:.1f} ops/s")
        
        # Verify storage scalability
        for result in results:
            assert result['throughput'] > 50  # At least 50 operations per second
    
    @pytest.mark.asyncio
    async def test_context_retrieval_scalability(self, context_engine):
        """Test scalability of context retrieval."""
        
        # Pre-populate context
        for i in range(1000):
            await context_engine.store_interaction({
                'type': 'test',
                'content': f'Test interaction {i}',
                'timestamp': f'2024-01-01T00:{i//60:02d}:{i%60:02d}'
            })
        
        # Test retrieval performance
        retrieval_counts = [10, 50, 100, 200]
        results = []
        
        for count in retrieval_counts:
            start_time = time.time()
            
            # Retrieve context multiple times
            for i in range(count):
                await context_engine.retrieve_relevant_context(f'test {i}')
            
            elapsed_time = time.time() - start_time
            
            results.append({
                'count': count,
                'time': elapsed_time,
                'throughput': count / elapsed_time
            })
            
            print(f"Retrievals: {count}, Time: {elapsed_time:.2f}s, Throughput: {results[-1]['throughput']:.1f} ops/s")
        
        # Verify retrieval scalability
        for result in results:
            assert result['throughput'] > 20  # At least 20 retrievals per second


class TestConfigurationScalability:
    """Test configuration system scalability."""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create configuration manager for testing."""
        return AdvancedConfigurationManager(base_path=tmp_path)
    
    def test_configuration_key_scalability(self, config_manager):
        """Test scalability with many configuration keys."""
        
        key_counts = [100, 500, 1000, 5000]
        results = []
        
        for count in key_counts:
            # Write phase
            write_start = time.time()
            
            for i in range(count):
                config_manager.set_config(
                    f"scalability.section_{i//100}.key_{i}",
                    f"value_{i}",
                    ConfigScope.USER,
                    validate=False
                )
            
            write_time = time.time() - write_start
            
            # Read phase
            read_start = time.time()
            
            for i in range(count):
                value = config_manager.get_config(f"scalability.section_{i//100}.key_{i}")
                assert value == f"value_{i}"
            
            read_time = time.time() - read_start
            
            results.append({
                'count': count,
                'write_time': write_time,
                'read_time': read_time,
                'write_throughput': count / write_time,
                'read_throughput': count / read_time
            })
            
            print(f"Keys: {count}, Write: {write_time:.2f}s ({results[-1]['write_throughput']:.1f} ops/s), "
                  f"Read: {read_time:.2f}s ({results[-1]['read_throughput']:.1f} ops/s)")
        
        # Verify configuration scalability
        for result in results:
            assert result['write_throughput'] > 20  # At least 20 writes per second
            assert result['read_throughput'] > 100  # At least 100 reads per second (cached)
    
    def test_configuration_hierarchy_scalability(self, config_manager, tmp_path):
        """Test scalability of configuration hierarchy resolution."""
        
        # Set up deep hierarchy
        scopes = [ConfigScope.GLOBAL, ConfigScope.USER, ConfigScope.PROJECT]
        
        for scope in scopes:
            for i in range(100):
                config_manager.set_config(
                    f"hierarchy.key_{i}",
                    f"{scope.value}_value_{i}",
                    scope,
                    project_path=tmp_path if scope == ConfigScope.PROJECT else None,
                    validate=False
                )
        
        # Test resolution performance
        start_time = time.time()
        
        for i in range(100):
            value = config_manager.get_config(
                f"hierarchy.key_{i}",
                project_path=tmp_path
            )
            assert value == f"project_value_{i}"
        
        elapsed_time = time.time() - start_time
        throughput = 100 / elapsed_time
        
        print(f"Hierarchy resolution: {elapsed_time:.2f}s, Throughput: {throughput:.1f} ops/s")
        
        # Should handle hierarchy efficiently
        assert throughput > 50  # At least 50 resolutions per second


class TestMemoryScalability:
    """Test memory usage scalability."""
    
    @pytest.mark.asyncio
    async def test_workflow_memory_scalability(self):
        """Test memory usage with many workflows."""
        
        import gc
        
        config = Mock()
        workflow_engine = WorkflowEngine(config)
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.01)
        )
        
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        # Force garbage collection
        gc.collect()
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create and execute many workflows
        workflow_count = 500
        
        for i in range(workflow_count):
            workflow = await orchestrator.create_workflow(
                WorkflowType.LEARNING_ADAPTATION,
                f"Memory test {i}",
                {"iteration": i}
            )
            
            await orchestrator.execute_workflow(workflow.id)
            
            # Periodic garbage collection
            if i % 50 == 0:
                gc.collect()
        
        # Force final garbage collection
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        memory_per_workflow = memory_increase / workflow_count
        
        print(f"Memory usage: {memory_increase:.1f}MB total, {memory_per_workflow:.3f}MB per workflow")
        
        # Memory should scale reasonably
        assert memory_per_workflow < 2.0  # Less than 2MB per workflow
        assert memory_increase < 500  # Total increase less than 500MB
    
    def test_configuration_memory_scalability(self, tmp_path):
        """Test memory usage with large configuration."""
        
        import gc
        
        # Force garbage collection
        gc.collect()
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        config_manager = AdvancedConfigurationManager(base_path=tmp_path)
        
        # Add many configuration values
        key_count = 10000
        
        for i in range(key_count):
            config_manager.set_config(
                f"memory.test.key_{i}",
                f"value_{i}" * 10,  # Larger values
                ConfigScope.USER,
                validate=False
            )
            
            if i % 1000 == 0:
                gc.collect()
        
        # Force final garbage collection
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        memory_per_key = memory_increase / key_count
        
        print(f"Configuration memory: {memory_increase:.1f}MB total, {memory_per_key:.4f}MB per key")
        
        # Memory should scale reasonably
        assert memory_per_key < 0.1  # Less than 0.1MB per key
        assert memory_increase < 500  # Total increase less than 500MB


class TestConcurrencyScalability:
    """Test concurrency scalability."""
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_scalability(self):
        """Test scalability with concurrent workflow execution."""
        
        config = Mock()
        workflow_engine = WorkflowEngine(config)
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.1)
        )
        
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        concurrency_levels = [5, 10, 20, 50]
        results = []
        
        for concurrency in concurrency_levels:
            start_time = time.time()
            
            # Create workflows
            workflows = []
            for i in range(concurrency):
                workflow = await orchestrator.create_workflow(
                    WorkflowType.FEATURE_DEVELOPMENT,
                    f"Concurrent test {i}",
                    {"concurrency": concurrency}
                )
                workflows.append(workflow)
            
            # Execute concurrently
            tasks = [
                orchestrator.execute_workflow(w.id)
                for w in workflows
            ]
            
            execution_results = await asyncio.gather(*tasks)
            
            elapsed_time = time.time() - start_time
            
            results.append({
                'concurrency': concurrency,
                'time': elapsed_time,
                'success_rate': sum(1 for r in execution_results if r.success) / concurrency,
                'throughput': concurrency / elapsed_time
            })
            
            print(f"Concurrency: {concurrency}, Time: {elapsed_time:.2f}s, "
                  f"Throughput: {results[-1]['throughput']:.1f} workflows/s")
        
        # Verify concurrency scaling
        for result in results:
            assert result['success_rate'] >= 0.95  # At least 95% success rate
            assert result['throughput'] > 2  # At least 2 workflows per second
    
    @pytest.mark.asyncio
    async def test_sustained_load_scalability(self):
        """Test scalability under sustained load."""
        
        config = Mock()
        workflow_engine = WorkflowEngine(config)
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.01)
        )
        
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        # Sustained load for 10 seconds
        duration = 10
        start_time = time.time()
        completed_count = 0
        batch_size = 10
        
        while time.time() - start_time < duration:
            # Create batch
            workflows = []
            for i in range(batch_size):
                workflow = await orchestrator.create_workflow(
                    WorkflowType.LEARNING_ADAPTATION,
                    f"Sustained load {completed_count + i}",
                    {"batch": completed_count // batch_size}
                )
                workflows.append(workflow)
            
            # Execute batch
            tasks = [
                orchestrator.execute_workflow(w.id)
                for w in workflows
            ]
            
            results = await asyncio.gather(*tasks)
            completed_count += sum(1 for r in results if r.success)
            
            # Brief pause
            await asyncio.sleep(0.05)
        
        actual_duration = time.time() - start_time
        throughput = completed_count / actual_duration
        
        print(f"Sustained load: {completed_count} workflows in {actual_duration:.1f}s, "
              f"Throughput: {throughput:.1f} workflows/s")
        
        # Should maintain reasonable throughput
        assert throughput > 10  # At least 10 workflows per second
        assert completed_count > 100  # At least 100 workflows completed


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
