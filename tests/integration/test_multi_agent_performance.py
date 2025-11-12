"""
Performance tests for multi-agent workflows.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from src.codegenie.agents.base_agent import BaseAgent, Task, AgentResult, AgentCapability
from src.codegenie.agents.communication import AgentCommunicationBus, Message, MessageType
from src.codegenie.agents.coordinator import AgentCoordinator, CoordinationStrategy
from src.codegenie.core.config import Config
from src.codegenie.models.model_router import ModelRouter


class MockAgent(BaseAgent):
    """Mock agent for performance testing."""
    
    def __init__(self, name: str, capabilities: List[AgentCapability], delay: float = 0.1):
        config = Mock(spec=Config)
        model_router = Mock(spec=ModelRouter)
        super().__init__(name, capabilities, config, model_router)
        self.execution_delay = delay
    
    async def can_handle_task(self, task: Task) -> bool:
        """Mock task handling check."""
        return True
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Mock task execution with configurable delay."""
        await asyncio.sleep(self.execution_delay)
        
        return AgentResult(
            agent_name=self.name,
            task_id=task.id,
            success=True,
            output=f"Result from {self.name}",
            confidence=0.8,
            execution_time=self.execution_delay
        )


class TestMultiAgentPerformance:
    """Test performance characteristics of multi-agent system."""
    
    @pytest.fixture
    async def communication_bus(self):
        """Create communication bus."""
        bus = AgentCommunicationBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.fixture
    async def coordinator(self, communication_bus):
        """Create coordinator."""
        return AgentCoordinator(communication_bus)
    
    @pytest.fixture
    async def fast_agents(self):
        """Create fast mock agents."""
        return {
            "agent1": MockAgent("agent1", [AgentCapability.CODE_GENERATION], delay=0.01),
            "agent2": MockAgent("agent2", [AgentCapability.CODE_ANALYSIS], delay=0.01),
            "agent3": MockAgent("agent3", [AgentCapability.TESTING], delay=0.01),
            "agent4": MockAgent("agent4", [AgentCapability.DOCUMENTATION], delay=0.01)
        }
    
    @pytest.fixture
    async def slow_agents(self):
        """Create slow mock agents."""
        return {
            "slow1": MockAgent("slow1", [AgentCapability.CODE_GENERATION], delay=0.5),
            "slow2": MockAgent("slow2", [AgentCapability.SECURITY_ANALYSIS], delay=0.5),
            "slow3": MockAgent("slow3", [AgentCapability.PERFORMANCE_OPTIMIZATION], delay=0.5)
        }
    
    async def test_parallel_execution_performance(self, coordinator, fast_agents):
        """Test performance of parallel task execution."""
        # Register agents
        for agent in fast_agents.values():
            coordinator.register_agent(agent)
        
        # Create multiple independent tasks
        tasks = []
        for i in range(10):
            task = Task(
                id=f"task_{i}",
                description=f"Task {i}",
                task_type="code_generation"
            )
            tasks.append(task)
        
        # Create parallel coordination plan
        plan = await coordinator.coordinate_complex_task(
            description="Parallel performance test",
            subtasks=tasks,
            strategy=CoordinationStrategy.PARALLEL
        )
        
        # Measure execution time
        start_time = time.time()
        success = await coordinator.execute_coordination_plan(plan)
        execution_time = time.time() - start_time
        
        assert success
        # Parallel execution should be much faster than sequential
        # With 0.01s delay per task, parallel should complete in ~0.1s
        assert execution_time < 0.5
        print(f"Parallel execution time: {execution_time:.3f}s")
    
    async def test_sequential_execution_performance(self, coordinator, fast_agents):
        """Test performance of sequential task execution."""
        # Register agents
        for agent in fast_agents.values():
            coordinator.register_agent(agent)
        
        # Create sequential tasks
        tasks = []
        for i in range(5):  # Fewer tasks for sequential to keep test reasonable
            task = Task(
                id=f"seq_task_{i}",
                description=f"Sequential Task {i}",
                task_type="code_generation"
            )
            tasks.append(task)
        
        # Create sequential coordination plan
        plan = await coordinator.coordinate_complex_task(
            description="Sequential performance test",
            subtasks=tasks,
            strategy=CoordinationStrategy.SEQUENTIAL
        )
        
        # Measure execution time
        start_time = time.time()
        success = await coordinator.execute_coordination_plan(plan)
        execution_time = time.time() - start_time
        
        assert success
        # Sequential execution should take approximately sum of individual delays
        # 5 tasks * 0.01s = ~0.05s minimum
        assert execution_time >= 0.04  # Allow for some overhead
        print(f"Sequential execution time: {execution_time:.3f}s")
    
    async def test_mixed_speed_coordination(self, coordinator, fast_agents, slow_agents):
        """Test coordination with mixed-speed agents."""
        # Register both fast and slow agents
        all_agents = {**fast_agents, **slow_agents}
        for agent in all_agents.values():
            coordinator.register_agent(agent)
        
        # Create tasks that will be assigned to different speed agents
        tasks = [
            Task(id="fast1", description="Fast task 1", task_type="code_generation"),
            Task(id="slow1", description="Slow task 1", task_type="security_analysis"),
            Task(id="fast2", description="Fast task 2", task_type="testing"),
            Task(id="slow2", description="Slow task 2", task_type="performance_optimization")
        ]
        
        # Create parallel plan
        plan = await coordinator.coordinate_complex_task(
            description="Mixed speed test",
            subtasks=tasks,
            strategy=CoordinationStrategy.PARALLEL
        )
        
        # Measure execution time
        start_time = time.time()
        success = await coordinator.execute_coordination_plan(plan)
        execution_time = time.time() - start_time
        
        assert success
        # Should complete in time of slowest agent (~0.5s)
        assert execution_time >= 0.4  # At least as long as slow agents
        assert execution_time < 1.0   # But not too much overhead
        print(f"Mixed speed execution time: {execution_time:.3f}s")
    
    async def test_communication_bus_performance(self, communication_bus):
        """Test communication bus performance under load."""
        # Register multiple mock agents
        agent_count = 10
        agents = {}
        
        for i in range(agent_count):
            agent_name = f"perf_agent_{i}"
            mock_agent = Mock()
            mock_agent.name = agent_name
            agents[agent_name] = mock_agent
            communication_bus.register_agent(agent_name, mock_agent)
        
        # Send many messages
        message_count = 100
        start_time = time.time()
        
        tasks = []
        for i in range(message_count):
            sender = f"perf_agent_{i % agent_count}"
            recipient = f"perf_agent_{(i + 1) % agent_count}"
            
            task = communication_bus.send_direct_message(
                sender=sender,
                recipient=recipient,
                content={"test": f"message_{i}"}
            )
            tasks.append(task)
        
        # Wait for all messages to be sent
        await asyncio.gather(*tasks)
        
        # Allow time for message processing
        await asyncio.sleep(0.1)
        
        send_time = time.time() - start_time
        
        # Should handle messages efficiently
        assert send_time < 2.0  # Should send 100 messages in under 2 seconds
        
        # Check message statistics
        stats = communication_bus.get_message_stats()
        assert stats["total_messages"] >= message_count
        
        print(f"Sent {message_count} messages in {send_time:.3f}s")
        print(f"Message rate: {message_count / send_time:.1f} messages/second")
    
    async def test_coordination_scalability(self, coordinator, fast_agents):
        """Test coordination scalability with increasing task count."""
        # Register agents
        for agent in fast_agents.values():
            coordinator.register_agent(agent)
        
        task_counts = [5, 10, 20, 50]
        execution_times = []
        
        for task_count in task_counts:
            # Create tasks
            tasks = []
            for i in range(task_count):
                task = Task(
                    id=f"scale_task_{task_count}_{i}",
                    description=f"Scalability test task {i}",
                    task_type="code_generation"
                )
                tasks.append(task)
            
            # Create plan
            plan = await coordinator.coordinate_complex_task(
                description=f"Scalability test with {task_count} tasks",
                subtasks=tasks,
                strategy=CoordinationStrategy.PARALLEL
            )
            
            # Measure execution time
            start_time = time.time()
            success = await coordinator.execute_coordination_plan(plan)
            execution_time = time.time() - start_time
            
            assert success
            execution_times.append(execution_time)
            
            print(f"Tasks: {task_count}, Time: {execution_time:.3f}s")
        
        # Execution time should scale reasonably (not exponentially)
        # For parallel execution, time should remain relatively constant
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Time shouldn't increase by more than 3x even with 10x more tasks
        assert max_time / min_time < 3.0
    
    async def test_memory_usage_under_load(self, coordinator, fast_agents):
        """Test memory usage during high-load coordination."""
        import psutil
        import os
        
        # Register agents
        for agent in fast_agents.values():
            coordinator.register_agent(agent)
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many tasks
        task_count = 100
        tasks = []
        for i in range(task_count):
            task = Task(
                id=f"memory_task_{i}",
                description=f"Memory test task {i}",
                task_type="code_generation"
            )
            tasks.append(task)
        
        # Execute coordination
        plan = await coordinator.coordinate_complex_task(
            description="Memory usage test",
            subtasks=tasks,
            strategy=CoordinationStrategy.PARALLEL
        )
        
        success = await coordinator.execute_coordination_plan(plan)
        assert success
        
        # Check memory usage after execution
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Final memory: {final_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        
        # Memory increase should be reasonable (less than 50MB for 100 tasks)
        assert memory_increase < 50
    
    async def test_concurrent_coordination_plans(self, coordinator, fast_agents):
        """Test performance with multiple concurrent coordination plans."""
        # Register agents
        for agent in fast_agents.values():
            coordinator.register_agent(agent)
        
        # Create multiple coordination plans
        plan_count = 5
        tasks_per_plan = 5
        
        plans = []
        for plan_idx in range(plan_count):
            tasks = []
            for task_idx in range(tasks_per_plan):
                task = Task(
                    id=f"concurrent_plan_{plan_idx}_task_{task_idx}",
                    description=f"Concurrent test task {task_idx}",
                    task_type="code_generation"
                )
                tasks.append(task)
            
            plan = await coordinator.coordinate_complex_task(
                description=f"Concurrent plan {plan_idx}",
                subtasks=tasks,
                strategy=CoordinationStrategy.PARALLEL
            )
            plans.append(plan)
        
        # Execute all plans concurrently
        start_time = time.time()
        
        execution_tasks = [
            coordinator.execute_coordination_plan(plan)
            for plan in plans
        ]
        
        results = await asyncio.gather(*execution_tasks)
        execution_time = time.time() - start_time
        
        # All plans should succeed
        assert all(results)
        
        # Should complete efficiently
        assert execution_time < 2.0
        
        print(f"Executed {plan_count} concurrent plans in {execution_time:.3f}s")
    
    async def test_agent_performance_metrics(self, coordinator, fast_agents):
        """Test agent performance metric tracking."""
        # Register agents
        for agent in fast_agents.values():
            coordinator.register_agent(agent)
        
        # Execute some tasks to generate metrics
        tasks = []
        for i in range(10):
            task = Task(
                id=f"metrics_task_{i}",
                description=f"Metrics test task {i}",
                task_type="code_generation"
            )
            tasks.append(task)
        
        plan = await coordinator.coordinate_complex_task(
            description="Performance metrics test",
            subtasks=tasks,
            strategy=CoordinationStrategy.PARALLEL
        )
        
        success = await coordinator.execute_coordination_plan(plan)
        assert success
        
        # Check coordination statistics
        stats = coordinator.get_coordination_stats()
        
        assert stats["registered_agents"] == len(fast_agents)
        assert stats["completed_plans"] > 0
        assert stats["success_rate"] > 0.0
        
        # Check individual agent performance
        for agent_name in fast_agents.keys():
            if agent_name in coordinator.agent_performance:
                perf = coordinator.agent_performance[agent_name]
                assert "success_rate" in perf
                assert perf["success_rate"] >= 0.0
        
        print(f"Coordination stats: {stats}")
    
    async def test_error_handling_performance(self, coordinator):
        """Test performance impact of error handling."""
        # Create agents with different failure rates
        reliable_agent = MockAgent("reliable", [AgentCapability.CODE_GENERATION], delay=0.01)
        
        # Mock unreliable agent that sometimes fails
        unreliable_agent = MockAgent("unreliable", [AgentCapability.CODE_ANALYSIS], delay=0.01)
        
        async def failing_execute_task(task: Task) -> AgentResult:
            await asyncio.sleep(0.01)
            # Fail 30% of the time
            import random
            if random.random() < 0.3:
                return AgentResult(
                    agent_name="unreliable",
                    task_id=task.id,
                    success=False,
                    error="Simulated failure"
                )
            return AgentResult(
                agent_name="unreliable",
                task_id=task.id,
                success=True,
                output="Success result",
                confidence=0.7
            )
        
        unreliable_agent.execute_task = failing_execute_task
        
        # Register agents
        coordinator.register_agent(reliable_agent)
        coordinator.register_agent(unreliable_agent)
        
        # Create tasks
        tasks = []
        for i in range(20):
            task = Task(
                id=f"error_task_{i}",
                description=f"Error handling test task {i}",
                task_type="code_generation" if i % 2 == 0 else "code_analysis"
            )
            tasks.append(task)
        
        # Execute with error handling
        plan = await coordinator.coordinate_complex_task(
            description="Error handling performance test",
            subtasks=tasks,
            strategy=CoordinationStrategy.PARALLEL
        )
        
        start_time = time.time()
        success = await coordinator.execute_coordination_plan(plan)
        execution_time = time.time() - start_time
        
        # Should complete even with some failures
        # (success depends on coordination strategy's error handling)
        assert execution_time < 2.0  # Should not be significantly slower
        
        print(f"Error handling test completed in {execution_time:.3f}s")
        print(f"Overall success: {success}")


if __name__ == "__main__":
    pytest.main([__file__])